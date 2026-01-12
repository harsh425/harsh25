"""
Leave management routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid

from utils.database import db
from utils.security import get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity, calculate_working_days
from utils.constants import KENYAN_HOLIDAYS, KENYAN_HOLIDAYS_2025

router = APIRouter(prefix="/leave", tags=["Leave"])


# Models
class LeaveRequest(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    reason: str


class LeaveApproval(BaseModel):
    status: str
    comments: Optional[str] = None


# Routes
@router.post("/request")
async def create_leave_request(leave_req: LeaveRequest, current_user: dict = Depends(get_current_user)):
    """Submit a leave request"""
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    days_requested = calculate_working_days(leave_req.start_date, leave_req.end_date)
    
    if days_requested <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    if leave_req.leave_type == "Annual":
        if employee.get("leave_balance", {}).get("annual", 0) < days_requested:
            raise HTTPException(status_code=400, detail="Insufficient annual leave balance")
    
    approval_levels = ["manager"]
    if employee.get("manager_id"):
        approval_levels.append("hr_admin")
        if days_requested > 14:
            approval_levels.append("director")
    else:
        approval_levels = ["hr_admin"]
        if days_requested > 14:
            approval_levels.append("director")
    
    leave_id = str(uuid.uuid4())
    leave_doc = {
        "leave_id": leave_id,
        "employee_number": employee["employee_number"],
        "employee_name": employee.get("full_name", f"{employee.get('first_name', '')} {employee.get('last_name', '')}"),
        "leave_type": leave_req.leave_type,
        "start_date": leave_req.start_date,
        "end_date": leave_req.end_date,
        "days_requested": days_requested,
        "reason": leave_req.reason,
        "status": "pending",
        "current_approval_level": approval_levels[0],
        "approval_levels": approval_levels,
        "approval_history": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    
    await db.leave_requests.insert_one(leave_doc)
    await log_activity(current_user["user_id"], "leave_request_created", f"Leave request {leave_id} created")
    
    if employee.get("manager_id"):
        manager = await db.users.find_one({"user_id": employee["manager_id"]}, {"_id": 0})
        if manager:
            email_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>New Leave Request</h2>
                <p>Hello {manager['full_name']},</p>
                <p>{employee.get('full_name', 'An employee')} has requested leave:</p>
                <ul>
                    <li><strong>Type:</strong> {leave_req.leave_type}</li>
                    <li><strong>Period:</strong> {leave_req.start_date} to {leave_req.end_date}</li>
                    <li><strong>Days:</strong> {days_requested}</li>
                    <li><strong>Reason:</strong> {leave_req.reason}</li>
                </ul>
                <p>Please review and approve/reject this request.</p>
            </div>
            """
            await send_email_async(manager["email"], "New Leave Request Pending Approval", email_html)
    
    return {
        "message": "Leave request submitted successfully",
        "leave_id": leave_id,
        "days_requested": days_requested
    }


@router.get("/my-requests")
async def get_my_leave_requests(current_user: dict = Depends(get_current_user)):
    """Get current user's leave requests"""
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        return []
    
    requests = await db.leave_requests.find(
        {"employee_number": employee["employee_number"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return requests


@router.get("/pending-approvals")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    """Get pending leave approvals for managers/HR"""
    if current_user["role"] not in ["manager", "admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if current_user["role"] == "manager":
        team_members = await db.employees.find({"manager_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
        employee_numbers = [emp["employee_number"] for emp in team_members]
        
        requests = await db.leave_requests.find({
            "employee_number": {"$in": employee_numbers},
            "status": "pending",
            "current_approval_level": "manager"
        }, {"_id": 0}).to_list(100)
        
    elif current_user["role"] in ["admin", "hr_assistant"]:
        requests = await db.leave_requests.find({
            "status": "pending",
            "current_approval_level": "hr_admin"
        }, {"_id": 0}).to_list(100)
        
    elif current_user["role"] == "director":
        requests = await db.leave_requests.find({
            "status": "pending",
            "current_approval_level": "director"
        }, {"_id": 0}).to_list(100)
    else:
        requests = []
    
    return requests


@router.post("/{leave_id}/approve")
async def approve_leave(leave_id: str, approval: LeaveApproval, current_user: dict = Depends(get_current_user)):
    """Approve or reject a leave request"""
    leave = await db.leave_requests.find_one({"leave_id": leave_id}, {"_id": 0})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave["status"] != "pending":
        raise HTTPException(status_code=400, detail="Leave request is not pending")
    
    current_level = leave["current_approval_level"]
    if current_level == "manager" and current_user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Only managers can approve at this level")
    elif current_level == "hr_admin" and current_user["role"] not in ["admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only HR can approve at this level")
    elif current_level == "director" and current_user["role"] != "director":
        raise HTTPException(status_code=403, detail="Only directors can approve at this level")
    
    approval_entry = {
        "level": current_level,
        "approver_name": current_user["full_name"],
        "approver_id": current_user["user_id"],
        "status": approval.status,
        "comments": approval.comments,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    approval_levels = leave["approval_levels"]
    current_index = approval_levels.index(current_level)
    
    if approval.status == "rejected":
        await db.leave_requests.update_one(
            {"leave_id": leave_id},
            {
                "$set": {"status": "rejected", "rejection_reason": approval.comments},
                "$push": {"approval_history": approval_entry}
            }
        )
        
        employee = await db.employees.find_one({"employee_number": leave["employee_number"]}, {"_id": 0})
        if employee:
            email_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Leave Request Rejected</h2>
                <p>Hello {employee.get('full_name', 'Employee')},</p>
                <p>Your leave request has been rejected by {current_user['full_name']} ({current_level}).</p>
                <p><strong>Reason:</strong> {approval.comments or 'No reason provided'}</p>
            </div>
            """
            await send_email_async(employee["email"], "Leave Request Rejected", email_html)
        
        await log_activity(current_user["user_id"], "leave_rejected", f"Rejected leave {leave_id}")
        return {"message": "Leave request rejected"}
    else:
        if current_index < len(approval_levels) - 1:
            next_level = approval_levels[current_index + 1]
            await db.leave_requests.update_one(
                {"leave_id": leave_id},
                {
                    "$set": {"current_approval_level": next_level},
                    "$push": {"approval_history": approval_entry}
                }
            )
            await log_activity(current_user["user_id"], "leave_approved_partial", f"Approved leave {leave_id} at {current_level}")
            return {"message": f"Leave approved at {current_level}. Moving to {next_level} approval."}
        else:
            await db.leave_requests.update_one(
                {"leave_id": leave_id},
                {
                    "$set": {"status": "approved"},
                    "$push": {"approval_history": approval_entry}
                }
            )
            
            if leave["leave_type"] == "Annual":
                await db.employees.update_one(
                    {"employee_number": leave["employee_number"]},
                    {"$inc": {"leave_balance.annual": -leave["days_requested"]}}
                )
            
            employee = await db.employees.find_one({"employee_number": leave["employee_number"]}, {"_id": 0})
            if employee:
                email_html = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #10B981;">Leave Request Approved!</h2>
                    <p>Hello {employee.get('full_name', 'Employee')},</p>
                    <p>Great news! Your leave request has been fully approved.</p>
                </div>
                """
                await send_email_async(employee["email"], "Leave Request Approved", email_html)
            
            await log_activity(current_user["user_id"], "leave_approved_final", f"Fully approved leave {leave_id}")
            return {"message": "Leave request fully approved"}


@router.get("/balance")
async def get_leave_balance(current_user: dict = Depends(get_current_user)):
    """Get current user's leave balance"""
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    balance = employee.get("leave_balance", {"annual": 21, "sick": 30, "maternity": 0, "paternity": 0})
    
    year_start = f"{datetime.now().year}-01-01"
    approved_leaves = await db.leave_requests.find({
        "employee_number": employee["employee_number"],
        "status": "approved",
        "start_date": {"$gte": year_start}
    }, {"_id": 0}).to_list(100)
    
    used = {"annual": 0, "sick": 0, "maternity": 0, "paternity": 0}
    
    for leave in approved_leaves:
        leave_type_key = leave["leave_type"].lower()
        if leave_type_key in used:
            used[leave_type_key] += leave["days_requested"]
    
    return {
        "balance": balance,
        "used": used,
        "available": {
            "annual": balance.get("annual", 21) - used["annual"],
            "sick": balance.get("sick", 30) - used["sick"]
        }
    }


@router.get("/team-calendar")
async def get_team_leave_calendar(current_user: dict = Depends(get_current_user)):
    """Get team leave calendar"""
    if current_user["role"] not in ["manager", "admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    today = datetime.now().date()
    three_months = (today + timedelta(days=90)).isoformat()
    
    if current_user["role"] == "manager":
        team_members = await db.employees.find({"manager_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
        employee_numbers = [emp["employee_number"] for emp in team_members]
        
        leaves = await db.leave_requests.find({
            "employee_number": {"$in": employee_numbers},
            "status": "approved",
            "start_date": {"$lte": three_months}
        }, {"_id": 0}).to_list(1000)
    else:
        leaves = await db.leave_requests.find({
            "status": "approved",
            "start_date": {"$lte": three_months}
        }, {"_id": 0}).to_list(1000)
    
    return leaves


@router.get("/holidays")
async def get_kenyan_holidays():
    """Get Kenyan public holidays"""
    return {
        "holidays": KENYAN_HOLIDAYS_2025,
        "year": 2025
    }
