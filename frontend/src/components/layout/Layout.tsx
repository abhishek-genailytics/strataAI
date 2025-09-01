import React from "react";
import { Sidebar } from "./Sidebar";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex h-screen overflow-hidden">
        <Sidebar />

        <div className="flex flex-col flex-1 overflow-hidden">
          <main className="flex-1 overflow-y-auto focus:outline-none">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};
