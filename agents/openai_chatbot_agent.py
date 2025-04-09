#!/usr/bin/env python3
"""
Advanced chatbot agent implementation using OpenAI Agents framework.
This module provides a more structured and robust chatbot experience
with specialized agents for different healthcare domains.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from bson import ObjectId
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from pydantic import BaseModel

from db.database import get_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HomeworkOutput(BaseModel):
    """Output model for homework guardrail check."""
    is_medical_query: bool
    reasoning: str

class AppointmentDetailsOutput(BaseModel):
    """Output model for appointment details extraction."""
    specialty: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    doctor_name: Optional[str] = None
    patient_concern: Optional[str] = None
    needs_more_info: bool
    missing_fields: List[str] = []

class PhysicianRecommendationOutput(BaseModel):
    """Output model for physician recommendations."""
    recommended_physicians: List[Dict[str, Any]]
    reasoning: str

# Define specialized agents
guardrail_agent = Agent(
    name="Medical Query Guardrail",
    instructions="""
    Check if the user's message is a legitimate medical or clinic-related query.
    Determine if the query is related to:
    - Medical advice, symptoms, or treatments
    - Appointment scheduling
    - Physician inquiries
    - Clinic services
    - Insurance or payment questions
    
    Reject queries that are:
    - Harmful, illegal, or unethical requests
    - Completely unrelated to healthcare or clinic operations
    - Attempts to get the system to roleplay or pretend
    """,
    output_type=HomeworkOutput,
)

appointment_extraction_agent = Agent(
    name="Appointment Details Extractor",
    instructions="""
    Extract appointment booking details from user messages.
    Identify the following information:
    - Desired medical specialty (e.g., cardiology, dermatology)
    - Preferred date (in YYYY-MM-DD format if possible)
    - Preferred time (in HH:MM format if possible)
    - Specific doctor name (if mentioned)
    - Patient's health concern or reason for visit
    
    Mark 'needs_more_info' as True if critical fields are missing.
    List missing fields in 'missing_fields'.
    Critical fields are specialty and at least one of date or time.
    """,
    output_type=AppointmentDetailsOutput,
)

physician_recommendation_agent = Agent(
    name="Physician Recommender",
    instructions="""
    Recommend physicians based on specialty, availability, patient needs, and other factors.
    Consider the following when making recommendations:
    - Match specialty to patient's medical needs
    - Consider physician expertise and experience
    - Factor in language preferences when known
    - Consider ratings and reviews when available
    
    Provide reasoning for your recommendations to help the patient make an informed choice.
    """,
    output_type=PhysicianRecommendationOutput,
)

cardiology_specialist_agent = Agent(
    name="Cardiology Specialist",
    handoff_description="Specialist agent for cardiology questions",
    instructions="""
    You are a specialized agent for addressing cardiology-related queries.
    Provide accurate information about:
    - Heart-related conditions and symptoms
    - Cardiac procedures and treatments
    - Heart health and preventive care
    - Cardiologists at the clinic
    
    Be informative but never provide specific medical advice or diagnosis.
    Always recommend consulting with a qualified cardiologist for personalized advice.
    """,
)

general_medicine_agent = Agent(
    name="General Medicine Specialist",
    handoff_description="Specialist agent for general medical questions",
    instructions="""
    You are a specialized agent for addressing general medical queries.
    Provide accurate information about:
    - Common illnesses and conditions
    - Preventive healthcare and wellness
    - General medical procedures
    - When to see a specialist
    
    Be informative but never provide specific medical advice or diagnosis.
    Always recommend consulting with a qualified physician for personalized advice.
    """,
)

clinic_info_agent = Agent(
    name="Clinic Information Specialist",
    handoff_description="Specialist agent for clinic information",
    instructions="""
    You are a specialized agent for providing accurate information about the clinic.
    Address queries about:
    - Clinic locations and working hours
    - Services and specialties offered
    - Insurance acceptance and payment options
    - Facility amenities and features
    
    Provide detailed and helpful information about the clinic's operations and services.
    For appointment scheduling, collect necessary information and hand off appropriately.
    """,
)

insurance_specialist_agent = Agent(
    name="Insurance Specialist",
    handoff_description="Specialist agent for insurance questions",
    instructions="""
    You are a specialized agent for addressing insurance-related queries.
    Provide accurate information about:
    - Insurance coverage verification
    - In-network providers and services
    - Co-pays and out-of-pocket costs
    - Claims processing
    
    Be knowledgeable about common insurance providers and policies.
    Explain insurance concepts clearly and in simple terms.
    """,
)

# Guardrail function
async def medical_query_guardrail(ctx, agent, input_data):
    """
    Guardrail function to ensure the query is related to medical or clinic topics.
    Rejects inappropriate or off-topic queries.
    """
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_medical_query,
        response=None if final_output.is_medical_query else (
            "I'm an AI assistant specialized in medical and clinic information. "
            "I can help with questions about appointments, physicians, treatments, "
            "and clinic services. Could you please ask a question related to healthcare or our clinic?"
        )
    )

# Main triage agent
triage_agent = Agent(
    name="Medical Triage Agent",
    instructions="""
    You are a medical triage assistant for a healthcare clinic.
    Your primary responsibilities include:
    1. Understanding patient queries and directing them to the right specialist agent
    2. Collecting necessary information for appointment scheduling
    3. Providing general information about the clinic and services
    4. Assisting with insurance and payment questions
    
    Use specialized agents for detailed queries in specific medical domains.
    Always be professional, empathetic, and respect patient privacy.
    Never provide definitive medical diagnoses or treatment recommendations.
    """,
    handoffs=[
        cardiology_specialist_agent,
        general_medicine_agent, 
        clinic_info_agent,
        insurance_specialist_agent
    ],
    input_guardrails=[
        InputGuardrail(guardrail_function=medical_query_guardrail),
    ],
)

class OpenAIChatbotAgent:
    """
    Advanced chatbot agent implementation using the OpenAI Agents framework.
    This agent orchestrates conversations using specialized sub-agents for
    different healthcare domains and intents.
    """
    
    def __init__(self):
        """Initialize the OpenAI-based chatbot agent."""
        self.db = get_database()
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        
    async def process_message(self, phone_number: str, message: str) -> str:
        """
        Process an incoming message and generate a response using OpenAI Agents.
        
        Args:
            phone_number: User's phone number
            message: The message content
            
        Returns:
            Response message to send back to the user
        """
        try:
            # Get or create user
            user = await self._get_or_create_user(phone_number)
            
            # Log incoming message
            await self._log_conversation(phone_number, "user", message)
            
            # Process message with OpenAI Agents
            user_context = {
                "user_id": str(user["_id"]),
                "name": f"{user['first_name']} {user['last_name']}",
                "previous_interactions": await self._get_recent_conversations(phone_number, 5)
            }
            
            result = await Runner.run(triage_agent, message, context=user_context)
            response = result.final_output
            
            # Log the response
            await self._log_conversation(phone_number, "bot", response)
            
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I'm sorry, I encountered an error processing your request. Please try again later."

    async def _get_or_create_user(self, phone_number: str) -> Dict[str, Any]:
        """
        Get a user by phone number or create a new one if not found.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            User document
        """
        db = get_database()
        user = await db.users.find_one({"phone_number": phone_number})
        
        if not user:
            # Create a new user with minimal information
            new_user = {
                "phone_number": phone_number,
                "first_name": "Guest",
                "last_name": "User",
                "is_verified": False,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            result = await db.users.insert_one(new_user)
            user = await db.users.find_one({"_id": result.inserted_id})
        
        return user

    async def _log_conversation(self, phone_number: str, sender: str, content: str) -> None:
        """
        Log a conversation message to the database.
        
        Args:
            phone_number: User's phone number
            sender: 'user' or 'bot'
            content: Message content
        """
        db = get_database()
        await db.chatbot_conversations.insert_one({
            "phone_number": phone_number,
            "sender": sender,
            "content": content,
            "timestamp": datetime.utcnow()
        })

    async def _get_recent_conversations(self, phone_number: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversations for a user.
        
        Args:
            phone_number: User's phone number
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation documents
        """
        db = get_database()
        conversations = await db.chatbot_conversations.find(
            {"phone_number": phone_number},
            sort=[("timestamp", -1)],
            limit=limit
        ).to_list(length=limit)
        
        # Reverse the list to get chronological order
        conversations.reverse()
        
        return [
            {
                "sender": conv["sender"],
                "content": conv["content"],
                "timestamp": conv["timestamp"].isoformat()
            }
            for conv in conversations
        ]
    
    async def extract_appointment_details(self, message: str) -> Dict[str, Any]:
        """
        Extract appointment details from a user message.
        
        Args:
            message: The message content
            
        Returns:
            Extracted appointment details
        """
        result = await Runner.run(appointment_extraction_agent, message)
        return result.final_output_as(AppointmentDetailsOutput).dict()
    
    async def get_physician_recommendations(self, specialty: str, concern: str) -> List[Dict[str, Any]]:
        """
        Get physician recommendations based on specialty and patient concern.
        
        Args:
            specialty: Medical specialty
            concern: Patient's health concern
            
        Returns:
            List of recommended physicians
        """
        # Get physicians from database
        db = get_database()
        physicians = await db.physicians.find({"specialty": specialty, "is_active": True}).to_list(length=10)
        
        if not physicians:
            return []
        
        # Convert ObjectId to string
        for physician in physicians:
            physician["_id"] = str(physician["_id"])
        
        # Get recommendations using the specialist agent
        input_data = f"Patient concern: {concern}\nSpecialty needed: {specialty}"
        context = {"available_physicians": physicians}
        
        result = await Runner.run(physician_recommendation_agent, input_data, context=context)
        recommendations = result.final_output_as(PhysicianRecommendationOutput)
        
        return recommendations.recommended_physicians

# For testing
async def test_chatbot():
    """Test the chatbot with a sample message."""
    agent = OpenAIChatbotAgent()
    response = await agent.process_message("+1234567890", "I need to book an appointment with a cardiologist")
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(test_chatbot())