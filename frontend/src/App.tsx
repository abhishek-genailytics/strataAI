import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from '@/components/layout/Layout'
import { AuthProvider } from '@/contexts/AuthContext'
import { OrganizationProvider } from '@/contexts/OrganizationContext'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const Models = lazy(() => import('@/pages/Models'))
const Playground = lazy(() => import('@/pages/Playground'))
const Access = lazy(() => import('@/pages/Access'))
const Monitor = lazy(() => import('@/pages/Monitor'))

const qc = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <OrganizationProvider>
          <Layout>
            <Suspense fallback={<div className="p-6">Loading…</div>}>
              <Routes>
                <Route path="/" element={<Navigate to="/models" replace />} />
                <Route path="/models" element={<Models />} />
                <Route path="/playground" element={<Playground />} />
                <Route path="/access" element={<Access />} />
                <Route path="/monitor" element={<Monitor />} />
              </Routes>
            </Suspense>
            <Toaster />
          </Layout>
        </OrganizationProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
