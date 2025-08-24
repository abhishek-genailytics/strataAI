import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card } from './ui/Card';
import { Modal } from './ui/Modal';
import { validateEmail, validatePassword, validatePasswordConfirmation, validateForm } from '../utils/validation';

interface UserProfileProps {
  className?: string;
}

export const UserProfile: React.FC<UserProfileProps> = ({ className = '' }) => {
  const { user, supabase, signOut } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Profile form state
  const [email, setEmail] = useState(user?.email || '');
  const [displayName, setDisplayName] = useState('');
  
  // Password change form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (user) {
      setEmail(user.email || '');
      // Get display name from user metadata
      setDisplayName(user.user_metadata?.display_name || user.user_metadata?.full_name || '');
    }
  }, [user]);

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Validate email
      const emailValidation = validateEmail(email);
      if (!emailValidation.isValid) {
        setError(emailValidation.error || 'Invalid email');
        setLoading(false);
        return;
      }

      // Update user profile
      const { error: updateError } = await supabase.auth.updateUser({
        email: email,
        data: {
          display_name: displayName,
          full_name: displayName,
        }
      });

      if (updateError) {
        setError(updateError.message);
      } else {
        setSuccess('Profile updated successfully');
        setIsEditing(false);
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Validate passwords
    const validators = {
      currentPassword: (value: string) => value ? { isValid: true } : { isValid: false, error: 'Current password is required' },
      newPassword: validatePassword,
      confirmNewPassword: (value: string) => validatePasswordConfirmation(newPassword, value),
    };

    const { isValid, errors } = validateForm(
      { currentPassword, newPassword, confirmNewPassword },
      validators
    );

    if (!isValid) {
      setPasswordErrors(errors);
      setLoading(false);
      return;
    }

    try {
      // Update password
      const { error: updateError } = await supabase.auth.updateUser({
        password: newPassword
      });

      if (updateError) {
        setError(updateError.message);
      } else {
        setSuccess('Password changed successfully');
        setIsChangingPassword(false);
        setCurrentPassword('');
        setNewPassword('');
        setConfirmNewPassword('');
        setPasswordErrors({});
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await signOut();
  };

  if (!user) {
    return null;
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Profile Information</h2>
            {!isEditing && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(true)}
              >
                Edit Profile
              </Button>
            )}
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-md">
              {success}
            </div>
          )}

          {isEditing ? (
            <form onSubmit={handleProfileUpdate} className="space-y-4">
              <Input
                label="Display Name"
                value={displayName}
                onChange={setDisplayName}
                placeholder="Enter your display name"
              />
              
              <Input
                label="Email Address"
                type="email"
                value={email}
                onChange={setEmail}
                required
                placeholder="Enter your email"
              />

              <div className="flex space-x-3">
                <Button
                  type="submit"
                  loading={loading}
                >
                  Save Changes
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsEditing(false);
                    setEmail(user.email || '');
                    setDisplayName(user.user_metadata?.display_name || '');
                    setError('');
                    setSuccess('');
                  }}
                >
                  Cancel
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Display Name</label>
                <p className="mt-1 text-sm text-gray-900">{displayName || 'Not set'}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Email Address</label>
                <p className="mt-1 text-sm text-gray-900">{user.email}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Account Created</label>
                <p className="mt-1 text-sm text-gray-900">
                  {new Date(user.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Security</h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsChangingPassword(true)}
            >
              Change Password
            </Button>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <p className="mt-1 text-sm text-gray-500">••••••••</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Account Actions</h2>
          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={handleSignOut}
            >
              Sign Out
            </Button>
          </div>
        </div>
      </Card>

      {/* Password Change Modal */}
      <Modal
        isOpen={isChangingPassword}
        onClose={() => {
          setIsChangingPassword(false);
          setCurrentPassword('');
          setNewPassword('');
          setConfirmNewPassword('');
          setPasswordErrors({});
          setError('');
          setSuccess('');
        }}
        title="Change Password"
      >
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <Input
            label="Current Password"
            type="password"
            value={currentPassword}
            onChange={setCurrentPassword}
            error={passwordErrors.currentPassword}
            required
            placeholder="Enter your current password"
          />
          
          <Input
            label="New Password"
            type="password"
            value={newPassword}
            onChange={setNewPassword}
            error={passwordErrors.newPassword}
            required
            placeholder="Enter your new password"
          />
          
          <Input
            label="Confirm New Password"
            type="password"
            value={confirmNewPassword}
            onChange={setConfirmNewPassword}
            error={passwordErrors.confirmNewPassword}
            required
            placeholder="Confirm your new password"
          />

          <div className="flex space-x-3 pt-4">
            <Button
              type="submit"
              loading={loading}
            >
              Change Password
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsChangingPassword(false);
                setCurrentPassword('');
                setNewPassword('');
                setConfirmNewPassword('');
                setPasswordErrors({});
                setError('');
                setSuccess('');
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
