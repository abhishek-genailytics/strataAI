import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "../ui/Button";
import { OrganizationSelector, OrganizationContext } from "../organization";

export const Header: React.FC = () => {
  const { user, signOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 relative z-10">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Organization Context */}
          <div className="flex items-center min-w-0 flex-1">
            <div className="flex-shrink-0 md:hidden">
              <h1 className="text-xl font-bold text-blue-600">StrataAI</h1>
            </div>
            <div className="hidden md:block">
              <p className="text-sm text-gray-500">Unified AI API Gateway</p>
              <OrganizationContext className="mt-1" />
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            >
              <span className="sr-only">Open main menu</span>
              {mobileMenuOpen ? (
                <svg
                  className="block h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                <svg
                  className="block h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              )}
            </button>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            <a
              href="/dashboard"
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150"
            >
              Dashboard
            </a>
            <a
              href="/playground"
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150"
            >
              Playground
            </a>

            <a
              href="/analytics"
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150"
            >
              Analytics
            </a>
          </nav>

          {/* Organization Selector and User menu */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            {user && (
              <>
                <OrganizationSelector className="w-40 lg:w-48" />
                <div className="flex items-center space-x-2">
                  <span className="hidden sm:block text-sm text-gray-700 truncate max-w-32">
                    {user.email}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleSignOut}
                    className="whitespace-nowrap"
                  >
                    Sign Out
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t border-gray-200">
            <a
              href="/dashboard"
              className="text-gray-500 hover:text-gray-700 block px-3 py-2 rounded-md text-base font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              Dashboard
            </a>
            <a
              href="/playground"
              className="text-gray-500 hover:text-gray-700 block px-3 py-2 rounded-md text-base font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              Playground
            </a>

            <a
              href="/analytics"
              className="text-gray-500 hover:text-gray-700 block px-3 py-2 rounded-md text-base font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              Analytics
            </a>
          </div>
        </div>
      )}
    </header>
  );
};
