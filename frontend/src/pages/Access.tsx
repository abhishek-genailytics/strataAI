import React, { useState, useEffect } from "react";
import {
  Search,
  Plus,
  MoreHorizontal,
  Trash2,
  Edit,
  Shield,
  Copy,
  Check,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Modal } from "../components/ui/Modal";
import { Input } from "../components/ui/Input";
import { useAuth } from "../contexts/AuthContext";
import {
  userManagementService,
  User,
  PersonalAccessToken,
  PersonalAccessTokenCreate,
} from "../services/userManagementService";
import { useToast } from "../contexts/ToastContext";

// Remove the duplicate interfaces since we're importing them from the service

export const Access: React.FC = () => {
  const { currentOrganization } = useAuth();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<"users" | "tokens">("users");
  const [users, setUsers] = useState<User[]>([]);
  const [tokens, setTokens] = useState<PersonalAccessToken[]>([]);
  const [newlyCreatedToken, setNewlyCreatedToken] =
    useState<PersonalAccessTokenCreate | null>(null);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [showNewTokenModal, setShowNewTokenModal] = useState(false);

  const [searchTerm, setSearchTerm] = useState("");
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "member">("member");
  const [tokenName, setTokenName] = useState("");
  const [tokenExpiration, setTokenExpiration] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const tabs = [
    { key: "users", label: "Users", icon: "👥" },
    { key: "tokens", label: "Personal Access Tokens", icon: "🔑" },
  ];

  // Load data on component mount
  useEffect(() => {
    loadUsers();
    loadTokens();
  }, []);

  const loadUsers = async () => {
    try {
      const usersData = await userManagementService.getOrganizationUsers();
      setUsers(usersData);
    } catch (error) {
      console.error("Failed to load users:", error);
      showToast("error", "Failed to load users");
    }
  };

  const loadTokens = async () => {
    try {
      const tokensData = await userManagementService.getPersonalAccessTokens();
      setTokens(tokensData);
    } catch (error) {
      console.error("Failed to load tokens:", error);
      showToast("error", "Failed to load tokens");
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.displayName?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredTokens = tokens.filter((t) =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleInviteUser = async () => {
    if (!inviteEmail) return;

    setIsLoading(true);
    try {
      await userManagementService.inviteUser({
        email: inviteEmail,
        role: inviteRole,
      });

      showToast("success", "User invitation sent successfully");
      setShowInviteModal(false);
      setInviteEmail("");
      setInviteRole("member");

      // Reload users to show the new invitation
      await loadUsers();
    } catch (error: any) {
      console.error("Failed to invite user:", error);
      showToast(
        "error",
        error.response?.data?.detail || "Failed to invite user"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateToken = async () => {
    if (!tokenName) return;

    setIsLoading(true);
    try {
      const newToken = await userManagementService.createPersonalAccessToken({
        name: tokenName,
        expiresAt: tokenExpiration || undefined,
      });

      setNewlyCreatedToken(newToken);
      setShowNewTokenModal(true);
      setShowTokenModal(false);
      setTokenName("");
      setTokenExpiration("");

      // Reload tokens
      await loadTokens();
    } catch (error: any) {
      console.error("Failed to create token:", error);
      showToast(
        "error",
        error.response?.data?.detail || "Failed to create token"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (window.confirm("Are you sure you want to remove this user?")) {
      try {
        await userManagementService.removeUser(userId);
        showToast("success", "User removed successfully");
        await loadUsers();
      } catch (error: any) {
        console.error("Failed to remove user:", error);
        showToast(
          "error",
          error.response?.data?.detail || "Failed to remove user"
        );
      }
    }
  };

  const handleDeleteToken = async (tokenId: string) => {
    if (
      window.confirm(
        "Are you sure you want to delete this token? This action cannot be undone."
      )
    ) {
      try {
        await userManagementService.deletePersonalAccessToken(tokenId);
        showToast("success", "Token deleted successfully");
        await loadTokens();
      } catch (error: any) {
        console.error("Failed to delete token:", error);
        showToast(
          "error",
          error.response?.data?.detail || "Failed to delete token"
        );
      }
    }
  };

  const handleCopyToken = async (token: string) => {
    try {
      await navigator.clipboard.writeText(token);
      setCopiedToken(token);
      showToast("success", "Token copied to clipboard");
      setTimeout(() => setCopiedToken(null), 2000);
    } catch (error) {
      console.error("Failed to copy token:", error);
      showToast("error", "Failed to copy token");
    }
  };

  // Helper functions moved to userManagementService

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Access Management
          </h1>
          <p className="text-slate-600 mt-1">
            Manage users and access tokens for your{" "}
            {currentOrganization ? "organization" : "workspace"}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 bg-white rounded-t-xl shadow-sm">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-all duration-200 flex items-center space-x-2 ${
                activeTab === tab.key
                  ? "border-blue-500 text-blue-600 bg-blue-50/50"
                  : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <Card className="bg-white shadow-lg border border-slate-200 min-h-[600px]">
        {activeTab === "users" && (
          <div className="space-y-6">
            {/* Users Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900 uppercase tracking-wide">
                  ALL USERS
                </h2>
                <p className="text-sm text-slate-500">
                  Showing 1 to {filteredUsers.length} of {users.length} results
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
                  />
                </div>
                <Button
                  onClick={() => setShowInviteModal(true)}
                  className="bg-slate-900 hover:bg-slate-800"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Invite User
                </Button>
              </div>
            </div>

            {/* Users Table */}
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      EMAIL
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      DISPLAY NAME
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      ROLE
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      ACTIONS
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-100">
                  {filteredUsers.map((user) => (
                    <tr
                      key={user.id}
                      className="hover:bg-slate-50 transition-colors duration-150"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-sm mr-3">
                            {user.email[0].toUpperCase()}
                          </div>
                          <span className="text-sm font-medium text-slate-900">
                            {user.email}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {user.displayName ? (
                            <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-full flex items-center justify-center text-white font-semibold text-sm mr-3">
                              {user.displayName[0].toUpperCase()}
                            </div>
                          ) : (
                            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center text-slate-500 font-semibold text-sm mr-3">
                              —
                            </div>
                          )}
                          <span className="text-sm text-slate-900">
                            {user.displayName || "—"}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${userManagementService.getRoleColor(
                            user.role
                          )}`}
                        >
                          {user.role === "no_org"
                            ? "NO ORG"
                            : user.role.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-slate-500 hover:text-slate-700"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-slate-500 hover:text-red-600"
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between border-t border-slate-200 pt-4">
              <div className="text-sm text-slate-500">
                Showing 1 to {filteredUsers.length} of {users.length} results
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-slate-500">Rows per page</span>
                  <select className="border border-slate-300 rounded px-2 py-1 text-sm focus:ring-blue-500 focus:border-blue-500">
                    <option>25</option>
                    <option>50</option>
                    <option>100</option>
                  </select>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled
                    className="text-slate-400"
                  >
                    Previous
                  </Button>
                  <span className="px-3 py-1 bg-blue-600 text-white rounded text-sm font-medium">
                    1
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled
                    className="text-slate-400"
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "tokens" && (
          <div className="space-y-6">
            {/* Tokens Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900 uppercase tracking-wide">
                  ALL PATs
                </h2>
                <p className="text-sm text-slate-500">
                  Showing 1 to {filteredTokens.length} of {tokens.length}{" "}
                  results
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search tokens..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
                  />
                </div>
                <Button
                  onClick={() => setShowTokenModal(true)}
                  className="bg-slate-900 hover:bg-slate-800"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Personal Access Token
                </Button>
              </div>
            </div>

            {/* Tokens Table */}
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      PERSONAL ACCESS TOKEN NAME
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      CREATED AT
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      EXPIRATION DATE
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      ACTIONS
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-100">
                  {filteredTokens.map((token) => (
                    <tr
                      key={token.id}
                      className="hover:bg-slate-50 transition-colors duration-150"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-red-600 rounded-full flex items-center justify-center text-white font-semibold text-sm mr-3">
                            🔑
                          </div>
                          <div>
                            <div className="text-sm font-medium text-slate-900">
                              {token.name}
                            </div>
                            <div className="text-xs font-mono text-slate-500">
                              {token.tokenPrefix}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-slate-900">
                          {userManagementService.formatDate(token.createdAt)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-slate-900">
                          {token.expiresAt
                            ? userManagementService.formatDate(token.expiresAt)
                            : "—"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteToken(token.id)}
                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Token Pagination */}
            <div className="flex items-center justify-between border-t border-slate-200 pt-4">
              <div className="text-sm text-slate-500">
                Showing 1 to {filteredTokens.length} of {tokens.length} results
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-slate-500">Rows per page</span>
                  <select className="border border-slate-300 rounded px-2 py-1 text-sm focus:ring-blue-500 focus:border-blue-500">
                    <option>10</option>
                    <option>25</option>
                    <option>50</option>
                  </select>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled
                    className="text-slate-400"
                  >
                    Previous
                  </Button>
                  <span className="px-3 py-1 bg-blue-600 text-white rounded text-sm font-medium">
                    1
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled
                    className="text-slate-400"
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Invite User Modal */}
      <Modal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        title="Invite User"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Email Address *"
            type="email"
            placeholder="user@example.com"
            value={inviteEmail}
            onChange={setInviteEmail}
            required
          />

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Role *
            </label>
            <select
              value={inviteRole}
              onChange={(e) =>
                setInviteRole(e.target.value as "admin" | "member")
              }
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowInviteModal(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleInviteUser}
              loading={isLoading}
              disabled={!inviteEmail}
            >
              Send Invitation
            </Button>
          </div>
        </div>
      </Modal>

      {/* Create Token Modal */}
      <Modal
        isOpen={showTokenModal}
        onClose={() => setShowTokenModal(false)}
        title="Create Personal Access Token"
        size="md"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <Shield className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-blue-900">
                  Security Notice
                </h4>
                <p className="text-sm text-blue-700 mt-1">
                  Personal access tokens function like passwords. Keep them
                  secure and don't share them.
                </p>
              </div>
            </div>
          </div>

          <Input
            label="Token Name *"
            placeholder="e.g., production-api-access"
            value={tokenName}
            onChange={setTokenName}
            required
          />

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Expiration (Optional)
            </label>
            <input
              type="date"
              value={tokenExpiration}
              onChange={(e) => setTokenExpiration(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowTokenModal(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateToken}
              loading={isLoading}
              disabled={!tokenName}
            >
              Create Token
            </Button>
          </div>
        </div>
      </Modal>

      {/* New Token Modal */}
      <Modal
        isOpen={showNewTokenModal}
        onClose={() => setShowNewTokenModal(false)}
        title="Personal Access Token Created"
        size="lg"
      >
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start">
              <Shield className="w-5 h-5 text-green-600 mr-3 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-green-900">
                  Token Created Successfully
                </h4>
                <p className="text-sm text-green-700 mt-1">
                  Make sure to copy your token now. You won't be able to see it
                  again!
                </p>
              </div>
            </div>
          </div>

          {newlyCreatedToken && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Token Name
                </label>
                <div className="text-sm text-slate-900 bg-slate-50 px-3 py-2 rounded border">
                  {newlyCreatedToken.name}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Personal Access Token
                </label>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-slate-50 px-3 py-2 rounded border font-mono text-sm">
                    {newlyCreatedToken.token}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopyToken(newlyCreatedToken.token)}
                    className="flex-shrink-0"
                  >
                    {copiedToken === newlyCreatedToken.token ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Scopes
                </label>
                <div className="flex flex-wrap gap-2">
                  {newlyCreatedToken.scopes.map((scope) => (
                    <span
                      key={scope}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {scope}
                    </span>
                  ))}
                </div>
              </div>

              {newlyCreatedToken.expiresAt && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Expires At
                  </label>
                  <div className="text-sm text-slate-900 bg-slate-50 px-3 py-2 rounded border">
                    {userManagementService.formatDate(
                      newlyCreatedToken.expiresAt
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              onClick={() => setShowNewTokenModal(false)}
              className="bg-slate-900 hover:bg-slate-800"
            >
              Done
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
