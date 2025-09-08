import { Link, useLocation } from 'react-router-dom'
import { type ReactNode } from 'react'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import { useOrganization } from '@/contexts/OrganizationContext'
import { useAuth } from '@/contexts/AuthContext'
import { 
  Bot, 
  PlayCircle, 
  BarChart3, 
  Key, 
  LogOut,
  ChevronDown
} from 'lucide-react'

const links = [
  { to: '/models', label: 'Models', icon: Bot },
  { to: '/playground', label: 'Playground', icon: PlayCircle },
  { to: '/monitor', label: 'Monitor', icon: BarChart3 },
  { to: '/access', label: 'Access', icon: Key }
]

export default function Layout({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()
  const { current, orgs, setCurrent } = useOrganization()
  const { user, signOut } = useAuth()

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  return (
    <div className="min-h-full grid grid-cols-[240px_1fr]">
      <aside className="border-r bg-slate-50 flex flex-col min-h-screen">
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
        <nav className="p-2 space-y-1 flex-1">
          {links.map(l => (
            <Link key={l.to} to={l.to}
              className={`block rounded-md px-3 py-2 text-sm hover:bg-slate-100 ${pathname===l.to?'bg-slate-100 font-medium':''}`}>
              {l.label}
            </Link>
          ))}
        </nav>
        <Separator />
        <div className="p-4">
          <div className="text-xs text-gray-600 mb-2">
            {user?.email}
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleSignOut}
            className="w-full"
          >
            Sign Out
          </Button>
        </div>
      </aside>
      <main className="min-h-screen">{children}</main>
    </div>
  )
}
