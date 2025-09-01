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
      <div className="flex items-center justify-between px-3 mb-3">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
          {section.title}
        </h3>
        {section.collapsible && (
          <button
            onClick={() => setAiGatewayCollapsed(!aiGatewayCollapsed)}
            className="text-slate-400 hover:text-slate-600 transition-colors duration-200 p-1 rounded-md hover:bg-white/50"
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
        <nav className="space-y-2">
          {section.items.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`${
                isActive(item.href)
                  ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg"
                  : "text-slate-600 hover:bg-gradient-to-r hover:from-slate-100 hover:to-blue-50 hover:text-slate-900"
              } group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 transform hover:translate-x-1`}
            >
              <span className={`mr-3 flex-shrink-0 ${
                isActive(item.href) ? "text-white" : "text-slate-500 group-hover:text-blue-600"
              } transition-colors duration-200`}>
                {item.icon}
              </span>
              {item.name}
              {item.badge && (
                <span className="ml-auto bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full font-semibold">
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
    <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 md:z-50 shadow-xl">
      <div className="flex flex-col flex-1 min-h-0 bg-gradient-to-b from-white to-slate-50 border-r border-slate-200 shadow-2xl">
        {/* Header */}
        <div className="flex items-center h-16 flex-shrink-0 px-4 border-b border-slate-200 bg-gradient-to-r from-white to-blue-50">
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
              className="text-slate-400 hover:text-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-lg p-1.5 hover:bg-white/60 transition-all duration-200"
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
            <div>
              <h1 className="text-lg font-bold text-slate-900">StrataAI</h1>
              <span className="text-xs text-slate-500 font-medium">v0.79.7</span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 flex flex-col pt-6 pb-4 overflow-y-auto">
          <div className="px-4">
            {renderSection(aiGatewaySection, aiGatewayCollapsed)}
            {renderSection(controlPanelSection)}
          </div>
        </div>

        {/* User Info */}
        <div className="flex-shrink-0 p-4 border-t border-slate-200 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center space-x-3 p-2 rounded-xl hover:bg-white/60 transition-colors duration-200">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
              <span className="text-white text-sm font-bold">
                {user?.email?.[0]?.toUpperCase() || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900 truncate">
                {user?.email || 'Unknown user'}
              </p>
              <p className="text-xs text-slate-500">Personal Workspace</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
