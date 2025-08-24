import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserProfile } from '../UserProfile';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock user data
const mockUser = {
  id: '123',
  email: 'test@example.com',
  created_at: '2023-01-01T00:00:00Z',
  user_metadata: {
    display_name: 'John Doe',
    full_name: 'John Doe',
  },
};

// Mock the AuthContext
const mockUpdateProfile = jest.fn();
const mockUpdatePassword = jest.fn();
const mockSignOut = jest.fn();
const mockSupabase = {
  auth: {
    updateUser: jest.fn(),
  },
};

const mockAuthContext = {
  user: mockUser,
  loading: false,
  error: null,
  signIn: jest.fn(),
  signUp: jest.fn(),
  signOut: mockSignOut,
  resetPassword: jest.fn(),
  updateProfile: mockUpdateProfile,
  updatePassword: mockUpdatePassword,
  refreshUser: jest.fn(),
  supabase: mockSupabase as any,
};

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const renderUserProfile = () => {
  return render(
    <AuthProvider>
      <UserProfile />
    </AuthProvider>
  );
};

describe('UserProfile Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render user profile information', () => {
    renderUserProfile();
    
    expect(screen.getByText('Profile Information')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('Security')).toBeInTheDocument();
    expect(screen.getByText('Account Actions')).toBeInTheDocument();
  });

  it('should show edit profile form when edit button is clicked', () => {
    renderUserProfile();
    
    const editButton = screen.getByText('Edit Profile');
    fireEvent.click(editButton);
    
    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('should update profile when form is submitted', async () => {
    mockSupabase.auth.updateUser.mockResolvedValue({ error: null });
    renderUserProfile();
    
    const editButton = screen.getByText('Edit Profile');
    fireEvent.click(editButton);
    
    const nameInput = screen.getByDisplayValue('John Doe');
    const emailInput = screen.getByDisplayValue('test@example.com');
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    
    fireEvent.change(nameInput, { target: { value: 'Jane Doe' } });
    fireEvent.change(emailInput, { target: { value: 'jane@example.com' } });
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockSupabase.auth.updateUser).toHaveBeenCalledWith({
        email: 'jane@example.com',
        data: {
          display_name: 'Jane Doe',
          full_name: 'Jane Doe',
        },
      });
    });
  });

  it('should show change password modal when button is clicked', () => {
    renderUserProfile();
    
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    expect(screen.getByText('Change Password')).toBeInTheDocument();
    expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();
  });

  it('should validate password change form', async () => {
    renderUserProfile();
    
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    const currentPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText(/new password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm new password/i);
    const submitButton = screen.getByRole('button', { name: /change password/i });
    
    // Submit with invalid data
    fireEvent.change(currentPasswordInput, { target: { value: '' } });
    fireEvent.change(newPasswordInput, { target: { value: 'short' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'different' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/current password is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument();
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
    
    expect(mockSupabase.auth.updateUser).not.toHaveBeenCalled();
  });

  it('should change password with valid data', async () => {
    mockSupabase.auth.updateUser.mockResolvedValue({ error: null });
    renderUserProfile();
    
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    const currentPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText(/new password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm new password/i);
    const submitButton = screen.getByRole('button', { name: /change password/i });
    
    const newPassword = 'NewSecurePassword123!';
    
    fireEvent.change(currentPasswordInput, { target: { value: 'currentPassword' } });
    fireEvent.change(newPasswordInput, { target: { value: newPassword } });
    fireEvent.change(confirmPasswordInput, { target: { value: newPassword } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockSupabase.auth.updateUser).toHaveBeenCalledWith({
        password: newPassword,
      });
    });
  });

  it('should call signOut when sign out button is clicked', () => {
    renderUserProfile();
    
    const signOutButton = screen.getByText('Sign Out');
    fireEvent.click(signOutButton);
    
    expect(mockSignOut).toHaveBeenCalled();
  });

  it('should cancel profile editing', () => {
    renderUserProfile();
    
    const editButton = screen.getByText('Edit Profile');
    fireEvent.click(editButton);
    
    const nameInput = screen.getByDisplayValue('John Doe');
    fireEvent.change(nameInput, { target: { value: 'Changed Name' } });
    
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);
    
    // Should return to view mode with original data
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.queryByDisplayValue('Changed Name')).not.toBeInTheDocument();
  });

  it('should not render when user is not logged in', () => {
    const mockAuthContextNoUser = {
      ...mockAuthContext,
      user: null,
    };
    
    jest.mocked(require('../../contexts/AuthContext').useAuth).mockReturnValue(mockAuthContextNoUser);
    
    const { container } = renderUserProfile();
    expect(container.firstChild).toBeNull();
  });
});
