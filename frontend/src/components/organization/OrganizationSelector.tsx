import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { Organization } from "../../types";

interface OrganizationSelectorProps {
  className?: string;
}

const OrganizationSelector: React.FC<OrganizationSelectorProps> = ({
  className = "",
}) => {
  const { organizations, currentOrganization, setCurrentOrganization } =
    useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleOrganizationChange = async (organization: Organization) => {
    setLoading(true);
    try {
      setCurrentOrganization(organization);
      setIsOpen(false);
    } catch (error) {
      console.error("Error changing organization:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!organizations || organizations.length === 0) {
    return null;
  }

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        disabled={loading}
      >
        <span>
          {currentOrganization?.display_name ||
            currentOrganization?.name ||
            "Select Organization"}
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-300 rounded-md shadow-lg z-50">
          <div className="py-1">
            {organizations.map((userOrg) => (
              <button
                key={userOrg.organization.id}
                onClick={() => handleOrganizationChange(userOrg.organization)}
                className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${
                  currentOrganization?.id === userOrg.organization.id
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-700"
                }`}
              >
                <div className="font-medium">
                  {userOrg.organization.display_name ||
                    userOrg.organization.name}
                </div>
                <div className="text-xs text-gray-500 capitalize">
                  {userOrg.role}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default OrganizationSelector;
