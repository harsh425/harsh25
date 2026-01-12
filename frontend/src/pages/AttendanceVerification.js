import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { Users, Clock, MapPin, CheckCircle, XCircle, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AttendanceVerification = () => {
  const [teamAttendance, setTeamAttendance] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedAttendance, setSelectedAttendance] = useState(null);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verificationComments, setVerificationComments] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTeamAttendance();
  }, [selectedDate]);

  const fetchTeamAttendance = async () => {
    try {
      const response = await axios.get(`${API}/attendance/team-attendance?date=${selectedDate}`);
      setTeamAttendance(response.data);
    } catch (error) {
      toast.error('Failed to load team attendance');
    } finally {
      setLoading(false);
    }
  };

  const openVerifyModal = (attendance) => {
    setSelectedAttendance(attendance);
    setShowVerifyModal(true);
  };

  const handleVerify = async (status) => {
    try {
      await axios.post(`${API}/attendance/${selectedAttendance.attendance_id}/verify`, {
        status,
        comments: verificationComments
      });
      toast.success(`Attendance ${status}`);
      setShowVerifyModal(false);
      setVerificationComments('');
      setSelectedAttendance(null);
      fetchTeamAttendance();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to verify attendance');
    }
  };

  const getStatusBadge = (record) => {
    if (record.within_geofence) {
      return <span className="badge badge-success">Auto-Verified</span>;
    } else if (record.verification_status === 'verified') {
      return <span className="badge badge-success">Verified</span>;
    } else if (record.verification_status === 'flagged') {
      return <span className="badge badge-danger">Flagged</span>;
    } else {
      return <span className="badge badge-warning">Needs Verification</span>;
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
      <div data-testid="attendance-verification-page">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Attendance Verification</h1>
          <p className="text-slate-600">Verify team attendance records</p>
        </div>

        {/* Date Selector */}
        <div className="card p-6 mb-6">
          <div className="flex items-center gap-4">
            <Calendar className="w-5 h-5 text-slate-600" />
            <label className="label mb-0">Select Date:</label>
            <input
              type="date"
              data-testid="date-selector"
              className="input-field max-w-xs"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
            />
            <Button
              onClick={fetchTeamAttendance}
              className="btn-primary"
            >
              Load
            </Button>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="label mb-2">Total Present</p>
                <p className="text-3xl font-bold text-blue-900">{teamAttendance.length}</p>
              </div>
              <Users className="w-10 h-10 text-blue-900" />
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="label mb-2">Late Arrivals</p>
                <p className="text-3xl font-bold text-orange-600">
                  {teamAttendance.filter(a => a.is_late).length}
                </p>
              </div>
              <Clock className="w-10 h-10 text-orange-600" />
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="label mb-2">Outside Geofence</p>
                <p className="text-3xl font-bold text-red-600">
                  {teamAttendance.filter(a => !a.within_geofence).length}
                </p>
              </div>
              <MapPin className="w-10 h-10 text-red-600" />
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="label mb-2">Needs Verification</p>
                <p className="text-3xl font-bold text-yellow-600">
                  {teamAttendance.filter(a => !a.within_geofence && !a.verification_status).length}
                </p>
              </div>
              <AlertCircle className="w-10 h-10 text-yellow-600" />
            </div>
          </div>
        </div>

        {/* Attendance Table */}
        <div className="card overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-xl font-semibold text-slate-900">Team Attendance</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full grid-border" data-testid="team-attendance-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Employee</th>
                  <th className="px-6 py-4 text-left label">Check In</th>
                  <th className="px-6 py-4 text-left label">Check Out</th>
                  <th className="px-6 py-4 text-left label">Hours</th>
                  <th className="px-6 py-4 text-left label">Distance</th>
                  <th className="px-6 py-4 text-left label">Status</th>
                  <th className="px-6 py-4 text-left label">Actions</th>
                </tr>
              </thead>
              <tbody>
                {teamAttendance.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="text-center py-12 text-slate-500">
                      No attendance records for this date
                    </td>
                  </tr>
                ) : (
                  teamAttendance.map((record) => (
                    <tr
                      key={record.attendance_id}
                      className={`hover:bg-slate-50 ${!record.within_geofence && !record.verification_status ? 'bg-yellow-50' : ''}`}
                      data-testid={`attendance-row-${record.attendance_id}`}
                    >
                      <td className="px-6 py-4 font-medium">
                        {record.employee_name}
                        {record.is_late && (
                          <span className="ml-2 badge badge-warning text-xs">Late</span>
                        )}
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {new Date(record.check_in_time).toLocaleTimeString()}
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {record.check_out_time ? new Date(record.check_out_time).toLocaleTimeString() : '-'}
                      </td>
                      <td className="px-6 py-4 font-semibold">
                        {record.total_hours ? `${record.total_hours}h` : '-'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={record.within_geofence ? 'text-emerald-600' : 'text-red-600'}>
                          {record.check_in_distance}m
                        </span>
                      </td>
                      <td className="px-6 py-4">{getStatusBadge(record)}</td>
                      <td className="px-6 py-4">
                        {!record.within_geofence && !record.verification_status ? (
                          <button
                            onClick={() => openVerifyModal(record)}
                            data-testid={`verify-button-${record.attendance_id}`}
                            className="text-blue-900 hover:underline font-medium"
                          >
                            Verify
                          </button>
                        ) : record.verification_status ? (
                          <span className="text-sm text-slate-500">
                            {record.verified_by}
                          </span>
                        ) : (
                          <span className="text-sm text-slate-500">-</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Verification Modal */}
        {selectedAttendance && (
          <Dialog open={showVerifyModal} onOpenChange={setShowVerifyModal}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold">Verify Attendance</DialogTitle>
              </DialogHeader>

              <div className="space-y-4">
                <div className="bg-slate-50 rounded-sm p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="label">Employee</p>
                      <p className="font-semibold">{selectedAttendance.employee_name}</p>
                    </div>
                    <div>
                      <p className="label">Employee Number</p>
                      <p className="mono font-semibold">{selectedAttendance.employee_number}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="label">Check In Time</p>
                      <p className="mono">{new Date(selectedAttendance.check_in_time).toLocaleTimeString()}</p>
                    </div>
                    <div>
                      <p className="label">Distance from Office</p>
                      <p className="text-red-600 font-semibold">{selectedAttendance.check_in_distance}m</p>
                    </div>
                  </div>
                  <div>
                    <p className="label">Location Coordinates</p>
                    <p className="text-sm mono text-slate-600">
                      {selectedAttendance.check_in_latitude.toFixed(6)}, {selectedAttendance.check_in_longitude.toFixed(6)}
                    </p>
                  </div>
                </div>

                <div>
                  <label className="label">Verification Comments</label>
                  <textarea
                    data-testid="verification-comments"
                    className="input-field"
                    rows="3"
                    value={verificationComments}
                    onChange={(e) => setVerificationComments(e.target.value)}
                    placeholder="Add comments about this attendance record..."
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    onClick={() => handleVerify('verified')}
                    data-testid="verify-approve-button"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-sm flex items-center gap-2 flex-1"
                  >
                    <CheckCircle className="w-5 h-5" />
                    Verify & Approve
                  </Button>
                  <Button
                    onClick={() => handleVerify('flagged')}
                    data-testid="verify-flag-button"
                    className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-sm flex items-center gap-2 flex-1"
                  >
                    <XCircle className="w-5 h-5" />
                    Flag as Issue
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

// Missing import
import { AlertCircle } from 'lucide-react';

export default AttendanceVerification;
