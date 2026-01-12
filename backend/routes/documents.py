"""
Document management routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
from bson import ObjectId
from fastapi.responses import StreamingResponse
import io

from utils.database import db, fs
from utils.security import get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity

router = APIRouter(prefix="/documents", tags=["Documents"])


# Models
class EmailSendRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    html_content: str


# Routes
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    employee_id: str = None,
    category: str = "general",
    expiry_date: Optional[str] = None,
    metadata: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Upload a document"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        # Employees can upload their own documents
        if employee_id:
            employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
            if not employee or employee.get("employee_number") != employee_id:
                raise HTTPException(status_code=403, detail="Can only upload your own documents")
        else:
            employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
            employee_id = employee.get("employee_number") if employee else None
    
    # Read file content
    content = await file.read()
    
    # Store in GridFS
    file_id = await fs.upload_from_stream(
        file.filename,
        content,
        metadata={
            "content_type": file.content_type,
            "employee_id": employee_id,
            "category": category
        }
    )
    
    # Parse metadata if provided
    import json
    meta_dict = {}
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except:
            pass
    
    document_doc = {
        "document_id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "category": category,
        "file_id": str(file_id),
        "expiry_date": expiry_date,
        "metadata": meta_dict,
        "uploaded_by": current_user["user_id"],
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(document_doc)
    await log_activity(current_user["user_id"], "document_uploaded", f"Uploaded {file.filename} for {employee_id}")
    
    return {"message": "Document uploaded successfully", "document_id": document_doc["document_id"]}


@router.get("/employee/{employee_id}")
async def get_employee_documents(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get documents for an employee"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if not employee or employee.get("employee_number") != employee_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    documents = await db.documents.find({"employee_id": employee_id}, {"_id": 0}).to_list(1000)
    return documents


@router.get("")
async def get_documents(employee_id: Optional[str] = None, category_prefix: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get documents with optional filters"""
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if category_prefix:
        query["category"] = {"$regex": f"^{category_prefix}", "$options": "i"}
    
    documents = await db.documents.find(query, {"_id": 0}).to_list(1000)
    return documents


@router.get("/{document_id}/download")
async def download_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Download a document"""
    document = await db.documents.find_one({"document_id": document_id}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if not employee or employee.get("employee_number") != document["employee_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get file from GridFS
    try:
        grid_out = await fs.open_download_stream(ObjectId(document["file_id"]))
        content = await grid_out.read()
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=document.get("content_type", "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={document['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found in storage")


@router.delete("/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can delete documents")
    
    document = await db.documents.find_one({"document_id": document_id}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from GridFS
    try:
        await fs.delete(ObjectId(document["file_id"]))
    except:
        pass
    
    await db.documents.delete_one({"document_id": document_id})
    await log_activity(current_user["user_id"], "document_deleted", f"Deleted document {document_id}")
    
    return {"message": "Document deleted successfully"}


@router.get("/expiring-soon")
async def get_expiring_documents(days: int = 30, current_user: dict = Depends(get_current_user)):
    """Get documents expiring soon"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    cutoff_date = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    
    documents = await db.documents.find({
        "expiry_date": {"$ne": None, "$lte": cutoff_date}
    }, {"_id": 0}).to_list(1000)
    
    return documents


@router.post("/send-expiry-reminders")
async def send_expiry_reminders(current_user: dict = Depends(get_current_user)):
    """Send reminders for expiring documents"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can send reminders")
    
    cutoff_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    documents = await db.documents.find({
        "expiry_date": {"$ne": None, "$lte": cutoff_date}
    }, {"_id": 0}).to_list(1000)
    
    employees_notified = set()
    
    for doc in documents:
        employee_id = doc.get("employee_id")
        if employee_id and employee_id not in employees_notified:
            employee = await db.employees.find_one({"employee_number": employee_id}, {"_id": 0})
            if employee and employee.get("email"):
                email_html = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Document Expiry Reminder</h2>
                    <p>Hello {employee.get('full_name', 'Employee')},</p>
                    <p>You have documents expiring soon. Please update them to avoid any issues:</p>
                    <ul>
                        <li>{doc['filename']} - Expires: {doc['expiry_date']}</li>
                    </ul>
                    <p>Please log in to upload updated documents.</p>
                </div>
                """
                await send_email_async(employee["email"], "Document Expiry Reminder", email_html)
                employees_notified.add(employee_id)
    
    return {"message": f"Sent reminders to {len(employees_notified)} employees"}
