import { renderHook } from '@testing-library/react';
import { useOrganizationApi } from '../useOrganizationApi';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';

// Mock dependencies
jest.mock('../../contexts/AuthContext');
jest.mock('../../services/api');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockApiService = apiService as jest.Mocked<typeof apiService>;

describe('useOrganizationApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('sets organization context when currentOrganization is provided', () => {
    const mockOrganization = {
      id: 'org-123',
      name: 'Test Organization',
      display_name: 'Test Organization Inc',
      domain: 'test.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    };

    mockUseAuth.mockReturnValue({
      currentOrganization: mockOrganization,
      organizations: [],
      setCurrentOrganization: jest.fn(),
      initiateSSO: jest.fn(),
      handleSSOCallback: jest.fn(),
      getUserOrganizations: jest.fn(),
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn()
    });

    const { result } = renderHook(() => useOrganizationApi());

    expect(mockApiService.setOrganizationContext).toHaveBeenCalledWith('org-123');
    expect(result.current.currentOrganization).toBe(mockOrganization);
    expect(result.current.organizationId).toBe('org-123');
    expect(result.current.isPersonalWorkspace).toBe(false);
  });

  it('clears organization context when currentOrganization is null', () => {
    mockUseAuth.mockReturnValue({
      currentOrganization: null,
      organizations: [],
      setCurrentOrganization: jest.fn(),
      initiateSSO: jest.fn(),
      handleSSOCallback: jest.fn(),
      getUserOrganizations: jest.fn(),
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn()
    });

    const { result } = renderHook(() => useOrganizationApi());

    expect(mockApiService.clearOrganizationContext).toHaveBeenCalled();
    expect(result.current.currentOrganization).toBe(null);
    expect(result.current.organizationId).toBe(null);
    expect(result.current.isPersonalWorkspace).toBe(true);
  });

  it('updates organization context when currentOrganization changes', () => {
    const mockOrganization1 = {
      id: 'org-123',
      name: 'Test Organization 1',
      display_name: 'Test Organization 1 Inc',
      domain: 'test1.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    };

    const mockOrganization2 = {
      id: 'org-456',
      name: 'Test Organization 2',
      display_name: 'Test Organization 2 Inc',
      domain: 'test2.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    };

    // Initial render with first organization
    mockUseAuth.mockReturnValue({
      currentOrganization: mockOrganization1,
      organizations: [],
      setCurrentOrganization: jest.fn(),
      initiateSSO: jest.fn(),
      handleSSOCallback: jest.fn(),
      getUserOrganizations: jest.fn(),
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn()
    });

    const { rerender } = renderHook(() => useOrganizationApi());

    expect(mockApiService.setOrganizationContext).toHaveBeenCalledWith('org-123');

    // Update to second organization
    mockUseAuth.mockReturnValue({
      currentOrganization: mockOrganization2,
      organizations: [],
      setCurrentOrganization: jest.fn(),
      initiateSSO: jest.fn(),
      handleSSOCallback: jest.fn(),
      getUserOrganizations: jest.fn(),
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn()
    });

    rerender();

    expect(mockApiService.setOrganizationContext).toHaveBeenCalledWith('org-456');
  });

  it('switches from organization to personal workspace', () => {
    const mockOrganization = {
      id: 'org-123',
      name: 'Test Organization',
      display_name: 'Test Organization Inc',
      domain: 'test.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    };

    // Initial render with organization
    mockUseAuth.mockReturnValue({
      currentOrganization: mockOrganization,
      organizations: [],
      setCurrentOrganization: jest.fn(),
      initiateSSO: jest.fn(),
      handleSSOCallback: jest.fn(),
      getUserOrganizations: jest.fn(),
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn()
    });

    const { rerender, result } = renderHook(() => useOrganizationApi());

    expect(mockApiService.setOrganizationContext).toHaveBeenCalledWith('org-123');
    expect(result.current.isPersonalWorkspace).toBe(false);

    // Switch to personal workspace
    mockUseAuth.mockReturnValue({
      currentOrganization: null,
      organizations: [],
      setCurrentOrganization: jest.fn(),
      initiateSSO: jest.fn(),
      handleSSOCallback: jest.fn(),
      getUserOrganizations: jest.fn(),
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn()
    });

    rerender();

    expect(mockApiService.clearOrganizationContext).toHaveBeenCalled();
    expect(result.current.isPersonalWorkspace).toBe(true);
  });
});
