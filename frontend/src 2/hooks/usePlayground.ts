import { useQuery } from '@tanstack/react-query'
import { listPlaygroundModels, listSessions, getUsageSummary } from '@/services/playground'
import { qk } from '@/utils/queryKeys'

export const usePlaygroundModels = () =>
  useQuery({ queryKey: qk.pgModels, queryFn: listPlaygroundModels })

export const useSessions = () =>
  useQuery({ queryKey: qk.sessions, queryFn: listSessions })

export const useGlobalUsageSummary = () =>
  useQuery({ queryKey: qk.usageSummary(), queryFn: () => getUsageSummary() })
