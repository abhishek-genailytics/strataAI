import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/services/supabase'

type User = { id: string; email?: string | null } | null
type Ctx = {
  user: User
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthCtx = createContext<Ctx>({
  user: null, loading: true, signIn: async()=>{}, signUp: async()=>{}, signOut: async()=>{}
})

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      const token = data.session?.access_token
      if (token) {
        localStorage.setItem('sb:jwt', token)
        console.log('JWT token stored from session')
      }
      setUser(data.session?.user ? { id: data.session.user.id, email: data.session.user.email } : null)
      setLoading(false)
    })

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.access_token) {
        localStorage.setItem('sb:jwt', session.access_token)
        console.log('JWT token updated from auth state change')
      }
      setUser(session?.user ? { id: session.user.id, email: session.user.email } : null)
    })

    return () => { sub.subscription.unsubscribe() }
  }, [])

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    if (data.session?.access_token) localStorage.setItem('sb:jwt', data.session.access_token)
    setUser(data.user ? { id: data.user.id, email: data.user.email } : null)
  }

  const signUp = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) throw error
    if (data.session?.access_token) localStorage.setItem('sb:jwt', data.session.access_token)
    setUser(data.user ? { id: data.user.id, email: data.user.email } : null)
  }

  const signOut = async () => {
    await supabase.auth.signOut()
    localStorage.removeItem('sb:jwt')
    setUser(null)
  }

  return <AuthCtx.Provider value={{ user, loading, signIn, signUp, signOut }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
