// Minimal streaming helper for OpenAI-compatible /chat/completions with stream:true
export type StreamChunk = { id?: string; choices?: Array<{ delta?: { content?: string } }> }
export type OnToken = (textChunk: string) => void

export async function streamChat({
  url,
  body,
  headers,
  signal,
  onToken
}: {
  url: string
  body: any
  headers?: Record<string, string>
  signal?: AbortSignal
  onToken: OnToken
}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(headers ?? {}) },
    body: JSON.stringify({ ...body, stream: true }),
    signal
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Stream failed: ${res.status} ${text}`)
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed || !trimmed.startsWith('data:')) continue
      const data = trimmed.slice(5).trim()
      if (data === '[DONE]') return
      try {
        const json: StreamChunk = JSON.parse(data)
        const txt = json.choices?.[0]?.delta?.content
        if (txt) onToken(txt)
      } catch { /* ignore partials */ }
    }
  }
}
