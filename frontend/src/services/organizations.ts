import { apiGet } from '@/services/api'
import type { Organization, Profile } from '@/types/backend'

export const listOrganizations = () => apiGet<Organization[]>('/organizations')
export const getProfile = () => apiGet<Profile>('/user-management/profile')
