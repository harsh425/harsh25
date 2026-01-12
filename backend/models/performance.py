from pydantic import BaseModel


class PerformanceReview(BaseModel):
    employee_number: str
    review_period_start: str
    review_period_end: str
    overall_rating: int  # 1-5
    goals_achieved: str
    strengths: str
    areas_for_improvement: str
    comments: str


class PerformanceGoal(BaseModel):
    employee_number: str
    goal_title: str
    goal_description: str
    target_date: str
    priority: str  # High, Medium, Low
