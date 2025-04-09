from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, Optional
from bson import ObjectId
from datetime import datetime

from utils.auth import get_current_active_user
from services.insurance_service import verify_insurance
from db.database import get_database

router = APIRouter()

@router.post("/verify", response_model=Dict[str, Any])
async def verify_insurance_coverage(
    emirates_id: str = Body(..., embed=True),
    current_user = Depends(get_current_active_user)
):
    """
    Verify insurance coverage using Emirates ID.
    
    This endpoint simulates checking insurance coverage by submitting the Emirates ID
    to a mock external service. In production, this would connect to actual insurance
    verification systems.
    """
    db = get_database()
    
    # Basic validation for Emirates ID format
    if not emirates_id or len(emirates_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Emirates ID format"
        )
    
    # Call the insurance verification service
    result = await verify_insurance(emirates_id)
    
    # Update user profile with insurance information if active
    if result.status == "active" and result.provider:
        await db.users.update_one(
            {"_id": current_user.id},
            {
                "$set": {
                    "insurance_status": result.status,
                    "insurance_provider": result.provider,
                    "insurance_details": result.coverage_details,
                    "emirates_id": emirates_id,  # Store the Emirates ID
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        # Update with inactive status
        await db.users.update_one(
            {"_id": current_user.id},
            {
                "$set": {
                    "insurance_status": result.status,
                    "insurance_provider": result.provider if result.provider else None,
                    "emirates_id": emirates_id,  # Still store the ID
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
    # Format response
    response = {
        "status": result.status,
        "provider": result.provider,
        "coverage_details": result.coverage_details
    }
    
    if result.error_message:
        response["error_message"] = result.error_message
        
    return response

@router.get("/status", response_model=Dict[str, Any])
async def get_insurance_status(
    current_user = Depends(get_current_active_user)
):
    """
    Get the current user's insurance status from their profile.
    """
    if not hasattr(current_user, "insurance_status") or not current_user.insurance_status:
        return {
            "status": "unknown",
            "message": "Insurance status not verified. Please submit your Emirates ID for verification."
        }
    
    # Prepare response based on stored insurance information
    response = {
        "status": current_user.insurance_status,
        "provider": getattr(current_user, "insurance_provider", None),
    }
    
    # Add coverage details if available
    insurance_details = getattr(current_user, "insurance_details", None)
    if insurance_details:
        response["coverage_details"] = insurance_details
    
    return response

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_insurance_status(
    current_user = Depends(get_current_active_user)
):
    """
    Refresh the insurance status by re-verifying with the stored Emirates ID.
    """
    # Check if user has an Emirates ID stored
    if not hasattr(current_user, "emirates_id") or not current_user.emirates_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Emirates ID found in your profile. Please submit your ID first."
        )
    
    # Re-verify with the stored Emirates ID
    result = await verify_insurance(current_user.emirates_id)
    
    # Update user profile with the latest insurance information
    db = get_database()
    if result.status == "active" and result.provider:
        await db.users.update_one(
            {"_id": current_user.id},
            {
                "$set": {
                    "insurance_status": result.status,
                    "insurance_provider": result.provider,
                    "insurance_details": result.coverage_details,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        # Update with inactive status
        await db.users.update_one(
            {"_id": current_user.id},
            {
                "$set": {
                    "insurance_status": result.status,
                    "insurance_provider": result.provider if result.provider else None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    # Format response
    response = {
        "status": result.status,
        "provider": result.provider,
        "coverage_details": result.coverage_details
    }
    
    if result.error_message:
        response["error_message"] = result.error_message
        
    return response
