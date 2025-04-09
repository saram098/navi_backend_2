from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from datetime import timedelta
from bson import ObjectId

from models.user import UserCreate, UserResponse, UserLogin, UserOTPVerify, UserPasswordReset, UserPasswordResetConfirm, Token
from utils.auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_active_user,
    generate_otp,
    verify_password_reset_token,
    get_user_by_email
)
from utils.email import send_otp_email, send_password_reset_email
from settings.config import settings
from db.database import get_database

router = APIRouter()

# In-memory OTP storage (for demo purposes)
# In production, this would be stored in a database with expiry
otp_store: Dict[str, str] = {}

@router.post("/register", response_model=Dict[str, str])
async def register_user(user_data: UserCreate):
    """
    Register a new user account.
    After registration, an OTP will be sent to the user's email for verification.
    """
    db = get_database()
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone number already exists (if provided)
    if user_data.phone_number:
        existing_phone = await db.users.find_one({"phone_number": user_data.phone_number})
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user object for database
    user_in_db = {
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone_number": user_data.phone_number,
        "emirates_id": user_data.emirates_id,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_verified": False,  # Will be set to True after OTP verification
        "created_at": datetime.utcnow()
    }
    
    # Insert user into database
    result = await db.users.insert_one(user_in_db)
    
    # Generate OTP for verification
    otp = generate_otp()
    otp_store[user_data.email] = otp
    
    # Send OTP to user's email
    await send_otp_email(user_data.email, otp)
    
    return {"message": "User registered successfully. Please verify your email with the OTP sent."}

@router.post("/verify", response_model=Dict[str, str])
async def verify_otp(verify_data: UserOTPVerify):
    """
    Verify user's email with OTP sent during registration.
    """
    db = get_database()
    
    # Check if email exists
    user = await db.users.find_one({"email": verify_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already verified
    if user.get("is_verified", False):
        return {"message": "Email already verified"}
    
    # Validate OTP
    stored_otp = otp_store.get(verify_data.email)
    if not stored_otp or stored_otp != verify_data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Update user's verification status
    await db.users.update_one(
        {"email": verify_data.email},
        {"$set": {"is_verified": True}}
    )
    
    # Remove OTP from storage
    if verify_data.email in otp_store:
        del otp_store[verify_data.email]
    
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return a JWT token.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/email", response_model=Token)
async def login_with_email_password(login_data: UserLogin):
    """
    Login with email and password.
    This endpoint provides a more user-friendly alternative to the OAuth2 endpoint.
    """
    user = await authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password", response_model=Dict[str, str])
async def forgot_password(reset_data: UserPasswordReset):
    """
    Initiate password reset process.
    Sends a password reset token to the user's email.
    """
    db = get_database()
    
    # Check if email exists
    user = await db.users.find_one({"email": reset_data.email})
    if not user:
        # For security reasons, don't reveal if email exists or not
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    # Generate password reset token
    from utils.auth import generate_password_reset_token
    reset_token = generate_password_reset_token(str(user["_id"]))
    
    # Send reset token to user's email
    await send_password_reset_email(reset_data.email, reset_token)
    
    return {"message": "Password reset instructions sent to your email"}

@router.post("/reset-password", response_model=Dict[str, str])
async def reset_password(reset_data: UserPasswordResetConfirm):
    """
    Reset password using token received via email.
    """
    db = get_database()
    
    # Verify reset token
    user_id = verify_password_reset_token(reset_data.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Find user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash new password
    hashed_password = get_password_hash(reset_data.new_password)
    
    # Update password in database
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    return {"message": "Password reset successful"}

@router.get("/me", response_model=UserResponse)
async def get_user_me(current_user = Depends(get_current_active_user)):
    """
    Get the current authenticated user's profile.
    """
    return current_user

@router.post("/resend-otp", response_model=Dict[str, str])
async def resend_verification_otp(email_data: Dict[str, str]):
    """
    Resend verification OTP to the user's email.
    """
    email = email_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    # Check if user exists
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Generate new OTP
    otp = generate_otp()
    otp_store[email] = otp
    
    # Send OTP
    await send_otp_email(email, otp)
    
    return {"message": "Verification OTP resent successfully"}
