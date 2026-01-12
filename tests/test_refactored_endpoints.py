"""
Additional Backend API Tests for Nexus HR - Post-Refactoring Regression Tests
Tests: Dashboard Stats, Attendance Check-in/out, Leave Holidays, Contracts, Documents
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stoic-feynman-1.preview.emergentagent.com').rstrip('/')

# Test data
TEST_USER_EMAIL = f"test_refactor_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "Test Refactor User"


class TestSetup:
    """Setup test user and company for subsequent tests"""
    
    token = None
    user_id = None
    company_id = None
    company_prefix = f"REF{uuid.uuid4().hex[:3].upper()}"
    employee_number = None
    employee_email = f"emp_refactor_{uuid.uuid4().hex[:6]}@testcompany.com"
    
    def test_01_register_admin_user(self):
        """Register a new admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": TEST_USER_NAME,
            "role": "admin"
        })
        
        print(f"Register response status: {response.status_code}")
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        TestSetup.token = data["access_token"]
        TestSetup.user_id = data["user"]["user_id"]
        print(f"Registered user: {TEST_USER_EMAIL}")
    
    def test_02_create_company(self):
        """Create a test company"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.post(f"{BASE_URL}/api/companies", headers=headers, json={
            "company_name": "Refactor Test Company",
            "prefix": TestSetup.company_prefix,
            "contact_email": "refactor@testcompany.com",
            "phone_number": "+254700000001",
            "address": "456 Refactor Street, Nairobi",
            "registration_number": "REF123456"
        })
        
        print(f"Create company response status: {response.status_code}")
        assert response.status_code == 200, f"Create company failed: {response.text}"
        
        data = response.json()
        TestSetup.company_id = data["company_id"]
        print(f"Created company with ID: {TestSetup.company_id}")
    
    def test_03_create_employee_with_user_email(self):
        """Create an employee linked to the test user email for attendance tests"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        emp_number = f"{TestSetup.company_prefix}001"
        
        response = requests.post(f"{BASE_URL}/api/employees", headers=headers, json={
            "company_id": TestSetup.company_id,
            "employee_number": emp_number,
            "first_name": "Refactor",
            "last_name": "Tester",
            "date_of_birth": "1990-05-20",
            "gender": "male",
            "marital_status": "single",
            "email": TEST_USER_EMAIL,  # Link to test user
            "phone_number": "+254711111112",
            "mpesa_number": "+254711111112",
            "kra_pin": "B123456789C",
            "nssf_number": "NSSF654321",
            "shif_number": "SHIF654321",
            "emergency_contact_name": "Emergency Contact",
            "emergency_contact_phone": "+254722222223",
            "emergency_contact_relationship": "Friend",
            "emergency_contact_email": "emergency@example.com",
            "bank_account_name": "Refactor Tester",
            "bank_name": "Test Bank",
            "bank_branch_name": "Main Branch",
            "bank_branch_code": "002",
            "bank_account_number": "9876543210",
            "department": "QA",
            "position": "QA Engineer",
            "employment_type": "permanent",
            "contract_start_date": "2024-01-01"
        })
        
        print(f"Create employee response status: {response.status_code}")
        assert response.status_code == 200, f"Create employee failed: {response.text}"
        
        data = response.json()
        TestSetup.employee_number = data["employee_number"]
        print(f"Created employee: {TestSetup.employee_number}")


class TestDashboardEndpoints:
    """Test Dashboard endpoints after refactoring"""
    
    def test_01_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        
        print(f"Dashboard stats response status: {response.status_code}")
        print(f"Dashboard stats response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        
        data = response.json()
        assert "total_employees" in data
        assert "active_employees" in data
        assert "total_documents" in data
        assert "total_contracts" in data
        assert "pending_signatures" in data
        print(f"Dashboard stats: {data['total_employees']} employees, {data['total_contracts']} contracts")
    
    def test_02_activity_logs(self):
        """Test activity logs endpoint"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/activity-logs", headers=headers)
        
        print(f"Activity logs response status: {response.status_code}")
        
        assert response.status_code == 200, f"Activity logs failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} activity logs")


class TestAttendanceEndpoints:
    """Test Attendance check-in/out endpoints after refactoring"""
    
    attendance_id = None
    
    def test_01_get_office_location(self):
        """Test office location endpoint"""
        response = requests.get(f"{BASE_URL}/api/attendance/office-location")
        
        print(f"Office location response status: {response.status_code}")
        print(f"Office location response: {response.text}")
        
        assert response.status_code == 200, f"Office location failed: {response.text}"
        
        data = response.json()
        assert "latitude" in data
        assert "longitude" in data
        print(f"Office location: {data}")
    
    def test_02_check_in(self):
        """Test attendance check-in"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        # Use office location coordinates for check-in
        response = requests.post(f"{BASE_URL}/api/attendance/check-in", headers=headers, json={
            "latitude": -1.2921,
            "longitude": 36.8219
        })
        
        print(f"Check-in response status: {response.status_code}")
        print(f"Check-in response: {response.text[:500]}")
        
        # May fail if already checked in today
        if response.status_code == 200:
            data = response.json()
            assert "attendance_id" in data
            TestAttendanceEndpoints.attendance_id = data["attendance_id"]
            print(f"Checked in: {data['attendance_id']}")
        elif response.status_code == 400:
            print("Already checked in today (expected)")
        else:
            assert False, f"Check-in failed unexpectedly: {response.text}"
    
    def test_03_get_my_attendance(self):
        """Test get my attendance history"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/attendance/my-attendance", headers=headers)
        
        print(f"My attendance response status: {response.status_code}")
        
        assert response.status_code == 200, f"My attendance failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} attendance records")
    
    def test_04_attendance_report_summary(self):
        """Test attendance report summary"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/attendance/reports/summary", headers=headers)
        
        print(f"Attendance summary response status: {response.status_code}")
        print(f"Attendance summary response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Attendance summary failed: {response.text}"
        
        data = response.json()
        assert "total_records" in data
        assert "late_count" in data
        assert "average_hours" in data
        print(f"Attendance summary: {data['total_records']} records")


class TestLeaveEndpoints:
    """Test Leave endpoints after refactoring"""
    
    def test_01_get_kenyan_holidays(self):
        """Test Kenyan holidays endpoint"""
        response = requests.get(f"{BASE_URL}/api/leave/holidays")
        
        print(f"Holidays response status: {response.status_code}")
        print(f"Holidays response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Holidays failed: {response.text}"
        
        data = response.json()
        assert "holidays" in data
        assert "year" in data
        print(f"Found {len(data['holidays'])} holidays for {data['year']}")
    
    def test_02_get_leave_balance(self):
        """Test leave balance endpoint"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/leave/balance", headers=headers)
        
        print(f"Leave balance response status: {response.status_code}")
        print(f"Leave balance response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Leave balance failed: {response.text}"
        
        data = response.json()
        assert "balance" in data
        assert "used" in data
        assert "available" in data
        print(f"Leave balance: {data['balance']}")
    
    def test_03_get_team_calendar(self):
        """Test team leave calendar"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/leave/team-calendar", headers=headers)
        
        print(f"Team calendar response status: {response.status_code}")
        
        assert response.status_code == 200, f"Team calendar failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} approved leaves in calendar")


class TestContractsEndpoints:
    """Test Contracts endpoints after refactoring"""
    
    def test_01_get_contracts_stats(self):
        """Test contracts stats endpoint"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/contracts/stats", headers=headers)
        
        print(f"Contracts stats response status: {response.status_code}")
        print(f"Contracts stats response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Contracts stats failed: {response.text}"
        
        data = response.json()
        assert "total" in data
        print(f"Contracts stats: {data}")
    
    def test_02_list_contracts(self):
        """Test list contracts endpoint"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers)
        
        print(f"List contracts response status: {response.status_code}")
        
        assert response.status_code == 200, f"List contracts failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} contracts")


class TestDocumentsEndpoints:
    """Test Documents endpoints after refactoring"""
    
    def test_01_get_expiring_documents(self):
        """Test expiring documents endpoint"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/documents/expiring-soon?days=30", headers=headers)
        
        print(f"Expiring documents response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expiring documents failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} expiring documents")
    
    def test_02_get_document_categories(self):
        """Test document categories endpoint"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/documents/categories", headers=headers)
        
        print(f"Document categories response status: {response.status_code}")
        
        assert response.status_code == 200, f"Document categories failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} document categories")


class TestCompanyUpdate:
    """Test company update endpoint"""
    
    def test_01_update_company(self):
        """Test company update"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.patch(f"{BASE_URL}/api/companies/{TestSetup.company_id}", headers=headers, json={
            "phone_number": "+254700000002"
        })
        
        print(f"Update company response status: {response.status_code}")
        
        assert response.status_code == 200, f"Update company failed: {response.text}"
        print("Company updated successfully")


class TestEmployeeTransfer:
    """Test employee transfer endpoint"""
    
    def test_01_get_employee_transfers(self):
        """Test get employee transfers"""
        headers = {"Authorization": f"Bearer {TestSetup.token}"}
        
        response = requests.get(f"{BASE_URL}/api/employees/{TestSetup.employee_number}/transfers", headers=headers)
        
        print(f"Employee transfers response status: {response.status_code}")
        
        assert response.status_code == 200, f"Employee transfers failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} transfers for employee")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
