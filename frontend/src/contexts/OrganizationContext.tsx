import { createContext, useContext, useEffect, useState } from 'react'
import api from '@/services/api'
import { supabase } from '@/services/supabase'

type Organization = { id: string; name: string }
type OrgCtx = {
  current: Organization | null
  orgs: Organization[]
  setCurrent: (org: Organization | null) => void
}

const OrgContext = createContext<OrgCtx>({
  current: null, orgs: [], setCurrent: ()=>{}
})

export const OrganizationProvider = ({ children }: { children: React.ReactNode }) => {
  const [orgs, setOrgs] = useState<Organization[]>([])
  const [current, setCurrent] = useState<Organization | null>(null)

  useEffect(() => {
    let mounted = true
    
    const loadOrganizations = async () => {
      try {
        // First check if we have a JWT token from Supabase session
        const { data: { session } } = await supabase.auth.getSession()
        if (!session?.access_token) {
          console.warn('No active Supabase session, skipping organization loading')
          return
        }

        // Ensure the JWT is stored for API calls
        localStorage.setItem('sb:jwt', session.access_token)

        const response = await api.get('/organizations')
        if (!mounted) return
        
        const organizations = response.data || []
        console.log('Loaded organizations:', organizations)
        setOrgs(organizations)
        
        const stored = localStorage.getItem('org_id')
        const found = organizations.find((o: Organization) => o.id === stored) ?? organizations[0] ?? null
        setCurrent(found || null)
        
        if (found) {
          localStorage.setItem('org_id', found.id)
          console.log('Organization context set:', found.name, found.id)
        } else {
          console.warn('No organizations found for user')
          // Clear invalid org_id if no organizations available
          localStorage.removeItem('org_id')
        }
      } catch (error) {
        if (!mounted) return
        console.error('Failed to load organizations:', error)
        // If it's an auth error, clear the org context
        if ((error as any)?.status === 401 || (error as any)?.status === 403) {
          localStorage.removeItem('org_id')
          localStorage.removeItem('sb:jwt')
          setCurrent(null)
        }
      }
    }
    
    // Add a small delay to ensure Supabase session is available
    const timer = setTimeout(() => {
      if (mounted) {
        loadOrganizations()
      }
    }, 500)
    
    return () => {
      mounted = false
      clearTimeout(timer)
    }
  }, [])

  useEffect(() => {
    if (current) localStorage.setItem('org_id', current.id)
  }, [current])

  return <OrgContext.Provider value={{ current, orgs, setCurrent }}>{children}</OrgContext.Provider>
}

export const useOrganization = ()=>useContext(OrgContext)
