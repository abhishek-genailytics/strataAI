// ScaleKit service for frontend integration
// Uses backend API endpoints instead of direct SDK integration

export interface ScaleKitSSOOptions {
  redirectUri: string;
  state?: string;
  organizationId?: string;
  connectionId?: string;
  loginHint?: string;
}

export interface ScaleKitCallbackOptions {
  code: string;
  state?: string;
  redirectUri: string;
}

export interface ScaleKitAuthResult {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    provider: string;
  };
  organization?: {
    id: string;
    name: string;
    display_name: string;
    domain?: string;
  };
}

export const scalekitService = {
  /**
   * Initiate SSO flow via backend API
   */
  initiateSSO: async (options: ScaleKitSSOOptions): Promise<{ authorization_url: string; state: string }> => {
    const response = await fetch('/api/v1/auth/scalekit/initiate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        redirect_uri: options.redirectUri,
        organization_id: options.organizationId,
        connection_id: options.connectionId,
        login_hint: options.loginHint,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to initiate SSO');
    }

    return response.json();
  },

  /**
   * Handle SSO callback via backend API
   */
  handleCallback: async (options: ScaleKitCallbackOptions): Promise<ScaleKitAuthResult> => {
    const response = await fetch('/api/v1/auth/scalekit/callback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        code: options.code,
        state: options.state,
        redirect_uri: options.redirectUri,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'SSO authentication failed');
    }

    return response.json();
  },

  /**
   * Validate ScaleKit token via backend API
   */
  validateToken: async (): Promise<{ valid: boolean; user?: any }> => {
    try {
      const response = await fetch('/api/v1/auth/scalekit/validate', {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        return { valid: false };
      }

      const result = await response.json();
      return result;
    } catch {
      return { valid: false };
    }
  },

  /**
   * Logout from ScaleKit SSO via backend API
   */
  logout: async (): Promise<void> => {
    const response = await fetch('/api/v1/auth/scalekit/logout', {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Logout failed');
    }
  },

  /**
   * Generate direct SSO redirect URL
   */
  getRedirectUrl: (organizationId?: string): string => {
    const baseUrl = '/api/v1/auth/scalekit/redirect';
    if (organizationId) {
      return `${baseUrl}?organization_id=${encodeURIComponent(organizationId)}`;
    }
    return baseUrl;
  },
};
