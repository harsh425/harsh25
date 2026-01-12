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


# ============ MODELS ============

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # "admin" or "employee"

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


# ============ EMPLOYEE MANAGEMENT ROUTES ============

@api_router.post("/employees")
async def create_employee(employee: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only admins and HR assistants can create employees")
    
    existing = await db.employees.find_one({"employee_number": employee.employee_number}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Employee number already exists")
    
    emp_doc = employee.model_dump()
    emp_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    emp_doc["status"] = "active"
    emp_doc["created_by"] = current_user["user_id"]
    emp_doc["full_name"] = f"{employee.first_name} {employee.last_name}"  # For backward compatibility
    
    # Initialize leave balances (Kenyan labor law: 21 days annual leave)
    emp_doc["leave_balance"] = {
        "annual": 21,
        "sick": 30,  # Not usually limited but tracked
        "maternity": 0,  # Allocated as needed
        "paternity": 0   # Allocated as needed
    }
    
    await db.employees.insert_one(emp_doc)
    await log_activity(current_user["user_id"], "employee_created", f"Created employee {employee.employee_number}")
    
    return {"message": "Employee created successfully", "employee_number": employee.employee_number}

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


@api_router.post("/employees/bulk-import")
async def bulk_import_employees(import_data: BulkEmployeeImport, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only admins and HR assistants can import employees")
    
    success_count = 0
    failed_count = 0
    errors = []
    
    for emp in import_data.employees:
        try:
            # Check if employee number already exists
            existing = await db.employees.find_one({"employee_number": emp.employee_number}, {"_id": 0})
            if existing:
                failed_count += 1
                errors.append(f"Employee number {emp.employee_number} already exists")
                continue
            
            emp_doc = emp.model_dump()
            emp_doc["created_at"] = datetime.now(timezone.utc).isoformat()
            emp_doc["status"] = "active"
            emp_doc["created_by"] = current_user["user_id"]
            emp_doc["full_name"] = f"{emp.first_name} {emp.last_name}"
            
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
            errors.append(f"Failed to import {emp.employee_number}: {str(e)}")
    
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
    expiry_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Check permissions
    if current_user["role"] != "admin":
        employee = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
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
        "filename": file.filename,
        "file_id": str(file_id),
        "uploaded_by": current_user["user_id"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "content_type": file.content_type,
        "expiry_date": expiry_date,
        "expiry_notified": False
    }
    
    await db.documents.insert_one(doc_meta)
    await log_activity(current_user["user_id"], "document_uploaded", f"Uploaded {category} document for {employee_id}")
    
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
