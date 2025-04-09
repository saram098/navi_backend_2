from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from services import twilio_service
from agents.chatbot_agent import chatbot_agent
from db.database import get_database
from utils.auth import get_current_active_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook", status_code=200)
async def twilio_webhook(request: Request):
    """
    Webhook endpoint for Twilio WhatsApp messages.
    
    This endpoint receives incoming WhatsApp messages from Twilio,
    processes them using the chatbot agent, and sends back a response.
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        
        # Extract relevant information
        message_body = form_data.get("Body", "")
        from_number = form_data.get("From", "")
        
        # Clean phone number format (remove 'whatsapp:' prefix if present)
        if from_number.startswith("whatsapp:"):
            from_number = from_number[9:]  # Remove 'whatsapp:' prefix
        
        logger.info(f"Received WhatsApp message from {from_number}: {message_body}")
        
        # Process message with chatbot agent
        response = await chatbot_agent.process_message(from_number, message_body)
        
        # Log conversation
        db = get_database()
        await db.chatbot_conversations.insert_one({
            "phone_number": from_number,
            "message": message_body,
            "response": response,
            "timestamp": datetime.utcnow()
        })
        
        # Return TwiML response
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>{response}</Message>
        </Response>
        """
        
        return twiml_response
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # Always return a 200 response to Twilio even if there's an error
        # to prevent Twilio from retrying
        return """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>Sorry, I encountered an error processing your request.</Message>
        </Response>
        """

@router.post("/send", response_model=Dict[str, Any])
async def send_whatsapp_message(
    phone_number: str = Body(...),
    message: str = Body(...),
    current_user = Depends(get_current_active_user)
):
    """
    Send a WhatsApp message to a user.
    This endpoint can be used by staff to initiate conversations with users.
    """
    try:
        # Validate phone number
        if not await twilio_service.validate_phone_number(phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format. Must include country code (e.g., +971xxxxxxxxx)"
            )
        
        # Send WhatsApp message
        message_sid = await twilio_service.send_whatsapp_message(phone_number, message)
        
        if not message_sid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send WhatsApp message"
            )
        
        # Log outgoing message
        db = get_database()
        await db.chatbot_conversations.insert_one({
            "phone_number": phone_number,
            "message": f"[OUTGOING] {message}",
            "message_sid": message_sid,
            "sent_by_user_id": str(current_user.id),
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": True,
            "message_sid": message_sid,
            "phone_number": phone_number
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send WhatsApp message: {str(e)}"
        )

@router.post("/send-sms", response_model=Dict[str, Any])
async def send_sms_message(
    phone_number: str = Body(...),
    message: str = Body(...),
    current_user = Depends(get_current_active_user)
):
    """
    Send an SMS message to a user.
    This endpoint can be used by staff when WhatsApp is not available.
    """
    try:
        # Validate phone number
        if not await twilio_service.validate_phone_number(phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format. Must include country code (e.g., +971xxxxxxxxx)"
            )
        
        # Send SMS message
        message_sid = await twilio_service.send_sms(phone_number, message)
        
        if not message_sid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send SMS message"
            )
        
        # Log outgoing message
        db = get_database()
        await db.chatbot_conversations.insert_one({
            "phone_number": phone_number,
            "message": f"[OUTGOING SMS] {message}",
            "message_sid": message_sid,
            "sent_by_user_id": str(current_user.id),
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": True,
            "message_sid": message_sid,
            "phone_number": phone_number
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending SMS message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send SMS message: {str(e)}"
        )

@router.get("/conversations/{phone_number}", response_model=Dict[str, Any])
async def get_conversation_history(
    phone_number: str,
    limit: int = 50,
    current_user = Depends(get_current_active_user)
):
    """
    Get conversation history with a specific user.
    """
    db = get_database()
    
    # Clean phone number format
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"
    
    # Query conversation history
    cursor = db.chatbot_conversations.find(
        {"phone_number": phone_number}
    ).sort("timestamp", -1).limit(limit)
    
    conversations = []
    async for doc in cursor:
        # Convert ObjectId to string for JSON serialization
        doc["_id"] = str(doc["_id"])
        conversations.append(doc)
    
    # Reverse to get chronological order
    conversations.reverse()
    
    # Get user profile if available
    user_profile = await db.users.find_one({"phone_number": phone_number})
    user_info = None
    
    if user_profile:
        user_info = {
            "user_id": str(user_profile["_id"]),
            "name": f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip(),
            "email": user_profile.get("email"),
            "insurance_status": user_profile.get("insurance_status")
        }
    
    return {
        "phone_number": phone_number,
        "conversations": conversations,
        "user_info": user_info
    }

@router.post("/test-agent", response_model=Dict[str, str])
async def test_chatbot_agent(
    message: str = Body(..., embed=True),
    current_user = Depends(get_current_active_user)
):
    """
    Test the chatbot agent with a message.
    This endpoint allows testing without sending real WhatsApp messages.
    """
    try:
        # Use a test phone number
        test_phone = f"+test{str(current_user.id)[-8:]}"
        
        # Process message with chatbot agent
        response = await chatbot_agent.process_message(test_phone, message)
        
        return {
            "message": message,
            "response": response
        }
    except Exception as e:
        logger.error(f"Error testing chatbot agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )
