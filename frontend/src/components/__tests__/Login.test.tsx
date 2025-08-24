import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Login } from '../../pages/Login';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the AuthContext
const mockSignIn = jest.fn();
const mockAuthContext = {
  user: null,
  loading: false,
  error: null,
  signIn: mockSignIn,
  signUp: jest.fn(),
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

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render login form', () => {
    renderLogin();
    
    expect(screen.getByText('Sign in to StrataAI')).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should show validation errors for invalid inputs', async () => {
    renderLogin();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Enter invalid data
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.change(passwordInput, { target: { value: 'short' } });
    fireEvent.blur(emailInput);
    fireEvent.blur(passwordInput);

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    });

    // Submit should not call signIn with invalid data
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockSignIn).not.toHaveBeenCalled();
    });
  });

  it('should call signIn with valid credentials', async () => {
    mockSignIn.mockResolvedValue({});
    renderLogin();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'validPassword123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('test@example.com', 'validPassword123');
    });
  });

  it('should show error message on sign in failure', async () => {
    const errorMessage = 'Invalid credentials';
    mockSignIn.mockResolvedValue({ error: errorMessage });
    renderLogin();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'validPassword123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('should show loading state during sign in', async () => {
    mockSignIn.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({}), 100)));
    renderLogin();
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'validPassword123' } });
    fireEvent.click(submitButton);

    // Should show loading state
    expect(submitButton).toBeDisabled();
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('should have link to register page', () => {
    renderLogin();
    
    const registerLink = screen.getByText(/sign up/i);
    expect(registerLink).toBeInTheDocument();
    expect(registerLink.closest('a')).toHaveAttribute('href', '/register');
  });
});
