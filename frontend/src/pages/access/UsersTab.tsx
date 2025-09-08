import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listOrgMembers, inviteMember, updateMemberRole, removeMember } from '@/services/userManagement'
import { qk } from '@/utils/queryKeys'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogFooter, AlertDialogCancel, AlertDialogAction } from '@/components/ui/alert-dialog'
import { useState } from 'react'
import { useToast } from '@/hooks/use-toast'
import DataTable, { Column } from '@/components/shared/DataTable'

export default function UsersTab(){
  const qc = useQueryClient()
  const { toast } = useToast()
  const { data, isLoading, error } = useQuery({ queryKey: qk.members, queryFn: listOrgMembers })

  const [inviteOpen, setInviteOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'admin'|'member'>('member')

  const [removeId, setRemoveId] = useState<string | null>(null)

  const mInvite = useMutation({
    mutationFn: () => inviteMember({ email, role }),
    onSuccess: () => {
      toast({ title: 'Invitation sent', description: `${email} (${role})` })
      setInviteOpen(false)
      setEmail('')
      setRole('member')
      qc.invalidateQueries({ queryKey: qk.members })
    },
    onError: (e:any) => toast({ title: 'Failed to invite', description: e.message, variant: 'destructive' })
  })

  const mRole = useMutation({
    mutationFn: ({ id, nextRole }: { id: string; nextRole: 'owner'|'admin'|'member' }) => updateMemberRole(id, nextRole),
    onSuccess: () => {
      toast({ title: 'Role updated' })
      qc.invalidateQueries({ queryKey: qk.members })
    },
    onError: (e:any) => toast({ title: 'Failed to update role', description: e.message, variant: 'destructive' })
  })

  const mRemove = useMutation({
    mutationFn: (id: string) => removeMember(id),
    onSuccess: () => {
      toast({ title: 'Member removed' })
      qc.invalidateQueries({ queryKey: qk.members })
      setRemoveId(null)
    },
    onError: (e:any) => toast({ title: 'Failed to remove', description: e.message, variant: 'destructive' })
  })

  const columns: Column<any>[] = [
    { key: 'name', header: 'Name', sortable: true, accessor: (m)=> m.name ?? '—' },
    { key: 'email', header: 'Email', sortable: true, accessor: (m)=> m.email },
    {
      key: 'role', header: 'Role', className: 'w-[220px]',
      accessor: (m)=> (
        <Select defaultValue={m.role ?? 'member'} onValueChange={(v)=>mRole.mutate({ id: m.id, nextRole: v as any })}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="member">Member</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
            <SelectItem value="owner">Owner</SelectItem>
          </SelectContent>
        </Select>
      )
    },
    {
      key: 'actions', header: 'Actions', className: 'text-right',
      accessor: (m)=> <Button variant="outline" onClick={()=>setRemoveId(m.id)}>Remove</Button>
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-600">Invite users to your organization and manage roles.</div>
        <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
          <DialogTrigger asChild><Button>Invite User</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Invite user</DialogTitle></DialogHeader>
            <div className="space-y-3">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input placeholder="user@example.com" value={email} onChange={(e)=>setEmail(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={role} onValueChange={(v)=>setRole(v as any)}>
                  <SelectTrigger><SelectValue placeholder="Select role"/></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="member">Member</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={()=>setInviteOpen(false)}>Cancel</Button>
              <Button onClick={()=>mInvite.mutate()} disabled={!email || mInvite.isPending}>Send Invite</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="p-4">
        <DataTable
          rows={data ?? []}
          columns={columns}
          loading={isLoading}
          emptyText="No members yet"
          searchableKeys={['name','email','role'] as any}
        />
      </Card>

      <AlertDialog open={!!removeId} onOpenChange={(o)=>!o && setRemoveId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>Remove this member?</AlertDialogTitle></AlertDialogHeader>
          <div className="text-sm text-slate-600">They'll immediately lose access to this organization.</div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={()=>setRemoveId(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={()=> removeId && mRemove.mutate(removeId) } className="bg-red-600 hover:bg-red-700">
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
