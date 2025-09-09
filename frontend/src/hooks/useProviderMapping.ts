import { useQuery } from "@tanstack/react-query";
import { listProviders } from "@/services/providers";
import { qk } from "@/utils/queryKeys";

/**
 * Hook to get provider mapping between names and UUIDs
 */
export function useProviderMapping() {
  const { data: providers } = useQuery({
    queryKey: qk.providers,
    queryFn: listProviders,
  });

  const nameToId = new Map<string, string>();
  const idToName = new Map<string, string>();

  if (providers) {
    providers.forEach((provider) => {
      nameToId.set(provider.name, provider.id);
      idToName.set(provider.id, provider.name);
    });
  }

  return {
    nameToId,
    idToName,
    getNameById: (id: string) => idToName.get(id),
    getIdByName: (name: string) => nameToId.get(name),
  };
}
