import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { FileText, Upload, Download, Trash2, Search, Calendar, DollarSign, User } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PayrollDocuments = () => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    employee_id: '',
    category: 'payslip',
    month: '',
    year: new Date().getFullYear().toString(),
    file: null
  });

  const documentCategories = [
    { value: 'payslip', label: 'Payslip' },
    { value: 'p9_form', label: 'P9 Form (KRA Tax Certificate)' },
    { value: 'bonus_statement', label: 'Bonus Statement' },
    { value: 'salary_advance', label: 'Salary Advance' },
    { value: 'nssf_statement', label: 'NSSF Statement' },
    { value: 'shif_statement', label: 'SHIF Statement' },
    { value: 'bank_statement', label: 'Bank Statement' },
    { value: 'other', label: 'Other' }
  ];

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    if (selectedEmployee) {
      fetchDocuments(selectedEmployee.employee_number);
    }
  }, [selectedEmployee]);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data.employees || response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load employees');
      setLoading(false);
    }
  };

  const fetchDocuments = async (employeeId) => {
    try {
      const response = await axios.get(`${API}/documents?employee_id=${employeeId}&category_prefix=payroll`);
      // Filter payroll-related documents
      const payrollDocs = response.data.filter(doc => 
        ['payslip', 'p9_form', 'bonus_statement', 'salary_advance', 'nssf_statement', 'shif_statement', 'bank_statement'].includes(doc.category) ||
        doc.category?.startsWith('payroll')
      );
      setDocuments(payrollDocs);
    } catch (error) {
      // If endpoint doesn't filter by category, get all and filter
      try {
        const response = await axios.get(`${API}/documents?employee_id=${employeeId}`);
        const payrollDocs = response.data.filter(doc => 
          ['payslip', 'p9_form', 'bonus_statement', 'salary_advance', 'nssf_statement', 'shif_statement', 'bank_statement'].includes(doc.category)
        );
        setDocuments(payrollDocs);
      } catch (err) {
        setDocuments([]);
      }
    }
  };

  const handleUpload = async () => {
    if (!uploadForm.employee_id || !uploadForm.file) {
      toast.error('Please select an employee and file');
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('employee_id', uploadForm.employee_id);
      formData.append('category', uploadForm.category);
      
      // Add metadata
      const metadata = {
        month: uploadForm.month,
        year: uploadForm.year,
        document_type: 'payroll'
      };
      formData.append('metadata', JSON.stringify(metadata));

      await axios.post(`${API}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success('Document uploaded successfully');
      setShowUploadModal(false);
      setUploadForm({
        employee_id: '',
        category: 'payslip',
        month: '',
        year: new Date().getFullYear().toString(),
        file: null
      });
      
      if (selectedEmployee) {
        fetchDocuments(selectedEmployee.employee_number);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (doc) => {
    try {
      const response = await axios.get(`${API}/documents/${doc.document_id}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download document');
    }
  };

  const handleDelete = async (doc) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/documents/${doc.document_id}`);
      toast.success('Document deleted');
      if (selectedEmployee) {
        fetchDocuments(selectedEmployee.employee_number);
      }
    } catch (error) {
      toast.error('Failed to delete document');
    }
  };

  const getCategoryLabel = (category) => {
    const cat = documentCategories.find(c => c.value === category);
    return cat ? cat.label : category;
  };

  const filteredEmployees = employees.filter(emp => 
    `${emp.first_name} ${emp.last_name} ${emp.employee_number}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <AdminLayout>
        <div className="text-center py-12">Loading...</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div data-testid="payroll-documents-page">
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Payroll Documents</h1>
            <p className="text-slate-600">Manage payslips, tax forms, and payroll-related documents</p>
          </div>
          
          <Button
            onClick={() => setShowUploadModal(true)}
            data-testid="upload-payroll-doc-btn"
            className="bg-blue-900 hover:bg-blue-800 text-white flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Upload Document
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Employee List */}
          <div className="card overflow-hidden">
            <div className="p-4 border-b border-slate-200">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  data-testid="employee-search-input"
                  className="input-field pl-10"
                  placeholder="Search employees..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <div className="max-h-[600px] overflow-y-auto" data-testid="employee-list">
              {filteredEmployees.map((emp) => (
                <button
                  key={emp.employee_number}
                  onClick={() => setSelectedEmployee(emp)}
                  data-testid={`employee-item-${emp.employee_number}`}
                  className={`w-full text-left p-4 border-b border-slate-100 hover:bg-slate-50 transition ${
                    selectedEmployee?.employee_number === emp.employee_number ? 'bg-blue-50 border-l-4 border-l-blue-900' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-slate-600" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{emp.first_name} {emp.last_name}</p>
                      <p className="text-sm text-slate-500 mono">{emp.employee_number}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Documents List */}
          <div className="md:col-span-2">
            {selectedEmployee ? (
              <div className="card overflow-hidden">
                <div className="p-6 border-b border-slate-200 bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-semibold text-slate-900">
                        {selectedEmployee.first_name} {selectedEmployee.last_name}
                      </h2>
                      <p className="text-sm text-slate-500">{selectedEmployee.position} • {selectedEmployee.department}</p>
                    </div>
                    <Button
                      onClick={() => {
                        setUploadForm(prev => ({ ...prev, employee_id: selectedEmployee.employee_number }));
                        setShowUploadModal(true);
                      }}
                      data-testid="upload-for-employee-btn"
                      size="sm"
                      className="bg-emerald-600 hover:bg-emerald-700 text-white"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Upload
                    </Button>
                  </div>
                </div>

                <div className="overflow-x-auto" data-testid="documents-table">
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Document</th>
                        <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Category</th>
                        <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Period</th>
                        <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Uploaded</th>
                        <th className="px-6 py-3 text-left text-sm font-medium text-slate-700">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {documents.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="text-center py-12 text-slate-500">
                            <FileText className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                            <p>No payroll documents found</p>
                            <p className="text-sm mt-2">Upload documents for this employee</p>
                          </td>
                        </tr>
                      ) : (
                        documents.map((doc) => (
                          <tr key={doc.document_id} className="border-t hover:bg-slate-50" data-testid={`doc-row-${doc.document_id}`}>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                <FileText className="w-5 h-5 text-slate-400" />
                                <span className="font-medium text-slate-900">{doc.filename}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className="badge badge-info">{getCategoryLabel(doc.category)}</span>
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-600">
                              {doc.metadata?.month && doc.metadata?.year 
                                ? `${doc.metadata.month} ${doc.metadata.year}` 
                                : '-'}
                            </td>
                            <td className="px-6 py-4 mono text-sm text-slate-600">
                              {new Date(doc.uploaded_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleDownload(doc)}
                                  data-testid={`download-doc-${doc.document_id}`}
                                  className="p-2 text-blue-600 hover:bg-blue-50 rounded transition"
                                  title="Download"
                                >
                                  <Download className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDelete(doc)}
                                  data-testid={`delete-doc-${doc.document_id}`}
                                  className="p-2 text-red-600 hover:bg-red-50 rounded transition"
                                  title="Delete"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="card p-12 text-center">
                <DollarSign className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-700 mb-2">Select an Employee</h3>
                <p className="text-slate-500">Choose an employee from the list to view their payroll documents</p>
              </div>
            )}
          </div>
        </div>

        {/* Upload Modal */}
        <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Upload Payroll Document</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <div>
                <label className="label">Employee *</label>
                <Select 
                  value={uploadForm.employee_id} 
                  onValueChange={(value) => setUploadForm(prev => ({ ...prev, employee_id: value }))}
                >
                  <SelectTrigger data-testid="upload-employee-select">
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

              <div>
                <label className="label">Document Category *</label>
                <Select 
                  value={uploadForm.category} 
                  onValueChange={(value) => setUploadForm(prev => ({ ...prev, category: value }))}
                >
                  <SelectTrigger data-testid="upload-category-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {documentCategories.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Month</label>
                  <Select 
                    value={uploadForm.month} 
                    onValueChange={(value) => setUploadForm(prev => ({ ...prev, month: value }))}
                  >
                    <SelectTrigger data-testid="upload-month-select">
                      <SelectValue placeholder="Select month" />
                    </SelectTrigger>
                    <SelectContent>
                      {months.map((month) => (
                        <SelectItem key={month} value={month}>
                          {month}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="label">Year</label>
                  <Select 
                    value={uploadForm.year} 
                    onValueChange={(value) => setUploadForm(prev => ({ ...prev, year: value }))}
                  >
                    <SelectTrigger data-testid="upload-year-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[2025, 2024, 2023, 2022, 2021].map((year) => (
                        <SelectItem key={year} value={year.toString()}>
                          {year}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <label className="label">File *</label>
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-blue-500 transition cursor-pointer">
                  <input
                    type="file"
                    data-testid="file-upload-input"
                    className="hidden"
                    id="payroll-file-upload"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                    onChange={(e) => setUploadForm(prev => ({ ...prev, file: e.target.files[0] }))}
                  />
                  <label htmlFor="payroll-file-upload" className="cursor-pointer">
                    <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                    {uploadForm.file ? (
                      <p className="text-slate-700 font-medium">{uploadForm.file.name}</p>
                    ) : (
                      <>
                        <p className="text-slate-700 font-medium">Click to upload</p>
                        <p className="text-sm text-slate-500 mt-1">PDF, DOC, XLS, or Images</p>
                      </>
                    )}
                  </label>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleUpload}
                  disabled={uploading}
                  data-testid="submit-upload-btn"
                  className="bg-blue-900 hover:bg-blue-800 text-white flex-1"
                >
                  {uploading ? 'Uploading...' : 'Upload Document'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
};

export default PayrollDocuments;
