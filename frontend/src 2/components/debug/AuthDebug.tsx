import { useEffect, useState } from 'react'
import { supabase } from '@/services/supabase'
import { useAuth } from '@/contexts/AuthContext'
import { useOrganization } from '@/contexts/OrganizationContext'

export default function AuthDebug() {
  const { user } = useAuth()
  const { current: org } = useOrganization()
  const [sessionInfo, setSessionInfo] = useState<any>(null)

  useEffect(() => {
    const checkSession = async () => {
      const { data } = await supabase.auth.getSession()
      setSessionInfo({
        hasSession: !!data.session,
        hasToken: !!data.session?.access_token,
        userId: data.session?.user?.id,
        tokenExpiry: data.session?.expires_at ? new Date(data.session.expires_at * 1000).toLocaleString() : null,
        localJwt: !!localStorage.getItem('sb:jwt'),
        localOrgId: localStorage.getItem('org_id')
      })
    }
    checkSession()
  }, [user])

  if (!sessionInfo) return null

  return (
    <div className="fixed top-4 right-4 bg-white border rounded p-4 text-xs shadow-lg z-50">
      <h3 className="font-bold mb-2">Auth Debug</h3>
      <div>User: {user?.email || 'None'}</div>
      <div>Org: {org?.name || 'None'}</div>
      <div>Session: {sessionInfo.hasSession ? '✅' : '❌'}</div>
      <div>Token: {sessionInfo.hasToken ? '✅' : '❌'}</div>
      <div>Local JWT: {sessionInfo.localJwt ? '✅' : '❌'}</div>
      <div>Local Org ID: {sessionInfo.localOrgId || 'None'}</div>
      {sessionInfo.tokenExpiry && (
        <div>Expires: {sessionInfo.tokenExpiry}</div>
      )}
    </div>
  )
}
