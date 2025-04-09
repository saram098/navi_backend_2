from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from models.physician import PhysicianResponse, PhysicianFilter
from utils.auth import get_current_active_user
from db.database import get_database

router = APIRouter()

@router.get("/", response_model=List[PhysicianResponse])
async def get_physicians(
    specialty: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available_date: Optional[str] = None,
    language: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user = Depends(get_current_active_user)
):
    """
    Get a list of physicians with optional filtering.
    """
    db = get_database()
    
    # Build query based on filters
    query = {"is_active": True}
    
    if specialty:
        query["specialty"] = specialty
    
    # Price range filter
    if min_price is not None or max_price is not None:
        price_query = {}
        if min_price is not None:
            price_query["$gte"] = min_price
        if max_price is not None:
            price_query["$lte"] = max_price
        if price_query:
            query["consultation_price"] = price_query
    
    # Language filter
    if language:
        query["languages"] = language
    
    # Date availability filter requires aggregation
    pipeline = []
    
    if available_date:
        pipeline.extend([
            {"$match": query},
            {"$unwind": "$schedule"},
            {"$match": {"schedule.date": available_date}},
            # Check if at least one time slot is available
            {"$match": {"schedule.time_slots.is_available": True}}
        ])
    else:
        pipeline.append({"$match": query})
    
    # Add pagination
    pipeline.extend([
        {"$skip": skip},
        {"$limit": limit}
    ])
    
    # Execute query
    cursor = db.physicians.aggregate(pipeline)
    physicians = [doc async for doc in cursor]
    
    if not physicians:
        return []
    
    return physicians

@router.get("/{physician_id}", response_model=PhysicianResponse)
async def get_physician(
    physician_id: str,
    current_user = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific physician.
    """
    db = get_database()
    
    # Validate ObjectId
    if not ObjectId.is_valid(physician_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid physician ID format"
        )
    
    # Find physician
    physician = await db.physicians.find_one({"_id": ObjectId(physician_id)})
    
    if not physician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physician not found"
        )
    
    return physician

@router.get("/{physician_id}/availability", response_model=List[dict])
async def get_physician_availability(
    physician_id: str,
    start_date: str,
    end_date: Optional[str] = None,
    current_user = Depends(get_current_active_user)
):
    """
    Get a physician's availability within a date range.
    """
    db = get_database()
    
    # Validate ObjectId
    if not ObjectId.is_valid(physician_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid physician ID format"
        )
    
    # Set end_date to start_date if not provided
    if not end_date:
        end_date = start_date
    
    # Find physician
    physician = await db.physicians.find_one({"_id": ObjectId(physician_id)})
    
    if not physician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physician not found"
        )
    
    # Filter schedule within date range
    schedule = []
    for day in physician.get("schedule", []):
        if start_date <= day["date"] <= end_date:
            # Only include available time slots
            available_slots = [slot for slot in day["time_slots"] if slot["is_available"]]
            if available_slots:
                schedule.append({
                    "date": day["date"],
                    "time_slots": available_slots
                })
    
    return schedule

@router.get("/specialties", response_model=List[str])
async def get_specialties(
    current_user = Depends(get_current_active_user)
):
    """
    Get a list of all available physician specialties.
    """
    db = get_database()
    
    # Aggregate unique specialties
    pipeline = [
        {"$group": {"_id": "$specialty"}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor = db.physicians.aggregate(pipeline)
    specialties = [doc["_id"] async for doc in cursor]
    
    return specialties

@router.get("/languages", response_model=List[str])
async def get_languages(
    current_user = Depends(get_current_active_user)
):
    """
    Get a list of all languages spoken by physicians.
    """
    db = get_database()
    
    # Aggregate unique languages
    pipeline = [
        {"$unwind": "$languages"},
        {"$group": {"_id": "$languages"}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor = db.physicians.aggregate(pipeline)
    languages = [doc["_id"] async for doc in cursor]
    
    return languages
