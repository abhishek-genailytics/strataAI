import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export default function ProtectedRoute({ children }:{children:React.ReactElement}){
  const { user, loading } = useAuth()
  
  // Temporarily allow access for demonstration - remove in production
  const isDemoMode = import.meta.env.DEV && window.location.hostname === 'localhost'
  
  if (loading) return <div className="p-6">Loading…</div>
  if (!user && !isDemoMode) return <Navigate to="/login" replace />
  return children
}
