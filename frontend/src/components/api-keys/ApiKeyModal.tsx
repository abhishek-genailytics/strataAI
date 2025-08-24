import React from 'react';
import { ApiKey } from '../../types';
import { Modal } from '../ui';
import { ApiKeyForm } from './ApiKeyForm';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  editingKey?: ApiKey | null;
}

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  editingKey,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={editingKey ? 'Edit API Key' : 'Add New API Key'}
      size="lg"
    >
      <ApiKeyForm
        onSuccess={onSuccess}
        onCancel={onClose}
        editingKey={editingKey}
      />
    </Modal>
  );
};
