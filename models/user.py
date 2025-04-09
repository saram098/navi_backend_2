from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
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

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str
    emirates_id: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOTPVerify(BaseModel):
    email: EmailStr
    otp: str

class UserPasswordReset(BaseModel):
    email: EmailStr
    
class UserPasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class UserDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    insurance_status: Optional[str] = None
    insurance_provider: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+971501234567",
                "emirates_id": "784-1234-1234567-1",
                "hashed_password": "[hashed password will be stored here]",
                "is_active": True,
                "is_verified": True,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-02T12:00:00",
                "insurance_status": "active",
                "insurance_provider": "Daman"
            }
        }

class UserResponse(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str
    emirates_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    insurance_status: Optional[str] = None
    insurance_provider: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+971501234567",
                "emirates_id": "784-1234-1234567-1",
                "is_active": True,
                "is_verified": True,
                "insurance_status": "active",
                "insurance_provider": "Daman"
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None
