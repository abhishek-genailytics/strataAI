import React, { useState, useEffect } from 'react';
import { ProviderModelInfo, ApiKey } from '../../types';
import { apiService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (model: string, provider: string) => void;
  disabled?: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  onModelChange,
  disabled = false
}) => {
  const { user } = useAuth();
  const [models, setModels] = useState<ProviderModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch available API keys to determine which providers are configured
        const apiKeysResponse = await apiService.getApiKeys();
        if (apiKeysResponse.error) {
          throw new Error(apiKeysResponse.error);
        }

        const activeApiKeys = apiKeysResponse.data?.filter(key => key.is_active) || [];

        // Fetch all available models
        const modelsResponse = await apiService.getModels();
        if (modelsResponse.error) {
          throw new Error(modelsResponse.error);
        }

        // Filter models to only show those for providers with active API keys
        const availableProviders = activeApiKeys.map(key => key.provider);
        const filteredModels = modelsResponse.data?.filter(model => 
          availableProviders.includes(model.provider as 'openai' | 'anthropic' | 'google')
        ) || [];

        setModels(filteredModels);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load models');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai':
        return '🤖';
      case 'anthropic':
        return '🧠';
      case 'google':
        return '🔍';
      default:
        return '⚡';
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai':
        return 'text-green-600';
      case 'anthropic':
        return 'text-orange-600';
      case 'google':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const handleModelChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedValue = event.target.value;
    const model = models.find(m => `${m.provider}:${m.model}` === selectedValue);
    if (model) {
      onModelChange(model.model, model.provider);
    }
  };

  if (loading) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Model Selection
        </label>
        <div className="animate-pulse">
          <div className="h-10 bg-gray-200 rounded-md"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Model Selection
        </label>
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Model Selection
        </label>
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-600">
            No models available. Please configure API keys for at least one provider.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Model Selection
      </label>
      <select
        value={selectedModel ? models.find(m => m.model === selectedModel)?.provider + ':' + selectedModel : ''}
        onChange={handleModelChange}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <option value="">Select a model...</option>
        {models.map((model) => (
          <option
            key={`${model.provider}:${model.model}`}
            value={`${model.provider}:${model.model}`}
          >
            {getProviderIcon(model.provider)} {model.display_name} ({model.provider})
          </option>
        ))}
      </select>
      
      {selectedModel && (
        <div className="mt-2 p-3 bg-gray-50 rounded-md">
          {(() => {
            const model = models.find(m => m.model === selectedModel);
            if (!model) return null;
            
            return (
              <div className="space-y-1 text-sm">
                <div className="flex items-center space-x-2">
                  <span className={`font-medium ${getProviderColor(model.provider)}`}>
                    {getProviderIcon(model.provider)} {model.provider.toUpperCase()}
                  </span>
                  <span className="text-gray-600">•</span>
                  <span className="font-medium">{model.display_name}</span>
                </div>
                <div className="text-gray-600">
                  Max tokens: {model.max_tokens.toLocaleString()}
                </div>
                <div className="text-gray-600">
                  Cost: ${model.cost_per_1k_input_tokens}/1K input • ${model.cost_per_1k_output_tokens}/1K output
                </div>
                {model.supports_streaming && (
                  <div className="text-green-600 text-xs">
                    ✓ Streaming supported
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
