import React, { useState } from 'react';
import { NavLink, Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Compass,
  LayoutDashboard,
  PlusCircle,
  FolderKanban,
  LayoutGrid,
  GitCompare,
  Calculator,
  Heart,
  Settings,
  HelpCircle,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  HardHat,
  Users,
  FileSpreadsheet,
  Activity,
  Layers,
  FileSearch,
  RotateCcw,
  Sliders,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useProjects } from '../../context/ProjectContext';
import { UserRole } from '../../types';

interface DashboardSidebarProps {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
  highlight?: boolean;
}

export const DashboardSidebar: React.FC<DashboardSidebarProps> = ({
  collapsed,
  setCollapsed,
  mobileOpen,
  setMobileOpen,
}) => {
  const { currentUser, logout, switchRole } = useAuth();
  const { notifications } = useProjects();
  const navigate = useNavigate();
  const location = useLocation();

  const [showSandbox, setShowSandbox] = useState(false);
  const role: UserRole = currentUser?.role || 'customer';

  // Navigation Menus tailored to each persona
  const customerNav: NavItem[] = [
    { name: 'Overview', path: '/app/dashboard', icon: LayoutDashboard },
    { name: 'My Designs', path: '/app/designs', icon: FolderKanban },
    { name: 'New Design', path: '/app/designs/new', icon: PlusCircle, highlight: true },
    { name: 'Templates', path: '/app/templates', icon: LayoutGrid },
    { name: 'Cost Estimation', path: '/app/cost-estimation', icon: Calculator },
    { name: 'Compare Designs', path: '/app/compare', icon: GitCompare },
    { name: 'Favorites', path: '/app/favorites', icon: Heart },
    { name: 'Settings', path: '/app/settings', icon: Settings },
  ];

  const architectNav: NavItem[] = [
    { name: 'Overview', path: '/app/dashboard', icon: LayoutDashboard },
    { name: 'Projects', path: '/app/architect/projects', icon: FolderKanban },
    { name: 'Design Workspace', path: '/app/designs/new', icon: PlusCircle, highlight: true },
    { name: 'Reviews', path: '/app/architect/reviews', icon: FileSearch },
    { name: 'Revisions', path: '/app/architect/revisions', icon: RotateCcw },
    { name: 'Templates', path: '/app/templates', icon: LayoutGrid },
    { name: 'Cost Estimation', path: '/app/cost-estimation', icon: Calculator },
    { name: 'Reports', path: '/app/architect/reports', icon: Activity },
    { name: 'Settings', path: '/app/settings', icon: Settings },
  ];

  const adminNav: NavItem[] = [
    { name: 'Overview', path: '/app/dashboard', icon: LayoutDashboard },
    { name: 'Users', path: '/app/admin/users', icon: Users },
    { name: 'Projects', path: '/app/admin/projects', icon: FolderKanban },
    { name: 'Templates', path: '/app/admin/templates', icon: LayoutGrid },
    { name: 'Cost Configuration', path: '/app/admin/cost-settings', icon: FileSpreadsheet },
    { name: 'Reports', path: '/app/admin/reports', icon: Activity },
    { name: 'Audit Logs', path: '/app/admin/audit-logs', icon: ShieldCheck },
    { name: 'System Settings', path: '/app/admin/settings', icon: Sliders },
  ];

  const contractorNav: NavItem[] = [
    { name: 'Overview', path: '/app/dashboard', icon: LayoutDashboard },
    { name: 'Assigned Projects', path: '/app/designs', icon: FolderKanban },
    { name: 'Cost Estimation', path: '/app/cost-estimation', icon: Calculator, highlight: true },
    { name: 'Material Rates', path: '/app/admin/cost-settings', icon: FileSpreadsheet },
    { name: 'Estimates & Reports', path: '/app/admin/reports', icon: Activity },
    { name: 'Templates', path: '/app/templates', icon: LayoutGrid },
    { name: 'Settings', path: '/app/settings', icon: Settings },
  ];

  const navItems =
    role === 'architect'
      ? architectNav
      : role === 'admin'
      ? adminNav
      : role === 'contractor'
      ? contractorNav
      : customerNav;

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const roleBadgeStyle = {
    customer: 'bg-[#EEF4F0] text-[#23483D] border-[#DCE7DE]',
    architect: 'bg-[#EBF3F5] text-[#1E5664] border-[#CCE0E5]',
    admin: 'bg-[#F4EFF7] text-[#5C2D6D] border-[#E0D0E7]',
    contractor: 'bg-[#FDF3EB] text-[#8C4A1A] border-[#F2DAC7]',
  }[role];

  const roleLabel = {
    customer: 'Homeowner',
    architect: 'PCATP Architect',
    admin: 'System Admin',
    contractor: 'Contractor',
  }[role];

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-[#202923]/40 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col bg-white border-r border-[#E2E7E1] transition-all duration-300 shadow-sm ${
          collapsed ? 'w-20' : 'w-64'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[#E2E7E1]">
          <Link to="/" className="flex items-center gap-3 overflow-hidden">
            <div className="h-9 w-9 rounded-xl bg-[#23483D] flex items-center justify-center shrink-0 shadow-sm">
              <Compass className="h-5 w-5 text-white" />
            </div>
            {!collapsed && (
              <div className="truncate">
                <span className="font-heading font-bold text-base text-[#202923] tracking-tight">ArchiCraft</span>
                <span className="text-[#B86F50] font-bold ml-1">AI</span>
              </div>
            )}
          </Link>

          {/* Desktop Collapse Button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex p-1.5 rounded-lg text-[#68736C] hover:text-[#202923] hover:bg-[#F1F4F0] transition-colors"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* User Persona Card */}
        <div className="p-3 border-b border-[#E2E7E1]">
          <div className={`rounded-xl p-2.5 bg-[#F7F7F2] border border-[#E2E7E1] ${collapsed ? 'text-center' : ''}`}>
            {!collapsed ? (
              <div className="flex items-center justify-between">
                <div className="truncate pr-2">
                  <p className="text-xs font-semibold text-[#202923] truncate">{currentUser?.name || 'User'}</p>
                  <p className="text-[11px] text-[#68736C] truncate">{currentUser?.email}</p>
                </div>
                <span className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded border shrink-0 ${roleBadgeStyle}`}>
                  {roleLabel}
                </span>
              </div>
            ) : (
              <div className="flex justify-center" title={`${currentUser?.name} (${roleLabel})`}>
                <span className={`h-2.5 w-2.5 rounded-full ${role === 'admin' ? 'bg-purple-600' : role === 'architect' ? 'bg-teal-600' : 'bg-[#23483D]'}`} />
              </div>
            )}
          </div>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-[#DCE7DE] text-[#23483D] font-bold shadow-xs'
                    : item.highlight
                    ? 'bg-[#EEF4F0] text-[#23483D] font-semibold border border-[#DCE7DE] hover:bg-[#DCE7DE]'
                    : 'text-[#68736C] hover:text-[#202923] hover:bg-[#F1F4F0]'
                } ${collapsed ? 'justify-center px-2' : ''}`}
                title={collapsed ? item.name : undefined}
              >
                <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-[#23483D]' : item.highlight ? 'text-[#B86F50]' : 'text-[#68736C]'}`} />
                {!collapsed && <span className="truncate">{item.name}</span>}
              </NavLink>
            );
          })}
        </div>

        {/* Bottom Help & Isolated Demo Switcher */}
        <div className="p-3 border-t border-[#E2E7E1] bg-white space-y-2">
          {/* Help & Support Link */}
          <NavLink
            to="/app/help-support"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                isActive ? 'bg-[#DCE7DE] text-[#23483D]' : 'text-[#68736C] hover:text-[#202923] hover:bg-[#F1F4F0]'
              } ${collapsed ? 'justify-center px-2' : ''}`
            }
            title="Help & Documentation"
          >
            <HelpCircle className="h-4 w-4 shrink-0 text-[#68736C]" />
            {!collapsed && <span>Help & Support</span>}
          </NavLink>

          {/* FYP Demo Sandbox Switcher (Clearly Labeled as Testing Tool) */}
          {!collapsed && (
            <div className="border border-[#E2E7E1] rounded-xl p-2 bg-[#F7F7F2] text-[11px]">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-semibold text-[#68736C] uppercase tracking-wider">
                  FYP Demo Sandbox
                </span>
                <button
                  onClick={() => setShowSandbox(!showSandbox)}
                  className="text-[10px] text-[#23483D] font-semibold underline"
                >
                  {showSandbox ? 'Hide' : 'Switch Role'}
                </button>
              </div>

              {showSandbox && (
                <div className="grid grid-cols-2 gap-1 pt-1">
                  <button
                    onClick={() => switchRole('customer')}
                    className={`px-1.5 py-1 rounded text-center truncate text-[10px] ${
                      role === 'customer' ? 'bg-[#23483D] text-white font-bold' : 'bg-white text-[#68736C] hover:bg-[#E2E7E1]'
                    }`}
                  >
                    Homeowner
                  </button>
                  <button
                    onClick={() => switchRole('architect')}
                    className={`px-1.5 py-1 rounded text-center truncate text-[10px] ${
                      role === 'architect' ? 'bg-[#23483D] text-white font-bold' : 'bg-white text-[#68736C] hover:bg-[#E2E7E1]'
                    }`}
                  >
                    Architect
                  </button>
                  <button
                    onClick={() => switchRole('admin')}
                    className={`px-1.5 py-1 rounded text-center truncate text-[10px] ${
                      role === 'admin' ? 'bg-[#23483D] text-white font-bold' : 'bg-white text-[#68736C] hover:bg-[#E2E7E1]'
                    }`}
                  >
                    Admin
                  </button>
                  <button
                    onClick={() => switchRole('contractor')}
                    className={`px-1.5 py-1 rounded text-center truncate text-[10px] ${
                      role === 'contractor' ? 'bg-[#23483D] text-white font-bold' : 'bg-white text-[#68736C] hover:bg-[#E2E7E1]'
                    }`}
                  >
                    Contractor
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Sign Out */}
          <button
            onClick={handleLogout}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#68736C] hover:text-[#DC2626] hover:bg-[#FEF2F2] transition-colors ${
              collapsed ? 'justify-center px-2' : ''
            }`}
            title="Sign Out"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {!collapsed && <span>Sign Out</span>}
          </button>
        </div>
      </aside>
    </>
  );
};
