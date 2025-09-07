import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
type Token = { id:string; name:string; scopes:string[]; expires_at:string|null }
export default function Access(){
  const [tokens,setTokens]=useState<Token[]>([])
  useEffect(()=>{ api.get('/user-management/tokens').then(r=>setTokens(r.data)) },[])
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Access</h1>
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="font-medium">Personal Access Tokens</div>
          <Button>Create PAT</Button>
        </div>
        <div className="text-sm">
          {tokens.map(t=>(
            <div key={t.id} className="flex items-center justify-between border-b py-2">
              <div>{t.name}</div>
              <div className="text-slate-500">{t.expires_at ?? 'no expiry'}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
