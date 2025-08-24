import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../../contexts/AuthContext';

// Mock Supabase client
const mockSupabaseClient = {
  auth: {
    signInWithPassword: jest.fn(),
    signUp: jest.fn(),
    signOut: jest.fn(),
    resetPasswordForEmail: jest.fn(),
    updateUser: jest.fn(),
    getSession: jest.fn(),
    onAuthStateChange: jest.fn(() => ({
      data: { subscription: { unsubscribe: jest.fn() } }
    })),
  },
};

jest.mock('@supabase/supabase-js', () => ({
  createClient: () => mockSupabaseClient,
}));

// Test component to access auth context
const TestComponent = () => {
  const { 
    user, 
    loading, 
    signIn, 
    signUp, 
    signOut, 
    resetPassword,
    updateProfile,
    updatePassword 
  } = useAuth();

  return (
    <div>
      <div data-testid="user-status">
        {loading ? 'Loading' : user ? `User: ${user.email}` : 'No user'}
      </div>
      <button onClick={() => signIn('test@example.com', 'password')}>
        Sign In
      </button>
      <button onClick={() => signUp('test@example.com', 'password')}>
        Sign Up
      </button>
      <button onClick={signOut}>Sign Out</button>
      <button onClick={() => resetPassword('test@example.com')}>
        Reset Password
      </button>
      <button onClick={() => updateProfile({ email: 'new@example.com' })}>
        Update Profile
      </button>
      <button onClick={() => updatePassword('newpassword')}>
        Update Password
      </button>
    </div>
  );
};

const TestWrapper = () => (
  <BrowserRouter>
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  </BrowserRouter>
);

describe('Supabase Authentication Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock successful session response
    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });
  });

  it('initializes auth context correctly', async () => {
    render(<TestWrapper />);
    
    await waitFor(() => {
      expect(screen.getByTestId('user-status')).toHaveTextContent('No user');
    });
  });

  it('handles sign in with Supabase', async () => {
    const mockUser = { 
      id: '123', 
      email: 'test@example.com',
      user_metadata: { display_name: 'Test User' }
    };
    
    mockSupabaseClient.auth.signInWithPassword.mockResolvedValue({
      data: { user: mockUser, session: { access_token: 'token' } },
      error: null,
    });

    render(<TestWrapper />);
    
    const signInButton = screen.getByText('Sign In');
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(mockSupabaseClient.auth.signInWithPassword).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
      });
    });
  });

  it('handles sign up with Supabase', async () => {
    const mockUser = { 
      id: '123', 
      email: 'test@example.com',
      user_metadata: { display_name: 'Test User' }
    };
    
    mockSupabaseClient.auth.signUp.mockResolvedValue({
      data: { user: mockUser, session: { access_token: 'token' } },
      error: null,
    });

    render(<TestWrapper />);
    
    const signUpButton = screen.getByText('Sign Up');
    fireEvent.click(signUpButton);

    await waitFor(() => {
      expect(mockSupabaseClient.auth.signUp).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
      });
    });
  });

  it('handles sign out with Supabase', async () => {
    mockSupabaseClient.auth.signOut.mockResolvedValue({
      error: null,
    });

    render(<TestWrapper />);
    
    const signOutButton = screen.getByText('Sign Out');
    fireEvent.click(signOutButton);

    await waitFor(() => {
      expect(mockSupabaseClient.auth.signOut).toHaveBeenCalled();
    });
  });

  it('handles password reset with Supabase', async () => {
    mockSupabaseClient.auth.resetPasswordForEmail.mockResolvedValue({
      error: null,
    });

    render(<TestWrapper />);
    
    const resetButton = screen.getByText('Reset Password');
    fireEvent.click(resetButton);

    await waitFor(() => {
      expect(mockSupabaseClient.auth.resetPasswordForEmail).toHaveBeenCalledWith(
        'test@example.com'
      );
    });
  });

  it('handles profile update with Supabase', async () => {
    mockSupabaseClient.auth.updateUser.mockResolvedValue({
      data: { user: { email: 'new@example.com' } },
      error: null,
    });

    render(<TestWrapper />);
    
    const updateProfileButton = screen.getByText('Update Profile');
    fireEvent.click(updateProfileButton);

    await waitFor(() => {
      expect(mockSupabaseClient.auth.updateUser).toHaveBeenCalledWith({
        email: 'new@example.com',
      });
    });
  });

  it('handles password update with Supabase', async () => {
    mockSupabaseClient.auth.updateUser.mockResolvedValue({
      data: { user: {} },
      error: null,
    });

    render(<TestWrapper />);
    
    const updatePasswordButton = screen.getByText('Update Password');
    fireEvent.click(updatePasswordButton);

    await waitFor(() => {
      expect(mockSupabaseClient.auth.updateUser).toHaveBeenCalledWith({
        password: 'newpassword',
      });
    });
  });

  it('handles authentication errors correctly', async () => {
    const errorMessage = 'Invalid credentials';
    mockSupabaseClient.auth.signInWithPassword.mockResolvedValue({
      data: { user: null, session: null },
      error: { message: errorMessage },
    });

    render(<TestWrapper />);
    
    const signInButton = screen.getByText('Sign In');
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(mockSupabaseClient.auth.signInWithPassword).toHaveBeenCalled();
    });

    // The error handling would be tested in the actual components that use these methods
  });

  it('sets up auth state change listener', () => {
    render(<TestWrapper />);
    
    expect(mockSupabaseClient.auth.onAuthStateChange).toHaveBeenCalled();
  });
});
