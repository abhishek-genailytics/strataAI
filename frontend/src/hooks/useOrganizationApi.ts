import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';

/**
 * Hook to automatically set organization context headers for API calls
 */
export const useOrganizationApi = () => {
  const { currentOrganization } = useAuth();

  useEffect(() => {
    // Update API service with organization context
    if (currentOrganization) {
      // Set organization header for all API calls
      apiService.setOrganizationContext(currentOrganization.id);
    } else {
      // Clear organization context for personal workspace
      apiService.clearOrganizationContext();
    }
  }, [currentOrganization]);

  return {
    currentOrganization,
    organizationId: currentOrganization?.id || null,
    isPersonalWorkspace: !currentOrganization
  };
};
