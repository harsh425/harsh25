from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta, date
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import logging
import uuid
import base64
import asyncio
import resend
import secrets
from pathlib import Path
import math


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
fs = AsyncIOMotorGridFSBucket(db)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
security = HTTPBearer()

# Resend Email
resend.api_key = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kenyan Public Holidays 2025
KENYAN_HOLIDAYS_2025 = [
    "2025-01-01",  # New Year
    "2025-04-18",  # Good Friday
    "2025-04-21",  # Easter Monday
    "2025-05-01",  # Labour Day
    "2025-06-01",  # Madaraka Day
    "2025-10-10",  # Huduma Day
    "2025-10-20",  # Mashujaa Day
    "2025-12-12",  # Jamhuri Day
    "2025-12-25",  # Christmas
    "2025-12-26",  # Boxing Day
]

# Office Location for Geofencing (example: Nairobi CBD)
OFFICE_LOCATION = {
    "latitude": -1.286389,
    "longitude": 36.817223,
    "radius_meters": 200  # 200m radius
}


# ============ MODELS ============

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # "admin", "employee", "hr_assistant", "director", "manager"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class EmployeeCreate(BaseModel):
    # Personal Info
    first_name: str
    last_name: str
    employee_number: str
    date_of_birth: str
    gender: str
    marital_status: str
    
    # Contact Information
    email: EmailStr
    phone_number: str
    mpesa_number: str
    
    # Statutory Information
    kra_pin: str
    nssf_number: str
    shif_number: str
    
    # Emergency Contact
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relationship: str
    emergency_contact_email: EmailStr
    
    # Bank Information
    bank_account_name: str
    bank_name: str
    bank_branch_name: str
    bank_branch_code: str
    bank_account_number: str
    
    # Employment Details
    department: str
    position: str
    employment_type: str
    contract_start_date: str
    contract_end_date: Optional[str] = None
    manager_id: Optional[str] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    mpesa_number: Optional[str] = None
    kra_pin: Optional[str] = None
    nssf_number: Optional[str] = None
    shif_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_email: Optional[EmailStr] = None
    bank_account_name: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch_name: Optional[str] = None
    bank_branch_code: Optional[str] = None
    bank_account_number: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    employment_type: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[str] = None

class LeaveRequest(BaseModel):
    leave_type: str  # Annual, Sick, Maternity, Paternity, Compassionate, etc.
    start_date: str
    end_date: str
    reason: str
    days_requested: int

class LeaveApproval(BaseModel):
    status: str  # "approved", "rejected"
    comments: Optional[str] = None

class AttendanceCheckIn(BaseModel):
    latitude: float
    longitude: float
    check_in_time: str

class AttendanceCheckOut(BaseModel):
    latitude: float
    longitude: float
    check_out_time: str

class AttendanceVerification(BaseModel):
    status: str  # "verified", "flagged"
    comments: Optional[str] = None

class ContractCreate(BaseModel):
    employee_id: str
    title: str
    description: str
    expiry_days: Optional[int] = 30

class ContractSign(BaseModel):
    signature_data: str
    signature_type: str
    ip_address: str

class EmailSendRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    html_content: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class BulkEmployeeImport(BaseModel):
    employees: List[EmployeeCreate]


# ============ HELPER FUNCTIONS ============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def log_activity(user_id: str, action: str, details: str):
    activity = {
        "activity_id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.activity_logs.insert_one(activity)

async def send_email_async(recipient: str, subject: str, html: str):
    params = {
        "from": SENDER_EMAIL,
        "to": [recipient],
        "subject": subject,
        "html": html
    }
    try:
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {recipient}")
        return email
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in meters using Haversine formula"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def is_within_geofence(lat, lon):
    """Check if coordinates are within office geofence"""
    distance = calculate_distance(
        lat, lon,
        OFFICE_LOCATION["latitude"],
        OFFICE_LOCATION["longitude"]
    )
    return distance <= OFFICE_LOCATION["radius_meters"]

def calculate_working_days(start_date: str, end_date: str) -> int:
    """Calculate working days excluding weekends and Kenyan public holidays"""
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    working_days = 0
    current = start
    
    while current <= end:
        # Skip weekends (Saturday=5, Sunday=6)
        if current.weekday() < 5:
            # Skip public holidays
            if current.isoformat() not in KENYAN_HOLIDAYS_2025:
                working_days += 1
        current += timedelta(days=1)
    
    return working_days


# ============ AUTHENTICATION ROUTES ============