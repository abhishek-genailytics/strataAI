import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Toast, ToastContainer } from '../ui/Toast';
import { ToastProvider, useToast } from '../../contexts/ToastContext';

describe('Toast', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders success toast correctly', () => {
    render(
      <Toast
        id="test-toast"
        type="success"
        title="Success!"
        message="Operation completed successfully"
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
  });

  it('renders error toast correctly', () => {
    render(
      <Toast
        id="test-toast"
        type="error"
        title="Error!"
        message="Something went wrong"
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Error!')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders warning toast correctly', () => {
    render(
      <Toast
        id="test-toast"
        type="warning"
        title="Warning!"
        message="Please check your input"
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Warning!')).toBeInTheDocument();
    expect(screen.getByText('Please check your input')).toBeInTheDocument();
  });

  it('renders info toast correctly', () => {
    render(
      <Toast
        id="test-toast"
        type="info"
        title="Info"
        message="Here's some information"
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Info')).toBeInTheDocument();
    expect(screen.getByText("Here's some information")).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <Toast
        id="test-toast"
        type="success"
        title="Success!"
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledWith('test-toast');
  });

  it('auto-closes after specified duration', async () => {
    render(
      <Toast
        id="test-toast"
        type="success"
        title="Success!"
        duration={100}
        onClose={mockOnClose}
      />
    );

    await waitFor(
      () => {
        expect(mockOnClose).toHaveBeenCalledWith('test-toast');
      },
      { timeout: 500 }
    );
  });

  it('does not auto-close when duration is 0', async () => {
    render(
      <Toast
        id="test-toast"
        type="success"
        title="Success!"
        duration={0}
        onClose={mockOnClose}
      />
    );

    // Wait a bit and ensure onClose was not called
    await new Promise(resolve => setTimeout(resolve, 200));
    expect(mockOnClose).not.toHaveBeenCalled();
  });
});

describe('ToastContainer', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders multiple toasts', () => {
    const toasts = [
      {
        id: 'toast-1',
        type: 'success' as const,
        title: 'Success 1',
        onClose: mockOnClose,
      },
      {
        id: 'toast-2',
        type: 'error' as const,
        title: 'Error 1',
        onClose: mockOnClose,
      },
    ];

    render(<ToastContainer toasts={toasts} onClose={mockOnClose} />);

    expect(screen.getByText('Success 1')).toBeInTheDocument();
    expect(screen.getByText('Error 1')).toBeInTheDocument();
  });

  it('renders nothing when no toasts', () => {
    const { container } = render(<ToastContainer toasts={[]} onClose={mockOnClose} />);
    expect(container.firstChild).toBeNull();
  });
});

describe('ToastProvider', () => {
  const TestComponent: React.FC = () => {
    const { showSuccess, showError, showWarning, showInfo, clearToasts } = useToast();

    return (
      <div>
        <button onClick={() => showSuccess('Success', 'Success message')}>
          Show Success
        </button>
        <button onClick={() => showError('Error', 'Error message')}>
          Show Error
        </button>
        <button onClick={() => showWarning('Warning', 'Warning message')}>
          Show Warning
        </button>
        <button onClick={() => showInfo('Info', 'Info message')}>
          Show Info
        </button>
        <button onClick={clearToasts}>Clear All</button>
      </div>
    );
  };

  it('provides toast context to children', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    expect(screen.getByText('Show Success')).toBeInTheDocument();
    expect(screen.getByText('Show Error')).toBeInTheDocument();
    expect(screen.getByText('Show Warning')).toBeInTheDocument();
    expect(screen.getByText('Show Info')).toBeInTheDocument();
  });

  it('shows success toast when showSuccess is called', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Success'));
    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByText('Success message')).toBeInTheDocument();
  });

  it('shows error toast when showError is called', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Error'));
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  it('shows warning toast when showWarning is called', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Warning'));
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('Warning message')).toBeInTheDocument();
  });

  it('shows info toast when showInfo is called', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Info'));
    expect(screen.getByText('Info')).toBeInTheDocument();
    expect(screen.getByText('Info message')).toBeInTheDocument();
  });

  it('clears all toasts when clearToasts is called', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    // Show multiple toasts
    fireEvent.click(screen.getByText('Show Success'));
    fireEvent.click(screen.getByText('Show Error'));

    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();

    // Clear all toasts
    fireEvent.click(screen.getByText('Clear All'));

    expect(screen.queryByText('Success')).not.toBeInTheDocument();
    expect(screen.queryByText('Error')).not.toBeInTheDocument();
  });

  it('throws error when useToast is used outside provider', () => {
    const TestComponentOutsideProvider: React.FC = () => {
      const { showSuccess } = useToast();
      return <button onClick={() => showSuccess('Test')}>Test</button>;
    };

    // Mock console.error to avoid noise in test output
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponentOutsideProvider />);
    }).toThrow('useToast must be used within a ToastProvider');

    consoleSpy.mockRestore();
  });
});
