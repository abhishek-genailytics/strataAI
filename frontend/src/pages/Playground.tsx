import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { 
  PlaygroundRequest, 
  ChatMessage, 
  PlaygroundState 
} from '../types';
import ModelSelector from '../components/playground/ModelSelector';
import RequestForm from '../components/playground/RequestForm';
import ResponseDisplay from '../components/playground/ResponseDisplay';
import RequestHistory from '../components/playground/RequestHistory';
import { MagicCard } from '../components/ui/magic-card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

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

  // Enhanced playground state
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful assistant.');
  const [inputVariations, setInputVariations] = useState<string[]>(['']);
  const [mcpServers, setMcpServers] = useState<string[]>([]);
  const [inputGuardrails, setInputGuardrails] = useState<string[]>([]);
  const [outputGuardrails, setOutputGuardrails] = useState<string[]>([]);
  const [structuredOutput, setStructuredOutput] = useState<any>(null);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);

  const [selectedProvider, setSelectedProvider] = useState('');
  const [showHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'embedding' | 'rerank' | 'image'>('chat');
  const [showSidebar, setShowSidebar] = useState(true);

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
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900">Playground</h1>
            
            {/* Tab Navigation */}
            <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
              {(['chat', 'embedding', 'rerank', 'image'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md capitalize transition-colors ${
                    activeTab === tab
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSidebar(!showSidebar)}
            >
              {showSidebar ? 'Hide Sidebar' : 'Show Sidebar'}
            </Button>
            
            {user && (
              <div className="text-sm text-gray-600">
                {user.email}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Configuration */}
        <div className={`${showSidebar ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden border-r border-gray-200 bg-white`}>
          <div className="w-80 h-full overflow-auto p-4 space-y-4">
            {/* Model Selection */}
            <MagicCard className="p-4">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                <span className="text-lg mr-2">🤖</span>
                Model Selection
              </h3>
              <ModelSelector
                selectedModel={state.selectedModel}
                onModelChange={handleModelChange}
                disabled={state.isLoading}
              />
            </MagicCard>

            {/* System Prompt */}
            <MagicCard className="p-4">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                <span className="text-lg mr-2">💭</span>
                System Prompt
              </h3>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="You are a helpful assistant."
                className="w-full h-20 p-3 border border-gray-300 rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </MagicCard>

            {/* Input Variations */}
            <MagicCard className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <span className="text-lg mr-2">🔄</span>
                  Input Variations (0)
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setInputVariations([...inputVariations, ''])}
                >
                  +
                </Button>
              </div>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {inputVariations.map((variation, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <Input
                      value={variation}
                      onChange={(value) => {
                        const newVariations = [...inputVariations];
                        newVariations[index] = value;
                        setInputVariations(newVariations);
                      }}
                      placeholder="Enter variation"
                      className="flex-1"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setInputVariations(inputVariations.filter((_, i) => i !== index));
                      }}
                      className="text-red-600"
                    >
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            </MagicCard>

            {/* MCP Servers */}
            <MagicCard className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <span className="text-lg mr-2">🔌</span>
                  MCP Servers (0)
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setMcpServers([...mcpServers, ''])}
                >
                  +
                </Button>
              </div>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {mcpServers.map((server, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <Input
                      value={server}
                      onChange={(value) => {
                        const newServers = [...mcpServers];
                        newServers[index] = value;
                        setMcpServers(newServers);
                      }}
                      placeholder="Server name"
                      className="flex-1"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setMcpServers(mcpServers.filter((_, i) => i !== index));
                      }}
                      className="text-red-600"
                    >
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            </MagicCard>

            {/* Input Guardrails */}
            <MagicCard className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <span className="text-lg mr-2">🛡️</span>
                  Input Guardrails (0)
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setInputGuardrails([...inputGuardrails, ''])}
                >
                  +
                </Button>
              </div>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {inputGuardrails.map((guardrail, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <Input
                      value={guardrail}
                      onChange={(value) => {
                        const newGuardrails = [...inputGuardrails];
                        newGuardrails[index] = value;
                        setInputGuardrails(newGuardrails);
                      }}
                      placeholder="Guardrail rule"
                      className="flex-1"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setInputGuardrails(inputGuardrails.filter((_, i) => i !== index));
                      }}
                      className="text-red-600"
                    >
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            </MagicCard>

            {/* Output Guardrails */}
            <MagicCard className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <span className="text-lg mr-2">🔒</span>
                  Output Guardrails (0)
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setOutputGuardrails([...outputGuardrails, ''])}
                >
                  +
                </Button>
              </div>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {outputGuardrails.map((guardrail, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <Input
                      value={guardrail}
                      onChange={(value) => {
                        const newGuardrails = [...outputGuardrails];
                        newGuardrails[index] = value;
                        setOutputGuardrails(newGuardrails);
                      }}
                      placeholder="Output rule"
                      className="flex-1"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setOutputGuardrails(outputGuardrails.filter((_, i) => i !== index));
                      }}
                      className="text-red-600"
                    >
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            </MagicCard>

            {/* Structured Output */}
            <MagicCard className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <span className="text-lg mr-2">📋</span>
                  Structured Output
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                >
                  {showAdvancedOptions ? '−' : '+'}
                </Button>
              </div>
              {showAdvancedOptions && (
                <textarea
                  value={structuredOutput ? JSON.stringify(structuredOutput, null, 2) : ''}
                  onChange={(e) => {
                    try {
                      setStructuredOutput(e.target.value ? JSON.parse(e.target.value) : null);
                    } catch {
                      // Invalid JSON, keep the text for editing
                    }
                  }}
                  placeholder={`{\n  "type": "object",\n  "properties": {\n    "answer": {"type": "string"}\n  }\n}`}
                  className="w-full h-32 p-3 border border-gray-300 rounded-lg text-sm font-mono resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              )}
            </MagicCard>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Messages */}
          <div className="flex-1 p-6 overflow-auto">
            <div className="max-w-4xl mx-auto space-y-4">
              {/* System Prompt Display */}
              {systemPrompt && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <span className="text-blue-600 font-medium text-sm">SYSTEM PROMPT</span>
                  </div>
                  <p className="text-blue-800 text-sm">{systemPrompt}</p>
                </div>
              )}
              
              {/* Chat Messages */}
              <div className="space-y-4">
                {state.messages.map((message, index) => (
                  <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-3xl rounded-lg p-4 ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-white border border-gray-200'
                    }`}>
                      <div className="flex items-center mb-2">
                        <span className="font-medium text-sm uppercase tracking-wide">
                          {message.role === 'user' ? 'You' : 'Assistant'}
                        </span>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Response Display */}
              {(state.response || state.error || state.isLoading) && (
                <ResponseDisplay
                  response={state.response}
                  error={state.error}
                  isLoading={state.isLoading}
                />
              )}
            </div>
          </div>
          
          {/* Input Area */}
          <div className="border-t border-gray-200 bg-white p-6">
            <div className="max-w-4xl mx-auto">
              <RequestForm
                messages={state.messages}
                onMessagesChange={handleMessagesChange}
                parameters={state.parameters}
                onParametersChange={handleParametersChange}
                onSubmit={handleSubmitRequest}
                isLoading={state.isLoading}
                disabled={!state.selectedModel}
              />
              
              {/* Quick Suggestions */}
              <div className="mt-4 flex flex-wrap gap-2">
                {[
                  'Data Extraction with JSON Outputs',
                  'JSON creation',
                  'Non-English Content Generation',
                  'Removing PII'
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      const newMessage = { role: 'user' as const, content: suggestion };
                      handleMessagesChange([...state.messages, newMessage]);
                    }}
                    className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* History Sidebar */}
        {showHistory && (
          <div className="w-80 border-l border-gray-200">
            <RequestHistory
              onReplayRequest={handleReplayRequest}
              currentRequest={currentRequest}
            />
          </div>
        )}
      </div>

    </div>
  );
};

export default Playground;
