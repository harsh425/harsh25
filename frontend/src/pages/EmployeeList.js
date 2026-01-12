import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import BulkImportModal from '@/components/BulkImportModal';
import { Plus, Search, Eye, CheckCircle, XCircle, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EmployeeList = () => {
  const [employees, setEmployees] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBulkImportModal, setShowBulkImportModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    employee_id: '',
    full_name: '',
    email: '',
    department: '',
    position: '',
    employment_type: 'Full-time',
    contract_start_date: '',
    contract_end_date: '',
    phone: '',
    emergency_contact: ''
  });

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    const filtered = employees.filter(emp =>
      emp.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.employee_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.department.toLowerCase().includes(searchTerm.toLowerCase())
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/employees`, formData);
      toast.success('Employee created successfully');
      setShowAddModal(false);
      fetchEmployees();
      setFormData({
        employee_id: '',
        full_name: '',
        email: '',
        department: '',
        position: '',
        employment_type: 'Full-time',
        contract_start_date: '',
        contract_end_date: '',
        phone: '',
        emergency_contact: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create employee');
    }
  };

  const handleDeactivate = async (employeeId) => {
    if (window.confirm('Are you sure you want to deactivate this employee?')) {
      try {
        await axios.delete(`${API}/employees/${employeeId}`);
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
                  <th className="px-6 py-4 text-left label">Employee ID</th>
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
                    <tr key={employee.employee_id} className="hover:bg-slate-50 transition" data-testid={`employee-row-${employee.employee_id}`}>
                      <td className="px-6 py-4 mono">{employee.employee_id}</td>
                      <td className="px-6 py-4 font-medium">{employee.full_name}</td>
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
                            to={`/employees/${employee.employee_id}`}
                            data-testid={`view-employee-${employee.employee_id}`}
                            className="text-blue-900 hover:underline flex items-center gap-1"
                          >
                            <Eye className="w-4 h-4" /> View
                          </Link>
                          {employee.status === 'active' && (
                            <button
                              onClick={() => handleDeactivate(employee.employee_id)}
                              data-testid={`deactivate-employee-${employee.employee_id}`}
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
        <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Add New Employee</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="add-employee-form">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Employee ID</label>
                  <input
                    type="text"
                    data-testid="form-employee-id"
                    className="input-field"
                    value={formData.employee_id}
                    onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label">Full Name</label>
                  <input
                    type="text"
                    data-testid="form-full-name"
                    className="input-field"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Email</label>
                  <input
                    type="email"
                    data-testid="form-email"
                    className="input-field"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label">Phone</label>
                  <input
                    type="tel"
                    data-testid="form-phone"
                    className="input-field"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Department</label>
                  <input
                    type="text"
                    data-testid="form-department"
                    className="input-field"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label">Position</label>
                  <input
                    type="text"
                    data-testid="form-position"
                    className="input-field"
                    value={formData.position}
                    onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Employment Type</label>
                  <select
                    data-testid="form-employment-type"
                    className="input-field"
                    value={formData.employment_type}
                    onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                    required
                  >
                    <option value="Full-time">Full-time</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Contract">Contract</option>
                  </select>
                </div>
                <div>
                  <label className="label">Contract Start Date</label>
                  <input
                    type="date"
                    data-testid="form-start-date"
                    className="input-field"
                    value={formData.contract_start_date}
                    onChange={(e) => setFormData({ ...formData, contract_start_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Emergency Contact</label>
                <input
                  type="text"
                  data-testid="form-emergency-contact"
                  className="input-field"
                  value={formData.emergency_contact}
                  onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                  required
                  placeholder="Name and phone number"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="btn-primary flex-1" data-testid="submit-employee-button">
                  Create Employee
                </Button>
                <Button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary flex-1"
                  data-testid="cancel-employee-button"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

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
