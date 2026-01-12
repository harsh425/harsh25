"""
Reports and analytics routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone, timedelta

from utils.database import db
from utils.security import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/company-summary")
async def get_company_summary(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get company workforce summary"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = {}
    if company_id:
        query["company_id"] = company_id
    
    total_employees = await db.employees.count_documents(query)
    active_employees = await db.employees.count_documents({**query, "status": "active"})
    
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$department", "count": {"$sum": 1}}}
    ]
    dept_breakdown = await db.employees.aggregate(pipeline).to_list(100)
    
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$gender", "count": {"$sum": 1}}}
    ]
    gender_breakdown = await db.employees.aggregate(pipeline).to_list(100)
    
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent_hires = await db.employees.count_documents({
        **query,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": total_employees - active_employees,
        "recent_hires": recent_hires,
        "department_breakdown": dept_breakdown,
        "gender_breakdown": gender_breakdown
    }


@router.get("/leave-summary")
async def get_leave_summary(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get leave analytics summary"""
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    emp_query = {}
    if company_id:
        emp_query["company_id"] = company_id
    
    employees = await db.employees.find(emp_query, {"employee_number": 1, "_id": 0}).to_list(10000)
    employee_numbers = [emp["employee_number"] for emp in employees]
    
    leave_query = {"employee_number": {"$in": employee_numbers}} if employee_numbers else {}
    
    total_requests = await db.leave_requests.count_documents(leave_query)
    pending = await db.leave_requests.count_documents({**leave_query, "status": "pending"})
    approved = await db.leave_requests.count_documents({**leave_query, "status": "approved"})
    rejected = await db.leave_requests.count_documents({**leave_query, "status": "rejected"})
    
    pipeline = [
        {"$match": leave_query},
        {"$group": {"_id": "$leave_type", "count": {"$sum": 1}, "total_days": {"$sum": "$days_requested"}}}
    ]
    leave_type_breakdown = await db.leave_requests.aggregate(pipeline).to_list(100)
    
    return {
        "total_requests": total_requests,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "leave_type_breakdown": leave_type_breakdown
    }


@router.get("/attendance-summary")
async def get_attendance_summary(
    company_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get attendance analytics summary"""
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    emp_query = {}
    if company_id:
        emp_query["company_id"] = company_id
    
    employees = await db.employees.find(emp_query, {"employee_number": 1, "_id": 0}).to_list(10000)
    employee_numbers = [emp["employee_number"] for emp in employees]
    
    att_query = {"employee_number": {"$in": employee_numbers}} if employee_numbers else {}
    if start_date:
        att_query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in att_query:
            att_query["date"]["$lte"] = end_date
        else:
            att_query["date"] = {"$lte": end_date}
    
    total_records = await db.attendance.count_documents(att_query)
    late_arrivals = await db.attendance.count_documents({**att_query, "is_late": True})
    outside_geofence = await db.attendance.count_documents({**att_query, "within_geofence": False})
    
    pipeline = [
        {"$match": {**att_query, "total_hours": {"$ne": None}}},
        {"$group": {"_id": None, "avg_hours": {"$avg": "$total_hours"}}}
    ]
    avg_result = await db.attendance.aggregate(pipeline).to_list(1)
    avg_hours = round(avg_result[0]["avg_hours"], 2) if avg_result else 0
    
    return {
        "total_records": total_records,
        "late_arrivals": late_arrivals,
        "late_percentage": round((late_arrivals / total_records * 100), 2) if total_records > 0 else 0,
        "outside_geofence": outside_geofence,
        "average_hours": avg_hours
    }


@router.get("/performance-summary")
async def get_performance_summary(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get performance analytics summary"""
    if current_user["role"] not in ["admin", "hr_assistant", "director"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = {}
    if company_id:
        query["company_id"] = company_id
    
    total_reviews = await db.performance_reviews.count_documents(query)
    
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$overall_rating"}}}
    ]
    avg_result = await db.performance_reviews.aggregate(pipeline).to_list(1)
    avg_rating = round(avg_result[0]["avg_rating"], 2) if avg_result else 0
    
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$overall_rating", "count": {"$sum": 1}}}
    ]
    rating_distribution = await db.performance_reviews.aggregate(pipeline).to_list(100)
    
    return {
        "total_reviews": total_reviews,
        "average_rating": avg_rating,
        "rating_distribution": rating_distribution
    }
