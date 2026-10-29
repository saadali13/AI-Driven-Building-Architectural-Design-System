import React, { useState } from 'react';
import { 
  Building2, 
  Layers, 
  BarChart3, 
  Sparkles, 
  ShieldCheck, 
  Menu, 
  X, 
  User, 
  LogOut, 
  ChevronDown,
  ArrowRight,
  PlusCircle,
  FolderKanban
} from 'lucide-react';
import { useAuth, ROLE_DETAILS, ROLES } from '../../context/AuthContext';
import BrandLogo from './BrandLogo';


export default function Navbar({ activeTab, setActiveTab, onOpenStudio }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const { user, logout } = useAuth();

  const roleMeta = user ? (ROLE_DETAILS[user.role] || ROLE_DETAILS[ROLES.HOMEOWNER]) : null;

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs font-sans">
      <div className="max-w-7xl mx-auto flex justify-between items-center px-6 md:px-10 h-24">
        
        {/* Brand Logo */}
        <div 
          onClick={() => setActiveTab('landing')}
          className="cursor-pointer shrink-0"
        >
          <BrandLogo size="lg" showSubtitle={true} subtitleText="Spatial Intelligence Studio" />
        </div>

        {/* Center Nav Links */}
        <div className="hidden md:flex items-center gap-2 bg-slate-100/90 p-2 rounded-2xl border border-slate-200/80">
          <button 
            type="button"
            onClick={() => setActiveTab('landing')} 
            className={`px-5 py-2.5 rounded-xl text-base font-bold transition cursor-pointer ${
              activeTab === 'landing' 
                ? 'bg-white text-slate-900 shadow-xs' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Overview
          </button>
          
          <button 
            type="button"
            onClick={() => setActiveTab('workspace')} 
            className={`px-5 py-2.5 rounded-xl text-base font-bold transition cursor-pointer flex items-center gap-2.5 ${
              activeTab === 'workspace' 
                ? 'bg-white text-slate-900 shadow-xs' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="w-5 h-5 text-blue-600" />
            <span>Workspace</span>
          </button>

          <button 
            type="button"
            onClick={() => setActiveTab('cost-estimator')} 
            className={`px-5 py-2.5 rounded-xl text-base font-bold transition cursor-pointer flex items-center gap-2.5 ${
              activeTab === 'cost-estimator' 
                ? 'bg-white text-slate-900 shadow-xs' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-5 h-5 text-emerald-600" />
            <span>PKR Cost Matrix</span>
          </button>
        </div>

        {/* Right CTA Group */}
        <div className="flex items-center gap-4">
          
          <button
            type="button"
            onClick={() => onOpenStudio && onOpenStudio('5marla')}
            className="hidden sm:flex items-center gap-2.5 px-5 py-3 rounded-xl bg-slate-100 hover:bg-slate-200/80 border border-slate-200 text-slate-800 text-base font-bold transition cursor-pointer shadow-2xs"
          >
            <Sparkles className="w-5 h-5 text-blue-600" />
            <span>3D Studio</span>
          </button>

          {user ? (
            <div className="flex items-center gap-3.5">
              {/* Role badge */}
              <div 
                onClick={() => setActiveTab('profile-settings')}
                className={`hidden lg:flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-mono font-bold cursor-pointer transition-all hover:opacity-90 ${roleMeta?.color || 'bg-slate-100 text-slate-700 border-slate-200'}`}
              >
                <span className={`w-2.5 h-2.5 rounded-full ${roleMeta?.dotColor || 'bg-slate-400'}`}></span>
                <span>{roleMeta?.badge || user.role}</span>
              </div>

              {/* User Dropdown */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center gap-2.5 p-1 rounded-xl hover:bg-slate-100 transition cursor-pointer"
                >
                  <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-base shadow-sm">
                    {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <ChevronDown className="w-5 h-5 text-slate-400 hidden sm:block" />
                </button>

                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-2xl p-3 shadow-2xl z-50 text-base animate-in fade-in">
                    <div className="p-4 border-b border-slate-100 mb-1">
                      <p className="font-bold text-slate-900 truncate text-base">{user.name}</p>
                      <p className="text-sm text-slate-500 truncate mt-0.5">{user.email}</p>
                      <span className="inline-block mt-2 px-3 py-1 rounded-md bg-blue-50 text-blue-700 font-mono text-xs font-bold border border-blue-200">
                        {user.role}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        setActiveTab('profile-settings');
                        setUserDropdownOpen(false);
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-xl transition text-left cursor-pointer font-semibold text-base"
                    >
                      <User className="w-5 h-5 text-slate-500" />
                      <span>Profile &amp; Settings</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setActiveTab('workspace');
                        setUserDropdownOpen(false);
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-xl transition text-left cursor-pointer font-semibold text-base"
                    >
                      <Layers className="w-5 h-5 text-blue-600" />
                      <span>AI Workspace</span>
                    </button>

                    <div className="my-1 border-t border-slate-100"></div>

                    <button
                      type="button"
                      onClick={() => {
                        logout();
                        setUserDropdownOpen(false);
                        setActiveTab('landing');
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition text-left cursor-pointer font-bold text-base"
                    >
                      <LogOut className="w-5 h-5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setActiveTab('auth')}
                className="px-5 py-3 text-slate-700 hover:text-slate-900 font-bold text-base rounded-xl transition cursor-pointer"
              >
                Sign In
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('auth')}
                className="px-6 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-base rounded-xl transition shadow-lg shadow-blue-500/25 flex items-center gap-2.5 cursor-pointer hover:scale-[1.01]"
              >
                <span>Get Started</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          )}


          {/* Mobile Menu Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>

        </div>

      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-6 py-5 space-y-3 shadow-lg">
          <button
            type="button"
            onClick={() => {
              setActiveTab('landing');
              setMobileMenuOpen(false);
            }}
            className="w-full text-left py-2.5 px-3 text-sm font-bold text-slate-800 hover:bg-slate-50 rounded-xl"
          >
            Overview
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('workspace');
              setMobileMenuOpen(false);
            }}
            className="w-full text-left py-2.5 px-3 text-sm font-bold text-slate-800 hover:bg-slate-50 rounded-xl flex items-center gap-2"
          >
            <Layers className="w-4 h-4 text-blue-600" />
            <span>Workspace Hub</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('cost-estimator');
              setMobileMenuOpen(false);
            }}
            className="w-full text-left py-2.5 px-3 text-sm font-bold text-slate-800 hover:bg-slate-50 rounded-xl flex items-center gap-2"
          >
            <BarChart3 className="w-4 h-4 text-emerald-600" />
            <span>PKR Cost Estimator</span>
          </button>
        </div>
      )}
    </nav>
  );
}
