import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EmployeeFormModal = ({ isOpen, onClose, onSuccess, initialData = null }) => {
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [formData, setFormData] = useState(initialData || {
    // Company Assignment
    company_id: '',
    
    // Personal Info
    employee_number: '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    marital_status: '',
    
    // Contact Information
    email: '',
    phone_number: '',
    mpesa_number: '',
    
    // Statutory Information
    kra_pin: '',
    nssf_number: '',
    shif_number: '',
    
    // Emergency Contact
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    emergency_contact_email: '',
    
    // Bank Information
    bank_account_name: '',
    bank_name: '',
    bank_branch_name: '',
    bank_branch_code: '',
    bank_account_number: '',
    
    // Employment Details
    department: '',
    position: '',
    employment_type: 'Full-time',
    contract_start_date: '',
    contract_end_date: '',
    manager_id: ''
  });

  useEffect(() => {
    if (isOpen) {
      fetchCompanies();
    }
  }, [isOpen]);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API}/companies`);
      setCompanies(response.data.filter(c => c.status === 'active'));
    } catch (error) {
      toast.error('Failed to load companies');
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Update selected company when company_id changes
    if (field === 'company_id') {
      const company = companies.find(c => c.company_id === value);
      setSelectedCompany(company);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    onSuccess(formData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">
            {initialData ? 'Edit Employee' : 'Add New Employee'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} data-testid="employee-form">
          <Tabs defaultValue="personal" className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="personal">Personal</TabsTrigger>
              <TabsTrigger value="contact">Contact</TabsTrigger>
              <TabsTrigger value="statutory">Statutory</TabsTrigger>
              <TabsTrigger value="emergency">Emergency</TabsTrigger>
              <TabsTrigger value="bank">Bank & Employment</TabsTrigger>
            </TabsList>

            {/* Personal Info */}
            <TabsContent value="personal" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">First Name *</label>
                  <input
                    type="text"
                    data-testid="first-name-input"
                    className="input-field"
                    value={formData.first_name}
                    onChange={(e) => handleChange('first_name', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Last Name *</label>
                  <input
                    type="text"
                    data-testid="last-name-input"
                    className="input-field"
                    value={formData.last_name}
                    onChange={(e) => handleChange('last_name', e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Employee Number *</label>
                  <input
                    type="text"
                    data-testid="employee-number-input"
                    className="input-field"
                    value={formData.employee_number}
                    onChange={(e) => handleChange('employee_number', e.target.value)}
                    required
                    disabled={initialData}
                  />
                </div>
                <div>
                  <label className="label">Date of Birth *</label>
                  <input
                    type="date"
                    data-testid="dob-input"
                    className="input-field"
                    value={formData.date_of_birth}
                    onChange={(e) => handleChange('date_of_birth', e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Gender *</label>
                  <select
                    data-testid="gender-select"
                    className="input-field"
                    value={formData.gender}
                    onChange={(e) => handleChange('gender', e.target.value)}
                    required
                  >
                    <option value="">Select...</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="label">Marital Status *</label>
                  <select
                    data-testid="marital-status-select"
                    className="input-field"
                    value={formData.marital_status}
                    onChange={(e) => handleChange('marital_status', e.target.value)}
                    required
                  >
                    <option value="">Select...</option>
                    <option value="Single">Single</option>
                    <option value="Married">Married</option>
                    <option value="Divorced">Divorced</option>
                    <option value="Widowed">Widowed</option>
                  </select>
                </div>
              </div>
            </TabsContent>

            {/* Contact Info */}
            <TabsContent value="contact" className="space-y-4 mt-4">
              <div>
                <label className="label">Email *</label>
                <input
                  type="email"
                  data-testid="email-input"
                  className="input-field"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="label">Phone Number *</label>
                <input
                  type="tel"
                  data-testid="phone-input"
                  className="input-field"
                  placeholder="+254700000000"
                  value={formData.phone_number}
                  onChange={(e) => handleChange('phone_number', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="label">M-Pesa Number *</label>
                <input
                  type="tel"
                  data-testid="mpesa-input"
                  className="input-field"
                  placeholder="+254700000000"
                  value={formData.mpesa_number}
                  onChange={(e) => handleChange('mpesa_number', e.target.value)}
                  required
                />
              </div>
            </TabsContent>

            {/* Statutory Info */}
            <TabsContent value="statutory" className="space-y-4 mt-4">
              <div>
                <label className="label">KRA PIN *</label>
                <input
                  type="text"
                  data-testid="kra-pin-input"
                  className="input-field"
                  placeholder="A000000000A"
                  value={formData.kra_pin}
                  onChange={(e) => handleChange('kra_pin', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="label">NSSF Number *</label>
                <input
                  type="text"
                  data-testid="nssf-input"
                  className="input-field"
                  value={formData.nssf_number}
                  onChange={(e) => handleChange('nssf_number', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="label">SHIF Number *</label>
                <input
                  type="text"
                  data-testid="shif-input"
                  className="input-field"
                  value={formData.shif_number}
                  onChange={(e) => handleChange('shif_number', e.target.value)}
                  required
                />
                <p className="text-xs text-slate-500 mt-1">Social Health Insurance Fund (formerly NHIF)</p>
              </div>
            </TabsContent>

            {/* Emergency Contact */}
            <TabsContent value="emergency" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Name *</label>
                  <input
                    type="text"
                    data-testid="emergency-name-input"
                    className="input-field"
                    value={formData.emergency_contact_name}
                    onChange={(e) => handleChange('emergency_contact_name', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Relationship *</label>
                  <input
                    type="text"
                    data-testid="emergency-relationship-input"
                    className="input-field"
                    placeholder="e.g., Spouse, Parent, Sibling"
                    value={formData.emergency_contact_relationship}
                    onChange={(e) => handleChange('emergency_contact_relationship', e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Phone *</label>
                  <input
                    type="tel"
                    data-testid="emergency-phone-input"
                    className="input-field"
                    value={formData.emergency_contact_phone}
                    onChange={(e) => handleChange('emergency_contact_phone', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Email *</label>
                  <input
                    type="email"
                    data-testid="emergency-email-input"
                    className="input-field"
                    value={formData.emergency_contact_email}
                    onChange={(e) => handleChange('emergency_contact_email', e.target.value)}
                    required
                  />
                </div>
              </div>
            </TabsContent>

            {/* Bank & Employment */}
            <TabsContent value="bank" className="space-y-4 mt-4">
              <h4 className="font-semibold text-slate-900">Bank Information</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Account Name *</label>
                  <input
                    type="text"
                    data-testid="bank-account-name-input"
                    className="input-field"
                    value={formData.bank_account_name}
                    onChange={(e) => handleChange('bank_account_name', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Bank Name *</label>
                  <input
                    type="text"
                    data-testid="bank-name-input"
                    className="input-field"
                    value={formData.bank_name}
                    onChange={(e) => handleChange('bank_name', e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="label">Branch Name *</label>
                  <input
                    type="text"
                    data-testid="branch-name-input"
                    className="input-field"
                    value={formData.bank_branch_name}
                    onChange={(e) => handleChange('bank_branch_name', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Branch Code *</label>
                  <input
                    type="text"
                    data-testid="branch-code-input"
                    className="input-field"
                    value={formData.bank_branch_code}
                    onChange={(e) => handleChange('bank_branch_code', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Account Number *</label>
                  <input
                    type="text"
                    data-testid="account-number-input"
                    className="input-field"
                    value={formData.bank_account_number}
                    onChange={(e) => handleChange('bank_account_number', e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="border-t border-slate-200 pt-4 mt-4">
                <h4 className="font-semibold text-slate-900 mb-4">Employment Details</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Department *</label>
                    <input
                      type="text"
                      data-testid="department-input"
                      className="input-field"
                      value={formData.department}
                      onChange={(e) => handleChange('department', e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="label">Position *</label>
                    <input
                      type="text"
                      data-testid="position-input"
                      className="input-field"
                      value={formData.position}
                      onChange={(e) => handleChange('position', e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <label className="label">Employment Type *</label>
                    <select
                      data-testid="employment-type-select"
                      className="input-field"
                      value={formData.employment_type}
                      onChange={(e) => handleChange('employment_type', e.target.value)}
                      required
                    >
                      <option value="Full-time">Full-time</option>
                      <option value="Part-time">Part-time</option>
                      <option value="Contract">Contract</option>
                      <option value="Intern">Intern</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Contract Start Date *</label>
                    <input
                      type="date"
                      data-testid="start-date-input"
                      className="input-field"
                      value={formData.contract_start_date}
                      onChange={(e) => handleChange('contract_start_date', e.target.value)}
                      required
                    />
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <div className="flex gap-3 pt-6 mt-6 border-t border-slate-200">
            <Button type="submit" className="btn-primary flex-1" data-testid="submit-employee-button">
              {initialData ? 'Update Employee' : 'Create Employee'}
            </Button>
            <Button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default EmployeeFormModal;
