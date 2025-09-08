import { apiGet } from '@/services/api'
import { BreakdownRow, ErrorRow, UsageSummary, SeriesPoint } from '@/types/backend'

export type AnalyticsFilters = {
  from?: string // ISO 'YYYY-MM-DD' or ISO datetime
  to?: string
  provider?: string
  model?: string
  user_id?: string
  limit?: number // for errors
}

export const getSummary = (params?: AnalyticsFilters) =>
  apiGet<UsageSummary>('/usage-analytics/summary', params)

export const getSeries = (params?: AnalyticsFilters) =>
  apiGet<SeriesPoint[]>('/usage-analytics/series', params)

export const getByModel = (params?: AnalyticsFilters) =>
  apiGet<BreakdownRow[]>('/usage-analytics/by-model', params)

export const getByUser = (params?: AnalyticsFilters) =>
  apiGet<BreakdownRow[]>('/usage-analytics/by-user', params)

export const getRecentErrors = (params?: AnalyticsFilters) =>
  apiGet<ErrorRow[]>('/errors/recent', params)
