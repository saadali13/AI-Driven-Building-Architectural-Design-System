import React, { useState } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { DashboardSidebar } from './DashboardSidebar';
import { DashboardHeader } from './DashboardHeader';
import { useAuth } from '../../context/AuthContext';

export const DashboardLayout: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // If user is completely unauthenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-[#F7F7F2] text-[#202923] flex font-sans antialiased">
      {/* Sidebar Navigation */}
      <DashboardSidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          collapsed ? 'lg:ml-20' : 'lg:ml-64'
        }`}
      >
        <DashboardHeader onMobileMenuToggle={() => setMobileOpen(true)} />
        
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>

        <footer className="py-4 px-6 border-t border-[#E2E7E1] text-center text-xs text-[#68736C]">
          <span>ArchiCraft AI Studio ? AI-Driven Building Architectural Design & BOQ System (FYP)</span>
        </footer>
      </div>
    </div>
  );
};
