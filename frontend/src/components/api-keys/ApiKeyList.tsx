import React from 'react';
import { ApiKey } from '../../types';
import { ApiKeyCard } from './ApiKeyCard';

interface ApiKeyListProps {
  apiKeys: ApiKey[];
  onEdit: (key: ApiKey) => void;
  onDelete: (keyId: string) => void;
  onRefresh: () => void;
}

export const ApiKeyList: React.FC<ApiKeyListProps> = ({
  apiKeys,
  onEdit,
  onDelete,
  onRefresh,
}) => {
  if (apiKeys.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11.5 16.5a6 6 0 01-7.743-5.743A6 6 0 0111.5 7.5l1.5 1.5a2 2 0 012 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No API keys</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by adding your first API key.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {apiKeys.map((apiKey) => (
        <ApiKeyCard
          key={apiKey.id}
          apiKey={apiKey}
          onEdit={onEdit}
          onDelete={onDelete}
          onRefresh={onRefresh}
        />
      ))}
    </div>
  );
};
