import React from "react";
import { Sidebar } from "./Sidebar";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar - Fixed position */}
      <Sidebar />
      
      {/* Main content area with left margin to account for fixed sidebar */}
      <div className="flex-1 ml-64">
        <main className="min-h-screen p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};