import { apiDelete, apiGet, apiPost, apiPut } from '@/services/api'
import type { Profile, TokenRow } from '@/types/backend'

// Org members
export const listOrgMembers = () => apiGet<Profile[]>('/user-management/users')
export const inviteMember = (payload: { email: string; role: 'admin' | 'member' }) =>
  apiPost<{ id: string }>('/user-management/invite', payload)
export const updateMemberRole = (id: string, role: 'owner'|'admin'|'member') =>
  apiPut<void>(`/user-management/members/${id}/role`, { role })
export const removeMember = (id: string) =>
  apiDelete<void>(`/user-management/users/${id}`)

// PATs
export const listTokens = () => apiGet<TokenRow[]>('/user-management/tokens')
export const createToken = (payload: { name: string; scopes: string[]; expires_at?: string | null }) =>
  apiPost<{ token: string; record: TokenRow }>('/user-management/tokens', payload)
export const revokeToken = (id: string) => apiDelete<void>(`/user-management/tokens/${id}`)
