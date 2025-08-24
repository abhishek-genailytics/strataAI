import React, { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';

export const Login: React.FC = () => {
  const { signIn, user, loading } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const from = location.state?.from?.pathname || '/dashboard';

  if (user) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const result = await signIn(email, password);
    
    if (result.error) {
      setError(result.error);
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
            Sign in to StrataAI
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your unified AI API gateway
          </p>
        </div>
        
        <Card>
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

            <Button
              type="submit"
              loading={isLoading}
              className="w-full"
            >
              Sign in
            </Button>
          </form>
          
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <a href="/register" className="font-medium text-primary-600 hover:text-primary-500">
                Sign up
              </a>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
