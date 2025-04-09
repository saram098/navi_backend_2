from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, Optional
from bson import ObjectId
from datetime import datetime

from utils.auth import get_current_active_user
from services.stripe_service import create_payment_intent, retrieve_payment_intent
from models.appointment import PaymentStatus
from db.database import get_database

router = APIRouter()

@router.post("/create-payment-intent", response_model=Dict[str, str])
async def create_payment_intent_for_appointment(
    appointment_id: str = Body(..., embed=True),
    current_user = Depends(get_current_active_user)
):
    """
    Create a Stripe payment intent for an appointment.
    Returns client_secret needed for frontend to complete payment.
    """
    db = get_database()
    
    # Validate ObjectId
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment ID format"
        )
    
    # Get appointment
    appointment = await db.appointments.find_one({
        "_id": ObjectId(appointment_id),
        "user_id": str(current_user.id)
    })
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check if payment is already processed
    if appointment.get("payment_status") == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already processed for this appointment"
        )
    
    # Check if there's already a payment intent
    existing_payment_intent_id = appointment.get("payment_intent_id")
    if existing_payment_intent_id:
        try:
            # Retrieve existing payment intent
            payment_intent = await retrieve_payment_intent(existing_payment_intent_id)
            
            # If payment intent status is succeeded, update appointment status
            if payment_intent.get("status") == "succeeded":
                await db.appointments.update_one(
                    {"_id": ObjectId(appointment_id)},
                    {
                        "$set": {
                            "payment_status": PaymentStatus.PAID,
                            "status": "confirmed",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment already processed for this appointment"
                )
            
            # Return existing client secret if payment intent is still valid
            if payment_intent.get("status") not in ["canceled", "succeeded"]:
                return {"client_secret": payment_intent.get("client_secret")}
        except Exception:
            # If retrieval fails, create a new payment intent
            pass
    
    # Create metadata for the payment
    metadata = {
        "appointment_id": str(appointment["_id"]),
        "user_id": str(current_user.id),
        "physician_id": appointment["physician_id"],
        "date": appointment["date"],
        "time": f"{appointment['start_time']} - {appointment['end_time']}"
    }
    
    # Create payment intent
    try:
        payment_intent_data = await create_payment_intent(
            amount=appointment["amount"],
            currency="aed",
            metadata=metadata
        )
        
        # Update appointment with payment intent ID
        await db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "payment_intent_id": payment_intent_data["payment_intent_id"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"client_secret": payment_intent_data["client_secret"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment intent: {str(e)}"
        )

@router.post("/confirm-payment", response_model=Dict[str, str])
async def confirm_payment(
    payment_intent_id: str = Body(..., embed=True),
    current_user = Depends(get_current_active_user)
):
    """
    Confirm payment was processed successfully.
    This is called by the frontend after payment is complete.
    """
    db = get_database()
    
    # Retrieve payment intent to verify status
    try:
        payment_intent = await retrieve_payment_intent(payment_intent_id)
        
        # Check if payment was successful
        if payment_intent.get("status") != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment not successful. Status: {payment_intent.get('status')}"
            )
        
        # Get appointment ID from metadata
        appointment_id = payment_intent.get("metadata", {}).get("appointment_id")
        if not appointment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment intent does not have appointment reference"
            )
        
        # Update appointment payment status
        result = await db.appointments.update_one(
            {"_id": ObjectId(appointment_id), "user_id": str(current_user.id)},
            {
                "$set": {
                    "payment_status": PaymentStatus.PAID,
                    "status": "confirmed",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found or not belonging to current user"
            )
        
        return {"message": "Payment confirmed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm payment: {str(e)}"
        )

@router.get("/payment-status/{appointment_id}", response_model=Dict[str, Any])
async def get_payment_status(
    appointment_id: str,
    current_user = Depends(get_current_active_user)
):
    """
    Get the payment status of an appointment.
    """
    db = get_database()
    
    # Validate ObjectId
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment ID format"
        )
    
    # Get appointment
    appointment = await db.appointments.find_one({
        "_id": ObjectId(appointment_id),
        "user_id": str(current_user.id)
    })
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    payment_status = appointment.get("payment_status", PaymentStatus.PENDING)
    payment_intent_id = appointment.get("payment_intent_id")
    
    # If there's a payment intent, get its status from Stripe
    stripe_status = None
    if payment_intent_id:
        try:
            payment_intent = await retrieve_payment_intent(payment_intent_id)
            stripe_status = payment_intent.get("status")
            
            # If Stripe says payment succeeded but our record doesn't, update it
            if stripe_status == "succeeded" and payment_status != PaymentStatus.PAID:
                await db.appointments.update_one(
                    {"_id": ObjectId(appointment_id)},
                    {
                        "$set": {
                            "payment_status": PaymentStatus.PAID,
                            "status": "confirmed",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                payment_status = PaymentStatus.PAID
        except Exception:
            # If retrieval fails, just use our stored status
            pass
    
    return {
        "appointment_id": str(appointment["_id"]),
        "payment_status": payment_status,
        "payment_intent_id": payment_intent_id,
        "stripe_status": stripe_status,
        "amount": appointment["amount"]
    }
