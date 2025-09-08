import { useEffect, useRef, useState } from 'react'
import { onError, type ErrorEvent } from '@/services/errorBus'
import { useToast } from '@/hooks/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { supabase } from '@/services/supabase'

export default function GlobalErrorPortal(){
  const { toast } = useToast()
  const [expiredOpen, setExpiredOpen] = useState(false)
  const lastShownRef = useRef<{ key: string; at: number } | null>(null)

  useEffect(() => {
    // de-dupe rapid repeats (same status+message within 5s)
    const sub = onError((ev: ErrorEvent) => {
      const key = `${ev.status}:${ev.message}`
      const now = Date.now()
      if (lastShownRef.current && lastShownRef.current.key === key && (now - lastShownRef.current.at) < 5000) {
        return
      }
      lastShownRef.current = { key, at: now }

      if (ev.status === 401) {
        setExpiredOpen(true)
        return
      }
      if (ev.status === 403) {
        toast({ title: 'Not authorized', description: ev.message || 'You do not have permission.', variant: 'destructive' })
        return
      }
      // All other errors → toast
      toast({
        title: `Request failed${ev.status ? ` (${ev.status})` : ''}`,
        description: ev.message || 'Unknown error',
        variant: 'destructive'
      })
    })
    return () => { sub() }
  }, [toast])

  const handleReauth = async () => {
    // Full sign-out then send to login
    await supabase.auth.signOut()
    localStorage.removeItem('sb:jwt')
    setExpiredOpen(false)
    window.location.assign('/login')
  }

  return (
    <>
      <Dialog open={expiredOpen} onOpenChange={setExpiredOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Session expired</DialogTitle></DialogHeader>
          <div className="text-sm text-slate-600">
            Your session has expired or is invalid. Please sign in again to continue.
          </div>
          <DialogFooter>
            <Button onClick={handleReauth}>Sign in again</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
