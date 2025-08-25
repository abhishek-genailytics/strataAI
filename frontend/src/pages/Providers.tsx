import React, { useState, useEffect } from 'react';
import { MagicCard } from '../components/ui/magic-card';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { apiService } from '../services/api';
import { ApiKey } from '../types';

interface Provider {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: 'connected' | 'disconnected' | 'setup';
  models?: string[];
  pricing?: string;
}

const providers: Provider[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4, GPT-3.5 Turbo, and more advanced language models',
    icon: '🤖',
    status: 'disconnected',
    models: ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
    pricing: 'From $0.01/1K tokens'
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude 3 family of models for advanced reasoning',
    icon: '🧠',
    status: 'disconnected',
    models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
    pricing: 'From $0.25/1K tokens'
  },
  {
    id: 'google',
    name: 'Google Vertex AI',
    description: 'Gemini Pro and other Google AI models',
    icon: '🔍',
    status: 'disconnected',
    models: ['gemini-pro', 'gemini-pro-vision'],
    pricing: 'From $0.125/1K tokens'
  },
  {
    id: 'google-gemini',
    name: 'Google Gemini',
    description: 'Direct access to Gemini models via Google AI',
    icon: '💎',
    status: 'disconnected',
    models: ['gemini-1.5-pro', 'gemini-1.5-flash'],
    pricing: 'From $0.075/1K tokens'
  },
  {
    id: 'azure-openai',
    name: 'Azure OpenAI',
    description: 'OpenAI models hosted on Microsoft Azure',
    icon: '☁️',
    status: 'disconnected',
    models: ['gpt-4', 'gpt-35-turbo'],
    pricing: 'Enterprise pricing'
  },
  {
    id: 'azure-foundry',
    name: 'Azure AI Foundry',
    description: 'Microsoft\'s AI model marketplace and platform',
    icon: '🏗️',
    status: 'disconnected',
    models: ['phi-3', 'llama-2'],
    pricing: 'Variable pricing'
  },
  {
    id: 'aws-bedrock',
    name: 'AWS Bedrock',
    description: 'Amazon\'s managed AI service with multiple providers',
    icon: '🪨',
    status: 'disconnected',
    models: ['claude-3', 'titan', 'jurassic-2'],
    pricing: 'Pay-per-use'
  },
  {
    id: 'cohere',
    name: 'Cohere',
    description: 'Command and Embed models for enterprise applications',
    icon: '🔗',
    status: 'disconnected',
    models: ['command-r', 'command-r-plus', 'embed-v3'],
    pricing: 'From $0.15/1K tokens'
  },
  {
    id: 'databricks',
    name: 'Databricks',
    description: 'DBRX and other models for data-driven applications',
    icon: '🧱',
    status: 'disconnected',
    models: ['dbrx-instruct', 'dolly-v2'],
    pricing: 'Enterprise pricing'
  },
  {
    id: 'groq',
    name: 'Groq',
    description: 'Ultra-fast inference for Llama, Mixtral, and Gemma',
    icon: '⚡',
    status: 'disconnected',
    models: ['llama-3-70b', 'mixtral-8x7b', 'gemma-7b'],
    pricing: 'From $0.27/1K tokens'
  },
  {
    id: 'mistral',
    name: 'Mistral AI',
    description: 'Mistral 7B, Mixtral, and other European AI models',
    icon: '🌪️',
    status: 'disconnected',
    models: ['mistral-large', 'mixtral-8x7b', 'mistral-7b'],
    pricing: 'From $0.25/1K tokens'
  },
  {
    id: 'ai21',
    name: 'AI21 Labs',
    description: 'Jurassic-2 models for text generation and analysis',
    icon: '🦕',
    status: 'disconnected',
    models: ['j2-ultra', 'j2-mid', 'j2-light'],
    pricing: 'From $0.125/1K tokens'
  },
  {
    id: 'anyscale',
    name: 'Anyscale',
    description: 'Scalable deployment of open-source models',
    icon: '📈',
    status: 'disconnected',
    models: ['llama-2-70b', 'codellama-34b'],
    pricing: 'From $0.15/1K tokens'
  },
  {
    id: 'deepinfra',
    name: 'DeepInfra',
    description: 'Serverless inference for popular open-source models',
    icon: '🏗️',
    status: 'disconnected',
    models: ['llama-2-70b', 'falcon-40b'],
    pricing: 'From $0.27/1K tokens'
  },
  {
    id: 'nomic',
    name: 'Nomic AI',
    description: 'GPT4All and embedding models for local deployment',
    icon: '🏠',
    status: 'disconnected',
    models: ['gpt4all-j', 'nomic-embed-text'],
    pricing: 'Open source'
  },
  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Run large language models locally on your machine',
    icon: '🦙',
    status: 'disconnected',
    models: ['llama2', 'codellama', 'mistral'],
    pricing: 'Free (local)'
  },
  {
    id: 'palm',
    name: 'PaLM API',
    description: 'Google\'s Pathways Language Model API',
    icon: '🌴',
    status: 'disconnected',
    models: ['text-bison', 'chat-bison'],
    pricing: 'From $0.125/1K tokens'
  },
  {
    id: 'perplexity',
    name: 'Perplexity AI',
    description: 'Search-augmented language models for accurate responses',
    icon: '🔍',
    status: 'disconnected',
    models: ['pplx-7b-online', 'pplx-70b-online'],
    pricing: 'From $0.20/1K tokens'
  },
  {
    id: 'together',
    name: 'Together AI',
    description: 'Fast inference for open-source models at scale',
    icon: '🤝',
    status: 'disconnected',
    models: ['llama-2-70b', 'falcon-40b', 'redpajama-7b'],
    pricing: 'From $0.20/1K tokens'
  },
  {
    id: 'self-hosted',
    name: 'Self-Hosted',
    description: 'Connect your own model endpoints and deployments',
    icon: '🏠',
    status: 'disconnected',
    models: ['Custom endpoints'],
    pricing: 'Your infrastructure'
  }
];

export default function Providers() {
  const [providerStatuses, setProviderStatuses] = useState<Record<string, Provider['status']>>({});
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    try {
      setLoading(true);
      const response = await apiService.getApiKeys();
      const keys = response.data || [];
      setApiKeys(keys);
      
      // Update provider statuses based on API keys
      const statuses: Record<string, Provider['status']> = {};
      providers.forEach(provider => {
        const hasKey = keys.some((key: ApiKey) => key.provider === provider.id && key.is_active);
        statuses[provider.id] = hasKey ? 'connected' : 'disconnected';
      });
      setProviderStatuses(statuses);
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderSetup = (providerId: string) => {
    // Navigate to API key setup for this provider
    window.location.href = `/api-keys?provider=${providerId}`;
  };

  const getStatusColor = (status: Provider['status']) => {
    switch (status) {
      case 'connected':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'setup':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusText = (status: Provider['status']) => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'setup':
        return 'Setup Required';
      default:
        return 'Not Connected';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading providers...</p>
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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            AI Providers
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Configure and manage your AI provider connections. Connect to multiple providers to access different models and capabilities.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <span className="text-2xl">🔗</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Connected Providers</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {Object.values(providerStatuses).filter(status => status === 'connected').length}
                </p>
              </div>
            </div>
          </Card>
          
          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                <span className="text-2xl">🤖</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Available Models</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {providers.reduce((acc, provider) => acc + (provider.models?.length || 0), 0)}
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
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">API Keys</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {apiKeys.filter(key => key.is_active).length}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Provider Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {providers.map((provider) => {
            const status = providerStatuses[provider.id] || provider.status;
            
            return (
              <MagicCard
                key={provider.id}
                className="p-6 cursor-pointer transition-all duration-200 hover:shadow-lg"
                gradientColor="#3b82f6"
                gradientOpacity={0.1}
                onClick={() => handleProviderSetup(provider.id)}
              >
                <div className="flex flex-col h-full">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      <span className="text-3xl mr-3">{provider.icon}</span>
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                          {provider.name}
                        </h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(status)}`}>
                          {getStatusText(status)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 flex-grow">
                    {provider.description}
                  </p>

                  {/* Models */}
                  {provider.models && (
                    <div className="mb-4">
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                        Popular Models:
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {provider.models.slice(0, 3).map((model) => (
                          <span
                            key={model}
                            className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                          >
                            {model}
                          </span>
                        ))}
                        {provider.models.length > 3 && (
                          <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                            +{provider.models.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Pricing */}
                  {provider.pricing && (
                    <div className="mb-4">
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                        Pricing:
                      </p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {provider.pricing}
                      </p>
                    </div>
                  )}

                  {/* Action Button */}
                  <Button
                    variant={status === 'connected' ? 'secondary' : 'primary'}
                    size="sm"
                    className="w-full mt-auto"
                  >
                    {status === 'connected' ? 'Manage' : 'Setup'}
                  </Button>
                </div>
              </MagicCard>
            );
          })}
        </div>

        {/* Quick Setup Section */}
        <div className="mt-12 bg-white dark:bg-gray-800 rounded-lg p-8 border border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Quick Setup Guide
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                Getting Started
              </h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-600 dark:text-gray-400">
                <li>Choose a provider from the grid above</li>
                <li>Click "Setup" to configure your API key</li>
                <li>Test your connection in the playground</li>
                <li>Start building with multiple AI models</li>
              </ol>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                Popular Combinations
              </h3>
              <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                <li>• <strong>OpenAI + Anthropic:</strong> Best for general use cases</li>
                <li>• <strong>Google + Mistral:</strong> Great for multilingual tasks</li>
                <li>• <strong>Groq + Together:</strong> Ultra-fast inference</li>
                <li>• <strong>Ollama + Self-hosted:</strong> Complete privacy</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
