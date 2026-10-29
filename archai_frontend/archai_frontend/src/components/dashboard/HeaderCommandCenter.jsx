import React, { useState } from 'react';
import { 
  Search, 
  Bell, 
  Sparkles, 
  ChevronDown, 
  User, 
  LogOut, 
  ShieldCheck, 
  Settings, 
  Clock,
  Menu
} from 'lucide-react';

export default function HeaderCommandCenter({ 
  user = { name: 'Sarah Vance', role: 'Principal Architect', email: 's.vance@archai.design' },
  searchQuery = '',
  onSearchChange,
  onOpenNewProject,
  onOpenNotifications,
  onOpenProfile,
  onLogout,
  onToggleMobileSidebar
}) {
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const mockNotifications = [
    { id: 1, title: 'AI Synthesis Completed', desc: '5 Marla Villa Layout generated with 99.4% spatial precision.', time: '2m ago', unread: true },
    { id: 2, title: 'BIM Export Ready', desc: 'Revit CAD blueprint archive ready for download.', time: '14m ago', unread: true },
    { id: 3, title: 'Cost Optimization', desc: 'Structural estimation reduced by 4.2% through smart cantilever analysis.', time: '1h ago', unread: false }
  ];

  return (
    <header className="h-20 px-6 md:px-8 bg-white border-b border-slate-200/90 flex items-center justify-between gap-4 shrink-0 shadow-2xs z-20">
      
      {/* Left: Mobile Toggle & Global Search Input */}
      <div className="flex items-center gap-3 flex-1 max-w-xl">
        <button
          type="button"
          onClick={onToggleMobileSidebar}
          className="md:hidden p-2 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-100 cursor-pointer"
          aria-label="Open mobile menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="relative w-full max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search blueprints, CAD templates, prompts (⌘K)..."
            value={searchQuery}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            className="w-full pl-11 pr-14 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all shadow-2xs"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 px-2 py-0.5 rounded-lg bg-slate-200/70 border border-slate-300/80 text-[10px] font-mono text-slate-600 font-bold">
            ⌘K
          </div>
        </div>
      </div>

      {/* Right Controls & User Profile Indicator */}
      <div className="flex items-center gap-3.5">
        
        {/* Quick Action: New AI Project CTA */}
        <button
          type="button"
          onClick={onOpenNewProject}
          className="hidden sm:flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition-all shadow-md shadow-blue-500/20 cursor-pointer active:scale-95"
        >
          <Sparkles className="w-4 h-4" />
          <span>New AI Blueprint</span>
        </button>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className={`p-2.5 rounded-xl border transition-colors relative cursor-pointer ${
              notificationsOpen 
                ? 'bg-blue-50 border-blue-200 text-blue-600' 
                : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-600 hover:text-slate-900'
            }`}
            aria-label="View notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-2 right-2 w-2 h-2 bg-blue-600 rounded-full ring-2 ring-white"></span>
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-3 w-80 sm:w-96 bg-white border border-slate-200 rounded-2xl p-4 shadow-xl z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-sm text-slate-900">Notifications</h4>
                  <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full border border-blue-200">
                    2 New
                  </span>
                </div>
                <button 
                  type="button"
                  onClick={() => onOpenNotifications && onOpenNotifications()}
                  className="text-xs font-semibold text-blue-600 hover:underline cursor-pointer"
                >
                  Mark all read
                </button>
              </div>

              <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto my-1">
                {mockNotifications.map((n) => (
                  <div key={n.id} className="py-3 hover:bg-slate-50/80 -mx-2 px-2 rounded-xl transition cursor-pointer">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-bold text-slate-900">{n.title}</p>
                      <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {n.time}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{n.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="h-6 w-[1px] bg-slate-200" />

        {/* User Profile Indicator */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}
            className="flex items-center gap-3 p-1.5 rounded-2xl hover:bg-slate-100 transition-colors cursor-pointer border border-transparent hover:border-slate-200"
          >
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center shadow-xs">
                {user?.name ? user.name.split(' ').map(n => n[0]).join('') : 'U'}
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full ring-2 ring-white" />
            </div>

            <div className="hidden md:flex flex-col text-left min-w-0">
              <span className="text-xs font-bold text-slate-900 leading-tight truncate">
                {user?.name || 'Lead Architect'}
              </span>
              <span className="text-[10px] font-mono text-slate-500 truncate">
                {user?.role || 'ARCHITECT'}
              </span>
            </div>

            <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden md:block" />
          </button>

          {/* Profile Dropdown Menu */}
          {userDropdownOpen && (
            <div className="absolute right-0 mt-3 w-64 bg-white border border-slate-200 rounded-2xl p-2.5 shadow-xl z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="p-3 border-b border-slate-100 mb-1">
                <p className="font-bold text-slate-900 text-xs truncate">{user?.name || 'Lead Architect'}</p>
                <p className="text-[11px] text-slate-500 truncate mt-0.5">{user?.email || 'architect@archai.design'}</p>
                <div className="mt-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-mono text-[10px] font-bold border border-blue-200">
                  <ShieldCheck className="w-3 h-3 text-blue-600" />
                  {user?.role || 'ARCHITECT'}
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  setUserDropdownOpen(false);
                  if (onOpenProfile) onOpenProfile();
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-xl transition text-xs font-medium cursor-pointer"
              >
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Account Profile</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setUserDropdownOpen(false);
                  if (onOpenProfile) onOpenProfile();
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-xl transition text-xs font-medium cursor-pointer"
              >
                <Settings className="w-3.5 h-3.5 text-slate-400" />
                <span>Workspace Preferences</span>
              </button>

              <div className="my-1 border-t border-slate-100" />

              <button
                type="button"
                onClick={() => {
                  setUserDropdownOpen(false);
                  if (onLogout) onLogout();
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition text-xs font-medium cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
