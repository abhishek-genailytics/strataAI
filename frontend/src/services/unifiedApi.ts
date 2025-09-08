import axios from 'axios'
import { getSupabaseClient } from './supabase'

// Create a separate axios instance for unified API endpoints (/v1/*)
const createUnifiedApiClient = () => {
  const baseURL = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'https://strataai-backend.onrender.com'
  
  const client = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Add auth interceptor
  client.interceptors.request.use(async (config) => {
    const supabase = getSupabaseClient()
    const { data: { session } } = await supabase.auth.getSession()
    
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }

    // Add organization header if available
    const orgId = localStorage.getItem('selectedOrganizationId')
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId
    }

    return config
  })

  return client
}

const unifiedApiClient = createUnifiedApiClient()

// Unified API endpoints
export const unifiedApi = {
  // Chat completions (OpenAI-compatible)
  chatCompletions: (payload: {
    model: string
    messages: Array<{ role: string; content: string }>
    temperature?: number
    max_tokens?: number
    stream?: boolean
  }) => unifiedApiClient.post('/v1/chat/completions', payload),

  // Playground read endpoints
  getSession: (sessionId: string) => 
    unifiedApiClient.get(`/v1/playground/sessions/${sessionId}`),
  
  getSessionMessages: (sessionId: string, params?: { after_index?: number; limit?: number }) =>
    unifiedApiClient.get(`/v1/playground/sessions/${sessionId}/messages`, { params }),
  
  listSessions: (params?: { limit?: number; cursor?: string }) =>
    unifiedApiClient.get('/v1/playground/sessions', { params }),
  
  getSessionByClientId: (clientSessionId: string) =>
    unifiedApiClient.get(`/v1/playground/sessions/by-client-id/${clientSessionId}`),
}

export default unifiedApi
