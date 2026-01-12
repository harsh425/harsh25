from pydantic import BaseModel, EmailStr
from typing import List, Optional


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


class BulkEmployeeImport(BaseModel):
    employees: List[EmployeeCreate]


class EmployeeTransfer(BaseModel):
    to_company_id: str
    transfer_date: str
    reason: str
