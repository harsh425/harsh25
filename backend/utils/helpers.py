from datetime import datetime, timezone, timedelta
import uuid
import math

from .database import db
from .constants import KENYAN_HOLIDAYS_2025, OFFICE_LOCATION


async def log_activity(user_id: str, action: str, details: str):
    activity = {
        "activity_id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.activity_logs.insert_one(activity)


def calculate_working_days(start_date_str: str, end_date_str: str) -> int:
    """Calculate working days excluding weekends and Kenyan public holidays"""
    start = datetime.fromisoformat(start_date_str).date()
    end = datetime.fromisoformat(end_date_str).date()
    
    working_days = 0
    current = start
    
    while current <= end:
        # Skip weekends (Saturday=5, Sunday=6)
        if current.weekday() < 5:
            # Skip public holidays
            if current.isoformat() not in KENYAN_HOLIDAYS_2025:
                working_days += 1
        current += timedelta(days=1)
    
    return working_days


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in meters using Haversine formula"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def is_within_geofence(lat, lon):
    """Check if coordinates are within office geofence"""
    distance = calculate_distance(
        lat, lon,
        OFFICE_LOCATION["latitude"],
        OFFICE_LOCATION["longitude"]
    )
    return distance <= OFFICE_LOCATION["radius_meters"], distance
