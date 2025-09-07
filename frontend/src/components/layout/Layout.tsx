import { Link, useLocation } from 'react-router-dom'
import { type ReactNode } from 'react'
import { Separator } from '@/components/ui/separator'
import { useOrganization } from '@/contexts/OrganizationContext'

const links = [
  { to: '/models', label: 'Models' },
  { to: '/playground', label: 'Playground' },
  { to: '/monitor', label: 'Monitor' },
  { to: '/access', label: 'Access' }
]

export default function Layout({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()
  const { current, orgs, setCurrent } = useOrganization()

  return (
    <div className="min-h-full grid grid-cols-[240px_1fr]">
      <aside className="border-r bg-slate-50">
        <div className="p-4">
          <div className="font-semibold">AI Gateway</div>
          <select
            className="mt-2 w-full rounded-md border p-1 text-sm"
            value={current?.id ?? ''}
            onChange={(e)=> setCurrent(orgs.find(o=>o.id===e.target.value) || null)}
          >
            {orgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        </div>
        <Separator />
        <nav className="p-2 space-y-1">
          {links.map(l => (
            <Link key={l.to} to={l.to}
              className={`block rounded-md px-3 py-2 text-sm hover:bg-slate-100 ${pathname===l.to?'bg-slate-100 font-medium':''}`}>
              {l.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="min-h-screen">{children}</main>
    </div>
  )
}
