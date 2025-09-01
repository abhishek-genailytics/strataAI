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
  Key,
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
    {
      name: "API Keys",
      href: "/api-keys",
      icon: <Key className="w-5 h-5" />,
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
    <div key={section.title} className="mb-8">
      <div className="flex items-center justify-between px-4 mb-4">
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">
          {section.title}
        </h3>
        {section.collapsible && (
          <button
            onClick={() => setAiGatewayCollapsed(!aiGatewayCollapsed)}
            className="text-gray-400 hover:text-gray-600 transition-colors duration-200 p-1.5 rounded-lg hover:bg-gray-100"
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
        <nav className="space-y-1 px-3">
          {section.items.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`${
                isActive(item.href)
                  ? "bg-blue-600 text-white shadow-lg border-l-4 border-blue-400"
                  : "text-gray-700 hover:bg-gray-100 hover:text-gray-900 border-l-4 border-transparent hover:border-gray-300"
              } group flex items-center px-3 py-3 text-sm font-medium rounded-r-lg transition-all duration-200`}
            >
              <span className={`mr-3 flex-shrink-0 ${
                isActive(item.href) 
                  ? "text-white" 
                  : "text-gray-500 group-hover:text-gray-700"
              } transition-colors duration-200`}>
                {item.icon}
              </span>
              <span className="font-medium">{item.name}</span>
              {item.badge && (
                <span className="ml-auto bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full font-semibold">
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
    <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 shadow-lg transform md:translate-x-0 transition-transform duration-300 ease-in-out">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center h-16 px-4 bg-white border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <button 
              type="button"
              onClick={() => window.history.back()}
              className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-lg p-2 hover:bg-gray-100 transition-all duration-200"
              aria-label="Go back"
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
            <div>
              <h1 className="text-lg font-bold text-gray-900">StrataAI</h1>
              <span className="text-xs text-blue-600 font-medium">v0.79.7</span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 pt-6 pb-4 overflow-y-auto bg-white">
          <div>
            {renderSection(aiGatewaySection, aiGatewayCollapsed)}
            {renderSection(controlPanelSection)}
          </div>
        </div>

        {/* User Info */}
        <div className="flex-shrink-0 p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-100 transition-colors duration-200 cursor-pointer">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center shadow-md">
              <span className="text-white text-sm font-bold">
                {user?.email?.[0]?.toUpperCase() || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">
                {user?.email || 'Unknown user'}
              </p>
              <p className="text-xs text-gray-500">Personal Workspace</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};