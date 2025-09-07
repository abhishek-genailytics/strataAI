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
    api.get('/organizations').then(r => {
      setOrgs(r.data || [])
      const stored = localStorage.getItem('org_id')
      const found = r.data?.find((o: Organization) => o.id === stored) ?? r.data?.[0] ?? null
      setCurrent(found || null)
      if (found) localStorage.setItem('org_id', found.id)
    }).catch(()=>{})
  }, [])

  useEffect(() => {
    if (current) localStorage.setItem('org_id', current.id)
  }, [current])

  return <OrgContext.Provider value={{ current, orgs, setCurrent }}>{children}</OrgContext.Provider>
}

export const useOrganization = ()=>useContext(OrgContext)
