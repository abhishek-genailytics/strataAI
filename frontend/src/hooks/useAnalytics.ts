import { useQuery } from '@tanstack/react-query'
import { getSummary, getByModel, getByUser, getRecentErrors, getSeries, AnalyticsFilters } from '@/services/analytics'
import { qk } from '@/utils/queryKeys'

export const useSummary = (f?: AnalyticsFilters) =>
  useQuery({ queryKey: [...qk.usageSummary('global'), f || {}], queryFn: () => getSummary(f) })

export const useSeries = (f?: AnalyticsFilters) =>
  useQuery({ queryKey: ['analytics-series', f || {}], queryFn: () => getSeries(f) })

export const useByModel = (f?: AnalyticsFilters) =>
  useQuery({ queryKey: [...qk.byModel, f || {}], queryFn: () => getByModel(f) })

export const useByUser = (f?: AnalyticsFilters) =>
  useQuery({ queryKey: [...qk.byUser, f || {}], queryFn: () => getByUser(f) })

export const useRecentErrors = (f?: AnalyticsFilters) =>
  useQuery({ queryKey: [...qk.errors, f || {}], queryFn: () => getRecentErrors(f) })
