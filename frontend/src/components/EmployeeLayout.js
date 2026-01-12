import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Home, FileText, LogOut, Calendar } from 'lucide-react';

const EmployeeLayout = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Navbar */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50 glassmorphism">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Nexus HR</h2>
              <p className="text-sm text-slate-600">Employee Portal</p>
            </div>

            <div className="flex items-center gap-6">
              <NavLink
                to="/employee-dashboard"
                data-testid="nav-employee-dashboard"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-sm transition ${isActive ? 'bg-blue-900 text-white' : 'text-slate-700 hover:bg-slate-100'}`
                }
              >
                <Home className="w-4 h-4" />
                Dashboard
              </NavLink>
              <NavLink
                to="/my-documents"
                data-testid="nav-my-documents"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-sm transition ${isActive ? 'bg-blue-900 text-white' : 'text-slate-700 hover:bg-slate-100'}`
                }
              >
                <FileText className="w-4 h-4" />
                My Documents
              </NavLink>
              <NavLink
                to="/my-leave"
                data-testid="nav-my-leave"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-sm transition ${isActive ? 'bg-blue-900 text-white' : 'text-slate-700 hover:bg-slate-100'}`
                }
              >
                <Calendar className="w-4 h-4" />
                My Leave
              </NavLink>

              <div className="flex items-center gap-3 ml-6 pl-6 border-l border-slate-200">
                <span className="text-sm text-slate-600">{user?.full_name}</span>
                <button
                  data-testid="employee-logout-button"
                  onClick={logout}
                  className="flex items-center gap-2 px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-sm transition"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-8">
        {children}
      </div>
    </div>
  );
};

export default EmployeeLayout;
