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

class ClinicInfoBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    phone: str
    email: str
    website: Optional[str] = None
    working_hours: Dict[str, str]  # e.g., {"Monday": "9:00-17:00", "Tuesday": "9:00-17:00", ...}
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class ClinicInfoDB(ClinicInfoBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class MedicalPackageBase(BaseModel):
    name: str
    description: str
    price: float
    duration_minutes: int
    services: List[str]
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class MedicalPackageDB(MedicalPackageBase):
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
                "name": "Comprehensive Health Checkup",
                "description": "Complete health assessment including blood work, cardiac evaluation, and consultation",
                "price": 1500.0,
                "duration_minutes": 120,
                "services": ["Blood Test", "ECG", "Physician Consultation", "Nutritionist Consultation"],
                "is_active": True,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-02T12:00:00"
            }
        }

class MedicalPackageResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    description: str
    price: float
    duration_minutes: int
    services: List[str]
    is_active: bool
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
