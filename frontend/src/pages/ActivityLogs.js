import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { Activity, Clock } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ActivityLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/activity-logs?limit=100`);
      setLogs(response.data);
    } catch (error) {
      toast.error('Failed to load activity logs');
    } finally {
      setLoading(false);
    }
  };

  const formatAction = (action) => {
    return action.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  return (
    <AdminLayout>
      <div data-testid="activity-logs-page">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Activity Logs</h1>
          <p className="text-slate-600">Track all system activities and changes</p>
        </div>

        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full grid-border" data-testid="activity-logs-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left label">Timestamp</th>
                  <th className="px-6 py-4 text-left label">Action</th>
                  <th className="px-6 py-4 text-left label">Details</th>
                  <th className="px-6 py-4 text-left label">User ID</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="4" className="text-center py-12 text-slate-500">Loading...</td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="text-center py-12 text-slate-500">No activity logs found</td>
                  </tr>
                ) : (
                  logs.map((log, index) => (
                    <tr key={log.activity_id || index} className="hover:bg-slate-50 transition" data-testid={`log-row-${index}`}>
                      <td className="px-6 py-4 mono text-sm">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-slate-400" />
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="badge badge-info flex items-center gap-1 w-fit">
                          <Activity className="w-3 h-3" />
                          {formatAction(log.action)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-600">{log.details}</td>
                      <td className="px-6 py-4 mono text-sm text-slate-500">
                        {log.user_id.substring(0, 8)}...
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default ActivityLogs;
