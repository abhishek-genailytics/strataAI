import React from 'react';
import { useOrganizationApi } from '../hooks/useOrganizationApi';

interface OrganizationProviderProps {
  children: React.ReactNode;
}

/**
 * Provider component that automatically manages organization context for API calls
 */
export const OrganizationProvider: React.FC<OrganizationProviderProps> = ({ children }) => {
  // This hook automatically sets organization context headers
  useOrganizationApi();

  return <>{children}</>;
};
