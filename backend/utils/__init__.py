"""
Utils package for Nexus HR
"""
from .database import db, fs, client
from .security import (
    pwd_context, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS, security,
    hash_password, verify_password, create_access_token, get_current_user
)
from .email import send_email_async, SENDER_EMAIL
from .helpers import log_activity, calculate_working_days, calculate_distance, is_within_geofence
from .constants import KENYAN_HOLIDAYS, KENYAN_HOLIDAYS_2025, KENYAN_HOLIDAYS_2026, OFFICE_LOCATION

__all__ = [
    'db', 'fs', 'client',
    'pwd_context', 'SECRET_KEY', 'ALGORITHM', 'ACCESS_TOKEN_EXPIRE_DAYS', 'security',
    'hash_password', 'verify_password', 'create_access_token', 'get_current_user',
    'send_email_async', 'SENDER_EMAIL',
    'log_activity', 'calculate_working_days', 'calculate_distance', 'is_within_geofence',
    'KENYAN_HOLIDAYS', 'KENYAN_HOLIDAYS_2025', 'KENYAN_HOLIDAYS_2026', 'OFFICE_LOCATION'
]
