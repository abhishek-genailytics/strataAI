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
  try {
    const { data, error } = await supabase.auth.getSession()
    if (error) {
      console.error('Supabase session error:', error)
      return localStorage.getItem('sb:jwt')
    }
    
    // Check if token is expired
    if (data.session?.expires_at) {
      const expiresAt = data.session.expires_at * 1000 // Convert to milliseconds
      const now = Date.now()
      if (now >= expiresAt) {
        console.warn('JWT token expired, attempting refresh...')
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
        if (refreshError) {
          console.error('Token refresh failed:', refreshError)
          return null
        }
        if (refreshData.session?.access_token) {
          localStorage.setItem('sb:jwt', refreshData.session.access_token)
          return refreshData.session.access_token
        }
      }
    }
    
    const token = data.session?.access_token
    if (token) {
      localStorage.setItem('sb:jwt', token)
      return token
    }
    
    return localStorage.getItem('sb:jwt')
  } catch (error) {
    console.error('Error getting JWT token:', error)
    return localStorage.getItem('sb:jwt')
  }
}

api.interceptors.request.use(async (config) => {
  // JWT
  const jwt = await getJwt()
  if (jwt) {
    config.headers.Authorization = `Bearer ${jwt}`
    console.log('API Request:', config.method?.toUpperCase(), config.url, 'with JWT token')
  } else {
    console.warn('API Request:', config.method?.toUpperCase(), config.url, 'NO JWT TOKEN')
  }
  // Organization scoping
  const orgId = localStorage.getItem('org_id')
  if (orgId) {
    config.headers['X-Organization-ID'] = orgId
    console.log('Using organization ID:', orgId)
  } else {
    console.warn('No organization ID found in localStorage')
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError<any>) => {
    const status = err.response?.status ?? 0
    const url = err.config?.url
    console.error(`API Error ${status} for ${url}:`, err.response?.data)
    
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

    // If token invalid/expired → try to refresh token first
    if (status === 401) {
      console.warn('401 Unauthorized - attempting token refresh before signing out')
      try {
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
        if (!refreshError && refreshData.session?.access_token) {
          localStorage.setItem('sb:jwt', refreshData.session.access_token)
          console.log('Token refreshed successfully, retry the request')
          // Don't sign out if refresh succeeded - let the user retry
          return Promise.reject(normalized)
        }
      } catch (refreshErr) {
        console.error('Token refresh failed:', refreshErr)
      }
      
      // Only sign out if refresh failed
      console.warn('Token refresh failed - signing out user')
      await supabase.auth.signOut()
      localStorage.removeItem('sb:jwt')
      localStorage.removeItem('org_id')
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
