import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/services/supabase'

type User = { id: string; email?: string | null } | null
type Ctx = { user: User; loading: boolean }

const AuthCtx = createContext<Ctx>({ user: null, loading: true })

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user ? { id: data.user.id, email: data.user.email } : null)
      // store JWT for backend auth (Task 2 will harden this)
      supabase.auth.getSession().then(({ data }) => {
        const token = data.session?.access_token
        if (token) localStorage.setItem('sb:jwt', token)
        setLoading(false)
      })
    })

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ? { id: session.user.id, email: session.user.email } : null)
      if (session?.access_token) localStorage.setItem('sb:jwt', session.access_token)
    })

    return () => { sub.subscription.unsubscribe() }
  }, [])

  return <AuthCtx.Provider value={{ user, loading }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
