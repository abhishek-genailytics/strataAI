import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { 
  PlaygroundRequest, 
  PlaygroundResponse, 
  ChatMessage, 
  PlaygroundState 
} from '../types';
import ModelSelector from '../components/playground/ModelSelector';
import RequestForm from '../components/playground/RequestForm';
import ResponseDisplay from '../components/playground/ResponseDisplay';
import RequestHistory from '../components/playground/RequestHistory';

const Playground: React.FC = () => {
  const { user } = useAuth();
  const [state, setState] = useState<PlaygroundState>({
    selectedModel: '',
    messages: [
      {
        role: 'user',
        content: 'Hello! Can you help me understand how AI models work?'
      }
    ],
    parameters: {
      temperature: 0.7,
      max_tokens: 1000,
      top_p: 1.0,
      frequency_penalty: 0.0,
      presence_penalty: 0.0,
      stop: []
    },
    isLoading: false
  });

  const [selectedProvider, setSelectedProvider] = useState('');
  const [showHistory, setShowHistory] = useState(false);

  // Generate a mock project_id for now (in real implementation, this would come from user context)
  const projectId = user?.id || 'default-project';

  const handleModelChange = (model: string, provider: string) => {
    setState(prev => ({ ...prev, selectedModel: model }));
    setSelectedProvider(provider);
  };

  const handleMessagesChange = (messages: ChatMessage[]) => {
    setState(prev => ({ ...prev, messages }));
  };

  const handleParametersChange = (parameters: any) => {
    setState(prev => ({ ...prev, parameters }));
  };

  const handleSubmitRequest = async () => {
    if (!state.selectedModel || state.messages.length === 0) {
      return;
    }

    setState(prev => ({ 
      ...prev, 
      isLoading: true, 
      response: undefined, 
      error: undefined 
    }));

    const request: PlaygroundRequest = {
      messages: state.messages,
      model: state.selectedModel,
      provider: selectedProvider,
      project_id: projectId,
      temperature: state.parameters.temperature,
      max_tokens: state.parameters.max_tokens,
      top_p: state.parameters.top_p,
      frequency_penalty: state.parameters.frequency_penalty,
      presence_penalty: state.parameters.presence_penalty,
      stop: state.parameters.stop.length > 0 ? state.parameters.stop : undefined,
      stream: false
    };

    try {
      const response = await apiService.createChatCompletion(request);
      
      if (response.error) {
        setState(prev => ({ 
          ...prev, 
          isLoading: false, 
          error: response.error 
        }));
      } else {
        setState(prev => ({ 
          ...prev, 
          isLoading: false, 
          response: response.data 
        }));
      }
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'An unexpected error occurred' 
      }));
    }
  };

  const handleReplayRequest = (request: PlaygroundRequest) => {
    setState(prev => ({
      ...prev,
      selectedModel: request.model,
      messages: request.messages,
      parameters: {
        temperature: request.temperature || 0.7,
        max_tokens: request.max_tokens || 1000,
        top_p: request.top_p || 1.0,
        frequency_penalty: request.frequency_penalty || 0.0,
        presence_penalty: request.presence_penalty || 0.0,
        stop: Array.isArray(request.stop) ? request.stop : []
      }
    }));
    
    if (request.provider) {
      setSelectedProvider(request.provider);
    }
  };

  const currentRequest: PlaygroundRequest | undefined = 
    state.selectedModel ? {
      messages: state.messages,
      model: state.selectedModel,
      provider: selectedProvider,
      project_id: projectId,
      ...state.parameters
    } : undefined;

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Playground</h1>
            <p className="text-sm text-gray-600 mt-1">
              Test and experiment with different AI models and parameters
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`lg:hidden px-3 py-2 text-sm font-medium rounded-md ${
                showHistory 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              History
            </button>
            
            {user && (
              <div className="text-sm text-gray-600">
                Welcome, {user.email}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Configuration */}
        <div className="w-full lg:w-1/2 xl:w-2/5 flex flex-col border-r border-gray-200 bg-white">
          <div className="flex-1 overflow-auto p-6 space-y-6">
            {/* Model Selection */}
            <ModelSelector
              selectedModel={state.selectedModel}
              onModelChange={handleModelChange}
              disabled={state.isLoading}
            />

            {/* Request Form */}
            <RequestForm
              messages={state.messages}
              onMessagesChange={handleMessagesChange}
              parameters={state.parameters}
              onParametersChange={handleParametersChange}
              onSubmit={handleSubmitRequest}
              isLoading={state.isLoading}
              disabled={!state.selectedModel}
            />
          </div>
        </div>

        {/* Right Panel - Response */}
        <div className="w-full lg:w-1/2 xl:w-3/5 flex">
          <div className="flex-1 p-6">
            <ResponseDisplay
              response={state.response}
              error={state.error}
              isLoading={state.isLoading}
            />
          </div>

          {/* History Sidebar */}
          <div className={`w-80 ${showHistory ? 'block' : 'hidden lg:block'}`}>
            <RequestHistory
              onReplayRequest={handleReplayRequest}
              currentRequest={currentRequest}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>
              Model: {state.selectedModel || 'None selected'}
            </span>
            {selectedProvider && (
              <span>
                Provider: {selectedProvider}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {state.response?.usage && (
              <span>
                Tokens: {state.response.usage.total_tokens.toLocaleString()}
              </span>
            )}
            {state.response?.processing_time_ms && (
              <span>
                Time: {state.response.processing_time_ms}ms
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Playground;
