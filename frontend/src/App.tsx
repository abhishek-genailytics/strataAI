import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Layout from '@/components/layout/Layout'
import { AuthProvider } from '@/contexts/AuthContext'
import { OrganizationProvider } from '@/contexts/OrganizationContext'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import Login from '@/pages/Login'
import SignUp from '@/pages/SignUp'

const Models = lazy(() => import('@/pages/Models'))
const ProviderManage = lazy(() => import('@/pages/models/ProviderManage'))
const Playground = lazy(() => import('@/pages/Playground'))
const Access = lazy(() => import('@/pages/Access'))
const Monitor = lazy(() => import('@/pages/Monitor'))

const qc = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <OrganizationProvider>
          <Suspense fallback={<div className="p-6">Loading…</div>}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<SignUp />} />
              <Route path="/" element={<Navigate to="/models" replace />} />
              <Route path="/models" element={<Layout><ProtectedRoute><Models /></ProtectedRoute></Layout>} />
              <Route path="/models/:providerId" element={<Layout><ProtectedRoute><ProviderManage /></ProtectedRoute></Layout>} />
              <Route path="/playground" element={<Layout><ProtectedRoute><Playground /></ProtectedRoute></Layout>} />
              <Route path="/access" element={<Layout><ProtectedRoute><Access /></ProtectedRoute></Layout>} />
              <Route path="/monitor" element={<Layout><ProtectedRoute><Monitor /></ProtectedRoute></Layout>} />
            </Routes>
          </Suspense>
          <Toaster />
        </OrganizationProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
