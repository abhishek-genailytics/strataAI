import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { OrganizationProvider } from './components/OrganizationProvider';
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute';
import { Layout } from './components/layout/Layout';
import { Dashboard, Login, Register, ApiKeys, Playground, SSOCallback } from './pages';
import { ForgotPassword, UserProfile } from './components';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <OrganizationProvider>
            <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              } />
              <Route path="/register" element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              } />
              <Route path="/forgot-password" element={
                <PublicRoute>
                  <ForgotPassword />
                </PublicRoute>
              } />
              
              {/* SSO Callback route - public but handles auth */}
              <Route path="/auth/callback" element={<SSOCallback />} />

              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/analytics" element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/api-keys" element={
                <ProtectedRoute>
                  <Layout>
                    <ApiKeys />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/playground" element={
                <ProtectedRoute>
                  <Layout>
                    <Playground />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute>
                  <Layout>
                    <UserProfile />
                  </Layout>
                </ProtectedRoute>
              } />

              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            </Router>
          </OrganizationProvider>
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
