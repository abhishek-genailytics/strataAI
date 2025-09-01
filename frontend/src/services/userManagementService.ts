import { apiService } from "./api";

export interface User {
  id: string;
  email: string;
  displayName?: string;
  role: "admin" | "member" | "no_org";
  status: "active" | "pending" | "inactive";
  createdAt: string;
  lastActivity?: string;
}

export interface PersonalAccessToken {
  id: string;
  name: string;
  tokenPrefix: string;
  scopes: string[];
  createdAt: string;
  expiresAt?: string;
  lastUsedAt?: string;
}

export interface PersonalAccessTokenCreate {
  id: string;
  name: string;
  token: string; // Only returned once during creation
  tokenPrefix: string;
  scopes: string[];
  createdAt: string;
  expiresAt?: string;
}

export interface UserInvitation {
  id: string;
  email: string;
  role: "admin" | "member";
  status: string;
  invitedBy: string;
  createdAt: string;
  expiresAt: string;
}

export interface CreateTokenRequest {
  name: string;
  scopes?: string[];
  expiresAt?: string;
}

export interface InviteUserRequest {
  email: string;
  role: "admin" | "member";
  organizationId?: string;
}

class UserManagementService {
  // User Management
  async getOrganizationUsers(organizationId?: string): Promise<User[]> {
    const params = organizationId ? { organization_id: organizationId } : {};
    const response = await apiService.get("/user-management/users", { params });

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data.map((user: any) => ({
      id: user.id,
      email: user.email,
      displayName: user.display_name,
      role: user.role,
      status: user.status,
      createdAt: user.created_at,
      lastActivity: user.last_activity,
    }));
  }

  async inviteUser(invitation: InviteUserRequest): Promise<UserInvitation> {
    const response = await apiService.post(
      "/user-management/invite",
      invitation
    );

    if (response.error) {
      throw new Error(response.error);
    }

    const data = response.data;
    return {
      id: data.id,
      email: data.email,
      role: data.role,
      status: data.status,
      invitedBy: data.invited_by,
      createdAt: data.created_at,
      expiresAt: data.expires_at,
    };
  }

  async removeUser(userId: string, organizationId?: string): Promise<void> {
    const params = organizationId ? { organization_id: organizationId } : {};
    const response = await apiService.delete(
      `/user-management/users/${userId}`,
      { params }
    );

    if (response.error) {
      throw new Error(response.error);
    }
  }

  // Personal Access Tokens
  async getPersonalAccessTokens(): Promise<PersonalAccessToken[]> {
    const response = await apiService.get("/user-management/tokens");

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data.map((token: any) => ({
      id: token.id,
      name: token.name,
      tokenPrefix: token.token_prefix,
      scopes: token.scopes,
      createdAt: token.created_at,
      expiresAt: token.expires_at,
      lastUsedAt: token.last_used_at,
    }));
  }

  async createPersonalAccessToken(
    tokenRequest: CreateTokenRequest
  ): Promise<PersonalAccessTokenCreate> {
    const response = await apiService.post(
      "/user-management/tokens",
      tokenRequest
    );

    if (response.error) {
      throw new Error(response.error);
    }

    const data = response.data;
    return {
      id: data.id,
      name: data.name,
      token: data.token, // Only returned once
      tokenPrefix: data.token_prefix,
      scopes: data.scopes,
      createdAt: data.created_at,
      expiresAt: data.expires_at,
    };
  }

  async deletePersonalAccessToken(tokenId: string): Promise<void> {
    const response = await apiService.delete(
      `/user-management/tokens/${tokenId}`
    );

    if (response.error) {
      throw new Error(response.error);
    }
  }

  // Helper methods
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("en-US", {
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  getRoleColor(role: string): string {
    switch (role) {
      case "admin":
        return "bg-blue-100 text-blue-800 border border-blue-200";
      case "member":
        return "bg-gray-100 text-gray-800 border border-gray-200";
      case "no_org":
        return "bg-orange-100 text-orange-800 border border-orange-200";
      default:
        return "bg-gray-100 text-gray-800 border border-gray-200";
    }
  }

  getStatusColor(status: string): string {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "inactive":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  }
}

export const userManagementService = new UserManagementService();
