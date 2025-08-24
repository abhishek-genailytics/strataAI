import React, { useState, useEffect } from 'react';
import { ApiKey } from '../../types';
import { apiService } from '../../services/api';
import { Button, Input } from '../ui';

interface ApiKeyFormProps {
  onSuccess: () => void;
  onCancel: () => void;
  editingKey?: ApiKey | null;
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', icon: '🤖' },
  { value: 'anthropic', label: 'Anthropic', icon: '🧠' },
  { value: 'google', label: 'Google', icon: '🔍' },
];

export const ApiKeyForm: React.FC<ApiKeyFormProps> = ({
  onSuccess,
  onCancel,
  editingKey,
}) => {
  const [formData, setFormData] = useState({
    provider: '',
    key_name: '',
    api_key: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isValidating, setIsValidating] = useState(false);

  useEffect(() => {
    if (editingKey) {
      setFormData({
        provider: editingKey.provider,
        key_name: editingKey.key_name,
        api_key: '', // Don't pre-fill the API key for security
      });
    }
  }, [editingKey]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.provider) {
      newErrors.provider = 'Provider is required';
    }

    if (!formData.key_name.trim()) {
      newErrors.key_name = 'Key name is required';
    }

    if (!editingKey && !formData.api_key.trim()) {
      newErrors.api_key = 'API key is required';
    }

    // Basic API key format validation
    if (formData.api_key.trim()) {
      if (formData.provider === 'openai' && !formData.api_key.startsWith('sk-')) {
        newErrors.api_key = 'OpenAI API keys should start with "sk-"';
      } else if (formData.provider === 'anthropic' && !formData.api_key.startsWith('sk-ant-')) {
        newErrors.api_key = 'Anthropic API keys should start with "sk-ant-"';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setIsSubmitting(true);
      
      let response;
      if (editingKey) {
        // Update existing key
        const updateData: any = { key_name: formData.key_name };
        if (formData.api_key.trim()) {
          updateData.api_key = formData.api_key;
        }
        response = await apiService.updateApiKey(editingKey.id, updateData);
      } else {
        // Create new key
        response = await apiService.createApiKey({
          provider: formData.provider,
          key_name: formData.key_name,
          api_key: formData.api_key,
        });
      }

      if (response.error) {
        setErrors({ submit: response.error });
      } else {
        onSuccess();
      }
    } catch (err) {
      setErrors({ submit: 'An unexpected error occurred' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleValidateKey = async () => {
    if (!formData.api_key.trim()) {
      setErrors({ api_key: 'Enter an API key to validate' });
      return;
    }

    try {
      setIsValidating(true);
      setErrors({});

      // For validation, we need to temporarily create the key or validate the format
      // Since we can't validate without saving, we'll do basic format validation
      if (formData.provider === 'openai' && !formData.api_key.startsWith('sk-')) {
        setErrors({ api_key: 'OpenAI API keys should start with "sk-"' });
        return;
      }
      
      if (formData.provider === 'anthropic' && !formData.api_key.startsWith('sk-ant-')) {
        setErrors({ api_key: 'Anthropic API keys should start with "sk-ant-"' });
        return;
      }

      // Basic length validation
      if (formData.api_key.length < 20) {
        setErrors({ api_key: 'API key appears to be too short' });
        return;
      }

      // If we get here, the format looks good
      setErrors({ api_key: '' });
      alert('API key format appears valid. Save to perform full validation.');
      
    } catch (err) {
      setErrors({ api_key: 'Validation failed' });
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Provider Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Provider *
        </label>
        <div className="grid grid-cols-3 gap-3">
          {PROVIDERS.map((provider) => (
            <button
              key={provider.value}
              type="button"
              onClick={() => setFormData({ ...formData, provider: provider.value })}
              disabled={!!editingKey} // Can't change provider when editing
              className={`
                flex flex-col items-center p-3 border-2 rounded-lg transition-colors
                ${formData.provider === provider.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
                }
                ${editingKey ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <span className="text-2xl mb-1">{provider.icon}</span>
              <span className="text-sm font-medium">{provider.label}</span>
            </button>
          ))}
        </div>
        {errors.provider && (
          <p className="mt-1 text-sm text-red-600">{errors.provider}</p>
        )}
      </div>

      {/* Key Name */}
      <div>
        <Input
          label="Key Name *"
          placeholder="e.g., Production API Key"
          value={formData.key_name}
          onChange={(value) => setFormData({ ...formData, key_name: value })}
          error={errors.key_name}
          required
        />
      </div>

      {/* API Key */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">
            API Key {!editingKey && '*'}
          </label>
          {formData.api_key.trim() && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleValidateKey}
              disabled={isValidating}
            >
              {isValidating ? 'Validating...' : 'Validate Format'}
            </Button>
          )}
        </div>
        <Input
          type="password"
          placeholder={editingKey ? "Leave empty to keep current key" : "Enter your API key"}
          value={formData.api_key}
          onChange={(value) => setFormData({ ...formData, api_key: value })}
          error={errors.api_key}
          required={!editingKey}
        />
        {editingKey && (
          <p className="mt-1 text-sm text-gray-500">
            Leave empty to keep the current API key unchanged
          </p>
        )}
      </div>

      {/* Submit Error */}
      {errors.submit && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{errors.submit}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end space-x-3">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          loading={isSubmitting}
          disabled={isSubmitting}
        >
          {editingKey ? 'Update Key' : 'Add Key'}
        </Button>
      </div>
    </form>
  );
};
