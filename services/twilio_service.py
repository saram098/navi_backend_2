from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from settings.config import settings
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Twilio client
twilio_client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)

async def send_whatsapp_message(to_phone: str, message: str) -> Optional[str]:
    """
    Send a WhatsApp message using Twilio.
    
    Args:
        to_phone: Recipient phone number (format: +971xxxxxxxxx)
        message: Message content
        
    Returns:
        Message SID if successful, None otherwise
    """
    try:
        # Ensure phone number is in proper format
        if not to_phone.startswith('+'):
            to_phone = f"+{to_phone}"
            
        # Format for WhatsApp
        whatsapp_to = f"whatsapp:{to_phone}"
        whatsapp_from = f"whatsapp:{settings.TWILIO_PHONE_NUMBER}"
        
        # Send message
        twilio_message = twilio_client.messages.create(
            body=message,
            from_=whatsapp_from,
            to=whatsapp_to
        )
        
        logger.info(f"WhatsApp message sent successfully. SID: {twilio_message.sid}")
        return twilio_message.sid
    except TwilioRestException as e:
        logger.error(f"Twilio error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        return None

async def send_sms(to_phone: str, message: str) -> Optional[str]:
    """
    Send an SMS using Twilio.
    
    Args:
        to_phone: Recipient phone number (format: +971xxxxxxxxx)
        message: Message content
        
    Returns:
        Message SID if successful, None otherwise
    """
    try:
        # Ensure phone number is in proper format
        if not to_phone.startswith('+'):
            to_phone = f"+{to_phone}"
            
        # Send SMS
        twilio_message = twilio_client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        logger.info(f"SMS sent successfully. SID: {twilio_message.sid}")
        return twilio_message.sid
    except TwilioRestException as e:
        logger.error(f"Twilio error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        return None

async def validate_phone_number(phone: str) -> bool:
    """
    Validate if a phone number is in the correct format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic validation
        if not phone:
            return False
            
        # Ensure it starts with '+'
        if not phone.startswith('+'):
            return False
            
        # Check if length is reasonable (country code + number)
        if len(phone) < 8 or len(phone) > 15:
            return False
            
        # Check if all remaining characters are digits
        for char in phone[1:]:
            if not char.isdigit():
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error validating phone number: {str(e)}")
        return False
