from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pymongo.bson import ObjectId

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

class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"

class AppointmentBase(BaseModel):
    physician_id: str
    date: str  # format: "YYYY-MM-DD"
    start_time: str  # format: "HH:MM", 24-hour
    end_time: str  # format: "HH:MM", 24-hour
    notes: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = None

class AppointmentDB(AppointmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    status: AppointmentStatus = AppointmentStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_intent_id: Optional[str] = None
    amount: float
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
                "user_id": "60d21b4967d0d8992e610c86",
                "physician_id": "60d21b4967d0d8992e610c87",
                "date": "2023-05-15",
                "start_time": "09:00",
                "end_time": "09:30",
                "notes": "First consultation for heart issues",
                "status": "confirmed",
                "payment_status": "paid",
                "payment_intent_id": "pi_1J2NxQEHVqKX9Mq8Y8jLQJnZ",
                "amount": 500.0,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-02T12:00:00"
            }
        }

class AppointmentResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    physician_id: str
    physician_name: Optional[str] = None  # Added field for UI convenience
    date: str
    start_time: str
    end_time: str
    notes: Optional[str] = None
    status: AppointmentStatus
    payment_status: PaymentStatus
    payment_intent_id: Optional[str] = None
    amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
