import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import BulkImportModal from '@/components/BulkImportModal';
import EmployeeFormModal from '@/components/EmployeeFormModal';
import { Plus, Search, Eye, CheckCircle, XCircle, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EmployeeList = () => {
  const [employees, setEmployees] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBulkImportModal, setShowBulkImportModal] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    const filtered = employees.filter(emp =>
      (emp.full_name && emp.full_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (emp.first_name && emp.first_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (emp.last_name && emp.last_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (emp.employee_number && emp.employee_number.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (emp.department && emp.department.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    setFilteredEmployees(filtered);
  }, [searchTerm, employees]);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data);
      setFilteredEmployees(response.data);
    } catch (error) {
      toast.error('Failed to load employees');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      await axios.post(`${API}/employees`, formData);
      toast.success('Employee created successfully');
      setShowAddModal(false);
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create employee');
    }
  };

  const handleDeactivate = async (employeeNumber) => {
    if (window.confirm('Are you sure you want to deactivate this employee?')) {
      try {
        await axios.delete(`${API}/employees/${employeeNumber}`);
        toast.success('Employee deactivated');
        fetchEmployees();
      } catch (error) {
        toast.error('Failed to deactivate employee');
      }
    }
  };

  return (
    <AdminLayout>
      <div data-testid="employee-list-page">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Employees</h1>
            <p className="text-slate-600">Manage your workforce</p>
          </div>
          <div className="flex gap-3">
            <Button
              data-testid="bulk-import-button"
              onClick={() => setShowBulkImportModal(true)}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-sm flex items-center gap-2 transition"
            >
              <Upload className="w-5 h-5" />
              Bulk Import
            </Button>
            <Button
              data-testid="add-employee-button"
              onClick={() => setShowAddModal(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Add Employee
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              data-testid="search-employees-input"
              className="input-field pl-10"
              placeholder="Search by name, ID, or department..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Employee Table */}
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full grid-border" data-testid="employees-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Employee Number</th>
                  <th className="px-6 py-4 text-left label">Name</th>
                  <th className="px-6 py-4 text-left label">Department</th>
                  <th className="px-6 py-4 text-left label">Position</th>
                  <th className="px-6 py-4 text-left label">Status</th>
                  <th className="px-6 py-4 text-left label">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-slate-500">Loading...</td>
                  </tr>
                ) : filteredEmployees.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-slate-500">No employees found</td>
                  </tr>
                ) : (
                  filteredEmployees.map((employee) => (
                    <tr key={employee.employee_number} className="hover:bg-slate-50 transition" data-testid={`employee-row-${employee.employee_number}`}>
                      <td className="px-6 py-4 mono">{employee.employee_number}</td>
                      <td className="px-6 py-4 font-medium">{employee.full_name || `${employee.first_name} ${employee.last_name}`}</td>
                      <td className="px-6 py-4">{employee.department}</td>
                      <td className="px-6 py-4">{employee.position}</td>
                      <td className="px-6 py-4">
                        {employee.status === 'active' ? (
                          <span className="badge badge-success flex items-center gap-1 w-fit">
                            <CheckCircle className="w-3 h-3" /> Active
                          </span>
                        ) : (
                          <span className="badge badge-danger flex items-center gap-1 w-fit">
                            <XCircle className="w-3 h-3" /> Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          <Link
                            to={`/employees/${employee.employee_number}`}
                            data-testid={`view-employee-${employee.employee_number}`}
                            className="text-blue-900 hover:underline flex items-center gap-1"
                          >
                            <Eye className="w-4 h-4" /> View
                          </Link>
                          {employee.status === 'active' && (
                            <button
                              onClick={() => handleDeactivate(employee.employee_number)}
                              data-testid={`deactivate-employee-${employee.employee_number}`}
                              className="text-red-600 hover:underline"
                            >
                              Deactivate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Add Employee Modal */}
        <EmployeeFormModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onSuccess={handleSubmit}
        />

        {/* Bulk Import Modal */}
        <BulkImportModal
          isOpen={showBulkImportModal}
          onClose={() => setShowBulkImportModal(false)}
          onSuccess={fetchEmployees}
        />
      </div>
    </AdminLayout>
  );
};

export default EmployeeList;
