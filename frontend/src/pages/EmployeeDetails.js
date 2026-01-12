import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { ArrowLeft, Upload, FileText, Download } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EmployeeDetails = () => {
  const { employeeId } = useParams();
  const navigate = useNavigate();
  const [employee, setEmployee] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadFile, setUploadFile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEmployee();
    fetchDocuments();
  }, [employeeId]);

  const fetchEmployee = async () => {
    try {
      const response = await axios.get(`${API}/employees/${employeeId}`);
      setEmployee(response.data);
    } catch (error) {
      toast.error('Failed to load employee');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents/employee/${employeeId}`);
      setDocuments(response.data);
    } catch (error) {
      toast.error('Failed to load documents');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile || !uploadCategory) {
      toast.error('Please select a file and category');
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      await axios.post(`${API}/documents/upload?employee_id=${employeeId}&category=${uploadCategory}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Document uploaded successfully');
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadCategory('');
      fetchDocuments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload document');
    }
  };

  const handleDownload = async (documentId, filename) => {
    try {
      const response = await axios.get(`${API}/documents/${documentId}/download`);
      const byteCharacters = atob(response.data.data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: response.data.content_type });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      toast.success('Document downloaded');
    } catch (error) {
      toast.error('Failed to download document');
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
      <div data-testid="employee-details-page">
        <button
          onClick={() => navigate('/employees')}
          data-testid="back-to-employees-button"
          className="flex items-center gap-2 text-blue-900 hover:underline mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Employees
        </button>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Employee Info */}
          <div className="md:col-span-2">
            <div className="card p-8">
              <h2 className="text-3xl font-bold text-slate-900 mb-6">{employee?.full_name}</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="label">Employee ID</p>
                  <p className="mono font-semibold">{employee?.employee_id}</p>
                </div>
                <div>
                  <p className="label">Email</p>
                  <p>{employee?.email}</p>
                </div>
                <div>
                  <p className="label">Phone</p>
                  <p>{employee?.phone}</p>
                </div>
                <div>
                  <p className="label">Department</p>
                  <p>{employee?.department}</p>
                </div>
                <div>
                  <p className="label">Position</p>
                  <p>{employee?.position}</p>
                </div>
                <div>
                  <p className="label">Employment Type</p>
                  <p>{employee?.employment_type}</p>
                </div>
                <div>
                  <p className="label">Start Date</p>
                  <p>{employee?.contract_start_date}</p>
                </div>
                <div>
                  <p className="label">Emergency Contact</p>
                  <p>{employee?.emergency_contact}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div>
            <div className="card p-6">
              <h3 className="text-xl font-semibold mb-4">Quick Stats</h3>
              <div className="space-y-3">
                <div>
                  <p className="label">Total Documents</p>
                  <p className="text-2xl font-bold text-blue-900">{documents.length}</p>
                </div>
                <div>
                  <p className="label">Status</p>
                  <span className={`badge ${employee?.status === 'active' ? 'badge-success' : 'badge-danger'}`}>
                    {employee?.status}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Documents Section */}
        <div className="mt-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-bold text-slate-900">Documents</h3>
            <Button
              onClick={() => setShowUploadModal(true)}
              data-testid="upload-document-button"
              className="btn-primary flex items-center gap-2"
            >
              <Upload className="w-4 h-4" /> Upload Document
            </Button>
          </div>

          <div className="card overflow-hidden">
            <table className="w-full grid-border" data-testid="documents-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Category</th>
                  <th className="px-6 py-4 text-left label">Filename</th>
                  <th className="px-6 py-4 text-left label">Uploaded At</th>
                  <th className="px-6 py-4 text-left label">Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="text-center py-12 text-slate-500">No documents uploaded</td>
                  </tr>
                ) : (
                  documents.map((doc) => (
                    <tr key={doc.document_id} className="hover:bg-slate-50" data-testid={`document-row-${doc.document_id}`}>
                      <td className="px-6 py-4">
                        <span className="badge badge-info">{doc.category}</span>
                      </td>
                      <td className="px-6 py-4 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-slate-500" />
                        {doc.filename}
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {new Date(doc.uploaded_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleDownload(doc.document_id, doc.filename)}
                          data-testid={`download-document-${doc.document_id}`}
                          className="text-blue-900 hover:underline flex items-center gap-1"
                        >
                          <Download className="w-4 h-4" /> Download
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Upload Modal */}
        <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Upload Document</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleUpload} className="space-y-4" data-testid="upload-document-form">
              <div>
                <label className="label">Category</label>
                <select
                  data-testid="upload-category-select"
                  className="input-field"
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  required
                >
                  <option value="">Select category...</option>
                  <option value="ID">ID Document</option>
                  <option value="KRA_PIN">KRA PIN</option>
                  <option value="NHIF">NHIF</option>
                  <option value="NSSF">NSSF</option>
                  <option value="Certificate">Certificate</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="label">File</label>
                <input
                  type="file"
                  data-testid="upload-file-input"
                  className="input-field"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  required
                  accept=".pdf,.jpg,.jpeg,.png"
                />
                <p className="text-sm text-slate-500 mt-1">Accepted formats: PDF, JPG, PNG</p>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="btn-primary flex-1" data-testid="submit-upload-button">
                  Upload
                </Button>
                <Button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="btn-secondary flex-1"
                  data-testid="cancel-upload-button"
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

export default EmployeeDetails;
