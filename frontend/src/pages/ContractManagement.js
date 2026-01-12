import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { Plus, Search, Send, CheckCircle, Clock, XCircle, Eye } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ContractManagement = () => {
  const [contracts, setContracts] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [filteredContracts, setFilteredContracts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    employee_id: '',
    title: '',
    description: '',
    expiry_days: 30
  });

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    const filtered = contracts.filter(contract => {
      const employee = employees.find(e => e.employee_id === contract.employee_id);
      return (
        contract.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        contract.employee_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (employee && employee.full_name.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    });
    setFilteredContracts(filtered);
  }, [searchTerm, contracts, employees]);

  const fetchData = async () => {
    try {
      const [contractsRes, employeesRes] = await Promise.all([
        axios.get(`${API}/contracts`),
        axios.get(`${API}/employees`)
      ]);
      setContracts(contractsRes.data);
      setEmployees(employeesRes.data);
      setFilteredContracts(contractsRes.data);
    } catch (error) {
      toast.error('Failed to load contracts');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/contracts`, formData);
      toast.success('Contract created and sent successfully');
      setShowCreateModal(false);
      fetchData();
      setFormData({
        employee_id: '',
        title: '',
        description: '',
        expiry_days: 30
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create contract');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      sent: { class: 'badge-info', icon: Send, text: 'Sent' },
      viewed: { class: 'badge-warning', icon: Eye, text: 'Viewed' },
      signed: { class: 'badge-success', icon: CheckCircle, text: 'Signed' },
      expired: { class: 'badge-danger', icon: XCircle, text: 'Expired' }
    };
    const badge = badges[status] || badges.sent;
    const Icon = badge.icon;
    return (
      <span className={`badge ${badge.class} flex items-center gap-1 w-fit`}>
        <Icon className="w-3 h-3" /> {badge.text}
      </span>
    );
  };

  const getEmployeeName = (employeeId) => {
    const employee = employees.find(e => e.employee_id === employeeId);
    return employee ? employee.full_name : employeeId;
  };

  return (
    <AdminLayout>
      <div data-testid="contract-management-page">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Contract Management</h1>
            <p className="text-slate-600">Create and track employment contracts</p>
          </div>
          <Button
            data-testid="create-contract-button"
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Create Contract
          </Button>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              data-testid="search-contracts-input"
              className="input-field pl-10"
              placeholder="Search by title, employee name, or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Contracts Table */}
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full grid-border" data-testid="contracts-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Contract ID</th>
                  <th className="px-6 py-4 text-left label">Title</th>
                  <th className="px-6 py-4 text-left label">Employee</th>
                  <th className="px-6 py-4 text-left label">Status</th>
                  <th className="px-6 py-4 text-left label">Created</th>
                  <th className="px-6 py-4 text-left label">Signed At</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-slate-500">Loading...</td>
                  </tr>
                ) : filteredContracts.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-slate-500">No contracts found</td>
                  </tr>
                ) : (
                  filteredContracts.map((contract) => (
                    <tr key={contract.contract_id} className="hover:bg-slate-50 transition" data-testid={`contract-row-${contract.contract_id}`}>
                      <td className="px-6 py-4 mono text-sm">{contract.contract_id.substring(0, 8)}...</td>
                      <td className="px-6 py-4 font-medium">{contract.title}</td>
                      <td className="px-6 py-4">{getEmployeeName(contract.employee_id)}</td>
                      <td className="px-6 py-4">{getStatusBadge(contract.status)}</td>
                      <td className="px-6 py-4 text-sm mono">
                        {new Date(contract.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm mono">
                        {contract.signed_at ? new Date(contract.signed_at).toLocaleDateString() : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Create Contract Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Create Employment Contract</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="create-contract-form">
              <div>
                <label className="label">Select Employee</label>
                <select
                  data-testid="form-employee-select"
                  className="input-field"
                  value={formData.employee_id}
                  onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                  required
                >
                  <option value="">Choose an employee...</option>
                  {employees.filter(e => e.status === 'active').map((emp) => (
                    <option key={emp.employee_id} value={emp.employee_id}>
                      {emp.full_name} ({emp.employee_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Contract Title</label>
                <input
                  type="text"
                  data-testid="form-contract-title"
                  className="input-field"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  placeholder="e.g., Employment Contract 2025"
                />
              </div>

              <div>
                <label className="label">Contract Description</label>
                <textarea
                  data-testid="form-contract-description"
                  className="input-field"
                  rows="4"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  placeholder="Enter contract details and terms..."
                />
              </div>

              <div>
                <label className="label">Link Expiry (Days)</label>
                <input
                  type="number"
                  data-testid="form-expiry-days"
                  className="input-field"
                  value={formData.expiry_days}
                  onChange={(e) => setFormData({ ...formData, expiry_days: parseInt(e.target.value) })}
                  required
                  min="1"
                  max="90"
                />
                <p className="text-sm text-slate-500 mt-1">Number of days before the signing link expires</p>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="btn-primary flex-1" data-testid="submit-contract-button">
                  <Send className="w-4 h-4 mr-2" /> Create & Send Contract
                </Button>
                <Button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
};

export default ContractManagement;
