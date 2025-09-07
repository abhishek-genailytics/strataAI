import axios, { AxiosError } from 'axios'
import { supabase } from '@/services/supabase'

export type ApiError = {
  status: number
  code?: string
  type?: string
  message: string
  details?: unknown
}

const api = axios.create({
  baseURL: (import.meta as any).env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  timeout: 120000,
})

// Always use the latest Supabase session (Supabase MCP keeps it fresh)
async function getJwt(): Promise<string | null> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? localStorage.getItem('sb:jwt')
}

api.interceptors.request.use(async (config) => {
  // JWT
  const jwt = await getJwt()
  if (jwt) config.headers.Authorization = `Bearer ${jwt}`
  // Organization scoping
  const orgId = localStorage.getItem('org_id')
  if (orgId) config.headers['X-Organization-ID'] = orgId
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError<any>) => {
    const status = err.response?.status ?? 0
    // Normalize backend errors (OpenAI-compatible or our own)
    const payload = err.response?.data
    const normalized: ApiError = {
      status,
      code: payload?.error?.code ?? payload?.code,
      type: payload?.error?.type ?? payload?.type,
      message:
        payload?.error?.message ??
        payload?.message ??
        err.message ??
        'Unknown error',
      details: payload?.error?.param ?? payload?.details,
    }

    // If token invalid/expired → sign out to force login (Supabase MCP)
    if (status === 401) {
      await supabase.auth.signOut()
      localStorage.removeItem('sb:jwt')
    }
    return Promise.reject(normalized)
  }
)

export default api

// Generic typed helpers
export const apiGet = async <T>(url: string, params?: any) =>
  (await api.get<T>(url, { params })).data
export const apiPost = async <T>(url: string, body?: any, params?: any) =>
  (await api.post<T>(url, body, { params })).data
export const apiPut = async <T>(url: string, body?: any) =>
  (await api.put<T>(url, body)).data
export const apiDelete = async <T>(url: string) =>
  (await api.delete<T>(url)).data
