import axios, { AxiosError } from 'axios'
import { supabase } from '@/services/supabase'
import { emitError } from '@/services/errorBus'
import { nanoid } from 'nanoid'

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

async function getJwt(): Promise<string | null> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? localStorage.getItem('sb:jwt')
}

// Attach auth/org + request id
api.interceptors.request.use(async (config: any) => {
  const jwt = await getJwt()
  const orgId = localStorage.getItem('org_id')
  
  // Ensure headers object exists
  if (!config.headers) {
    config.headers = {}
  }
  
  if (jwt) config.headers.Authorization = `Bearer ${jwt}`
  if (orgId) config.headers['X-Organization-ID'] = orgId
  const rid = nanoid(10)
  config.headers['X-Request-ID'] = rid
  config._rid = rid
  return config
})

// Helper: normalize backend/openai-style errors
function normalize(err: AxiosError<any>): ApiError {
  const status = err.response?.status ?? 0
  const payload = err.response?.data
  return {
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
}

// Retry GETs once on transient errors
async function maybeRetry(err: AxiosError, config: any) {
  const transient = [429, 502, 503, 504]
  if (
    config &&
    !config._retry &&
    config.method?.toUpperCase() === 'GET' &&
    transient.includes(err.response?.status || 0)
  ) {
    config._retry = true
    await new Promise(r => setTimeout(r, 500 + Math.random()*500))
    return api(config)
  }
  throw err
}

// Attempt refresh once on 401
async function maybeRefreshAndRetry(err: AxiosError, config: any) {
  if (config && !config._retry401 && err.response?.status === 401) {
    config._retry401 = true
    try {
      const { data, error } = await supabase.auth.refreshSession()
      if (!error && data.session?.access_token) {
        localStorage.setItem('sb:jwt', data.session.access_token)
        // re-attach token header
        config.headers.Authorization = `Bearer ${data.session.access_token}`
        return api(config)
      }
    } catch {}
  }
  throw err
}

api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError<any>) => {
    const cfg: any = err.config || {}
    // Step 1: transient retry (GET)
    try { return await maybeRetry(err, cfg) } catch {}
    // Step 2: refresh & retry (401)
    try { return await maybeRefreshAndRetry(err, cfg) } catch {}

    // Step 3: normalize + emit to UI
    const n = normalize(err)
    emitError({
      ...n,
      url: cfg?.url,
      method: cfg?.method,
      requestId: cfg?._rid,
    })

    // Final: if 401, ensure sign-out so guard redirects (dialog also prompts)
    if (n.status === 401) {
      await supabase.auth.signOut()
      localStorage.removeItem('sb:jwt')
    }
    return Promise.reject(n)
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
