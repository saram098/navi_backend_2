import os
import json
from openai import OpenAI
from typing import Dict, Any, List, Optional, Union
from settings.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai = OpenAI(api_key=settings.OPENAI_API_KEY)

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
MODEL = "gpt-4o"

async def get_intent_classification(message: str) -> Dict[str, Any]:
    """
    Classify the user's message intent using OpenAI.
    
    Args:
        message: User's message text
        
    Returns:
        Dictionary with intent classification and confidence
    """
    try:
        prompt = f"""
        You are an AI assistant for a medical clinic. Classify the following message into one of these intents:
        1. book_appointment - User wants to book a doctor appointment
        2. check_availability - User wants to check physician availability
        3. cancel_appointment - User wants to cancel an existing appointment
        4. reschedule_appointment - User wants to reschedule an appointment
        5. physician_info - User wants information about physicians
        6. insurance_check - User wants to check insurance coverage
        7. clinic_info - User wants information about the clinic
        8. pricing - User wants information about pricing or costs
        9. greeting - User is just saying hello or starting a conversation
        10. other - Message doesn't fit any of the above categories

        The user message is: "{message}"
        
        Respond in JSON format with:
        1. The intent category
        2. A confidence score from 0 to 1
        3. Extracted relevant entities (like specialty, date, time)
        """
        
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a medical clinic AI assistant."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Intent classification: {result}")
        return result
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        # Return a default classification if the API fails
        return {
            "intent": "other",
            "confidence": 0.5,
            "entities": {}
        }

async def generate_appointment_response(physician_data: Dict[str, Any], 
                                       date: str, 
                                       time_slot: Dict[str, Any]) -> str:
    """
    Generate a natural language response for an appointment confirmation.
    
    Args:
        physician_data: Physician details
        date: Appointment date
        time_slot: Time slot details
        
    Returns:
        Natural language response for the user
    """
    try:
        prompt = f"""
        Generate a friendly, conversational response confirming an appointment booking with the following details:

        Physician: Dr. {physician_data['name']}
        Specialty: {physician_data['specialty']}
        Date: {date}
        Time: {time_slot['start_time']} to {time_slot['end_time']}
        Price: {physician_data['consultation_price']} AED

        The response should be warm and reassuring, appropriate for a medical context.
        """
        
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful medical clinic assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        # Return a default response if the API fails
        return f"Your appointment with Dr. {physician_data['name']} ({physician_data['specialty']}) is confirmed for {date} at {time_slot['start_time']}. The consultation fee is {physician_data['consultation_price']} AED."

async def generate_physician_recommendations(user_query: str, 
                                           physicians_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate personalized physician recommendations based on user query.
    
    Args:
        user_query: User's query about physicians
        physicians_data: List of available physicians
        
    Returns:
        Dictionary with recommended physicians and reasoning
    """
    try:
        # Convert physicians data to a string for the prompt
        physicians_str = "\n".join([
            f"- Dr. {p['name']}: {p['specialty']}, {p['experience_years']} years experience, {p['consultation_price']} AED"
            for p in physicians_data[:10]  # Limit to 10 physicians to avoid token limits
        ])
        
        prompt = f"""
        Based on the user query and the available physicians, recommend the most suitable options.
        
        User query: "{user_query}"
        
        Available physicians:
        {physicians_str}
        
        Provide recommendations in JSON format with:
        1. A list of recommended physician IDs (from the original list)
        2. A brief explanation for each recommendation
        3. Follow-up questions the user might want to ask
        """
        
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a medical clinic assistant who helps patients find the right doctor."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Physician recommendations generated successfully")
        return result
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        # Return a default response if the API fails
        return {
            "recommendations": [],
            "explanation": "I'm unable to process your request right now. Please try again later or contact our clinic directly."
        }
