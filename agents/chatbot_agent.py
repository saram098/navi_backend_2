import json
import logging
from typing import Dict, Any, List, Optional
from services import openai_service, twilio_service
from db.database import get_database
from models.appointment import AppointmentStatus, PaymentStatus
from datetime import datetime
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotAgent:
    """
    Agent that processes chatbot messages, determines intent, and orchestrates responses.
    This is the main entry point for chatbot functionality.
    """
    
    def __init__(self):
        self.db = get_database()
    
    async def process_message(self, phone_number: str, message: str) -> str:
        """
        Process an incoming WhatsApp message and generate a response.
        
        Args:
            phone_number: User's phone number
            message: The message content
            
        Returns:
            Response message to send back to the user
        """
        try:
            logger.info(f"Processing message from {phone_number}: {message}")
            
            # Step 1: Get or create user profile based on phone number
            user = await self._get_or_create_user(phone_number)
            
            # Step 2: Classify the intent using OpenAI
            intent_data = await openai_service.get_intent_classification(message)
            intent = intent_data.get("intent", "other")
            entities = intent_data.get("entities", {})
            
            # Step 3: Route to the appropriate handler based on intent
            if intent == "book_appointment":
                return await self._handle_book_appointment(user, message, entities)
            elif intent == "check_availability":
                return await self._handle_check_availability(user, message, entities)
            elif intent == "cancel_appointment":
                return await self._handle_cancel_appointment(user, message, entities)
            elif intent == "reschedule_appointment":
                return await self._handle_reschedule_appointment(user, message, entities)
            elif intent == "physician_info":
                return await self._handle_physician_info(user, message, entities)
            elif intent == "insurance_check":
                return await self._handle_insurance_check(user, message, entities)
            elif intent == "clinic_info":
                return await self._handle_clinic_info(user, message, entities)
            elif intent == "pricing":
                return await self._handle_pricing(user, message, entities)
            elif intent == "greeting":
                return await self._handle_greeting(user)
            else:
                return await self._handle_other(user, message)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request. Please try again later or contact our clinic directly for assistance."
    
    async def _get_or_create_user(self, phone_number: str) -> Dict[str, Any]:
        """
        Get a user by phone number or create a new one if not found.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            User document
        """
        # Ensure phone number is in correct format for lookup
        if not phone_number.startswith('+'):
            phone_number = f"+{phone_number}"
        
        # Look up user by phone number
        user = await self.db.users.find_one({"phone_number": phone_number})
        
        if user:
            return user
        
        # Create a new user if not found
        new_user = {
            "phone_number": phone_number,
            "first_name": "WhatsApp",  # Placeholder until we collect real name
            "last_name": "User",
            "created_at": datetime.utcnow(),
            "is_active": True,
            "is_verified": False,  # Will need verification later
            "chatbot_session": {},  # For storing conversation context
        }
        
        result = await self.db.users.insert_one(new_user)
        new_user["_id"] = result.inserted_id
        return new_user
    
    async def _handle_greeting(self, user: Dict[str, Any]) -> str:
        """Handle greeting messages"""
        user_name = user.get("first_name", "there")
        if user_name == "WhatsApp":
            return (
                f"Hello! Welcome to our clinic chatbot assistant. How can I help you today? "
                f"You can ask about booking appointments, physician information, "
                f"insurance checks, or clinic information."
            )
        else:
            return (
                f"Hello {user_name}! Welcome back to our clinic chatbot assistant. "
                f"How can I help you today?"
            )
    
    async def _handle_book_appointment(self, user: Dict[str, Any], message: str, entities: Dict[str, Any]) -> str:
        """Handle appointment booking intent"""
        # Check if we have enough information to book
        specialty = entities.get("specialty")
        date = entities.get("date")
        time = entities.get("time")
        
        if not specialty:
            # Store the intent in the session and ask for specialty
            await self.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"chatbot_session.intent": "book_appointment"}}
            )
            
            # Get available specialties
            specialties = await self._get_available_specialties()
            specialty_list = ", ".join(specialties[:5])  # Show first 5
            
            return (
                f"I'd be happy to help you book an appointment. "
                f"What type of specialist would you like to see? "
                f"Our available specialties include: {specialty_list}"
            )
        
        if not date:
            await self.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "chatbot_session.intent": "book_appointment",
                    "chatbot_session.specialty": specialty
                }}
            )
            
            # Get top physicians for this specialty
            physicians = await self._get_physicians_by_specialty(specialty)
            if not physicians:
                return f"I'm sorry, we don't have any {specialty} specialists available currently. Would you like to check another specialty?"
            
            # Format physician list
            physician_texts = []
            for p in physicians[:3]:  # Show top 3
                physician_texts.append(f"Dr. {p['name']} - {p['experience_years']} years experience, {p['consultation_price']} AED")
            
            physician_list = "\n".join(physician_texts)
            
            return (
                f"Great! Here are some of our {specialty} specialists:\n\n"
                f"{physician_list}\n\n"
                f"What date would you like to book your appointment? (Please specify in YYYY-MM-DD format, e.g., 2023-05-15)"
            )
        
        if not time:
            await self.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "chatbot_session.intent": "book_appointment",
                    "chatbot_session.specialty": specialty,
                    "chatbot_session.date": date
                }}
            )
            
            # Get available time slots
            time_slots = await self._get_available_time_slots(specialty, date)
            if not time_slots:
                return f"I'm sorry, there are no available appointments for {specialty} on {date}. Would you like to try another date?"
            
            # Format time slots
            time_slot_list = ", ".join([slot["start_time"] for slot in time_slots[:6]])  # Show first 6
            
            return (
                f"What time would you prefer for your {specialty} appointment on {date}? "
                f"Available times: {time_slot_list}"
            )
        
        # If we have all the information, proceed with booking
        # This would typically involve more validation and confirmation steps
        # For now, we'll provide a simple confirmation and next steps
        
        await self.db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "chatbot_session.intent": None,  # Clear session
                "chatbot_session.specialty": None,
                "chatbot_session.date": None
            }}
        )
        
        return (
            f"Great! I've started the process to book your {specialty} appointment on {date} at {time}. "
            f"To complete the booking, we'll need a few more details. "
            f"Would you like me to help you check your insurance coverage first? "
            f"Just reply with 'yes' or send your Emirates ID number if you'd like to proceed with the insurance check."
        )
    
    async def _handle_check_availability(self, user: Dict[str, Any], message: str, entities: Dict[str, Any]) -> str:
        """Handle availability checking intent"""
        specialty = entities.get("specialty")
        date = entities.get("date")
        
        if not specialty:
            # Get available specialties
            specialties = await self._get_available_specialties()
            specialty_list = ", ".join(specialties[:5])  # Show first 5
            
            return (
                f"I can help you check physician availability. "
                f"Which specialty are you interested in? "
                f"Our available specialties include: {specialty_list}"
            )
        
        if not date:
            return (
                f"For which date would you like to check {specialty} appointments? "
                f"Please specify in YYYY-MM-DD format, e.g., 2023-05-15"
            )
        
        # Get available time slots for the specialty and date
        time_slots = await self._get_available_time_slots(specialty, date)
        
        if not time_slots:
            # Get next available dates
            next_dates = await self._get_next_available_dates(specialty, date, 3)
            
            if not next_dates:
                return f"I'm sorry, there are no available appointments for {specialty} in the near future. Please contact our clinic directly for assistance."
            
            next_dates_str = ", ".join(next_dates)
            
            return (
                f"I'm sorry, there are no available appointments for {specialty} on {date}. "
                f"The next available dates are: {next_dates_str}. "
                f"Would you like to check availability for any of these dates?"
            )
        
        # Format time slots
        time_slot_texts = []
        for slot in time_slots[:8]:  # Show first 8
            physician_name = slot.get("physician_name", "")
            time_slot_texts.append(f"{slot['start_time']} - {slot['end_time']} (Dr. {physician_name})")
        
        time_slot_list = "\n".join(time_slot_texts)
        
        return (
            f"Here are the available appointments for {specialty} on {date}:\n\n"
            f"{time_slot_list}\n\n"
            f"Would you like to book any of these appointments? Just reply with the time you prefer."
        )
    
    async def _handle_cancel_appointment(self, user: Dict[str, Any], message: str, entities: Dict[str, Any]) -> str:
        """Handle appointment cancellation intent"""
        # Get user's upcoming appointments
        appointments = await self._get_user_appointments(user["_id"], status=AppointmentStatus.CONFIRMED)
        
        if not appointments:
            return "You don't have any upcoming appointments to cancel. Would you like to book a new appointment instead?"
        
        # Format appointments
        appointment_texts = []
        for i, appt in enumerate(appointments, 1):
            physician_name = appt.get("physician_name", "Unknown")
            appointment_texts.append(
                f"{i}. {appt['date']} at {appt['start_time']} with Dr. {physician_name} ({appt['specialty']})"
            )
        
        appointment_list = "\n".join(appointment_texts)
        
        # Store the list in session for reference when user selects one
        await self.db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "chatbot_session.intent": "cancel_appointment",
                "chatbot_session.appointments": [str(appt["_id"]) for appt in appointments]
            }}
        )
        
        return (
            f"Here are your upcoming appointments:\n\n"
            f"{appointment_list}\n\n"
            f"Which appointment would you like to cancel? Please reply with the number."
        )
    
    async def _handle_reschedule_appointment(self, user: Dict[str, Any], message: str, entities: Dict[str, Any]) -> str:
        """Handle appointment rescheduling intent"""
        # Similar to cancel but with reschedule options
        appointments = await self._get_user_appointments(user["_id"], status=AppointmentStatus.CONFIRMED)
        
        if not appointments:
            return "You don't have any upcoming appointments to reschedule. Would you like to book a new appointment instead?"
        
        # Format appointments
        appointment_texts = []
        for i, appt in enumerate(appointments, 1):
            physician_name = appt.get("physician_name", "Unknown")
            appointment_texts.append(
                f"{i}. {appt['date']} at {appt['start_time']} with Dr. {physician_name} ({appt['specialty']})"
            )
        
        appointment_list = "\n".join(appointment_texts)
        
        # Store the list in session for reference when user selects one
        await self.db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "chatbot_session.intent": "reschedule_appointment",
                "chatbot_session.appointments": [str(appt["_id"]) for appt in appointments]
            }}
        )
        
        return (
            f"Here are your upcoming appointments:\n\n"
            f"{appointment_list}\n\n"
            f"Which appointment would you like to reschedule? Please reply with the number."
        )
    
    async def _handle_physician_info(self, user: Dict[str, Any], message: str, entities: Dict[str, Any]) -> str:
        """Handle physician information intent"""
        specialty = entities.get("specialty")
        physician_name = entities.get("physician_name")
        
        if not specialty and not physician_name:
            # Get available specialties
            specialties = await self._get_available_specialties()
            specialty_list = ", ".join(specialties[:5])  # Show first 5
            
            return (
                f"I can provide information about our physicians. "
                f"Are you looking for a specific specialty? Our available specialties include: {specialty_list}. "
                f"Or if you know the doctor's name, you can mention that as well."
            )
        
        # If we have a physician name, try to find that physician
        if physician_name:
            physician = await self._get_physician_by_name(physician_name)
            if physician:
                return await self._format_physician_details(physician)
        
        # If we have a specialty, get physicians in that specialty
        if specialty:
            physicians = await self._get_physicians_by_specialty(specialty)
            if not physicians:
                return f"I'm sorry, we don't have any {specialty} specialists available currently. Would you like to check another specialty?"
            
            # Use OpenAI to generate recommendations based on the original query
            recommendations = await openai_service.generate_physician_recommendations(message, physicians)
            
            # If we couldn't get recommendations, fall back to a simple list
            if not recommendations or not recommendations.get("recommendations"):
                return await self._format_physician_list(physicians)
            
            return await self._format_physician_recommendations(recommendations, physicians)
        
        # If we couldn't find anything specific
        return (
            f"I'm sorry, I couldn't find specific information about that. "
            f"Could you please clarify which physician or specialty you're interested in?"
        )
    
    async def _handle_insurance_check(self, user: Dict[str, Any], message: str, entities: Dict[str, Any]) -> str:
        """Handle insurance check intent"""
        emirates_id = entities.get("emirates_id")
        
        # Check if message contains something that looks like an Emirates ID
        if not emirates_id:
            # Look for patterns like XXX-XXXX-XXXXXXX-X or numeric sequences
            import re
            id_patterns = [
                r'\d{3}-\d{4}-\d{7}-\d{1}',  # Formatted ID
                r'\d{15}',                    # 15-digit number
                r'\d{3}\s?\d{4}\s?\d{7}\s?\d{1}'  # Spaced digits
            ]
            
            for pattern in id_patterns:
                match = re.search(pattern, message)
                if match:
                    emirates_id = match.group(0)
                    break
        
        if not emirates_id:
            if user.get("emirates_id"):
                emirates_id = user["emirates_id"]
            else:
                return (
                    f"To check your insurance coverage, I'll need your Emirates ID number. "
                    f"Please provide your Emirates ID in the format XXX-XXXX-XXXXXXX-X"
                )
        
        # In a real system, we'd call an external service to verify insurance
        # For now, we'll simulate this with our mock service
        from services.insurance_service import verify_insurance
        result = await verify_insurance(emirates_id)
        
        # Store the Emirates ID in the user profile if we don't have it yet
        if not user.get("emirates_id"):
            await self.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"emirates_id": emirates_id}}
            )
        
        # Format the response based on the verification result
        if result.status == "active":
            coverage_details = result.coverage_details
            return (
                f"Good news! Your insurance is active with {result.provider}.\n\n"
                f"Plan: {coverage_details.get('plan_name', 'N/A')}\n"
                f"Coverage type: {coverage_details.get('coverage_type', 'N/A')}\n"
                f"Member ID: {coverage_details.get('member_id', 'N/A')}\n"
                f"Expiry date: {coverage_details.get('expiry_date', 'N/A')}\n\n"
                f"Would you like to book an appointment now?"
            )
        elif result.status == "expired":
            return (
                f"Your insurance with {result.provider} has expired on {result.coverage_details.get('expiry_date', 'unknown date')}. "
                f"Please contact your insurance provider to renew your coverage. "
                f"Would you like to book a self-pay appointment instead?"
            )
        elif result.status == "inactive":
            reason = result.coverage_details.get('reason', 'unknown reason')
            return (
                f"Your insurance with {result.provider} is currently inactive due to: {reason}. "
                f"Please contact your insurance provider to resolve this issue. "
                f"Would you like to book a self-pay appointment instead?"
            )
        elif result.status == "not_found":
            return (
                f"I couldn't find any insurance records associated with the Emirates ID you provided. "
                f"If you believe this is an error, please contact our clinic directly or your insurance provider. "
                f"Would you like to book a self-pay appointment?"
            )
        else:
            return (
                f"I encountered an error while checking your insurance status: {result.error_message}. "
                f"Please try again later or contact our clinic directly for assistance."
            )
    
    async def _handle_clinic_info(self, user: Dict[str, Any], message: str, entities: Dict[str, Any]) -> str:
        """Handle clinic information intent"""
        clinic_info = await self.db.clinic_info.find_one()
        
        if not clinic_info:
            return (
                "Our clinic provides comprehensive healthcare services with a team of experienced physicians. "
                "For specific details about our location and contact information, please call our reception at +971-X-XXX-XXXX."
            )
        
        # Format working hours
        working_hours = clinic_info.get("working_hours", {})
        hours_text = "\n".join([f"{day}: {hours}" for day, hours in working_hours.items()])
        
        return (
            f"{clinic_info.get('name', 'Our Clinic')}\n\n"
            f"{clinic_info.get('description', '')}\n\n"
            f"Address: {clinic_info.get('address', 'N/A')}\n"
            f"Phone: {clinic_info.get('phone', 'N/A')}\n"
            f"Email: {clinic_info.get('email', 'N/A')}\n"
            f"Website: {clinic_info.get('website', 'N/A')}\n\n"
            f"Working Hours:\n{hours_text}\n\n"
            f"How can I assist you further? Would you like to book an appointment or check physician availability?"
        )
    
    async def _handle_pricing(self, user: Dict[str, Any], message: str, entities: Dict[str, Any]) -> str:
        """Handle pricing information intent"""
        specialty = entities.get("specialty")
        
        if not specialty:
            # Get price ranges by specialty
            price_info = await self._get_specialty_price_ranges()
            
            price_text = "\n".join([f"{spec}: {prices['min']} - {prices['max']} AED" for spec, prices in price_info.items()])
            
            return (
                f"Here are our consultation price ranges by specialty:\n\n"
                f"{price_text}\n\n"
                f"Would you like more detailed pricing for a specific specialty?"
            )
        
        # Get physicians in that specialty with prices
        physicians = await self._get_physicians_by_specialty(specialty)
        
        if not physicians:
            return f"I'm sorry, we don't have any {specialty} specialists available currently. Would you like to check pricing for another specialty?"
        
        # Sort by price
        physicians.sort(key=lambda x: x.get('consultation_price', 0))
        
        # Format physician prices
        physician_texts = []
        for p in physicians[:5]:  # Show top 5
            physician_texts.append(f"Dr. {p['name']} - {p['consultation_price']} AED")
        
        physician_list = "\n".join(physician_texts)
        
        return (
            f"Here are the consultation prices for our {specialty} specialists:\n\n"
            f"{physician_list}\n\n"
            f"Would you like to book an appointment with one of these physicians?"
        )
    
    async def _handle_other(self, user: Dict[str, Any], message: str) -> str:
        """Handle general queries or fallback"""
        # Check if user is in the middle of a conversation flow
        session = user.get("chatbot_session", {})
        intent = session.get("intent")
        
        if intent:
            # User is in the middle of another intent flow
            return (
                f"I notice we were discussing something else. "
                f"Would you like to continue with that or start a new conversation? "
                f"You can say 'new conversation' to start fresh."
            )
        
        # Use OpenAI to generate a general response
        prompt = f"""
        You are a medical clinic assistant. The user has sent this message: "{message}"
        
        It doesn't clearly match any of our predefined intents. Respond helpfully and offer guidance
        on how they can interact with the clinic chatbot. Suggest they might want to:
        1. Book an appointment
        2. Check physician availability
        3. Learn about our physicians
        4. Check insurance coverage
        5. Get clinic information
        
        Keep your response friendly and concise.
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful medical clinic chatbot assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating fallback response: {str(e)}")
            return (
                f"I'm not sure I understand your request. Here are some things I can help you with:\n\n"
                f"- Book a doctor appointment\n"
                f"- Check physician availability\n"
                f"- Get information about our physicians\n"
                f"- Check your insurance coverage\n"
                f"- Provide clinic information\n\n"
                f"How can I assist you today?"
            )
    
    # Helper methods for data retrieval
    async def _get_available_specialties(self) -> List[str]:
        """Get list of available specialties"""
        pipeline = [
            {"$group": {"_id": "$specialty"}},
            {"$sort": {"_id": 1}}
        ]
        
        cursor = self.db.physicians.aggregate(pipeline)
        specialties = [doc["_id"] async for doc in cursor]
        return specialties
    
    async def _get_physicians_by_specialty(self, specialty: str) -> List[Dict[str, Any]]:
        """Get physicians by specialty"""
        cursor = self.db.physicians.find({"specialty": specialty, "is_active": True})
        physicians = [doc async for doc in cursor]
        return physicians
    
    async def _get_physician_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get physician by name (partial match)"""
        query = {"name": {"$regex": name, "$options": "i"}, "is_active": True}
        physician = await self.db.physicians.find_one(query)
        return physician
    
    async def _get_available_time_slots(self, specialty: str, date: str) -> List[Dict[str, Any]]:
        """Get available time slots for a specialty and date"""
        pipeline = [
            {"$match": {"specialty": specialty, "is_active": True}},
            {"$unwind": "$schedule"},
            {"$match": {"schedule.date": date}},
            {"$unwind": "$schedule.time_slots"},
            {"$match": {"schedule.time_slots.is_available": True}},
            {"$project": {
                "physician_id": "$_id",
                "physician_name": "$name",
                "start_time": "$schedule.time_slots.start_time",
                "end_time": "$schedule.time_slots.end_time",
                "consultation_price": 1
            }}
        ]
        
        cursor = self.db.physicians.aggregate(pipeline)
        time_slots = [slot async for slot in cursor]
        return time_slots
    
    async def _get_next_available_dates(self, specialty: str, from_date: str, limit: int) -> List[str]:
        """Get next available dates after the given date"""
        pipeline = [
            {"$match": {"specialty": specialty, "is_active": True}},
            {"$unwind": "$schedule"},
            {"$match": {"schedule.date": {"$gt": from_date}}},
            {"$group": {"_id": "$schedule.date"}},
            {"$sort": {"_id": 1}},
            {"$limit": limit}
        ]
        
        cursor = self.db.physicians.aggregate(pipeline)
        dates = [doc["_id"] async for doc in cursor]
        return dates
    
    async def _get_user_appointments(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user's appointments with optional status filter"""
        match_query = {"user_id": str(user_id)}
        if status:
            match_query["status"] = status
        
        pipeline = [
            {"$match": match_query},
            {"$lookup": {
                "from": "physicians",
                "localField": "physician_id",
                "foreignField": "_id",
                "as": "physician"
            }},
            {"$unwind": {"path": "$physician", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 1,
                "date": 1,
                "start_time": 1,
                "end_time": 1,
                "status": 1,
                "payment_status": 1,
                "amount": 1,
                "physician_name": "$physician.name",
                "specialty": "$physician.specialty"
            }},
            {"$sort": {"date": 1, "start_time": 1}}
        ]
        
        cursor = self.db.appointments.aggregate(pipeline)
        appointments = [appt async for appt in cursor]
        return appointments
    
    async def _get_specialty_price_ranges(self) -> Dict[str, Dict[str, float]]:
        """Get price ranges by specialty"""
        pipeline = [
            {"$group": {
                "_id": "$specialty",
                "min": {"$min": "$consultation_price"},
                "max": {"$max": "$consultation_price"},
                "avg": {"$avg": "$consultation_price"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        cursor = self.db.physicians.aggregate(pipeline)
        results = {}
        async for doc in cursor:
            results[doc["_id"]] = {
                "min": doc["min"],
                "max": doc["max"],
                "avg": doc["avg"]
            }
        return results
    
    async def _format_physician_details(self, physician: Dict[str, Any]) -> str:
        """Format physician details for display"""
        return (
            f"Dr. {physician['name']}\n\n"
            f"Specialty: {physician['specialty']}\n"
            f"Qualification: {physician['qualification']}\n"
            f"Experience: {physician['experience_years']} years\n"
            f"Languages: {', '.join(physician['languages'])}\n"
            f"Consultation fee: {physician['consultation_price']} AED\n\n"
            f"{physician.get('bio', '')}\n\n"
            f"Would you like to book an appointment with Dr. {physician['name']}?"
        )
    
    async def _format_physician_list(self, physicians: List[Dict[str, Any]]) -> str:
        """Format a list of physicians for display"""
        physician_texts = []
        for i, p in enumerate(physicians[:5], 1):  # Show top 5
            physician_texts.append(
                f"{i}. Dr. {p['name']} - {p['specialty']}\n"
                f"   Experience: {p['experience_years']} years\n"
                f"   Fee: {p['consultation_price']} AED"
            )
        
        physician_list = "\n\n".join(physician_texts)
        
        return (
            f"Here are some physicians that match your criteria:\n\n"
            f"{physician_list}\n\n"
            f"Would you like more details about any of these physicians? Just reply with the number."
        )
    
    async def _format_physician_recommendations(self, recommendations: Dict[str, Any], physicians: List[Dict[str, Any]]) -> str:
        """Format physician recommendations from OpenAI"""
        physician_map = {str(p["_id"]): p for p in physicians}
        
        rec_texts = []
        for rec in recommendations.get("recommendations", [])[:3]:  # Show top 3
            rec_id = rec.get("id") if isinstance(rec, dict) else rec
            explanation = rec.get("explanation", "") if isinstance(rec, dict) else ""
            
            if rec_id in physician_map:
                p = physician_map[rec_id]
                rec_texts.append(
                    f"Dr. {p['name']} - {p['specialty']}\n"
                    f"Experience: {p['experience_years']} years\n"
                    f"Fee: {p['consultation_price']} AED\n"
                    f"{explanation}"
                )
        
        if not rec_texts:
            # Fallback to simple list if no recommendations matched
            return await self._format_physician_list(physicians)
        
        rec_list = "\n\n".join(rec_texts)
        
        follow_up = recommendations.get("follow_up_questions", [])
        follow_up_text = ""
        if follow_up:
            follow_up_text = "\n\n" + "You might want to ask:\n- " + "\n- ".join(follow_up[:3])
        
        return (
            f"Based on your query, here are the most suitable physicians:\n\n"
            f"{rec_list}"
            f"{follow_up_text}\n\n"
            f"Would you like to book an appointment with one of these physicians?"
        )

# Create a singleton instance
chatbot_agent = ChatbotAgent()
