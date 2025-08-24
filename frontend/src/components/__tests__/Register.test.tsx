import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Register } from '../../pages/Register';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the AuthContext
const mockSignUp = jest.fn();
const mockAuthContext = {
  user: null,
  loading: false,
  error: null,
  signIn: jest.fn(),
  signUp: mockSignUp,
  signOut: jest.fn(),
  resetPassword: jest.fn(),
  updateProfile: jest.fn(),
  updatePassword: jest.fn(),
  refreshUser: jest.fn(),
  supabase: {} as any,
};

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const renderRegister = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Register />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Register Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render registration form', () => {
    renderRegister();
    
    expect(screen.getByText('Create your StrataAI account')).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('should show password strength indicator', async () => {
    renderRegister();
    
    const passwordInput = screen.getByLabelText(/^password$/i);
    
    fireEvent.change(passwordInput, { target: { value: 'weak' } });
    
    await waitFor(() => {
      expect(screen.getByText(/password strength/i)).toBeInTheDocument();
    });
  });

  it('should show validation errors for invalid inputs', async () => {
    renderRegister();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });

    // Enter invalid data
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.change(passwordInput, { target: { value: 'short' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'different' } });
    fireEvent.blur(emailInput);
    fireEvent.blur(passwordInput);
    fireEvent.blur(confirmPasswordInput);

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument();
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });

    // Submit should not call signUp with invalid data
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockSignUp).not.toHaveBeenCalled();
    });
  });

  it('should call signUp with valid credentials', async () => {
    mockSignUp.mockResolvedValue({});
    renderRegister();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });

    const validPassword = 'ValidPassword123!';
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: validPassword } });
    fireEvent.change(confirmPasswordInput, { target: { value: validPassword } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith('test@example.com', validPassword);
    });
  });

  it('should show success message after successful registration', async () => {
    mockSignUp.mockResolvedValue({});
    renderRegister();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });

    const validPassword = 'ValidPassword123!';
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: validPassword } });
    fireEvent.change(confirmPasswordInput, { target: { value: validPassword } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/registration successful/i)).toBeInTheDocument();
      expect(screen.getByText(/check your email to verify/i)).toBeInTheDocument();
    });
  });

  it('should show error message on registration failure', async () => {
    const errorMessage = 'Email already exists';
    mockSignUp.mockResolvedValue({ error: errorMessage });
    renderRegister();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });

    const validPassword = 'ValidPassword123!';
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: validPassword } });
    fireEvent.change(confirmPasswordInput, { target: { value: validPassword } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('should have link to login page', () => {
    renderRegister();
    
    const loginLink = screen.getByText(/sign in/i);
    expect(loginLink).toBeInTheDocument();
    expect(loginLink.closest('a')).toHaveAttribute('href', '/login');
  });

  it('should require strong password for submission', async () => {
    renderRegister();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });

    const weakPassword = 'password'; // Weak password
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: weakPassword } });
    fireEvent.change(confirmPasswordInput, { target: { value: weakPassword } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/password is not strong enough/i)).toBeInTheDocument();
      expect(mockSignUp).not.toHaveBeenCalled();
    });
  });
});
