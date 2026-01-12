from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
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

# Office Location for Geofencing (Nairobi CBD - example coordinates)
OFFICE_LOCATION = {
    "latitude": -1.286389,
    "longitude": 36.817223,
    "radius_meters": 200  # 200m radius
}

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    # Company Assignment
    company_id: str
    
    # Personal Info
    employee_number: str  # HR Admin provides manually
    first_name: str
    last_name: str
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

class ContractCreate(BaseModel):
    employee_id: str
    title: str
    description: str
    expiry_days: Optional[int] = 30

class ContractSign(BaseModel):
    signature_data: str  # base64 encoded signature
    signature_type: str  # "typed", "drawn", "uploaded"
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

class CompanyCreate(BaseModel):
    company_name: str
    prefix: str  # e.g., "INT"
    contact_email: EmailStr
    phone_number: str
    address: Optional[str] = None
    registration_number: Optional[str] = None

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    prefix: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    registration_number: Optional[str] = None
    status: Optional[str] = None

class EmployeeTransfer(BaseModel):
    to_company_id: str
    transfer_date: str
    reason: str

class PerformanceReview(BaseModel):
    employee_number: str
    review_period_start: str
    review_period_end: str
    overall_rating: int  # 1-5
    goals_achieved: str
    strengths: str
    areas_for_improvement: str
    comments: str

class PerformanceGoal(BaseModel):
    employee_number: str
    goal_title: str
    goal_description: str
    target_date: str
    priority: str  # High, Medium, Low

class BulkEmployeeImport(BaseModel):
    employees: List[EmployeeCreate]

class LeaveRequest(BaseModel):
    leave_type: str  # Annual, Sick, Maternity, Paternity, Compassionate
    start_date: str
    end_date: str
    reason: str
    
class LeaveApproval(BaseModel):
    status: str  # "approved", "rejected"
    comments: Optional[str] = None

class AttendanceCheckIn(BaseModel):
    latitude: float
    longitude: float

class AttendanceCheckOut(BaseModel):
    latitude: float
    longitude: float

class AttendanceVerification(BaseModel):
    status: str  # "verified", "flagged"
    comments: Optional[str] = None


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

def calculate_working_days(start_date_str: str, end_date_str: str) -> int:
    """Calculate working days excluding weekends and Kenyan public holidays"""
    start = datetime.fromisoformat(start_date_str).date()
    end = datetime.fromisoformat(end_date_str).date()
    
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
    return distance <= OFFICE_LOCATION["radius_meters"], distance


# ============ AUTHENTICATION ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserRegister):
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
    user_data = {k: v for k, v in user_doc.items() if k != "password_hash"}
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
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

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ============ PASSWORD RESET ROUTES ============

@api_router.post("/auth/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user:
        # Don't reveal if email exists for security
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token
    await db.password_resets.insert_one({
        "token": reset_token,
        "user_id": user["user_id"],
        "email": request.email,
        "expiry": expiry.isoformat(),
        "used": False
    })
    
    # Send reset email
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

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm):
    # Find valid reset token
    reset = await db.password_resets.find_one({
        "token": request.token,
        "used": False
    }, {"_id": 0})
    
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check expiry
    expiry = datetime.fromisoformat(reset["expiry"])
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Update password
    hashed_pw = hash_password(request.new_password)
    await db.users.update_one(
        {"user_id": reset["user_id"]},
        {"$set": {"password_hash": hashed_pw}}
    )
    
    # Mark token as used
    await db.password_resets.update_one(
        {"token": request.token},
        {"$set": {"used": True}}
    )
    
    await log_activity(reset["user_id"], "password_reset", f"Password reset for {reset['email']}")
    
    return {"message": "Password reset successful"}


# ============ COMPANY MANAGEMENT ROUTES ============

@api_router.post("/companies")
async def create_company(company: CompanyCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create companies")
    
    # Check if prefix already exists
    existing = await db.companies.find_one({"prefix": company.prefix.upper()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail=f"Prefix '{company.prefix.upper()}' already in use")
    
    company_id = str(uuid.uuid4())
    company_doc = {
        "company_id": company_id,
        "company_name": company.company_name,
        "prefix": company.prefix.upper(),
        "contact_email": company.contact_email,
        "phone_number": company.phone_number,
        "address": company.address,
        "registration_number": company.registration_number,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    
    await db.companies.insert_one(company_doc)
    await log_activity(current_user["user_id"], "company_created", f"Created company {company.company_name}")
    
    return {"message": "Company created successfully", "company_id": company_id}

@api_router.get("/companies")
async def get_companies(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    companies = await db.companies.find({}, {"_id": 0}).to_list(100)
    return companies

@api_router.get("/companies/{company_id}")
async def get_company(company_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company

@api_router.patch("/companies/{company_id}")
async def update_company(company_id: str, updates: CompanyUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update companies")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # If updating prefix, check it's not already used
    if "prefix" in update_data:
        update_data["prefix"] = update_data["prefix"].upper()
        existing = await db.companies.find_one({
            "prefix": update_data["prefix"],
            "company_id": {"$ne": company_id}
        }, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail=f"Prefix '{update_data['prefix']}' already in use")
    
    result = await db.companies.update_one(
        {"company_id": company_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    await log_activity(current_user["user_id"], "company_updated", f"Updated company {company_id}")
    return {"message": "Company updated successfully"}


# ============ EMPLOYEE MANAGEMENT ROUTES ============

@api_router.post("/employees")
async def create_employee(employee: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only admins and HR assistants can create employees")
    
    # Validate company exists
    company = await db.companies.find_one({"company_id": employee.company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if company["status"] != "active":
        raise HTTPException(status_code=400, detail="Cannot add employees to inactive company")
    
    # Validate employee number starts with company prefix
    if not employee.employee_number.upper().startswith(company["prefix"]):
        raise HTTPException(
            status_code=400,
            detail=f"Employee number must start with company prefix '{company['prefix']}'"
        )
    
    # Check if employee number already exists for active employees
    existing = await db.employees.find_one({
        "employee_number": employee.employee_number.upper(),
        "status": {"$in": ["active", "on_leave"]}
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Employee number '{employee.employee_number.upper()}' already exists for an active employee. Cannot reuse unless previous employee is inactive/suspended."
        )
    
    emp_doc = employee.model_dump()
    emp_doc["employee_number"] = employee.employee_number.upper()
    emp_doc["company_name"] = company["company_name"]
    emp_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    emp_doc["status"] = "active"
    emp_doc["created_by"] = current_user["user_id"]
    emp_doc["full_name"] = f"{employee.first_name} {employee.last_name}"
    emp_doc["transfer_history"] = []
    
    # Initialize leave balances (Kenyan labor law: 21 days annual leave)
    emp_doc["leave_balance"] = {
        "annual": 21,
        "sick": 30,
        "maternity": 0,
        "paternity": 0
    }
    
    await db.employees.insert_one(emp_doc)
    await log_activity(current_user["user_id"], "employee_created", f"Created employee {employee.employee_number.upper()} for {company['company_name']}")
    
    return {"message": "Employee created successfully", "employee_number": employee.employee_number.upper()}

@api_router.get("/employees")
async def get_all_employees(current_user: dict = Depends(get_current_user)):
    if current_user["role"] in ["admin", "hr_assistant", "director", "manager"]:
        # Admins, HR, Directors, and Managers can see all employees
        if current_user["role"] == "manager":
            # Managers see their team + themselves
            employees = await db.employees.find({
                "$or": [
                    {"manager_id": current_user["user_id"]},
                    {"email": current_user["email"]}
                ]
            }, {"_id": 0}).to_list(1000)
        else:
            employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
    else:
        # Regular employees can only see their own record
        employees = await db.employees.find({"email": current_user["email"]}, {"_id": 0}).to_list(1)
    
    return employees

@api_router.get("/employees/{employee_number}")
async def get_employee(employee_number: str, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check permissions
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        if employee["email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return employee

@api_router.patch("/employees/{employee_number}")
async def update_employee(employee_number: str, updates: EmployeeUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only admins and HR assistants can update employees")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # Update full_name if first_name or last_name changed
    if "first_name" in update_data or "last_name" in update_data:
        employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
        first_name = update_data.get("first_name", employee.get("first_name", ""))
        last_name = update_data.get("last_name", employee.get("last_name", ""))
        update_data["full_name"] = f"{first_name} {last_name}"
    
    result = await db.employees.update_one(
        {"employee_number": employee_number},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await log_activity(current_user["user_id"], "employee_updated", f"Updated employee {employee_number}")
    return {"message": "Employee updated successfully"}

@api_router.delete("/employees/{employee_number}")
async def deactivate_employee(employee_number: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can deactivate employees")
    
    result = await db.employees.update_one(
        {"employee_number": employee_number},
        {"$set": {"status": "inactive"}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await log_activity(current_user["user_id"], "employee_deactivated", f"Deactivated employee {employee_number}")
    return {"message": "Employee deactivated successfully"}


@api_router.post("/employees/{employee_number}/transfer")
async def transfer_employee(employee_number: str, transfer: EmployeeTransfer, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can transfer employees")
    
    # Get employee
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get target company
    to_company = await db.companies.find_one({"company_id": transfer.to_company_id}, {"_id": 0})
    if not to_company:
        raise HTTPException(status_code=404, detail="Target company not found")
    
    if to_company["status"] != "active":
        raise HTTPException(status_code=400, detail="Cannot transfer to inactive company")
    
    from_company_id = employee.get("company_id")
    from_company_name = employee.get("company_name", "Unknown")
    
    # Create transfer record
    transfer_record = {
        "transfer_id": str(uuid.uuid4()),
        "employee_number": employee_number,
        "employee_name": employee.get("full_name", f"{employee.get('first_name', '')} {employee.get('last_name', '')}"),
        "from_company_id": from_company_id,
        "from_company_name": from_company_name,
        "to_company_id": transfer.to_company_id,
        "to_company_name": to_company["company_name"],
        "transfer_date": transfer.transfer_date,
        "reason": transfer.reason,
        "created_by": current_user["full_name"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.transfers.insert_one(transfer_record)
    
    # Update employee record
    await db.employees.update_one(
        {"employee_number": employee_number},
        {
            "$set": {
                "company_id": transfer.to_company_id,
                "company_name": to_company["company_name"]
            },
            "$push": {"transfer_history": transfer_record}
        }
    )
    
    # Generate transfer letter (stored in documents)
    letter_content = f"""
    TRANSFER LETTER
    
    Date: {datetime.now().strftime('%B %d, %Y')}
    
    To: {employee.get('full_name')}
    Employee Number: {employee_number}
    
    Dear {employee.get('first_name')},
    
    Re: TRANSFER TO {to_company['company_name'].upper()}
    
    We are pleased to inform you of your transfer from {from_company_name} to {to_company['company_name']}, 
    effective {datetime.fromisoformat(transfer.transfer_date).strftime('%B %d, %Y')}.
    
    Reason: {transfer.reason}
    
    Your terms and conditions of employment remain unchanged unless otherwise communicated.
    
    We wish you success in your new assignment.
    
    Yours faithfully,
    HR Department
    """
    
    # Store transfer letter as document
    transfer_doc = {
        "document_id": str(uuid.uuid4()),
        "employee_id": employee_number,
        "category": "Transfer Letter",
        "document_type": "official",
        "filename": f"Transfer_Letter_{employee_number}_{datetime.now().strftime('%Y%m%d')}.txt",
        "content": letter_content,
        "uploaded_by": current_user["user_id"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "content_type": "text/plain"
    }
    
    await db.documents.insert_one(transfer_doc)
    
    # Send email notification
    if employee.get("email"):
        email_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Employee Transfer Notification</h2>
            <p>Dear {employee.get('first_name')},</p>
            <p>This is to inform you that you have been transferred to <strong>{to_company['company_name']}</strong>, 
            effective {datetime.fromisoformat(transfer.transfer_date).strftime('%B %d, %Y')}.</p>
            <p><strong>Reason:</strong> {transfer.reason}</p>
            <p>Your transfer letter has been generated and is available in your document portal.</p>
            <p>For any questions, please contact HR.</p>
            <br>
            <p>Best regards,<br>HR Department</p>
        </div>
        """
        await send_email_async(employee["email"], "Employee Transfer Notification", email_html)
    
    await log_activity(current_user["user_id"], "employee_transferred", 
                      f"Transferred {employee_number} from {from_company_name} to {to_company['company_name']}")
    
    return {
        "message": "Employee transferred successfully",
        "transfer_id": transfer_record["transfer_id"],
        "transfer_letter_id": transfer_doc["document_id"]
    }

@api_router.get("/employees/{employee_number}/transfers")
async def get_employee_transfers(employee_number: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        # Employees can only see their own transfers
        employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
        if not employee or employee.get("email") != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    transfers = await db.transfers.find({"employee_number": employee_number}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return transfers


# ============ PERFORMANCE TRACKING ROUTES ============

@api_router.post("/performance/reviews")
async def create_performance_review(review: PerformanceReview, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant", "manager"]:
        raise HTTPException(status_code=403, detail="Only managers and HR can create reviews")
    
    # Get employee
    employee = await db.employees.find_one({"employee_number": review.employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Verify manager can review this employee
    if current_user["role"] == "manager" and employee.get("manager_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only review your direct reports")
    
    review_id = str(uuid.uuid4())
    review_doc = {
        "review_id": review_id,
        "employee_number": review.employee_number,
        "employee_name": employee.get("full_name", f"{employee.get('first_name', '')} {employee.get('last_name', '')}"),
        "company_id": employee.get("company_id"),
        "company_name": employee.get("company_name"),
        "review_period_start": review.review_period_start,
        "review_period_end": review.review_period_end,
        "overall_rating": review.overall_rating,
        "goals_achieved": review.goals_achieved,
        "strengths": review.strengths,
        "areas_for_improvement": review.areas_for_improvement,
        "comments": review.comments,
        "reviewer_name": current_user["full_name"],
        "reviewer_id": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.performance_reviews.insert_one(review_doc)
    await log_activity(current_user["user_id"], "performance_review_created", f"Created review for {review.employee_number}")
    
    # Send notification to employee
    if employee.get("email"):
        email_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Performance Review Completed</h2>
            <p>Dear {employee.get('first_name')},</p>
            <p>Your performance review for the period {review.review_period_start} to {review.review_period_end} has been completed.</p>
            <p><strong>Overall Rating:</strong> {review.overall_rating}/5</p>
            <p>Please log in to view the complete review details.</p>
        </div>
        """
        await send_email_async(employee["email"], "Performance Review Completed", email_html)
    
    return {"message": "Performance review created successfully", "review_id": review_id}

@api_router.get("/performance/reviews/{employee_number}")
async def get_employee_reviews(employee_number: str, current_user: dict = Depends(get_current_user)):
    # Check permissions
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        if employee.get("email") != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    reviews = await db.performance_reviews.find(
        {"employee_number": employee_number},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return reviews

@api_router.post("/performance/goals")
async def create_performance_goal(goal: PerformanceGoal, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant", "manager"]:
        raise HTTPException(status_code=403, detail="Only managers and HR can set goals")
    
    employee = await db.employees.find_one({"employee_number": goal.employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    goal_id = str(uuid.uuid4())
    goal_doc = {
        "goal_id": goal_id,
        "employee_number": goal.employee_number,
        "employee_name": employee.get("full_name"),
        "goal_title": goal.goal_title,
        "goal_description": goal.goal_description,
        "target_date": goal.target_date,
        "priority": goal.priority,
        "status": "in_progress",
        "set_by": current_user["full_name"],
        "set_by_id": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.performance_goals.insert_one(goal_doc)
    await log_activity(current_user["user_id"], "goal_created", f"Set goal for {goal.employee_number}")
    
    return {"message": "Goal created successfully", "goal_id": goal_id}

@api_router.get("/performance/goals/{employee_number}")
async def get_employee_goals(employee_number: str, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        if employee.get("email") != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    goals = await db.performance_goals.find(
        {"employee_number": employee_number},
        {"_id": 0}
    ).to_list(100)
    
    return goals


# ============ REPORTS & ANALYTICS ROUTES ============

@api_router.get("/reports/company-summary")
async def get_company_summary(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = {}
    if company_id:
        query["company_id"] = company_id
    
    # Employee statistics
    total_employees = await db.employees.count_documents(query)
    active_employees = await db.employees.count_documents({**query, "status": "active"})
    
    # Department breakdown
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$department", "count": {"$sum": 1}}}
    ]
    dept_breakdown = await db.employees.aggregate(pipeline).to_list(100)
    
    # Gender breakdown
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$gender", "count": {"$sum": 1}}}
    ]
    gender_breakdown = await db.employees.aggregate(pipeline).to_list(100)
    
    # Recent hires (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent_hires = await db.employees.count_documents({
        **query,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": total_employees - active_employees,
        "recent_hires": recent_hires,
        "department_breakdown": dept_breakdown,
        "gender_breakdown": gender_breakdown
    }

@api_router.get("/reports/leave-summary")
async def get_leave_summary(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get employees for company filter
    emp_query = {}
    if company_id:
        emp_query["company_id"] = company_id
    
    employees = await db.employees.find(emp_query, {"employee_number": 1, "_id": 0}).to_list(10000)
    employee_numbers = [emp["employee_number"] for emp in employees]
    
    # Leave statistics
    leave_query = {"employee_number": {"$in": employee_numbers}} if employee_numbers else {}
    
    total_requests = await db.leave_requests.count_documents(leave_query)
    pending = await db.leave_requests.count_documents({**leave_query, "status": "pending"})
    approved = await db.leave_requests.count_documents({**leave_query, "status": "approved"})
    rejected = await db.leave_requests.count_documents({**leave_query, "status": "rejected"})
    
    # Leave type breakdown
    pipeline = [
        {"$match": leave_query},
        {"$group": {"_id": "$leave_type", "count": {"$sum": 1}, "total_days": {"$sum": "$days_requested"}}}
    ]
    leave_type_breakdown = await db.leave_requests.aggregate(pipeline).to_list(100)
    
    return {
        "total_requests": total_requests,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "leave_type_breakdown": leave_type_breakdown
    }

@api_router.get("/reports/attendance-summary")
async def get_attendance_summary(
    company_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get employees for company filter
    emp_query = {}
    if company_id:
        emp_query["company_id"] = company_id
    
    employees = await db.employees.find(emp_query, {"employee_number": 1, "_id": 0}).to_list(10000)
    employee_numbers = [emp["employee_number"] for emp in employees]
    
    # Attendance query
    att_query = {"employee_number": {"$in": employee_numbers}} if employee_numbers else {}
    if start_date:
        att_query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in att_query:
            att_query["date"]["$lte"] = end_date
        else:
            att_query["date"] = {"$lte": end_date}
    
    total_records = await db.attendance.count_documents(att_query)
    late_arrivals = await db.attendance.count_documents({**att_query, "is_late": True})
    outside_geofence = await db.attendance.count_documents({**att_query, "within_geofence": False})
    
    # Average working hours
    pipeline = [
        {"$match": {**att_query, "total_hours": {"$ne": None}}},
        {"$group": {"_id": None, "avg_hours": {"$avg": "$total_hours"}}}
    ]
    avg_result = await db.attendance.aggregate(pipeline).to_list(1)
    avg_hours = round(avg_result[0]["avg_hours"], 2) if avg_result else 0
    
    return {
        "total_records": total_records,
        "late_arrivals": late_arrivals,
        "late_percentage": round((late_arrivals / total_records * 100), 2) if total_records > 0 else 0,
        "outside_geofence": outside_geofence,
        "average_hours": avg_hours
    }

@api_router.get("/reports/performance-summary")
async def get_performance_summary(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = {}
    if company_id:
        query["company_id"] = company_id
    
    total_reviews = await db.performance_reviews.count_documents(query)
    
    # Average rating
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$overall_rating"}}}
    ]
    avg_result = await db.performance_reviews.aggregate(pipeline).to_list(1)
    avg_rating = round(avg_result[0]["avg_rating"], 2) if avg_result else 0
    
    # Rating distribution
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$overall_rating", "count": {"$sum": 1}}}
    ]
    rating_distribution = await db.performance_reviews.aggregate(pipeline).to_list(100)
    
    return {
        "total_reviews": total_reviews,
        "average_rating": avg_rating,
        "rating_distribution": rating_distribution
    }


@api_router.post("/employees/bulk-import")
async def bulk_import_employees(import_data: BulkEmployeeImport, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only admins and HR assistants can import employees")
    
    success_count = 0
    failed_count = 0
    errors = []
    
    for emp in import_data.employees:
        try:
            # Validate company
            company = await db.companies.find_one({"company_id": emp.company_id}, {"_id": 0})
            if not company:
                failed_count += 1
                errors.append(f"Employee {emp.employee_number}: Company not found")
                continue
            
            # Validate prefix
            if not emp.employee_number.upper().startswith(company["prefix"]):
                failed_count += 1
                errors.append(f"Employee {emp.employee_number}: Must start with prefix '{company['prefix']}'")
                continue
            
            # Check duplicate for active employees
            existing = await db.employees.find_one({
                "employee_number": emp.employee_number.upper(),
                "status": {"$in": ["active", "on_leave"]}
            }, {"_id": 0})
            
            if existing:
                failed_count += 1
                errors.append(f"Employee {emp.employee_number.upper()}: Already exists (active)")
                continue
            
            emp_doc = emp.model_dump()
            emp_doc["employee_number"] = emp.employee_number.upper()
            emp_doc["company_name"] = company["company_name"]
            emp_doc["created_at"] = datetime.now(timezone.utc).isoformat()
            emp_doc["status"] = "active"
            emp_doc["created_by"] = current_user["user_id"]
            emp_doc["full_name"] = f"{emp.first_name} {emp.last_name}"
            emp_doc["transfer_history"] = []
            
            # Initialize leave balances
            emp_doc["leave_balance"] = {
                "annual": 21,
                "sick": 30,
                "maternity": 0,
                "paternity": 0
            }
            
            await db.employees.insert_one(emp_doc)
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            errors.append(f"Employee {emp.employee_number}: {str(e)}")
    
    await log_activity(current_user["user_id"], "bulk_import", f"Imported {success_count} employees, {failed_count} failed")
    
    return {
        "message": "Bulk import completed",
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors if errors else None
    }


# ============ DOCUMENT MANAGEMENT ROUTES ============

@api_router.post("/documents/upload")
async def upload_document(
    employee_id: str,
    category: str,
    file: UploadFile = File(...),
    document_type: str = "personal",  # "personal" or "payroll"
    expiry_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Check permissions
    if current_user["role"] not in ["admin", "hr_assistant"]:
        employee = await db.employees.find_one({"employee_number": employee_id}, {"_id": 0})
        if not employee or employee["email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Read file content
    file_content = await file.read()
    
    # Upload to GridFS
    file_id = await fs.upload_from_stream(
        filename=file.filename,
        source=file_content,
        metadata={
            "employee_id": employee_id,
            "category": category,
            "document_type": document_type,
            "uploaded_by": current_user["user_id"],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "content_type": file.content_type
        }
    )
    
    # Store document metadata
    doc_meta = {
        "document_id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "category": category,
        "document_type": document_type,
        "filename": file.filename,
        "file_id": str(file_id),
        "uploaded_by": current_user["user_id"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "content_type": file.content_type,
        "expiry_date": expiry_date,
        "expiry_notified": False
    }
    
    await db.documents.insert_one(doc_meta)
    await log_activity(current_user["user_id"], "document_uploaded", f"Uploaded {document_type} {category} document for {employee_id}")
    
    return {"message": "Document uploaded successfully", "document_id": doc_meta["document_id"]}

@api_router.get("/documents/employee/{employee_id}")
async def get_employee_documents(employee_id: str, current_user: dict = Depends(get_current_user)):
    # Check permissions
    if current_user["role"] != "admin":
        employee = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
        if not employee or employee["email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    documents = await db.documents.find({"employee_id": employee_id}, {"_id": 0}).to_list(1000)
    return documents

@api_router.get("/documents/{document_id}/download")
async def download_document(document_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.documents.find_one({"document_id": document_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions
    if current_user["role"] != "admin":
        employee = await db.employees.find_one({"employee_id": doc["employee_id"]}, {"_id": 0})
        if not employee or employee["email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    from bson import ObjectId
    grid_out = await fs.open_download_stream(ObjectId(doc["file_id"]))
    file_data = await grid_out.read()
    
    return {
        "filename": doc["filename"],
        "content_type": doc["content_type"],
        "data": base64.b64encode(file_data).decode('utf-8')
    }


@api_router.get("/documents/expiring-soon")
async def get_expiring_documents(days: int = 30, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    threshold_date = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    
    expiring_docs = await db.documents.find({
        "expiry_date": {"$ne": None, "$lte": threshold_date}
    }, {"_id": 0}).to_list(1000)
    
    return expiring_docs


@api_router.post("/documents/send-expiry-reminders")
async def send_expiry_reminders(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Get documents expiring in 30 days that haven't been notified
    threshold_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    expiring_docs = await db.documents.find({
        "expiry_date": {"$ne": None, "$lte": threshold_date},
        "expiry_notified": False
    }, {"_id": 0}).to_list(1000)
    
    reminder_count = 0
    
    for doc in expiring_docs:
        # Get employee details
        employee = await db.employees.find_one({"employee_id": doc["employee_id"]}, {"_id": 0})
        if not employee:
            continue
        
        # Send reminder email
        expiry_date = datetime.fromisoformat(doc["expiry_date"]).strftime('%Y-%m-%d')
        email_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Document Expiry Reminder</h2>
            <p>Hello {employee['full_name']},</p>
            <p>Your document is expiring soon:</p>
            <ul>
                <li><strong>Category:</strong> {doc['category']}</li>
                <li><strong>Filename:</strong> {doc['filename']}</li>
                <li><strong>Expiry Date:</strong> {expiry_date}</li>
            </ul>
            <p>Please upload a new version before it expires.</p>
        </div>
        """
        
        result = await send_email_async(employee["email"], "Document Expiry Reminder", email_html)
        if result:
            # Mark as notified
            await db.documents.update_one(
                {"document_id": doc["document_id"]},
                {"$set": {"expiry_notified": True}}
            )
            reminder_count += 1
    
    await log_activity(current_user["user_id"], "expiry_reminders_sent", f"Sent {reminder_count} document expiry reminders")
    
    return {"message": f"Sent {reminder_count} expiry reminders"}


# ============ LEAVE MANAGEMENT ROUTES ============

@api_router.post("/leave/request")
async def create_leave_request(leave_req: LeaveRequest, current_user: dict = Depends(get_current_user)):
    # Get employee record
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Calculate working days
    days_requested = calculate_working_days(leave_req.start_date, leave_req.end_date)
    
    if days_requested <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    # Check leave balance for annual leave
    if leave_req.leave_type == "Annual":
        if employee.get("leave_balance", {}).get("annual", 0) < days_requested:
            raise HTTPException(status_code=400, detail="Insufficient annual leave balance")
    
    # Determine approval workflow
    # Manager approval required for all leave types
    # HR Admin approval required after manager
    # Director approval required if > 14 days
    approval_levels = ["manager"]
    if employee.get("manager_id"):
        approval_levels.append("hr_admin")
        if days_requested > 14:
            approval_levels.append("director")
    else:
        # No manager assigned, go directly to HR
        approval_levels = ["hr_admin"]
        if days_requested > 14:
            approval_levels.append("director")
    
    leave_id = str(uuid.uuid4())
    leave_doc = {
        "leave_id": leave_id,
        "employee_number": employee["employee_number"],
        "employee_name": employee.get("full_name", f"{employee.get('first_name', '')} {employee.get('last_name', '')}"),
        "leave_type": leave_req.leave_type,
        "start_date": leave_req.start_date,
        "end_date": leave_req.end_date,
        "days_requested": days_requested,
        "reason": leave_req.reason,
        "status": "pending",
        "current_approval_level": approval_levels[0],
        "approval_levels": approval_levels,
        "approval_history": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    
    await db.leave_requests.insert_one(leave_doc)
    await log_activity(current_user["user_id"], "leave_request_created", f"Leave request {leave_id} created")
    
    # Send notification to manager/HR
    if employee.get("manager_id"):
        manager = await db.users.find_one({"user_id": employee["manager_id"]}, {"_id": 0})
        if manager:
            email_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>New Leave Request</h2>
                <p>Hello {manager['full_name']},</p>
                <p>{employee.get('full_name', 'An employee')} has requested leave:</p>
                <ul>
                    <li><strong>Type:</strong> {leave_req.leave_type}</li>
                    <li><strong>Period:</strong> {leave_req.start_date} to {leave_req.end_date}</li>
                    <li><strong>Days:</strong> {days_requested}</li>
                    <li><strong>Reason:</strong> {leave_req.reason}</li>
                </ul>
                <p>Please review and approve/reject this request.</p>
            </div>
            """
            await send_email_async(manager["email"], "New Leave Request Pending Approval", email_html)
    
    return {
        "message": "Leave request submitted successfully",
        "leave_id": leave_id,
        "days_requested": days_requested
    }

@api_router.get("/leave/my-requests")
async def get_my_leave_requests(current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        return []
    
    requests = await db.leave_requests.find(
        {"employee_number": employee["employee_number"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return requests

@api_router.get("/leave/pending-approvals")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["manager", "admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build query based on role
    if current_user["role"] == "manager":
        # Get leave requests for team members
        team_members = await db.employees.find({"manager_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
        employee_numbers = [emp["employee_number"] for emp in team_members]
        
        requests = await db.leave_requests.find({
            "employee_number": {"$in": employee_numbers},
            "status": "pending",
            "current_approval_level": "manager"
        }, {"_id": 0}).to_list(100)
        
    elif current_user["role"] in ["admin", "hr_assistant"]:
        # HR sees all requests at hr_admin level
        requests = await db.leave_requests.find({
            "status": "pending",
            "current_approval_level": "hr_admin"
        }, {"_id": 0}).to_list(100)
        
    elif current_user["role"] == "director":
        # Directors see requests requiring director approval
        requests = await db.leave_requests.find({
            "status": "pending",
            "current_approval_level": "director"
        }, {"_id": 0}).to_list(100)
    else:
        requests = []
    
    return requests

@api_router.post("/leave/{leave_id}/approve")
async def approve_leave(leave_id: str, approval: LeaveApproval, current_user: dict = Depends(get_current_user)):
    leave = await db.leave_requests.find_one({"leave_id": leave_id}, {"_id": 0})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave["status"] != "pending":
        raise HTTPException(status_code=400, detail="Leave request is not pending")
    
    # Verify user has permission to approve at this level
    current_level = leave["current_approval_level"]
    if current_level == "manager" and current_user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Only managers can approve at this level")
    elif current_level == "hr_admin" and current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can approve at this level")
    elif current_level == "director" and current_user["role"] != "director":
        raise HTTPException(status_code=403, detail="Only directors can approve at this level")
    
    # Add to approval history
    approval_entry = {
        "level": current_level,
        "approver_name": current_user["full_name"],
        "approver_id": current_user["user_id"],
        "status": approval.status,
        "comments": approval.comments,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Update leave request
    approval_levels = leave["approval_levels"]
    current_index = approval_levels.index(current_level)
    
    if approval.status == "rejected":
        # Rejection at any level = rejected
        await db.leave_requests.update_one(
            {"leave_id": leave_id},
            {
                "$set": {
                    "status": "rejected",
                    "rejection_reason": approval.comments
                },
                "$push": {"approval_history": approval_entry}
            }
        )
        
        # Notify employee
        employee = await db.employees.find_one({"employee_number": leave["employee_number"]}, {"_id": 0})
        if employee:
            email_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Leave Request Rejected</h2>
                <p>Hello {employee.get('full_name', 'Employee')},</p>
                <p>Your leave request has been rejected by {current_user['full_name']} ({current_level}).</p>
                <p><strong>Reason:</strong> {approval.comments or 'No reason provided'}</p>
                <p><strong>Leave Details:</strong></p>
                <ul>
                    <li>Type: {leave['leave_type']}</li>
                    <li>Period: {leave['start_date']} to {leave['end_date']}</li>
                </ul>
            </div>
            """
            await send_email_async(employee["email"], "Leave Request Rejected", email_html)
        
        await log_activity(current_user["user_id"], "leave_rejected", f"Rejected leave {leave_id}")
        return {"message": "Leave request rejected"}
        
    else:
        # Approved at this level
        if current_index < len(approval_levels) - 1:
            # Move to next approval level
            next_level = approval_levels[current_index + 1]
            await db.leave_requests.update_one(
                {"leave_id": leave_id},
                {
                    "$set": {"current_approval_level": next_level},
                    "$push": {"approval_history": approval_entry}
                }
            )
            
            # Notify next approver
            # Find users with the next approval role
            if next_level == "hr_admin":
                hr_users = await db.users.find({"role": {"$in": ["admin", "hr_assistant"]}}, {"_id": 0}).to_list(10)
                for hr_user in hr_users[:1]:  # Notify first HR user
                    email_html = f"""
                    <div style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2>Leave Request Awaiting Your Approval</h2>
                        <p>Hello {hr_user['full_name']},</p>
                        <p>A leave request has been approved by the manager and now requires HR approval:</p>
                        <ul>
                            <li><strong>Employee:</strong> {leave['employee_name']}</li>
                            <li><strong>Type:</strong> {leave['leave_type']}</li>
                            <li><strong>Period:</strong> {leave['start_date']} to {leave['end_date']}</li>
                            <li><strong>Days:</strong> {leave['days_requested']}</li>
                        </ul>
                    </div>
                    """
                    await send_email_async(hr_user["email"], "Leave Request Awaiting HR Approval", email_html)
            
            await log_activity(current_user["user_id"], "leave_approved_partial", f"Approved leave {leave_id} at {current_level}")
            return {"message": f"Leave approved at {current_level}. Moving to {next_level} approval."}
            
        else:
            # Final approval - update leave balance and mark as approved
            await db.leave_requests.update_one(
                {"leave_id": leave_id},
                {
                    "$set": {"status": "approved"},
                    "$push": {"approval_history": approval_entry}
                }
            )
            
            # Deduct from leave balance if Annual leave
            if leave["leave_type"] == "Annual":
                await db.employees.update_one(
                    {"employee_number": leave["employee_number"]},
                    {"$inc": {"leave_balance.annual": -leave["days_requested"]}}
                )
            
            # Notify employee
            employee = await db.employees.find_one({"employee_number": leave["employee_number"]}, {"_id": 0})
            if employee:
                email_html = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #10B981;">Leave Request Approved!</h2>
                    <p>Hello {employee.get('full_name', 'Employee')},</p>
                    <p>Great news! Your leave request has been fully approved.</p>
                    <p><strong>Leave Details:</strong></p>
                    <ul>
                        <li>Type: {leave['leave_type']}</li>
                        <li>Period: {leave['start_date']} to {leave['end_date']}</li>
                        <li>Days: {leave['days_requested']}</li>
                    </ul>
                    <p>Have a great time off!</p>
                </div>
                """
                await send_email_async(employee["email"], "Leave Request Approved", email_html)
            
            await log_activity(current_user["user_id"], "leave_approved_final", f"Fully approved leave {leave_id}")
            return {"message": "Leave request fully approved"}

@api_router.get("/leave/balance")
async def get_leave_balance(current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    balance = employee.get("leave_balance", {
        "annual": 21,
        "sick": 30,
        "maternity": 0,
        "paternity": 0
    })
    
    # Calculate used leave this year
    year_start = f"{datetime.now().year}-01-01"
    approved_leaves = await db.leave_requests.find({
        "employee_number": employee["employee_number"],
        "status": "approved",
        "start_date": {"$gte": year_start}
    }, {"_id": 0}).to_list(100)
    
    used = {
        "annual": 0,
        "sick": 0,
        "maternity": 0,
        "paternity": 0
    }
    
    for leave in approved_leaves:
        leave_type_key = leave["leave_type"].lower()
        if leave_type_key in used:
            used[leave_type_key] += leave["days_requested"]
    
    return {
        "balance": balance,
        "used": used,
        "available": {
            "annual": balance.get("annual", 21) - used["annual"],
            "sick": balance.get("sick", 30) - used["sick"]
        }
    }

@api_router.get("/leave/team-calendar")
async def get_team_leave_calendar(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["manager", "admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get approved leave requests for the next 3 months
    today = datetime.now().date()
    three_months = (today + timedelta(days=90)).isoformat()
    
    if current_user["role"] == "manager":
        # Get team members
        team_members = await db.employees.find({"manager_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
        employee_numbers = [emp["employee_number"] for emp in team_members]
        
        leaves = await db.leave_requests.find({
            "employee_number": {"$in": employee_numbers},
            "status": "approved",
            "start_date": {"$lte": three_months}
        }, {"_id": 0}).to_list(1000)
    else:
        # HR/Directors see all
        leaves = await db.leave_requests.find({
            "status": "approved",
            "start_date": {"$lte": three_months}
        }, {"_id": 0}).to_list(1000)
    
    return leaves

@api_router.get("/leave/holidays")
async def get_kenyan_holidays():
    return {
        "holidays": KENYAN_HOLIDAYS_2025,
        "year": 2025
    }


# ============ ATTENDANCE MODULE ROUTES ============

@api_router.post("/attendance/check-in")
async def check_in(attendance: AttendanceCheckIn, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Check if already checked in today
    today = datetime.now(timezone.utc).date().isoformat()
    existing = await db.attendance.find_one({
        "employee_number": employee["employee_number"],
        "date": today,
        "check_out_time": None
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Verify geolocation
    within_fence, distance = is_within_geofence(attendance.latitude, attendance.longitude)
    
    check_in_time = datetime.now(timezone.utc)
    
    # Determine if late (after 9:00 AM)
    expected_time = check_in_time.replace(hour=9, minute=0, second=0, microsecond=0)
    is_late = check_in_time > expected_time
    
    attendance_doc = {
        "attendance_id": str(uuid.uuid4()),
        "employee_number": employee["employee_number"],
        "employee_name": employee.get("full_name", f"{employee.get('first_name', '')} {employee.get('last_name', '')}"),
        "date": today,
        "check_in_time": check_in_time.isoformat(),
        "check_in_latitude": attendance.latitude,
        "check_in_longitude": attendance.longitude,
        "check_in_distance": round(distance, 2),
        "within_geofence": within_fence,
        "is_late": is_late,
        "check_out_time": None,
        "total_hours": None,
        "status": "pending_verification" if not within_fence else "checked_in",
        "verified_by": None,
        "verification_status": None,
        "verification_comments": None
    }
    
    await db.attendance.insert_one(attendance_doc)
    await log_activity(current_user["user_id"], "attendance_check_in", f"Checked in at {check_in_time.strftime('%H:%M')}")
    
    # Flag if outside geofence
    if not within_fence:
        # Notify manager
        if employee.get("manager_id"):
            manager = await db.users.find_one({"user_id": employee["manager_id"]}, {"_id": 0})
            if manager:
                email_html = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #FF4500;">Attendance Alert</h2>
                    <p>Hello {manager['full_name']},</p>
                    <p>{employee.get('full_name', 'An employee')} checked in outside the office geofence:</p>
                    <ul>
                        <li><strong>Distance from office:</strong> {round(distance, 2)}m</li>
                        <li><strong>Time:</strong> {check_in_time.strftime('%H:%M')}</li>
                    </ul>
                    <p>Please verify this attendance record.</p>
                </div>
                """
                await send_email_async(manager["email"], "Attendance Verification Required", email_html)
    
    return {
        "message": "Checked in successfully" if within_fence else "Checked in (outside geofence - requires verification)",
        "attendance_id": attendance_doc["attendance_id"],
        "check_in_time": check_in_time.strftime('%H:%M'),
        "within_geofence": within_fence,
        "distance": round(distance, 2),
        "is_late": is_late
    }

@api_router.post("/attendance/check-out")
async def check_out(attendance: AttendanceCheckOut, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Find today's check-in record
    today = datetime.now(timezone.utc).date().isoformat()
    attendance_record = await db.attendance.find_one({
        "employee_number": employee["employee_number"],
        "date": today,
        "check_out_time": None
    }, {"_id": 0})
    
    if not attendance_record:
        raise HTTPException(status_code=404, detail="No active check-in found for today")
    
    # Verify geolocation
    within_fence, distance = is_within_geofence(attendance.latitude, attendance.longitude)
    
    check_out_time = datetime.now(timezone.utc)
    check_in_time = datetime.fromisoformat(attendance_record["check_in_time"])
    
    # Calculate total hours
    time_diff = check_out_time - check_in_time
    total_hours = round(time_diff.total_seconds() / 3600, 2)
    
    # Update attendance record
    await db.attendance.update_one(
        {"attendance_id": attendance_record["attendance_id"]},
        {"$set": {
            "check_out_time": check_out_time.isoformat(),
            "check_out_latitude": attendance.latitude,
            "check_out_longitude": attendance.longitude,
            "check_out_distance": round(distance, 2),
            "total_hours": total_hours,
            "status": "completed"
        }}
    )
    
    await log_activity(current_user["user_id"], "attendance_check_out", f"Checked out at {check_out_time.strftime('%H:%M')}")
    
    return {
        "message": "Checked out successfully",
        "check_out_time": check_out_time.strftime('%H:%M'),
        "total_hours": total_hours,
        "within_geofence": within_fence,
        "distance": round(distance, 2)
    }

@api_router.get("/attendance/my-attendance")
async def get_my_attendance(days: int = 30, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        return []
    
    # Get attendance for last N days
    start_date = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
    
    attendance_records = await db.attendance.find({
        "employee_number": employee["employee_number"],
        "date": {"$gte": start_date}
    }, {"_id": 0}).sort("date", -1).to_list(1000)
    
    return attendance_records

@api_router.get("/attendance/team-attendance")
async def get_team_attendance(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["manager", "admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Default to today
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()
    
    if current_user["role"] == "manager":
        # Get team members
        team_members = await db.employees.find({"manager_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
        employee_numbers = [emp["employee_number"] for emp in team_members]
        
        attendance = await db.attendance.find({
            "employee_number": {"$in": employee_numbers},
            "date": date
        }, {"_id": 0}).to_list(1000)
    else:
        # HR/Directors see all
        attendance = await db.attendance.find({"date": date}, {"_id": 0}).to_list(1000)
    
    return attendance

@api_router.post("/attendance/{attendance_id}/verify")
async def verify_attendance(attendance_id: str, verification: AttendanceVerification, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["manager", "admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only managers and HR can verify attendance")
    
    attendance = await db.attendance.find_one({"attendance_id": attendance_id}, {"_id": 0})
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # For managers, verify they manage this employee
    if current_user["role"] == "manager":
        employee = await db.employees.find_one({"employee_number": attendance["employee_number"]}, {"_id": 0})
        if not employee or employee.get("manager_id") != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized to verify this employee's attendance")
    
    # Update verification
    await db.attendance.update_one(
        {"attendance_id": attendance_id},
        {"$set": {
            "verification_status": verification.status,
            "verification_comments": verification.comments,
            "verified_by": current_user["full_name"],
            "verified_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(current_user["user_id"], "attendance_verified", f"Verified attendance {attendance_id} as {verification.status}")
    
    return {"message": f"Attendance {verification.status}"}

@api_router.get("/attendance/reports/summary")
async def get_attendance_summary(
    employee_number: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["manager", "admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build query
    query = {}
    
    if employee_number:
        query["employee_number"] = employee_number
    elif current_user["role"] == "manager":
        # Manager sees only their team
        team_members = await db.employees.find({"manager_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
        employee_numbers = [emp["employee_number"] for emp in team_members]
        query["employee_number"] = {"$in": employee_numbers}
    
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}
    
    # Get records
    records = await db.attendance.find(query, {"_id": 0}).to_list(10000)
    
    # Calculate summary
    total_days = len(set(r["date"] for r in records))
    late_count = sum(1 for r in records if r.get("is_late"))
    outside_geofence = sum(1 for r in records if not r.get("within_geofence"))
    avg_hours = sum(r.get("total_hours", 0) for r in records if r.get("total_hours")) / len(records) if records else 0
    
    return {
        "total_records": len(records),
        "total_days": total_days,
        "late_count": late_count,
        "outside_geofence_count": outside_geofence,
        "average_hours": round(avg_hours, 2)
    }

@api_router.get("/attendance/office-location")
async def get_office_location():
    """Return office location for geofencing"""
    return OFFICE_LOCATION


# ============ CONTRACT MANAGEMENT ROUTES ============

@api_router.post("/contracts")
async def create_contract(contract: ContractCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create contracts")
    
    employee = await db.employees.find_one({"employee_id": contract.employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    contract_id = str(uuid.uuid4())
    signing_token = str(uuid.uuid4())
    
    contract_doc = {
        "contract_id": contract_id,
        "employee_id": contract.employee_id,
        "title": contract.title,
        "description": contract.description,
        "status": "sent",
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "signing_token": signing_token,
        "expiry_date": (datetime.now(timezone.utc) + timedelta(days=contract.expiry_days)).isoformat(),
        "viewed_at": None,
        "signed_at": None,
        "signature_data": None
    }
    
    await db.contracts.insert_one(contract_doc)
    await log_activity(current_user["user_id"], "contract_created", f"Created contract for {contract.employee_id}")
    
    # Send email with signing link
    frontend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:3000").replace(":8001", ":3000")
    signing_url = f"{frontend_url}/sign-contract/{signing_token}"
    
    email_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>New Employment Contract</h2>
        <p>Hello {employee['full_name']},</p>
        <p>You have received a new contract to review and sign:</p>
        <p><strong>{contract.title}</strong></p>
        <p>{contract.description}</p>
        <p><a href="{signing_url}" style="background: #002FA7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Sign Contract</a></p>
        <p>This link will expire in {contract.expiry_days} days.</p>
    </div>
    """
    
    await send_email_async(employee["email"], "New Contract to Sign", email_html)
    
    return {
        "message": "Contract created and sent successfully",
        "contract_id": contract_id,
        "signing_url": signing_url
    }

@api_router.get("/contracts")
async def get_contracts(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "admin":
        contracts = await db.contracts.find({}, {"_id": 0, "signing_token": 0}).to_list(1000)
    else:
        # Get employee's contracts
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if employee:
            contracts = await db.contracts.find(
                {"employee_id": employee["employee_id"]},
                {"_id": 0, "signing_token": 0}
            ).to_list(1000)
        else:
            contracts = []
    
    return contracts

@api_router.get("/contracts/sign/{signing_token}")
async def get_contract_for_signing(signing_token: str):
    contract = await db.contracts.find_one({"signing_token": signing_token}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Check if expired
    expiry = datetime.fromisoformat(contract["expiry_date"])
    if datetime.now(timezone.utc) > expiry:
        await db.contracts.update_one(
            {"signing_token": signing_token},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=400, detail="Contract link has expired")
    
    # Mark as viewed
    if not contract.get("viewed_at"):
        await db.contracts.update_one(
            {"signing_token": signing_token},
            {"$set": {"viewed_at": datetime.now(timezone.utc).isoformat(), "status": "viewed"}}
        )
    
    # Get employee details
    employee = await db.employees.find_one({"employee_id": contract["employee_id"]}, {"_id": 0})
    
    return {**contract, "employee": employee}

@api_router.post("/contracts/sign/{signing_token}")
async def sign_contract(signing_token: str, signature: ContractSign):
    contract = await db.contracts.find_one({"signing_token": signing_token}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract["status"] == "signed":
        raise HTTPException(status_code=400, detail="Contract already signed")
    
    # Check if expired
    expiry = datetime.fromisoformat(contract["expiry_date"])
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="Contract link has expired")
    
    # Update contract
    await db.contracts.update_one(
        {"signing_token": signing_token},
        {"$set": {
            "status": "signed",
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "signature_data": signature.signature_data,
            "signature_type": signature.signature_type,
            "signature_ip": signature.ip_address
        }}
    )
    
    # Send confirmation email to employee
    employee = await db.employees.find_one({"employee_id": contract["employee_id"]}, {"_id": 0})
    if employee:
        email_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Contract Signed Successfully</h2>
            <p>Hello {employee['full_name']},</p>
            <p>You have successfully signed the contract: <strong>{contract['title']}</strong></p>
            <p>Signed on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        """
        await send_email_async(employee["email"], "Contract Signed", email_html)
    
    return {"message": "Contract signed successfully"}

@api_router.get("/contracts/stats")
async def get_contract_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    total = await db.contracts.count_documents({})
    sent = await db.contracts.count_documents({"status": "sent"})
    viewed = await db.contracts.count_documents({"status": "viewed"})
    signed = await db.contracts.count_documents({"status": "signed"})
    expired = await db.contracts.count_documents({"status": "expired"})
    
    return {
        "total": total,
        "sent": sent,
        "viewed": viewed,
        "signed": signed,
        "expired": expired
    }


# ============ DASHBOARD & REPORTS ============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    total_employees = await db.employees.count_documents({})
    active_employees = await db.employees.count_documents({"status": "active"})
    total_documents = await db.documents.count_documents({})
    total_contracts = await db.contracts.count_documents({})
    pending_signatures = await db.contracts.count_documents({"status": {"$in": ["sent", "viewed"]}})
    
    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "total_documents": total_documents,
        "total_contracts": total_contracts,
        "pending_signatures": pending_signatures
    }

@api_router.get("/activity-logs")
async def get_activity_logs(current_user: dict = Depends(get_current_user), limit: int = 50):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    logs = await db.activity_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return logs


# ============ EMAIL TESTING ROUTE ============

@api_router.post("/send-test-email")
async def send_test_email(email_req: EmailSendRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = await send_email_async(email_req.recipient_email, email_req.subject, email_req.html_content)
    if result:
        return {"message": "Email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
