import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { DollarSign, Users, FileText, Play, Send, Calendar, Building2, Download } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PayrollManagement = () => {
  const [employees, setEmployees] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [payrollRuns, setPayrollRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [payslips, setPayslips] = useState([]);
  const [showSalaryModal, setShowSalaryModal] = useState(false);
  const [showRunModal, setShowRunModal] = useState(false);
  const [showPayslipModal, setShowPayslipModal] = useState(false);
  const [selectedPayslip, setSelectedPayslip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('runs');

  // Salary form state
  const [salaryForm, setSalaryForm] = useState({
    employee_number: '',
    basic_salary: '',
    house_allowance: '',
    transport_allowance: '',
    medical_allowance: '',
    other_allowances: '',
    pension_contribution: '',
    loan_deduction: '',
    other_deductions: '',
    effective_date: new Date().toISOString().split('T')[0]
  });

  // Payroll run form state
  const [runForm, setRunForm] = useState({
    company_id: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  });

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const [empRes, compRes, runsRes] = await Promise.all([
        axios.get(`${API}/employees`),
        axios.get(`${API}/companies`),
        axios.get(`${API}/payroll/runs`)
      ]);
      setEmployees(empRes.data.employees || empRes.data);
      setCompanies(compRes.data);
      setPayrollRuns(runsRes.data);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load data');
      setLoading(false);
    }
  };

  const fetchPayslips = async (runId) => {
    try {
      const response = await axios.get(`${API}/payroll/payslips/${runId}`);
      setPayslips(response.data);
      setSelectedRun(runId);
    } catch (error) {
      toast.error('Failed to fetch payslips');
    }
  };

  const handleCreateSalary = async () => {
    if (!salaryForm.employee_number || !salaryForm.basic_salary) {
      toast.error('Please select an employee and enter basic salary');
      return;
    }

    try {
      const payload = {
        ...salaryForm,
        basic_salary: parseFloat(salaryForm.basic_salary) || 0,
        house_allowance: parseFloat(salaryForm.house_allowance) || 0,
        transport_allowance: parseFloat(salaryForm.transport_allowance) || 0,
        medical_allowance: parseFloat(salaryForm.medical_allowance) || 0,
        other_allowances: parseFloat(salaryForm.other_allowances) || 0,
        pension_contribution: parseFloat(salaryForm.pension_contribution) || 0,
        loan_deduction: parseFloat(salaryForm.loan_deduction) || 0,
        other_deductions: parseFloat(salaryForm.other_deductions) || 0
      };

      await axios.post(`${API}/payroll/salary-structure`, payload);
      toast.success('Salary structure created successfully');
      setShowSalaryModal(false);
      setSalaryForm({
        employee_number: '',
        basic_salary: '',
        house_allowance: '',
        transport_allowance: '',
        medical_allowance: '',
        other_allowances: '',
        pension_contribution: '',
        loan_deduction: '',
        other_deductions: '',
        effective_date: new Date().toISOString().split('T')[0]
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create salary structure');
    }
  };

  const handleRunPayroll = async () => {
    if (!runForm.month || !runForm.year) {
      toast.error('Please select month and year');
      return;
    }

    try {
      const payload = {
        month: parseInt(runForm.month),
        year: parseInt(runForm.year),
        company_id: runForm.company_id || null
      };

      const response = await axios.post(`${API}/payroll/run`, payload);
      toast.success(response.data.message);
      setShowRunModal(false);
      fetchInitialData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to run payroll');
    }
  };

  const handleSendPayslip = async (payslipId) => {
    try {
      await axios.post(`${API}/payroll/send-payslip/${payslipId}`);
      toast.success('Payslip sent successfully');
    } catch (error) {
      toast.error('Failed to send payslip');
    }
  };

  const viewPayslip = (payslip) => {
    setSelectedPayslip(payslip);
    setShowPayslipModal(true);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES',
      minimumFractionDigits: 2
    }).format(amount);
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
      <div data-testid="payroll-management-page">
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Payroll Management</h1>
            <p className="text-slate-600">Manage salaries, run payroll, and generate payslips</p>
          </div>
          
          <div className="flex gap-3">
            <Button
              onClick={() => setShowSalaryModal(true)}
              data-testid="add-salary-btn"
              className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-2"
            >
              <DollarSign className="w-4 h-4" />
              Add Salary Structure
            </Button>
            <Button
              onClick={() => setShowRunModal(true)}
              data-testid="run-payroll-btn"
              className="bg-blue-900 hover:bg-blue-800 text-white flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Run Payroll
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card p-6" data-testid="stat-total-runs">
            <p className="label mb-2">Payroll Runs</p>
            <p className="text-3xl font-bold text-slate-900">{payrollRuns.length}</p>
          </div>
          <div className="card p-6" data-testid="stat-employees">
            <p className="label mb-2">Active Employees</p>
            <p className="text-3xl font-bold text-emerald-600">{employees.filter(e => e.status === 'active').length}</p>
          </div>
          <div className="card p-6" data-testid="stat-latest-gross">
            <p className="label mb-2">Latest Gross Total</p>
            <p className="text-3xl font-bold text-blue-900">
              {payrollRuns[0] ? formatCurrency(payrollRuns[0].totals?.gross_salary || 0) : 'N/A'}
            </p>
          </div>
          <div className="card p-6" data-testid="stat-latest-net">
            <p className="label mb-2">Latest Net Total</p>
            <p className="text-3xl font-bold text-slate-700">
              {payrollRuns[0] ? formatCurrency(payrollRuns[0].totals?.net_salary || 0) : 'N/A'}
            </p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="runs" data-testid="runs-tab">
              <Calendar className="w-4 h-4 mr-2" />
              Payroll Runs
            </TabsTrigger>
            <TabsTrigger value="payslips" data-testid="payslips-tab">
              <FileText className="w-4 h-4 mr-2" />
              Payslips
            </TabsTrigger>
          </TabsList>

          <TabsContent value="runs">
            <div className="card overflow-hidden" data-testid="payroll-runs-table">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Period</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Company</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Employees</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Gross Salary</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Net Salary</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">PAYE</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payrollRuns.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="text-center py-12 text-slate-500">
                        No payroll runs yet. Click "Run Payroll" to start.
                      </td>
                    </tr>
                  ) : (
                    payrollRuns.map((run) => (
                      <tr key={run.payroll_run_id} className="border-t hover:bg-slate-50" data-testid={`run-${run.payroll_run_id}`}>
                        <td className="px-6 py-4 font-semibold">{run.period}</td>
                        <td className="px-6 py-4">{run.company_id ? companies.find(c => c.company_id === run.company_id)?.company_name || 'N/A' : 'All Companies'}</td>
                        <td className="px-6 py-4">{run.employees_processed}</td>
                        <td className="px-6 py-4 mono">{formatCurrency(run.totals?.gross_salary || 0)}</td>
                        <td className="px-6 py-4 mono">{formatCurrency(run.totals?.net_salary || 0)}</td>
                        <td className="px-6 py-4 mono">{formatCurrency(run.totals?.paye || 0)}</td>
                        <td className="px-6 py-4">
                          <span className={`badge ${run.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                            {run.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => fetchPayslips(run.payroll_run_id)}
                            data-testid={`view-payslips-${run.payroll_run_id}`}
                          >
                            View Payslips
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </TabsContent>

          <TabsContent value="payslips">
            {selectedRun ? (
              <div className="card overflow-hidden" data-testid="payslips-table">
                <div className="p-4 bg-slate-50 border-b">
                  <p className="font-semibold">Payslips for: {payrollRuns.find(r => r.payroll_run_id === selectedRun)?.period}</p>
                </div>
                <table className="w-full">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Employee</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Gross</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">PAYE</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">NSSF</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">SHIF</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Net</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payslips.map((payslip) => (
                      <tr key={payslip.payslip_id} className="border-t hover:bg-slate-50">
                        <td className="px-6 py-4">
                          <p className="font-medium">{payslip.employee_name}</p>
                          <p className="text-sm text-slate-500 mono">{payslip.employee_number}</p>
                        </td>
                        <td className="px-6 py-4 mono">{formatCurrency(payslip.earnings?.gross_salary || 0)}</td>
                        <td className="px-6 py-4 mono">{formatCurrency(payslip.deductions?.paye || 0)}</td>
                        <td className="px-6 py-4 mono">{formatCurrency(payslip.deductions?.nssf_employee || 0)}</td>
                        <td className="px-6 py-4 mono">{formatCurrency(payslip.deductions?.shif || 0)}</td>
                        <td className="px-6 py-4 mono font-semibold">{formatCurrency(payslip.net_salary || 0)}</td>
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline" onClick={() => viewPayslip(payslip)}>
                              <FileText className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleSendPayslip(payslip.payslip_id)}>
                              <Send className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="card p-12 text-center text-slate-500">
                Select a payroll run to view payslips
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Add Salary Structure Modal */}
        <Dialog open={showSalaryModal} onOpenChange={setShowSalaryModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Add Salary Structure</DialogTitle>
            </DialogHeader>

            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              <div>
                <label className="label">Employee *</label>
                <Select 
                  value={salaryForm.employee_number} 
                  onValueChange={(value) => setSalaryForm(prev => ({ ...prev, employee_number: value }))}
                >
                  <SelectTrigger data-testid="salary-employee-select">
                    <SelectValue placeholder="Select employee" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map((emp) => (
                      <SelectItem key={emp.employee_number} value={emp.employee_number}>
                        {emp.first_name} {emp.last_name} ({emp.employee_number})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Basic Salary (KSh) *</label>
                  <input
                    type="number"
                    data-testid="basic-salary-input"
                    className="input-field"
                    value={salaryForm.basic_salary}
                    onChange={(e) => setSalaryForm(prev => ({ ...prev, basic_salary: e.target.value }))}
                    placeholder="e.g., 50000"
                  />
                </div>
                <div>
                  <label className="label">House Allowance (KSh)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={salaryForm.house_allowance}
                    onChange={(e) => setSalaryForm(prev => ({ ...prev, house_allowance: e.target.value }))}
                    placeholder="e.g., 15000"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Transport Allowance (KSh)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={salaryForm.transport_allowance}
                    onChange={(e) => setSalaryForm(prev => ({ ...prev, transport_allowance: e.target.value }))}
                    placeholder="e.g., 5000"
                  />
                </div>
                <div>
                  <label className="label">Medical Allowance (KSh)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={salaryForm.medical_allowance}
                    onChange={(e) => setSalaryForm(prev => ({ ...prev, medical_allowance: e.target.value }))}
                    placeholder="e.g., 3000"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Other Allowances (KSh)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={salaryForm.other_allowances}
                    onChange={(e) => setSalaryForm(prev => ({ ...prev, other_allowances: e.target.value }))}
                    placeholder="e.g., 2000"
                  />
                </div>
                <div>
                  <label className="label">Pension Contribution (KSh)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={salaryForm.pension_contribution}
                    onChange={(e) => setSalaryForm(prev => ({ ...prev, pension_contribution: e.target.value }))}
                    placeholder="e.g., 5000"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Loan Deduction (KSh)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={salaryForm.loan_deduction}
                    onChange={(e) => setSalaryForm(prev => ({ ...prev, loan_deduction: e.target.value }))}
                    placeholder="e.g., 3000"
                  />
                </div>
                <div>
                  <label className="label">Other Deductions (KSh)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={salaryForm.other_deductions}
                    onChange={(e) => setSalaryForm(prev => ({ ...prev, other_deductions: e.target.value }))}
                    placeholder="e.g., 1000"
                  />
                </div>
              </div>

              <div>
                <label className="label">Effective Date *</label>
                <input
                  type="date"
                  className="input-field"
                  value={salaryForm.effective_date}
                  onChange={(e) => setSalaryForm(prev => ({ ...prev, effective_date: e.target.value }))}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleCreateSalary}
                  data-testid="submit-salary-btn"
                  className="bg-emerald-600 hover:bg-emerald-700 text-white flex-1"
                >
                  Create Salary Structure
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowSalaryModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Run Payroll Modal */}
        <Dialog open={showRunModal} onOpenChange={setShowRunModal}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Run Payroll</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <div>
                <label className="label">Company (optional)</label>
                <Select 
                  value={runForm.company_id} 
                  onValueChange={(value) => setRunForm(prev => ({ ...prev, company_id: value }))}
                >
                  <SelectTrigger data-testid="run-company-select">
                    <SelectValue placeholder="All Companies" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Companies</SelectItem>
                    {companies.map((company) => (
                      <SelectItem key={company.company_id} value={company.company_id}>
                        {company.company_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Month *</label>
                  <Select 
                    value={runForm.month.toString()} 
                    onValueChange={(value) => setRunForm(prev => ({ ...prev, month: parseInt(value) }))}
                  >
                    <SelectTrigger data-testid="run-month-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {months.map((month, index) => (
                        <SelectItem key={index} value={(index + 1).toString()}>
                          {month}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="label">Year *</label>
                  <Select 
                    value={runForm.year.toString()} 
                    onValueChange={(value) => setRunForm(prev => ({ ...prev, year: parseInt(value) }))}
                  >
                    <SelectTrigger data-testid="run-year-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[2025, 2024, 2023].map((year) => (
                        <SelectItem key={year} value={year.toString()}>
                          {year}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleRunPayroll}
                  data-testid="submit-run-btn"
                  className="bg-blue-900 hover:bg-blue-800 text-white flex-1"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Run Payroll
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowRunModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* View Payslip Modal */}
        <Dialog open={showPayslipModal} onOpenChange={setShowPayslipModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Payslip Details</DialogTitle>
            </DialogHeader>

            {selectedPayslip && (
              <div className="space-y-6">
                <div className="flex justify-between items-start border-b pb-4">
                  <div>
                    <h3 className="text-xl font-semibold">{selectedPayslip.employee_name}</h3>
                    <p className="text-slate-600 mono">{selectedPayslip.employee_number}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-blue-900">{selectedPayslip.period}</p>
                    <p className="text-sm text-slate-500">{selectedPayslip.company_name}</p>
                  </div>
                </div>

                {/* Earnings */}
                <div>
                  <h4 className="font-semibold text-emerald-700 mb-3">Earnings</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span className="text-slate-600">Basic Salary:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.earnings?.basic_salary || 0)}</span>
                    <span className="text-slate-600">House Allowance:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.earnings?.house_allowance || 0)}</span>
                    <span className="text-slate-600">Transport Allowance:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.earnings?.transport_allowance || 0)}</span>
                    <span className="text-slate-600">Medical Allowance:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.earnings?.medical_allowance || 0)}</span>
                    <span className="text-slate-600">Other Allowances:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.earnings?.other_allowances || 0)}</span>
                    <span className="font-semibold border-t pt-2">Gross Salary:</span>
                    <span className="text-right mono font-semibold border-t pt-2">{formatCurrency(selectedPayslip.earnings?.gross_salary || 0)}</span>
                  </div>
                </div>

                {/* Deductions */}
                <div>
                  <h4 className="font-semibold text-red-700 mb-3">Deductions</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span className="text-slate-600">PAYE Tax:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.deductions?.paye || 0)}</span>
                    <span className="text-slate-600">NSSF:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.deductions?.nssf_employee || 0)}</span>
                    <span className="text-slate-600">SHIF:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.deductions?.shif || 0)}</span>
                    <span className="text-slate-600">Pension:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.deductions?.pension_contribution || 0)}</span>
                    <span className="text-slate-600">Loan Deduction:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.deductions?.loan_deduction || 0)}</span>
                    <span className="text-slate-600">Other Deductions:</span>
                    <span className="text-right mono">{formatCurrency(selectedPayslip.deductions?.other_deductions || 0)}</span>
                    <span className="font-semibold border-t pt-2">Total Deductions:</span>
                    <span className="text-right mono font-semibold border-t pt-2">{formatCurrency(selectedPayslip.deductions?.total_deductions || 0)}</span>
                  </div>
                </div>

                {/* Net Salary */}
                <div className="bg-blue-900 text-white p-4 rounded-lg">
                  <div className="flex justify-between items-center">
                    <span className="text-lg">Net Salary:</span>
                    <span className="text-2xl font-bold">{formatCurrency(selectedPayslip.net_salary || 0)}</span>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    onClick={() => handleSendPayslip(selectedPayslip.payslip_id)}
                    className="bg-blue-900 hover:bg-blue-800 text-white flex-1"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Send to Employee
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowPayslipModal(false)}
                    className="flex-1"
                  >
                    Close
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
};

export default PayrollManagement;
