import { apiGet } from '@/services/api'
import type { BreakdownRow, ErrorRow, UsageSummary } from '@/types/backend'

export const getSummary = (params?: { from?: string; to?: string }) =>
  apiGet<UsageSummary>('/usage-analytics/summary', params)

export const getByModel = (params?: { from?: string; to?: string }) =>
  apiGet<BreakdownRow[]>('/usage-analytics/by-model', params)

export const getByUser = (params?: { from?: string; to?: string }) =>
  apiGet<BreakdownRow[]>('/usage-analytics/by-user', params)

export const getRecentErrors = (params?: { limit?: number }) =>
  apiGet<ErrorRow[]>('/errors/recent', params)
