import { useQuery } from "@tanstack/react-query";
import { getEnabledModels } from "@/services/providers";

export function useEnabledModels(providerId: string | undefined) {
  return useQuery({
    queryKey: ["enabled-models", providerId],
    queryFn: () => getEnabledModels(providerId!),
    enabled: !!providerId,
  });
}
