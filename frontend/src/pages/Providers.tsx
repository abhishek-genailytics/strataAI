import React, { useState, useEffect } from "react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Modal } from "../components/ui/Modal";
import { Input } from "../components/ui/Input";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";
import { apiService } from "../services/api";

interface Provider {
  id: string;
  name: string;
  display_name: string;
  description: string;
  logo_url: string;
  website_url: string;
  base_url: string;
  is_active: boolean;
}

interface ConfiguredProvider {
  provider: Provider;
  api_key_count: number;
}

export const Providers: React.FC = () => {
  const { currentOrganization } = useAuth();
  const { showToast } = useToast();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [configuredProviders, setConfiguredProviders] = useState<
    ConfiguredProvider[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(
    null
  );
  const [apiKeyForm, setApiKeyForm] = useState({
    name: "",
    apiKey: "",
    projectId: "",
  });

  useEffect(() => {
    loadProviders();
    loadConfiguredProviders();
  }, [currentOrganization]);

  const loadProviders = async () => {
    try {
      if (currentOrganization?.id) {
        apiService.setOrganizationContext(currentOrganization.id);
      }

      const response = await apiService.get("/providers/");
      if (response.error) {
        throw new Error(response.error);
      }
      setProviders(response.data || []);
    } catch (error) {
      console.error("Failed to load providers:", error);
      showToast("error", "Failed to load providers");
      setProviders([]);
    }
  };

  const loadConfiguredProviders = async () => {
    try {
      if (currentOrganization?.id) {
        apiService.setOrganizationContext(currentOrganization.id);
      }

      const response = await apiService.get(
        "/providers/organization/configured"
      );
      if (response.error) {
        throw new Error(response.error);
      }
      setConfiguredProviders(response.data || []);
    } catch (error) {
      console.error("Failed to load configured providers:", error);
      setConfiguredProviders([]);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderSetup = (provider: Provider) => {
    setSelectedProvider(provider);
    setApiKeyForm({
      name: `${provider.display_name} API Key`,
      apiKey: "",
      projectId: "",
    });
    setShowApiKeyModal(true);
  };

  const handleApiKeySubmit = async () => {
    if (!selectedProvider || !apiKeyForm.name || !apiKeyForm.apiKey) {
      showToast("error", "Please fill in all required fields");
      return;
    }

    try {
      if (currentOrganization?.id) {
        apiService.setOrganizationContext(currentOrganization.id);
      }

      const response = await apiService.post("/api-keys/", {
        name: apiKeyForm.name,
        provider_id: selectedProvider.id,
        project_id: apiKeyForm.projectId || null,
        api_key_value: apiKeyForm.apiKey,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      showToast("success", "API key added successfully");
      setShowApiKeyModal(false);
      loadConfiguredProviders(); // Refresh the list
    } catch (error) {
      console.error("Failed to add API key:", error);
      showToast("error", "Failed to add API key");
    }
  };

  const getProviderStatus = (providerId: string) => {
    const configured = configuredProviders.find(
      (cp) => cp.provider.id === providerId
    );
    return configured ? "connected" : "disconnected";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300";
      case "disconnected":
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300";
      case "setup":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "connected":
        return "Connected";
      case "disconnected":
        return "Disconnected";
      case "setup":
        return "Setup Required";
      default:
        return "Unknown";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              Loading providers...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              AI Providers
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              Configure and manage your AI provider connections. Connect to
              multiple providers to access different models and capabilities.
            </p>
          </div>

          {/* Stats */}
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
                    {configuredProviders.length}
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
                    {configuredProviders.reduce(
                      (acc, cp) => acc + cp.api_key_count,
                      0
                    )}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Provider Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {providers.map((provider) => {
              const status = getProviderStatus(provider.id);

              return (
                <Card
                  key={provider.id}
                  className="p-6 cursor-pointer transition-all duration-200 hover:shadow-lg"
                  onClick={() => handleProviderSetup(provider)}
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
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                              status
                            )}`}
                          >
                            {getStatusText(status)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 flex-grow">
                      {provider.description || "No description available"}
                    </p>

                    {/* Action Button */}
                    <Button
                      variant={status === "connected" ? "secondary" : "primary"}
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
        </div>
      </div>

      {/* API Key Setup Modal */}
      <Modal
        isOpen={showApiKeyModal}
        onClose={() => setShowApiKeyModal(false)}
        title={`Setup ${selectedProvider?.display_name} API Key`}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              API Key Name
            </label>
            <Input
              type="text"
              placeholder="Enter a name for this API key"
              value={apiKeyForm.name}
              onChange={(value: string) =>
                setApiKeyForm((prev) => ({ ...prev, name: value }))
              }
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              API Key <span className="text-red-500">*</span>
            </label>
            <Input
              type="password"
              placeholder="Enter your API key"
              value={apiKeyForm.apiKey}
              onChange={(value: string) =>
                setApiKeyForm((prev) => ({ ...prev, apiKey: value }))
              }
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Project ID (Optional)
            </label>
            <Input
              type="text"
              placeholder="Enter project ID if applicable"
              value={apiKeyForm.projectId}
              onChange={(value: string) =>
                setApiKeyForm((prev) => ({ ...prev, projectId: value }))
              }
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => setShowApiKeyModal(false)}
            >
              Cancel
            </Button>
            <Button variant="primary" onClick={handleApiKeySubmit}>
              Add API Key
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};
