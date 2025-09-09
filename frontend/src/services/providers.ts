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
}) => apiPost<ApiKey>("/api-keys", payload);
export const deleteApiKey = (id: string) => apiDelete<void>(`/api-keys/${id}`);

// Models - using playground models endpoint since /providers/models returns empty array
export const listModels = async (params?: { provider?: string }) => {
  const response = await apiGet<{ data: ModelInfo[]; meta: any }>(
    "/playground/models",
    { ...params, type: "chat,multimodal" }
  );
  return response.data; // Extract the data array from the response
};
// Model enablement - this endpoint may not be implemented yet
export const enableModels = (payload: {
  provider: string;
  model_ids: string[];
}) => apiPost<void>("/models/enable", payload);
