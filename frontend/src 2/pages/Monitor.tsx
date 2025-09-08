import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Card } from '@/components/ui/card'
type Summary = { requests:number; input_tokens:number; output_tokens:number; cost_usd:number }
export default function Monitor(){
  const [data,setData]=useState<Summary|null>(null)
  useEffect(()=>{ api.get('/usage-analytics/summary').then(r=>setData(r.data)) },[])
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Monitor</h1>
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {['requests','input_tokens','output_tokens','cost_usd'].map((k)=>(
          <Card key={k} className="p-4">
            <div className="text-sm text-slate-500">{k.replace('_',' ').toUpperCase()}</div>
            <div className="text-2xl font-semibold">{(data as any)?.[k] ?? '—'}</div>
          </Card>
        ))}
      </div>
    </div>
  )
}
