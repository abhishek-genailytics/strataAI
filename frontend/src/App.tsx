import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { OrganizationProvider } from '@/contexts/OrganizationContext'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import Login from '@/pages/Login'
import SignUp from '@/pages/SignUp'
import ErrorBoundary from '@/components/layout/ErrorBoundary'
import GlobalErrorPortal from '@/components/layout/GlobalErrorPortal'
import { Toaster } from '@/components/ui/toaster'

const Models = lazy(() => import('@/pages/Models'))
const Playground = lazy(() => import('@/pages/Playground'))
const Access = lazy(() => import('@/pages/Access'))
const Monitor = lazy(() => import('@/pages/Monitor'))
const ProviderManage = lazy(() => import('@/pages/models/ProviderManage'))

const qc = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <OrganizationProvider>
          <ErrorBoundary>
            <div className="min-h-screen">
              <Suspense fallback={<div className="p-6 text-center">Loading application...</div>}>
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route path="/signup" element={<SignUp />} />
                  <Route path="/" element={<Navigate to="/models" replace />} />
                  <Route path="/models" element={<ProtectedRoute><Models /></ProtectedRoute>} />
                  <Route path="/models/:providerId" element={<ProtectedRoute><ProviderManage /></ProtectedRoute>} />
                  <Route path="/playground" element={<ProtectedRoute><Playground /></ProtectedRoute>} />
                  <Route path="/access" element={<ProtectedRoute><Access /></ProtectedRoute>} />
                  <Route path="/monitor" element={<ProtectedRoute><Monitor /></ProtectedRoute>} />
                </Routes>
              </Suspense>
              <GlobalErrorPortal />
              <Toaster />
            </div>
          </ErrorBoundary>
        </OrganizationProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
