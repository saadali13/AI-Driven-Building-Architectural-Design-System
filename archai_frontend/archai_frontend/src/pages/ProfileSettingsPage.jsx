import React, { useState } from 'react';
import {
  LayoutDashboard,
  BarChart3,
  Users,
  Settings,
  Archive,
  ArrowLeft,
  Menu,
  X,
  ShieldCheck,
  HelpCircle,
  ChevronRight,
  Building2,
  Layers,
  ChevronLeft,
  User
} from 'lucide-react';
import { useAuth, ROLES, ROLE_DETAILS } from '../context/AuthContext';
import SettingsModule from '../components/modules/SettingsModule';
import { LOGO_URL } from '../components/common/BrandLogo';


export default function ProfileSettings({ setActiveTab }) {
  const { user } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);


  const currentRoleInfo = user?.role && ROLE_DETAILS[user.role] ? ROLE_DETAILS[user.role] : ROLE_DETAILS[ROLES.HOMEOWNER];

  return (
    <div className="h-screen w-full overflow-hidden flex bg-slate-50 text-slate-900 font-sans select-none">
      
      {/* Mobile Drawer Overlay */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-50 md:hidden backdrop-blur-xs"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar in Black */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 flex flex-col bg-slate-950 border-r border-slate-800 text-slate-200 transition-all duration-300 ease-in-out shrink-0 shadow-xl ${
          sidebarCollapsed ? 'w-20' : 'w-64'
        } ${
          mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/90 bg-slate-950">
          <div 
            onClick={() => setActiveTab('workspace')}
            className="flex items-center gap-3 cursor-pointer overflow-hidden group"
          >
            <div className="w-9 h-9 rounded-xl bg-slate-900 border border-slate-700/80 p-0.5 shadow-xs flex items-center justify-center shrink-0">
              <img src={LOGO_URL} alt="ArchAI Logo" className="w-full h-full object-contain rounded-lg" />
            </div>
            {!sidebarCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="font-bold text-sm text-white tracking-tight truncate">
                  Arch<span className="text-blue-400">AI</span> Studio
                </span>
                <span className="text-[10px] font-mono text-blue-400 uppercase font-bold truncate">Settings Suite</span>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 transition cursor-pointer"
          >
            {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Item */}
        <div className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
          <button
            type="button"
            onClick={() => setActiveTab('workspace')}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-900/90 transition cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4 shrink-0 text-slate-400" />
            {!sidebarCollapsed && <span>Return to Workspace</span>}
          </button>

          <button
            type="button"
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-bold bg-blue-600 text-white shadow-md shadow-blue-500/25 transition cursor-pointer"
          >
            <Settings className="w-4 h-4 shrink-0" />
            {!sidebarCollapsed && <span>Account &amp; System</span>}
          </button>
        </div>

        {/* User Card in Black Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-xs text-white shrink-0 shadow-2xs">
              {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            {!sidebarCollapsed && (
              <div className="flex flex-col min-w-0 flex-1">
                <span className="text-xs font-bold text-white truncate">{user?.name || 'Authenticated User'}</span>
                <span className="text-[10px] font-mono text-slate-400">{currentRoleInfo.title}</span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main View Area */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-slate-50">
        <SettingsModule defaultTab="profile" />
      </main>

    </div>
  );
}
