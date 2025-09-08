import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/hooks/use-toast'
import { qk } from '@/utils/queryKeys'
import { getQueryParam, removeQueryParam } from '@/utils/url'
import {
  listPlaygroundModels, listSessions, createSession,
  getSessionMessages, chatStream, getUsageSummary, regenerate
} from '@/services/playground'
import type { ChatMessage, ModelInfo, Session, UsageSummary } from '@/types/backend'

type Params = {
  temperature: number
  max_tokens: number
  top_p: number
  stop?: string[]
}

export default function Playground(){
  const { toast } = useToast()
  const qc = useQueryClient()
  const [searchParams] = useSearchParams()

  // Models
  const { data: models } = useQuery({ queryKey: qk.pgModels, queryFn: listPlaygroundModels })
  const modelOptions = models ?? []

  // Sessions
  const { data: sessions } = useQuery({ queryKey: qk.sessions, queryFn: listSessions })
  const [currentSession, setCurrentSession] = useState<Session | null>(null)

  // Messages + usage
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const { data: usage } = useQuery({
    queryKey: qk.usageSummary(currentSession?.id),
    queryFn: () => currentSession?.id ? getUsageSummary(currentSession.id) : Promise.resolve({} as UsageSummary),
    enabled: !!currentSession?.id
  })

  // Input composer
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  // Right-rail state
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [params, setParams] = useState<Params>({ temperature: 0.7, max_tokens: 512, top_p: 1 })

  // Handoff from Models page (?model=provider/model)
  useEffect(() => {
    if (!modelOptions.length) return
    const queryModel = searchParams.get('model') || getQueryParam('model')
    if (queryModel) {
      // If the model exists, auto-create a session using it
      const exists = modelOptions.some(m => m.id === queryModel)
      if (exists) {
        mCreateSession.mutate({ model: queryModel })
        removeQueryParam('model')
      } else {
        // fallback: just preselect in the dropdown even if not in list (unlikely)
        setSelectedModel(queryModel)
        removeQueryParam('model')
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modelOptions.length])

  // When sessions load and none selected, pick the latest or create new with first model
  useEffect(() => {
    if (!sessions) return
    if (currentSession?.id) return
    if (sessions.length > 0) {
      setCurrentSession(sessions[0])
    } else {
      const firstModel = modelOptions[0]?.id
      if (firstModel) mCreateSession.mutate({ model: firstModel })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessions, modelOptions])

  // When current session changes, load messages + model/params defaults
  useEffect(() => {
    let ignore = false
    const run = async () => {
      if (!currentSession) return
      try {
        const msgs = await getSessionMessages(currentSession.id)
        if (ignore) return
        setMessages(msgs)
        setSelectedModel(currentSession.model)
      } catch (e:any) {
        toast({ title: 'Failed to load messages', description: e.message, variant: 'destructive' })
      }
    }
    run()
    return () => { ignore = true }
  }, [currentSession, toast])

  // Create session mutation
  const mCreateSession = useMutation({
    mutationFn: ({ model, name, system }: { model: string; name?: string; system?: string }) =>
      createSession({ model, name, system }),
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: qk.sessions })
      setCurrentSession(s)
      setMessages([])
      setSelectedModel(s.model)
    },
    onError: (e:any) => toast({ title: 'Failed to create session', description: e.message, variant: 'destructive' })
  })

  // Send message with streaming
  const send = async () => {
    if (!currentSession?.id) return
    const content = input.trim()
    if (!content) return
    setInput('')

    const newMsgs = [...messages, { role: 'user', content } as ChatMessage]
    setMessages(newMsgs)

    // Prepare a placeholder assistant message to stream into
    const assistantIndex = newMsgs.length
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    setIsStreaming(true)
    const controller = new AbortController()
    abortRef.current = controller

    try {
      await chatStream({
        body: {
          model: selectedModel || currentSession.model,
          messages: newMsgs,
          params
        },
        onToken: (chunk) => {
          setMessages(prev => {
            const copy = [...prev]
            const last = copy[assistantIndex]
            if (last) last.content = (last.content || '') + chunk
            return copy
          })
        },
        signal: controller.signal
      })
      // refresh usage
      qc.invalidateQueries({ queryKey: qk.usageSummary(currentSession.id) })
    } catch (e:any) {
      toast({ title: 'Chat failed', description: e.message, variant: 'destructive' })
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }

  const cancel = () => {
    if (abortRef.current) abortRef.current.abort()
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const currentModelInfo: ModelInfo | undefined = useMemo(
    () => modelOptions.find(m => m.id === (selectedModel || currentSession?.model)),
    [modelOptions, selectedModel, currentSession?.model]
  )

  return (
    <div className="grid grid-cols-[280px_1fr_320px] gap-4 p-4">
      {/* Left: Sessions */}
      <Card className="p-0 overflow-hidden">
        <div className="p-3 border-b flex items-center justify-between">
          <div className="font-medium">Sessions</div>
          <Button size="sm" onClick={() => mCreateSession.mutate({ model: selectedModel || modelOptions[0]?.id })}>
            New
          </Button>
        </div>
        <ScrollArea className="h-[calc(100vh-140px)]">
          <div className="p-2 space-y-1">
            {(sessions ?? []).map(s => (
              <button
                key={s.id}
                className={`w-full text-left px-3 py-2 rounded-md text-sm hover:bg-slate-100 ${
                  currentSession?.id === s.id ? 'bg-slate-100 font-medium' : ''
                }`}
                onClick={() => setCurrentSession(s)}
              >
                <div className="truncate">{s.name || s.model}</div>
                <div className="text-[11px] text-slate-500 truncate">{s.model}</div>
              </button>
            ))}
          </div>
        </ScrollArea>
      </Card>

      {/* Middle: Chat */}
      <div className="flex flex-col min-h-[calc(100vh-100px)]">
        <Card className="flex-1 p-0 overflow-hidden">
          <ScrollArea className="h-[calc(100vh-220px)]">
            <div className="p-4 space-y-4">
              {messages.map((m, idx) => (
                <div key={idx} className="flex">
                  <div className={`rounded-lg px-3 py-2 max-w-[80%] whitespace-pre-wrap text-sm ${
                    m.role === 'user' ? 'bg-blue-50 ml-auto' : 'bg-slate-50'
                  }`}>
                    <div className="text-[11px] text-slate-500 mb-1">{m.role}</div>
                    {m.content}
                  </div>
                </div>
              ))}
              {!messages.length && (
                <div className="text-sm text-slate-500">No messages yet. Type a prompt below to get started.</div>
              )}
            </div>
          </ScrollArea>

          <Separator />
          <div className="p-3 space-y-2">
            <Label>Message</Label>
            <Textarea
              placeholder="Ask anything… (Enter to send, Shift+Enter for new line)"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={3}
            />
            <div className="flex items-center gap-2">
              <Button onClick={send} disabled={!currentSession || isStreaming}>Send</Button>
              <Button variant="outline" onClick={cancel} disabled={!isStreaming}>Stop</Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Right: Model + Params + Usage */}
      <Card className="p-4">
        <div className="space-y-4">
          <div>
            <Label>Model</Label>
            <Select
              value={selectedModel || currentSession?.model || ''}
              onValueChange={(v) => setSelectedModel(v)}
            >
              <SelectTrigger className="mt-1"><SelectValue placeholder="Select a model" /></SelectTrigger>
              <SelectContent>
                {modelOptions.map(m => (
                  <SelectItem key={m.id} value={m.id}>{m.display_name} ({m.id})</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {currentModelInfo && (
              <div className="mt-2 text-[11px] text-slate-500">
                ctx {currentModelInfo.context_window} •
                {currentModelInfo.pricing && (
                  <> ${currentModelInfo.pricing.input_per_1k ?? '—'}/1K in • ${currentModelInfo.pricing.output_per_1k ?? '—'}/1K out</>
                )}
              </div>
            )}
          </div>

          <Separator />

          <div className="space-y-3">
            <Label>Temperature: {params.temperature.toFixed(1)}</Label>
            <Slider
              value={[params.temperature]}
              min={0} max={2} step={0.1}
              onValueChange={([v]) => setParams(p => ({ ...p, temperature: v }))}
            />
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Max tokens</Label>
                <Input
                  type="number"
                  value={params.max_tokens}
                  onChange={(e)=>setParams(p=>({...p, max_tokens: Math.max(1, Number(e.target.value)||1)}))}
                />
              </div>
              <div>
                <Label>Top-p</Label>
                <Input
                  type="number" step="0.05" min="0" max="1"
                  value={params.top_p}
                  onChange={(e)=>setParams(p=>({...p, top_p: Math.max(0, Math.min(1, Number(e.target.value)||0))}))}
                />
              </div>
            </div>
            <div>
              <Label>Stop sequences (comma-separated)</Label>
              <Input
                placeholder="e.g. ###, END"
                onBlur={(e)=> {
                  const raw = e.target.value
                  const arr = raw ? raw.split(',').map(s=>s.trim()).filter(Boolean) : undefined
                  setParams(p=>({ ...p, stop: arr }))
                }}
              />
            </div>
          </div>

          <Separator />

          <UsagePanel usage={usage} />

          <Separator />

          <RegenerateBlock
            disabled={!currentSession || isStreaming || messages.filter(m=>m.role==='assistant').length===0}
            onRegenerate={async () => {
              if (!currentSession) return
              try {
                await regenerate(currentSession.id) // server will regen last
                const msgs = await getSessionMessages(currentSession.id)
                setMessages(msgs)
                qc.invalidateQueries({ queryKey: qk.usageSummary(currentSession.id) })
              } catch (e:any) {
                toast({ title: 'Regenerate failed', description: e.message, variant: 'destructive' })
              }
            }}
          />
        </div>
      </Card>
    </div>
  )
}

function UsagePanel({ usage }: { usage?: UsageSummary }){
  return (
    <div className="space-y-2">
      <div className="font-medium">Usage (session)</div>
      <div className="text-sm grid grid-cols-2 gap-x-3 gap-y-1">
        <span className="text-slate-500">Requests</span><span>{usage?.requests ?? '—'}</span>
        <span className="text-slate-500">Input tokens</span><span>{usage?.input_tokens ?? '—'}</span>
        <span className="text-slate-500">Output tokens</span><span>{usage?.output_tokens ?? '—'}</span>
        <span className="text-slate-500">Cost (USD)</span><span>{usage?.cost_usd != null ? `$${usage.cost_usd.toFixed(4)}` : '—'}</span>
      </div>
    </div>
  )
}

function RegenerateBlock({ disabled, onRegenerate }:{ disabled:boolean; onRegenerate:()=>void }){
  return (
    <div className="space-y-2">
      <div className="font-medium">Actions</div>
      <Button variant="outline" disabled={disabled} onClick={onRegenerate}>Regenerate last</Button>
    </div>
  )
}
