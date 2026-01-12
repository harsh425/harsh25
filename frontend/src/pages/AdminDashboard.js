import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { Users, FileText, CheckCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [contractStats, setContractStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const [dashboardRes, contractRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/contracts/stats`)
      ]);
      setStats(dashboardRes.data);
      setContractStats(contractRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
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
      <div data-testid="admin-dashboard">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Control Room</h1>
          <p className="text-slate-600">Welcome back! Here's your HR overview.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card p-6" data-testid="stat-employees">
            <div className="flex items-center justify-between">
              <div>
                <p className="label mb-2">Total Employees</p>
                <p className="text-3xl font-bold text-slate-900">{stats?.total_employees || 0}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-sm flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-900" />
              </div>
            </div>
          </div>

          <div className="card p-6" data-testid="stat-active">
            <div className="flex items-center justify-between">
              <div>
                <p className="label mb-2">Active Employees</p>
                <p className="text-3xl font-bold text-emerald-600">{stats?.active_employees || 0}</p>
              </div>
              <div className="w-12 h-12 bg-emerald-100 rounded-sm flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
          </div>

          <div className="card p-6" data-testid="stat-documents">
            <div className="flex items-center justify-between">
              <div>
                <p className="label mb-2">Total Documents</p>
                <p className="text-3xl font-bold text-slate-900">{stats?.total_documents || 0}</p>
              </div>
              <div className="w-12 h-12 bg-slate-100 rounded-sm flex items-center justify-center">
                <FileText className="w-6 h-6 text-slate-700" />
              </div>
            </div>
          </div>

          <div className="card p-6" data-testid="stat-pending">
            <div className="flex items-center justify-between">
              <div>
                <p className="label mb-2">Pending Signatures</p>
                <p className="text-3xl font-bold text-orange-600">{stats?.pending_signatures || 0}</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-sm flex items-center justify-center">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Contract Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card p-6">
            <h3 className="text-xl font-semibold mb-4 text-slate-900">Contract Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Total Contracts</span>
                <span className="mono text-lg font-bold">{contractStats?.total || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Sent</span>
                <span className="badge badge-info">{contractStats?.sent || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Viewed</span>
                <span className="badge badge-warning">{contractStats?.viewed || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Signed</span>
                <span className="badge badge-success">{contractStats?.signed || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Expired</span>
                <span className="badge badge-danger">{contractStats?.expired || 0}</span>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-xl font-semibold mb-4 text-slate-900">Quick Actions</h3>
            <div className="space-y-3">
              <a
                href="/employees"
                data-testid="quick-action-add-employee"
                className="block p-4 bg-blue-50 hover:bg-blue-100 rounded-sm transition"
              >
                <p className="font-semibold text-blue-900">Add New Employee</p>
                <p className="text-sm text-blue-700">Create a new employee profile</p>
              </a>
              <a
                href="/contracts"
                data-testid="quick-action-send-contract"
                className="block p-4 bg-orange-50 hover:bg-orange-100 rounded-sm transition"
              >
                <p className="font-semibold text-orange-900">Send Contract</p>
                <p className="text-sm text-orange-700">Create and send employment contract</p>
              </a>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminDashboard;
