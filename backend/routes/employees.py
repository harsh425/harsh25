"""
Employee management routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from utils.database import db
from utils.security import get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity

router = APIRouter(prefix="/employees", tags=["Employees"])


# Models
class EmployeeCreate(BaseModel):
    company_id: str
    employee_number: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    marital_status: str
    email: EmailStr
    phone_number: str
    mpesa_number: str
    kra_pin: str
    nssf_number: str
    shif_number: str
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relationship: str
    emergency_contact_email: EmailStr
    bank_account_name: str
    bank_name: str
    bank_branch_name: str
    bank_branch_code: str
    bank_account_number: str
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


class EmployeeTransfer(BaseModel):
    to_company_id: str
    transfer_date: str
    reason: str


class BulkEmployeeImport(BaseModel):
    employees: List[EmployeeCreate]


# Routes
@router.post("")
async def create_employee(employee: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    """Create a new employee"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only admins and HR assistants can create employees")
    
    company = await db.companies.find_one({"company_id": employee.company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if company["status"] != "active":
        raise HTTPException(status_code=400, detail="Cannot add employees to inactive company")
    
    if not employee.employee_number.upper().startswith(company["prefix"]):
        raise HTTPException(
            status_code=400,
            detail=f"Employee number must start with company prefix '{company['prefix']}'"
        )
    
    existing = await db.employees.find_one({
        "employee_number": employee.employee_number.upper(),
        "status": {"$in": ["active", "on_leave"]}
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Employee number '{employee.employee_number.upper()}' already exists for an active employee."
        )
    
    emp_doc = employee.model_dump()
    emp_doc["employee_number"] = employee.employee_number.upper()
    emp_doc["company_name"] = company["company_name"]
    emp_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    emp_doc["status"] = "active"
    emp_doc["created_by"] = current_user["user_id"]
    emp_doc["full_name"] = f"{employee.first_name} {employee.last_name}"
    emp_doc["transfer_history"] = []
    emp_doc["leave_balance"] = {
        "annual": 21,
        "sick": 30,
        "maternity": 0,
        "paternity": 0
    }
    
    await db.employees.insert_one(emp_doc)
    await log_activity(current_user["user_id"], "employee_created", f"Created employee {employee.employee_number.upper()}")
    
    return {"message": "Employee created successfully", "employee_number": employee.employee_number.upper()}


@router.get("")
async def get_all_employees(current_user: dict = Depends(get_current_user)):
    """Get all employees based on user role"""
    if current_user["role"] in ["admin", "hr_assistant", "director", "manager"]:
        if current_user["role"] == "manager":
            employees = await db.employees.find({
                "$or": [
                    {"manager_id": current_user["user_id"]},
                    {"email": current_user["email"]}
                ]
            }, {"_id": 0}).to_list(1000)
        else:
            employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
    else:
        employees = await db.employees.find({"email": current_user["email"]}, {"_id": 0}).to_list(1)
    
    return employees


@router.get("/{employee_number}")
async def get_employee(employee_number: str, current_user: dict = Depends(get_current_user)):
    """Get employee by employee number"""
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        if employee["email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return employee


@router.patch("/{employee_number}")
async def update_employee(employee_number: str, updates: EmployeeUpdate, current_user: dict = Depends(get_current_user)):
    """Update employee"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only admins and HR assistants can update employees")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
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


@router.delete("/{employee_number}")
async def deactivate_employee(employee_number: str, current_user: dict = Depends(get_current_user)):
    """Deactivate employee"""
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


@router.post("/{employee_number}/transfer")
async def transfer_employee(employee_number: str, transfer: EmployeeTransfer, current_user: dict = Depends(get_current_user)):
    """Transfer employee to another company"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can transfer employees")
    
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    to_company = await db.companies.find_one({"company_id": transfer.to_company_id}, {"_id": 0})
    if not to_company:
        raise HTTPException(status_code=404, detail="Target company not found")
    
    if to_company["status"] != "active":
        raise HTTPException(status_code=400, detail="Cannot transfer to inactive company")
    
    from_company_id = employee.get("company_id")
    from_company_name = employee.get("company_name", "Unknown")
    
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


@router.get("/{employee_number}/transfers")
async def get_employee_transfers(employee_number: str, current_user: dict = Depends(get_current_user)):
    """Get transfer history for an employee"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
        if not employee or employee.get("email") != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    transfers = await db.transfers.find({"employee_number": employee_number}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return transfers


@router.post("/bulk-import")
async def bulk_import_employees(import_data: BulkEmployeeImport, current_user: dict = Depends(get_current_user)):
    """Bulk import employees"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only admins and HR assistants can import employees")
    
    success_count = 0
    failed_count = 0
    errors = []
    
    for emp in import_data.employees:
        try:
            company = await db.companies.find_one({"company_id": emp.company_id}, {"_id": 0})
            if not company:
                failed_count += 1
                errors.append(f"Employee {emp.employee_number}: Company not found")
                continue
            
            if not emp.employee_number.upper().startswith(company["prefix"]):
                failed_count += 1
                errors.append(f"Employee {emp.employee_number}: Must start with prefix '{company['prefix']}'")
                continue
            
            existing = await db.employees.find_one({
                "employee_number": emp.employee_number.upper(),
                "status": {"$in": ["active", "on_leave"]}
            }, {"_id": 0})
            
            if existing:
                failed_count += 1
                errors.append(f"Employee {emp.employee_number}: Already exists")
                continue
            
            emp_doc = emp.model_dump()
            emp_doc["employee_number"] = emp.employee_number.upper()
            emp_doc["company_name"] = company["company_name"]
            emp_doc["created_at"] = datetime.now(timezone.utc).isoformat()
            emp_doc["status"] = "active"
            emp_doc["created_by"] = current_user["user_id"]
            emp_doc["full_name"] = f"{emp.first_name} {emp.last_name}"
            emp_doc["transfer_history"] = []
            emp_doc["leave_balance"] = {"annual": 21, "sick": 30, "maternity": 0, "paternity": 0}
            
            await db.employees.insert_one(emp_doc)
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            errors.append(f"Employee {emp.employee_number}: {str(e)}")
    
    await log_activity(current_user["user_id"], "bulk_import", f"Imported {success_count} employees, {failed_count} failed")
    
    return {
        "message": f"Import completed: {success_count} successful, {failed_count} failed",
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors[:20]
    }
