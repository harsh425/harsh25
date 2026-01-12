import React, { useEffect, useState } from 'react';
import axios from 'axios';
import EmployeeLayout from '@/components/EmployeeLayout';
import { Upload, FileText, Download, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DocumentManagement = () => {
  const [employee, setEmployee] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadFile, setUploadFile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const empRes = await axios.get(`${API}/employees`);
      if (empRes.data.length > 0) {
        const empData = empRes.data[0];
        setEmployee(empData);
        const docsRes = await axios.get(`${API}/documents/employee/${empData.employee_id}`);
        setDocuments(docsRes.data);
      }
    } catch (error) {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
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
      await axios.post(`${API}/documents/upload?employee_id=${employee.employee_id}&category=${uploadCategory}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Document uploaded successfully');
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadCategory('');
      fetchData();
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

  // Group documents by category
  const groupedDocs = documents.reduce((acc, doc) => {
    if (!acc[doc.category]) acc[doc.category] = [];
    acc[doc.category].push(doc);
    return acc;
  }, {});

  if (loading) {
    return (
      <EmployeeLayout>
        <div className="text-center py-12">Loading...</div>
      </EmployeeLayout>
    );
  }

  return (
    <EmployeeLayout>
      <div data-testid="document-management-page">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">My Documents</h1>
            <p className="text-slate-600">Manage your personal documents</p>
          </div>
          <Button
            onClick={() => setShowUploadModal(true)}
            data-testid="upload-document-button"
            className="btn-primary flex items-center gap-2"
          >
            <Upload className="w-5 h-5" /> Upload Document
          </Button>
        </div>

        {documents.length === 0 ? (
          <div className="card p-12 text-center">
            <AlertCircle className="w-16 h-16 mx-auto mb-4 text-slate-400" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">No Documents Yet</h3>
            <p className="text-slate-600 mb-6">Start by uploading your first document</p>
            <Button
              onClick={() => setShowUploadModal(true)}
              className="btn-primary"
              data-testid="upload-first-document-button"
            >
              Upload Now
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedDocs).map(([category, docs]) => (
              <div key={category} className="card p-6">
                <h3 className="text-xl font-semibold mb-4 text-slate-900">{category}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {docs.map((doc) => (
                    <div
                      key={doc.document_id}
                      className="flex items-center justify-between p-4 border border-slate-200 rounded-sm hover:bg-slate-50 transition"
                      data-testid={`document-item-${doc.document_id}`}
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <FileText className="w-8 h-8 text-blue-900" />
                        <div>
                          <p className="font-semibold">{doc.filename}</p>
                          <p className="text-sm text-slate-500 mono">
                            {new Date(doc.uploaded_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDownload(doc.document_id, doc.filename)}
                        data-testid={`download-document-${doc.document_id}`}
                        className="text-blue-900 hover:underline flex items-center gap-1"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

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
                <p className="text-sm text-slate-500 mt-1">Accepted formats: PDF, JPG, PNG (Max 10MB)</p>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="btn-primary flex-1" data-testid="submit-upload-button">
                  Upload
                </Button>
                <Button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </EmployeeLayout>
  );
};

export default DocumentManagement;
