import { apiDelete, apiGet, apiPost } from "@/services/api";
import type { ApiKey, ModelInfo, Provider } from "@/types/backend";

// Use the actual backend endpoints from providers.py
export const listProviders = () => apiGet<Provider[]>("/providers");
export const listConfiguredProviders = () =>
  apiGet<any[]>("/providers/organization/configured");
export const listApiKeys = () => apiGet<ApiKey[]>("/api-keys");
export const createApiKey = (payload: {
  provider: string;
  label: string;
  api_key: string;
}) =>
  apiPost<ApiKey>("/api-keys", {
    provider_id: payload.provider,
    name: payload.label,
    api_key_value: payload.api_key,
  });
export const deleteApiKey = (id: string) => apiDelete<void>(`/api-keys/${id}`);

// Models - for configuration dialog, show ALL models for a provider (not just connected)
export const listModels = async (params?: {
  provider?: string;
  provider_id?: string;
}) => {
  const response = await apiGet<ModelInfo[]>("/models", {
    ...params,
    model_type: "chat,multimodal", // Include both chat and multimodal models
  });
  return response; // Return the array directly
};
// Model enablement - save selected models to org_model_enablement table
export const enableModels = (payload: {
  provider: string;
  model_ids: string[];
}) => apiPost<void>("/models/enable", payload);

// Get enabled models for a provider from org_model_enablement table
export const getEnabledModels = (providerId: string) =>
  apiGet<{
    provider_id: string;
    organization_id: string;
    enabled_models: any[];
    count: number;
  }>(`/models/organization/enabled/${providerId}`);

// Disconnect a provider - sets API keys and model enablement to inactive
export const disconnectProvider = (providerId: string) =>
  apiPost<{ message: string; provider_id: string }>(
    `/providers/${providerId}/disconnect`,
    {}
  );
