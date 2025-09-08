import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { OrganizationProvider } from '@/contexts/OrganizationContext'

const qc = new QueryClient()

function SimpleLogin() {
  return <div>Login Page</div>
}

function SimpleModels() {
  return <div>Models Page</div>
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <OrganizationProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<SimpleLogin />} />
            <Route path="/models" element={<SimpleModels />} />
            <Route path="/" element={<Navigate to="/models" replace />} />
          </Routes>
        </BrowserRouter>
      </OrganizationProvider>
    </QueryClientProvider>
  )
}
