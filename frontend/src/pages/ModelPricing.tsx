import React, { useState, useEffect } from 'react';
import { MagicCard } from '../components/ui/magic-card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { apiService } from '../services/api';
import { ApiKey } from '../types';

interface ModelPricingItem {
  id: string;
  name: string;
  provider: string;
  type: 'Chat' | 'Embedding' | 'Image' | 'Audio';
  inputTokenPrice: number;
  outputTokenPrice: number;
  contextWindow: number;
  maxOutputTokens: number;
  features: string[];
}

const modelPricingData: ModelPricingItem[] = [
  // OpenAI Models
  {
    id: 'chatgpt-4o-latest',
    name: 'ChatGPT-4o Latest',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 5.0,
    outputTokenPrice: 15.0,
    contextWindow: 128000,
    maxOutputTokens: 16384,
    features: ['Vision', 'Function Calling', 'JSON Mode']
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 1.5,
    outputTokenPrice: 2.0,
    contextWindow: 16385,
    maxOutputTokens: 4096,
    features: ['Function Calling', 'JSON Mode']
  },
  {
    id: 'gpt-3.5-turbo-1106',
    name: 'GPT-3.5 Turbo 1106',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 1.0,
    outputTokenPrice: 2.0,
    contextWindow: 16385,
    maxOutputTokens: 4096,
    features: ['Function Calling', 'JSON Mode']
  },
  {
    id: 'gpt-4',
    name: 'GPT-4',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 30.0,
    outputTokenPrice: 60.0,
    contextWindow: 8192,
    maxOutputTokens: 4096,
    features: ['Advanced Reasoning', 'Function Calling']
  },
  {
    id: 'gpt-4-turbo',
    name: 'GPT-4 Turbo',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 10.0,
    outputTokenPrice: 30.0,
    contextWindow: 128000,
    maxOutputTokens: 4096,
    features: ['Vision', 'Function Calling', 'JSON Mode']
  },
  {
    id: 'gpt-4-0613',
    name: 'GPT-4 0613',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 30.0,
    outputTokenPrice: 60.0,
    contextWindow: 8192,
    maxOutputTokens: 4096,
    features: ['Function Calling']
  },
  {
    id: 'gpt-4-turbo-2024-04-09',
    name: 'GPT-4 Turbo 2024-04-09',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 10.0,
    outputTokenPrice: 30.0,
    contextWindow: 128000,
    maxOutputTokens: 4096,
    features: ['Vision', 'Function Calling', 'JSON Mode']
  },
  {
    id: 'gpt-4-1',
    name: 'GPT-4-1',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 2.5,
    outputTokenPrice: 5.0,
    contextWindow: 128000,
    maxOutputTokens: 16384,
    features: ['Latest Model', 'Function Calling']
  },
  {
    id: 'gpt-4-1-2025-01-14',
    name: 'GPT-4-1 2025-01-14',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 2.5,
    outputTokenPrice: 5.0,
    contextWindow: 128000,
    maxOutputTokens: 16384,
    features: ['Latest Model', 'Function Calling']
  },
  {
    id: 'gpt-4-mini',
    name: 'GPT-4 Mini',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 0.6,
    outputTokenPrice: 1.8,
    contextWindow: 128000,
    maxOutputTokens: 16384,
    features: ['Cost Effective', 'Function Calling']
  },
  {
    id: 'gpt-4-nano',
    name: 'GPT-4 Nano',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 0.1,
    outputTokenPrice: 0.4,
    contextWindow: 128000,
    maxOutputTokens: 16384,
    features: ['Ultra Cost Effective']
  },
  {
    id: 'gpt-4-nano-2025-01-14',
    name: 'GPT-4 Nano 2025-01-14',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 0.1,
    outputTokenPrice: 0.4,
    contextWindow: 128000,
    maxOutputTokens: 16384,
    features: ['Ultra Cost Effective']
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 2.5,
    outputTokenPrice: 10.0,
    contextWindow: 128000,
    maxOutputTokens: 16384,
    features: ['Multimodal', 'Vision', 'Audio']
  },
  {
    id: 'gpt-4o-2024-05-13',
    name: 'GPT-4o 2024-05-13',
    provider: 'OpenAI',
    type: 'Chat',
    inputTokenPrice: 5.0,
    outputTokenPrice: 15.0,
    contextWindow: 128000,
    maxOutputTokens: 4096,
    features: ['Multimodal', 'Vision', 'Audio']
  }
];

export default function ModelPricing() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'inputPrice' | 'outputPrice'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [connectedProviders, setConnectedProviders] = useState<string[]>([]);

  useEffect(() => {
    fetchConnectedProviders();
  }, []);

  const fetchConnectedProviders = async () => {
    try {
      const response = await apiService.getApiKeys();
      const keys = response.data || [];
      const providers = keys
        .filter((key: ApiKey) => key.is_active)
        .map((key: ApiKey) => key.provider);
      setConnectedProviders(Array.from(new Set(providers)));
    } catch (error) {
      console.error('Failed to fetch connected providers:', error);
    }
  };

  const filteredModels = modelPricingData
    .filter(model => {
      const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           model.provider.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesProvider = selectedProvider === 'all' || model.provider.toLowerCase() === selectedProvider.toLowerCase();
      const matchesType = selectedType === 'all' || model.type === selectedType;
      return matchesSearch && matchesProvider && matchesType;
    })
    .sort((a, b) => {
      let aValue, bValue;
      switch (sortBy) {
        case 'inputPrice':
          aValue = a.inputTokenPrice;
          bValue = b.inputTokenPrice;
          break;
        case 'outputPrice':
          aValue = a.outputTokenPrice;
          bValue = b.outputTokenPrice;
          break;
        default:
          aValue = a.name;
          bValue = b.name;
      }
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      }
      
      return sortOrder === 'asc' ? (aValue as number) - (bValue as number) : (bValue as number) - (aValue as number);
    });

  const providers = Array.from(new Set(modelPricingData.map(model => model.provider)));
  const types = Array.from(new Set(modelPricingData.map(model => model.type)));

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai': return '🤖';
      case 'anthropic': return '🧠';
      case 'google': return '🔍';
      default: return '🔧';
    }
  };

  const isProviderConnected = (provider: string) => {
    return connectedProviders.includes(provider.toLowerCase());
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Model Pricing</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Compare pricing and features across different AI models and providers
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Connected Providers: {connectedProviders.length}
              </span>
            </div>
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input
              placeholder="Search models..."
              value={searchTerm}
              onChange={setSearchTerm}
            />
            
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Providers</option>
              {providers.map(provider => (
                <option key={provider} value={provider}>
                  {getProviderIcon(provider)} {provider}
                </option>
              ))}
            </select>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              {types.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>

            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field as 'name' | 'inputPrice' | 'outputPrice');
                setSortOrder(order as 'asc' | 'desc');
              }}
              className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="name-asc">Name A-Z</option>
              <option value="name-desc">Name Z-A</option>
              <option value="inputPrice-asc">Input Price Low-High</option>
              <option value="inputPrice-desc">Input Price High-Low</option>
              <option value="outputPrice-asc">Output Price Low-High</option>
              <option value="outputPrice-desc">Output Price High-Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Model Grid */}
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-4 flex items-center justify-between">
          <p className="text-gray-600 dark:text-gray-400">
            Showing {filteredModels.length} models
          </p>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Prices shown per 1K tokens
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredModels.map((model) => (
            <MagicCard
              key={model.id}
              className="p-6 hover:shadow-lg transition-all duration-200"
              gradientColor={isProviderConnected(model.provider) ? "#10b981" : "#6b7280"}
              gradientOpacity={0.1}
            >
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getProviderIcon(model.provider)}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                        {model.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {model.provider}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end space-y-1">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      model.type === 'Chat' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                      model.type === 'Embedding' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                      model.type === 'Image' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' :
                      'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}>
                      {model.type}
                    </span>
                    {isProviderConnected(model.provider) && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        ✓ Connected
                      </span>
                    )}
                  </div>
                </div>

                {/* Pricing */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                      INPUT CUSTOM TOKENS
                    </p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      ${model.inputTokenPrice.toFixed(1)} 🔵
                    </p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                      OUTPUT CUSTOM TOKENS
                    </p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      ${model.outputTokenPrice.toFixed(1)} 🔵
                    </p>
                  </div>
                </div>

                {/* Specifications */}
                <div className="space-y-2 mb-4 flex-grow">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Context Window:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {model.contextWindow.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Max Output:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {model.maxOutputTokens.toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* Features */}
                <div className="mb-4">
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                    FEATURES
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {model.features.map((feature) => (
                      <span
                        key={feature}
                        className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-2 mt-auto">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    disabled={!isProviderConnected(model.provider)}
                  >
                    {isProviderConnected(model.provider) ? 'Try Model' : 'Setup Required'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="px-3"
                  >
                    ⚙️
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="px-3"
                  >
                    ▶️
                  </Button>
                </div>
              </div>
            </MagicCard>
          ))}
        </div>

        {filteredModels.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 text-6xl mb-4">🔍</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No models found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Try adjusting your search criteria or filters
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
