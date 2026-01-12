# Routes package
from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/api")

# Import all route modules
from . import auth, employees, companies, leave, attendance, performance, reports, contracts, documents, dashboard
