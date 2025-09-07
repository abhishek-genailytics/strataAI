import { useQuery } from '@tanstack/react-query'
import { getSummary, getByModel, getByUser, getRecentErrors } from '@/services/analytics'
import { qk } from '@/utils/queryKeys'

export const useSummary = (range?: {from?: string; to?: string}) =>
  useQuery({ queryKey: qk.usageSummary('global'), queryFn: () => getSummary(range) })

export const useByModel = (range?: {from?: string; to?: string}) =>
  useQuery({ queryKey: qk.byModel, queryFn: () => getByModel(range) })

export const useByUser = (range?: {from?: string; to?: string}) =>
  useQuery({ queryKey: qk.byUser, queryFn: () => getByUser(range) })

export const useRecentErrors = (limit = 50) =>
  useQuery({ queryKey: qk.errors, queryFn: () => getRecentErrors({ limit }) })
