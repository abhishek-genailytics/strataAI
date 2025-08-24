import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';
import { errorLoggingService } from '../../services/errorLoggingService';

// Mock the error logging service
jest.mock('../../services/errorLoggingService', () => ({
  errorLoggingService: {
    logClientError: jest.fn().mockResolvedValue('test-error-id'),
  },
}));

// Component that throws an error for testing
const ThrowError: React.FC<{ shouldThrow: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('Test error message');
  }
  return <div>No error</div>;
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock console.error to avoid noise in tests
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();
  });

  it('renders error UI when child component throws', async () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText(/Our team has been notified/)).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
    expect(screen.getByText('Refresh Page')).toBeInTheDocument();

    // Wait for error logging to complete
    await waitFor(() => {
      expect(errorLoggingService.logClientError).toHaveBeenCalledWith({
        error: expect.any(Error),
        errorInfo: expect.any(Object),
        timestamp: expect.any(String),
        userAgent: expect.any(String),
        url: expect.any(String),
        userId: null,
      });
    });
  });

  it('displays error ID when available', async () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    await waitFor(() => {
      expect(screen.getByText(/Error ID: test-error-id/)).toBeInTheDocument();
    });
  });

  it('shows error details in development mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Error details (development only)')).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('hides error details in production mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.queryByText('Error details (development only)')).not.toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('calls custom error handler when provided', async () => {
    const mockErrorHandler = jest.fn();

    render(
      <ErrorBoundary onError={mockErrorHandler}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    await waitFor(() => {
      expect(mockErrorHandler).toHaveBeenCalledWith(
        expect.any(Error),
        expect.any(Object)
      );
    });
  });

  it('renders custom fallback when provided', () => {
    const customFallback = <div>Custom error message</div>;

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom error message')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  it('recovers from error when Try Again is clicked', async () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Try Again'));

    // Rerender with non-throwing component
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  it('handles error logging failure gracefully', async () => {
    // Mock error logging service to throw
    (errorLoggingService.logClientError as jest.Mock).mockRejectedValue(
      new Error('Logging failed')
    );

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Should still render error UI even if logging fails
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    await waitFor(() => {
      expect(console.error).toHaveBeenCalledWith(
        'Failed to log error:',
        expect.any(Error)
      );
    });
  });

  it('extracts user ID from localStorage', async () => {
    const mockAuthData = {
      user: { id: 'user123' },
      token: 'mock-token',
    };

    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn().mockReturnValue(JSON.stringify(mockAuthData)),
    };
    Object.defineProperty(window, 'localStorage', { value: localStorageMock });

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    await waitFor(() => {
      expect(errorLoggingService.logClientError).toHaveBeenCalledWith(
        expect.objectContaining({
          userId: 'user123',
        })
      );
    });
  });
});
