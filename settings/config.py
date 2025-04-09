import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # MongoDB settings
    MONGO_URI: str = Field(..., env="MONGO_URI")
    DB_NAME: str = "clinic_db"
    
    # JWT settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Stripe settings
    STRIPE_SECRET_KEY: str = Field(..., env="STRIPE_SECRET_KEY")
    
    # Twilio settings
    TWILIO_SID: str = Field(..., env="TWILIO_SID")
    TWILIO_AUTH_TOKEN: str = Field(..., env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = Field(..., env="TWILIO_PHONE_NUMBER")
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    
    # Email settings (for OTP)
    EMAIL_HOST: str = Field("smtp.gmail.com", env="EMAIL_HOST")
    EMAIL_PORT: int = Field(587, env="EMAIL_PORT")
    EMAIL_USERNAME: Optional[str] = Field(None, env="EMAIL_USERNAME")
    EMAIL_PASSWORD: Optional[str] = Field(None, env="EMAIL_PASSWORD")
    EMAIL_FROM: Optional[str] = Field(None, env="EMAIL_FROM")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create a global settings object
settings = Settings()
