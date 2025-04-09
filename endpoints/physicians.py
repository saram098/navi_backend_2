from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from db.database import get_database
from models.physician import PhysicianCreate, PhysicianResponse, PhysicianDB, PhysicianUpdate, PhysicianFilter
from services.auth_service import get_current_active_user

router = APIRouter(
    prefix="/physicians",
    tags=["physicians"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=PhysicianResponse)
async def create_physician(
    physician_data: PhysicianCreate,
    current_user = Depends(get_current_active_user)
):
    """
    Add a new physician to the clinic.
    This endpoint requires admin privileges.
    """
    db = get_database()
    
    # Check if a physician with the same name already exists
    existing = await db.physicians.find_one({"name": physician_data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Physician with this name already exists")
    
    # Prepare the physician data for insertion
    physician_dict = physician_data.dict()
    physician_dict["created_at"] = datetime.utcnow()
    physician_dict["is_active"] = True
    
    # Insert the new physician
    result = await db.physicians.insert_one(physician_dict)
    
    # Retrieve the created physician
    created_physician = await db.physicians.find_one({"_id": result.inserted_id})
    
    # Convert the ObjectId to string
    created_physician["_id"] = str(created_physician["_id"])
    
    return created_physician

@router.get("/", response_model=List[PhysicianResponse])
async def get_physicians(
    specialty: Optional[str] = None,
    name: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    language: Optional[str] = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get a list of physicians, with optional filtering.
    """
    db = get_database()
    
    # Build the query
    query = {}
    
    if active_only:
        query["is_active"] = True
    
    if specialty:
        query["specialty"] = specialty
    
    if name:
        query["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive search
    
    if min_price is not None:
        query["consultation_price"] = query.get("consultation_price", {})
        query["consultation_price"]["$gte"] = min_price
    
    if max_price is not None:
        query["consultation_price"] = query.get("consultation_price", {})
        query["consultation_price"]["$lte"] = max_price
    
    if language:
        query["languages"] = language
    
    # Execute the query
    physicians = await db.physicians.find(query).skip(skip).limit(limit).to_list(length=limit)
    
    # Convert ObjectId to string for each physician
    for physician in physicians:
        physician["_id"] = str(physician["_id"])
    
    return physicians

@router.get("/{physician_id}", response_model=PhysicianResponse)
async def get_physician(physician_id: str):
    """
    Get details of a specific physician.
    """
    db = get_database()
    
    # Check if the physician ID is valid
    if not ObjectId.is_valid(physician_id):
        raise HTTPException(status_code=400, detail="Invalid physician ID")
    
    # Retrieve the physician
    physician = await db.physicians.find_one({"_id": ObjectId(physician_id)})
    if not physician:
        raise HTTPException(status_code=404, detail="Physician not found")
    
    # Convert ObjectId to string
    physician["_id"] = str(physician["_id"])
    
    return physician

@router.put("/{physician_id}", response_model=PhysicianResponse)
async def update_physician(
    physician_id: str,
    update_data: PhysicianUpdate,
    current_user = Depends(get_current_active_user)
):
    """
    Update an existing physician.
    This endpoint requires admin privileges.
    """
    db = get_database()
    
    # Check if the physician ID is valid
    if not ObjectId.is_valid(physician_id):
        raise HTTPException(status_code=400, detail="Invalid physician ID")
    
    # Check if the physician exists
    physician = await db.physicians.find_one({"_id": ObjectId(physician_id)})
    if not physician:
        raise HTTPException(status_code=404, detail="Physician not found")
    
    # Filter out None values
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    # Add updated_at timestamp
    update_dict["updated_at"] = datetime.utcnow()
    
    # Update the physician
    await db.physicians.update_one(
        {"_id": ObjectId(physician_id)},
        {"$set": update_dict}
    )
    
    # Retrieve the updated physician
    updated_physician = await db.physicians.find_one({"_id": ObjectId(physician_id)})
    
    # Convert ObjectId to string
    updated_physician["_id"] = str(updated_physician["_id"])
    
    return updated_physician

@router.delete("/{physician_id}", response_model=dict)
async def delete_physician(
    physician_id: str,
    current_user = Depends(get_current_active_user)
):
    """
    Remove a physician (sets is_active to False).
    This endpoint requires admin privileges.
    """
    db = get_database()
    
    # Check if the physician ID is valid
    if not ObjectId.is_valid(physician_id):
        raise HTTPException(status_code=400, detail="Invalid physician ID")
    
    # Check if the physician exists
    physician = await db.physicians.find_one({"_id": ObjectId(physician_id)})
    if not physician:
        raise HTTPException(status_code=404, detail="Physician not found")
    
    # Soft delete the physician
    await db.physicians.update_one(
        {"_id": ObjectId(physician_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Physician successfully deactivated"}

@router.get("/{physician_id}/availability", response_model=List[dict])
async def get_physician_availability(
    physician_id: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """
    Get availability slots for a specific physician.
    """
    db = get_database()
    
    # Check if the physician ID is valid
    if not ObjectId.is_valid(physician_id):
        raise HTTPException(status_code=400, detail="Invalid physician ID")
    
    # Retrieve the physician
    physician = await db.physicians.find_one({"_id": ObjectId(physician_id)})
    if not physician:
        raise HTTPException(status_code=404, detail="Physician not found")
    
    # Filter schedule based on date range
    schedule = physician.get("schedule", [])
    filtered_schedule = []
    
    for day in schedule:
        if from_date and day["date"] < from_date:
            continue
        if to_date and day["date"] > to_date:
            continue
        
        # Keep only available slots
        available_slots = [slot for slot in day["time_slots"] if slot["is_available"]]
        if available_slots:
            filtered_schedule.append({
                "date": day["date"],
                "time_slots": available_slots
            })
    
    return filtered_schedule