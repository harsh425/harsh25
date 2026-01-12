"""
Attendance management routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid

from utils.database import db
from utils.security import get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity, is_within_geofence
from utils.constants import OFFICE_LOCATION

router = APIRouter(prefix="/attendance", tags=["Attendance"])


# Models
class AttendanceCheckIn(BaseModel):
    latitude: float
    longitude: float


class AttendanceCheckOut(BaseModel):
    latitude: float
    longitude: float


class AttendanceVerification(BaseModel):
    status: str
    comments: Optional[str] = None


# Routes
@router.post("/check-in")
async def check_in(attendance: AttendanceCheckIn, current_user: dict = Depends(get_current_user)):
    """Check in for the day"""
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    today = datetime.now(timezone.utc).date().isoformat()
    existing = await db.attendance.find_one({
        "employee_number": employee["employee_number"],
        "date": today,
        "check_out_time": None
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    within_fence, distance = is_within_geofence(attendance.latitude, attendance.longitude)
    
    check_in_time = datetime.now(timezone.utc)
    expected_time = check_in_time.replace(hour=9, minute=0, second=0, microsecond=0)
    is_late = check_in_time > expected_time
    
    attendance_doc = {
        "attendance_id": str(uuid.uuid4()),
        "employee_number": employee["employee_number"],
        "employee_name": employee.get("full_name", f"{employee.get('first_name', '')} {employee.get('last_name', '')}"),
        "date": today,
        "check_in_time": check_in_time.isoformat(),
        "check_in_latitude": attendance.latitude,
        "check_in_longitude": attendance.longitude,
        "check_in_distance": round(distance, 2),
        "within_geofence": within_fence,
        "is_late": is_late,
        "check_out_time": None,
        "total_hours": None,
        "status": "pending_verification" if not within_fence else "checked_in",
        "verified_by": None,
        "verification_status": None,
        "verification_comments": None
    }
    
    await db.attendance.insert_one(attendance_doc)
    await log_activity(current_user["user_id"], "attendance_check_in", f"Checked in at {check_in_time.strftime('%H:%M')}")
    
    if not within_fence and employee.get("manager_id"):
        manager = await db.users.find_one({"user_id": employee["manager_id"]}, {"_id": 0})
        if manager:
            email_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #FF4500;">Attendance Alert</h2>
                <p>Hello {manager['full_name']},</p>
                <p>{employee.get('full_name', 'An employee')} checked in outside the office geofence:</p>
                <ul>
                    <li><strong>Distance from office:</strong> {round(distance, 2)}m</li>
                    <li><strong>Time:</strong> {check_in_time.strftime('%H:%M')}</li>
                </ul>
                <p>Please verify this attendance record.</p>
            </div>
            """
            await send_email_async(manager["email"], "Attendance Verification Required", email_html)
    
    return {
        "message": "Checked in successfully" if within_fence else "Checked in (outside geofence - requires verification)",
        "attendance_id": attendance_doc["attendance_id"],
        "check_in_time": check_in_time.strftime('%H:%M'),
        "within_geofence": within_fence,
        "distance": round(distance, 2),
        "is_late": is_late
    }


@router.post("/check-out")
async def check_out(attendance: AttendanceCheckOut, current_user: dict = Depends(get_current_user)):
    """Check out for the day"""
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    today = datetime.now(timezone.utc).date().isoformat()
    attendance_record = await db.attendance.find_one({
        "employee_number": employee["employee_number"],
        "date": today,
        "check_out_time": None
    }, {"_id": 0})
    
    if not attendance_record:
        raise HTTPException(status_code=404, detail="No active check-in found for today")
    
    within_fence, distance = is_within_geofence(attendance.latitude, attendance.longitude)
    
    check_out_time = datetime.now(timezone.utc)
    check_in_time = datetime.fromisoformat(attendance_record["check_in_time"])
    
    time_diff = check_out_time - check_in_time
    total_hours = round(time_diff.total_seconds() / 3600, 2)
    
    await db.attendance.update_one(
        {"attendance_id": attendance_record["attendance_id"]},
        {"$set": {
            "check_out_time": check_out_time.isoformat(),
            "check_out_latitude": attendance.latitude,
            "check_out_longitude": attendance.longitude,
            "check_out_distance": round(distance, 2),
            "total_hours": total_hours,
            "status": "completed"
        }}
    )
    
    await log_activity(current_user["user_id"], "attendance_check_out", f"Checked out at {check_out_time.strftime('%H:%M')}")
    
    return {
        "message": "Checked out successfully",
        "check_out_time": check_out_time.strftime('%H:%M'),
        "total_hours": total_hours,
        "within_geofence": within_fence,
        "distance": round(distance, 2)
    }


@router.get("/my-attendance")
async def get_my_attendance(days: int = 30, current_user: dict = Depends(get_current_user)):
    """Get current user's attendance history"""
    employee = await db.employees.find_one({"email": current_user["email"]}, {"_id": 0})
    if not employee:
        return []
    
    start_date = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
    
    attendance_records = await db.attendance.find({
        "employee_number": employee["employee_number"],
        "date": {"$gte": start_date}
    }, {"_id": 0}).sort("date", -1).to_list(1000)
    
    return attendance_records


@router.get("/team-attendance")
async def get_team_attendance(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get team attendance for a specific date"""
    if current_user["role"] not in ["manager", "admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()
    
    if current_user["role"] == "manager":
        team_members = await db.employees.find({"manager_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
        employee_numbers = [emp["employee_number"] for emp in team_members]
        
        attendance = await db.attendance.find({
            "employee_number": {"$in": employee_numbers},
            "date": date
        }, {"_id": 0}).to_list(1000)
    else:
        attendance = await db.attendance.find({"date": date}, {"_id": 0}).to_list(1000)
    
    return attendance


@router.post("/{attendance_id}/verify")
async def verify_attendance(attendance_id: str, verification: AttendanceVerification, current_user: dict = Depends(get_current_user)):
    """Verify an attendance record"""
    if current_user["role"] not in ["manager", "admin", "hr_assistant"]:
        raise HTTPException(status_code=403, detail="Only managers and HR can verify attendance")
    
    attendance = await db.attendance.find_one({"attendance_id": attendance_id}, {"_id": 0})
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    if current_user["role"] == "manager":
        employee = await db.employees.find_one({"employee_number": attendance["employee_number"]}, {"_id": 0})
        if not employee or employee.get("manager_id") != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized to verify this employee's attendance")
    
    await db.attendance.update_one(
        {"attendance_id": attendance_id},
        {"$set": {
            "verification_status": verification.status,
            "verification_comments": verification.comments,
            "verified_by": current_user["full_name"],
            "verified_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(current_user["user_id"], "attendance_verified", f"Verified attendance {attendance_id} as {verification.status}")
    
    return {"message": f"Attendance {verification.status}"}


@router.get("/reports/summary")
async def get_attendance_report_summary(
    employee_number: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get attendance summary report"""
    if current_user["role"] not in ["manager", "admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = {}
    
    if employee_number:
        query["employee_number"] = employee_number
    elif current_user["role"] == "manager":
        team_members = await db.employees.find({"manager_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
        employee_numbers = [emp["employee_number"] for emp in team_members]
        query["employee_number"] = {"$in": employee_numbers}
    
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}
    
    records = await db.attendance.find(query, {"_id": 0}).to_list(10000)
    
    total_days = len(set(r["date"] for r in records))
    late_count = sum(1 for r in records if r.get("is_late"))
    outside_geofence = sum(1 for r in records if not r.get("within_geofence"))
    avg_hours = sum(r.get("total_hours", 0) for r in records if r.get("total_hours")) / len(records) if records else 0
    
    return {
        "total_records": len(records),
        "total_days": total_days,
        "late_count": late_count,
        "outside_geofence_count": outside_geofence,
        "average_hours": round(avg_hours, 2)
    }


@router.get("/office-location")
async def get_office_location():
    """Return office location for geofencing"""
    return OFFICE_LOCATION
