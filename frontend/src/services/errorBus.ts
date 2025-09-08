// Lightweight, imperative event bus so interceptors (non-React) can notify UI
export type ErrorEvent = {
  status: number
  code?: string
  type?: string
  message: string
  details?: unknown
  url?: string
  method?: string
  requestId?: string
  ts?: number
}

type Listener = (ev: ErrorEvent) => void
const listeners: Listener[] = []

export function onError(cb: Listener) {
  listeners.push(cb)
  return () => {
    const idx = listeners.indexOf(cb)
    if (idx >= 0) listeners.splice(idx, 1)
  }
}

export function emitError(ev: ErrorEvent) {
  const withTs = { ts: Date.now(), ...ev }
  listeners.forEach(l => l(withTs))
}
