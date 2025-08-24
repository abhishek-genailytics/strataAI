import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';

export const Register: React.FC = () => {
  const { signUp, user, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess(false);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      setIsLoading(false);
      return;
    }

    const result = await signUp(email, password);
    
    if (result.error) {
      setError(result.error);
    } else {
      setSuccess(true);
    }
    
    setIsLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your StrataAI account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Get started with your unified AI API gateway
          </p>
        </div>
        
        <Card>
          {success ? (
            <div className="text-center space-y-4">
              <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-md">
                Registration successful! Please check your email to verify your account.
              </div>
              <Button onClick={() => window.location.href = '/login'}>
                Go to Login
              </Button>
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
                onChange={setEmail}
                required
                placeholder="Enter your email"
              />
              
              <Input
                label="Password"
                type="password"
                value={password}
                onChange={setPassword}
                required
                placeholder="Enter your password"
              />

              <Input
                label="Confirm Password"
                type="password"
                value={confirmPassword}
                onChange={setConfirmPassword}
                required
                placeholder="Confirm your password"
              />

              <Button
                type="submit"
                loading={isLoading}
                className="w-full"
              >
                Create Account
              </Button>
            </form>
          )}
          
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <a href="/login" className="font-medium text-primary-600 hover:text-primary-500">
                Sign in
              </a>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
