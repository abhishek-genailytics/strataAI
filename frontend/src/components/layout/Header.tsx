import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/Button';
import { OrganizationSelector, OrganizationContext } from '../organization';

export const Header: React.FC = () => {
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Organization Context */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-2xl font-bold text-primary-600">StrataAI</h1>
            </div>
            <div className="hidden md:block ml-4">
              <p className="text-sm text-gray-500">Unified AI API Gateway</p>
              <OrganizationContext className="mt-1" />
            </div>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex space-x-8">
            <a
              href="/dashboard"
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Dashboard
            </a>
            <a
              href="/playground"
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Playground
            </a>
            <a
              href="/api-keys"
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              API Keys
            </a>
            <a
              href="/analytics"
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Analytics
            </a>
          </nav>

          {/* Organization Selector and User menu */}
          <div className="flex items-center space-x-4">
            {user && (
              <>
                <OrganizationSelector className="w-48" />
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-700">{user.email}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleSignOut}
                  >
                    Sign Out
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
