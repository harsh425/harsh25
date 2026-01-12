import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { BarChart3, Users, Calendar, Clock, TrendingUp, Building2, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ReportsDashboard = () => {
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('all');
  const [companySummary, setCompanySummary] = useState(null);
  const [leaveSummary, setLeaveSummary] = useState(null);
  const [attendanceSummary, setAttendanceSummary] = useState(null);
  const [performanceSummary, setPerformanceSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompanies();
  }, []);

  useEffect(() => {
    fetchAllReports();
  }, [selectedCompany]);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API}/companies`);
      setCompanies(response.data);
    } catch (error) {
      console.error('Failed to fetch companies');
    }
  };

  const fetchAllReports = async () => {
    setLoading(true);
    try {
      const companyParam = selectedCompany !== 'all' ? `?company_id=${selectedCompany}` : '';
      
      const [companyRes, leaveRes, attendanceRes, performanceRes] = await Promise.all([
        axios.get(`${API}/reports/company-summary${companyParam}`),
        axios.get(`${API}/reports/leave-summary${companyParam}`),
        axios.get(`${API}/reports/attendance-summary${companyParam}`),
        axios.get(`${API}/reports/performance-summary${companyParam}`)
      ]);
      
      setCompanySummary(companyRes.data);
      setLeaveSummary(leaveRes.data);
      setAttendanceSummary(attendanceRes.data);
      setPerformanceSummary(performanceRes.data);
    } catch (error) {
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const renderRatingStars = (rating) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} className={i <= rating ? 'text-yellow-500' : 'text-slate-300'}>
          ★
        </span>
      );
    }
    return stars;
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="text-center py-12">Loading reports...</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div data-testid="reports-dashboard">
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Reports & Analytics</h1>
            <p className="text-slate-600">Comprehensive workforce analytics and insights</p>
          </div>
          
          <div className="w-64">
            <label className="label">Filter by Company</label>
            <Select value={selectedCompany} onValueChange={setSelectedCompany}>
              <SelectTrigger data-testid="company-filter-select">
                <SelectValue placeholder="Select company" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Companies</SelectItem>
                {companies.map((company) => (
                  <SelectItem key={company.company_id} value={company.company_id}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Employee Statistics */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-900" />
            Workforce Summary
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card p-6" data-testid="stat-total-employees">
              <p className="label mb-2">Total Employees</p>
              <p className="text-3xl font-bold text-slate-900">{companySummary?.total_employees || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-active-employees">
              <p className="label mb-2">Active</p>
              <p className="text-3xl font-bold text-emerald-600">{companySummary?.active_employees || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-inactive-employees">
              <p className="label mb-2">Inactive</p>
              <p className="text-3xl font-bold text-slate-500">{companySummary?.inactive_employees || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-recent-hires">
              <p className="label mb-2">Recent Hires (30 days)</p>
              <p className="text-3xl font-bold text-blue-900">{companySummary?.recent_hires || 0}</p>
            </div>
          </div>
        </div>

        {/* Department & Gender Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="card p-6" data-testid="department-breakdown">
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Building2 className="w-5 h-5" />
              Department Breakdown
            </h3>
            <div className="space-y-3">
              {companySummary?.department_breakdown?.length > 0 ? (
                companySummary.department_breakdown.map((dept, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-slate-700">{dept._id || 'Unassigned'}</span>
                    <span className="badge badge-info">{dept.count}</span>
                  </div>
                ))
              ) : (
                <p className="text-slate-500">No department data available</p>
              )}
            </div>
          </div>
          
          <div className="card p-6" data-testid="gender-breakdown">
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5" />
              Gender Distribution
            </h3>
            <div className="space-y-3">
              {companySummary?.gender_breakdown?.length > 0 ? (
                companySummary.gender_breakdown.map((gender, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-slate-700 capitalize">{gender._id || 'Not Specified'}</span>
                    <span className="badge badge-info">{gender.count}</span>
                  </div>
                ))
              ) : (
                <p className="text-slate-500">No gender data available</p>
              )}
            </div>
          </div>
        </div>

        {/* Leave Summary */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-orange-600" />
            Leave Analytics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-4">
            <div className="card p-6" data-testid="stat-total-leave-requests">
              <p className="label mb-2">Total Requests</p>
              <p className="text-3xl font-bold text-slate-900">{leaveSummary?.total_requests || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-pending-leaves">
              <p className="label mb-2">Pending</p>
              <p className="text-3xl font-bold text-orange-600">{leaveSummary?.pending || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-approved-leaves">
              <p className="label mb-2">Approved</p>
              <p className="text-3xl font-bold text-emerald-600">{leaveSummary?.approved || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-rejected-leaves">
              <p className="label mb-2">Rejected</p>
              <p className="text-3xl font-bold text-red-600">{leaveSummary?.rejected || 0}</p>
            </div>
          </div>
          
          <div className="card p-6" data-testid="leave-type-breakdown">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Leave Type Breakdown</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">Leave Type</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">Requests</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">Total Days</th>
                  </tr>
                </thead>
                <tbody>
                  {leaveSummary?.leave_type_breakdown?.length > 0 ? (
                    leaveSummary.leave_type_breakdown.map((type, index) => (
                      <tr key={index} className="border-t">
                        <td className="px-4 py-3">
                          <span className="badge badge-info">{type._id}</span>
                        </td>
                        <td className="px-4 py-3 font-semibold">{type.count}</td>
                        <td className="px-4 py-3 mono">{type.total_days}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="3" className="text-center py-4 text-slate-500">No leave data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Attendance Summary */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-purple-600" />
            Attendance Analytics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card p-6" data-testid="stat-total-attendance">
              <p className="label mb-2">Total Records</p>
              <p className="text-3xl font-bold text-slate-900">{attendanceSummary?.total_records || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-late-arrivals">
              <p className="label mb-2">Late Arrivals</p>
              <p className="text-3xl font-bold text-orange-600">{attendanceSummary?.late_arrivals || 0}</p>
              <p className="text-sm text-slate-500 mt-1">{attendanceSummary?.late_percentage || 0}% of total</p>
            </div>
            <div className="card p-6" data-testid="stat-outside-geofence">
              <p className="label mb-2">Outside Geofence</p>
              <p className="text-3xl font-bold text-red-600">{attendanceSummary?.outside_geofence || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-avg-hours">
              <p className="label mb-2">Avg. Working Hours</p>
              <p className="text-3xl font-bold text-blue-900">{attendanceSummary?.average_hours || 0}</p>
              <p className="text-sm text-slate-500 mt-1">hours per day</p>
            </div>
          </div>
        </div>

        {/* Performance Summary */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
            Performance Analytics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card p-6" data-testid="stat-total-reviews">
              <p className="label mb-2">Total Reviews</p>
              <p className="text-3xl font-bold text-slate-900">{performanceSummary?.total_reviews || 0}</p>
            </div>
            <div className="card p-6" data-testid="stat-avg-rating">
              <p className="label mb-2">Average Rating</p>
              <div className="flex items-center gap-2">
                <p className="text-3xl font-bold text-yellow-600">{performanceSummary?.average_rating || 0}</p>
                <div className="text-xl">{renderRatingStars(Math.round(performanceSummary?.average_rating || 0))}</div>
              </div>
            </div>
            <div className="card p-6" data-testid="rating-distribution">
              <p className="label mb-3">Rating Distribution</p>
              <div className="space-y-2">
                {[5, 4, 3, 2, 1].map((rating) => {
                  const count = performanceSummary?.rating_distribution?.find(r => r._id === rating)?.count || 0;
                  const total = performanceSummary?.total_reviews || 1;
                  const percentage = (count / total * 100).toFixed(0);
                  return (
                    <div key={rating} className="flex items-center gap-2">
                      <span className="w-8 text-sm font-medium">{rating}★</span>
                      <div className="flex-1 bg-slate-200 rounded-full h-2">
                        <div 
                          className="bg-yellow-500 h-2 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="w-10 text-sm text-slate-600">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default ReportsDashboard;
