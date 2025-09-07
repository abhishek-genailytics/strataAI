import { useEffect, useState } from 'react'
import { api } from '@/services/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

type Provider = { id:string; name:string; configured:boolean }
export default function Models(){
  const [providers,setProviders]=useState<Provider[]>([])
  useEffect(()=>{ api.get('/providers').then(r=>setProviders(r.data)) },[])
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Models & Providers</h1>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {providers.map(p=>(
          <Card key={p.id} className="p-4 flex items-center justify-between">
            <div>
              <div className="font-medium">{p.name}</div>
              <div className="text-xs text-slate-500">{p.configured?'Connected':'Not connected'}</div>
            </div>
            <Button variant="outline">{p.configured?'Manage':'Configure'}</Button>
          </Card>
        ))}
      </div>
    </div>
  )
}
