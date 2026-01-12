"""
Payroll management routes for Nexus HR
Includes Kenyan PAYE, NSSF, and SHIF calculations
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import uuid

from utils.database import db
from utils.security import get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity

router = APIRouter(prefix="/payroll", tags=["Payroll"])


# ============ KENYAN TAX CONSTANTS (2025) ============

# PAYE Tax Brackets (Monthly - KSh)
PAYE_BRACKETS = [
    {"min": 0, "max": 24000, "rate": 0.10},
    {"min": 24001, "max": 32333, "rate": 0.25},
    {"min": 32334, "max": 500000, "rate": 0.30},
    {"min": 500001, "max": 800000, "rate": 0.325},
    {"min": 800001, "max": float('inf'), "rate": 0.35},
]

# Personal Tax Relief (Monthly)
PERSONAL_RELIEF = 2400

# NSSF Rates (Effective Feb 2025)
NSSF_TIER_I_LIMIT = 8000  # First KSh 8,000
NSSF_TIER_II_LIMIT = 72000  # KSh 8,001 to 72,000
NSSF_RATE = 0.06  # 6% for both tiers

# SHIF Rate
SHIF_RATE = 0.0275  # 2.75% of gross salary

# Maximum pension deduction for tax
MAX_PENSION_DEDUCTION = 30000


# ============ MODELS ============

class SalaryStructure(BaseModel):
    employee_number: str
    basic_salary: float
    house_allowance: float = 0
    transport_allowance: float = 0
    medical_allowance: float = 0
    other_allowances: float = 0
    pension_contribution: float = 0  # Employee's pension contribution
    loan_deduction: float = 0
    other_deductions: float = 0
    effective_date: str


class SalaryStructureUpdate(BaseModel):
    basic_salary: Optional[float] = None
    house_allowance: Optional[float] = None
    transport_allowance: Optional[float] = None
    medical_allowance: Optional[float] = None
    other_allowances: Optional[float] = None
    pension_contribution: Optional[float] = None
    loan_deduction: Optional[float] = None
    other_deductions: Optional[float] = None
    effective_date: Optional[str] = None


class PayrollRunRequest(BaseModel):
    company_id: Optional[str] = None
    month: int  # 1-12
    year: int


class CustomTaxConfig(BaseModel):
    company_id: str
    brackets: List[dict]  # [{"min": 0, "max": 24000, "rate": 0.10}, ...]
    personal_relief: float = 2400
    nssf_rate: float = 0.06
    nssf_tier_i_limit: float = 8000
    nssf_tier_ii_limit: float = 72000
    shif_rate: float = 0.0275


# ============ TAX CALCULATION FUNCTIONS ============

def calculate_paye(taxable_income: float, brackets: list = None) -> float:
    """Calculate PAYE tax based on Kenyan tax brackets"""
    if brackets is None:
        brackets = PAYE_BRACKETS
    
    tax = 0
    remaining = taxable_income
    prev_max = 0
    
    for bracket in brackets:
        if remaining <= 0:
            break
        
        bracket_min = bracket["min"]
        bracket_max = bracket["max"]
        rate = bracket["rate"]
        
        # Amount in this bracket
        if taxable_income > bracket_max:
            bracket_amount = bracket_max - prev_max
        else:
            bracket_amount = remaining
        
        if bracket_amount > 0:
            tax += bracket_amount * rate
            remaining -= bracket_amount
        
        prev_max = bracket_max
    
    # Apply personal relief
    tax = max(0, tax - PERSONAL_RELIEF)
    
    return round(tax, 2)


def calculate_nssf(gross_salary: float, tier_i_limit: float = None, tier_ii_limit: float = None, rate: float = None) -> dict:
    """Calculate NSSF contribution (both employee and employer)"""
    tier_i_limit = tier_i_limit or NSSF_TIER_I_LIMIT
    tier_ii_limit = tier_ii_limit or NSSF_TIER_II_LIMIT
    rate = rate or NSSF_RATE
    
    # Tier I: 6% of first 8,000
    tier_i = min(gross_salary, tier_i_limit) * rate
    
    # Tier II: 6% of 8,001 to 72,000
    if gross_salary > tier_i_limit:
        tier_ii_amount = min(gross_salary - tier_i_limit, tier_ii_limit - tier_i_limit)
        tier_ii = tier_ii_amount * rate
    else:
        tier_ii = 0
    
    total = tier_i + tier_ii
    
    return {
        "tier_i": round(tier_i, 2),
        "tier_ii": round(tier_ii, 2),
        "employee_contribution": round(total, 2),
        "employer_contribution": round(total, 2),
        "total": round(total * 2, 2)
    }


def calculate_shif(gross_salary: float, rate: float = None) -> float:
    """Calculate SHIF contribution"""
    rate = rate or SHIF_RATE
    return round(gross_salary * rate, 2)


def calculate_taxable_income(gross_salary: float, pension_contribution: float) -> float:
    """Calculate taxable income after pension deduction"""
    # Pension contribution is tax-deductible up to KSh 30,000
    pension_deduction = min(pension_contribution, MAX_PENSION_DEDUCTION)
    return max(0, gross_salary - pension_deduction)


def generate_payslip(salary_structure: dict, tax_config: dict = None) -> dict:
    """Generate a complete payslip calculation"""
    # Gross salary components
    basic = salary_structure.get("basic_salary", 0)
    house = salary_structure.get("house_allowance", 0)
    transport = salary_structure.get("transport_allowance", 0)
    medical = salary_structure.get("medical_allowance", 0)
    other_allow = salary_structure.get("other_allowances", 0)
    
    gross_salary = basic + house + transport + medical + other_allow
    
    # Pension contribution (employee's own contribution)
    pension = salary_structure.get("pension_contribution", 0)
    
    # Calculate taxable income
    taxable_income = calculate_taxable_income(gross_salary, pension)
    
    # PAYE calculation
    brackets = tax_config.get("brackets") if tax_config else None
    paye = calculate_paye(taxable_income, brackets)
    
    # NSSF calculation
    nssf = calculate_nssf(gross_salary)
    
    # SHIF calculation
    shif = calculate_shif(gross_salary)
    
    # Other deductions
    loan_deduction = salary_structure.get("loan_deduction", 0)
    other_deductions = salary_structure.get("other_deductions", 0)
    
    # Total deductions
    total_deductions = (
        paye + 
        nssf["employee_contribution"] + 
        shif + 
        pension +
        loan_deduction + 
        other_deductions
    )
    
    # Net salary
    net_salary = gross_salary - total_deductions
    
    return {
        "earnings": {
            "basic_salary": basic,
            "house_allowance": house,
            "transport_allowance": transport,
            "medical_allowance": medical,
            "other_allowances": other_allow,
            "gross_salary": round(gross_salary, 2)
        },
        "deductions": {
            "paye": paye,
            "nssf_employee": nssf["employee_contribution"],
            "shif": shif,
            "pension_contribution": pension,
            "loan_deduction": loan_deduction,
            "other_deductions": other_deductions,
            "total_deductions": round(total_deductions, 2)
        },
        "employer_contributions": {
            "nssf_employer": nssf["employer_contribution"]
        },
        "taxable_income": round(taxable_income, 2),
        "net_salary": round(net_salary, 2)
    }


# ============ ROUTES ============

@router.post("/salary-structure")
async def create_salary_structure(salary: SalaryStructure, current_user: dict = Depends(get_current_user)):
    """Create or update salary structure for an employee"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can manage salary structures")
    
    employee = await db.employees.find_one({"employee_number": salary.employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if salary structure already exists
    existing = await db.salary_structures.find_one(
        {"employee_number": salary.employee_number, "is_current": True},
        {"_id": 0}
    )
    
    if existing:
        # Mark old structure as not current
        await db.salary_structures.update_one(
            {"employee_number": salary.employee_number, "is_current": True},
            {"$set": {"is_current": False, "ended_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    structure_id = str(uuid.uuid4())
    structure_doc = {
        "structure_id": structure_id,
        "employee_number": salary.employee_number,
        "employee_name": employee.get("full_name"),
        "company_id": employee.get("company_id"),
        "basic_salary": salary.basic_salary,
        "house_allowance": salary.house_allowance,
        "transport_allowance": salary.transport_allowance,
        "medical_allowance": salary.medical_allowance,
        "other_allowances": salary.other_allowances,
        "pension_contribution": salary.pension_contribution,
        "loan_deduction": salary.loan_deduction,
        "other_deductions": salary.other_deductions,
        "effective_date": salary.effective_date,
        "is_current": True,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.salary_structures.insert_one(structure_doc)
    await log_activity(current_user["user_id"], "salary_structure_created", 
                      f"Created salary structure for {salary.employee_number}")
    
    return {"message": "Salary structure created successfully", "structure_id": structure_id}


@router.get("/salary-structure/{employee_number}")
async def get_salary_structure(employee_number: str, current_user: dict = Depends(get_current_user)):
    """Get salary structure for an employee"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if not employee or employee.get("employee_number") != employee_number:
            raise HTTPException(status_code=403, detail="Access denied")
    
    structure = await db.salary_structures.find_one(
        {"employee_number": employee_number, "is_current": True},
        {"_id": 0}
    )
    
    if not structure:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    
    return structure


@router.patch("/salary-structure/{employee_number}")
async def update_salary_structure(
    employee_number: str, 
    updates: SalaryStructureUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Update salary structure"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can update salary structures")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = await db.salary_structures.update_one(
        {"employee_number": employee_number, "is_current": True},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    
    await log_activity(current_user["user_id"], "salary_structure_updated", 
                      f"Updated salary structure for {employee_number}")
    
    return {"message": "Salary structure updated successfully"}


@router.get("/calculate-payslip/{employee_number}")
async def calculate_employee_payslip(employee_number: str, current_user: dict = Depends(get_current_user)):
    """Calculate payslip for an employee"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if not employee or employee.get("employee_number") != employee_number:
            raise HTTPException(status_code=403, detail="Access denied")
    
    structure = await db.salary_structures.find_one(
        {"employee_number": employee_number, "is_current": True},
        {"_id": 0}
    )
    
    if not structure:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    
    # Check for custom tax config
    tax_config = None
    if employee and employee.get("company_id"):
        config = await db.tax_configs.find_one(
            {"company_id": employee["company_id"], "is_active": True},
            {"_id": 0}
        )
        if config:
            tax_config = config
    
    payslip = generate_payslip(structure, tax_config)
    payslip["employee_number"] = employee_number
    payslip["employee_name"] = structure.get("employee_name")
    payslip["calculated_at"] = datetime.now(timezone.utc).isoformat()
    
    return payslip


@router.post("/run")
async def run_payroll(request: PayrollRunRequest, current_user: dict = Depends(get_current_user)):
    """Run payroll for all employees or a specific company"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can run payroll")
    
    # Build query for employees
    emp_query = {"status": "active"}
    if request.company_id:
        emp_query["company_id"] = request.company_id
    
    employees = await db.employees.find(emp_query, {"_id": 0}).to_list(10000)
    
    payroll_run_id = str(uuid.uuid4())
    period = f"{request.year}-{str(request.month).zfill(2)}"
    
    # Check if payroll already run for this period
    existing_run = await db.payroll_runs.find_one({
        "period": period,
        "company_id": request.company_id,
        "status": {"$in": ["completed", "approved"]}
    }, {"_id": 0})
    
    if existing_run:
        raise HTTPException(
            status_code=400, 
            detail=f"Payroll already run for {period}. Use recalculate endpoint to update."
        )
    
    payslips = []
    total_gross = 0
    total_net = 0
    total_paye = 0
    total_nssf = 0
    total_shif = 0
    processed = 0
    skipped = 0
    
    for employee in employees:
        structure = await db.salary_structures.find_one(
            {"employee_number": employee["employee_number"], "is_current": True},
            {"_id": 0}
        )
        
        if not structure:
            skipped += 1
            continue
        
        # Get custom tax config if any
        tax_config = None
        if employee.get("company_id"):
            config = await db.tax_configs.find_one(
                {"company_id": employee["company_id"], "is_active": True},
                {"_id": 0}
            )
            if config:
                tax_config = config
        
        payslip = generate_payslip(structure, tax_config)
        payslip_id = str(uuid.uuid4())
        
        payslip_doc = {
            "payslip_id": payslip_id,
            "payroll_run_id": payroll_run_id,
            "period": period,
            "employee_number": employee["employee_number"],
            "employee_name": employee.get("full_name"),
            "company_id": employee.get("company_id"),
            "company_name": employee.get("company_name"),
            **payslip,
            "status": "generated",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payslips.insert_one(payslip_doc)
        payslips.append(payslip_doc)
        
        total_gross += payslip["earnings"]["gross_salary"]
        total_net += payslip["net_salary"]
        total_paye += payslip["deductions"]["paye"]
        total_nssf += payslip["deductions"]["nssf_employee"]
        total_shif += payslip["deductions"]["shif"]
        processed += 1
    
    # Create payroll run record
    payroll_run = {
        "payroll_run_id": payroll_run_id,
        "period": period,
        "month": request.month,
        "year": request.year,
        "company_id": request.company_id,
        "employees_processed": processed,
        "employees_skipped": skipped,
        "totals": {
            "gross_salary": round(total_gross, 2),
            "net_salary": round(total_net, 2),
            "paye": round(total_paye, 2),
            "nssf": round(total_nssf, 2),
            "shif": round(total_shif, 2)
        },
        "status": "completed",
        "run_by": current_user["full_name"],
        "run_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payroll_runs.insert_one(payroll_run)
    await log_activity(current_user["user_id"], "payroll_run", f"Payroll run for {period}: {processed} employees")
    
    return {
        "message": f"Payroll run completed for {period}",
        "payroll_run_id": payroll_run_id,
        "employees_processed": processed,
        "employees_skipped": skipped,
        "totals": payroll_run["totals"]
    }


@router.get("/runs")
async def get_payroll_runs(current_user: dict = Depends(get_current_user)):
    """Get all payroll runs"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    runs = await db.payroll_runs.find({}, {"_id": 0}).sort("run_at", -1).to_list(100)
    return runs


@router.get("/payslips/{payroll_run_id}")
async def get_payroll_payslips(payroll_run_id: str, current_user: dict = Depends(get_current_user)):
    """Get all payslips for a payroll run"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    payslips = await db.payslips.find(
        {"payroll_run_id": payroll_run_id},
        {"_id": 0}
    ).to_list(10000)
    
    return payslips


@router.get("/my-payslips")
async def get_my_payslips(current_user: dict = Depends(get_current_user)):
    """Get current user's payslips"""
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        return []
    
    payslips = await db.payslips.find(
        {"employee_number": employee["employee_number"]},
        {"_id": 0}
    ).sort("period", -1).to_list(100)
    
    return payslips


@router.get("/payslip/{payslip_id}")
async def get_payslip(payslip_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific payslip"""
    payslip = await db.payslips.find_one({"payslip_id": payslip_id}, {"_id": 0})
    
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    # Check access
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
        if not employee or employee.get("employee_number") != payslip["employee_number"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return payslip


@router.post("/tax-config")
async def create_custom_tax_config(config: CustomTaxConfig, current_user: dict = Depends(get_current_user)):
    """Create custom tax configuration for a company"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can configure tax settings")
    
    company = await db.companies.find_one({"company_id": config.company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Deactivate existing config
    await db.tax_configs.update_many(
        {"company_id": config.company_id},
        {"$set": {"is_active": False}}
    )
    
    config_id = str(uuid.uuid4())
    config_doc = {
        "config_id": config_id,
        "company_id": config.company_id,
        "company_name": company["company_name"],
        "brackets": config.brackets,
        "personal_relief": config.personal_relief,
        "nssf_rate": config.nssf_rate,
        "nssf_tier_i_limit": config.nssf_tier_i_limit,
        "nssf_tier_ii_limit": config.nssf_tier_ii_limit,
        "shif_rate": config.shif_rate,
        "is_active": True,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tax_configs.insert_one(config_doc)
    await log_activity(current_user["user_id"], "tax_config_created", f"Custom tax config for {company['company_name']}")
    
    return {"message": "Tax configuration created successfully", "config_id": config_id}


@router.get("/tax-config/{company_id}")
async def get_tax_config(company_id: str, current_user: dict = Depends(get_current_user)):
    """Get tax configuration for a company"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    config = await db.tax_configs.find_one(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    )
    
    if not config:
        # Return default Kenya tax config
        return {
            "brackets": PAYE_BRACKETS,
            "personal_relief": PERSONAL_RELIEF,
            "nssf_rate": NSSF_RATE,
            "nssf_tier_i_limit": NSSF_TIER_I_LIMIT,
            "nssf_tier_ii_limit": NSSF_TIER_II_LIMIT,
            "shif_rate": SHIF_RATE,
            "is_default": True
        }
    
    return config


@router.get("/summary")
async def get_payroll_summary(
    year: Optional[int] = None,
    company_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get payroll summary statistics"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    year = year or datetime.now().year
    
    query = {"year": year}
    if company_id:
        query["company_id"] = company_id
    
    runs = await db.payroll_runs.find(query, {"_id": 0}).to_list(100)
    
    total_gross = sum(r["totals"]["gross_salary"] for r in runs)
    total_net = sum(r["totals"]["net_salary"] for r in runs)
    total_paye = sum(r["totals"]["paye"] for r in runs)
    total_nssf = sum(r["totals"]["nssf"] for r in runs)
    total_shif = sum(r["totals"]["shif"] for r in runs)
    
    return {
        "year": year,
        "company_id": company_id,
        "payroll_runs": len(runs),
        "totals": {
            "gross_salary": round(total_gross, 2),
            "net_salary": round(total_net, 2),
            "paye": round(total_paye, 2),
            "nssf": round(total_nssf, 2),
            "shif": round(total_shif, 2)
        },
        "monthly_breakdown": [
            {
                "period": r["period"],
                "totals": r["totals"],
                "employees": r["employees_processed"]
            }
            for r in runs
        ]
    }


@router.post("/send-payslip/{payslip_id}")
async def send_payslip_email(payslip_id: str, current_user: dict = Depends(get_current_user)):
    """Send payslip to employee via email"""
    if current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can send payslips")
    
    payslip = await db.payslips.find_one({"payslip_id": payslip_id}, {"_id": 0})
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    employee = await db.employees.find_one({"employee_number": payslip["employee_number"]}, {"_id": 0})
    if not employee or not employee.get("email"):
        raise HTTPException(status_code=404, detail="Employee email not found")
    
    email_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
        <h2 style="color: #002FA7;">Payslip for {payslip['period']}</h2>
        <p>Dear {payslip['employee_name']},</p>
        <p>Please find your payslip details below:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background: #f5f5f5;">
                <th colspan="2" style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Earnings</th>
            </tr>
            <tr><td style="padding: 8px;">Basic Salary</td><td style="text-align: right;">KSh {payslip['earnings']['basic_salary']:,.2f}</td></tr>
            <tr><td style="padding: 8px;">House Allowance</td><td style="text-align: right;">KSh {payslip['earnings']['house_allowance']:,.2f}</td></tr>
            <tr><td style="padding: 8px;">Transport Allowance</td><td style="text-align: right;">KSh {payslip['earnings']['transport_allowance']:,.2f}</td></tr>
            <tr style="font-weight: bold; background: #f0f0f0;">
                <td style="padding: 10px;">Gross Salary</td>
                <td style="text-align: right;">KSh {payslip['earnings']['gross_salary']:,.2f}</td>
            </tr>
            
            <tr style="background: #f5f5f5;">
                <th colspan="2" style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Deductions</th>
            </tr>
            <tr><td style="padding: 8px;">PAYE Tax</td><td style="text-align: right;">KSh {payslip['deductions']['paye']:,.2f}</td></tr>
            <tr><td style="padding: 8px;">NSSF</td><td style="text-align: right;">KSh {payslip['deductions']['nssf_employee']:,.2f}</td></tr>
            <tr><td style="padding: 8px;">SHIF</td><td style="text-align: right;">KSh {payslip['deductions']['shif']:,.2f}</td></tr>
            <tr style="font-weight: bold; background: #f0f0f0;">
                <td style="padding: 10px;">Total Deductions</td>
                <td style="text-align: right;">KSh {payslip['deductions']['total_deductions']:,.2f}</td>
            </tr>
            
            <tr style="font-weight: bold; background: #002FA7; color: white;">
                <td style="padding: 12px;">Net Salary</td>
                <td style="text-align: right; font-size: 18px;">KSh {payslip['net_salary']:,.2f}</td>
            </tr>
        </table>
        
        <p style="color: #666; font-size: 12px;">This is a system-generated payslip. For any queries, please contact HR.</p>
    </div>
    """
    
    await send_email_async(employee["email"], f"Payslip for {payslip['period']}", email_html)
    
    await db.payslips.update_one(
        {"payslip_id": payslip_id},
        {"$set": {"email_sent": True, "email_sent_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Payslip sent successfully"}
