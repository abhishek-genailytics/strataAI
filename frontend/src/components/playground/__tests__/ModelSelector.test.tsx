import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ModelSelector from '../ModelSelector';
import { apiService } from '../../../services/api';

// Mock the API service
jest.mock('../../../services/api', () => ({
  apiService: {
    getApiKeys: jest.fn(),
    getModels: jest.fn(),
  },
}));

const mockApiService = apiService as jest.Mocked<typeof apiService>;

const mockApiKeys = [
  {
    id: '1',
    user_id: 'user1',
    provider: 'openai',
    key_name: 'OpenAI Key',
    masked_key: 'sk-...abc123',
    is_active: true,
    created_at: '2023-01-01',
    updated_at: '2023-01-01',
  },
  {
    id: '2',
    user_id: 'user1',
    provider: 'anthropic',
    key_name: 'Anthropic Key',
    masked_key: 'sk-...def456',
    is_active: true,
    created_at: '2023-01-01',
    updated_at: '2023-01-01',
  },
];

const mockModels = [
  {
    provider: 'openai',
    model: 'gpt-4',
    display_name: 'GPT-4',
    max_tokens: 8192,
    supports_streaming: true,
    cost_per_1k_input_tokens: 0.03,
    cost_per_1k_output_tokens: 0.06,
  },
  {
    provider: 'anthropic',
    model: 'claude-3-opus',
    display_name: 'Claude 3 Opus',
    max_tokens: 4096,
    supports_streaming: true,
    cost_per_1k_input_tokens: 0.015,
    cost_per_1k_output_tokens: 0.075,
  },
];

describe('ModelSelector', () => {
  const mockOnModelChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.getApiKeys.mockResolvedValue({ data: mockApiKeys });
    mockApiService.getModels.mockResolvedValue({ data: mockModels });
  });

  it('renders loading state initially', () => {
    render(
      <ModelSelector
        selectedModel=""
        onModelChange={mockOnModelChange}
      />
    );

    expect(screen.getByText('Model Selection')).toBeInTheDocument();
    expect(screen.getByRole('generic')).toHaveClass('animate-pulse');
  });

  it('renders model options after loading', async () => {
    render(
      <ModelSelector
        selectedModel=""
        onModelChange={mockOnModelChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    expect(screen.getByText('🤖 GPT-4 (openai)')).toBeInTheDocument();
    expect(screen.getByText('🧠 Claude 3 Opus (anthropic)')).toBeInTheDocument();
  });

  it('calls onModelChange when a model is selected', async () => {
    const user = userEvent.setup();
    
    render(
      <ModelSelector
        selectedModel=""
        onModelChange={mockOnModelChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, 'openai:gpt-4');

    expect(mockOnModelChange).toHaveBeenCalledWith('gpt-4', 'openai');
  });

  it('shows model details when a model is selected', async () => {
    render(
      <ModelSelector
        selectedModel="gpt-4"
        onModelChange={mockOnModelChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('🤖 OPENAI')).toBeInTheDocument();
    });

    expect(screen.getByText('Max tokens: 8,192')).toBeInTheDocument();
    expect(screen.getByText('Cost: $0.03/1K input • $0.06/1K output')).toBeInTheDocument();
    expect(screen.getByText('✓ Streaming supported')).toBeInTheDocument();
  });

  it('shows error message when API calls fail', async () => {
    mockApiService.getApiKeys.mockResolvedValue({ error: 'Failed to fetch API keys' });

    render(
      <ModelSelector
        selectedModel=""
        onModelChange={mockOnModelChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch API keys')).toBeInTheDocument();
    });
  });

  it('shows no models message when no API keys are configured', async () => {
    mockApiService.getApiKeys.mockResolvedValue({ data: [] });

    render(
      <ModelSelector
        selectedModel=""
        onModelChange={mockOnModelChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No models available. Please configure API keys for at least one provider.')).toBeInTheDocument();
    });
  });

  it('disables the select when disabled prop is true', async () => {
    render(
      <ModelSelector
        selectedModel=""
        onModelChange={mockOnModelChange}
        disabled={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeDisabled();
    });
  });
});
