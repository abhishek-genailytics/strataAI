import { apiDelete, apiGet, apiPost } from '@/services/api'
import type { Profile, TokenRow } from '@/types/backend'

// Org members (read-only table for now; role changes can be added if backend supports)
export const listOrgMembers = () => apiGet<Profile[]>('/user-management/members')

// PATs
export const listTokens = () => apiGet<TokenRow[]>('/user-management/tokens')
export const createToken = (payload: { name: string; scopes: string[]; expires_at?: string | null }) =>
  apiPost<{ token: string; record: TokenRow }>('/user-management/tokens', payload)
export const revokeToken = (id: string) => apiDelete<void>(`/user-management/tokens/${id}`)
