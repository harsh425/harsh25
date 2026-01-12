"""
Onboarding workflow routes for Nexus HR
Automated document requests and progress tracking for new hires
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

from utils.database import db
from utils.security import get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# ============ DEFAULT DOCUMENT CHECKLIST ============

DEFAULT_CHECKLIST = [
    {
        "item_id": "id_copy",
        "name": "Copy of ID / Passport",
        "description": "A clear copy of your National ID or Passport (front and back)",
        "category": "identity",
        "required": True,
        "order": 1
    },
    {
        "item_id": "kra_pin",
        "name": "KRA PIN Certificate",
        "description": "Kenya Revenue Authority PIN registration certificate",
        "category": "statutory",
        "required": True,
        "order": 2
    },
    {
        "item_id": "nssf_card",
        "name": "NSSF Card / Statement",
        "description": "National Social Security Fund membership card or statement",
        "category": "statutory",
        "required": True,
        "order": 3
    },
    {
        "item_id": "sha_card",
        "name": "SHA Card / Statement",
        "description": "Social Health Authority (formerly NHIF) card or statement",
        "category": "statutory",
        "required": True,
        "order": 4
    },
    {
        "item_id": "bank_details",
        "name": "Bank Details",
        "description": "Bank account details: Bank Name, Branch, and Account Number (provide a bank statement or letter)",
        "category": "financial",
        "required": True,
        "order": 5
    },
    {
        "item_id": "passport_photos",
        "name": "2 Passport Size Photographs",
        "description": "Two recent passport size photographs (colored, white background)",
        "category": "identity",
        "required": True,
        "order": 6
    },
    {
        "item_id": "education_certificates",
        "name": "Educational & Professional Certificates",
        "description": "Copies of educational certificates (degree, diploma, etc.) and professional certifications",
        "category": "qualifications",
        "required": True,
        "order": 7
    }
]


# ============ MODELS ============

class OnboardingCreate(BaseModel):
    employee_number: str
    start_date: str
    welcome_message: Optional[str] = None
    additional_items: Optional[List[dict]] = None


class ChecklistItemUpdate(BaseModel):
    status: str  # pending, submitted, approved, rejected
    notes: Optional[str] = None


class OnboardingChecklistItem(BaseModel):
    item_id: str
    name: str
    description: str
    category: str
    required: bool = True


class OnboardingTemplateCreate(BaseModel):
    company_id: str
    name: str
    checklist_items: List[OnboardingChecklistItem]


# ============ ROUTES ============

@router.post("/start")
async def start_onboarding(onboarding: OnboardingCreate, current_user: dict = Depends(get_current_user)):
    """Start onboarding process for a new employee"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can start onboarding")
    
    employee = await db.employees.find_one({"employee_number": onboarding.employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if onboarding already exists
    existing = await db.onboarding.find_one({
        "employee_number": onboarding.employee_number,
        "status": {"$in": ["in_progress", "pending"]}
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Onboarding already in progress for this employee")
    
    # Get company-specific template or use default
    template = await db.onboarding_templates.find_one({
        "company_id": employee.get("company_id"),
        "is_active": True
    }, {"_id": 0})
    
    checklist_items = template["checklist_items"] if template else DEFAULT_CHECKLIST
    
    # Add any additional items
    if onboarding.additional_items:
        for item in onboarding.additional_items:
            checklist_items.append({
                "item_id": str(uuid.uuid4()),
                "name": item.get("name"),
                "description": item.get("description", ""),
                "category": item.get("category", "other"),
                "required": item.get("required", True),
                "order": len(checklist_items) + 1
            })
    
    # Create checklist with status tracking
    checklist = []
    for item in checklist_items:
        checklist.append({
            **item,
            "status": "pending",
            "submitted_at": None,
            "document_id": None,
            "approved_by": None,
            "approved_at": None,
            "notes": None
        })
    
    onboarding_id = str(uuid.uuid4())
    onboarding_doc = {
        "onboarding_id": onboarding_id,
        "employee_number": onboarding.employee_number,
        "employee_name": employee.get("full_name"),
        "employee_email": employee.get("email"),
        "company_id": employee.get("company_id"),
        "company_name": employee.get("company_name"),
        "start_date": onboarding.start_date,
        "welcome_message": onboarding.welcome_message,
        "checklist": checklist,
        "total_items": len(checklist),
        "completed_items": 0,
        "progress_percentage": 0,
        "status": "in_progress",
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    
    await db.onboarding.insert_one(onboarding_doc)
    await log_activity(current_user["user_id"], "onboarding_started", f"Started onboarding for {onboarding.employee_number}")
    
    # Send welcome email with document requests
    if employee.get("email"):
        checklist_html = ""
        for item in checklist:
            checklist_html += f"""
            <li style="margin-bottom: 10px;">
                <strong>{item['name']}</strong>
                <br><span style="color: #666; font-size: 14px;">{item['description']}</span>
            </li>
            """
        
        email_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
            <h2 style="color: #002FA7;">Welcome to {employee.get('company_name', 'the Team')}!</h2>
            
            <p>Dear {employee.get('first_name', 'Employee')},</p>
            
            {f'<p>{onboarding.welcome_message}</p>' if onboarding.welcome_message else ''}
            
            <p>As part of your onboarding process, please submit the following documents:</p>
            
            <ol style="line-height: 1.8;">
                {checklist_html}
            </ol>
            
            <p>Your start date is: <strong>{onboarding.start_date}</strong></p>
            
            <p>Please log in to the HR portal to upload your documents. If you have any questions, please contact HR.</p>
            
            <div style="margin-top: 30px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                <p style="margin: 0; color: #666; font-size: 14px;">
                    <strong>Tip:</strong> Ensure all documents are clear and readable. Scanned copies or photos are acceptable.
                </p>
            </div>
            
            <p style="margin-top: 20px;">
                Best regards,<br>
                HR Team
            </p>
        </div>
        """
        
        await send_email_async(employee["email"], f"Welcome! Your Onboarding Documents Required", email_html)
    
    return {
        "message": "Onboarding started successfully",
        "onboarding_id": onboarding_id,
        "checklist_items": len(checklist)
    }


@router.get("")
async def get_all_onboarding(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all onboarding records"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = {}
    if status:
        query["status"] = status
    if company_id:
        query["company_id"] = company_id
    
    onboardings = await db.onboarding.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return onboardings


@router.get("/{onboarding_id}")
async def get_onboarding(onboarding_id: str, current_user: dict = Depends(get_current_user)):
    """Get onboarding details"""
    onboarding = await db.onboarding.find_one({"onboarding_id": onboarding_id}, {"_id": 0})
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    # Check access
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if not employee or employee.get("employee_number") != onboarding["employee_number"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return onboarding


@router.get("/employee/{employee_number}")
async def get_employee_onboarding(employee_number: str, current_user: dict = Depends(get_current_user)):
    """Get onboarding for a specific employee"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if not employee or employee.get("employee_number") != employee_number:
            raise HTTPException(status_code=403, detail="Access denied")
    
    onboarding = await db.onboarding.find_one({
        "employee_number": employee_number,
        "status": {"$in": ["in_progress", "pending"]}
    }, {"_id": 0})
    
    if not onboarding:
        # Check for completed onboarding
        onboarding = await db.onboarding.find_one(
            {"employee_number": employee_number},
            {"_id": 0}
        )
    
    return onboarding


@router.patch("/{onboarding_id}/item/{item_id}")
async def update_checklist_item(
    onboarding_id: str,
    item_id: str,
    update: ChecklistItemUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a checklist item status"""
    onboarding = await db.onboarding.find_one({"onboarding_id": onboarding_id}, {"_id": 0})
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    # Find and update the item
    updated = False
    completed_count = 0
    
    for item in onboarding["checklist"]:
        if item["item_id"] == item_id:
            item["status"] = update.status
            item["notes"] = update.notes
            
            if update.status == "submitted":
                item["submitted_at"] = datetime.now(timezone.utc).isoformat()
            elif update.status == "approved":
                item["approved_by"] = current_user["full_name"]
                item["approved_at"] = datetime.now(timezone.utc).isoformat()
            
            updated = True
        
        if item["status"] == "approved":
            completed_count += 1
    
    if not updated:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    # Calculate progress
    total_items = len(onboarding["checklist"])
    progress = round((completed_count / total_items) * 100, 1)
    
    # Check if all items are approved
    status = "in_progress"
    completed_at = None
    if completed_count == total_items:
        status = "completed"
        completed_at = datetime.now(timezone.utc).isoformat()
    
    await db.onboarding.update_one(
        {"onboarding_id": onboarding_id},
        {"$set": {
            "checklist": onboarding["checklist"],
            "completed_items": completed_count,
            "progress_percentage": progress,
            "status": status,
            "completed_at": completed_at
        }}
    )
    
    await log_activity(current_user["user_id"], "onboarding_item_updated", 
                      f"Updated {item_id} to {update.status} for {onboarding['employee_number']}")
    
    # Send notification if completed
    if status == "completed":
        employee = await db.employees.find_one({"employee_number": onboarding["employee_number"]}, {"_id": 0})
        if employee and employee.get("email"):
            email_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #10B981;">Onboarding Complete!</h2>
                <p>Dear {employee.get('first_name', 'Employee')},</p>
                <p>Congratulations! Your onboarding process is now complete. All required documents have been submitted and approved.</p>
                <p>Welcome to the team!</p>
            </div>
            """
            await send_email_async(employee["email"], "Onboarding Complete - Welcome!", email_html)
    
    return {
        "message": f"Item updated to {update.status}",
        "progress_percentage": progress,
        "status": status
    }


@router.post("/submit-document/{onboarding_id}/{item_id}")
async def submit_document_for_item(
    onboarding_id: str,
    item_id: str,
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Link a document to a checklist item"""
    onboarding = await db.onboarding.find_one({"onboarding_id": onboarding_id}, {"_id": 0})
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    # Verify document exists
    document = await db.documents.find_one({"document_id": document_id}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update the checklist item
    for item in onboarding["checklist"]:
        if item["item_id"] == item_id:
            item["document_id"] = document_id
            item["status"] = "submitted"
            item["submitted_at"] = datetime.now(timezone.utc).isoformat()
            break
    
    await db.onboarding.update_one(
        {"onboarding_id": onboarding_id},
        {"$set": {"checklist": onboarding["checklist"]}}
    )
    
    # Notify HR
    hr_users = await db.users.find({"role": {"$in": ["admin", "hr_assistant"]}}, {"_id": 0}).to_list(5)
    for hr in hr_users[:1]:
        if hr.get("email"):
            email_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Document Submitted for Review</h2>
                <p>{onboarding['employee_name']} has submitted a document for onboarding review:</p>
                <p><strong>Document:</strong> {document.get('filename', 'Unknown')}</p>
                <p>Please review and approve/reject the submission.</p>
            </div>
            """
            await send_email_async(hr["email"], "Onboarding Document Submitted", email_html)
    
    return {"message": "Document submitted successfully"}


@router.post("/send-reminder/{onboarding_id}")
async def send_onboarding_reminder(onboarding_id: str, current_user: dict = Depends(get_current_user)):
    """Send reminder email for pending documents"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can send reminders")
    
    onboarding = await db.onboarding.find_one({"onboarding_id": onboarding_id}, {"_id": 0})
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    if onboarding["status"] == "completed":
        raise HTTPException(status_code=400, detail="Onboarding already completed")
    
    # Get pending items
    pending_items = [item for item in onboarding["checklist"] if item["status"] == "pending"]
    
    if not pending_items:
        return {"message": "No pending items to remind about"}
    
    employee = await db.employees.find_one({"employee_number": onboarding["employee_number"]}, {"_id": 0})
    if not employee or not employee.get("email"):
        raise HTTPException(status_code=404, detail="Employee email not found")
    
    pending_html = ""
    for item in pending_items:
        pending_html += f"<li>{item['name']}</li>"
    
    email_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #FF6B00;">Reminder: Outstanding Documents</h2>
        <p>Dear {employee.get('first_name', 'Employee')},</p>
        <p>This is a friendly reminder that the following onboarding documents are still pending:</p>
        <ul style="line-height: 1.8;">
            {pending_html}
        </ul>
        <p>Please log in to the HR portal to upload your documents at your earliest convenience.</p>
        <p>If you have any questions, please contact HR.</p>
    </div>
    """
    
    await send_email_async(employee["email"], "Reminder: Onboarding Documents Pending", email_html)
    
    await log_activity(current_user["user_id"], "onboarding_reminder_sent", 
                      f"Sent reminder to {onboarding['employee_number']}")
    
    return {"message": "Reminder sent successfully", "pending_items": len(pending_items)}


@router.post("/template")
async def create_onboarding_template(template: OnboardingTemplateCreate, current_user: dict = Depends(get_current_user)):
    """Create custom onboarding template for a company"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create templates")
    
    company = await db.companies.find_one({"company_id": template.company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Deactivate existing template
    await db.onboarding_templates.update_many(
        {"company_id": template.company_id},
        {"$set": {"is_active": False}}
    )
    
    template_id = str(uuid.uuid4())
    template_doc = {
        "template_id": template_id,
        "company_id": template.company_id,
        "company_name": company["company_name"],
        "name": template.name,
        "checklist_items": [item.model_dump() for item in template.checklist_items],
        "is_active": True,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.onboarding_templates.insert_one(template_doc)
    await log_activity(current_user["user_id"], "onboarding_template_created", 
                      f"Created template for {company['company_name']}")
    
    return {"message": "Template created successfully", "template_id": template_id}


@router.get("/template/{company_id}")
async def get_onboarding_template(company_id: str, current_user: dict = Depends(get_current_user)):
    """Get onboarding template for a company"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    template = await db.onboarding_templates.find_one(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    )
    
    if not template:
        # Return default checklist
        return {
            "checklist_items": DEFAULT_CHECKLIST,
            "is_default": True
        }
    
    return template


@router.get("/default-checklist")
async def get_default_checklist(current_user: dict = Depends(get_current_user)):
    """Get the default onboarding checklist"""
    return {"checklist_items": DEFAULT_CHECKLIST}


@router.get("/dashboard/stats")
async def get_onboarding_stats(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get onboarding statistics"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = {}
    if company_id:
        query["company_id"] = company_id
    
    total = await db.onboarding.count_documents(query)
    in_progress = await db.onboarding.count_documents({**query, "status": "in_progress"})
    completed = await db.onboarding.count_documents({**query, "status": "completed"})
    
    # Calculate average completion rate
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "avg_progress": {"$avg": "$progress_percentage"}}}
    ]
    avg_result = await db.onboarding.aggregate(pipeline).to_list(1)
    avg_progress = round(avg_result[0]["avg_progress"], 1) if avg_result else 0
    
    return {
        "total": total,
        "in_progress": in_progress,
        "completed": completed,
        "average_progress": avg_progress
    }
