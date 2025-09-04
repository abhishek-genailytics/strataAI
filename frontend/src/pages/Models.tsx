import React, { useState, useEffect, useCallback } from "react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ProviderConnectionModal } from "../components/provider/ProviderConnectionModal";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";
import { apiService } from "../services/api";

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
  capabilities: Record<string, any>;
  pricing: Pricing[];
}

interface Pricing {
  id: string;
  pricing_type: string;
  price_per_unit: number;
  unit: string;
  currency: string;
  region: string;
}

interface Provider {
  id: string;
  name: string;
  display_name: string;
  description: string;
  logo_url: string;
  base_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const Models: React.FC = () => {
  const { currentOrganization } = useAuth();
  const { showToast } = useToast();
  const [models, setModels] = useState<Model[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [connectedProviders, setConnectedProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"providers" | "pricing">(
    "providers"
  );
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(
    null
  );
  const [selectedProviderForModels, setSelectedProviderForModels] =
    useState<Provider | null>(null);
  const [showAddModelsModal, setShowAddModelsModal] = useState(false);
  const [availableModels, setAvailableModels] = useState<Model[]>([]);

  const loadData = useCallback(async () => {
    try {
      console.log("Starting loadData...");
      setLoading(true);

      // Set organization context for API calls
      if (currentOrganization?.id) {
        console.log("Setting organization context:", currentOrganization.id);
        apiService.setOrganizationContext(currentOrganization.id);
      } else {
        console.log("No current organization ID");
        setLoading(false);
        return;
      }

      // Load providers
      try {
        console.log("Loading providers...");
        const providersResponse = await apiService.get("/providers/");
        console.log("Providers response:", providersResponse);
        if (providersResponse.error) {
          throw new Error(providersResponse.error);
        }
        setProviders(providersResponse.data || []);
        console.log("Providers loaded:", providersResponse.data?.length || 0);
      } catch (error) {
        console.error("Failed to load providers:", error);
        showToast("error", "Failed to load providers");
        setProviders([]);
      }

      // Load models with pricing
      try {
        console.log("Loading models...");
        const modelsResponse = await apiService.get("/models/");
        console.log("Models response:", modelsResponse);
        if (modelsResponse.error) {
          throw new Error(modelsResponse.error);
        }
        setModels(modelsResponse.data || []);
        console.log("Models loaded:", modelsResponse.data?.length || 0);
      } catch (error) {
        console.error("Failed to load models:", error);
        showToast("error", "Failed to load models");
        setModels([]);
      }

      // Load connected providers (those with API keys)
      try {
        console.log("Loading connected providers...");
        const connectedResponse = await apiService.get(
          "/providers/organization/configured"
        );
        console.log("Connected providers response:", connectedResponse);
        if (connectedResponse.error) {
          throw new Error(connectedResponse.error);
        }
        const connectedData = connectedResponse.data || [];
        // Extract just the provider objects from the configured providers
        const connectedProvidersList = connectedData.map(
          (cp: any) => cp.provider
        );
        setConnectedProviders(connectedProvidersList);
        console.log(
          "Connected providers loaded:",
          connectedProvidersList.length
        );

        // Set the first connected provider as selected by default
        if (connectedProvidersList.length > 0 && !selectedProviderForModels) {
          setSelectedProviderForModels(connectedProvidersList[0]);
        }
      } catch (error) {
        console.error("Failed to load connected providers:", error);
        setConnectedProviders([]);
      }
    } catch (error) {
      console.error("Failed to load data:", error);
      showToast("error", "Failed to load data");
    } finally {
      console.log("Setting loading to false");
      setLoading(false);
    }
  }, [currentOrganization?.id, showToast]);

  useEffect(() => {
    if (currentOrganization?.id) {
      loadData();
    }
  }, [currentOrganization?.id, loadData]);

  const filteredModels = selectedProviderForModels
    ? models.filter(
        (model) => model.provider_id === selectedProviderForModels.id
      )
    : models.filter((model) =>
        connectedProviders.some((cp) => cp.id === model.provider_id)
      );

  const getConnectedProvidersCount = () => {
    return connectedProviders.length;
  };

  const handleProviderConnect = (provider: Provider) => {
    const isConnected = connectedProviders.some((cp) => cp.id === provider.id);

    if (isConnected) {
      // If connected, switch to Manage Model tab and select this provider
      setActiveTab("pricing");
      setSelectedProviderForModels(provider);
    } else {
      // If not connected, show connection modal
      setSelectedProvider(provider);
      setShowConnectionModal(true);
    }
  };

  const handleConnectionSuccess = () => {
    // Reload data to show updated connected providers
    loadData();
  };

  const handleCloseModal = () => {
    setShowConnectionModal(false);
    setSelectedProvider(null);
  };

  const handleAddModelsClick = () => {
    if (!selectedProviderForModels) {
      showToast("error", "Please select a provider first");
      return;
    }

    // Get all models for the selected provider
    const providerModels = models.filter(
      (model) => model.provider_id === selectedProviderForModels.id
    );

    // For now, we'll show all models as "available" since we don't have a concept of "selected" models
    // In a real implementation, you might have a separate API to get available models
    if (providerModels.length === 0) {
      showToast("info", "No models available for this provider");
      return;
    }

    setAvailableModels(providerModels);
    setShowAddModelsModal(true);
  };

  const handleCloseAddModelsModal = () => {
    setShowAddModelsModal(false);
    setAvailableModels([]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              Loading models...
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
            AI Models
          </h1>
          <p className="text-slate-600 dark:text-slate-400 text-lg">
            Explore and manage AI models from your connected providers. View
            capabilities, pricing, and performance metrics.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab("providers")}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "providers"
                    ? "border-blue-500 text-blue-600 dark:text-blue-400"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
                }`}
              >
                AI Providers
              </button>
              <button
                onClick={() => setActiveTab("pricing")}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "pricing"
                    ? "border-blue-500 text-blue-600 dark:text-blue-400"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
                }`}
              >
                Manage Model
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "providers" ? (
          <>
            {/* Providers Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Card className="p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                    <span className="text-2xl">🔗</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      Connected Providers
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {getConnectedProvidersCount()}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                    <span className="text-2xl">🤖</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Total Providers
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {providers.length}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                    <span className="text-2xl">🔑</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      API Keys
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {connectedProviders.length}
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Provider Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 items-stretch">
              {providers.map((provider) => {
                const isConnected = connectedProviders.some(
                  (cp) => cp.id === provider.id
                );
                const status = isConnected ? "connected" : "disconnected";

                return (
                  <Card
                    key={provider.id}
                    className="p-6 cursor-pointer transition-all duration-200 hover:shadow-lg h-full flex flex-col min-h-[280px]"
                    onClick={() => handleProviderConnect(provider)}
                  >
                    <div className="flex flex-col h-full">
                      {/* Header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center">
                          {provider.logo_url ? (
                            <img
                              src={provider.logo_url}
                              alt={provider.display_name}
                              className="w-12 h-12 rounded-lg mr-3 object-cover"
                            />
                          ) : (
                            <span className="text-3xl mr-3">🤖</span>
                          )}
                          <div>
                            <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                              {provider.display_name}
                            </h3>
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                status === "connected"
                                  ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
                                  : "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
                              }`}
                            >
                              {status === "connected"
                                ? "Connected"
                                : "Disconnected"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 flex-grow overflow-hidden">
                        {provider.description || "No description available"}
                      </p>

                      {/* Action Button */}
                      <Button
                        variant={
                          status === "connected" ? "secondary" : "primary"
                        }
                        size="sm"
                        className="w-full mt-auto"
                      >
                        {status === "connected" ? "Manage" : "Setup"}
                      </Button>
                    </div>
                  </Card>
                );
              })}
            </div>

            {/* Setup Instructions */}
            <div className="mt-12 bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Getting Started
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    Setup Process
                  </h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
                    <li>Choose a provider from the grid above</li>
                    <li>Click "Setup" to configure your API key</li>
                    <li>Enter your API key and optional project name</li>
                    <li>Test your connection in the playground</li>
                    <li>Start building with multiple AI models</li>
                  </ol>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    Benefits
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
                    <li>Access to multiple AI models and providers</li>
                    <li>Unified interface for all your AI needs</li>
                    <li>Cost optimization across different providers</li>
                    <li>Easy switching between models</li>
                    <li>Centralized API key management</li>
                  </ul>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex gap-6">
            {/* Left Sidebar - Connected Providers */}
            <div className="w-80 flex-shrink-0">
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Connected Providers
                  </h3>
                  <div className="flex items-center text-green-600 dark:text-green-400">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-sm font-medium">
                      {connectedProviders.length} Connected
                    </span>
                  </div>
                </div>

                {connectedProviders.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🔗</div>
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                      No providers connected yet
                    </p>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setActiveTab("providers")}
                    >
                      Connect Provider
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* Show All Option */}
                    <div
                      className={`border rounded-lg p-4 transition-colors cursor-pointer ${
                        !selectedProviderForModels
                          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400"
                          : "border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                      }`}
                      onClick={() => setSelectedProviderForModels(null)}
                    >
                      <div className="flex items-center mb-3">
                        <span className="text-2xl mr-3">🌐</span>
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                            All Providers
                          </h4>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {
                              models.filter((model) =>
                                connectedProviders.some(
                                  (cp) => cp.id === model.provider_id
                                )
                              ).length
                            }{" "}
                            total models
                          </p>
                        </div>
                      </div>
                    </div>
                    {connectedProviders.map((provider) => {
                      const providerModels = models.filter(
                        (model) => model.provider_id === provider.id
                      );

                      return (
                        <div
                          key={provider.id}
                          className={`border rounded-lg p-4 transition-colors cursor-pointer ${
                            selectedProviderForModels?.id === provider.id
                              ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400"
                              : "border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                          }`}
                          onClick={() => setSelectedProviderForModels(provider)}
                        >
                          <div className="flex items-center mb-3">
                            {provider.logo_url ? (
                              <img
                                src={provider.logo_url}
                                alt={provider.display_name}
                                className="w-8 h-8 rounded mr-3"
                              />
                            ) : (
                              <span className="text-2xl mr-3">🤖</span>
                            )}
                            <div>
                              <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                                {provider.display_name}
                              </h4>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {providerModels.length} models
                              </p>
                            </div>
                          </div>

                          {/* Show models under this provider */}
                          {providerModels.length > 0 && (
                            <div className="space-y-2">
                              {providerModels.slice(0, 3).map((model) => (
                                <div
                                  key={model.id}
                                  className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-600 rounded px-2 py-1"
                                >
                                  <span className="text-gray-700 dark:text-gray-300 truncate">
                                    {model.display_name}
                                  </span>
                                  <span className="text-gray-500 dark:text-gray-400">
                                    {model.model_type}
                                  </span>
                                </div>
                              ))}
                              {providerModels.length > 3 && (
                                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                                  +{providerModels.length - 3} more models
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Main Content - Models Table */}
            <div className="flex-1">
              {/* Header */}
              <div className="mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                      {selectedProviderForModels
                        ? `${selectedProviderForModels.display_name} Models`
                        : "All Connected Models"}
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                      {selectedProviderForModels
                        ? `Manage your ${selectedProviderForModels.display_name} models and their pricing`
                        : "Manage your connected AI models and their pricing"}
                    </p>
                  </div>
                  <Button variant="primary" onClick={handleAddModelsClick}>
                    + Add{" "}
                    {selectedProviderForModels
                      ? selectedProviderForModels.display_name
                      : "Provider"}{" "}
                    Models
                  </Button>
                </div>
              </div>

              {/* Models Table */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          MODEL
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          TYPE
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          INPUT COST/1M TOKENS
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          OUTPUT COST/1M TOKENS
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          ACTIONS
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {filteredModels.map((model) => {
                        // Extract pricing information
                        const inputPricing = model.pricing?.find(
                          (p) => p.pricing_type === "input"
                        );
                        const outputPricing = model.pricing?.find(
                          (p) => p.pricing_type === "output"
                        );

                        return (
                          <tr
                            key={model.id}
                            className="hover:bg-gray-50 dark:hover:bg-gray-700"
                          >
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-2xl mr-3">🤖</span>
                                <div>
                                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                                    {model.display_name}
                                  </div>
                                  <div className="text-sm text-gray-500 dark:text-gray-400">
                                    {model.model_name}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-lg mr-2">💬</span>
                                <span className="text-sm text-gray-900 dark:text-white">
                                  {model.model_type}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {inputPricing
                                  ? `$${inputPricing.price_per_unit}`
                                  : "N/A"}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {outputPricing
                                  ? `$${outputPricing.price_per_unit}`
                                  : "N/A"}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                                  <svg
                                    className="w-4 h-4"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path
                                      fillRule="evenodd"
                                      d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z"
                                      clipRule="evenodd"
                                    />
                                  </svg>
                                </button>
                                <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                                  <svg
                                    className="w-4 h-4"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path
                                      fillRule="evenodd"
                                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                                      clipRule="evenodd"
                                    />
                                  </svg>
                                </button>
                                <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                                  <svg
                                    className="w-4 h-4"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                                  </svg>
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Empty State */}
                {filteredModels.length === 0 && (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">💰</div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                      No models found
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Connect to providers to see their models and pricing.
                    </p>
                    <Button
                      variant="primary"
                      onClick={() => setActiveTab("providers")}
                    >
                      Go to Providers
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Provider Connection Modal */}
      <ProviderConnectionModal
        isOpen={showConnectionModal}
        onClose={handleCloseModal}
        provider={selectedProvider}
        onSuccess={handleConnectionSuccess}
      />

      {/* Add Models Modal */}
      {showAddModelsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Add {selectedProviderForModels?.display_name} Models
              </h3>
              <button
                onClick={handleCloseAddModelsModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="mb-4">
              <p className="text-gray-600 dark:text-gray-400">
                All available models for{" "}
                {selectedProviderForModels?.display_name} are already configured
                and ready to use.
              </p>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {availableModels.map((model) => (
                <div
                  key={model.id}
                  className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">🤖</span>
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {model.display_name}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {model.model_name} • {model.model_type}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-600 dark:text-green-400 text-sm font-medium">
                      ✓ Available
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end mt-6">
              <Button variant="secondary" onClick={handleCloseAddModelsModal}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Models;
