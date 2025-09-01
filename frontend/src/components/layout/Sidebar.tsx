import React, { useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import {
  Play,
  Grid3X3,
  BarChart3,
  Server,
  Shield,
  Settings,
  Monitor,
  Users,
  ChevronUp,
  ChevronDown,
} from "lucide-react";

interface SidebarItem {
  name: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

interface SidebarSection {
  title: string;
  items: SidebarItem[];
  collapsible?: boolean;
}

const aiGatewaySection: SidebarSection = {
  title: "AI Gateway",
  items: [
    {
      name: "Playground",
      href: "/playground",
      icon: <Play className="w-5 h-5" />,
    },
    {
      name: "Models",
      href: "/models",
      icon: <Grid3X3 className="w-5 h-5" />,
    },
    {
      name: "Monitor",
      href: "/monitor",
      icon: <BarChart3 className="w-5 h-5" />,
    },
    {
      name: "MCP Servers",
      href: "/mcp-servers",
      icon: <Server className="w-5 h-5" />,
    },
    {
      name: "Guardrails",
      href: "/guardrails",
      icon: <Shield className="w-5 h-5" />,
    },
    {
      name: "Configs",
      href: "/configs",
      icon: <Settings className="w-5 h-5" />,
    },
  ],
  collapsible: true,
};

const controlPanelSection: SidebarSection = {
  title: "CONTROL PANEL",
  items: [
    {
      name: "Platform",
      href: "/platform",
      icon: <Monitor className="w-5 h-5" />,
    },
    {
      name: "Access",
      href: "/access",
      icon: <Users className="w-5 h-5" />,
    },
  ],
};

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [aiGatewayCollapsed, setAiGatewayCollapsed] = useState(false);

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return location.pathname === "/" || location.pathname === "/dashboard";
    }
    return location.pathname === href;
  };

  const renderSection = (
    section: SidebarSection,
    isCollapsed: boolean = false
  ) => (
    <div key={section.title} className="mb-6">
      <div className="flex items-center justify-between px-3 mb-2">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          {section.title}
        </h3>
        {section.collapsible && (
          <button
            onClick={() => setAiGatewayCollapsed(!aiGatewayCollapsed)}
            className="text-gray-400 hover:text-gray-300 transition-colors"
          >
            {isCollapsed ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronUp className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {(!section.collapsible || !isCollapsed) && (
        <nav className="space-y-1">
          {section.items.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`${
                isActive(item.href)
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-gray-700 hover:text-white"
              } group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150`}
            >
              <span className="mr-3 flex-shrink-0">{item.icon}</span>
              {item.name}
              {item.badge && (
                <span className="ml-auto bg-gray-600 text-gray-300 text-xs px-2 py-1 rounded-full">
                  {item.badge}
                </span>
              )}
            </Link>
          ))}
        </nav>
      )}
    </div>
  );

  return (
    <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 md:z-50">
      <div className="flex flex-col flex-1 min-h-0 bg-white border-r border-gray-200">
        {/* Header */}
        <div className="flex items-center h-16 flex-shrink-0 px-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <button 
              type="button"
              onClick={() => window.history.back()}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  window.history.back();
                }
              }}
              className="text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 rounded-md p-1"
              aria-label="Go back"
              role="button"
              tabIndex={0}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-gray-900">v0.79.7</h1>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
          <div className="px-3">
            {renderSection(aiGatewaySection, aiGatewayCollapsed)}
            {renderSection(controlPanelSection)}
          </div>
        </div>

        {/* User Info */}
        <div className="flex-shrink-0 p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">A</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.email || 'Unknown user'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
