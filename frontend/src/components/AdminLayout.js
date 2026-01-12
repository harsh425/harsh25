import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { LayoutDashboard, Users, FileText, Activity, LogOut } from 'lucide-react';

const AdminLayout = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <div className="sidebar w-64 flex-shrink-0">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-white">Nexus HR</h2>
          <p className="text-slate-400 text-sm">Admin Portal</p>
        </div>

        <nav className="space-y-2">
          <NavLink
            to="/admin-dashboard"
            data-testid="nav-dashboard"
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <LayoutDashboard className="w-5 h-5 mr-3" />
            Dashboard
          </NavLink>
          <NavLink
            to="/employees"
            data-testid="nav-employees"
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <Users className="w-5 h-5 mr-3" />
            Employees
          </NavLink>
          <NavLink
            to="/contracts"
            data-testid="nav-contracts"
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <FileText className="w-5 h-5 mr-3" />
            Contracts
          </NavLink>
          <NavLink
            to="/activity-logs"
            data-testid="nav-activity-logs"
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <Activity className="w-5 h-5 mr-3" />
            Activity Logs
          </NavLink>
        </nav>

        <div className="mt-auto pt-8">
          <div className="text-slate-400 text-sm mb-2">
            {user?.full_name}
          </div>
          <button
            data-testid="logout-button"
            onClick={logout}
            className="sidebar-link w-full text-left"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8 bg-slate-50">
        {children}
      </div>
    </div>
  );
};

export default AdminLayout;
