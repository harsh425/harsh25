"""
Company management routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid

from utils.database import db
from utils.security import get_current_user
from utils.helpers import log_activity

router = APIRouter(prefix="/companies", tags=["Companies"])


# Models
class CompanyCreate(BaseModel):
    company_name: str
    prefix: str
    contact_email: EmailStr
    phone_number: str
    address: str
    registration_number: str


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    registration_number: Optional[str] = None
    status: Optional[str] = None


# Routes
@router.post("")
async def create_company(company: CompanyCreate, current_user: dict = Depends(get_current_user)):
    """Create a new company"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create companies")
    
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


@router.get("")
async def get_companies(current_user: dict = Depends(get_current_user)):
    """Get all companies"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    companies = await db.companies.find({}, {"_id": 0}).to_list(100)
    return companies


@router.get("/{company_id}")
async def get_company(company_id: str, current_user: dict = Depends(get_current_user)):
    """Get a company by ID"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company


@router.patch("/{company_id}")
async def update_company(company_id: str, updates: CompanyUpdate, current_user: dict = Depends(get_current_user)):
    """Update a company"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update companies")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
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
