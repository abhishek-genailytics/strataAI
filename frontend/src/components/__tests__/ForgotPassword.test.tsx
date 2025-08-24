import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ForgotPassword } from '../ForgotPassword';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the AuthContext
const mockResetPassword = jest.fn();
const mockAuthContextValue = {
  user: null,
  loading: false,
  signIn: jest.fn(),
  signUp: jest.fn(),
  signOut: jest.fn(),
  resetPassword: mockResetPassword,
  updateProfile: jest.fn(),
  updatePassword: jest.fn(),
  refreshUser: jest.fn(),
};

jest.mock('../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../contexts/AuthContext'),
  useAuth: () => mockAuthContextValue,
}));

const ForgotPasswordWrapper = () => (
  <BrowserRouter>
    <AuthProvider>
      <ForgotPassword />
    </AuthProvider>
  </BrowserRouter>
);

describe('ForgotPassword Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders forgot password form correctly', () => {
    render(<ForgotPasswordWrapper />);
    
    expect(screen.getByText('Reset Password')).toBeInTheDocument();
    expect(screen.getByText('Enter your email address and we\'ll send you a link to reset your password.')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send Reset Link' })).toBeInTheDocument();
    expect(screen.getByText('Back to Login')).toBeInTheDocument();
  });

  it('validates email field on blur', async () => {
    render(<ForgotPasswordWrapper />);
    
    const emailInput = screen.getByLabelText('Email');
    
    // Test invalid email
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.blur(emailInput);
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });
    
    // Test valid email
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.blur(emailInput);
    
    await waitFor(() => {
      expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument();
    });
  });

  it('validates email field on form submission', async () => {
    render(<ForgotPasswordWrapper />);
    
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    
    // Submit without email
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
    });
    
    // Submit with invalid email
    const emailInput = screen.getByLabelText('Email');
    fireEvent.change(emailInput, { target: { value: 'invalid' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });
  });

  it('submits form with valid email successfully', async () => {
    mockResetPassword.mockResolvedValueOnce({ error: null });
    
    render(<ForgotPasswordWrapper />);
    
    const emailInput = screen.getByLabelText('Email');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockResetPassword).toHaveBeenCalledWith('test@example.com');
    });
    
    await waitFor(() => {
      expect(screen.getByText('Password reset link sent! Check your email for instructions.')).toBeInTheDocument();
    });
  });

  it('handles reset password error', async () => {
    const errorMessage = 'User not found';
    mockResetPassword.mockResolvedValueOnce({ 
      error: { message: errorMessage } 
    });
    
    render(<ForgotPasswordWrapper />);
    
    const emailInput = screen.getByLabelText('Email');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    // Mock a delayed response
    mockResetPassword.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ error: null }), 100))
    );
    
    render(<ForgotPasswordWrapper />);
    
    const emailInput = screen.getByLabelText('Email');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    // Check loading state
    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Sending...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
      expect(screen.queryByText('Sending...')).not.toBeInTheDocument();
    });
  });

  it('navigates back to login when back link is clicked', () => {
    render(<ForgotPasswordWrapper />);
    
    const backLink = screen.getByText('Back to Login');
    expect(backLink).toHaveAttribute('href', '/login');
  });

  it('clears success message when email is changed after successful submission', async () => {
    mockResetPassword.mockResolvedValueOnce({ error: null });
    
    render(<ForgotPasswordWrapper />);
    
    const emailInput = screen.getByLabelText('Email');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    
    // Submit successfully
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Password reset link sent! Check your email for instructions.')).toBeInTheDocument();
    });
    
    // Change email
    fireEvent.change(emailInput, { target: { value: 'new@example.com' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Password reset link sent! Check your email for instructions.')).not.toBeInTheDocument();
    });
  });

  it('clears error message when email is changed after error', async () => {
    mockResetPassword.mockResolvedValueOnce({ 
      error: { message: 'User not found' } 
    });
    
    render(<ForgotPasswordWrapper />);
    
    const emailInput = screen.getByLabelText('Email');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    
    // Submit with error
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('User not found')).toBeInTheDocument();
    });
    
    // Change email
    fireEvent.change(emailInput, { target: { value: 'new@example.com' } });
    
    await waitFor(() => {
      expect(screen.queryByText('User not found')).not.toBeInTheDocument();
    });
  });

  it('allows resubmission after successful reset', async () => {
    mockResetPassword.mockResolvedValue({ error: null });
    
    render(<ForgotPasswordWrapper />);
    
    const emailInput = screen.getByLabelText('Email');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    
    // First submission
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Password reset link sent! Check your email for instructions.')).toBeInTheDocument();
    });
    
    // Second submission
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockResetPassword).toHaveBeenCalledTimes(2);
    });
  });
});
