import React, { useEffect, useState } from 'react';
import axios from 'axios';
import EmployeeLayout from '@/components/EmployeeLayout';
import { MapPin, Clock, CheckCircle, AlertTriangle, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AttendancePage = () => {
  const [attendance, setAttendance] = useState([]);
  const [todayAttendance, setTodayAttendance] = useState(null);
  const [officeLocation, setOfficeLocation] = useState(null);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [checkingIn, setCheckingIn] = useState(false);
  const [checkingOut, setCheckingOut] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    getLocation();
  }, []);

  const fetchData = async () => {
    try {
      const [attendanceRes, officeRes] = await Promise.all([
        axios.get(`${API}/attendance/my-attendance?days=30`),
        axios.get(`${API}/attendance/office-location`)
      ]);
      setAttendance(attendanceRes.data);
      setOfficeLocation(officeRes.data);
      
      // Find today's attendance
      const today = new Date().toISOString().split('T')[0];
      const todayRecord = attendanceRes.data.find(a => a.date === today);
      setTodayAttendance(todayRecord);
    } catch (error) {
      toast.error('Failed to load attendance data');
    } finally {
      setLoading(false);
    }
  };

  const getLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
        },
        (error) => {
          toast.error('Please enable location services');
        }
      );
    } else {
      toast.error('Geolocation is not supported by your browser');
    }
  };

  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371000; // Earth radius in meters
    const phi1 = lat1 * Math.PI / 180;
    const phi2 = lat2 * Math.PI / 180;
    const deltaPhi = (lat2 - lat1) * Math.PI / 180;
    const deltaLambda = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
              Math.cos(phi1) * Math.cos(phi2) *
              Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return Math.round(R * c);
  };

  const handleCheckIn = async () => {
    if (!currentLocation) {
      toast.error('Location not available. Please enable location services.');
      return;
    }

    setCheckingIn(true);
    try {
      const response = await axios.post(`${API}/attendance/check-in`, {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude
      });
      toast.success(response.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to check in');
    } finally {
      setCheckingIn(false);
    }
  };

  const handleCheckOut = async () => {
    if (!currentLocation) {
      toast.error('Location not available. Please enable location services.');
      return;
    }

    setCheckingOut(true);
    try {
      const response = await axios.post(`${API}/attendance/check-out`, {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude
      });
      toast.success(response.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to check out');
    } finally {
      setCheckingOut(false);
    }
  };

  const distanceToOffice = currentLocation && officeLocation
    ? calculateDistance(
        currentLocation.latitude,
        currentLocation.longitude,
        officeLocation.latitude,
        officeLocation.longitude
      )
    : null;

  const withinGeofence = distanceToOffice !== null && distanceToOffice <= officeLocation?.radius_meters;

  if (loading) {
    return (
      <EmployeeLayout>
        <div className="text-center py-12">Loading...</div>
      </EmployeeLayout>
    );
  }

  return (
    <EmployeeLayout>
      <div data-testid="attendance-page">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Attendance</h1>
          <p className="text-slate-600">Check in and out with geolocation verification</p>
        </div>

        {/* Check In/Out Card */}
        <div className="card p-8 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Location Status */}
            <div>
              <h3 className="text-xl font-semibold mb-4 text-slate-900 flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                Location Status
              </h3>
              <div className="space-y-3">
                {currentLocation ? (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">Distance from Office:</span>
                      <span className={`font-semibold ${withinGeofence ? 'text-emerald-600' : 'text-orange-600'}`}>
                        {distanceToOffice}m
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">Geofence Status:</span>
                      {withinGeofence ? (
                        <span className="badge badge-success flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" /> Within Range
                        </span>
                      ) : (
                        <span className="badge badge-warning flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" /> Outside Range
                        </span>
                      )}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">GPS Accuracy:</span>
                      <span className="text-sm text-slate-500">±{Math.round(currentLocation.accuracy)}m</span>
                    </div>
                  </>
                ) : (
                  <div className="text-slate-500">Getting your location...</div>
                )}
              </div>
            </div>

            {/* Check In/Out Actions */}
            <div>
              <h3 className="text-xl font-semibold mb-4 text-slate-900 flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Today's Attendance
              </h3>
              {todayAttendance ? (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-sm p-4">
                    <p className="text-sm text-blue-900 mb-2">
                      <strong>Checked In:</strong> {new Date(todayAttendance.check_in_time).toLocaleTimeString()}
                    </p>
                    {todayAttendance.is_late && (
                      <span className="badge badge-warning">Late</span>
                    )}
                  </div>
                  {todayAttendance.check_out_time ? (
                    <div className="bg-emerald-50 border border-emerald-200 rounded-sm p-4">
                      <p className="text-sm text-emerald-900 mb-2">
                        <strong>Checked Out:</strong> {new Date(todayAttendance.check_out_time).toLocaleTimeString()}
                      </p>
                      <p className="text-sm text-emerald-700">
                        Total Hours: <strong>{todayAttendance.total_hours}h</strong>
                      </p>
                    </div>
                  ) : (
                    <Button
                      onClick={handleCheckOut}
                      disabled={checkingOut || !currentLocation}
                      data-testid="check-out-button"
                      className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-sm w-full"
                    >
                      {checkingOut ? 'Checking Out...' : 'Check Out'}
                    </Button>
                  )}
                </div>
              ) : (
                <Button
                  onClick={handleCheckIn}
                  disabled={checkingIn || !currentLocation}
                  data-testid="check-in-button"
                  className="btn-primary px-6 py-3 w-full"
                >
                  {checkingIn ? 'Checking In...' : 'Check In'}
                </Button>
              )}
            </div>
          </div>

          {!withinGeofence && currentLocation && (
            <div className="mt-6 bg-orange-50 border border-orange-200 rounded-sm p-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-orange-900">Outside Office Geofence</p>
                  <p className="text-sm text-orange-700 mt-1">
                    You are currently {distanceToOffice}m from the office. Check-ins outside the {officeLocation?.radius_meters}m radius require manager verification.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Attendance History */}
        <div className="card overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Last 30 Days
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full grid-border" data-testid="attendance-history-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Date</th>
                  <th className="px-6 py-4 text-left label">Check In</th>
                  <th className="px-6 py-4 text-left label">Check Out</th>
                  <th className="px-6 py-4 text-left label">Hours</th>
                  <th className="px-6 py-4 text-left label">Status</th>
                </tr>
              </thead>
              <tbody>
                {attendance.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center py-12 text-slate-500">
                      No attendance records yet
                    </td>
                  </tr>
                ) : (
                  attendance.map((record) => (
                    <tr key={record.attendance_id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 mono font-semibold">
                        {new Date(record.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {new Date(record.check_in_time).toLocaleTimeString()}
                        {record.is_late && <span className="ml-2 badge badge-warning text-xs">Late</span>}
                      </td>
                      <td className="px-6 py-4 mono text-sm">
                        {record.check_out_time ? new Date(record.check_out_time).toLocaleTimeString() : '-'}
                      </td>
                      <td className="px-6 py-4 font-semibold">
                        {record.total_hours ? `${record.total_hours}h` : '-'}
                      </td>
                      <td className="px-6 py-4">
                        {record.within_geofence ? (
                          <span className="badge badge-success">Verified</span>
                        ) : record.verification_status === 'verified' ? (
                          <span className="badge badge-success">Manager Verified</span>
                        ) : record.verification_status === 'flagged' ? (
                          <span className="badge badge-danger">Flagged</span>
                        ) : (
                          <span className="badge badge-warning">Pending Verification</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </EmployeeLayout>
  );
};

export default AttendancePage;
