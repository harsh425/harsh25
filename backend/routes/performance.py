"""
Performance tracking routes for Nexus HR
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from utils.database import db
from utils.security import get_current_user
from utils.email import send_email_async
from utils.helpers import log_activity

router = APIRouter(prefix="/performance", tags=["Performance"])


# Models
class PerformanceReview(BaseModel):
    employee_number: str
    review_period_start: str
    review_period_end: str
    overall_rating: int
    goals_achieved: str
    strengths: str
    areas_for_improvement: str
    comments: str


class PerformanceGoal(BaseModel):
    employee_number: str
    goal_title: str
    goal_description: str
    target_date: str
    priority: str


# Routes
@router.post("/reviews")
async def create_performance_review(review: PerformanceReview, current_user: dict = Depends(get_current_user)):
    """Create a performance review for an employee"""
    if current_user["role"] not in ["admin", "hr_assistant", "manager"]:
        raise HTTPException(status_code=403, detail="Only managers and HR can create reviews")
    
    employee = await db.employees.find_one({"employee_number": review.employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if current_user["role"] == "manager" and employee.get("manager_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only review your direct reports")
    
    review_id = str(uuid.uuid4())
    review_doc = {
        "review_id": review_id,
        "employee_number": review.employee_number,
        "employee_name": employee.get("full_name", f"{employee.get('first_name', '')} {employee.get('last_name', '')}"),
        "company_id": employee.get("company_id"),
        "company_name": employee.get("company_name"),
        "review_period_start": review.review_period_start,
        "review_period_end": review.review_period_end,
        "overall_rating": review.overall_rating,
        "goals_achieved": review.goals_achieved,
        "strengths": review.strengths,
        "areas_for_improvement": review.areas_for_improvement,
        "comments": review.comments,
        "reviewer_name": current_user["full_name"],
        "reviewer_id": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.performance_reviews.insert_one(review_doc)
    await log_activity(current_user["user_id"], "performance_review_created", f"Created review for {review.employee_number}")
    
    if employee.get("email"):
        email_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Performance Review Completed</h2>
            <p>Dear {employee.get('first_name')},</p>
            <p>Your performance review for the period {review.review_period_start} to {review.review_period_end} has been completed.</p>
            <p><strong>Overall Rating:</strong> {review.overall_rating}/5</p>
            <p>Please log in to view the complete review details.</p>
        </div>
        """
        await send_email_async(employee["email"], "Performance Review Completed", email_html)
    
    return {"message": "Performance review created successfully", "review_id": review_id}


@router.get("/reviews/{employee_number}")
async def get_employee_reviews(employee_number: str, current_user: dict = Depends(get_current_user)):
    """Get performance reviews for an employee"""
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        if employee.get("email") != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    reviews = await db.performance_reviews.find(
        {"employee_number": employee_number},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return reviews


@router.post("/goals")
async def create_performance_goal(goal: PerformanceGoal, current_user: dict = Depends(get_current_user)):
    """Create a performance goal for an employee"""
    if current_user["role"] not in ["admin", "hr_assistant", "manager"]:
        raise HTTPException(status_code=403, detail="Only managers and HR can set goals")
    
    employee = await db.employees.find_one({"employee_number": goal.employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    goal_id = str(uuid.uuid4())
    goal_doc = {
        "goal_id": goal_id,
        "employee_number": goal.employee_number,
        "employee_name": employee.get("full_name"),
        "goal_title": goal.goal_title,
        "goal_description": goal.goal_description,
        "target_date": goal.target_date,
        "priority": goal.priority,
        "status": "in_progress",
        "set_by": current_user["full_name"],
        "set_by_id": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.performance_goals.insert_one(goal_doc)
    await log_activity(current_user["user_id"], "goal_created", f"Set goal for {goal.employee_number}")
    
    return {"message": "Goal created successfully", "goal_id": goal_id}


@router.get("/goals/{employee_number}")
async def get_employee_goals(employee_number: str, current_user: dict = Depends(get_current_user)):
    """Get performance goals for an employee"""
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if current_user["role"] not in ["admin", "hr_assistant", "director", "manager"]:
        if employee.get("email") != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    goals = await db.performance_goals.find(
        {"employee_number": employee_number},
        {"_id": 0}
    ).to_list(100)
    
    return goals
