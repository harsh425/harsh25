"""
Contract management routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import os

from utils.database import db
from utils.security import get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity

router = APIRouter(prefix="/contracts", tags=["Contracts"])


# Models
class ContractCreate(BaseModel):
    employee_id: str
    title: str
    description: str
    expiry_days: int = 30


class ContractSign(BaseModel):
    signature_data: str
    signature_type: str = "drawn"
    ip_address: Optional[str] = None


# Routes
@router.post("")
async def create_contract(contract: ContractCreate, current_user: dict = Depends(get_current_user)):
    """Create and send a contract"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create contracts")
    
    employee = await db.employees.find_one({"employee_id": contract.employee_id}, {"_id": 0})
    if not employee:
        # Try finding by employee_number
        employee = await db.employees.find_one({"employee_number": contract.employee_id}, {"_id": 0})
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
    
    frontend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:3000").replace(":8001", ":3000")
    signing_url = f"{frontend_url}/sign-contract/{signing_token}"
    
    email_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>New Employment Contract</h2>
        <p>Hello {employee.get('full_name', employee.get('first_name', 'Employee'))},</p>
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


@router.get("")
async def get_contracts(current_user: dict = Depends(get_current_user)):
    """Get contracts"""
    if current_user["role"] == "admin":
        contracts = await db.contracts.find({}, {"_id": 0, "signing_token": 0}).to_list(1000)
    else:
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if employee:
            contracts = await db.contracts.find(
                {"employee_id": {"$in": [employee.get("employee_id"), employee.get("employee_number")]}},
                {"_id": 0, "signing_token": 0}
            ).to_list(1000)
        else:
            contracts = []
    
    return contracts


@router.get("/sign/{signing_token}")
async def get_contract_for_signing(signing_token: str):
    """Get contract for signing"""
    contract = await db.contracts.find_one({"signing_token": signing_token}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    expiry = datetime.fromisoformat(contract["expiry_date"])
    if datetime.now(timezone.utc) > expiry:
        await db.contracts.update_one(
            {"signing_token": signing_token},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=400, detail="Contract link has expired")
    
    if not contract.get("viewed_at"):
        await db.contracts.update_one(
            {"signing_token": signing_token},
            {"$set": {"viewed_at": datetime.now(timezone.utc).isoformat(), "status": "viewed"}}
        )
    
    employee = await db.employees.find_one({"employee_id": contract["employee_id"]}, {"_id": 0})
    if not employee:
        employee = await db.employees.find_one({"employee_number": contract["employee_id"]}, {"_id": 0})
    
    return {**contract, "employee": employee}


@router.post("/sign/{signing_token}")
async def sign_contract(signing_token: str, signature: ContractSign):
    """Sign a contract"""
    contract = await db.contracts.find_one({"signing_token": signing_token}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract["status"] == "signed":
        raise HTTPException(status_code=400, detail="Contract already signed")
    
    expiry = datetime.fromisoformat(contract["expiry_date"])
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="Contract link has expired")
    
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
    
    employee = await db.employees.find_one({"employee_id": contract["employee_id"]}, {"_id": 0})
    if not employee:
        employee = await db.employees.find_one({"employee_number": contract["employee_id"]}, {"_id": 0})
    
    if employee:
        email_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Contract Signed Successfully</h2>
            <p>Hello {employee.get('full_name', 'Employee')},</p>
            <p>You have successfully signed the contract: <strong>{contract['title']}</strong></p>
            <p>Signed on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        """
        await send_email_async(employee["email"], "Contract Signed", email_html)
    
    return {"message": "Contract signed successfully"}


@router.get("/stats")
async def get_contract_stats(current_user: dict = Depends(get_current_user)):
    """Get contract statistics"""
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
