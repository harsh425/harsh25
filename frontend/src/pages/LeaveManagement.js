import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import EmployeeLayout from '@/components/EmployeeLayout';
import { Calendar, Plus, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LeaveManagement = () => {
  const { user } = useAuth();
  const [balance, setBalance] = useState(null);
  const [requests, setRequests] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    leave_type: 'Annual',
    start_date: '',
    end_date: '',
    reason: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [balanceRes, requestsRes, holidaysRes] = await Promise.all([
        axios.get(`${API}/leave/balance`),
        axios.get(`${API}/leave/my-requests`),
        axios.get(`${API}/leave/holidays`)
      ]);
      setBalance(balanceRes.data);
      setRequests(requestsRes.data);
      setHolidays(holidaysRes.data.holidays);
    } catch (error) {
      toast.error('Failed to load leave data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/leave/request`, formData);
      toast.success(`Leave request submitted! ${response.data.days_requested} working days requested`);
      setShowRequestModal(false);
      setFormData({
        leave_type: 'Annual',
        start_date: '',
        end_date: '',
        reason: ''
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit leave request');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { class: 'badge-warning', icon: Clock, text: 'Pending' },
      approved: { class: 'badge-success', icon: CheckCircle, text: 'Approved' },
      rejected: { class: 'badge-danger', icon: XCircle, text: 'Rejected' }
    };
    const badge = badges[status] || badges.pending;
    const Icon = badge.icon;
    return (
      <span className={`badge ${badge.class} flex items-center gap-1 w-fit`}>
        <Icon className="w-3 h-3" /> {badge.text}
      </span>
    );
  };

  if (loading) {
    return (
      <EmployeeLayout>
        <div className="text-center py-12">Loading...</div>
      </EmployeeLayout>
    );
  }

  return (
    <EmployeeLayout>
      <div data-testid="leave-management-page">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Leave Management</h1>
            <p className="text-slate-600">Request and track your leave</p>
          </div>
          <Button
            onClick={() => setShowRequestModal(true)}
            data-testid="request-leave-button"
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Request Leave
          </Button>
        </div>

        {/* Leave Balance Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Annual Leave</h3>
              <Calendar className="w-8 h-8 text-blue-900" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-blue-900">
                {balance?.available?.annual || 0}
              </span>
              <span className="text-slate-600">/ {balance?.balance?.annual || 21} days</span>
            </div>
            <p className="text-sm text-slate-500 mt-2">Used: {balance?.used?.annual || 0} days</p>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Sick Leave</h3>
              <AlertCircle className="w-8 h-8 text-orange-600" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-orange-600">
                {(balance?.balance?.sick || 30) - (balance?.used?.sick || 0)}
              </span>
              <span className="text-slate-600">/ {balance?.balance?.sick || 30} days</span>
            </div>
            <p className="text-sm text-slate-500 mt-2">Used: {balance?.used?.sick || 0} days</p>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Public Holidays</h3>
              <Calendar className="w-8 h-8 text-emerald-600" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-emerald-600">{holidays.length}</span>
              <span className="text-slate-600">in 2025</span>
            </div>
            <p className="text-sm text-slate-500 mt-2">Kenya public holidays</p>
          </div>
        </div>

        {/* Leave Requests History */}
        <div className="card overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-xl font-semibold text-slate-900">My Leave Requests</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full grid-border" data-testid="leave-requests-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Type</th>
                  <th className="px-6 py-4 text-left label">Start Date</th>
                  <th className="px-6 py-4 text-left label">End Date</th>
                  <th className="px-6 py-4 text-left label">Days</th>
                  <th className="px-6 py-4 text-left label">Status</th>
                  <th className="px-6 py-4 text-left label">Current Level</th>
                </tr>
              </thead>
              <tbody>
                {requests.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-slate-500">
                      No leave requests yet
                    </td>
                  </tr>
                ) : (
                  requests.map((request) => (
                    <tr key={request.leave_id} className="hover:bg-slate-50" data-testid={`leave-request-${request.leave_id}`}>
                      <td className="px-6 py-4">
                        <span className="badge badge-info">{request.leave_type}</span>
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {new Date(request.start_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {new Date(request.end_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 font-semibold">{request.days_requested}</td>
                      <td className="px-6 py-4">{getStatusBadge(request.status)}</td>
                      <td className="px-6 py-4 text-sm capitalize">
                        {request.status === 'pending' ? request.current_approval_level.replace('_', ' ') : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Request Leave Modal */}
        <Dialog open={showRequestModal} onOpenChange={setShowRequestModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Request Leave</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="leave-request-form">
              <div>
                <label className="label">Leave Type</label>
                <select
                  data-testid="leave-type-select"
                  className="input-field"
                  value={formData.leave_type}
                  onChange={(e) => setFormData({ ...formData, leave_type: e.target.value })}
                  required
                >
                  <option value="Annual">Annual Leave</option>
                  <option value="Sick">Sick Leave</option>
                  <option value="Maternity">Maternity Leave (90 days)</option>
                  <option value="Paternity">Paternity Leave (14 days)</option>
                  <option value="Compassionate">Compassionate Leave</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Start Date</label>
                  <input
                    type="date"
                    data-testid="start-date-input"
                    className="input-field"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    required
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
                <div>
                  <label className="label">End Date</label>
                  <input
                    type="date"
                    data-testid="end-date-input"
                    className="input-field"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    required
                    min={formData.start_date || new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>

              <div>
                <label className="label">Reason</label>
                <textarea
                  data-testid="reason-textarea"
                  className="input-field"
                  rows="3"
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  required
                  placeholder="Please provide a reason for your leave request..."
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-sm p-3">
                <p className="text-sm text-blue-900">
                  <strong>Note:</strong> Working days calculation excludes weekends and {holidays.length} Kenyan public holidays.
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="submit" className="btn-primary flex-1" data-testid="submit-leave-request">
                  Submit Request
                </Button>
                <Button
                  type="button"
                  onClick={() => setShowRequestModal(false)}
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

export default LeaveManagement;
