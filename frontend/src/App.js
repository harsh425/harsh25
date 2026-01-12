import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import '@/App.css';

// Pages
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import ForgotPassword from '@/pages/ForgotPassword';
import ResetPassword from '@/pages/ResetPassword';
import AdminDashboard from '@/pages/AdminDashboard';
import EmployeeDashboard from '@/pages/EmployeeDashboard';
import EmployeeList from '@/pages/EmployeeList';
import EmployeeDetails from '@/pages/EmployeeDetails';
import DocumentManagement from '@/pages/DocumentManagement';
import ContractManagement from '@/pages/ContractManagement';
import SignContract from '@/pages/SignContract';
import ActivityLogs from '@/pages/ActivityLogs';

// Auth context
import { AuthProvider, useAuth } from '@/context/AuthContext';

const PrivateRoute = ({ children, adminOnly = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && user.role !== 'admin') {
    return <Navigate to="/employee-dashboard" />;
  }

  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password/:token" element={<ResetPassword />} />
          <Route path="/sign-contract/:token" element={<SignContract />} />
          
          {/* Admin Routes */}
          <Route path="/admin-dashboard" element={
            <PrivateRoute adminOnly>
              <AdminDashboard />
            </PrivateRoute>
          } />
          <Route path="/employees" element={
            <PrivateRoute adminOnly>
              <EmployeeList />
            </PrivateRoute>
          } />
          <Route path="/employees/:employeeId" element={
            <PrivateRoute adminOnly>
              <EmployeeDetails />
            </PrivateRoute>
          } />
          <Route path="/contracts" element={
            <PrivateRoute adminOnly>
              <ContractManagement />
            </PrivateRoute>
          } />
          <Route path="/activity-logs" element={
            <PrivateRoute adminOnly>
              <ActivityLogs />
            </PrivateRoute>
          } />
          
          {/* Employee Routes */}
          <Route path="/employee-dashboard" element={
            <PrivateRoute>
              <EmployeeDashboard />
            </PrivateRoute>
          } />
          <Route path="/my-documents" element={
            <PrivateRoute>
              <DocumentManagement />
            </PrivateRoute>
          } />
          
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
        <Toaster position="top-right" />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
