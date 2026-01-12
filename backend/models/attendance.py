from pydantic import BaseModel
from typing import Optional


class AttendanceCheckIn(BaseModel):
    latitude: float
    longitude: float


class AttendanceCheckOut(BaseModel):
    latitude: float
    longitude: float


class AttendanceVerification(BaseModel):
    status: str  # "verified", "flagged"
    comments: Optional[str] = None
