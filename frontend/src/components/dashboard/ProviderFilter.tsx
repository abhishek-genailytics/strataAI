import React from 'react';
import { ProviderFilterProps } from '../../types';

const ProviderFilter: React.FC<ProviderFilterProps> = ({ value, onChange, providers }) => {
  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai': return '🤖';
      case 'anthropic': return '🧠';
      case 'google': return '🔍';
      default: return '🔧';
    }
  };

  const getProviderDisplayName = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai': return 'OpenAI';
      case 'anthropic': return 'Anthropic';
      case 'google': return 'Google';
      default: return provider.charAt(0).toUpperCase() + provider.slice(1);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
      <label className="text-sm font-medium text-gray-700">Provider:</label>
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value || undefined)}
        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
      >
        <option value="">All Providers</option>
        {providers.map((provider) => (
          <option key={provider} value={provider}>
            {getProviderIcon(provider)} {getProviderDisplayName(provider)}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ProviderFilter;
