import React, { useState, useEffect, useCallback } from "react";
import { Search, Grid, List } from "lucide-react";
import { MagicCard } from "../components/ui/magic-card";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
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
}

export const Models: React.FC = () => {
  const { currentOrganization } = useAuth();
  const { showToast } = useToast();
  const [models, setModels] = useState<Model[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [connectedProviders, setConnectedProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProvider, setSelectedProvider] = useState<string>("all");
  const [selectedModelType, setSelectedModelType] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [showConnectedOnly, setShowConnectedOnly] = useState(false);
  const [showPricing, setShowPricing] = useState(true);
  const [activeTab, setActiveTab] = useState<"providers" | "pricing">(
    "providers"
  );

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

  const filteredModels = models.filter((model) => {
    const matchesSearch =
      model.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      model.model_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      model.description?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesProvider =
      selectedProvider === "all" || model.provider_id === selectedProvider;
    const matchesType =
      selectedModelType === "all" || model.model_type === selectedModelType;

    return matchesSearch && matchesProvider && matchesType;
  });

  const getProviderInfo = (providerId: string) => {
    return providers.find((p) => p.id === providerId);
  };

  const getConnectedProvidersCount = () => {
    return connectedProviders.length;
  };

  const getModelTypeIcon = (modelType: string) => {
    switch (modelType) {
      case "chat":
        return "💬";
      case "completion":
        return "✍️";
      case "embedding":
        return "🔗";
      case "image":
        return "🖼️";
      case "audio":
        return "🎵";
      case "multimodal":
        return "🌟";
      default:
        return "🤖";
    }
  };

  const getModelTypeColor = (modelType: string) => {
    switch (modelType) {
      case "chat":
        return "bg-blue-100 text-blue-800";
      case "completion":
        return "bg-green-100 text-green-800";
      case "embedding":
        return "bg-purple-100 text-purple-800";
      case "image":
        return "bg-pink-100 text-pink-800";
      case "audio":
        return "bg-yellow-100 text-yellow-800";
      case "multimodal":
        return "bg-indigo-100 text-indigo-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatPrice = (pricing: Pricing[]) => {
    if (!pricing || pricing.length === 0) return "Pricing not available";

    const inputPricing = pricing.find((p) => p.pricing_type === "input");
    const outputPricing = pricing.find((p) => p.pricing_type === "output");

    let priceText = "";
    if (inputPricing) {
      priceText += `Input: $${inputPricing.price_per_unit}/${inputPricing.unit}`;
    }
    if (outputPricing) {
      if (priceText) priceText += ", ";
      priceText += `Output: $${outputPricing.price_per_unit}/${outputPricing.unit}`;
    }

    return priceText || "Pricing not available";
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
                Model Pricing
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
                    onClick={() => (window.location.href = "/providers")}
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
          <>
            {/* Model Pricing Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card className="p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                    <span className="text-2xl">🤖</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      Total Models
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {models.length}
                    </p>
                  </div>
                </div>
              </Card>

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
                  <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                    <span className="text-2xl">💬</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      Chat Models
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {models.filter((m) => m.model_type === "chat").length}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
                    <span className="text-2xl">🖼️</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      Vision Models
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {models.filter((m) => m.supports_vision).length}
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Filters and Controls */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 mb-8 border border-gray-200 dark:border-gray-700">
              <div className="flex flex-col lg:flex-row gap-4 items-center justify-between">
                {/* Search and Filters */}
                <div className="flex flex-col sm:flex-row gap-4 flex-1">
                  <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      type="text"
                      placeholder="Search models..."
                      value={searchTerm}
                      onChange={setSearchTerm}
                      className="pl-10"
                    />
                  </div>

                  <select
                    value={selectedProvider}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                      setSelectedProvider(e.target.value)
                    }
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="all">All Providers</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.display_name}
                      </option>
                    ))}
                  </select>

                  <select
                    value={selectedModelType}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                      setSelectedModelType(e.target.value)
                    }
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="all">All Types</option>
                    <option value="chat">Chat</option>
                    <option value="completion">Completion</option>
                    <option value="embedding">Embedding</option>
                    <option value="image">Image</option>
                    <option value="audio">Audio</option>
                    <option value="multimodal">Multimodal</option>
                  </select>
                </div>

                {/* View Controls */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="connectedOnly"
                      checked={showConnectedOnly}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setShowConnectedOnly(e.target.checked)
                      }
                      className="rounded border-gray-300"
                    />
                    <label
                      htmlFor="connectedOnly"
                      className="text-sm text-gray-600 dark:text-gray-400"
                    >
                      Connected Only
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="showPricing"
                      checked={showPricing}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setShowPricing(e.target.checked)
                      }
                      className="rounded border-gray-300"
                    />
                    <label
                      htmlFor="showPricing"
                      className="text-sm text-gray-600 dark:text-gray-400"
                    >
                      Show Pricing
                    </label>
                  </div>

                  <div className="flex border border-gray-300 dark:border-gray-600 rounded-md">
                    <Button
                      variant={viewMode === "grid" ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => setViewMode("grid")}
                      className="rounded-r-none border-r-0"
                    >
                      <Grid className="h-4 w-4" />
                    </Button>
                    <Button
                      variant={viewMode === "list" ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => setViewMode("list")}
                      className="rounded-l-none"
                    >
                      <List className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Empty State - Show when no providers are connected */}
            {connectedProviders.length === 0 ? (
              <div className="text-center py-12">
                {/* Hero Section */}
                <div className="mb-12 max-w-3xl mx-auto">
                  <div className="mb-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4">
                      <span className="text-2xl text-white">🚀</span>
                    </div>
                  </div>
                  <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4 bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 bg-clip-text text-transparent">
                    Start adding your Models here
                  </h2>
                  <p className="text-xl text-slate-600 dark:text-slate-400 leading-relaxed">
                    Configure a new provider account by adding your API keys and
                    start using Models
                  </p>
                </div>

                {/* Provider Grid */}
                <div className="max-w-6xl mx-auto">
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 lg:gap-6">
                    {providers.map((provider) => (
                      <Card
                        key={provider.id}
                        className="group relative overflow-hidden border-0 shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-1 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm"
                        onClick={() => (window.location.href = "/providers")}
                      >
                        <div className="p-6 text-center">
                          {/* Provider Logo */}
                          <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                            {provider.logo_url ? (
                              <img
                                src={provider.logo_url}
                                alt={provider.display_name}
                                className="w-12 h-12 mx-auto rounded-lg object-cover"
                              />
                            ) : (
                              "🤖"
                            )}
                          </div>

                          {/* Provider Name */}
                          <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors duration-200 mb-2">
                            {provider.display_name}
                          </h3>

                          {/* Provider Type */}
                          <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                            {provider.name}
                          </p>

                          {/* Model Count */}
                          <div className="text-xs text-slate-400 dark:text-slate-500">
                            {
                              models.filter(
                                (m) => m.provider_id === provider.id
                              ).length
                            }{" "}
                            models
                          </div>

                          {/* Hover Effect */}
                          <div className="absolute inset-0 bg-gradient-to-t from-blue-600/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>

                {/* Quick Setup Guide */}
                <div className="mt-16 max-w-4xl mx-auto">
                  <Card className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm border-0 shadow-lg">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center">
                          <span className="text-blue-500 mr-2">✨</span>
                          Quick Setup
                        </h3>
                        <ol className="space-y-3 text-slate-600 dark:text-slate-400">
                          <li className="flex items-start space-x-3">
                            <div className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-sm font-medium">
                              1
                            </div>
                            <span>
                              Choose your preferred AI provider from the grid
                              above
                            </span>
                          </li>
                          <li className="flex items-start space-x-3">
                            <div className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-sm font-medium">
                              2
                            </div>
                            <span>
                              Click to setup and configure your API credentials
                            </span>
                          </li>
                          <li className="flex items-start space-x-3">
                            <div className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-sm font-medium">
                              3
                            </div>
                            <span>Test your connection in the playground</span>
                          </li>
                          <li className="flex items-start space-x-3">
                            <div className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-sm font-medium">
                              4
                            </div>
                            <span>Start building with powerful AI models</span>
                          </li>
                        </ol>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center">
                          <span className="text-purple-500 mr-2">🎯</span>
                          Popular Combinations
                        </h3>
                        <div className="space-y-3 text-slate-600 dark:text-slate-400">
                          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                            <span className="font-medium text-blue-900 dark:text-blue-100">
                              OpenAI + Anthropic:
                            </span>{" "}
                            Best for general use cases
                          </div>
                          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                            <span className="font-medium text-green-900 dark:text-green-100">
                              Google + Mistral:
                            </span>{" "}
                            Great for multilingual tasks
                          </div>
                          <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
                            <span className="font-medium text-orange-900 dark:text-orange-100">
                              Groq + Together:
                            </span>{" "}
                            Ultra-fast inference
                          </div>
                          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                            <span className="font-medium text-purple-900 dark:text-purple-100">
                              Ollama + Self-hosted:
                            </span>{" "}
                            Complete privacy
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            ) : (
              /* Connected Providers View */
              <div className="mb-8">
                {/* Connected Providers */}
                <div className="mb-6">
                  <div className="flex items-center mb-4">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                    <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                      CONNECTED PROVIDERS
                    </h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {connectedProviders.map((provider) => (
                      <Card key={provider.id} className="p-4">
                        <div className="flex items-center">
                          {provider.logo_url ? (
                            <img
                              src={provider.logo_url}
                              alt={provider.display_name}
                              className="w-10 h-10 rounded-lg mr-3 object-cover"
                            />
                          ) : (
                            <span className="text-2xl mr-3">🤖</span>
                          )}
                          <div>
                            <h3 className="font-medium text-gray-900 dark:text-white">
                              {provider.display_name}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {
                                models.filter(
                                  (m) => m.provider_id === provider.id
                                ).length
                              }{" "}
                              models
                            </p>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>

                {/* Other Providers */}
                <div>
                  <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
                    OTHER PROVIDERS
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {providers
                      .filter(
                        (provider) =>
                          !connectedProviders.find(
                            (cp) => cp.id === provider.id
                          )
                      )
                      .map((provider) => (
                        <Card key={provider.id} className="p-4">
                          <div className="flex items-center">
                            {provider.logo_url ? (
                              <img
                                src={provider.logo_url}
                                alt={provider.display_name}
                                className="w-10 h-10 rounded-lg mr-3 object-cover"
                              />
                            ) : (
                              <span className="text-2xl mr-3">🤖</span>
                            )}
                            <div>
                              <h3 className="font-medium text-gray-900 dark:text-white">
                                {provider.display_name}
                              </h3>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {
                                  models.filter(
                                    (m) => m.provider_id === provider.id
                                  ).length
                                }{" "}
                                models
                              </p>
                            </div>
                          </div>
                        </Card>
                      ))}
                  </div>
                </div>
              </div>
            )}

            {/* Models Grid/List */}
            {viewMode === "grid" ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredModels.map((model) => {
                  const provider = getProviderInfo(model.provider_id);

                  return (
                    <MagicCard
                      key={model.id}
                      className="p-6 cursor-pointer transition-all duration-200 hover:shadow-lg"
                      gradientColor="#3b82f6"
                      gradientOpacity={0.1}
                    >
                      <div className="flex flex-col h-full">
                        {/* Header */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center">
                            <span className="text-3xl mr-3">
                              {getModelTypeIcon(model.model_type)}
                            </span>
                            <div>
                              <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                                {model.display_name}
                              </h3>
                              <span
                                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getModelTypeColor(
                                  model.model_type
                                )}`}
                              >
                                {model.model_type}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Provider Info */}
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

                        {/* Description */}
                        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 flex-grow">
                          {model.description || "No description available"}
                        </p>

                        {/* Capabilities */}
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

                        {/* Pricing */}
                        {showPricing && (
                          <div className="mb-4">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                              Pricing:
                            </p>
                            <p className="text-sm text-gray-700 dark:text-gray-300">
                              {formatPrice(model.pricing)}
                            </p>
                          </div>
                        )}

                        {/* Action Button */}
                        <Button
                          variant="primary"
                          size="sm"
                          className="w-full mt-auto"
                        >
                          Use Model
                        </Button>
                      </div>
                    </MagicCard>
                  );
                })}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredModels.map((model) => {
                  const provider = getProviderInfo(model.provider_id);

                  return (
                    <Card key={model.id} className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-2xl">
                              {getModelTypeIcon(model.model_type)}
                            </span>
                            <div>
                              <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                                {model.display_name}
                              </h3>
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                {model.model_name}
                              </p>
                            </div>
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getModelTypeColor(
                                model.model_type
                              )}`}
                            >
                              {model.model_type}
                            </span>
                          </div>

                          <p className="text-gray-600 dark:text-gray-400 mb-3">
                            {model.description || "No description available"}
                          </p>

                          <div className="flex flex-wrap gap-2 mb-3">
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

                          {showPricing && (
                            <p className="text-sm text-gray-700 dark:text-gray-300">
                              <strong>Pricing:</strong>{" "}
                              {formatPrice(model.pricing)}
                            </p>
                          )}
                        </div>

                        <div className="flex flex-col items-end gap-2">
                          {provider && (
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {provider.display_name}
                            </p>
                          )}
                          <Button variant="primary" size="sm">
                            Use Model
                          </Button>
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* Empty State */}
            {filteredModels.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🤖</div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  No models found
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Try adjusting your search criteria or filters.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
