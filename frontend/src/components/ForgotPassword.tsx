import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card } from './ui/Card';
import { validateEmail } from '../utils/validation';

interface ForgotPasswordProps {
  className?: string;
}

export const ForgotPassword: React.FC<ForgotPasswordProps> = ({ className = '' }) => {
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [emailError, setEmailError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setEmailError('');
    setSuccess(false);

    // Validate email
    const emailValidation = validateEmail(email);
    if (!emailValidation.isValid) {
      setEmailError(emailValidation.error || 'Invalid email');
      setIsLoading(false);
      return;
    }

    const result = await resetPassword(email);
    
    if (result.error) {
      setError(result.error);
    } else {
      setSuccess(true);
    }
    
    setIsLoading(false);
  };

  const handleEmailChange = (value: string) => {
    setEmail(value);
    if (emailError) {
      const validation = validateEmail(value);
      if (validation.isValid) {
        setEmailError('');
      }
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 ${className}`}>
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Reset your password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your email address and we'll send you a link to reset your password
          </p>
        </div>
        
        <Card>
          {success ? (
            <div className="text-center space-y-4">
              <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-md">
                Password reset email sent! Please check your inbox and follow the instructions to reset your password.
              </div>
              <div className="space-y-2">
                <Link to="/login">
                  <Button className="w-full">
                    Back to Login
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setSuccess(false);
                    setEmail('');
                    setError('');
                    setEmailError('');
                  }}
                >
                  Send Another Email
                </Button>
              </div>
            </div>
          ) : (
            <form className="space-y-6" onSubmit={handleSubmit}>
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
                  {error}
                </div>
              )}
              
              <Input
                label="Email address"
                type="email"
                value={email}
                onChange={handleEmailChange}
                error={emailError}
                required
                placeholder="Enter your email address"
              />

              <Button
                type="submit"
                loading={isLoading}
                className="w-full"
              >
                Send Reset Link
              </Button>
            </form>
          )}
          
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Remember your password?{' '}
              <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
                Sign in
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
