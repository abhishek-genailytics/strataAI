import React, { useState, useMemo } from "react";
import { Plus, Search, Copy, Play, MoreHorizontal, Eye } from "lucide-react";

// Helper function to mask email addresses
const maskEmail = (email: string): string => {
  if (!email) return '';
  const [username, domain] = email.split('@');
  if (!username || !domain) return email;
  
  const maskedUsername = username.length > 1 
    ? `${username[0]}${'*'.repeat(Math.max(0, username.length - 2))}${username.slice(-1)}`
    : username;
    
  return `${maskedUsername}@${domain}`;
};

interface Provider {
  id: string;
  name: string;
  logo: string;
  connected: boolean;
}

interface Model {
  id: string;
  name: string;
  type: string;
  inputCost: number;
  outputCost: number;
  provider: string;
}

const providers: Provider[] = [
  { id: "openai", name: "OpenAI", logo: "🔴", connected: true },
  { id: "anthropic", name: "Anthropic", logo: "🟠", connected: false },
  { id: "google", name: "Google Vertex", logo: "🔵", connected: false },
  { id: "azure", name: "Azure OpenAI", logo: "🟦", connected: false },
  { id: "bedrock", name: "AWS Bedrock", logo: "🟧", connected: false },
  { id: "cohere", name: "Cohere", logo: "🟪", connected: false },
  { id: "mistral", name: "Mistral AI", logo: "🟨", connected: false },
  { id: "groq", name: "Groq", logo: "🟥", connected: false },
  { id: "together", name: "Together AI", logo: "🟫", connected: false },
  { id: "ollama", name: "Ollama", logo: "🟩", connected: false },
  { id: "perplexity", name: "Perplexity AI", logo: "🟦", connected: false },
  { id: "nomic", name: "Nomic", logo: "🟨", connected: false },
  { id: "ai21", name: "AI21", logo: "🟪", connected: false },
  { id: "anyscale", name: "Anyscale", logo: "🟧", connected: false },
  { id: "deepinfra", name: "Deepinfra", logo: "🟩", connected: false },
  { id: "palm", name: "Palm", logo: "🟥", connected: false },
  { id: "databricks", name: "Databricks", logo: "🟦", connected: false },
  { id: "openrouter", name: "OpenRouter", logo: "🟨", connected: false },
  {
    id: "self-hosted",
    name: "Self-Hosted Model",
    logo: "🟫",
    connected: false,
  },
];

const openaiModels: Model[] = [
  {
    id: "gpt-4o",
    name: "gpt-4o",
    type: "Chat",
    inputCost: 2.5,
    outputCost: 10,
    provider: "openai",
  },
  {
    id: "gpt-4o-mini",
    name: "gpt-4o-mini",
    type: "Chat",
    inputCost: 0.15,
    outputCost: 0.6,
    provider: "openai",
  },
  {
    id: "gpt-4o-2024-11-20",
    name: "gpt-4o-2024-11-20",
    type: "Chat",
    inputCost: 2.5,
    outputCost: 10,
    provider: "openai",
  },
  {
    id: "gpt-4-turbo",
    name: "gpt-4-turbo",
    type: "Chat",
    inputCost: 10,
    outputCost: 30,
    provider: "openai",
  },
  {
    id: "gpt-4",
    name: "gpt-4",
    type: "Chat",
    inputCost: 30,
    outputCost: 60,
    provider: "openai",
  },
  {
    id: "gpt-3.5-turbo",
    name: "gpt-3.5-turbo",
    type: "Chat",
    inputCost: 1.5,
    outputCost: 2,
    provider: "openai",
  },
  {
    id: "gpt-3.5-turbo-0125",
    name: "gpt-3.5-turbo-0125",
    type: "Chat",
    inputCost: 0.5,
    outputCost: 1.5,
    provider: "openai",
  },
  {
    id: "gpt-3.5-turbo-1106",
    name: "gpt-3.5-turbo-1106",
    type: "Chat",
    inputCost: 1,
    outputCost: 2,
    provider: "openai",
  },
  {
    id: "gpt-3.5-turbo-16k",
    name: "gpt-3.5-turbo-16k",
    type: "Chat",
    inputCost: 3,
    outputCost: 4,
    provider: "openai",
  },
  {
    id: "gpt-4-0613",
    name: "gpt-4-0613",
    type: "Chat",
    inputCost: 30,
    outputCost: 60,
    provider: "openai",
  },
  {
    id: "gpt-4-turbo-2024-04-09",
    name: "gpt-4-turbo-2024-04-09",
    type: "Chat",
    inputCost: 10,
    outputCost: 30,
    provider: "openai",
  },
  {
    id: "gpt-4-1",
    name: "gpt-4-1",
    type: "Chat",
    inputCost: 2,
    outputCost: 8,
    provider: "openai",
  },
  {
    id: "gpt-4-1-2025-04-14",
    name: "gpt-4-1-2025-04-14",
    type: "Chat",
    inputCost: 2,
    outputCost: 8,
    provider: "openai",
  },
  {
    id: "gpt-4-1-mini",
    name: "gpt-4-1-mini",
    type: "Chat",
    inputCost: 0.4,
    outputCost: 1.6,
    provider: "openai",
  },
  {
    id: "gpt-4-1-mini-2025-04-14",
    name: "gpt-4-1-mini-2025-04-14",
    type: "Chat",
    inputCost: 0.4,
    outputCost: 1.6,
    provider: "openai",
  },
  {
    id: "gpt-4-1-nano",
    name: "gpt-4-1-nano",
    type: "Chat",
    inputCost: 0.1,
    outputCost: 0.4,
    provider: "openai",
  },
  {
    id: "gpt-4-1-nano-2025-04-14",
    name: "gpt-4-1-nano-2025-04-14",
    type: "Chat",
    inputCost: 0.1,
    outputCost: 0.4,
    provider: "openai",
  },
  {
    id: "gpt-40",
    name: "gpt-40",
    type: "Chat",
    inputCost: 2.5,
    outputCost: 10,
    provider: "openai",
  },
  {
    id: "gpt-40-2024-05-13",
    name: "gpt-40-2024-05-13",
    type: "Chat",
    inputCost: 5,
    outputCost: 15,
    provider: "openai",
  },
];

export const ModelPricing: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState("models");
  const [selectedModelIds, setSelectedModelIds] = useState<Set<string>>(new Set());
  const [showProviderGrid, setShowProviderGrid] = useState(false);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState("openai");

  const filteredModels = openaiModels.filter((model) =>
    model.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const connectedProviders = providers.filter((p) => p.connected);

  // Show provider grid if no providers are connected
  if (connectedProviders.length === 0 || showProviderGrid) {
    return (
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <button className="text-gray-500 hover:text-gray-700">
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
            <h1 className="text-2xl font-bold text-gray-900">Models</h1>
          </div>
        </div>

        {/* Instructions */}
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Start adding your Models here
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Configure a new provider account by adding your API keys and start
            using Models
          </p>
        </div>

        {/* Provider Grid */}
        <div className="grid grid-cols-5 gap-6 max-w-6xl mx-auto">
          {providers.map((provider) => (
            <button
              key={provider.id}
              onClick={() => {
                if (provider.id === "openai") {
                  setSelectedProvider(provider.id);
                  setShowProviderGrid(false);
                } else {
                  setSelectedProvider(provider.id);
                  setShowAddAccount(true);
                }
              }}
              className="flex flex-col items-center p-6 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all duration-200 group"
            >
              <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-200">
                {provider.logo}
              </div>
              <h3 className="text-sm font-medium text-gray-900 text-center group-hover:text-blue-600 transition-colors">
                {provider.name}
              </h3>
            </button>
          ))}
        </div>

      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-3">
          <button className="text-gray-500 hover:text-gray-700">
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
          <h1 className="text-2xl font-bold text-gray-900">Models</h1>
        </div>

        <button
          onClick={() => setShowProviderGrid(true)}
          className="text-sm text-blue-600 hover:text-blue-700 px-3 py-1 rounded hover:bg-blue-50"
        >
          View All Providers
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar - Provider Selection */}
        <div className="lg:col-span-1">
          {/* Connected Providers */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              CONNECTED PROVIDERS
            </h3>
            <div className="space-y-2">
              {providers
                .filter((p) => p.connected)
                .map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                      selectedProvider === provider.id
                        ? "bg-blue-50 border border-blue-200"
                        : "hover:bg-gray-50"
                    }`}
                  >
                    <span className="text-2xl">{provider.logo}</span>
                    <span className="font-medium text-gray-900">
                      {provider.name}
                    </span>
                  </button>
                ))}
            </div>
          </div>

          {/* Other Providers */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              OTHER PROVIDERS
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {providers
                .filter((p) => !p.connected)
                .map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setShowAddAccount(true)}
                    className="flex flex-col items-center p-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors"
                  >
                    <span className="text-2xl mb-1">{provider.logo}</span>
                    <span className="text-xs text-gray-600 text-center">
                      {provider.name}
                    </span>
                  </button>
                ))}
            </div>
          </div>
        </div>

        {/* Right Content - Models Table */}
        <div className="lg:col-span-3">
          {/* OpenAI Accounts Header */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                OpenAI Accounts
              </h2>
              <button
                onClick={() => setShowAddAccount(true)}
                className="bg-black text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Add OpenAI Account</span>
              </button>
            </div>

            {/* Account Info */}
            <div className="flex items-center space-x-3 mb-4">
              <div className="flex space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
                  A
                </div>
                <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-white font-medium">
                  E
                </div>
              </div>
              <span className="text-sm text-gray-600">openai</span>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3 mb-4">
              <button className="text-sm text-gray-600 hover:text-gray-900 flex items-center space-x-1">
                <Copy className="w-4 h-4" />
                <span>Copy FQN</span>
              </button>
              <button className="text-sm text-gray-600 hover:text-gray-900 flex items-center space-x-1">
                <Plus className="w-4 h-4" />
                <span>Add Model</span>
              </button>
              <button className="text-sm text-gray-600 hover:text-gray-900 flex items-center space-x-1">
                <span>Edit</span>
              </button>
              <button className="text-sm text-gray-600 hover:text-gray-900">
                <MoreHorizontal className="w-4 h-4" />
              </button>
            </div>

            {/* Search and Select All */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={selectedModelIds.size > 0 && selectedModelIds.size === filteredModels.length}
                    ref={(el) => {
                      if (el) {
                        el.indeterminate = selectedModelIds.size > 0 && selectedModelIds.size < filteredModels.length;
                      }
                    }}
                    onChange={(e) => {
                      if (e.target.checked) {
                        // Select all filtered models
                        setSelectedModelIds(new Set(filteredModels.map(model => model.id)));
                      } else {
                        // Clear selection
                        setSelectedModelIds(new Set());
                      }
                    }}
                  />
                  <span className="text-sm text-gray-700">
                    {selectedModelIds.size > 0 ? `Selected ${selectedModelIds.size}` : 'Select All'}
                  </span>
                </label>
                {selectedModelIds.size > 0 && (
                  <button 
                    onClick={() => setSelectedModelIds(new Set())}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Clear
                  </button>
                )}
              </div>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Models Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      MODEL
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      TYPE
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      INPUT COST/1M TOKENS
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      OUTPUT COST/1M TOKENS
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ACTIONS
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredModels.map((model) => (
                    <tr 
                      key={model.id} 
                      className={`hover:bg-gray-50 ${selectedModelIds.has(model.id) ? 'bg-blue-50' : ''}`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            className="h-4 w-4 text-blue-600 rounded border-gray-300 mr-3"
                            checked={selectedModelIds.has(model.id)}
                            onChange={() => {
                              const newSelected = new Set(selectedModelIds);
                              if (newSelected.has(model.id)) {
                                newSelected.delete(model.id);
                              } else {
                                newSelected.add(model.id);
                              }
                              setSelectedModelIds(newSelected);
                            }}
                          />
                          <span className="font-medium text-gray-900">
                            {model.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {model.type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${model.inputCost}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${model.outputCost}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center space-x-2">
                          <button className="text-gray-400 hover:text-gray-600">
                            <span className="text-xs">&lt;/&gt;</span>
                          </button>
                          <button className="text-gray-400 hover:text-gray-600">
                            <Play className="w-4 h-4" />
                          </button>
                          <button className="text-gray-400 hover:text-gray-600">
                            <MoreHorizontal className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Add OpenAI Account Modal */}
      {showAddAccount && selectedProvider && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Add {providers.find(p => p.id === selectedProvider)?.name || 'Provider'} Account
                </h2>
                <button
                  onClick={() => setShowAddAccount(false)}
                  className="text-gray-400 hover:text-gray-600"
                  aria-label="Close modal"
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

            <div className="space-y-6">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name*
                </label>
                <input
                  type="text"
                  placeholder="Enter Name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Collaborators */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Collaborators (Optional)
                  </label>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      List of users who have access to this provider account
                    </span>
                    <div className="w-12 h-6 bg-purple-600 rounded-full relative">
                      <div className="w-5 h-5 bg-white rounded-full absolute top-0.5 right-0.5 transition-transform"></div>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700" title="Masked collaborator email">
                      {maskEmail('abhishek@genailytics.com')}
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        Manager
                      </span>
                      <button className="text-gray-400 hover:text-gray-600">
                        ×
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">everyone</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                        User
                      </span>
                      <button className="text-gray-400 hover:text-gray-600">
                        ×
                      </button>
                    </div>
                  </div>
                </div>
                <button className="text-sm text-blue-600 hover:text-blue-700 mt-2">
                  + Add Collaborators
                </button>
                <button className="text-sm text-blue-600 hover:text-blue-700 ml-4">
                  View Permission Details ▼
                </button>
              </div>

              {/* API Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {providers.find(p => p.id === selectedProvider)?.name || 'Provider'} API Key*
                </label>
                <div className="relative">
                  <input
                    type="password"
                    placeholder="Enter API Key"
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Models */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Models*
                </label>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">
                      chatgpt-4o-latest • Chat
                    </span>
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                    />
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">
                      gpt-3.5-turbo-0125 • Chat
                    </span>
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                    />
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">
                      gpt-3.5-turbo-16k • Chat
                    </span>
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                    />
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">
                      gpt-4-0613 • Chat
                    </span>
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                    />
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">
                      gpt-3.5-turbo • Chat
                    </span>
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                    />
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">
                      gpt-3.5-turbo-1106 • Chat
                    </span>
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                    />
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">gpt-4 • Chat</span>
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                    />
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">
                      gpt-4-turbo • Chat
                    </span>
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                    />
                  </div>
                </div>
              </div>

              {/* Advanced Fields */}
              <div className="flex items-center space-x-2">
                <input type="checkbox" className="rounded border-gray-300" />
                <span className="text-sm text-gray-700">
                  Show advanced fields
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  onClick={() => setShowAddAccount(false)}
                  className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                  Apply using YAML
                </button>
                <button 
                  className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800"
                  onClick={() => {
                    // Handle add account logic here
                    setShowAddAccount(false);
                  }}
                >
                  Add {providers.find(p => p.id === selectedProvider)?.name || 'Provider'} Account
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
