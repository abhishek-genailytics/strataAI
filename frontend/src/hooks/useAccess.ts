import { useQuery } from '@tanstack/react-query'
import { listOrgMembers } from '@/services/userManagement'
import { qk } from '@/utils/queryKeys'

export const useMembers = () =>
  useQuery({ queryKey: qk.members, queryFn: listOrgMembers })
