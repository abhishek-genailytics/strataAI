import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProviders } from '@/hooks/useProviders'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import ConfigureProviderDialog from '@/pages/models/ConfigureProviderDialog'
import AuthDebug from '@/components/debug/AuthDebug'
import { EmptyState } from '@/components/shared/EmptyState'
import { SkeletonList } from '@/components/shared/SkeletonList'

export default function Models(){
  const { data, isLoading, error } = useProviders()
  const navigate = useNavigate()

  const [openCfg, setOpenCfg] = useState(false)
  const [currentProvider, setCurrentProvider] = useState<any>(null)

  const openConfigure = (p:any) => { setCurrentProvider(p); setOpenCfg(true) }

  if (isLoading) return <SkeletonList rows={6} />
  if (error) return <div className="p-6 text-red-500">Failed to load providers</div>

  return (
    <div className="p-6 space-y-4">
      <AuthDebug />
      <h1 className="text-2xl font-semibold">Models & Providers</h1>
      {(!data || data.length === 0) ? (
        <EmptyState
          title="No providers found"
          description="Your organization doesn't have any providers yet."
        />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.map(p=>(
            <Card key={p.id} className="p-4 flex items-center justify-between">
              <div className="min-w-0">
                <div className="font-medium truncate">{p.name}</div>
                <div className="text-xs text-slate-500">{p.configured ? 'Connected' : 'Not connected'}</div>
              </div>
              <div className="flex items-center gap-2">
                {p.configured ? (
                  <Button variant="outline" onClick={()=>navigate(`/models/${p.id}`)}>Manage</Button>
                ) : (
                  <Button onClick={()=>openConfigure(p)}>Configure</Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <ConfigureProviderDialog
        open={openCfg}
        onOpenChange={setOpenCfg}
        provider={currentProvider}
      />
    </div>
  )
}
