import os
import json
from openai import OpenAI
from typing import Dict, Any, List, Optional, Union, Callable
from settings.config import settings
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai = OpenAI(api_key=settings.OPENAI_API_KEY)

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
MODEL = "gpt-4o"

# Define a Tools class for the OpenAI agent framework
class AgentTools:
    """
    Tool definitions for the OpenAI agent framework.
    Each method is a tool that can be used by the agent.
    """
    
    def __init__(self, db=None):
        self.db = db
        
    def get_clinic_info(self, query: str) -> str:
        """
        Get information about the clinic based on a query.
        
        Args:
            query: Query string about clinic information
            
        Returns:
            String with clinic information
        """
        try:
            if not self.db:
                logger.warning("Database not available for clinic info lookup")
                return "I can't access clinic information at the moment."
            
            # In a real implementation, we would use Atlas Search with $search
            # Since we're simulating, we'll use a simple find operation
            clinic_info = asyncio.run(self.db.clinic_info.find_one({}))
            
            if not clinic_info:
                return "I couldn't find information about our clinic."
            
            # Format clinic information
            formatted_info = f"Clinic Name: {clinic_info.get('name')}\n"
            formatted_info += f"Description: {clinic_info.get('description')}\n"
            formatted_info += f"Address: {clinic_info.get('address')}\n"
            formatted_info += f"Phone: {clinic_info.get('phone')}\n"
            formatted_info += f"Email: {clinic_info.get('email')}\n"
            formatted_info += f"Website: {clinic_info.get('website')}\n"
            formatted_info += f"Working Hours:\n"
            
            for day, hours in clinic_info.get('working_hours', {}).items():
                formatted_info += f"  {day}: {hours}\n"
                
            formatted_info += f"\nMission: {clinic_info.get('mission')}\n"
            formatted_info += f"Vision: {clinic_info.get('vision')}\n"
            
            return formatted_info
        except Exception as e:
            logger.error(f"Error in get_clinic_info: {str(e)}")
            return "I encountered an error retrieving clinic information."
    
    def find_physicians(self, specialty: Optional[str] = None, name: Optional[str] = None, language: Optional[str] = None) -> str:
        """
        Find physicians based on specialty, name, or language.
        
        Args:
            specialty: Physician specialty
            name: Physician name (partial match)
            language: Language spoken by the physician
            
        Returns:
            String with physician information
        """
        try:
            if not self.db:
                logger.warning("Database not available for physician lookup")
                return "I can't access physician information at the moment."
            
            # Build query
            query = {"is_active": True}
            if specialty:
                query["specialty"] = specialty
            if name:
                # In a real implementation, we would use Atlas Search with $regex
                query["name"] = {"$regex": name, "$options": "i"}
            if language:
                query["languages"] = language
            
            # Find physicians
            physicians = asyncio.run(self.db.physicians.find(query).limit(5).to_list(5))
            
            if not physicians:
                return "I couldn't find any physicians matching your criteria."
            
            # Format physician information
            result = f"I found {len(physicians)} physicians:\n\n"
            
            for idx, physician in enumerate(physicians, 1):
                result += f"{idx}. {physician.get('name')} - {physician.get('specialty')}\n"
                result += f"   Qualification: {physician.get('qualification')}\n"
                result += f"   Experience: {physician.get('experience_years')} years\n"
                result += f"   Languages: {', '.join(physician.get('languages', []))}\n"
                result += f"   Consultation Fee: AED {physician.get('consultation_price')}\n"
                result += f"   Specialties: {', '.join(physician.get('specialties', []))}\n\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in find_physicians: {str(e)}")
            return "I encountered an error retrieving physician information."
    
    def find_treatments(self, specialty: Optional[str] = None, name: Optional[str] = None) -> str:
        """
        Find treatments based on specialty or name.
        
        Args:
            specialty: Treatment specialty
            name: Treatment name (partial match)
            
        Returns:
            String with treatment information
        """
        try:
            if not self.db:
                logger.warning("Database not available for treatment lookup")
                return "I can't access treatment information at the moment."
            
            # Build query
            query = {"is_active": True}
            if specialty:
                query["specialty"] = specialty
            if name:
                # In a real implementation, we would use Atlas Search with $regex
                query["name"] = {"$regex": name, "$options": "i"}
            
            # Find treatments
            treatments = asyncio.run(self.db.treatments.find(query).limit(5).to_list(5))
            
            if not treatments:
                return "I couldn't find any treatments matching your criteria."
            
            # Format treatment information
            result = f"I found {len(treatments)} treatments:\n\n"
            
            for idx, treatment in enumerate(treatments, 1):
                result += f"{idx}. {treatment.get('name')} - {treatment.get('specialty')}\n"
                result += f"   Description: {treatment.get('description')}\n"
                
                price_range = treatment.get('price_range', {})
                if price_range:
                    result += f"   Price Range: AED {price_range.get('min')} - AED {price_range.get('max')}\n"
                
                duration = treatment.get('duration_minutes')
                if duration:
                    result += f"   Duration: {duration} minutes\n\n"
                
            return result
        except Exception as e:
            logger.error(f"Error in find_treatments: {str(e)}")
            return "I encountered an error retrieving treatment information."
    
    def find_medical_packages(self, name: Optional[str] = None, max_price: Optional[float] = None) -> str:
        """
        Find medical packages based on name or maximum price.
        
        Args:
            name: Package name (partial match)
            max_price: Maximum package price
            
        Returns:
            String with medical package information
        """
        try:
            if not self.db:
                logger.warning("Database not available for medical package lookup")
                return "I can't access medical package information at the moment."
            
            # Build query
            query = {"is_active": True}
            if name:
                # In a real implementation, we would use Atlas Search with $regex
                query["name"] = {"$regex": name, "$options": "i"}
            if max_price:
                query["price"] = {"$lte": max_price}
            
            # Find packages
            packages = asyncio.run(self.db.medical_packages.find(query).limit(5).to_list(5))
            
            if not packages:
                return "I couldn't find any medical packages matching your criteria."
            
            # Format package information
            result = f"I found {len(packages)} medical packages:\n\n"
            
            for idx, package in enumerate(packages, 1):
                result += f"{idx}. {package.get('name')}\n"
                result += f"   Description: {package.get('description')}\n"
                result += f"   Price: AED {package.get('price')}\n"
                result += f"   Duration: {package.get('duration_minutes')} minutes\n"
                
                services = package.get('services', [])
                if services:
                    result += f"   Services: {', '.join(services[:5])}"
                    if len(services) > 5:
                        result += f" and {len(services) - 5} more"
                    result += "\n\n"
                
            return result
        except Exception as e:
            logger.error(f"Error in find_medical_packages: {str(e)}")
            return "I encountered an error retrieving medical package information."
    
    def check_appointment_availability(self, physician_name: Optional[str] = None, specialty: Optional[str] = None, date: Optional[str] = None) -> str:
        """
        Check appointment availability for a physician or specialty.
        
        Args:
            physician_name: Physician name
            specialty: Physician specialty
            date: Date in YYYY-MM-DD format
            
        Returns:
            String with availability information
        """
        try:
            if not self.db:
                logger.warning("Database not available for availability lookup")
                return "I can't access appointment information at the moment."
            
            # Build physician query
            query = {"is_active": True}
            if physician_name:
                query["name"] = {"$regex": physician_name, "$options": "i"}
            if specialty:
                query["specialty"] = specialty
                
            # Find physicians
            physicians = asyncio.run(self.db.physicians.find(query).to_list(3))
            
            if not physicians:
                return "I couldn't find any physicians matching your criteria."
            
            # Get current date if not provided
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
                
            # Format availability information
            result = f"Here is the availability for {date}:\n\n"
            
            for physician in physicians:
                result += f"{physician.get('name')} - {physician.get('specialty')}:\n"
                
                # Find available slots for the date
                available_slots = []
                for schedule_day in physician.get('schedule', []):
                    if schedule_day.get('date') == date:
                        available_slots = [
                            slot for slot in schedule_day.get('time_slots', [])
                            if slot.get('is_available', False)
                        ]
                        break
                
                if available_slots:
                    result += "   Available time slots:\n"
                    for slot in available_slots[:5]:  # Limit to 5 slots for readability
                        result += f"   - {slot.get('start_time')} to {slot.get('end_time')}\n"
                    
                    if len(available_slots) > 5:
                        result += f"   ... and {len(available_slots) - 5} more slots\n"
                else:
                    result += "   No available slots for this date.\n"
                    
                result += "\n"
                
            return result
        except Exception as e:
            logger.error(f"Error in check_appointment_availability: {str(e)}")
            return "I encountered an error retrieving appointment availability."

# Include required import for async operations
import asyncio

async def process_message_with_agent(message: str, user_info: Dict[str, Any], db=None) -> str:
    """
    Process a user message using the OpenAI agent framework.
    
    This function uses the OpenAI agent to create a more conversational experience,
    with the ability to fetch information from various tools.
    
    Args:
        message: User's message text
        user_info: Information about the user
        db: Database connection
        
    Returns:
        Agent's response
    """
    try:
        # Initialize agent tools with database connection
        tools = AgentTools(db)
        
        # Define available tools for the agent
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_clinic_info",
                    "description": "Get information about the clinic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What the user wants to know about the clinic"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_physicians",
                    "description": "Find physicians based on specialty, name, or language",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "specialty": {
                                "type": "string",
                                "description": "Physician specialty"
                            },
                            "name": {
                                "type": "string",
                                "description": "Physician name (partial match)"
                            },
                            "language": {
                                "type": "string",
                                "description": "Language spoken by the physician"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_treatments",
                    "description": "Find treatments based on specialty or name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "specialty": {
                                "type": "string",
                                "description": "Treatment specialty"
                            },
                            "name": {
                                "type": "string",
                                "description": "Treatment name (partial match)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_medical_packages",
                    "description": "Find medical packages based on name or maximum price",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Package name (partial match)"
                            },
                            "max_price": {
                                "type": "number",
                                "description": "Maximum package price"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_appointment_availability",
                    "description": "Check appointment availability for a physician or specialty",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "physician_name": {
                                "type": "string",
                                "description": "Physician name"
                            },
                            "specialty": {
                                "type": "string",
                                "description": "Physician specialty"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format"
                            }
                        }
                    }
                }
            }
        ]
        
        # Create system message with user context
        system_message = f"""
        You are an AI assistant for Valiant Clinic, a premium healthcare facility in Dubai.
        
        Your role is to help patients by providing information about the clinic, doctors, treatments, 
        and assist with appointment scheduling via WhatsApp.
        
        Current user: {user_info.get('first_name', 'Guest')} {user_info.get('last_name', '')}
        Phone number: {user_info.get('phone_number', 'Unknown')}
        
        When responding:
        1. Be professional, warm, and empathetic
        2. Provide concise but informative answers
        3. When users ask about appointments, physicians, or treatments, use the appropriate tool to fetch accurate information
        4. Remind users that for actual booking, they should use the clinic's mobile app or website
        5. For insurance verification, ask for their Emirates ID
        6. Do not make up information - only provide details retrieved from the tools
        
        The clinic offers various medical specialties including Cardiology, Urology, Orthopedics, General Practice, 
        Gastroenterology, and Plastic Surgery.
        """
        
        # Create message history
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
        
        # Get a session from the user's data or create a new one
        session = user_info.get('chatbot_session', {})
        if 'messages' in session:
            # Add previous conversation context (limit to last 5 messages)
            history = session['messages'][-10:]
            messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
        
        # Call the OpenAI API with tool definitions
        response = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=available_tools,
            tool_choice="auto"
        )
        
        # Get the response
        response_message = response.choices[0].message
        
        # Check if the agent wants to use a tool
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            # Process each tool call
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the appropriate tool function
                if function_name == "get_clinic_info":
                    tool_result = tools.get_clinic_info(**function_args)
                elif function_name == "find_physicians":
                    tool_result = tools.find_physicians(**function_args)
                elif function_name == "find_treatments":
                    tool_result = tools.find_treatments(**function_args)
                elif function_name == "find_medical_packages":
                    tool_result = tools.find_medical_packages(**function_args)
                elif function_name == "check_appointment_availability":
                    tool_result = tools.check_appointment_availability(**function_args)
                else:
                    tool_result = f"Tool {function_name} not found"
                
                # Add the tool response to the messages
                messages.append(response_message)
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(tool_result)
                })
            
            # Get the final response after tool use
            second_response = openai.chat.completions.create(
                model=MODEL,
                messages=messages
            )
            
            # Final answer after using the tools
            final_response = second_response.choices[0].message.content
        else:
            # Agent didn't need to use tools
            final_response = response_message.content
            
        # Update message history in session
        if 'messages' not in session:
            session['messages'] = []
            
        # Add the user message and assistant response to history
        session['messages'].append({"role": "user", "content": message})
        session['messages'].append({"role": "assistant", "content": final_response})
        
        # Trim history to keep only the last 10 messages
        if len(session['messages']) > 20:
            session['messages'] = session['messages'][-20:]
            
        # Return updated session and response
        user_info['chatbot_session'] = session
        
        return final_response
    except Exception as e:
        logger.error(f"OpenAI agent error: {str(e)}")
        # Return a default response if the API fails
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later or contact our clinic directly for assistance."

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
