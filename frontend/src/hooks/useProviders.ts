import { useQuery } from "@tanstack/react-query";
import {
  listProviders,
  listConfiguredProviders,
  listApiKeys,
  listModels,
} from "@/services/providers";
import { qk } from "@/utils/queryKeys";

// Demo data for development/demonstration
const demoProviders = [
  { id: "openai", name: "openai", display_name: "OpenAI", configured: true },
  {
    id: "anthropic",
    name: "anthropic",
    display_name: "Anthropic",
    configured: false,
  },
  { id: "grok", name: "grok", display_name: "Grok", configured: false },
];

export const useProviders = () => {
  const {
    data: allProviders,
    error: providersError,
    ...rest
  } = useQuery({
    queryKey: qk.providers,
    queryFn: listProviders,
    retry: (failureCount, error: any) => {
      console.error("Providers query failed:", error);
      // Don't retry on 401 errors (auth issues)
      if (error?.status === 401) return false;
      return failureCount < 2;
    },
  });

  const { data: configuredProviders, error: configError } = useQuery({
    queryKey: ["configured-providers"],
    queryFn: listConfiguredProviders,
    enabled: !!allProviders, // Only run after providers are loaded
    retry: (failureCount, error: any) => {
      console.error("Configured providers query failed:", error);
      if (error?.status === 401) return false;
      return failureCount < 2;
    },
  });

  // Merge provider data with configuration status
  let providersWithConfig = allProviders?.map((provider) => ({
    ...provider,
    configured:
      configuredProviders?.some((cp) => cp.provider?.id === provider.id) ||
      false,
  }));

  // Don't use demo data - let the real API calls handle the data
  // This ensures we get the actual configured status from the backend

  // Log errors for debugging
  if (providersError) {
    console.error("Providers loading error:", providersError);
  }
  if (configError) {
    console.error("Configured providers loading error:", configError);
  }

  return { data: providersWithConfig, error: providersError, ...rest };
};

export const useApiKeys = () =>
  useQuery({ queryKey: qk.apiKeys, queryFn: listApiKeys });
export const useModels = (provider?: string) =>
  useQuery({
    queryKey: qk.models(provider),
    queryFn: () => listModels({ provider }),
  });
