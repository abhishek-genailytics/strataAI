import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

const qc = new QueryClient()

function SimpleLogin() {
  return <div>Login Page</div>
}

function SimpleModels() {
  return <div>Models Page</div>
}

function SupabaseTest() {
  const [status, setStatus] = useState('Testing Supabase...')
  
  useEffect(() => {
    const testSupabase = async () => {
      try {
        // Test importing supabase
        const { supabase } = await import('@/services/supabase')
        setStatus('Supabase imported successfully')
        
        // Test basic connection
        const { data, error } = await supabase.auth.getSession()
        if (error) {
          setStatus(`Supabase error: ${error.message}`)
        } else {
          setStatus('Supabase working - no session found (expected)')
        }
      } catch (err) {
        setStatus(`Import error: ${(err as Error).message}`)
      }
    }
    
    testSupabase()
  }, [])
  
  return <div>{status}</div>
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<SimpleLogin />} />
          <Route path="/models" element={<SimpleModels />} />
          <Route path="/test" element={<SupabaseTest />} />
          <Route path="/" element={<Navigate to="/test" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
