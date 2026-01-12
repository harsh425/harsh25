import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { BarChart3, Users, Calendar, MapPin, TrendingUp, Download } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ReportsDashboard = () => {
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [employeeStats, setEmployeeStats] = useState(null);
  const [leaveStats, setLeaveStats] = useState(null);
  const [attendanceStats, setAttendanceStats] = useState(null);
  const [performanceStats, setPerformanceStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompanies();
  }, []);

  useEffect(() => {
    if (companies.length > 0) {
      fetchAllReports();
    }
  }, [selectedCompany]);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API}/companies`);
      setCompanies(response.data);
    } catch (error) {
      console.error('Failed to load companies');
    }
  };

  const fetchAllReports = async () => {
    setLoading(true);
    try {
      const companyParam = selectedCompany ? `?company_id=${selectedCompany}` : '';
      
      const [empRes, leaveRes, attRes, perfRes] = await Promise.all([
        axios.get(`${API}/reports/company-summary${companyParam}`),
        axios.get(`${API}/reports/leave-summary${companyParam}`),
        axios.get(`${API}/reports/attendance-summary${companyParam}`),
        axios.get(`${API}/reports/performance-summary${companyParam}`)
      ]);

      setEmployeeStats(empRes.data);
      setLeaveStats(leaveRes.data);
      setAttendanceStats(attRes.data);
      setPerformanceStats(perfRes.data);
    } catch (error) {
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const selectedCompanyName = companies.find(c => c.company_id === selectedCompany)?.company_name || 'All Companies';

  if (loading && !employeeStats) {
    return (
      <AdminLayout>
        <div className="text-center py-12">Loading reports...</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div data-testid="reports-dashboard">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Reports & Analytics</h1>
            <p className="text-slate-600">Comprehensive HR insights and metrics</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              data-testid="company-filter"
              className="input-field"
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
            >
              <option value="">All Companies</option>
              {companies.map((company) => (
                <option key={company.company_id} value={company.company_id}>
                  {company.company_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-sm p-4">
          <p className="text-blue-900 font-semibold">
            Viewing: <span className="text-blue-700">{selectedCompanyName}</span>
          </p>
        </div>

        {/* Employee Statistics */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Users className="w-6 h-6" />
            Employee Statistics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card p-6">
              <p className="label mb-2">Total Employees</p>
              <p className="text-4xl font-bold text-blue-900">{employeeStats?.total_employees || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Active Employees</p>
              <p className="text-4xl font-bold text-emerald-600">{employeeStats?.active_employees || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Inactive</p>
              <p className="text-4xl font-bold text-slate-600">{employeeStats?.inactive_employees || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Recent Hires (30d)</p>
              <p className="text-4xl font-bold text-orange-600">{employeeStats?.recent_hires || 0}</p>
            </div>
          </div>

          {/* Department & Gender Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Department Breakdown</h3>
              <div className="space-y-3">
                {employeeStats?.department_breakdown?.map((dept, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-slate-700">{dept._id || 'Unassigned'}</span>
                    <span className="badge badge-info">{dept.count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Gender Distribution</h3>
              <div className="space-y-3">
                {employeeStats?.gender_breakdown?.map((gender, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-slate-700">{gender._id}</span>
                    <span className="badge badge-success">{gender.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Leave Statistics */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Calendar className="w-6 h-6" />
            Leave Management
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card p-6">
              <p className="label mb-2">Total Requests</p>
              <p className="text-4xl font-bold text-blue-900">{leaveStats?.total_requests || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Pending</p>
              <p className="text-4xl font-bold text-yellow-600">{leaveStats?.pending || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Approved</p>
              <p className="text-4xl font-bold text-emerald-600">{leaveStats?.approved || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Rejected</p>
              <p className="text-4xl font-bold text-red-600">{leaveStats?.rejected || 0}</p>
            </div>
          </div>

          <div className="card p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">Leave Type Breakdown</h3>
            <div className="space-y-3">
              {leaveStats?.leave_type_breakdown?.map((type, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-slate-700">{type._id}</span>
                  <div className="flex items-center gap-3">
                    <span className="badge badge-info">{type.count} requests</span>
                    <span className="badge badge-warning">{type.total_days} days</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Attendance Statistics */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <MapPin className="w-6 h-6" />
            Attendance Metrics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card p-6">
              <p className="label mb-2">Total Records</p>
              <p className="text-4xl font-bold text-blue-900">{attendanceStats?.total_records || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Late Arrivals</p>
              <p className="text-4xl font-bold text-orange-600">{attendanceStats?.late_arrivals || 0}</p>
              <p className="text-sm text-slate-500 mt-1">{attendanceStats?.late_percentage || 0}% of total</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Outside Geofence</p>
              <p className="text-4xl font-bold text-red-600">{attendanceStats?.outside_geofence || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Avg Hours/Day</p>
              <p className="text-4xl font-bold text-emerald-600">{attendanceStats?.average_hours || 0}h</p>
            </div>
          </div>
        </div>

        {/* Performance Statistics */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-6 h-6" />
            Performance Insights
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card p-6">
              <p className="label mb-2">Total Reviews</p>
              <p className="text-4xl font-bold text-blue-900">{performanceStats?.total_reviews || 0}</p>
            </div>
            <div className="card p-6">
              <p className="label mb-2">Average Rating</p>
              <p className="text-4xl font-bold text-emerald-600">{performanceStats?.average_rating || 0}/5</p>
            </div>
            <div className="card p-6">
              <h3 className="text-sm font-semibold mb-3 text-slate-700">Rating Distribution</h3>
              <div className="space-y-2">
                {performanceStats?.rating_distribution?.sort((a, b) => b._id - a._id).map((rating, index) => (
                  <div key={index} className="flex justify-between items-center text-sm">
                    <span className="text-slate-600">{rating._id} Stars</span>
                    <span className="badge badge-success">{rating.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default ReportsDashboard;
