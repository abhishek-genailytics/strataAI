import React, { useState, useEffect } from "react";
import { ChevronDown, Settings, Zap } from "lucide-react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { apiService } from "../../services/api";
import "./ModelConfigCard.css";

interface ModelConfig {
  temperature: number;
  maxTokens: number;
  streaming: boolean;
}

interface ConfiguredModel {
  id: string;
  provider: string;
  model: string;
  displayName: string;
  isConfigured: boolean;
  maxTokens: number;
  supportsStreaming: boolean;
}

interface ModelConfigCardProps {
  selectedModel: string;
  onModelChange: (model: string) => void;
  modelConfig: ModelConfig;
  onConfigChange: (config: ModelConfig) => void;
  currentSessionId?: string | null;
  onSessionSelect?: (sessionId: string) => Promise<void>;
}

export const ModelConfigCard: React.FC<ModelConfigCardProps> = ({
  selectedModel,
  onModelChange,
  modelConfig,
  onConfigChange,
}) => {
  const [configuredModels, setConfiguredModels] = useState<ConfiguredModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [models, setModels] = useState([]);

  useEffect(() => {
    fetchConfiguredModels();
  }, []);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await apiService.getPlaygroundModels();
        if (response.data) {
          setModels(response.data);
        }
      } catch (error) {
        console.error('Error fetching playground models:', error);
      }
    };

    fetchModels();
  }, []);

  const fetchConfiguredModels = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get playground models (already filtered by user's API keys)
      const playgroundModelsResponse = await apiService.getPlaygroundModels();
      if (playgroundModelsResponse.error) {
        throw new Error(playgroundModelsResponse.error);
      }

      const playgroundModels = playgroundModelsResponse.data || [];

      const configured = playgroundModels.map((model: any) => ({
        id: model.id, // Already in format "provider/model"
        provider: model.provider,
        model: model.model,
        displayName: model.display_name,
        isConfigured: true,
        maxTokens: model.max_tokens,
        supportsStreaming: model.supports_streaming || false,
      }));

      setConfiguredModels(configured);

      // If no model is selected and we have configured models, select the first one
      if (!selectedModel && configured.length > 0) {
        onModelChange(configured[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load configured models");
    } finally {
      setLoading(false);
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case "openai":
        return "🤖";
      case "anthropic":
        return "🧠";
      case "google":
        return "🔍";
      default:
        return "⚡";
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider.toLowerCase()) {
      case "openai":
        return "from-green-50 to-emerald-50 border-green-200";
      case "anthropic":
        return "from-orange-50 to-amber-50 border-orange-200";
      case "google":
        return "from-blue-50 to-indigo-50 border-blue-200";
      default:
        return "from-slate-50 to-gray-50 border-slate-200";
    }
  };

  const selectedModelData = configuredModels.find(m => m.id === selectedModel);

  const handleConfigChange = (key: keyof ModelConfig, value: number | boolean) => {
    onConfigChange({
      ...modelConfig,
      [key]: value,
    });
  };

  if (loading) {
    return (
      <Card className="bg-white shadow-lg border border-gray-200">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Model Configuration</h3>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500">⚡</span>
              <span className="text-xs text-slate-500">⚙️</span>
            </div>
          </div>
          <div className="animate-pulse">
            <div className="h-20 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-white shadow-lg border border-gray-200">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Model Configuration</h3>
          </div>
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      </Card>
    );
  }

  if (configuredModels.length === 0) {
    return (
      <Card className="bg-white shadow-lg border border-gray-200">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Model Configuration</h3>
          </div>
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-700 mb-2">No models configured</p>
            <p className="text-xs text-yellow-600">
              Please configure API keys in the Access section to use models in the playground.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="bg-white shadow-lg border border-gray-200 overflow-visible">
      <div className="space-y-4 overflow-visible">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">Model Configuration</h3>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
              className="text-slate-500 hover:text-slate-700"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Model Selection */}
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className={`w-full p-3 rounded-lg border text-left transition-all duration-200 ${
              selectedModelData
                ? `bg-gradient-to-r ${getProviderColor(selectedModelData.provider)}`
                : "bg-slate-50 border-slate-200"
            }`}
          >
            {selectedModelData ? (
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-lg">{getProviderIcon(selectedModelData.provider)}</span>
                    <span className="font-semibold text-slate-900 text-sm">
                      {selectedModelData.displayName}
                    </span>
                  </div>
                  <div className="text-xs text-slate-600">
                    {selectedModelData.provider} • Max: {selectedModelData.maxTokens.toLocaleString()} tokens
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Select a model...</span>
                <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
              </div>
            )}
          </button>

          {/* Dropdown */}
          {showDropdown && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-[9999] max-h-150 overflow-y-auto">
              {configuredModels.map((model) => (
                <button
                  key={model.id}
                  onClick={() => {
                    onModelChange(model.id);
                    setShowDropdown(false);
                  }}
                  className="w-full p-3 text-left hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-b-0"
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-lg">{getProviderIcon(model.provider)}</span>
                    <span className="font-medium text-slate-900 text-sm">
                      {model.displayName}
                    </span>
                    {model.supportsStreaming && (
                      <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                        Streaming
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-600">
                    {model.provider} • Max: {model.maxTokens.toLocaleString()} tokens
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Model Settings */}
        {showSettings && selectedModelData && (
          <div className="space-y-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
              Model Settings
            </h4>

            {/* Temperature */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-700">Temperature</label>
                <span className="text-xs text-slate-500">{modelConfig.temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={modelConfig.temperature}
                onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>Focused</span>
                <span>Creative</span>
              </div>
            </div>

            {/* Max Tokens */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-700">Max Tokens</label>
                <span className="text-xs text-slate-500">{modelConfig.maxTokens.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="1"
                max={selectedModelData.maxTokens}
                step="100"
                value={modelConfig.maxTokens}
                onChange={(e) => handleConfigChange('maxTokens', parseInt(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>1</span>
                <span>{selectedModelData.maxTokens.toLocaleString()}</span>
              </div>
            </div>

            {/* Streaming */}
            {selectedModelData.supportsStreaming && (
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-700">Streaming Mode</label>
                <button
                  onClick={() => handleConfigChange('streaming', !modelConfig.streaming)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    modelConfig.streaming ? 'bg-blue-600' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                      modelConfig.streaming ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Quick Settings Display */}
        {!showSettings && selectedModelData && (
          <div className="flex flex-wrap gap-2">
            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">
              temp: {modelConfig.temperature}
            </span>
            <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
              max: {modelConfig.maxTokens.toLocaleString()}
            </span>
            {selectedModelData.supportsStreaming && (
              <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
                streaming: {modelConfig.streaming ? 'on' : 'off'}
              </span>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
