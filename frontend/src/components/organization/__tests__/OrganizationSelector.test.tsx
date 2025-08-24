import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OrganizationSelector } from '../OrganizationSelector';
import { useAuth } from '../../../contexts/AuthContext';

// Mock the auth context
jest.mock('../../../contexts/AuthContext');
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// Mock organization data
const mockOrganizations = [
  {
    id: 'org-1',
    organization: {
      id: 'org-1',
      name: 'Acme Corp',
      display_name: 'Acme Corporation',
      domain: 'acme.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    },
    role: 'admin' as const,
    joined_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'org-2',
    organization: {
      id: 'org-2',
      name: 'Tech Startup',
      display_name: 'Tech Startup Inc',
      domain: 'techstartup.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    },
    role: 'member' as const,
    joined_at: '2024-01-01T00:00:00Z'
  }
];

describe('OrganizationSelector', () => {
  const mockSetCurrentOrganization = jest.fn();
  const mockInitiateSSO = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders SSO login button when no organizations are available', () => {
    mockUseAuth.mockReturnValue({
      organizations: [],
      currentOrganization: null,
      setCurrentOrganization: mockSetCurrentOrganization,
      initiateSSO: mockInitiateSSO,
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn(),
      refreshSession: jest.fn(),
      getUserOrganizations: jest.fn(),
      handleSSOCallback: jest.fn()
    });

    render(<OrganizationSelector />);
    
    expect(screen.getByText('Join Organization')).toBeInTheDocument();
    expect(screen.getByRole('button')).toHaveTextContent('Join Organization');
  });

  it('renders organization selector with current organization selected', () => {
    mockUseAuth.mockReturnValue({
      organizations: mockOrganizations,
      currentOrganization: mockOrganizations[0].organization,
      setCurrentOrganization: mockSetCurrentOrganization,
      initiateSSO: mockInitiateSSO,
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn(),
      refreshSession: jest.fn(),
      getUserOrganizations: jest.fn(),
      handleSSOCallback: jest.fn()
    });

    render(<OrganizationSelector />);
    
    expect(screen.getByText('Acme Corporation')).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument(); // Organization initial
  });

  it('opens dropdown and shows organization options when clicked', async () => {
    mockUseAuth.mockReturnValue({
      organizations: mockOrganizations,
      currentOrganization: null,
      setCurrentOrganization: mockSetCurrentOrganization,
      initiateSSO: mockInitiateSSO,
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn(),
      refreshSession: jest.fn(),
      getUserOrganizations: jest.fn(),
      handleSSOCallback: jest.fn()
    });

    render(<OrganizationSelector />);
    
    // Click to open dropdown
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      expect(screen.getByText('Personal')).toBeInTheDocument();
      expect(screen.getByText('Acme Corporation')).toBeInTheDocument();
      expect(screen.getByText('Tech Startup Inc')).toBeInTheDocument();
      expect(screen.getByText('Admin')).toBeInTheDocument();
      expect(screen.getByText('Join Another Organization')).toBeInTheDocument();
    });
  });

  it('selects organization when clicked', async () => {
    mockUseAuth.mockReturnValue({
      organizations: mockOrganizations,
      currentOrganization: null,
      setCurrentOrganization: mockSetCurrentOrganization,
      initiateSSO: mockInitiateSSO,
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn(),
      refreshSession: jest.fn(),
      getUserOrganizations: jest.fn(),
      handleSSOCallback: jest.fn()
    });

    render(<OrganizationSelector />);
    
    // Open dropdown
    fireEvent.click(screen.getByRole('button'));
    
    // Click on organization
    await waitFor(() => {
      fireEvent.click(screen.getByText('Acme Corporation'));
    });
    
    expect(mockSetCurrentOrganization).toHaveBeenCalledWith(mockOrganizations[0].organization);
  });

  it('selects personal workspace when clicked', async () => {
    mockUseAuth.mockReturnValue({
      organizations: mockOrganizations,
      currentOrganization: mockOrganizations[0].organization,
      setCurrentOrganization: mockSetCurrentOrganization,
      initiateSSO: mockInitiateSSO,
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn(),
      refreshSession: jest.fn(),
      getUserOrganizations: jest.fn(),
      handleSSOCallback: jest.fn()
    });

    render(<OrganizationSelector />);
    
    // Open dropdown
    fireEvent.click(screen.getByRole('button'));
    
    // Click on Personal
    await waitFor(() => {
      fireEvent.click(screen.getByText('Personal'));
    });
    
    expect(mockSetCurrentOrganization).toHaveBeenCalledWith(null);
  });

  it('initiates SSO when join organization is clicked', async () => {
    mockInitiateSSO.mockResolvedValue({ authUrl: 'https://sso.example.com/auth' });
    
    // Mock window.location.href
    delete (window as any).location;
    window.location = { href: '' } as any;

    mockUseAuth.mockReturnValue({
      organizations: mockOrganizations,
      currentOrganization: null,
      setCurrentOrganization: mockSetCurrentOrganization,
      initiateSSO: mockInitiateSSO,
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn(),
      refreshSession: jest.fn(),
      getUserOrganizations: jest.fn(),
      handleSSOCallback: jest.fn()
    });

    render(<OrganizationSelector />);
    
    // Open dropdown
    fireEvent.click(screen.getByRole('button'));
    
    // Click on join organization
    await waitFor(() => {
      fireEvent.click(screen.getByText('Join Another Organization'));
    });
    
    expect(mockInitiateSSO).toHaveBeenCalled();
    
    await waitFor(() => {
      expect(window.location.href).toBe('https://sso.example.com/auth');
    });
  });

  it('shows loading state during SSO initiation', async () => {
    mockInitiateSSO.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    mockUseAuth.mockReturnValue({
      organizations: [],
      currentOrganization: null,
      setCurrentOrganization: mockSetCurrentOrganization,
      initiateSSO: mockInitiateSSO,
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: jest.fn(),
      refreshSession: jest.fn(),
      getUserOrganizations: jest.fn(),
      handleSSOCallback: jest.fn()
    });

    render(<OrganizationSelector />);
    
    // Click SSO button
    fireEvent.click(screen.getByRole('button'));
    
    expect(screen.getByText('Connecting...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
