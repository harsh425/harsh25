import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { Plus, Building2, Edit, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyManagement = () => {
  const [companies, setCompanies] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    company_name: '',
    prefix: '',
    contact_email: '',
    phone_number: '',
    address: '',
    registration_number: ''
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API}/companies`);
      setCompanies(response.data);
    } catch (error) {
      toast.error('Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/companies`, formData);
      toast.success('Company created successfully');
      setShowAddModal(false);
      setFormData({
        company_name: '',
        prefix: '',
        contact_email: '',
        phone_number: '',
        address: '',
        registration_number: ''
      });
      fetchCompanies();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create company');
    }
  };

  const getEmployeeCount = async (companyId) => {
    try {
      const response = await axios.get(`${API}/employees`);
      return response.data.filter(emp => emp.company_id === companyId).length;
    } catch {
      return 0;
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="text-center py-12">Loading...</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div data-testid="company-management-page">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Company Management</h1>
            <p className="text-slate-600">Manage your company entities and prefixes</p>
          </div>
          <Button
            onClick={() => setShowAddModal(true)}
            data-testid="add-company-button"
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Company
          </Button>
        </div>

        {/* Companies Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {companies.length === 0 ? (
            <div className="col-span-3 card p-12 text-center text-slate-500">
              <Building2 className="w-16 h-16 mx-auto mb-4 text-slate-400" />
              <p>No companies added yet</p>
              <Button
                onClick={() => setShowAddModal(true)}
                className="btn-primary mt-4"
              >
                Add Your First Company
              </Button>
            </div>
          ) : (
            companies.map((company) => (
              <div key={company.company_id} className="card p-6" data-testid={`company-${company.company_id}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-sm flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-blue-900" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg text-slate-900">{company.company_name}</h3>
                      <span className="badge badge-info mono">Prefix: {company.prefix}</span>
                    </div>
                  </div>
                  {company.status === 'active' ? (
                    <span className="badge badge-success">
                      <CheckCircle className="w-3 h-3" /> Active
                    </span>
                  ) : (
                    <span className="badge badge-danger">
                      <XCircle className="w-3 h-3" /> Inactive
                    </span>
                  )}
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <p className="label text-xs">Contact Email</p>
                    <p className="text-slate-700">{company.contact_email}</p>
                  </div>
                  <div>
                    <p className="label text-xs">Phone Number</p>
                    <p className="text-slate-700">{company.phone_number}</p>
                  </div>
                  {company.registration_number && (
                    <div>
                      <p className="label text-xs">Registration Number</p>
                      <p className="mono text-slate-700">{company.registration_number}</p>
                    </div>
                  )}
                  {company.address && (
                    <div>
                      <p className="label text-xs">Address</p>
                      <p className="text-slate-700 text-xs">{company.address}</p>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t border-slate-200 flex justify-between items-center">
                  <span className="text-sm text-slate-600">
                    <strong>Employee ID Format:</strong> {company.prefix}XXX
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Add Company Modal */}
        <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Add New Company</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="add-company-form">
              <div>
                <label className="label">Company Name *</label>
                <input
                  type="text"
                  data-testid="company-name-input"
                  className="input-field"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  required
                  placeholder="e.g., INTI BY JIT LTD"
                />
              </div>

              <div>
                <label className="label">Employee ID Prefix *</label>
                <input
                  type="text"
                  data-testid="prefix-input"
                  className="input-field mono"
                  value={formData.prefix}
                  onChange={(e) => setFormData({ ...formData, prefix: e.target.value.toUpperCase() })}
                  required
                  maxLength={10}
                  placeholder="e.g., INT"
                />
                <p className="text-sm text-slate-500 mt-1">
                  Employee IDs will be: <strong>{formData.prefix || 'XXX'}001, {formData.prefix || 'XXX'}002, etc.</strong>
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Contact Email *</label>
                  <input
                    type="email"
                    data-testid="contact-email-input"
                    className="input-field"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label">Phone Number *</label>
                  <input
                    type="tel"
                    data-testid="phone-number-input"
                    className="input-field"
                    value={formData.phone_number}
                    onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Registration Number (Optional)</label>
                <input
                  type="text"
                  data-testid="registration-number-input"
                  className="input-field"
                  value={formData.registration_number}
                  onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
                />
              </div>

              <div>
                <label className="label">Address (Optional)</label>
                <textarea
                  data-testid="address-textarea"
                  className="input-field"
                  rows="2"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="btn-primary flex-1" data-testid="submit-company-button">
                  Create Company
                </Button>
                <Button
                  type="button"
                  onClick={() => setShowAddModal(false)}
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

export default CompanyManagement;
