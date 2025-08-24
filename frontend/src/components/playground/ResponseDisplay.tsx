import React, { useState } from 'react';
import { PlaygroundResponse } from '../../types';

interface ResponseDisplayProps {
  response?: PlaygroundResponse;
  error?: string;
  isLoading: boolean;
}

const ResponseDisplay: React.FC<ResponseDisplayProps> = ({
  response,
  error,
  isLoading
}) => {
  const [activeTab, setActiveTab] = useState<'response' | 'raw' | 'usage'>('response');

  const formatJson = (obj: any) => {
    return JSON.stringify(obj, null, 2);
  };

  const calculateCost = (response: PlaygroundResponse) => {
    if (!response.usage) return 0;
    
    // This is a simplified cost calculation
    // In a real implementation, you'd get the model pricing from the backend
    const inputCost = (response.usage.prompt_tokens / 1000) * 0.01; // $0.01 per 1K tokens (example)
    const outputCost = (response.usage.completion_tokens / 1000) * 0.02; // $0.02 per 1K tokens (example)
    return inputCost + outputCost;
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Generating response...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full bg-red-50 rounded-lg border border-red-200 p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <span className="text-red-400 text-xl">⚠️</span>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <div className="mt-2 text-sm text-red-700">
              <pre className="whitespace-pre-wrap font-mono text-xs bg-red-100 p-3 rounded border">
                {error}
              </pre>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!response) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center">
          <span className="text-4xl mb-4 block">💬</span>
          <p className="text-gray-600">Response will appear here</p>
          <p className="text-sm text-gray-500 mt-2">Configure your request and click "Send Request"</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white rounded-lg border border-gray-200">
      {/* Header with tabs */}
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div className="flex space-x-1">
          <button
            onClick={() => setActiveTab('response')}
            className={`px-3 py-1 text-sm font-medium rounded-md ${
              activeTab === 'response'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Response
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={`px-3 py-1 text-sm font-medium rounded-md ${
              activeTab === 'raw'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Raw JSON
          </button>
          <button
            onClick={() => setActiveTab('usage')}
            className={`px-3 py-1 text-sm font-medium rounded-md ${
              activeTab === 'usage'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Usage
          </button>
        </div>
        
        {response.processing_time_ms && (
          <div className="text-sm text-gray-500">
            {response.processing_time_ms}ms
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'response' && (
          <div className="p-4">
            {response.choices.map((choice, index) => (
              <div key={index} className="mb-4">
                <div className="flex items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    Choice {choice.index + 1}
                  </span>
                  {choice.finish_reason && (
                    <span className="ml-2 px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                      {choice.finish_reason}
                    </span>
                  )}
                </div>
                <div className="bg-gray-50 rounded-lg p-4 border">
                  <div className="flex items-center mb-2">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                      {choice.message.role}
                    </span>
                  </div>
                  <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap font-sans text-gray-900 leading-relaxed">
                      {choice.message.content}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'raw' && (
          <div className="p-4">
            <pre className="text-sm font-mono bg-gray-50 p-4 rounded-lg border overflow-auto">
              <code>{formatJson(response)}</code>
            </pre>
          </div>
        )}

        {activeTab === 'usage' && response.usage && (
          <div className="p-4 space-y-4">
            {/* Token Usage */}
            <div className="bg-gray-50 rounded-lg p-4 border">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Token Usage</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {response.usage.prompt_tokens.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Input Tokens</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {response.usage.completion_tokens.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Output Tokens</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {response.usage.total_tokens.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Total Tokens</div>
                </div>
              </div>
            </div>

            {/* Cost Estimate */}
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <h4 className="text-sm font-medium text-green-900 mb-2">Cost Estimate</h4>
              <div className="text-2xl font-bold text-green-700">
                ${calculateCost(response).toFixed(6)}
              </div>
              <div className="text-sm text-green-600 mt-1">
                Estimated cost for this request
              </div>
            </div>

            {/* Model Info */}
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h4 className="text-sm font-medium text-blue-900 mb-3">Request Details</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-blue-700">Model:</span>
                  <span className="font-medium">{response.model}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">Provider:</span>
                  <span className="font-medium">{response.provider}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">Request ID:</span>
                  <span className="font-mono text-xs">{response.id}</span>
                </div>
                {response.processing_time_ms && (
                  <div className="flex justify-between">
                    <span className="text-blue-700">Processing Time:</span>
                    <span className="font-medium">{response.processing_time_ms}ms</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResponseDisplay;
