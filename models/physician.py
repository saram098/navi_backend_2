from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, time
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

class TimeSlot(BaseModel):
    start_time: str  # format: "HH:MM", 24-hour
    end_time: str  # format: "HH:MM", 24-hour
    is_available: bool = True

class DailySchedule(BaseModel):
    date: str  # format: "YYYY-MM-DD"
    time_slots: List[TimeSlot]

class PhysicianBase(BaseModel):
    name: str
    specialty: str
    qualification: str
    experience_years: int
    consultation_price: float
    bio: Optional[str] = None
    languages: List[str] = []
    profile_image: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class PhysicianCreate(PhysicianBase):
    schedule: List[DailySchedule] = []

class PhysicianUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_price: Optional[float] = None
    bio: Optional[str] = None
    languages: Optional[List[str]] = None
    profile_image: Optional[str] = None
    schedule: Optional[List[DailySchedule]] = None

class PhysicianDB(PhysicianBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    schedule: List[DailySchedule] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "name": "Dr. Jane Smith",
                "specialty": "Cardiology",
                "qualification": "MD, FRCS",
                "experience_years": 15,
                "consultation_price": 500.0,
                "bio": "Experienced cardiologist with focus on preventive care",
                "languages": ["English", "Arabic", "French"],
                "profile_image": "https://example.com/image.jpg",
                "schedule": [
                    {
                        "date": "2023-05-15",
                        "time_slots": [
                            {
                                "start_time": "09:00",
                                "end_time": "09:30",
                                "is_available": True
                            },
                            {
                                "start_time": "09:30",
                                "end_time": "10:00",
                                "is_available": False
                            }
                        ]
                    }
                ],
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-02T12:00:00",
                "is_active": True
            }
        }

class PhysicianResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    specialty: str
    qualification: str
    experience_years: int
    consultation_price: float
    bio: Optional[str] = None
    languages: List[str] = []
    profile_image: Optional[str] = None
    schedule: Optional[List[DailySchedule]] = None
    is_active: bool
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class PhysicianFilter(BaseModel):
    specialty: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    date: Optional[str] = None  # format: "YYYY-MM-DD"
    language: Optional[str] = None
