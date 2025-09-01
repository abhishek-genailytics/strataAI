import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ToastProvider } from "./contexts/ToastContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { OrganizationProvider } from "./components/OrganizationProvider";
import { ProtectedRoute, PublicRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/layout/Layout";
import {
  Login,
  Register,
  ApiKeys,
  Playground,
  Providers,
  ModelPricing,
  Access,
} from "./pages";
import Monitor from "./pages/Monitor";
import { ForgotPassword, UserProfile } from "./components";
import "./App.css";

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <OrganizationProvider>
            <Router>
              <Routes>
                {/* Public routes */}
                <Route
                  path="/login"
                  element={
                    <PublicRoute>
                      <Login />
                    </PublicRoute>
                  }
                />
                <Route
                  path="/register"
                  element={
                    <PublicRoute>
                      <Register />
                    </PublicRoute>
                  }
                />
                <Route
                  path="/forgot-password"
                  element={
                    <PublicRoute>
                      <ForgotPassword />
                    </PublicRoute>
                  }
                />

                {/* Protected routes */}
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Navigate to="/models" replace />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/models"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ModelPricing />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/playground"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Playground />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/monitor"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Monitor />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/access"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Access />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/api-keys"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ApiKeys />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/providers"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Providers />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <UserProfile />
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                {/* Catch all route */}
                <Route path="*" element={<Navigate to="/models" replace />} />
              </Routes>
            </Router>
          </OrganizationProvider>
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
