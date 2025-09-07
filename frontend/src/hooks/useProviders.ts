import { useQuery } from '@tanstack/react-query'
import { listProviders, listApiKeys, listModels } from '@/services/providers'
import { qk } from '@/utils/queryKeys'

export const useProviders = () => useQuery({ queryKey: qk.providers, queryFn: listProviders })
export const useApiKeys = () => useQuery({ queryKey: qk.apiKeys, queryFn: listApiKeys })
export const useModels = (provider?: string) =>
  useQuery({ queryKey: qk.models(provider), queryFn: () => listModels({ provider }) })
