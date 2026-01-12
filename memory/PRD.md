# Nexus HR - Employee Management System
## Product Requirements Document

### Original Problem Statement
Build a secure, web-based Employee Management System with the following capabilities:
- HR/Admin: Manage employee profiles, upload documents, send contracts via secure signing links, track contract status, download signed contracts with audit trail
- Employee: Secure login, view personal profile, upload documents, view/sign/download contracts

### Technology Stack
- **Backend:** FastAPI (Python) with Motor (async MongoDB driver)
- **Frontend:** React with Tailwind CSS, Shadcn/UI components
- **Database:** MongoDB
- **Email:** Resend API
- **Authentication:** JWT-based

### User Roles
1. **Admin** - Full system access, manage all employees and companies
2. **HR Assistant** - Employee and document management
3. **Manager** - Team management, leave approvals, attendance verification
4. **Director** - High-level approvals, reports access
5. **Employee** - Self-service portal

---

## Implemented Features

### Phase 1: Core System (COMPLETED)
- [x] JWT Authentication (register, login, logout)
- [x] Password reset with email verification
- [x] Role-based access control
- [x] Activity logging

### Phase 2: Employee Data Restructure (COMPLETED)
- [x] Detailed employee profiles with sections:
  - Personal Info (name, DOB, gender, marital status)
  - Contact Information (email, phone, M-Pesa number)
  - Statutory Information (KRA PIN, NSSF, SHIF - Kenya specific)
  - Emergency Contact
  - Bank Information
- [x] Multi-tab employee form (EmployeeFormModal.js)
- [x] Bulk employee import functionality

### Phase 3A: Leave Management System (COMPLETED)
- [x] Leave request submission (Annual, Sick, Maternity, Paternity, Compassionate)
- [x] Multi-level approval workflow (Manager → HR → Director)
- [x] Kenyan public holidays integration
- [x] Working days calculation excluding weekends and holidays
- [x] Leave balance tracking
- [x] Email notifications for leave status changes
- [x] Team leave calendar

### Phase 3B: Attendance Module (COMPLETED)
- [x] Geolocation-based check-in/check-out
- [x] Geofencing with configurable office location
- [x] Late arrival detection (after 9:00 AM)
- [x] Manager verification for out-of-geofence check-ins
- [x] Working hours calculation
- [x] Attendance history and reporting

### Phase 3C: Multi-Company Structure (COMPLETED)
- [x] Company management (create, edit, deactivate)
- [x] Custom employee ID prefixes per company
- [x] Employee number validation against company prefix
- [x] Employee transfer between companies with history tracking
- [x] Company-scoped reports and filtering

### Phase 4: Enhancements (COMPLETED - Jan 12, 2025)
- [x] **Reports Dashboard** (`/reports`)
  - Company summary (total/active/inactive employees, recent hires)
  - Department and gender distribution
  - Leave analytics (requests by status and type)
  - Attendance analytics (late arrivals, geofence violations, avg hours)
  - Performance analytics (reviews, ratings distribution)
  - Company filter for multi-company views
  
- [x] **Performance Tracking** (`/performance`)
  - Create performance reviews with 1-5 star ratings
  - Set performance goals with priorities
  - View employee review history
  - Goal status tracking (in_progress, completed)
  - Email notifications on review completion
  
- [x] **Payroll Documents** (`/payroll-documents`)
  - Employee-specific document management
  - Document categories: Payslip, P9 Form, Bonus Statement, NSSF/SHIF Statements
  - Month/Year metadata for payroll documents
  - Upload, download, delete functionality

### Document Management (COMPLETED)
- [x] Document upload with GridFS storage
- [x] Document categorization
- [x] Expiry date tracking
- [x] Expiry reminder emails
- [x] Download functionality

### Contract Management (COMPLETED)
- [x] Contract creation and sending
- [x] Secure signing tokens
- [x] E-signature capture (canvas-based)
- [x] Contract status tracking (Sent, Viewed, Signed, Expired)
- [x] Contract statistics dashboard

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password

### Companies
- `GET /api/companies` - List all companies
- `POST /api/companies` - Create company
- `GET /api/companies/{id}` - Get company details
- `PATCH /api/companies/{id}` - Update company

### Employees
- `GET /api/employees` - List employees
- `POST /api/employees` - Create employee
- `GET /api/employees/{number}` - Get employee details
- `PATCH /api/employees/{number}` - Update employee
- `DELETE /api/employees/{number}` - Deactivate employee
- `POST /api/employees/{number}/transfer` - Transfer employee
- `POST /api/employees/bulk-import` - Bulk import

### Reports
- `GET /api/reports/company-summary` - Workforce analytics
- `GET /api/reports/leave-summary` - Leave statistics
- `GET /api/reports/attendance-summary` - Attendance statistics
- `GET /api/reports/performance-summary` - Performance statistics

### Performance
- `POST /api/performance/reviews` - Create review
- `GET /api/performance/reviews/{employee}` - Get reviews
- `POST /api/performance/goals` - Create goal
- `GET /api/performance/goals/{employee}` - Get goals

### Leave
- `POST /api/leave/request` - Submit leave request
- `GET /api/leave/my-requests` - Get my requests
- `GET /api/leave/pending-approvals` - Get pending approvals
- `POST /api/leave/{id}/approve` - Approve/reject leave
- `GET /api/leave/balance` - Get leave balance
- `GET /api/leave/team-calendar` - Team leave calendar

### Attendance
- `POST /api/attendance/check-in` - Check in
- `POST /api/attendance/check-out` - Check out
- `GET /api/attendance/my-attendance` - My attendance
- `GET /api/attendance/team-attendance` - Team attendance
- `POST /api/attendance/{id}/verify` - Verify attendance

---

## File Structure
```
/app/
├── backend/
│   ├── server.py          # Main FastAPI application (monolithic)
│   ├── models/            # Pydantic models (created for future refactor)
│   ├── routes/            # Route modules (template for future refactor)
│   └── utils/             # Utility functions (template for future refactor)
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── ReportsDashboard.js    # NEW - Phase 4
│       │   ├── PerformanceTracking.js # NEW - Phase 4
│       │   ├── PayrollDocuments.js    # NEW - Phase 4
│       │   └── [other pages...]
│       └── components/
│           ├── AdminLayout.js         # Updated with new nav links
│           └── [other components...]
└── test_reports/
    └── iteration_1.json   # Test results (23/23 passed)
```

---

## Upcoming Tasks (P1)
1. **Full Payroll Integration** - Move beyond document uploads to integrated payroll processing
2. **Onboarding Workflow** - Automated document request emails and progress tracking
3. **Backend Refactoring** - Split monolithic server.py into modular routes

## Future/Backlog (P2)
- Advanced reporting with charts/graphs
- Employee self-service enhancements
- Mobile-responsive optimizations
- Audit trail export
- Bulk contract sending

---

## Testing Status
- **Backend Tests:** 23/23 PASSED (100%)
- **Frontend Tests:** All pages load, navigation works, modals functional
- **Test File:** `/app/tests/test_backend_api.py`
- **Test Report:** `/app/test_reports/iteration_1.json`

## Known Issues
- ESLint warnings for missing useEffect dependencies (non-blocking)
- Email sending via Resend limited to verified domains in test mode

---

*Last Updated: January 12, 2025*
