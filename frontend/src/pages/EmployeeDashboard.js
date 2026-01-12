import React, { useEffect, useState } from 'react';
import axios from 'axios';
import EmployeeLayout from '@/components/EmployeeLayout';
import { FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EmployeeDashboard = () => {
  const [employee, setEmployee] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [empRes, contractsRes] = await Promise.all([
        axios.get(`${API}/employees`),
        axios.get(`${API}/contracts`)
      ]);

      if (empRes.data.length > 0) {
        const empData = empRes.data[0];
        setEmployee(empData);

        // Fetch documents
        const docsRes = await axios.get(`${API}/documents/employee/${empData.employee_id}`);
        setDocuments(docsRes.data);
      }

      setContracts(contractsRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const pendingContracts = contracts.filter(c => c.status === 'sent' || c.status === 'viewed');
  const signedContracts = contracts.filter(c => c.status === 'signed');

  if (loading) {
    return (
      <EmployeeLayout>
        <div className="text-center py-12">Loading...</div>
      </EmployeeLayout>
    );
  }

  return (
    <EmployeeLayout>
      <div data-testid="employee-dashboard">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Welcome, {employee?.full_name}!</h1>
          <p className="text-slate-600">Your personal dashboard</p>
        </div>

        {/* Stats Grid - Tetris Layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-8">
          {/* Large Card */}
          <div className="md:col-span-8 card p-8">
            <h2 className="text-2xl font-semibold mb-6 text-slate-900">Your Profile</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="label">Employee ID</p>
                <p className="mono font-semibold text-lg">{employee?.employee_id}</p>
              </div>
              <div>
                <p className="label">Department</p>
                <p className="text-lg">{employee?.department}</p>
              </div>
              <div>
                <p className="label">Position</p>
                <p className="text-lg">{employee?.position}</p>
              </div>
              <div>
                <p className="label">Employment Type</p>
                <p className="text-lg">{employee?.employment_type}</p>
              </div>
              <div>
                <p className="label">Start Date</p>
                <p className="text-lg">{employee?.contract_start_date}</p>
              </div>
              <div>
                <p className="label">Status</p>
                <span className="badge badge-success">{employee?.status}</span>
              </div>
            </div>
          </div>

          {/* Small Cards */}
          <div className="md:col-span-4 space-y-6">
            <div className="card p-6" data-testid="stat-documents">
              <div className="flex items-center justify-between">
                <div>
                  <p className="label mb-2">My Documents</p>
                  <p className="text-3xl font-bold text-blue-900">{documents.length}</p>
                </div>
                <FileText className="w-10 h-10 text-blue-900" />
              </div>
            </div>

            <div className="card p-6" data-testid="stat-contracts">
              <div className="flex items-center justify-between">
                <div>
                  <p className="label mb-2">Signed Contracts</p>
                  <p className="text-3xl font-bold text-emerald-600">{signedContracts.length}</p>
                </div>
                <CheckCircle className="w-10 h-10 text-emerald-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Pending Contracts - Tracing Beam Effect */}
        {pendingContracts.length > 0 && (
          <div className="mb-8">
            <h3 className="text-2xl font-bold text-slate-900 mb-4">Action Required</h3>
            <div className="space-y-4">
              {pendingContracts.map((contract) => (
                <div
                  key={contract.contract_id}
                  className="card p-6 tracing-beam pl-8"
                  data-testid={`pending-contract-${contract.contract_id}`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="text-lg font-semibold text-slate-900 mb-2">{contract.title}</h4>
                      <p className="text-slate-600 mb-3">{contract.description}</p>
                      <div className="flex items-center gap-4">
                        <span className="badge badge-warning flex items-center gap-1">
                          <Clock className="w-3 h-3" /> Pending Signature
                        </span>
                        <span className="text-sm text-slate-500">
                          Expires: {new Date(contract.expiry_date).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <a
                      href={`/sign-contract/${contract.signing_token}`}
                      data-testid={`sign-contract-${contract.contract_id}`}
                      className="btn-secondary"
                    >
                      Sign Now
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Documents */}
        <div>
          <h3 className="text-2xl font-bold text-slate-900 mb-4">Recent Documents</h3>
          {documents.length === 0 ? (
            <div className="card p-12 text-center text-slate-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 text-slate-400" />
              <p>No documents uploaded yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {documents.slice(0, 6).map((doc) => (
                <div key={doc.document_id} className="card p-4" data-testid={`document-${doc.document_id}`}>
                  <div className="flex items-center gap-3">
                    <FileText className="w-8 h-8 text-blue-900" />
                    <div className="flex-1">
                      <p className="font-semibold text-sm truncate">{doc.filename}</p>
                      <p className="text-xs text-slate-500">{doc.category}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </EmployeeLayout>
  );
};

export default EmployeeDashboard;
