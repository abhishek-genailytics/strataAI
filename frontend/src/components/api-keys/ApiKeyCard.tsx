import React, { useState } from 'react';
import { ApiKey } from '../../types';
import { apiService } from '../../services/api';
import { Button, Card } from '../ui';

interface ApiKeyCardProps {
  apiKey: ApiKey;
  onEdit: (key: ApiKey) => void;
  onDelete: (keyId: string) => void;
  onRefresh: () => void;
}

export const ApiKeyCard: React.FC<ApiKeyCardProps> = ({
  apiKey,
  onEdit,
  onDelete,
  onRefresh,
}) => {
  const [isRevealed, setIsRevealed] = useState(false);
  const [revealedKey, setRevealedKey] = useState<string>('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationStatus, setValidationStatus] = useState<'valid' | 'invalid' | null>(null);
  const [isRevealing, setIsRevealing] = useState(false);

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai':
        return '🤖';
      case 'anthropic':
        return '🧠';
      case 'google':
        return '🔍';
      default:
        return '🔑';
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai':
        return 'bg-green-100 text-green-800';
      case 'anthropic':
        return 'bg-purple-100 text-purple-800';
      case 'google':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleRevealKey = async () => {
    if (isRevealed) {
      setIsRevealed(false);
      setRevealedKey('');
      return;
    }

    try {
      setIsRevealing(true);
      const response = await apiService.revealApiKey(apiKey.id);
      
      if (response.error) {
        console.error('Failed to reveal API key:', response.error);
      } else {
        setRevealedKey(response.data?.api_key || '');
        setIsRevealed(true);
      }
    } catch (err) {
      console.error('Failed to reveal API key:', err);
    } finally {
      setIsRevealing(false);
    }
  };

  const handleValidateKey = async () => {
    try {
      setIsValidating(true);
      setValidationStatus(null);
      const response = await apiService.validateApiKey(apiKey.id);
      
      if (response.error) {
        setValidationStatus('invalid');
      } else {
        setValidationStatus(response.data?.valid ? 'valid' : 'invalid');
      }
    } catch (err) {
      setValidationStatus('invalid');
    } finally {
      setIsValidating(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <Card className="relative">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{getProviderIcon(apiKey.provider)}</div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">{apiKey.key_name}</h3>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getProviderColor(apiKey.provider)}`}>
              {apiKey.provider.charAt(0).toUpperCase() + apiKey.provider.slice(1)}
            </span>
          </div>
        </div>
        
        {/* Status Indicator */}
        <div className="flex items-center space-x-2">
          {validationStatus && (
            <div className={`w-3 h-3 rounded-full ${validationStatus === 'valid' ? 'bg-green-400' : 'bg-red-400'}`} />
          )}
          <div className={`w-3 h-3 rounded-full ${apiKey.is_active ? 'bg-green-400' : 'bg-gray-400'}`} />
        </div>
      </div>

      {/* API Key Display */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
        <div className="flex items-center space-x-2">
          <div className="flex-1 font-mono text-sm bg-gray-50 p-2 rounded border">
            {isRevealed ? revealedKey : apiKey.masked_key}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRevealKey}
            disabled={isRevealing}
            className="flex-shrink-0"
          >
            {isRevealing ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
            ) : isRevealed ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.464 8.464a10.05 10.05 0 00-5.878 8.536c1.274 4.057 5.065 7 9.543 7 1.726 0 3.35-.413 4.793-1.146M9.878 9.878a3 3 0 013.535-.372m4.242 4.242L19.536 15.464a10.05 10.05 0 005.878-8.536c-1.274-4.057-5.065-7-9.543-7-1.726 0-3.35.413-4.793 1.146" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            )}
          </Button>
        </div>
      </div>

      {/* Metadata */}
      <div className="mt-4 text-sm text-gray-500">
        <p>Created: {formatDate(apiKey.created_at)}</p>
        {apiKey.updated_at !== apiKey.created_at && (
          <p>Updated: {formatDate(apiKey.updated_at)}</p>
        )}
      </div>

      {/* Actions */}
      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleValidateKey}
          disabled={isValidating}
        >
          {isValidating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
              Validating...
            </>
          ) : (
            'Validate'
          )}
        </Button>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(apiKey)}
          >
            Edit
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => onDelete(apiKey.id)}
          >
            Delete
          </Button>
        </div>
      </div>
    </Card>
  );
};
