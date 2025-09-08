import { apiGet, apiPost } from '@/services/api'
import type { ChatMessage, ModelInfo, Session, UsageSummary } from '@/types/backend'
import { streamChat } from '@/services/stream'

export const listPlaygroundModels = () => apiGet<ModelInfo[]>('/playground/models')

export const listSessions = () => apiGet<Session[]>('/playground/sessions')
export const createSession = (payload: { name?: string; model: string; system?: string }) =>
  apiPost<Session>('/playground/sessions', payload)

export const getSessionMessages = (sessionId: string) =>
  apiGet<ChatMessage[]>(`/playground/sessions/${sessionId}/messages`)

export const chat = (payload: { model: string; messages: ChatMessage[]; stream?: boolean; params?: any }) =>
  apiPost<any>('/playground/chat/completions', payload)

export const chatStream = async ({
  body,
  onToken,
  signal
}: {
  body: { model: string; messages: ChatMessage[]; params?: any }
  onToken: (chunk: string) => void
  signal?: AbortSignal
}) => {
  const base = (import.meta as any).env.VITE_API_URL ?? 'http://localhost:8000/api/v1'
  await streamChat({
    url: `${base}/playground/chat/completions`,
    body: { ...body, stream: true },
    onToken,
    signal,
  })
}

export const regenerate = (sessionId: string, messageId?: string) =>
  apiPost<any>(`/playground/sessions/${sessionId}/regenerate`, { message_id: messageId })

export const getUsageSummary = (sessionId?: string) =>
  sessionId
    ? apiGet<UsageSummary>(`/playground/sessions/${sessionId}/usage`)
    : apiGet<UsageSummary>('/usage-analytics/summary')
