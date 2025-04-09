from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from models.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate, AppointmentStatus, PaymentStatus
from utils.auth import get_current_active_user
from db.database import get_database
from services.stripe_service import create_payment_intent, cancel_payment_intent

router = APIRouter()

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user = Depends(get_current_active_user)
):
    """
    Book a new appointment with a physician.
    """
    db = get_database()
    
    # Validate physician ID
    if not ObjectId.is_valid(appointment_data.physician_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid physician ID format"
        )
    
    # Check if physician exists
    physician = await db.physicians.find_one({"_id": ObjectId(appointment_data.physician_id)})
    if not physician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physician not found"
        )
    
    # Validate time slot availability
    available = False
    for day in physician.get("schedule", []):
        if day["date"] == appointment_data.date:
            for slot in day["time_slots"]:
                if (slot["start_time"] == appointment_data.start_time and 
                    slot["end_time"] == appointment_data.end_time and 
                    slot["is_available"]):
                    available = True
                    break
            break
    
    if not available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected time slot is not available"
        )
    
    # Create appointment
    appointment = {
        "user_id": str(current_user.id),
        "physician_id": appointment_data.physician_id,
        "date": appointment_data.date,
        "start_time": appointment_data.start_time,
        "end_time": appointment_data.end_time,
        "notes": appointment_data.notes,
        "status": AppointmentStatus.PENDING,
        "payment_status": PaymentStatus.PENDING,
        "amount": physician["consultation_price"],
        "created_at": datetime.utcnow()
    }
    
    # Insert appointment into database
    result = await db.appointments.insert_one(appointment)
    appointment["_id"] = result.inserted_id
    
    # Update physician's schedule to mark the time slot as unavailable
    await db.physicians.update_one(
        {
            "_id": ObjectId(appointment_data.physician_id),
            "schedule.date": appointment_data.date,
            "schedule.time_slots.start_time": appointment_data.start_time,
            "schedule.time_slots.end_time": appointment_data.end_time
        },
        {"$set": {"schedule.$[day].time_slots.$[slot].is_available": False}},
        array_filters=[
            {"day.date": appointment_data.date},
            {
                "slot.start_time": appointment_data.start_time,
                "slot.end_time": appointment_data.end_time
            }
        ]
    )
    
    # Add physician name for response
    appointment["physician_name"] = physician["name"]
    
    return appointment

@router.get("/", response_model=List[AppointmentResponse])
async def get_user_appointments(
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user = Depends(get_current_active_user)
):
    """
    Get a list of the current user's appointments.
    """
    db = get_database()
    
    # Build query
    query = {"user_id": str(current_user.id)}
    
    if status:
        if status not in [s.value for s in AppointmentStatus]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in AppointmentStatus])}"
            )
        query["status"] = status
    
    # Date range filter
    if from_date or to_date:
        date_query = {}
        if from_date:
            date_query["$gte"] = from_date
        if to_date:
            date_query["$lte"] = to_date
        if date_query:
            query["date"] = date_query
    
    # Create aggregation pipeline for joining physician data
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "physicians",
            "localField": "physician_id",
            "foreignField": "_id",
            "as": "physician"
        }},
        {"$unwind": {"path": "$physician", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1,
            "user_id": 1,
            "physician_id": 1,
            "physician_name": "$physician.name",
            "date": 1,
            "start_time": 1,
            "end_time": 1,
            "notes": 1,
            "status": 1,
            "payment_status": 1,
            "payment_intent_id": 1,
            "amount": 1,
            "created_at": 1,
            "updated_at": 1
        }},
        {"$sort": {"date": 1, "start_time": 1}},
        {"$skip": skip},
        {"$limit": limit}
    ]
    
    # Execute query
    cursor = db.appointments.aggregate(pipeline)
    appointments = [doc async for doc in cursor]
    
    return appointments

@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    current_user = Depends(get_current_active_user)
):
    """
    Get details of a specific appointment.
    """
    db = get_database()
    
    # Validate ObjectId
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment ID format"
        )
    
    # Create aggregation pipeline for joining physician data
    pipeline = [
        {"$match": {"_id": ObjectId(appointment_id), "user_id": str(current_user.id)}},
        {"$lookup": {
            "from": "physicians",
            "localField": "physician_id",
            "foreignField": "_id",
            "as": "physician"
        }},
        {"$unwind": {"path": "$physician", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1,
            "user_id": 1,
            "physician_id": 1,
            "physician_name": "$physician.name",
            "date": 1,
            "start_time": 1,
            "end_time": 1,
            "notes": 1,
            "status": 1,
            "payment_status": 1,
            "payment_intent_id": 1,
            "amount": 1,
            "created_at": 1,
            "updated_at": 1
        }}
    ]
    
    # Execute query
    cursor = db.appointments.aggregate(pipeline)
    appointments = [doc async for doc in cursor]
    
    if not appointments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    return appointments[0]

@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    update_data: AppointmentUpdate,
    current_user = Depends(get_current_active_user)
):
    """
    Update an existing appointment.
    """
    db = get_database()
    
    # Validate ObjectId
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment ID format"
        )
    
    # Get existing appointment
    appointment = await db.appointments.find_one({
        "_id": ObjectId(appointment_id),
        "user_id": str(current_user.id)
    })
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Prepare update data
    update_fields = {}
    if update_data.status is not None:
        update_fields["status"] = update_data.status
    if update_data.payment_status is not None:
        update_fields["payment_status"] = update_data.payment_status
    if update_data.notes is not None:
        update_fields["notes"] = update_data.notes
    
    if update_fields:
        update_fields["updated_at"] = datetime.utcnow()
        
        # Update appointment
        await db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": update_fields}
        )
    
    # Get updated appointment with physician details
    pipeline = [
        {"$match": {"_id": ObjectId(appointment_id)}},
        {"$lookup": {
            "from": "physicians",
            "localField": "physician_id",
            "foreignField": "_id",
            "as": "physician"
        }},
        {"$unwind": {"path": "$physician", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1,
            "user_id": 1,
            "physician_id": 1,
            "physician_name": "$physician.name",
            "date": 1,
            "start_time": 1,
            "end_time": 1,
            "notes": 1,
            "status": 1,
            "payment_status": 1,
            "payment_intent_id": 1,
            "amount": 1,
            "created_at": 1,
            "updated_at": 1
        }}
    ]
    
    cursor = db.appointments.aggregate(pipeline)
    updated_appointments = [doc async for doc in cursor]
    
    if not updated_appointments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found after update"
        )
    
    return updated_appointments[0]

@router.delete("/{appointment_id}", response_model=Dict[str, str])
async def cancel_appointment(
    appointment_id: str,
    current_user = Depends(get_current_active_user)
):
    """
    Cancel an appointment.
    """
    db = get_database()
    
    # Validate ObjectId
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment ID format"
        )
    
    # Get existing appointment
    appointment = await db.appointments.find_one({
        "_id": ObjectId(appointment_id),
        "user_id": str(current_user.id)
    })
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check if appointment can be cancelled
    if appointment["status"] in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel appointment with status: {appointment['status']}"
        )
    
    # Update appointment status
    await db.appointments.update_one(
        {"_id": ObjectId(appointment_id)},
        {
            "$set": {
                "status": AppointmentStatus.CANCELLED,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # If there's a payment intent, cancel it
    payment_intent_id = appointment.get("payment_intent_id")
    if payment_intent_id:
        try:
            await cancel_payment_intent(payment_intent_id)
            
            # Update payment status
            await db.appointments.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$set": {"payment_status": PaymentStatus.REFUNDED}}
            )
        except Exception as e:
            # Log the error but continue with cancellation
            print(f"Error cancelling payment intent: {str(e)}")
    
    # Update physician's schedule to mark the time slot as available again
    try:
        await db.physicians.update_one(
            {
                "_id": ObjectId(appointment["physician_id"]),
                "schedule.date": appointment["date"],
                "schedule.time_slots.start_time": appointment["start_time"],
                "schedule.time_slots.end_time": appointment["end_time"]
            },
            {"$set": {"schedule.$[day].time_slots.$[slot].is_available": True}},
            array_filters=[
                {"day.date": appointment["date"]},
                {
                    "slot.start_time": appointment["start_time"],
                    "slot.end_time": appointment["end_time"]
                }
            ]
        )
    except Exception as e:
        # Log the error but continue with cancellation
        print(f"Error updating physician schedule: {str(e)}")
    
    return {"message": "Appointment cancelled successfully"}
