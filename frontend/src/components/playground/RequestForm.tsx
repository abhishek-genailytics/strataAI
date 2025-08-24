import React, { useState } from 'react';
import { ChatMessage } from '../../types';
import { Button, Input } from '../ui';

interface RequestFormProps {
  messages: ChatMessage[];
  onMessagesChange: (messages: ChatMessage[]) => void;
  parameters: {
    temperature: number;
    max_tokens: number;
    top_p: number;
    frequency_penalty: number;
    presence_penalty: number;
    stop: string[];
  };
  onParametersChange: (parameters: any) => void;
  onSubmit: () => void;
  isLoading: boolean;
  disabled?: boolean;
}

const RequestForm: React.FC<RequestFormProps> = ({
  messages,
  onMessagesChange,
  parameters,
  onParametersChange,
  onSubmit,
  isLoading,
  disabled = false
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [newMessage, setNewMessage] = useState('');

  const addMessage = (role: 'system' | 'user' | 'assistant') => {
    if (!newMessage.trim()) return;
    
    const message: ChatMessage = {
      role,
      content: newMessage.trim()
    };
    
    onMessagesChange([...messages, message]);
    setNewMessage('');
  };

  const updateMessage = (index: number, content: string) => {
    const updatedMessages = messages.map((msg, i) => 
      i === index ? { ...msg, content } : msg
    );
    onMessagesChange(updatedMessages);
  };

  const removeMessage = (index: number) => {
    const updatedMessages = messages.filter((_, i) => i !== index);
    onMessagesChange(updatedMessages);
  };

  const updateParameter = (key: string, value: any) => {
    onParametersChange({
      ...parameters,
      [key]: value
    });
  };

  const handleStopSequencesChange = (value: string) => {
    const sequences = value.split(',').map(s => s.trim()).filter(s => s);
    updateParameter('stop', sequences);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!disabled && !isLoading && messages.some(m => m.role === 'user')) {
      onSubmit();
    }
  };

  return (
    <div className="space-y-6">
      {/* Messages Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Messages</h3>
          <span className="text-sm text-gray-500">
            {messages.length} message{messages.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Existing Messages */}
        <div className="space-y-3">
          {messages.map((message, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <select
                  value={message.role}
                  onChange={(e) => {
                    const updatedMessages = messages.map((msg, i) => 
                      i === index ? { ...msg, role: e.target.value as any } : msg
                    );
                    onMessagesChange(updatedMessages);
                  }}
                  disabled={disabled}
                  className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="system">System</option>
                  <option value="user">User</option>
                  <option value="assistant">Assistant</option>
                </select>
                <button
                  onClick={() => removeMessage(index)}
                  disabled={disabled}
                  className="text-red-600 hover:text-red-800 disabled:opacity-50"
                >
                  ✕
                </button>
              </div>
              <textarea
                value={message.content}
                onChange={(e) => updateMessage(index, e.target.value)}
                disabled={disabled}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                placeholder="Enter message content..."
              />
            </div>
          ))}
        </div>

        {/* Add New Message */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            disabled={disabled}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            placeholder="Type your message here..."
          />
          <div className="flex space-x-2 mt-3">
            <Button
              onClick={() => addMessage('user')}
              disabled={disabled || !newMessage.trim()}
              variant="primary"
              size="sm"
            >
              Add User Message
            </Button>
            <Button
              onClick={() => addMessage('system')}
              disabled={disabled || !newMessage.trim()}
              variant="secondary"
              size="sm"
            >
              Add System Message
            </Button>
            <Button
              onClick={() => addMessage('assistant')}
              disabled={disabled || !newMessage.trim()}
              variant="secondary"
              size="sm"
            >
              Add Assistant Message
            </Button>
          </div>
        </div>
      </div>

      {/* Parameters Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Parameters</h3>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Temperature */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperature: {parameters.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={parameters.temperature}
              onChange={(e) => updateParameter('temperature', parseFloat(e.target.value))}
              disabled={disabled}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Focused</span>
              <span>Creative</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div>
            <Input
              label="Max Tokens"
              type="number"
              value={parameters.max_tokens.toString()}
              onChange={(value) => updateParameter('max_tokens', parseInt(value) || 1000)}
              disabled={disabled}
              placeholder="1000"
            />
          </div>
        </div>

        {/* Advanced Parameters */}
        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
            {/* Top P */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Top P: {parameters.top_p}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={parameters.top_p}
                onChange={(e) => updateParameter('top_p', parseFloat(e.target.value))}
                disabled={disabled}
                className="w-full"
              />
            </div>

            {/* Frequency Penalty */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frequency Penalty: {parameters.frequency_penalty}
              </label>
              <input
                type="range"
                min="-2"
                max="2"
                step="0.1"
                value={parameters.frequency_penalty}
                onChange={(e) => updateParameter('frequency_penalty', parseFloat(e.target.value))}
                disabled={disabled}
                className="w-full"
              />
            </div>

            {/* Presence Penalty */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Presence Penalty: {parameters.presence_penalty}
              </label>
              <input
                type="range"
                min="-2"
                max="2"
                step="0.1"
                value={parameters.presence_penalty}
                onChange={(e) => updateParameter('presence_penalty', parseFloat(e.target.value))}
                disabled={disabled}
                className="w-full"
              />
            </div>

            {/* Stop Sequences */}
            <div>
              <Input
                label="Stop Sequences (comma-separated)"
                value={parameters.stop.join(', ')}
                onChange={handleStopSequencesChange}
                disabled={disabled}
                placeholder="\\n, ., !"
              />
            </div>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <form onSubmit={handleSubmit}>
        <Button
          type="submit"
          variant="primary"
          loading={isLoading}
          disabled={disabled || !messages.some(m => m.role === 'user')}
          className="w-full"
        >
          {isLoading ? 'Generating...' : 'Send Request'}
        </Button>
      </form>

      {/* Request Info */}
      {messages.length > 0 && (
        <div className="text-sm text-gray-500 bg-gray-50 p-3 rounded-md">
          <div className="flex justify-between">
            <span>Messages: {messages.length}</span>
            <span>Est. tokens: ~{messages.reduce((acc, msg) => acc + Math.ceil(msg.content.length / 4), 0)}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default RequestForm;
