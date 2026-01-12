from pydantic import BaseModel, EmailStr
from typing import Optional


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
