import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ApiKeyCard } from '../ApiKeyCard';
import { apiService } from '../../../services/api';
import { ApiKey } from '../../../types';

// Mock the API service
jest.mock('../../../services/api');
const mockApiService = apiService as jest.Mocked<typeof apiService>;

// Mock UI components
jest.mock('../../ui', () => ({
  Button: ({ children, onClick, disabled, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  ),
  Card: ({ children, ...props }: any) => (
    <div {...props}>{children}</div>
  ),
}));

const mockApiKey: ApiKey = {
  id: '1',
  user_id: 'user1',
  provider: 'openai',
  key_name: 'Test API Key',
  masked_key: 'sk-...abc123',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('ApiKeyCard', () => {
  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnRefresh = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders API key information correctly', () => {
    render(
      <ApiKeyCard
        apiKey={mockApiKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText('Test API Key')).toBeInTheDocument();
    expect(screen.getByText('Openai')).toBeInTheDocument();
    expect(screen.getByText('sk-...abc123')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    render(
      <ApiKeyCard
        apiKey={mockApiKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    fireEvent.click(screen.getByText('Edit'));
    expect(mockOnEdit).toHaveBeenCalledWith(mockApiKey);
  });

  it('calls onDelete when delete button is clicked', () => {
    render(
      <ApiKeyCard
        apiKey={mockApiKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    fireEvent.click(screen.getByText('Delete'));
    expect(mockOnDelete).toHaveBeenCalledWith(mockApiKey.id);
  });

  it('reveals API key when reveal button is clicked', async () => {
    mockApiService.revealApiKey.mockResolvedValue({
      data: { api_key: 'sk-full-api-key-here' },
    });

    render(
      <ApiKeyCard
        apiKey={mockApiKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    const revealButton = screen.getByRole('button', { name: /reveal/i });
    fireEvent.click(revealButton);

    await waitFor(() => {
      expect(mockApiService.revealApiKey).toHaveBeenCalledWith(mockApiKey.id);
    });
  });

  it('validates API key when validate button is clicked', async () => {
    mockApiService.validateApiKey.mockResolvedValue({
      data: { valid: true },
    });

    render(
      <ApiKeyCard
        apiKey={mockApiKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    fireEvent.click(screen.getByText('Validate'));

    await waitFor(() => {
      expect(mockApiService.validateApiKey).toHaveBeenCalledWith(mockApiKey.id);
    });
  });

  it('displays correct provider icon and color', () => {
    const anthropicKey = { ...mockApiKey, provider: 'anthropic' as const };
    
    render(
      <ApiKeyCard
        apiKey={anthropicKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText('🧠')).toBeInTheDocument();
    expect(screen.getByText('Anthropic')).toBeInTheDocument();
  });
});
