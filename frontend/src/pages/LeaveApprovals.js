import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { Clock, CheckCircle, XCircle, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LeaveApprovals = () => {
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [teamCalendar, setTeamCalendar] = useState([]);
  const [selectedLeave, setSelectedLeave] = useState(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [approvalComments, setApprovalComments] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [pendingRes, calendarRes] = await Promise.all([
        axios.get(`${API}/leave/pending-approvals`),
        axios.get(`${API}/leave/team-calendar`)
      ]);
      setPendingLeaves(pendingRes.data);
      setTeamCalendar(calendarRes.data);
    } catch (error) {
      toast.error('Failed to load leave approvals');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (leaveId) => {
    try {
      await axios.post(`${API}/leave/${leaveId}/approve`, {
        status: 'approved',
        comments: approvalComments
      });
      toast.success('Leave request approved');
      setShowApprovalModal(false);
      setApprovalComments('');
      setSelectedLeave(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve leave');
    }
  };

  const handleReject = async (leaveId) => {
    if (!approvalComments.trim()) {
      toast.error('Please provide a reason for rejection');
      return;
    }
    try {
      await axios.post(`${API}/leave/${leaveId}/approve`, {
        status: 'rejected',
        comments: approvalComments
      });
      toast.success('Leave request rejected');
      setShowApprovalModal(false);
      setApprovalComments('');
      setSelectedLeave(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject leave');
    }
  };

  const openApprovalModal = (leave) => {
    setSelectedLeave(leave);
    setShowApprovalModal(true);
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
      <div data-testid="leave-approvals-page">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Leave Approvals</h1>
          <p className="text-slate-600">Review and approve leave requests</p>
        </div>

        {/* Pending Approvals */}
        <div className="card overflow-hidden mb-8">
          <div className="p-6 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-xl font-semibold text-slate-900">Pending Approvals</h3>
            <span className="badge badge-warning flex items-center gap-1">
              <Clock className="w-4 h-4" /> {pendingLeaves.length} Pending
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full grid-border" data-testid="pending-approvals-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Employee</th>
                  <th className="px-6 py-4 text-left label">Type</th>
                  <th className="px-6 py-4 text-left label">Dates</th>
                  <th className="px-6 py-4 text-left label">Days</th>
                  <th className="px-6 py-4 text-left label">Reason</th>
                  <th className="px-6 py-4 text-left label">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingLeaves.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-slate-500">
                      No pending approvals
                    </td>
                  </tr>
                ) : (
                  pendingLeaves.map((leave) => (
                    <tr key={leave.leave_id} className="hover:bg-slate-50" data-testid={`pending-leave-${leave.leave_id}`}>
                      <td className="px-6 py-4 font-medium">{leave.employee_name}</td>
                      <td className="px-6 py-4">
                        <span className="badge badge-info">{leave.leave_type}</span>
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 font-semibold">{leave.days_requested}</td>
                      <td className="px-6 py-4 text-sm text-slate-600 max-w-xs truncate">
                        {leave.reason}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => openApprovalModal(leave)}
                          data-testid={`review-leave-${leave.leave_id}`}
                          className="text-blue-900 hover:underline font-medium"
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Team Leave Calendar */}
        <div className="card overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Upcoming Team Leave
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full grid-border" data-testid="team-calendar-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Employee</th>
                  <th className="px-6 py-4 text-left label">Type</th>
                  <th className="px-6 py-4 text-left label">Start Date</th>
                  <th className="px-6 py-4 text-left label">End Date</th>
                  <th className="px-6 py-4 text-left label">Days</th>
                </tr>
              </thead>
              <tbody>
                {teamCalendar.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center py-12 text-slate-500">
                      No upcoming leave
                    </td>
                  </tr>
                ) : (
                  teamCalendar.map((leave, index) => (
                    <tr key={index} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium">{leave.employee_name}</td>
                      <td className="px-6 py-4">
                        <span className="badge badge-success">{leave.leave_type}</span>
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {new Date(leave.start_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {new Date(leave.end_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 font-semibold">{leave.days_requested}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Approval Modal */}
        {selectedLeave && (
          <Dialog open={showApprovalModal} onOpenChange={setShowApprovalModal}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold">Review Leave Request</DialogTitle>
              </DialogHeader>

              <div className="space-y-4">
                <div className="bg-slate-50 rounded-sm p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="label">Employee</p>
                      <p className="font-semibold">{selectedLeave.employee_name}</p>
                    </div>
                    <div>
                      <p className="label">Employee Number</p>
                      <p className="mono font-semibold">{selectedLeave.employee_number}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="label">Leave Type</p>
                      <span className="badge badge-info inline-block">{selectedLeave.leave_type}</span>
                    </div>
                    <div>
                      <p className="label">Days Requested</p>
                      <p className="text-2xl font-bold text-blue-900">{selectedLeave.days_requested}</p>
                    </div>
                  </div>
                  <div>
                    <p className="label">Period</p>
                    <p className="mono">
                      {new Date(selectedLeave.start_date).toLocaleDateString()} - {new Date(selectedLeave.end_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="label">Reason</p>
                    <p className="text-slate-700">{selectedLeave.reason}</p>
                  </div>
                </div>

                {selectedLeave.approval_history && selectedLeave.approval_history.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-2">Approval History</h4>
                    <div className="space-y-2">
                      {selectedLeave.approval_history.map((approval, index) => (
                        <div key={index} className="flex items-center gap-3 text-sm">
                          {approval.status === 'approved' ? (
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-600" />
                          )}
                          <span className="font-medium capitalize">{approval.level.replace('_', ' ')}</span>
                          <span className="text-slate-600">by {approval.approver_name}</span>
                          {approval.comments && <span className="text-slate-500">- {approval.comments}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="label">Comments (Optional for approval, Required for rejection)</label>
                  <textarea
                    data-testid="approval-comments-textarea"
                    className="input-field"
                    rows="3"
                    value={approvalComments}
                    onChange={(e) => setApprovalComments(e.target.value)}
                    placeholder="Add your comments here..."
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    onClick={() => handleApprove(selectedLeave.leave_id)}
                    data-testid="approve-leave-button"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-sm flex items-center gap-2 flex-1"
                  >
                    <CheckCircle className="w-5 h-5" />
                    Approve
                  </Button>
                  <Button
                    onClick={() => handleReject(selectedLeave.leave_id)}
                    data-testid="reject-leave-button"
                    className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-sm flex items-center gap-2 flex-1"
                  >
                    <XCircle className="w-5 h-5" />
                    Reject
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </AdminLayout>
  );
};

export default LeaveApprovals;
