import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/utils/queryKeys'
import { listTokens, createToken, revokeToken } from '@/services/userManagement'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { useToast } from '@/hooks/use-toast'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'

export default function PATsTab(){
  const qc = useQueryClient()
  const { toast } = useToast()

  const { data, isLoading, error } = useQuery({ queryKey: qk.tokens, queryFn: listTokens })

  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [scopes, setScopes] = useState<string>('read,write') // comma-separated for simplicity
  const [expires, setExpires] = useState<string>('') // ISO date

  const [showToken, setShowToken] = useState<string | null>(null)
  const [revokeId, setRevokeId] = useState<string | null>(null)

  const mCreate = useMutation({
    mutationFn: () => createToken({
      name,
      scopes: scopes.split(',').map(s=>s.trim()).filter(Boolean),
      expires_at: expires || null
    }),
    onSuccess: (res) => {
      setOpen(false)
      setName('')
      setScopes('read,write')
      setExpires('')
      setShowToken(res.token) // copy-once
      qc.invalidateQueries({ queryKey: qk.tokens })
    },
    onError: (e:any) => toast({ title: 'Failed to create token', description: e.message, variant: 'destructive' })
  })

  const mRevoke = useMutation({
    mutationFn: (id: string) => revokeToken(id),
    onSuccess: () => {
      toast({ title: 'Token revoked' })
      qc.invalidateQueries({ queryKey: qk.tokens })
      setRevokeId(null)
    },
    onError: (e:any) => toast({ title: 'Failed to revoke', description: e.message, variant: 'destructive' })
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-600">Create personal access tokens to authenticate with CLI / API. You'll only see the token once.</div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button>Create PAT</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Personal Access Token</DialogTitle></DialogHeader>
            <div className="space-y-3">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input placeholder="My PAT" value={name} onChange={(e)=>setName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Scopes (comma-separated)</Label>
                <Input placeholder="read,write" value={scopes} onChange={(e)=>setScopes(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Expiry (optional, ISO yyyy-mm-dd)</Label>
                <Input type="date" value={expires} onChange={(e)=>setExpires(e.target.value)} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={()=>setOpen(false)}>Cancel</Button>
              <Button onClick={()=>mCreate.mutate()} disabled={!name || mCreate.isPending}>Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-6">Loading tokens…</div>
        ) : error ? (
          <div className="p-6 text-red-500">Failed to load tokens</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Scopes</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead>Last used</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map(t=>(
                <TableRow key={t.id}>
                  <TableCell>{t.name}</TableCell>
                  <TableCell className="text-xs">{t.scopes.join(', ')}</TableCell>
                  <TableCell>{t.expires_at ?? '—'}</TableCell>
                  <TableCell>{t.last_used ?? '—'}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" onClick={()=>setRevokeId(t.id)}>Revoke</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Copy-once token reveal */}
      <Dialog open={!!showToken} onOpenChange={(o)=>!o && setShowToken(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Copy your token</DialogTitle></DialogHeader>
          <div className="space-y-2">
            <div className="text-sm text-slate-600">This token will not be shown again.</div>
            <div className="rounded-md border p-3 font-mono text-sm break-all">{showToken}</div>
            <div className="flex justify-end">
              <Button onClick={()=>{ navigator.clipboard.writeText(showToken || ''); setShowToken(null) }}>Copy & Close</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Revoke confirm */}
      <AlertDialog open={!!revokeId} onOpenChange={(o)=>!o && setRevokeId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>Revoke this token?</AlertDialogTitle></AlertDialogHeader>
          <div className="text-sm text-slate-600">Any scripts/services using it will stop working.</div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={()=>setRevokeId(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={()=> revokeId && mRevoke.mutate(revokeId)} className="bg-red-600 hover:bg-red-700">
              Revoke
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
