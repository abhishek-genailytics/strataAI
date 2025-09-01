import React from "react";
import { useAuth } from "../../contexts/AuthContext";

interface OrganizationContextProps {
  className?: string;
}

const OrganizationContext: React.FC<OrganizationContextProps> = ({
  className = "",
}) => {
  const { currentOrganization, organizations } = useAuth();

  // Find current user's role in the organization
  const currentUserOrg = organizations.find(
    (uo) => uo.organization.id === currentOrganization?.id
  );
  const userRole = currentUserOrg?.role;

  if (!currentOrganization) {
    return (
      <div className={`text-xs text-gray-500 ${className}`}>
        Personal Workspace
      </div>
    );
  }

  return (
    <div className={`text-xs text-gray-500 ${className}`}>
      <div className="flex items-center space-x-2">
        <span>
          {currentOrganization.display_name || currentOrganization.name}
        </span>
        {userRole && (
          <>
            <span>•</span>
            <span
              className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                userRole === "admin"
                  ? "bg-blue-100 text-blue-700"
                  : userRole === "no_org"
                  ? "bg-orange-100 text-orange-700"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {userRole === "admin"
                ? "Admin"
                : userRole === "no_org"
                ? "No Org"
                : "Member"}
            </span>
          </>
        )}
      </div>
      {currentOrganization.domain && (
        <div className="text-gray-400 mt-0.5">{currentOrganization.domain}</div>
      )}
    </div>
  );
};

export default OrganizationContext;
