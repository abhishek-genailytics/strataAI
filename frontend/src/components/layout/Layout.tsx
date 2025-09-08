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

  // Demo data for when user is not loaded
  const displayEmail = user?.email || 'demo@strataai.com'
  const displayOrgs = orgs.length > 0 ? orgs : [{ id: 'demo', name: 'Demo Organization' }]
  const displayCurrent = current || displayOrgs[0]

  return (
    <div className="min-h-screen grid grid-cols-[240px_1fr]">
      <aside className="border-r bg-slate-50/50 flex flex-col min-h-screen">
        <div className="p-4">
          <div className="flex items-center gap-2 font-semibold text-lg mb-4">
            <Bot className="h-6 w-6 text-blue-600" />
            StrataAI
          </div>
          
          {/* Organization Selector */}
          <div className="relative">
            <select
              className="w-full appearance-none rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              value={displayCurrent?.id ?? ''}
              onChange={(e) => setCurrent && setCurrent(displayOrgs.find(o => o.id === e.target.value) || null)}
            >
              {displayOrgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 pointer-events-none" />
          </div>
        </div>
        
        <Separator />
        
        <nav className="p-2 space-y-1 flex-1">
          {links.map(l => {
            const Icon = l.icon
            const isActive = pathname === l.to
            return (
              <Link 
                key={l.to} 
                to={l.to}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors hover:bg-slate-100 ${
                  isActive ? 'bg-blue-50 text-blue-700 font-medium border-r-2 border-blue-600' : 'text-slate-700'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-blue-600' : 'text-slate-500'}`} />
                {l.label}
              </Link>
            )
          })}
        </nav>
        
        <Separator />
        
        <div className="p-4">
          <div className="text-xs text-gray-500 mb-3 truncate">
            {user?.email}
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleSignOut}
            className="w-full justify-start gap-2"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </Button>
        </div>
      </aside>
      <main className="min-h-screen bg-gray-50/30">{children}</main>
    </div>
  )
}
