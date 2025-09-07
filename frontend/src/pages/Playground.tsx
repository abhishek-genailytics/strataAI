import { useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function Playground(){
  const [model,setModel]=useState('openai/gpt-4o')
  const [input,setInput]=useState('')
  const [output,setOutput]=useState<string>('')

  const run = async ()=>{
    const { data } = await api.post('/playground/chat/completions',{ // streaming can be added later
      model, messages:[{role:'user',content:input}], stream:false
    })
    setOutput(data?.choices?.[0]?.message?.content ?? '')
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Playground</h1>
      <Card className="p-4 space-y-3">
        <input className="w-full border rounded-md p-2" value={input} onChange={e=>setInput(e.target.value)} placeholder="Enter prompt…" />
        <div className="flex items-center gap-2">
          <input className="border rounded-md p-2" value={model} onChange={e=>setModel(e.target.value)} />
          <Button onClick={run}>Run</Button>
        </div>
      </Card>
      <Card className="p-4 whitespace-pre-wrap">{output}</Card>
    </div>
  )
}
