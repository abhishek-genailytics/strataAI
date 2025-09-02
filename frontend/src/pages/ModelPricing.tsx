import React, { useState, useEffect } from "react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";
import { apiService } from "../services/api";

interface Provider {
  id: string;
  name: string;
  display_name: string;
  description: string;
  logo_url: string;
  is_active: boolean;
}

interface Model {
  id: string;
  provider_id: string;
  model_name: string;
  display_name: string;
  description: string;
  model_type: string;
  max_tokens: number;
  max_input_tokens: number;
  supports_streaming: boolean;
  supports_function_calling: boolean;
  supports_vision: boolean;
  supports_audio: boolean;
}

export const ModelPricing: React.FC = () => {
  const { currentOrganization } = useAuth();
  const { showToast } = useToast();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<string>("all");

  useEffect(() => {
    if (currentOrganization?.id) {
      loadData();
    }
  }, [currentOrganization?.id]);

  const loadData = async () => {
    try {
      console.log("ModelPricing: Starting loadData...");
      setLoading(true);

      // Set organization context for API calls
      if (currentOrganization?.id) {
        console.log("ModelPricing: Setting organization context:", currentOrganization.id);
        apiService.setOrganizationContext(currentOrganization.id);
      } else {
        console.log("ModelPricing: No current organization ID");
        setLoading(false);
        return;
      }

      // Load providers
      try {
        console.log("ModelPricing: Loading providers...");
        const providersResponse = await apiService.get("/providers/");
        console.log("ModelPricing: Providers response:", providersResponse);
        if (providersResponse.error) {
          throw new Error(providersResponse.error);
        }
        setProviders(providersResponse.data || []);
        console.log("ModelPricing: Providers loaded:", providersResponse.data?.length || 0);
      } catch (error) {
        console.error("ModelPricing: Failed to load providers:", error);
        showToast("error", "Failed to load providers");
        setProviders([]);
      }

      // Load models
      try {
        console.log("ModelPricing: Loading models...");
        const modelsResponse = await apiService.get("/models/");
        console.log("ModelPricing: Models response:", modelsResponse);
        if (modelsResponse.error) {
          throw new Error(modelsResponse.error);
        }
        setModels(modelsResponse.data || []);
        console.log("ModelPricing: Models loaded:", modelsResponse.data?.length || 0);
      } catch (error) {
        console.error("ModelPricing: Failed to load models:", error);
        showToast("error", "Failed to load models");
        setModels([]);
      }
    } catch (error) {
      console.error("ModelPricing: Failed to load data:", error);
      showToast("error", "Failed to load data");
    } finally {
      console.log("ModelPricing: Setting loading to false");
      setLoading(false);
    }
  };

  const filteredModels =
    selectedProvider === "all"
      ? models
      : models.filter((model) => model.provider_id === selectedProvider);

  const getProviderInfo = (providerId: string) => {
    return providers.find((p) => p.id === providerId);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              Loading model pricing...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            Model Pricing
          </h1>
          <p className="text-slate-600 dark:text-slate-400 text-lg">
            View pricing information for all available AI models across
            providers.
          </p>
        </div>

        {/* Provider Filter */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Filter by Provider
          </label>
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="all">All Providers</option>
            {providers.map((provider) => (
              <option key={provider.id} value={provider.id}>
                {provider.display_name}
              </option>
            ))}
          </select>
        </div>

        {/* Models Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map((model) => {
            const provider = getProviderInfo(model.provider_id);

            return (
              <Card key={model.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">🤖</span>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                        {model.display_name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {model.model_name}
                      </p>
                    </div>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                    {model.model_type}
                  </span>
                </div>

                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {model.description || "No description available"}
                </p>

                {provider && (
                  <div className="mb-4">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                      Provider:
                    </p>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {provider.display_name}
                    </p>
                  </div>
                )}

                <div className="mb-4">
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                    Capabilities:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {model.supports_streaming && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-green-100 dark:bg-green-800 text-green-700 dark:text-green-300">
                        Streaming
                      </span>
                    )}
                    {model.supports_function_calling && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300">
                        Function Calling
                      </span>
                    )}
                    {model.supports_vision && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300">
                        Vision
                      </span>
                    )}
                    {model.supports_audio && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-yellow-100 dark:bg-yellow-800 text-yellow-700 dark:text-yellow-300">
                        Audio
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <p>
                    <strong>Max Tokens:</strong>{" "}
                    {model.max_tokens?.toLocaleString() || "Unlimited"}
                  </p>
                  <p>
                    <strong>Max Input Tokens:</strong>{" "}
                    {model.max_input_tokens?.toLocaleString() || "Unlimited"}
                  </p>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                    Pricing information will be available once you connect to
                    this provider.
                  </p>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => (window.location.href = "/providers")}
                  >
                    Connect Provider
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Empty State */}
        {filteredModels.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">💰</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              No models found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {selectedProvider === "all"
                ? "No models are available. Connect to providers to see their models and pricing."
                : "No models found for the selected provider."}
            </p>
            {selectedProvider === "all" && (
              <Button
                variant="primary"
                onClick={() => (window.location.href = "/providers")}
              >
                Go to Providers
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
