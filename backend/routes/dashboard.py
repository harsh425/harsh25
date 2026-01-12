"""
Dashboard routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from utils.database import db
from utils.security import get_current_user
from utils.email import send_email_async

router = APIRouter(tags=["Dashboard"])


# Models
class EmailSendRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    html_content: str


# Routes
@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
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


@router.get("/activity-logs")
async def get_activity_logs(current_user: dict = Depends(get_current_user), limit: int = 50):
    """Get activity logs"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    logs = await db.activity_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return logs


@router.post("/send-test-email")
async def send_test_email(email_req: EmailSendRequest, current_user: dict = Depends(get_current_user)):
    """Send a test email"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = await send_email_async(email_req.recipient_email, email_req.subject, email_req.html_content)
    if result:
        return {"message": "Email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")
