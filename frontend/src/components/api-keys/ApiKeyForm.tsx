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
  { 
    value: 'openai', 
    label: 'OpenAI', 
    icon: '🤖',
    models: [
      { id: 'gpt-4', name: 'GPT-4', type: 'Chat' },
      { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', type: 'Chat' },
      { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', type: 'Chat' },
      { id: 'gpt-3.5-turbo-0125', name: 'GPT-3.5 Turbo 0125', type: 'Chat' },
      { id: 'gpt-3.5-turbo-1106', name: 'GPT-3.5 Turbo 1106', type: 'Chat' },
    ]
  },
  { 
    value: 'anthropic', 
    label: 'Anthropic', 
    icon: '🧠',
    models: [
      { id: 'claude-3-opus', name: 'Claude 3 Opus', type: 'Chat' },
      { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', type: 'Chat' },
      { id: 'claude-3-haiku', name: 'Claude 3 Haiku', type: 'Chat' },
    ]
  },
  { 
    value: 'google', 
    label: 'Google', 
    icon: '🔍',
    models: [
      { id: 'gemini-pro', name: 'Gemini Pro', type: 'Chat' },
      { id: 'gemini-pro-vision', name: 'Gemini Pro Vision', type: 'Chat' },
    ]
  },
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
    selectedModels: [] as string[],
    collaborators: [] as { email: string; role: 'manager' | 'user' }[],
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
        selectedModels: [],
        collaborators: [],
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

      {/* Model Selection */}
      {formData.provider && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Select Models
          </label>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {PROVIDERS.find(p => p.value === formData.provider)?.models.map((model) => (
              <label key={model.id} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.selectedModels.includes(model.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFormData({
                        ...formData,
                        selectedModels: [...formData.selectedModels, model.id]
                      });
                    } else {
                      setFormData({
                        ...formData,
                        selectedModels: formData.selectedModels.filter(id => id !== model.id)
                      });
                    }
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{model.name}</span>
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{model.type}</span>
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Collaborators */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Collaborators (Optional)
          </label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              setFormData({
                ...formData,
                collaborators: [...formData.collaborators, { email: '', role: 'user' }]
              });
            }}
          >
            + Add Collaborator
          </Button>
        </div>
        <p className="text-sm text-gray-500 mb-3">
          List of users who have access to this provider account
        </p>
        
        {formData.collaborators.length > 0 && (
          <div className="space-y-3">
            {formData.collaborators.map((collaborator, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 border rounded-lg">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-medium text-sm">
                    {collaborator.email ? collaborator.email[0].toUpperCase() : 'U'}
                  </span>
                </div>
                <div className="flex-1">
                  <Input
                    placeholder="Enter email address"
                    value={collaborator.email}
                    onChange={(value) => {
                      const newCollaborators = [...formData.collaborators];
                      newCollaborators[index].email = value;
                      setFormData({ ...formData, collaborators: newCollaborators });
                    }}
                  />
                </div>
                <select
                  value={collaborator.role}
                  onChange={(e) => {
                    const newCollaborators = [...formData.collaborators];
                    newCollaborators[index].role = e.target.value as 'manager' | 'user';
                    setFormData({ ...formData, collaborators: newCollaborators });
                  }}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="user">User</option>
                  <option value="manager">Manager</option>
                </select>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const newCollaborators = formData.collaborators.filter((_, i) => i !== index);
                    setFormData({ ...formData, collaborators: newCollaborators });
                  }}
                  className="text-red-600 hover:text-red-700"
                >
                  ×
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

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
