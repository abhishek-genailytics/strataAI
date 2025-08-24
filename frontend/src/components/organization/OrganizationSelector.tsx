import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Organization } from '../../types';

interface OrganizationSelectorProps {
  className?: string;
}

const OrganizationSelector: React.FC<OrganizationSelectorProps> = ({ className = '' }) => {
  const { organizations, currentOrganization, setCurrentOrganization, initiateSSO } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleOrganizationSelect = (organization: Organization) => {
    setCurrentOrganization(organization);
    setIsOpen(false);
  };

  const handleSSOLogin = async () => {
    setLoading(true);
    try {
      const result = await initiateSSO();
      if (result.authUrl) {
        window.location.href = result.authUrl;
      } else if (result.error) {
        console.error('SSO initiation failed:', result.error);
      }
    } catch (error) {
      console.error('SSO error:', error);
    } finally {
      setLoading(false);
    }
  };

  // If no organizations, show SSO login option
  if (organizations.length === 0) {
    return (
      <div className={`relative ${className}`}>
        <button
          onClick={handleSSOLogin}
          disabled={loading}
          className="flex items-center justify-between w-full px-3 py-2 text-sm bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
        >
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            {loading ? 'Connecting...' : 'Join Organization'}
          </span>
          {loading && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-3 py-2 text-sm bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <span className="flex items-center">
          <div className="w-6 h-6 mr-2 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-xs font-medium text-blue-600">
              {currentOrganization?.display_name?.[0] || currentOrganization?.name?.[0] || 'P'}
            </span>
          </div>
          <span className="truncate">
            {currentOrganization?.display_name || currentOrganization?.name || 'Personal'}
          </span>
        </span>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
          <div className="py-1">
            {/* Personal workspace option */}
            <button
              onClick={() => {
                setCurrentOrganization(null);
                setIsOpen(false);
              }}
              className={`flex items-center w-full px-3 py-2 text-sm hover:bg-gray-100 ${
                !currentOrganization ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
              }`}
            >
              <div className="w-6 h-6 mr-2 bg-gray-100 rounded-full flex items-center justify-center">
                <span className="text-xs font-medium text-gray-600">P</span>
              </div>
              <span>Personal</span>
              {!currentOrganization && (
                <svg className="w-4 h-4 ml-auto text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>

            {/* Organization options */}
            {organizations.map((userOrg) => (
              <button
                key={userOrg.organization.id}
                onClick={() => handleOrganizationSelect(userOrg.organization)}
                className={`flex items-center w-full px-3 py-2 text-sm hover:bg-gray-100 ${
                  currentOrganization?.id === userOrg.organization.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <div className="w-6 h-6 mr-2 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-medium text-blue-600">
                    {userOrg.organization.display_name?.[0] || userOrg.organization.name[0]}
                  </span>
                </div>
                <div className="flex-1 text-left">
                  <div className="truncate">
                    {userOrg.organization.display_name || userOrg.organization.name}
                  </div>
                  {userOrg.role === 'admin' && (
                    <div className="text-xs text-gray-500">Admin</div>
                  )}
                </div>
                {currentOrganization?.id === userOrg.organization.id && (
                  <svg className="w-4 h-4 ml-auto text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}

            {/* Divider and SSO login option */}
            <div className="border-t border-gray-200 my-1"></div>
            <button
              onClick={handleSSOLogin}
              disabled={loading}
              className="flex items-center w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
            >
              <svg className="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              {loading ? 'Connecting...' : 'Join Another Organization'}
              {loading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 ml-auto"></div>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default OrganizationSelector;
