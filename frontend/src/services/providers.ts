import { apiDelete, apiGet, apiPost } from '@/services/api'
import type { ApiKey, ModelInfo, Provider } from '@/types/backend'

export const listProviders = () => apiGet<Provider[]>('/providers')
export const listApiKeys = () => apiGet<ApiKey[]>('/api-keys')
export const createApiKey = (payload: { provider: string; label: string; api_key: string }) =>
  apiPost<ApiKey>('/api-keys', payload)
export const deleteApiKey = (id: string) => apiDelete<void>(`/api-keys/${id}`)

// Models exposed by backend for catalog/enablement
export const listModels = (params?: { provider?: string }) => apiGet<ModelInfo[]>('/models', params)
// Optional: Upsert/enable models for a provider if backend supports it
export const enableModels = (payload: { provider: string; model_ids: string[] }) =>
  apiPost<void>('/models/enable', payload)
