import { useState } from 'react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'
import UsersTab from '@/pages/access/UsersTab'
import PATsTab from '@/pages/access/PATsTab'

export default function Access(){
  const [tab, setTab] = useState<'users'|'pats'>('users')
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Access</h1>
      </div>

      <Card className="p-0 overflow-hidden">
        <Tabs value={tab} onValueChange={(v: string)=>setTab(v as 'users'|'pats')}>
          <div className="border-b px-4 pt-4">
            <TabsList>
              <TabsTrigger value="users">User Management</TabsTrigger>
              <TabsTrigger value="pats">Personal Access Tokens</TabsTrigger>
            </TabsList>
          </div>
          <div className="p-4">
            <TabsContent value="users" className="m-0">
              <UsersTab />
            </TabsContent>
            <TabsContent value="pats" className="m-0">
              <PATsTab />
            </TabsContent>
          </div>
        </Tabs>
      </Card>
    </div>
  )
}
