import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface SSOButtonProps {
  organizationId?: string;
  connectionId?: string;
  loginHint?: string;
  className?: string;
  children?: React.ReactNode;
}

const SSOButton: React.FC<SSOButtonProps> = ({
  organizationId,
  connectionId,
  loginHint,
  className = '',
  children = 'Sign in with SSO'
}) => {
  const { initiateSSO } = useAuth();

  const handleSSOLogin = async () => {
    try {
      const result = await initiateSSO(organizationId, connectionId);
      
      if (result.authUrl) {
        // Redirect to ScaleKit authorization URL
        window.location.href = result.authUrl;
      } else if (result.error) {
        console.error('SSO initiation failed:', result.error);
        // You could show a toast notification here
      }
    } catch (error) {
      console.error('SSO error:', error);
    }
  };

  return (
    <button
      onClick={handleSSOLogin}
      className={`w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors ${className}`}
    >
      <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-2 0V5H5v10h10v-1a1 1 0 112 0v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm7.707 3.293a1 1 0 010 1.414L9.414 10l1.293 1.293a1 1 0 01-1.414 1.414l-2-2a1 1 0 010-1.414l2-2a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
      {children}
    </button>
  );
};

export default SSOButton;
