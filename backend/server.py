"""
Nexus HR - Employee Management System
Main Application Entry Point (Refactored Modular Structure)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import database client for shutdown
from utils.database import client

# Import all route modules
from routes.auth import router as auth_router
from routes.companies import router as companies_router
from routes.employees import router as employees_router
from routes.leave import router as leave_router
from routes.attendance import router as attendance_router
from routes.performance import router as performance_router
from routes.reports import router as reports_router
from routes.contracts import router as contracts_router
from routes.documents import router as documents_router
from routes.dashboard import router as dashboard_router
from routes.payroll import router as payroll_router

# Create FastAPI app
app = FastAPI(
    title="Nexus HR - Employee Management System",
    description="A comprehensive HR management system for Kenyan businesses",
    version="2.0.0"
)

# Include all routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(companies_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(leave_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(performance_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(contracts_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(payroll_router, prefix="/api")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown"""
    client.close()
