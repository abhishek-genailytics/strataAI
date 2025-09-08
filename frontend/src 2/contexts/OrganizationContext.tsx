import { createContext, useContext, useEffect, useState } from 'react'
import api from '@/services/api'

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
    const loadOrganizations = async () => {
      try {
        // First check if we have a JWT token
        const jwt = localStorage.getItem('sb:jwt')
        if (!jwt) {
          console.warn('No JWT token available, skipping organization loading')
          return
        }

        const response = await api.get('/organizations')
        const organizations = response.data || []
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
        console.error('Failed to load organizations:', error)
        // If it's an auth error, clear the org context
        if ((error as any)?.status === 401) {
          localStorage.removeItem('org_id')
          setCurrent(null)
        }
      }
    }
    
    // Add a small delay to ensure JWT token is available
    const timer = setTimeout(loadOrganizations, 100)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (current) localStorage.setItem('org_id', current.id)
  }, [current])

  return <OrgContext.Provider value={{ current, orgs, setCurrent }}>{children}</OrgContext.Provider>
}

export const useOrganization = ()=>useContext(OrgContext)
