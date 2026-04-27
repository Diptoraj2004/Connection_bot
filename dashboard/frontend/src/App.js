// App.js
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute/ProtectedRoute';
import RegisterForm from './components/RegisterForm/RegisterForm';
import LoginForm from './components/LoginForm/LoginForm';
import RoleSelection from './components/RoleSelection/RoleSelection';
import StudentDashboard from './components/StudentDashboard/StudentDashboard';
import AdminDashboard from './components/AdminDashboard/AdminDashboard';
import HeatmapPage from './components/AdminDashboard/HeatmapPage';
import CounselorDashboard from './components/CounsellorDashboard/CounsellorDashboard';
import BookingTherapySessionsPage from './components/StudentDashboard/BookingTherapySessionsPage';

const DashboardRouter = () => {
  const { user } = useAuth();
  switch (user.role) {
    case 'student': return <Navigate to="/student" replace />;
    case 'counselor': return <Navigate to="/counselor" replace />;
    case 'admin': return <Navigate to="/admin" replace />;
    default: return <Navigate to="/login" replace />;
  }
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RoleSelection />} />
          <Route path="/register/:role" element={<RegisterForm />} />
          <Route path="/login" element={<LoginForm />} />

          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardRouter />
            </ProtectedRoute>
          } />

          <Route path="/book-therapy" element={
            <ProtectedRoute allowedRoles={['student']}>
              <BookingTherapySessionsPage />
            </ProtectedRoute>
          } />

          <Route path="/student" element={
            <ProtectedRoute allowedRoles={['student']}>
              <StudentDashboard />
            </ProtectedRoute>
          } />

          <Route path="/admin" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          } />

          {/* NEW HEATMAP PAGE ROUTE */}
          <Route path="/admin/heatmap" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <HeatmapPage />
            </ProtectedRoute>
          } />

          <Route path="/counselor" element={
            <ProtectedRoute allowedRoles={['counselor']}>
              <CounselorDashboard />
            </ProtectedRoute>
          } />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
