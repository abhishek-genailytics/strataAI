import React, { useState, useEffect } from "react";
import { MultiSelect, MultiSelectOption } from "./MultiSelect";
import { apiService } from "../../services/api";

export interface User {
  id: string;
  email: string;
  display_name?: string;
  role: "admin" | "member" | "no_org";
  status: "active" | "pending" | "inactive";
  created_at: string;
  last_activity?: string;
}

export interface UserSelectorProps {
  label?: string;
  placeholder?: string;
  selectedUserIds: string[];
  onChange: (userIds: string[]) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  organizationId?: string;
  excludeCurrentUser?: boolean;
}

export const UserSelector: React.FC<UserSelectorProps> = ({
  label = "Collaborators",
  placeholder = "Select collaborators...",
  selectedUserIds,
  onChange,
  error,
  disabled = false,
  required = false,
  className = "",
  organizationId,
  excludeCurrentUser = true,
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load organization users
  useEffect(() => {
    const loadUsers = async () => {
      if (!organizationId) return;

      setLoading(true);
      setErrorMessage(null);

      try {
        // Set organization context for API calls
        apiService.setOrganizationContext(organizationId);

        const response = await apiService.get("/user-management/users", {
          params: { organization_id: organizationId },
        });

        if (response.error) {
          throw new Error(response.error);
        }

        let userList = response.data || [];

        // Filter out current user if requested
        if (excludeCurrentUser) {
          // Get current user from localStorage or context
          const currentUserEmail = localStorage.getItem("strataai-user-email");
          if (currentUserEmail) {
            userList = userList.filter(
              (user: User) => user.email !== currentUserEmail
            );
          }
        }

        // Filter to only active users
        userList = userList.filter((user: User) => user.status === "active");

        setUsers(userList);
      } catch (err) {
        console.error("Failed to load users:", err);
        setErrorMessage("Failed to load organization users");
        setUsers([]);
      } finally {
        setLoading(false);
      }
    };

    loadUsers();
  }, [organizationId, excludeCurrentUser]);

  // Convert users to MultiSelect options
  const userOptions: MultiSelectOption[] = users.map((user) => ({
    id: user.id,
    label: user.display_name || user.email,
    value: user.id,
    description: user.display_name ? user.email : undefined,
    disabled: user.status !== "active",
  }));

  // Handle loading state
  if (loading) {
    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-semibold text-slate-700">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <div className="block w-full px-4 py-3 border border-slate-300 rounded-xl bg-slate-50">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span className="text-sm text-slate-500">Loading users...</span>
          </div>
        </div>
      </div>
    );
  }

  // Handle error state
  if (errorMessage) {
    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-semibold text-slate-700">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <div className="block w-full px-4 py-3 border border-red-300 rounded-xl bg-red-50">
          <div className="flex items-center space-x-2">
            <svg
              className="w-4 h-4 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-sm text-red-600">{errorMessage}</span>
          </div>
        </div>
      </div>
    );
  }

  // Handle empty state
  if (users.length === 0) {
    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-semibold text-slate-700">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <div className="block w-full px-4 py-3 border border-slate-300 rounded-xl bg-slate-50">
          <span className="text-sm text-slate-500">
            No collaborators available
          </span>
        </div>
      </div>
    );
  }

  return (
    <MultiSelect
      label={label}
      placeholder={placeholder}
      options={userOptions}
      selectedValues={selectedUserIds}
      onChange={onChange}
      error={error || undefined}
      disabled={disabled}
      required={required}
      className={className}
      searchable={true}
      showSelectAll={true}
    />
  );
};
