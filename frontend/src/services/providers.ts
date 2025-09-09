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

// Models - using organization connected models endpoint for manage page
export const listModels = async (params?: { provider?: string }) => {
  const response = await apiGet<ModelInfo[]>("/models/organization/connected", {
    ...params,
    type: "chat,multimodal",
  });
  return response; // Return the array directly
};
// Model enablement - this endpoint may not be implemented yet
export const enableModels = (payload: {
  provider: string;
  model_ids: string[];
}) => apiPost<void>("/models/enable", payload);
