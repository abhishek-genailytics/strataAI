import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/hooks/use-toast'
import { qk } from '@/utils/queryKeys'
import { listModels, createApiKey, enableModels } from '@/services/providers'
import { formatMoney } from '@/utils/format'
import { Key, Bot, DollarSign } from 'lucide-react'
import type { ModelInfo, Provider } from '@/types/backend'

export default function ConfigureProviderDialog({
  open, onOpenChange, provider
}: {
  open: boolean
  onOpenChange: (o: boolean) => void
  provider: Provider | null
}) {
  const { toast } = useToast()
  const qc = useQueryClient()
  const [label, setLabel] = useState('')
  const [apiKey, setApiKey] = useState('')

  const provKey = provider?.id // adjust if your backend expects provider "name" instead of "id"
  const { data: models, isLoading } = useQuery({
    queryKey: ['cfg-models', provKey],
    queryFn: () => listModels({ provider: provKey! }),
    enabled: !!provKey && open
  })

  const [selected, setSelected] = useState<Record<string, boolean>>({})
  useEffect(() => {
    // reset selections when dialog opens
    if (open) setSelected({})
  }, [open])

  const selectedIds = useMemo(() => Object.keys(selected).filter(k => selected[k]), [selected])
  
  // Select All functionality
  const toggleSelectAll = () => {
    if (!models?.length) return
    const allSelected = models.every((m: ModelInfo) => selected[m.id])
    if (allSelected) {
      // Deselect all
      setSelected({})
    } else {
      // Select all
      const newSelected: Record<string, boolean> = {}
      models.forEach((m: ModelInfo) => {
        newSelected[m.id] = true
      })
      setSelected(newSelected)
    }
  }

  const allSelected = models?.length ? models.every((m: ModelInfo) => selected[m.id]) : false
  const someSelected = models?.length ? models.some((m: ModelInfo) => selected[m.id]) : false

  const mCreateKey = useMutation({
    mutationFn: async () => {
      if (!provider) throw new Error('No provider selected')
      // 1) create API key/connection
      await createApiKey({ provider: provider.id, label, api_key: apiKey })
      // 2) enable models (optional)
      if (selectedIds.length) {
        await enableModels({ provider: provider.id, model_ids: selectedIds })
      }
    },
    onSuccess: async () => {
      toast({ title: 'Provider configured', description: `${provider?.name} connected` })
      await Promise.all([
        qc.invalidateQueries({ queryKey: qk.providers }),
        qc.invalidateQueries({ queryKey: qk.apiKeys }),
        qc.invalidateQueries({ queryKey: qk.models(provider?.id) })
      ])
      onOpenChange(false)
      setLabel(''); setApiKey('')
    },
    onError: (e: any) => toast({ title: 'Configuration failed', description: e.message, variant: 'destructive' })
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>Configure {provider?.name}</DialogTitle></DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Connection label</Label>
            <Input placeholder="e.g. Production key" value={label} onChange={e=>setLabel(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>API key</Label>
            <Input placeholder="sk-..." value={apiKey} onChange={e=>setApiKey(e.target.value)} />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Select models to enable</Label>
              {models?.length > 0 && (
                <Button 
                  type="button"
                  variant="outline" 
                  size="sm"
                  onClick={toggleSelectAll}
                  className="h-8 px-3 text-xs"
                >
                  {allSelected ? 'Deselect All' : 'Select All'}
                </Button>
              )}
            </div>
            <div className="rounded-md border">
              <ScrollArea className="h-64">
                <div className="divide-y">
                  {isLoading ? (
                    <div className="p-4 text-sm text-slate-500">Loading models…</div>
                  ) : (models?.length ? (
                    <>
                      {/* Select All option at the top */}
                      <label className="flex items-center gap-3 p-3 cursor-pointer bg-slate-50 font-medium">
                        <Checkbox 
                          checked={allSelected}
                          ref={(el) => {
                            if (el) {
                              el.indeterminate = someSelected && !allSelected
                            }
                          }}
                          onCheckedChange={toggleSelectAll} 
                        />
                        <div>
                          <div className="font-medium">
                            {allSelected ? 'All Models Selected' : someSelected ? 'Some Models Selected' : 'Select All Models'}
                          </div>
                          <div className="text-xs text-slate-500">
                            {selectedIds.length} of {models.length} models selected
                          </div>
                        </div>
                      </label>
                      {/* Individual models */}
                      {models.map((m: ModelInfo) => (
                        <label key={m.id} className="flex items-center gap-3 p-3 cursor-pointer hover:bg-slate-50">
                          <Checkbox 
                            checked={!!selected[m.id]} 
                            onCheckedChange={(v: boolean) => setSelected(s => ({ ...s, [m.id]: !!v }))} 
                          />
                          <div className="min-w-0 flex-1">
                            <div className="font-medium truncate">{m.display_name}</div>
                            <div className="text-xs text-slate-500 truncate">
                              {m.id} • Context: {m.context_window?.toLocaleString() || 'N/A'} tokens
                              {m.pricing && (
                                <>
                                  • Input: {formatMoney(m.pricing.input_per_1k, m.pricing.currency || 'USD')}/1K
                                  • Output: {formatMoney(m.pricing.output_per_1k, m.pricing.currency || 'USD')}/1K
                                </>
                              )}
                            </div>
                            {m.capabilities && m.capabilities.length > 0 && (
                              <div className="flex gap-1 mt-1">
                                {m.capabilities.map((cap: string) => (
                                  <span key={cap} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-800">
                                    {cap}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </label>
                      ))}
                    </>
                  ) : (
                    <div className="p-4 text-sm text-slate-500">No models found for this provider.</div>
                  ))}
                </div>
              </ScrollArea>
            </div>
            {selectedIds.length > 0 && (
              <div className="text-sm text-slate-600">
                {selectedIds.length} model{selectedIds.length === 1 ? '' : 's'} selected
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={()=>onOpenChange(false)}>Cancel</Button>
          <Button onClick={()=>mCreateKey.mutate()} disabled={!label || !apiKey || mCreateKey.isPending}>
            Save & Connect
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
