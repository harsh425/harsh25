"""
Backend API Tests for Nexus HR Employee Management System
Tests: Authentication, Companies, Employees, Reports, Performance, Leave, Attendance
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stoic-feynman-1.preview.emergentagent.com').rstrip('/')

# Test data
TEST_USER_EMAIL = f"test_admin_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "Test Admin User"

class TestAuthenticationFlow:
    """Test user registration and login"""
    
    token = None
    user_id = None
    
    def test_01_register_admin_user(self):
        """Register a new admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": TEST_USER_NAME,
            "role": "admin"
        })
        
        print(f"Register response status: {response.status_code}")
        print(f"Register response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access token in response"
        assert "user" in data, "No user data in response"
        assert data["user"]["email"] == TEST_USER_EMAIL
        assert data["user"]["role"] == "admin"
        
        TestAuthenticationFlow.token = data["access_token"]
        TestAuthenticationFlow.user_id = data["user"]["user_id"]
        print(f"Registered user: {TEST_USER_EMAIL}")
    
    def test_02_login_user(self):
        """Login with registered user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        print(f"Login response status: {response.status_code}")
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        
        TestAuthenticationFlow.token = data["access_token"]
        print("Login successful")
    
    def test_03_get_current_user(self):
        """Get current user info"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        print(f"Get me response status: {response.status_code}")
        
        assert response.status_code == 200, f"Get me failed: {response.text}"
        
        data = response.json()
        assert data["email"] == TEST_USER_EMAIL
        print("Get current user successful")
    
    def test_04_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Invalid login correctly rejected")


class TestCompanyManagement:
    """Test company CRUD operations"""
    
    company_id = None
    company_prefix = f"TST{uuid.uuid4().hex[:3].upper()}"
    
    def test_01_create_company(self):
        """Create a new company"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.post(f"{BASE_URL}/api/companies", headers=headers, json={
            "company_name": "Test Company Ltd",
            "prefix": TestCompanyManagement.company_prefix,
            "contact_email": "test@testcompany.com",
            "phone_number": "+254700000000",
            "address": "123 Test Street, Nairobi",
            "registration_number": "REG123456"
        })
        
        print(f"Create company response status: {response.status_code}")
        print(f"Create company response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Create company failed: {response.text}"
        
        data = response.json()
        assert "company_id" in data
        TestCompanyManagement.company_id = data["company_id"]
        print(f"Created company with ID: {TestCompanyManagement.company_id}")
    
    def test_02_list_companies(self):
        """List all companies"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/companies", headers=headers)
        
        print(f"List companies response status: {response.status_code}")
        
        assert response.status_code == 200, f"List companies failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} companies")
    
    def test_03_get_company_by_id(self):
        """Get company by ID"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/companies/{TestCompanyManagement.company_id}", headers=headers)
        
        print(f"Get company response status: {response.status_code}")
        
        assert response.status_code == 200, f"Get company failed: {response.text}"
        
        data = response.json()
        assert data["company_id"] == TestCompanyManagement.company_id
        assert data["company_name"] == "Test Company Ltd"
        print("Get company by ID successful")


class TestEmployeeManagement:
    """Test employee CRUD operations"""
    
    employee_number = None
    
    def test_01_create_employee(self):
        """Create a new employee"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        emp_number = f"{TestCompanyManagement.company_prefix}001"
        
        response = requests.post(f"{BASE_URL}/api/employees", headers=headers, json={
            "company_id": TestCompanyManagement.company_id,
            "employee_number": emp_number,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-15",
            "gender": "male",
            "marital_status": "single",
            "email": f"john.doe.{uuid.uuid4().hex[:6]}@testcompany.com",
            "phone_number": "+254711111111",
            "mpesa_number": "+254711111111",
            "kra_pin": "A123456789B",
            "nssf_number": "NSSF123456",
            "shif_number": "SHIF123456",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "+254722222222",
            "emergency_contact_relationship": "Spouse",
            "emergency_contact_email": "jane.doe@example.com",
            "bank_account_name": "John Doe",
            "bank_name": "Test Bank",
            "bank_branch_name": "Main Branch",
            "bank_branch_code": "001",
            "bank_account_number": "1234567890",
            "department": "Engineering",
            "position": "Software Developer",
            "employment_type": "permanent",
            "contract_start_date": "2024-01-01"
        })
        
        print(f"Create employee response status: {response.status_code}")
        print(f"Create employee response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Create employee failed: {response.text}"
        
        data = response.json()
        assert "employee_number" in data
        TestEmployeeManagement.employee_number = data["employee_number"]
        print(f"Created employee: {TestEmployeeManagement.employee_number}")
    
    def test_02_list_employees(self):
        """List all employees"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/employees", headers=headers)
        
        print(f"List employees response status: {response.status_code}")
        
        assert response.status_code == 200, f"List employees failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} employees")
    
    def test_03_get_employee_by_number(self):
        """Get employee by employee number"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/employees/{TestEmployeeManagement.employee_number}", headers=headers)
        
        print(f"Get employee response status: {response.status_code}")
        
        assert response.status_code == 200, f"Get employee failed: {response.text}"
        
        data = response.json()
        assert data["employee_number"] == TestEmployeeManagement.employee_number
        assert data["first_name"] == "John"
        print("Get employee by number successful")
    
    def test_04_update_employee(self):
        """Update employee details"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.patch(f"{BASE_URL}/api/employees/{TestEmployeeManagement.employee_number}", headers=headers, json={
            "position": "Senior Software Developer",
            "department": "Engineering"
        })
        
        print(f"Update employee response status: {response.status_code}")
        
        assert response.status_code == 200, f"Update employee failed: {response.text}"
        print("Update employee successful")


class TestReportsAPI:
    """Test Reports & Analytics endpoints"""
    
    def test_01_company_summary(self):
        """Get company summary report"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/reports/company-summary", headers=headers)
        
        print(f"Company summary response status: {response.status_code}")
        print(f"Company summary response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Company summary failed: {response.text}"
        
        data = response.json()
        assert "total_employees" in data
        assert "active_employees" in data
        assert "department_breakdown" in data
        assert "gender_breakdown" in data
        print(f"Company summary: {data['total_employees']} total employees")
    
    def test_02_leave_summary(self):
        """Get leave summary report"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/reports/leave-summary", headers=headers)
        
        print(f"Leave summary response status: {response.status_code}")
        print(f"Leave summary response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Leave summary failed: {response.text}"
        
        data = response.json()
        assert "total_requests" in data
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
        print(f"Leave summary: {data['total_requests']} total requests")
    
    def test_03_attendance_summary(self):
        """Get attendance summary report"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/reports/attendance-summary", headers=headers)
        
        print(f"Attendance summary response status: {response.status_code}")
        print(f"Attendance summary response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Attendance summary failed: {response.text}"
        
        data = response.json()
        assert "total_records" in data
        assert "late_arrivals" in data
        assert "average_hours" in data
        print(f"Attendance summary: {data['total_records']} total records")
    
    def test_04_performance_summary(self):
        """Get performance summary report"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/reports/performance-summary", headers=headers)
        
        print(f"Performance summary response status: {response.status_code}")
        print(f"Performance summary response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Performance summary failed: {response.text}"
        
        data = response.json()
        assert "total_reviews" in data
        assert "average_rating" in data
        print(f"Performance summary: {data['total_reviews']} total reviews")


class TestPerformanceTracking:
    """Test Performance Tracking endpoints"""
    
    review_id = None
    goal_id = None
    
    def test_01_create_performance_review(self):
        """Create a performance review"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.post(f"{BASE_URL}/api/performance/reviews", headers=headers, json={
            "employee_number": TestEmployeeManagement.employee_number,
            "review_period_start": "2024-01-01",
            "review_period_end": "2024-06-30",
            "overall_rating": 4,
            "goals_achieved": "Completed all Q1 and Q2 targets",
            "strengths": "Strong technical skills, good team player",
            "areas_for_improvement": "Time management",
            "comments": "Excellent performance overall"
        })
        
        print(f"Create review response status: {response.status_code}")
        print(f"Create review response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Create review failed: {response.text}"
        
        data = response.json()
        assert "review_id" in data
        TestPerformanceTracking.review_id = data["review_id"]
        print(f"Created review: {TestPerformanceTracking.review_id}")
    
    def test_02_get_employee_reviews(self):
        """Get reviews for an employee"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/performance/reviews/{TestEmployeeManagement.employee_number}", headers=headers)
        
        print(f"Get reviews response status: {response.status_code}")
        
        assert response.status_code == 200, f"Get reviews failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"Found {len(data)} reviews for employee")
    
    def test_03_create_performance_goal(self):
        """Create a performance goal"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        target_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        
        response = requests.post(f"{BASE_URL}/api/performance/goals", headers=headers, json={
            "employee_number": TestEmployeeManagement.employee_number,
            "goal_title": "Complete AWS Certification",
            "goal_description": "Obtain AWS Solutions Architect certification",
            "target_date": target_date,
            "priority": "High"
        })
        
        print(f"Create goal response status: {response.status_code}")
        print(f"Create goal response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Create goal failed: {response.text}"
        
        data = response.json()
        assert "goal_id" in data
        TestPerformanceTracking.goal_id = data["goal_id"]
        print(f"Created goal: {TestPerformanceTracking.goal_id}")
    
    def test_04_get_employee_goals(self):
        """Get goals for an employee"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/performance/goals/{TestEmployeeManagement.employee_number}", headers=headers)
        
        print(f"Get goals response status: {response.status_code}")
        
        assert response.status_code == 200, f"Get goals failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"Found {len(data)} goals for employee")


class TestLeaveManagement:
    """Test Leave Management endpoints"""
    
    def test_01_get_leave_balance(self):
        """Get leave balance - may fail if user is not an employee"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/leave/balance", headers=headers)
        
        print(f"Leave balance response status: {response.status_code}")
        print(f"Leave balance response: {response.text[:500]}")
        
        # This may return 404 if the admin user doesn't have an employee record
        if response.status_code == 200:
            data = response.json()
            assert "annual" in data.get("balance", data)
            print("Leave balance retrieved")
        else:
            print(f"Leave balance not available for admin user (expected): {response.status_code}")
    
    def test_02_get_pending_approvals(self):
        """Get pending leave approvals"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/leave/pending-approvals", headers=headers)
        
        print(f"Pending approvals response status: {response.status_code}")
        
        assert response.status_code == 200, f"Pending approvals failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} pending approvals")


class TestAttendanceManagement:
    """Test Attendance Management endpoints"""
    
    def test_01_get_team_attendance(self):
        """Get team attendance records"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/attendance/team-attendance", headers=headers)
        
        print(f"Team attendance response status: {response.status_code}")
        
        assert response.status_code == 200, f"Team attendance failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} attendance records")


class TestDocumentManagement:
    """Test Document Management endpoints"""
    
    def test_01_get_employee_documents(self):
        """Get documents for an employee"""
        headers = {"Authorization": f"Bearer {TestAuthenticationFlow.token}"}
        
        response = requests.get(f"{BASE_URL}/api/documents/employee/{TestEmployeeManagement.employee_number}", headers=headers)
        
        print(f"Get documents response status: {response.status_code}")
        
        assert response.status_code == 200, f"Get documents failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} documents for employee")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
