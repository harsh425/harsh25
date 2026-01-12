"""
Authentication routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import uuid
import secrets
import os

from utils.database import db
from utils.security import hash_password, verify_password, create_access_token, get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# Routes
@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    """Register a new user"""
    existing_user = await db.users.find_one({"email": user.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user.password)
    
    user_doc = {
        "user_id": user_id,
        "email": user.email,
        "password_hash": hashed_pw,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }
    
    await db.users.insert_one(user_doc)
    await log_activity(user_id, "user_registered", f"User {user.email} registered")
    
    # Send welcome email
    welcome_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Welcome to Nexus HR System</h2>
        <p>Hello {user.full_name},</p>
        <p>Your account has been created successfully.</p>
        <p>Role: <strong>{user.role.upper()}</strong></p>
        <p>You can now log in to access the system.</p>
    </div>
    """
    await send_email_async(user.email, "Welcome to Nexus HR", welcome_html)
    
    access_token = create_access_token(data={"sub": user_id})
    user_data = {k: v for k, v in user_doc.items() if k not in ["password_hash", "_id"]}
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login with email and password"""
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="Account is inactive")
    
    access_token = create_access_token(data={"sub": user["user_id"]})
    user_data = {k: v for k, v in user.items() if k != "password_hash"}
    
    await log_activity(user["user_id"], "user_login", f"User {credentials.email} logged in")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    return current_user


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Request a password reset email"""
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    
    reset_token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.password_resets.insert_one({
        "token": reset_token,
        "user_id": user["user_id"],
        "email": request.email,
        "expiry": expiry.isoformat(),
        "used": False
    })
    
    frontend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:3000").replace(":8001", ":3000")
    reset_url = f"{frontend_url}/reset-password/{reset_token}"
    
    email_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Password Reset Request</h2>
        <p>Hello {user['full_name']},</p>
        <p>You requested to reset your password. Click the button below to proceed:</p>
        <p><a href="{reset_url}" style="background: #002FA7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
    </div>
    """
    
    await send_email_async(request.email, "Password Reset Request", email_html)
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """Reset password with token"""
    reset = await db.password_resets.find_one({
        "token": request.token,
        "used": False
    }, {"_id": 0})
    
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    expiry = datetime.fromisoformat(reset["expiry"])
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    hashed_pw = hash_password(request.new_password)
    await db.users.update_one(
        {"user_id": reset["user_id"]},
        {"$set": {"password_hash": hashed_pw}}
    )
    
    await db.password_resets.update_one(
        {"token": request.token},
        {"$set": {"used": True}}
    )
    
    await log_activity(reset["user_id"], "password_reset", f"Password reset for {reset['email']}")
    
    return {"message": "Password reset successful"}
