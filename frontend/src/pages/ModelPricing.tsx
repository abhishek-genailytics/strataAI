import React, { useState, useEffect } from "react";
import {
  Plus,
  Search,
  Copy,
  Play,
  MoreHorizontal,
  Eye,
  Check,
  Settings,
  ExternalLink,
  AlertCircle,
  Code,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Modal } from "../components/ui/Modal";
import { Input } from "../components/ui/Input";

// Helper function to mask email addresses
const maskEmail = (email: string): string => {
  if (!email) return "";
  const [username, domain] = email.split("@");
  if (!username || !domain) return email;

  const maskedUsername =
    username.length > 1
      ? `${username[0]}${"*".repeat(
          Math.max(0, username.length - 2)
        )}${username.slice(-1)}`
      : username;

  return `${maskedUsername}@${domain}`;
};

interface Provider {
  id: string;
  name: string;
  logo: string;
  connected: boolean;
  color: string;
  description: string;
  models?: number;
}

interface Model {
  id: string;
  name: string;
  type: string;
  inputCost: number;
  outputCost: number;
  provider: string;
  maxTokens?: number;
  features?: string[];
}

const providers: Provider[] = [
  {
    id: "openai",
    name: "OpenAI",
    logo: "⚡",
    connected: true,
    color: "bg-green-50 border-green-200 text-green-800",
    description: "GPT models for chat and completion",
    models: 16,
  },
  {
    id: "anthropic",
    name: "Anthropic",
    logo: "🧠",
    connected: false,
    color: "bg-orange-50 border-orange-200 text-orange-800",
    description: "Claude models for reasoning",
    models: 3,
  },
  {
    id: "google-vertex",
    name: "Google Vertex",
    logo: "🔵",
    connected: false,
    color: "bg-blue-50 border-blue-200 text-blue-800",
    description: "Vertex AI models",
    models: 5,
  },
  {
    id: "google-gemini",
    name: "Google Gemini",
    logo: "💎",
    connected: false,
    color: "bg-purple-50 border-purple-200 text-purple-800",
    description: "Gemini Pro models",
    models: 4,
  },
  {
    id: "azure-openai",
    name: "Azure OpenAI",
    logo: "☁️",
    connected: false,
    color: "bg-blue-50 border-blue-200 text-blue-800",
    description: "Azure-hosted OpenAI models",
    models: 8,
  },
  {
    id: "aws-bedrock",
    name: "AWS Bedrock",
    logo: "🪨",
    connected: false,
    color: "bg-amber-50 border-amber-200 text-amber-800",
    description: "Amazon Bedrock models",
    models: 12,
  },
  {
    id: "cohere",
    name: "Cohere",
    logo: "🔗",
    connected: false,
    color: "bg-teal-50 border-teal-200 text-teal-800",
    description: "Command and embed models",
    models: 6,
  },
  {
    id: "groq",
    name: "Groq",
    logo: "⚡",
    connected: false,
    color: "bg-red-50 border-red-200 text-red-800",
    description: "Ultra-fast inference",
    models: 8,
  },
  {
    id: "mistral",
    name: "Mistral AI",
    logo: "🌪️",
    connected: false,
    color: "bg-violet-50 border-violet-200 text-violet-800",
    description: "European AI models",
    models: 5,
  },
  {
    id: "ai21",
    name: "AI21",
    logo: "🦕",
    connected: false,
    color: "bg-emerald-50 border-emerald-200 text-emerald-800",
    description: "Jurassic models",
    models: 4,
  },
  {
    id: "anyscale",
    name: "Anyscale",
    logo: "📈",
    connected: false,
    color: "bg-cyan-50 border-cyan-200 text-cyan-800",
    description: "Scalable model deployment",
    models: 7,
  },
  {
    id: "deepinfra",
    name: "Deepinfra",
    logo: "🏗️",
    connected: false,
    color: "bg-slate-50 border-slate-200 text-slate-800",
    description: "Serverless inference",
    models: 9,
  },
  {
    id: "nomic",
    name: "Nomic",
    logo: "🏠",
    connected: false,
    color: "bg-gray-50 border-gray-200 text-gray-800",
    description: "Local deployment models",
    models: 3,
  },
  {
    id: "ollama",
    name: "Ollama",
    logo: "🦙",
    connected: false,
    color: "bg-yellow-50 border-yellow-200 text-yellow-800",
    description: "Run models locally",
    models: 15,
  },
  {
    id: "palm",
    name: "Palm",
    logo: "🌴",
    connected: false,
    color: "bg-green-50 border-green-200 text-green-800",
    description: "Google PaLM API",
    models: 4,
  },
  {
    id: "perplexity",
    name: "Perplexity AI",
    logo: "🔍",
    connected: false,
    color: "bg-indigo-50 border-indigo-200 text-indigo-800",
    description: "Search-augmented models",
    models: 6,
  },
  {
    id: "together",
    name: "Together AI",
    logo: "🤝",
    connected: false,
    color: "bg-pink-50 border-pink-200 text-pink-800",
    description: "Fast open-source inference",
    models: 11,
  },
  {
    id: "openrouter",
    name: "OpenRouter",
    logo: "🛣️",
    connected: false,
    color: "bg-lime-50 border-lime-200 text-lime-800",
    description: "Model routing service",
    models: 20,
  },
  {
    id: "self-hosted",
    name: "Self-Hosted",
    logo: "🏠",
    connected: false,
    color: "bg-neutral-50 border-neutral-200 text-neutral-800",
    description: "Your own model endpoints",
    models: 0,
  },
];

const openaiModels: Model[] = [
  {
    id: "chatgpt-4o-latest",
    name: "chatgpt-4o-latest",
    type: "Chat",
    inputCost: 5.0,
    outputCost: 15.0,
    provider: "openai",
    maxTokens: 128000,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-3.5-turbo",
    name: "gpt-3.5-turbo",
    type: "Chat",
    inputCost: 1.5,
    outputCost: 2.0,
    provider: "openai",
    maxTokens: 4096,
    features: ["Function Calling"],
  },
  {
    id: "gpt-3.5-turbo-0125",
    name: "gpt-3.5-turbo-0125",
    type: "Chat",
    inputCost: 0.5,
    outputCost: 1.5,
    provider: "openai",
    maxTokens: 16385,
    features: ["Function Calling"],
  },
  {
    id: "gpt-3.5-turbo-1106",
    name: "gpt-3.5-turbo-1106",
    type: "Chat",
    inputCost: 1.0,
    outputCost: 2.0,
    provider: "openai",
    maxTokens: 16385,
    features: ["Function Calling"],
  },
  {
    id: "gpt-3.5-turbo-16k",
    name: "gpt-3.5-turbo-16k",
    type: "Chat",
    inputCost: 3.0,
    outputCost: 4.0,
    provider: "openai",
    maxTokens: 16385,
  },
  {
    id: "gpt-4",
    name: "gpt-4",
    type: "Chat",
    inputCost: 30.0,
    outputCost: 60.0,
    provider: "openai",
    maxTokens: 8192,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-4-0613",
    name: "gpt-4-0613",
    type: "Chat",
    inputCost: 30.0,
    outputCost: 60.0,
    provider: "openai",
    maxTokens: 8192,
    features: ["Function Calling"],
  },
  {
    id: "gpt-4-turbo",
    name: "gpt-4-turbo",
    type: "Chat",
    inputCost: 10.0,
    outputCost: 30.0,
    provider: "openai",
    maxTokens: 128000,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-4-turbo-2024-04-09",
    name: "gpt-4-turbo-2024-04-09",
    type: "Chat",
    inputCost: 10.0,
    outputCost: 30.0,
    provider: "openai",
    maxTokens: 128000,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-4-1",
    name: "gpt-4-1",
    type: "Chat",
    inputCost: 2.0,
    outputCost: 8.0,
    provider: "openai",
    maxTokens: 200000,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-4-1-2025-04-14",
    name: "gpt-4-1-2025-04-14",
    type: "Chat",
    inputCost: 2.0,
    outputCost: 8.0,
    provider: "openai",
    maxTokens: 200000,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-4-1-mini",
    name: "gpt-4-1-mini",
    type: "Chat",
    inputCost: 0.4,
    outputCost: 1.6,
    provider: "openai",
    maxTokens: 128000,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-4-1-mini-2025-04-14",
    name: "gpt-4-1-mini-2025-04-14",
    type: "Chat",
    inputCost: 0.4,
    outputCost: 1.6,
    provider: "openai",
    maxTokens: 128000,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-4-1-nano",
    name: "gpt-4-1-nano",
    type: "Chat",
    inputCost: 0.1,
    outputCost: 0.4,
    provider: "openai",
    maxTokens: 128000,
    features: ["Function Calling"],
  },
  {
    id: "gpt-4-1-nano-2025-04-14",
    name: "gpt-4-1-nano-2025-04-14",
    type: "Chat",
    inputCost: 0.1,
    outputCost: 0.4,
    provider: "openai",
    maxTokens: 128000,
    features: ["Function Calling"],
  },
  {
    id: "gpt-4o",
    name: "gpt-4o",
    type: "Chat",
    inputCost: 2.5,
    outputCost: 10.0,
    provider: "openai",
    maxTokens: 128000,
    features: ["Vision", "Function Calling"],
  },
  {
    id: "gpt-4o-2024-05-13",
    name: "gpt-4o-2024-05-13",
    type: "Chat",
    inputCost: 5.0,
    outputCost: 15.0,
    provider: "openai",
    maxTokens: 128000,
    features: ["Vision", "Function Calling"],
  },
];

interface AddAccountFormData {
  name: string;
  apiKey: string;
  collaborators: Array<{ email: string; role: "Manager" | "User" }>;
  selectedModels: string[];
  showAdvanced: boolean;
}

export const ModelPricing: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());
  const [showAddAccountModal, setShowAddAccountModal] = useState(false);
  const [providerBeingAdded, setProviderBeingAdded] = useState<string | null>(
    null
  );
  const [formData, setFormData] = useState<AddAccountFormData>({
    name: "",
    apiKey: "",
    collaborators: [],
    selectedModels: [],
    showAdvanced: false,
  });
  const [showApiKey, setShowApiKey] = useState(false);

  const connectedProviders = providers.filter((p) => p.connected);
  const otherProviders = providers.filter((p) => !p.connected);

  const filteredModels = openaiModels.filter((model) =>
    model.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleProviderSelect = (providerId: string) => {
    const provider = providers.find((p) => p.id === providerId);
    if (provider?.connected) {
      setSelectedProvider(providerId);
    } else {
      setProviderBeingAdded(providerId);
      setFormData({
        name: "",
        apiKey: "",
        collaborators: [
          { email: maskEmail("abhishek@genailytics.com"), role: "Manager" },
          { email: "everyone", role: "User" },
        ],
        selectedModels: [],
        showAdvanced: false,
      });
      setShowAddAccountModal(true);
    }
  };

  const handleSelectAllModels = (checked: boolean) => {
    if (checked) {
      setSelectedModels(new Set(filteredModels.map((m) => m.id)));
    } else {
      setSelectedModels(new Set());
    }
  };

  const toggleModelSelection = (modelId: string) => {
    const newSelection = new Set(selectedModels);
    if (newSelection.has(modelId)) {
      newSelection.delete(modelId);
    } else {
      newSelection.add(modelId);
    }
    setSelectedModels(newSelection);
  };

  const handleAddAccount = () => {
    // Here you would implement the actual account addition logic
    console.log("Adding account:", formData);
    setShowAddAccountModal(false);
    setProviderBeingAdded(null);
    // Update the provider status to connected
    const providerIndex = providers.findIndex(
      (p) => p.id === providerBeingAdded
    );
    if (providerIndex !== -1) {
      providers[providerIndex].connected = true;
    }
  };

  const copyFQN = (model: string) => {
    navigator.clipboard.writeText(`openai/${model}`);
  };

  // If no providers are connected, show the provider selection grid
  if (connectedProviders.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <div className="flex items-center justify-between mb-8 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center space-x-3">
              <button className="text-slate-500 hover:text-slate-700 transition-colors">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                  />
                </svg>
              </button>
              <h1 className="text-2xl font-bold text-slate-900">Models</h1>
            </div>
          </div>

          {/* Hero Section */}
          <div className="text-center mb-12 max-w-3xl mx-auto">
            <div className="mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4">
                <span className="text-2xl text-white">🚀</span>
              </div>
            </div>
            <h2 className="text-4xl font-bold text-slate-900 mb-4 bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 bg-clip-text text-transparent">
              Start adding your Models here
            </h2>
            <p className="text-xl text-slate-600 leading-relaxed">
              Configure a new provider account by adding your API keys and start
              using Models
            </p>
          </div>

          {/* Provider Grid */}
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 lg:gap-6">
              {providers.map((provider) => (
                <Card
                  key={provider.id}
                  className="group relative overflow-hidden border-0 shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-1 bg-white/80 backdrop-blur-sm"
                  padding={false}
                  onClick={() => handleProviderSelect(provider.id)}
                >
                  <div className="p-6 text-center">
                    {/* Provider Logo */}
                    <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                      {provider.logo}
                    </div>

                    {/* Provider Name */}
                    <h3 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors duration-200 mb-2">
                      {provider.name}
                    </h3>

                    {/* Description */}
                    <p className="text-xs text-slate-500 mb-3 line-clamp-2">
                      {provider.description}
                    </p>

                    {/* Model Count */}
                    {provider.models && provider.models > 0 && (
                      <div className="text-xs text-slate-400">
                        {provider.models} models
                      </div>
                    )}

                    {/* Connection Status */}
                    {provider.connected && (
                      <div className="absolute top-2 right-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full shadow-sm"></div>
                      </div>
                    )}

                    {/* Hover Effect */}
                    <div className="absolute inset-0 bg-gradient-to-t from-blue-600/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Quick Setup Guide */}
          <div className="mt-16 max-w-4xl mx-auto">
            <Card className="bg-white/60 backdrop-blur-sm border-0 shadow-lg">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                    <span className="text-blue-500 mr-2">✨</span>
                    Quick Setup
                  </h3>
                  <ol className="space-y-3 text-slate-600">
                    <li className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        1
                      </div>
                      <span>
                        Choose your preferred AI provider from the grid above
                      </span>
                    </li>
                    <li className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        2
                      </div>
                      <span>
                        Click to setup and configure your API credentials
                      </span>
                    </li>
                    <li className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        3
                      </div>
                      <span>Test your connection in the playground</span>
                    </li>
                    <li className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        4
                      </div>
                      <span>Start building with powerful AI models</span>
                    </li>
                  </ol>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                    <span className="text-purple-500 mr-2">🎯</span>
                    Popular Combinations
                  </h3>
                  <div className="space-y-3 text-slate-600">
                    <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <span className="font-medium text-blue-900">
                        OpenAI + Anthropic:
                      </span>{" "}
                      Best for general use cases
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                      <span className="font-medium text-green-900">
                        Google + Mistral:
                      </span>{" "}
                      Great for multilingual tasks
                    </div>
                    <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                      <span className="font-medium text-orange-900">
                        Groq + Together:
                      </span>{" "}
                      Ultra-fast inference
                    </div>
                    <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                      <span className="font-medium text-purple-900">
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
    );
  }

  // Main connected view
  return (
    <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="flex items-center justify-between mb-8 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <h1 className="text-3xl font-bold text-slate-900">Models</h1>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
          {/* Left Sidebar - Provider Selection */}
          <div className="xl:col-span-1 space-y-6">
            {/* Connected Providers */}
            <Card className="bg-white shadow-lg border border-gray-200">
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                    Connected Providers
                  </h3>
                </div>
                <div className="space-y-2">
                  {connectedProviders.map((provider) => (
                    <button
                      key={provider.id}
                      onClick={() => setSelectedProvider(provider.id)}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200 group ${
                        selectedProvider === provider.id
                          ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg"
                          : "hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <span className="text-xl">{provider.logo}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">
                          {provider.name}
                        </div>
                        {provider.models && (
                          <div
                            className={`text-xs ${
                              selectedProvider === provider.id
                                ? "text-blue-100"
                                : "text-slate-500"
                            }`}
                          >
                            {provider.models} models
                          </div>
                        )}
                      </div>
                      {selectedProvider === provider.id && (
                        <Check className="w-4 h-4 flex-shrink-0" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </Card>

            {/* Other Providers */}
            <Card className="bg-white shadow-lg border border-gray-200">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                  Other Providers
                </h3>
                <div className="grid grid-cols-2 xl:grid-cols-1 gap-3">
                  {otherProviders.slice(0, 8).map((provider) => (
                    <button
                      key={provider.id}
                      onClick={() => handleProviderSelect(provider.id)}
                      className="flex flex-col xl:flex-row items-center xl:items-start p-4 rounded-xl border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 transition-all duration-200 group text-center xl:text-left"
                    >
                      <span className="text-2xl xl:text-xl xl:mr-3 mb-2 xl:mb-0 group-hover:scale-110 transition-transform duration-200">
                        {provider.logo}
                      </span>
                      <div className="xl:flex-1 min-w-0">
                        <div className="font-medium text-slate-900 text-sm xl:truncate">
                          {provider.name}
                        </div>
                        {provider.models && provider.models > 0 && (
                          <div className="text-xs text-slate-500 mt-1">
                            {provider.models} models
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
                {otherProviders.length > 8 && (
                  <button className="w-full text-sm text-blue-600 hover:text-blue-800 py-2">
                    View all {otherProviders.length} providers →
                  </button>
                )}
              </div>
            </Card>
          </div>

          {/* Main Content - Models Table */}
          <div className="xl:col-span-3">
            {selectedProvider === 'openai' && (
              <Card className="bg-white shadow-lg border border-gray-200">
                {/* Account Header */}
                <div className="border-b border-slate-200 pb-6 mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-slate-900 flex items-center">
                      <span className="text-2xl mr-3">⚡</span>
                      OpenAI Accounts
                    </h2>
                    <Button
                      onClick={() => handleProviderSelect("openai")}
                      className="bg-gradient-to-r from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 text-white shadow-lg border-0"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add OpenAI Account
                    </Button>
                  </div>

                  {/* Account Info */}
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="flex items-center space-x-2">
                      <div className="flex -space-x-1">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-semibold text-sm shadow-lg">
                          A
                        </div>
                        <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-semibold text-sm shadow-lg">
                          E
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-slate-900">
                          openai
                        </div>
                        <div className="text-xs text-slate-500">
                          2 collaborators
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Active
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyFQN("openai")}
                      className="border-slate-200 hover:border-slate-300"
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy FQN
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-slate-200 hover:border-slate-300"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Model
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-slate-200 hover:border-slate-300"
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-slate-500"
                    >
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Search and Selection Controls */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center space-x-2 cursor-pointer group">
                      <input
                        type="checkbox"
                        className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500 focus:ring-2"
                        checked={
                          selectedModels.size > 0 &&
                          selectedModels.size === filteredModels.length
                        }
                        ref={(el) => {
                          if (el) {
                            el.indeterminate =
                              selectedModels.size > 0 &&
                              selectedModels.size < filteredModels.length;
                          }
                        }}
                        onChange={(e) =>
                          handleSelectAllModels(e.target.checked)
                        }
                      />
                      <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900">
                        {selectedModels.size > 0
                          ? `Selected ${selectedModels.size}`
                          : "Select All"}
                      </span>
                    </label>
                    {selectedModels.size > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedModels(new Set())}
                        className="text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                      >
                        Clear Selection
                      </Button>
                    )}
                  </div>

                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Search models..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm transition-shadow"
                    />
                  </div>
                </div>

                {/* Models Table */}
                <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-gradient-to-r from-slate-50 to-slate-100">
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Model
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Input Cost/1M Tokens
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Output Cost/1M Tokens
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {filteredModels.map((model, index) => (
                        <tr
                          key={model.id}
                          className={`hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-purple-50/50 transition-all duration-200 ${
                            selectedModels.has(model.id)
                              ? "bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500"
                              : ""
                          }`}
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500 mr-4"
                                checked={selectedModels.has(model.id)}
                                onChange={() => toggleModelSelection(model.id)}
                              />
                              <div>
                                <div className="font-semibold text-slate-900">
                                  {model.name}
                                </div>
                                {model.features &&
                                  model.features.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {model.features.map((feature) => (
                                        <span
                                          key={feature}
                                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700"
                                        >
                                          {feature}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                              💬 {model.type}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <span className="font-bold text-slate-900">
                                ${model.inputCost}
                              </span>
                              <span className="text-slate-500 ml-1 text-sm">
                                🔵
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <span className="font-bold text-slate-900">
                                ${model.outputCost}
                              </span>
                              <span className="text-slate-500 ml-1 text-sm">
                                🔵
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-slate-500 hover:text-blue-600"
                              >
                                <Code className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-slate-500 hover:text-green-600"
                              >
                                <Play className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-slate-500 hover:text-slate-700"
                              >
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Footer Stats */}
                <div className="mt-6 flex items-center justify-between text-sm text-slate-500">
                  <span>Showing {filteredModels.length} models</span>
                  <div className="flex items-center space-x-4">
                    <span>Total cost range: $0.1 - $60 per 1M tokens</span>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>

      {/* Add Account Modal */}
      <Modal
        isOpen={showAddAccountModal}
        onClose={() => {
          setShowAddAccountModal(false);
          setProviderBeingAdded(null);
        }}
        title={`Setup ${
          providers.find((p) => p.id === providerBeingAdded)?.name
        } account and manage models`}
        size="xl"
      >
        <div className="space-y-6">
          {/* Name Field */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Name <span className="text-red-500">*</span>
            </label>
            <Input
              placeholder="Enter Name"
              value={formData.name}
              onChange={(value) =>
                setFormData((prev) => ({ ...prev, name: value }))
              }
              className="bg-white border-slate-300 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          {/* Collaborators */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-semibold text-slate-700">
                Collaborators
                <span className="text-slate-500 font-normal ml-1">
                  (Optional)
                </span>
              </label>
              <div className="flex items-center space-x-3">
                <span className="text-xs text-slate-500">
                  List of users who have access to this provider account
                </span>
                <div className="relative">
                  <div className="w-11 h-6 bg-blue-600 rounded-full p-1 cursor-pointer">
                    <div className="w-4 h-4 bg-white rounded-full transform translate-x-5 transition-transform"></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {formData.collaborators.map((collab, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                      {collab.email[0]?.toUpperCase()}
                    </div>
                    <span className="text-sm font-medium text-slate-700">
                      {collab.email}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${
                        collab.role === "Manager"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {collab.role}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-slate-400 hover:text-red-600"
                    >
                      ×
                    </Button>
                  </div>
                </div>
              ))}

              <div className="flex items-center space-x-3">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Collaborators
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                >
                  View Permission Details
                  <svg
                    className="w-3 h-3 ml-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </Button>
              </div>
            </div>
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              OpenAI API Key <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Input
                type={showApiKey ? "text" : "password"}
                placeholder="Enter API Key"
                value={formData.apiKey}
                onChange={(value) =>
                  setFormData((prev) => ({ ...prev, apiKey: value }))
                }
                className="bg-white border-slate-300 focus:border-blue-500 focus:ring-blue-500 pr-12"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <Eye className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Models Selection */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-semibold text-slate-700">
                Models <span className="text-red-500">*</span>
              </label>
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm" className="text-blue-600">
                  <input type="checkbox" className="mr-2" />
                  Select All
                </Button>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search"
                    className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
                  />
                </div>
              </div>
            </div>

            <div className="max-h-64 overflow-y-auto border border-slate-200 rounded-xl bg-white">
              <div className="divide-y divide-slate-100">
                {[
                  { name: "chatgpt-4o-latest", type: "Chat" },
                  { name: "gpt-3.5-turbo-0125", type: "Chat" },
                  { name: "gpt-3.5-turbo-16k", type: "Chat" },
                  { name: "gpt-4-0613", type: "Chat" },
                  { name: "gpt-3.5-turbo", type: "Chat" },
                  { name: "gpt-3.5-turbo-1106", type: "Chat" },
                  { name: "gpt-4", type: "Chat" },
                  { name: "gpt-4-turbo", type: "Chat" },
                ].map((model, index) => (
                  <label
                    key={index}
                    className="flex items-center justify-between p-4 hover:bg-slate-50 cursor-pointer group transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                        checked={formData.selectedModels.includes(model.name)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData((prev) => ({
                              ...prev,
                              selectedModels: [
                                ...prev.selectedModels,
                                model.name,
                              ],
                            }));
                          } else {
                            setFormData((prev) => ({
                              ...prev,
                              selectedModels: prev.selectedModels.filter(
                                (m) => m !== model.name
                              ),
                            }));
                          }
                        }}
                      />
                      <div>
                        <div className="font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                          {model.name}
                        </div>
                        <div className="text-xs text-slate-500">
                          {model.type}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-slate-500 group-hover:text-slate-700 transition-colors">
                      {model.type}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Advanced Fields Toggle */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
              checked={formData.showAdvanced}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  showAdvanced: e.target.checked,
                }))
              }
            />
            <span className="text-sm font-medium text-slate-700">
              Show advanced fields
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-6 border-t border-slate-200">
            <Button
              variant="outline"
              onClick={() => setShowAddAccountModal(false)}
              className="border-slate-300 text-slate-700 hover:border-slate-400 hover:bg-slate-50"
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              className="border-slate-300 text-slate-700 hover:border-slate-400 hover:bg-slate-50"
            >
              Apply using YAML
            </Button>
            <Button
              onClick={handleAddAccount}
              className="bg-gradient-to-r from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 text-white shadow-lg border-0"
            >
              Add {providers.find((p) => p.id === providerBeingAdded)?.name}{" "}
              Account
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
