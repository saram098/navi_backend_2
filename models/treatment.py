from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class TreatmentBase(BaseModel):
    name: str
    specialty: str
    description: str
    price_range: Optional[Dict[str, float]] = None  # e.g., {"min": 500, "max": 1500}
    duration_minutes: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class TreatmentDB(TreatmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "name": "Cardiac Generator Replacement",
                "specialty": "Cardiology",
                "description": "This procedure replaces the pacemaker's battery-powered generator...",
                "price_range": {"min": 5000, "max": 10000},
                "duration_minutes": 120,
                "is_active": True,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-02T12:00:00"
            }
        }

class TreatmentResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    specialty: str
    description: str
    price_range: Optional[Dict[str, float]] = None
    duration_minutes: Optional[int] = None
    is_active: bool
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }