import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Compass, Menu, X, ArrowRight, ShieldCheck, ChevronDown, UserCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types';

export const PublicNavbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);
  const location = useLocation();
  const { currentUser, switchRole, isAuthenticated } = useAuth();

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Design Templates', path: '/templates' },
    { name: 'Cost Estimation', path: '/cost-estimation-preview' },
    { name: 'How It Works', path: '/#how-it-works' },
    { name: 'About FYP', path: '/about' },
    { name: 'Help & Bylaws', path: '/help' },
  ];

  const handleRoleSelect = (role: UserRole) => {
    switchRole(role);
    setRoleDropdownOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 bg-slate-950/85 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="h-11 w-11 rounded-xl bg-gradient-to-tr from-teal-600 via-teal-500 to-emerald-400 p-0.5 shadow-lg shadow-teal-500/20 group-hover:scale-105 transition-transform">
              <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Compass className="h-6 w-6 text-teal-400 transform group-hover:rotate-45 transition-transform duration-300" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-heading font-bold text-xl text-white tracking-tight">ArchiCraft</span>
                <span className="text-xs font-mono font-semibold px-1.5 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
                  AI ARCH
                </span>
              </div>
              <p className="text-[11px] text-slate-400 tracking-wide">Building Architectural System</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-teal-400 bg-teal-950/40'
                      : 'text-slate-300 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* Right Action / Role Preview Switcher */}
          <div className="hidden md:flex items-center gap-3">
            {/* Quick Role Tester Pill for Reviewer */}
            <div className="relative">
              <button
                onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-700/80 hover:border-teal-500/60 text-xs text-slate-300 transition-all"
                title="Switch role to preview role-based views"
              >
                <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse" />
                <span>Role:</span>
                <span className="font-semibold text-teal-300 capitalize">{currentUser?.role || 'Guest'}</span>
                <ChevronDown className="h-3 w-3 text-slate-400" />
              </button>

              {roleDropdownOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl py-2 z-50">
                  <div className="px-3 py-1.5 border-b border-slate-800 text-[11px] text-slate-400 font-medium">
                    SWITCH DEMO ROLE:
                  </div>
                  {(['customer', 'architect', 'admin', 'contractor'] as UserRole[]).map((role) => (
                    <button
                      key={role}
                      onClick={() => handleRoleSelect(role)}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-800 transition-colors ${
                        currentUser?.role === role ? 'text-teal-400 font-semibold bg-teal-950/30' : 'text-slate-300'
                      }`}
                    >
                      <span className="capitalize">{role === 'customer' ? 'Homeowner / Customer' : role === 'architect' ? 'Architect (PCATP)' : role === 'admin' ? 'Administrator' : 'Contractor / Estimator'}</span>
                      {currentUser?.role === role && <ShieldCheck className="h-3.5 w-3.5 text-teal-400" />}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {isAuthenticated ? (
              <Link
                to="/app/dashboard"
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold shadow-lg shadow-teal-900/30 transition-all hover:-translate-y-0.5"
              >
                <span>Dashboard</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold shadow-lg shadow-teal-900/30 transition-all hover:-translate-y-0.5"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <div className="lg:hidden flex items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-slate-950 border-b border-slate-800 px-4 pt-2 pb-6 space-y-3">
          <div className="flex flex-col space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-lg text-base font-medium text-slate-300 hover:text-white hover:bg-slate-900"
              >
                {link.name}
              </Link>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs text-slate-400 py-1">
              <span>Current Demo Role:</span>
              <span className="font-semibold text-teal-400 capitalize">{currentUser?.role}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => { switchRole('customer'); setMobileMenuOpen(false); }}
                className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-300 hover:border-teal-500"
              >
                Homeowner
              </button>
              <button
                onClick={() => { switchRole('architect'); setMobileMenuOpen(false); }}
                className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-300 hover:border-teal-500"
              >
                Architect
              </button>
              <button
                onClick={() => { switchRole('admin'); setMobileMenuOpen(false); }}
                className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-300 hover:border-teal-500"
              >
                Admin
              </button>
              <button
                onClick={() => { switchRole('contractor'); setMobileMenuOpen(false); }}
                className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-300 hover:border-teal-500"
              >
                Contractor
              </button>
            </div>

            <Link
              to="/app/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className="mt-2 w-full py-2.5 rounded-xl bg-teal-600 text-white font-semibold text-center text-sm"
            >
              Go to Workspace Dashboard
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
