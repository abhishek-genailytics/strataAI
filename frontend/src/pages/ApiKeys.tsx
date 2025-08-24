import React, { useState, useEffect } from 'react';
import { ApiKey } from '../types';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui';
import { ApiKeyList } from '../components/api-keys/ApiKeyList';
import { ApiKeyModal } from '../components/api-keys/ApiKeyModal';

export const ApiKeys: React.FC = () => {
  const { currentOrganization } = useAuth();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingKey, setEditingKey] = useState<ApiKey | null>(null);

  useEffect(() => {
    fetchApiKeys();
  }, [currentOrganization]); // Refetch when organization changes

  const fetchApiKeys = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getApiKeys();
      
      if (response.error) {
        setError(response.error);
      } else {
        setApiKeys(response.data || []);
      }
    } catch (err) {
      setError('Failed to fetch API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = () => {
    setEditingKey(null);
    setIsModalOpen(true);
  };

  const handleEditKey = (key: ApiKey) => {
    setEditingKey(key);
    setIsModalOpen(true);
  };

  const handleDeleteKey = async (keyId: string) => {
    if (!window.confirm('Are you sure you want to delete this API key?')) {
      return;
    }

    try {
      const response = await apiService.deleteApiKey(keyId);
      
      if (response.error) {
        setError(response.error);
      } else {
        await fetchApiKeys(); // Refresh the list
      }
    } catch (err) {
      setError('Failed to delete API key');
    }
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setEditingKey(null);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    setEditingKey(null);
    fetchApiKeys(); // Refresh the list
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <div className="mt-1 space-y-1">
            <p className="text-gray-500">
              Manage your API keys for different AI providers
            </p>
            {currentOrganization ? (
              <div className="flex items-center text-sm text-blue-600">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                Organization: {currentOrganization.display_name || currentOrganization.name}
              </div>
            ) : (
              <div className="flex items-center text-sm text-gray-500">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Personal Workspace
              </div>
            )}
          </div>
        </div>
        <Button onClick={handleCreateKey}>
          Add API Key
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setError(null)}
                className="inline-flex text-red-400 hover:text-red-500"
              >
                <span className="sr-only">Dismiss</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys List */}
      <ApiKeyList
        apiKeys={apiKeys}
        onEdit={handleEditKey}
        onDelete={handleDeleteKey}
        onRefresh={fetchApiKeys}
      />

      {/* Modal */}
      <ApiKeyModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onSuccess={handleModalSuccess}
        editingKey={editingKey}
      />
    </div>
  );
};

export default ApiKeys;
