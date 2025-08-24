import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MetricsOverview from '../MetricsOverview';
import { UsageSummary } from '../../../types';

const mockSummary: UsageSummary = {
  total_requests: 1250,
  total_tokens: 45000,
  total_cost: 12.50,
  average_latency: 850,
  success_rate: 0.98,
  failed_requests: 25,
  unique_users: 5,
  providers: {
    openai: {
      requests: 800,
      tokens: 30000,
      cost: 8.50,
    },
    anthropic: {
      requests: 450,
      tokens: 15000,
      cost: 4.00,
    },
  },
};

describe('MetricsOverview', () => {
  it('renders loading state correctly', () => {
    render(<MetricsOverview summary={mockSummary} loading={true} />);
    
    // Should show loading skeleton
    const skeletonElements = document.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('renders metrics correctly', () => {
    render(<MetricsOverview summary={mockSummary} loading={false} />);
    
    // Check if all metric cards are rendered
    expect(screen.getByText('Total Requests')).toBeInTheDocument();
    expect(screen.getByText('Total Cost')).toBeInTheDocument();
    expect(screen.getByText('Success Rate')).toBeInTheDocument();
    expect(screen.getByText('Avg Latency')).toBeInTheDocument();
    
    // Check formatted values
    expect(screen.getByText('1.3K')).toBeInTheDocument(); // 1250 requests formatted
    expect(screen.getByText('$12.50')).toBeInTheDocument();
    expect(screen.getByText('98.0%')).toBeInTheDocument();
    expect(screen.getByText('850ms')).toBeInTheDocument();
  });

  it('formats large numbers correctly', () => {
    const largeSummary: UsageSummary = {
      ...mockSummary,
      total_requests: 1500000,
      total_tokens: 45000000,
    };
    
    render(<MetricsOverview summary={largeSummary} loading={false} />);
    
    expect(screen.getByText('1.5M')).toBeInTheDocument();
  });

  it('displays metric icons', () => {
    render(<MetricsOverview summary={mockSummary} loading={false} />);
    
    // Check if emoji icons are present
    expect(screen.getByText('📊')).toBeInTheDocument();
    expect(screen.getByText('💰')).toBeInTheDocument();
    expect(screen.getByText('✅')).toBeInTheDocument();
    expect(screen.getByText('⚡')).toBeInTheDocument();
  });
});
