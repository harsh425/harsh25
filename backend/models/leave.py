from pydantic import BaseModel
from typing import Optional


class LeaveRequest(BaseModel):
    leave_type: str  # Annual, Sick, Maternity, Paternity, Compassionate
    start_date: str
    end_date: str
    reason: str


class LeaveApproval(BaseModel):
    status: str  # "approved", "rejected"
    comments: Optional[str] = None
