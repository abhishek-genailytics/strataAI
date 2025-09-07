import axios from 'axios'

export const api = axios.create({
  baseURL: (import.meta as any).env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const jwt = localStorage.getItem('sb:jwt') // will be set from Supabase session in Task 2
  const orgId = localStorage.getItem('org_id')
  if (jwt) config.headers.Authorization = `Bearer ${jwt}`
  if (orgId) config.headers['X-Organization-ID'] = orgId
  return config
})
