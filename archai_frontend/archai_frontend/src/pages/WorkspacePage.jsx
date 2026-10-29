import React, { useState, useEffect } from 'react';
import FloorPlanEditor2D from '../components/editor/FloorPlanEditor2D';
import BuildingViewport3D from '../components/editor/BuildingViewport3D';
import DesignComparisonMatrix from '../components/editor/DesignComparisonMatrix';
import RequirementsGenerator from '../components/editor/RequirementsGenerator';
import ProtectedRoute from '../components/common/ProtectedRoute';
import BrandLogo, { LOGO_URL } from '../components/common/BrandLogo';
import TeamModule from '../components/modules/TeamModule';
import AnalyticsModule from '../components/modules/AnalyticsModule';
import SettingsModule from '../components/modules/SettingsModule';
import ArchiveModule from '../components/modules/ArchiveModule';
import ProjectsModule from '../components/modules/ProjectsModule';
import AdminDashboardModule from '../components/modules/AdminDashboardModule';
import FeedbackModule from '../components/modules/FeedbackModule';
import NotificationsModule from '../components/modules/NotificationsModule';
import CostEstimatorPage from './CostEstimatorPage';
import HeroGreetingBanner from '../components/dashboard/HeroGreetingBanner';
import TelemetryKpiGrid from '../components/dashboard/TelemetryKpiGrid';
import TemplateGallerySection from '../components/dashboard/TemplateGallerySection';
import DashboardCharts from '../components/dashboard/DashboardCharts';
import CommandPaletteModal from '../components/common/CommandPaletteModal';
import NotificationDropdown from '../components/common/NotificationDropdown';
import { 
  ArchitectDashboardView, 
  ConstructionDashboardView, 
  DesignerDashboardView, 
  DeveloperDashboardView 
} from '../components/dashboard/RoleDashboardViews';
import { useAuth, ROLES, ROLE_DETAILS, PERMISSIONS } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

import { 
  LayoutDashboard, 
  BarChart3, 
  Users, 
  Settings, 
  Archive, 
  Layers, 
  Calculator,
  MapPin,
  Coins,
  ChevronRight, 
  ChevronLeft,
  ChevronDown, 
  Sparkles, 
  Wand2,
  X, 
  Box, 
  LayoutGrid, 
  Scale, 
  ShieldCheck, 
  FileCode,
  FileText,
  CheckCircle2,
  Lock,
  Menu,
  Search,
  Bell,
  Download,
  Share2,
  RefreshCw,
  Zap,
  Building2,
  DollarSign,
  TrendingUp,
  Cpu,
  LogOut,
  User,
  Compass,
  PlusCircle,
  FolderKanban,
  Clock,
  HardDrive,
  ArrowRight,
  ShieldAlert,
  MessageSquare,
  Home,
  Sun,
  Moon,
  Plus,
  Heart,
  HelpCircle
} from 'lucide-react';

export default function WorkspaceHub({ setActiveTab, onOpenStudio, initialNav = 'dashboard' }) {
  const { user, logout, switchRole, hasPermission, isViewAllowed } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();
  
  // Active sub-navigation state (defaults to initialNav or 'dashboard')
  const [activeNav, setActiveNav] = useState(initialNav);
  const [activeCanvasView, setActiveCanvasView] = useState('view3d'); // 'view3d' | 'editor2d' | 'compare'
  
  // Keep activeNav synced when initialNav prop changes
  React.useEffect(() => {
    if (initialNav) {
      setActiveNav(initialNav);
    }
  }, [initialNav]);
  
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showRoleSwitcher, setShowRoleSwitcher] = useState(false);
  const [showQuickCreateMenu, setShowQuickCreateMenu] = useState(false);
  const [showNotificationDropdown, setShowNotificationDropdown] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3500);
  };

  // Keyboard shortcut listener for Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setShowCommandPalette((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [quickPrompt, setQuickPrompt] = useState('5 Marla double story residential layout with 3 ensuite bedrooms, modern open lounge, and terrace in Islamabad...');

  const currentRole = user?.role || ROLES.HOMEOWNER;
  const currentRoleInfo = ROLE_DETAILS[currentRole] || ROLE_DETAILS[ROLES.HOMEOWNER];

  // Role-Aware Drawer Navigation Configuration (Strictly relevant tools per role, zero useless locked padlocks)
  const ROLE_DRAWER_CONFIG = {
    [ROLES.HOMEOWNER]: {
      roleTitle: 'Homeowner Portal',
      badgeLabel: 'Residential Client',
      sections: [
        {
          title: 'My Dream Home',
          items: [
            { id: 'dashboard', label: 'Homeowner Hub', icon: LayoutDashboard, desc: 'Overview & status' },
            { id: 'new-design', label: 'Dream House Generator', icon: Wand2, desc: 'AI Floor Plans & 3D' },
            { id: 'projects', label: 'My Saved House Plans', icon: FolderKanban, desc: '3D tours & exports' },
            { id: 'cost-estimation', label: 'Construction Cost & BOQ', icon: Calculator, desc: 'PKR Grey & Finishing rates' },
          ]
        },
        {
          title: 'Approvals & Support',
          items: [
            { id: 'notifications', label: 'Society & Municipal Alerts', icon: Bell, badge: 'CDA/LDA' },
            { id: 'feedback', label: 'Architect & Builder Reviews', icon: MessageSquare },
            { id: 'settings', label: 'My Profile & Plot Budget', icon: Settings },
          ]
        }
      ]
    },
    [ROLES.ARCHITECT]: {
      roleTitle: 'Architecture Studio',
      badgeLabel: 'Lead Architect',
      sections: [
        {
          title: 'Spatial Studio',
          items: [
            { id: 'dashboard', label: 'Studio Workspace', icon: LayoutDashboard, desc: 'Design command overview' },
            { id: 'new-design', label: 'Parametric CAD Generator', icon: Wand2, desc: 'Generative floor plans' },
            { id: 'projects', label: 'Blueprint Vault & BIM', icon: FolderKanban, desc: 'CAD, DWG & 3D models' },
            { id: 'cost-estimation', label: 'Material Schedules & Rates', icon: Calculator, desc: 'Live BOQ estimation' },
          ]
        },
        {
          title: 'Collaboration & Export',
          items: [
            { id: 'team', label: 'Design Team & Clients', icon: Users, desc: 'Multi-seat access' },
            { id: 'analytics', label: 'Spatial Metrics & Vector DB', icon: BarChart3, desc: 'Bylaw compliance logs' },
            { id: 'notifications', label: 'Project Review Alerts', icon: Bell },
            { id: 'settings', label: 'Studio & Model Settings', icon: Settings },
          ]
        }
      ]
    },
    [ROLES.CONSTRUCTION_PRO]: {
      roleTitle: 'Civil Engineering Hub',
      badgeLabel: 'Civil Engineer',
      sections: [
        {
          title: 'Site & Engineering',
          items: [
            { id: 'dashboard', label: 'Civil Engineering Hub', icon: LayoutDashboard, desc: 'Site load & operations' },
            { id: 'cost-estimation', label: 'Live Material BOQ (PKR)', icon: Calculator, desc: 'Steel, Cement & Brick rates' },
            { id: 'projects', label: 'Active Construction Sites', icon: FolderKanban, desc: 'Site plans & blueprints' },
            { id: 'new-design', label: 'Structural Layout Checker', icon: Wand2, desc: 'Load-bearing & column grid' },
          ]
        },
        {
          title: 'Procurement & Logs',
          items: [
            { id: 'analytics', label: 'Material Variance & Audits', icon: BarChart3, desc: 'Wastage & rate trends' },
            { id: 'notifications', label: 'Site Delivery & Alerts', icon: Bell },
            { id: 'settings', label: 'Contractor Profile & Rates', icon: Settings },
          ]
        }
      ]
    },
    [ROLES.DESIGNER]: {
      roleTitle: 'Interior Design Hub',
      badgeLabel: 'Spatial Stylist',
      sections: [
        {
          title: 'Spatial & Staging',
          items: [
            { id: 'dashboard', label: 'Interior Design Hub', icon: LayoutDashboard, desc: 'Scene & palette overview' },
            { id: 'new-design', label: 'Room & Moodboard Studio', icon: Wand2, desc: '2.5D layouts & staging' },
            { id: 'projects', label: 'Client Concept Portfolios', icon: FolderKanban, desc: 'Finishes & renders' },
            { id: 'cost-estimation', label: 'Fixture & Tile Budgets', icon: Calculator, desc: 'Interior finish schedules' },
          ]
        },
        {
          title: 'Client Approvals',
          items: [
            { id: 'feedback', label: 'Client Approvals & Reviews', icon: MessageSquare, desc: 'Sign-offs & mood feedback' },
            { id: 'notifications', label: 'Revision Notifications', icon: Bell },
            { id: 'settings', label: 'Design Palette Settings', icon: Settings },
          ]
        }
      ]
    },
    [ROLES.REAL_ESTATE_DEV]: {
      roleTitle: 'Developer Master Hub',
      badgeLabel: 'Real Estate Developer',
      sections: [
        {
          title: 'Master Planning',
          items: [
            { id: 'dashboard', label: 'Developer Executive Hub', icon: LayoutDashboard, desc: 'Portfolios & plot yield' },
            { id: 'new-design', label: 'Multi-Unit Synthesizer', icon: Wand2, desc: 'Townships & multi-family' },
            { id: 'projects', label: 'Schemes & Land Portfolios', icon: FolderKanban, desc: 'Subdivision layouts' },
            { id: 'cost-estimation', label: 'Feasibility & ROI Model', icon: Calculator, desc: 'Per-sq-ft development cost' },
          ]
        },
        {
          title: 'Stakeholder Management',
          items: [
            { id: 'team', label: 'Project Stakeholders', icon: Users, desc: 'Investor & team access' },
            { id: 'analytics', label: 'Commercial & Sales Velocity', icon: BarChart3, desc: 'Yield & compliance stats' },
            { id: 'notifications', label: 'Municipal Approvals', icon: Bell },
            { id: 'settings', label: 'Corporate Entity Settings', icon: Settings },
          ]
        }
      ]
    },
    [ROLES.SYSTEM_ADMIN]: {
      roleTitle: 'Admin Command Console',
      badgeLabel: 'Super Admin',
      sections: [
        {
          title: 'Core Infrastructure',
          items: [
            { id: 'dashboard', label: 'Admin Command Console', icon: ShieldCheck, desc: 'System health & uptime' },
            { id: 'new-design', label: 'Blueprint Synthesis Engine', icon: Wand2, desc: 'Architext AI testing' },
            { id: 'projects', label: 'Global Blueprint Database', icon: FolderKanban, desc: 'All tenant projects' },
            { id: 'cost-estimation', label: 'Global Material Rate Master', icon: Calculator, desc: 'National market indices' },
          ]
        },
        {
          title: 'Security & Operations',
          items: [
            { id: 'team', label: 'User Provisioning & RBAC', icon: Users, desc: '6 Role management' },
            { id: 'analytics', label: 'Vector Index & GPU Cluster', icon: BarChart3, desc: 'ChromaDB & latency' },
            { id: 'notifications', label: 'System Security Alerts', icon: Bell },
            { id: 'settings', label: 'Platform Configuration', icon: Settings },
          ]
        }
      ]
    }
  };

  const activeDrawerSections = ROLE_DRAWER_CONFIG[currentRole]?.sections || ROLE_DRAWER_CONFIG[ROLES.HOMEOWNER].sections;

  const handleQuickSynthesis = () => {
    setIsSynthesizing(true);
    setTimeout(() => {
      setIsSynthesizing(false);
    }, 1200);
  };

  return (
    <div className="h-screen w-full overflow-hidden flex bg-[#F8FAFC] text-slate-900 font-sans select-none">
      
      {/* Mobile Drawer Overlay */}
      {mobileSidebarOpen && (
        <div 
          className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs z-50 md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* LUXURY OBSIDIAN-NAVY ROLE-AWARE SIDEBAR */}
      <aside 
        className={`fixed md:static inset-y-0 left-0 z-50 flex flex-col bg-[#0B132B] border-r border-[#1C2541] text-slate-200 transition-all duration-300 ease-in-out shrink-0 shadow-2xl ${
          sidebarCollapsed ? 'w-20' : 'w-72'
        } ${
          mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="h-20 flex items-center justify-between px-5 border-b border-[#1C2541] bg-[#080D1E]">
          <div 
            onClick={() => setActiveTab('landing')}
            className="flex items-center gap-3.5 cursor-pointer overflow-hidden group"
          >
            <div className="w-11 h-11 rounded-xl bg-[#101D42] border border-blue-500/30 p-1 shadow-lg flex items-center justify-center shrink-0 group-hover:scale-105 group-hover:border-cyan-400 transition-all">
              <img src={LOGO_URL} alt="ArchAI Logo" className="w-full h-full object-contain rounded-lg" />
            </div>
            {!sidebarCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="font-extrabold text-lg text-white tracking-tight leading-none truncate">
                  Arch<span className="text-cyan-400">AI</span> Studio
                </span>
                <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-wider mt-1 truncate">
                  {ROLE_DRAWER_CONFIG[currentRole]?.roleTitle || 'Enterprise Studio'}
                </span>
              </div>
            )}
          </div>

          {/* Collapse Toggle */}
          <button
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden md:flex p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition cursor-pointer"
            title={sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {sidebarCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </button>

          {/* Mobile Close Button */}
          <button
            type="button"
            onClick={() => setMobileSidebarOpen(false)}
            className="md:hidden p-2 text-slate-400 hover:text-white"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Dynamic Role-Based Drawer Sections */}
        <div className="flex-1 py-4 px-3 space-y-4 overflow-y-auto">
          {activeDrawerSections.map((section, sIdx) => (
            <div key={sIdx} className="space-y-1">
              {!sidebarCollapsed && (
                <div className="px-3 pt-2 pb-1 text-[10px] font-mono uppercase tracking-wider font-bold text-slate-400 flex items-center justify-between">
                  <span>{section.title}</span>
                  <span className="w-8 h-px bg-slate-800"></span>
                </div>
              )}

              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeNav === item.id;

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setActiveNav(item.id);
                      setMobileSidebarOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer group relative ${
                      isActive
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold shadow-md shadow-blue-500/25 border-l-4 border-cyan-400'
                        : 'text-slate-300 hover:text-white hover:bg-white/5'
                    }`}
                    title={sidebarCollapsed ? item.label : undefined}
                  >
                    <Icon className={`w-4 h-4 shrink-0 transition-colors ${
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-cyan-400'
                    }`} />
                    
                    {!sidebarCollapsed && (
                      <div className="flex items-center justify-between flex-1 min-w-0">
                        <span className="truncate">{item.label}</span>
                        {item.badge && (
                          <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/80 shrink-0 ml-1.5">
                            {item.badge}
                          </span>
                        )}
                      </div>
                    )}

                    {isActive && !sidebarCollapsed && (
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-300 shadow-xs shrink-0 ml-1"></div>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {/* User Card with Role Badge and Interactive Role Switcher */}
        <div className="p-3 border-t border-[#1C2541] bg-[#0A1024]/90 space-y-2">
          
          <div
            onClick={() => {
              setActiveNav('settings');
              setMobileSidebarOpen(false);
            }}
            className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 cursor-pointer transition border border-transparent hover:border-slate-800 group"
            title="Click to manage profile settings"
          >
            <div className="relative shrink-0">
              {user?.avatarUrl ? (
                <img
                  src={user.avatarUrl}
                  alt={user?.name || 'User'}
                  className="w-9 h-9 rounded-full object-cover ring-2 ring-blue-500/50"
                />
              ) : (
                <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center font-bold text-xs text-white shadow-md">
                  {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
              )}
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 border-2 border-[#0B132B] rounded-full"></span>
            </div>

            {!sidebarCollapsed && (
              <div className="flex flex-col min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white group-hover:text-cyan-300 transition-colors truncate">
                    {user?.name || 'Saad Ali Qureshi'}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-white transition-all shrink-0 ml-1" />
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-blue-950/80 text-cyan-300 border border-blue-800/60 truncate">
                    {ROLE_DRAWER_CONFIG[currentRole]?.badgeLabel || currentRoleInfo.badge}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

      </aside>

      {/* MAIN VIEWPORT */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-[#F8FAFC]">
        
        {/* FROSTED GLASS TOP HEADER */}
        <header className="h-20 px-4 sm:px-6 md:px-8 border-b border-slate-200/90 dark:border-slate-800 flex items-center justify-between gap-4 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md shrink-0 shadow-2xs z-30">
          
          {/* Left: Breadcrumbs & Search Bar */}
          <div className="flex items-center gap-3 sm:gap-4 flex-1 max-w-2xl min-w-0">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              className="md:hidden p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Breadcrumbs */}
            <div className="hidden xl:flex items-center gap-2 text-xs font-medium text-slate-400 dark:text-slate-500 shrink-0">
              <span className="hover:text-slate-900 dark:hover:text-white cursor-pointer transition" onClick={() => setActiveNav('dashboard')}>
                ArchAI Studio
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-700 dark:text-slate-300 font-semibold truncate max-w-[140px]">
                {ROLE_DRAWER_CONFIG[currentRole]?.roleTitle}
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-blue-600 dark:text-blue-400 font-bold capitalize truncate max-w-[140px]">
                {activeNav.replace('-', ' ')}
              </span>
            </div>

            {/* Search / Command Palette Trigger */}
            <div 
              onClick={() => setShowCommandPalette(true)}
              className="relative w-full max-w-md hidden sm:flex items-center cursor-pointer group"
              title="Click or press ⌘K / Ctrl+K to search"
            >
              <Search className="w-4 h-4 text-slate-400 group-hover:text-blue-600 absolute left-3.5 top-1/2 -translate-y-1/2 transition-colors" />
              <div className="w-full pl-10 pr-12 py-2 bg-slate-100/90 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-500 dark:text-slate-400 group-hover:border-blue-400 transition shadow-2xs">
                Search models, blueprints, prompts (⌘K)...
              </div>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-mono text-slate-500 dark:text-slate-300 font-bold shadow-2xs">
                ⌘K
              </div>
            </div>
          </div>

          {/* Right Header Controls */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            
            {/* Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100/80 dark:bg-slate-800/80 text-slate-600 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 transition cursor-pointer"
              title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            </button>

            {/* Quick-Create Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowQuickCreateMenu(!showQuickCreateMenu)}
                className="px-3 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200/80 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-bold text-xs rounded-xl transition flex items-center gap-1.5 cursor-pointer shadow-2xs"
              >
                <Plus className="w-3.5 h-3.5 text-blue-600" />
                <span className="hidden sm:inline">Create</span>
                <ChevronDown className="w-3 h-3 text-slate-400" />
              </button>

              {showQuickCreateMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-2 shadow-2xl z-50 text-xs">
                  <button
                    type="button"
                    onClick={() => { setActiveNav('new-design'); setShowQuickCreateMenu(false); }}
                    className="w-full text-left px-3 py-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 flex items-center gap-2 cursor-pointer font-medium"
                  >
                    <Wand2 className="w-4 h-4 text-blue-600" />
                    <span>New AI Floor Plan</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActiveNav('cost-estimation'); setShowQuickCreateMenu(false); }}
                    className="w-full text-left px-3 py-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 flex items-center gap-2 cursor-pointer font-medium"
                  >
                    <Calculator className="w-4 h-4 text-emerald-600" />
                    <span>Calculate BOQ</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActiveNav('templates'); setShowQuickCreateMenu(false); }}
                    className="w-full text-left px-3 py-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 flex items-center gap-2 cursor-pointer font-medium"
                  >
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    <span>Browse Templates</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { onOpenStudio && onOpenStudio('5marla'); setShowQuickCreateMenu(false); }}
                    className="w-full text-left px-3 py-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 flex items-center gap-2 cursor-pointer font-medium"
                  >
                    <Box className="w-4 h-4 text-indigo-600" />
                    <span>Open 3D Studio</span>
                  </button>
                </div>
              )}
            </div>

            {/* Interactive Role Switcher Pill */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowRoleSwitcher(!showRoleSwitcher)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200/80 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-xs font-bold text-slate-700 dark:text-slate-200 transition cursor-pointer"
                title="Switch active role to preview role-tailored drawer and dashboard"
              >
                <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
                <span className="hidden sm:inline text-slate-500 dark:text-slate-400 font-medium">Role:</span>
                <span className="text-blue-700 dark:text-cyan-300 font-bold truncate max-w-[110px]">{ROLE_DRAWER_CONFIG[currentRole]?.badgeLabel || currentRole}</span>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {showRoleSwitcher && (
                <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-2 shadow-2xl z-50 text-xs">
                  <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800 mb-1">
                    <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider font-bold">Select Role Preview</span>
                  </div>
                  {[
                    { role: ROLES.HOMEOWNER, label: '🏡 Homeowner / Residential Client', desc: 'Plot sizes, 3D plans & PKR cost' },
                    { role: ROLES.ARCHITECT, label: '📐 Lead Architect', desc: 'Parametric CAD & BIM massing' },
                    { role: ROLES.CONSTRUCTION_PRO, label: '🏗️ Civil Engineer / Contractor', desc: 'Live steel & cement rates, site BOQ' },
                    { role: ROLES.DESIGNER, label: '🎨 Spatial Interior Designer', desc: 'Moodboards & 2.5D staging' },
                    { role: ROLES.REAL_ESTATE_DEV, label: '🏢 Real Estate Developer', desc: 'Master plans & commercial yield' },
                    { role: ROLES.SYSTEM_ADMIN, label: '🛡️ System Administrator', desc: 'Global control & ChromaDB vectors' },
                  ].map((r) => (
                    <button
                      key={r.role}
                      type="button"
                      onClick={() => {
                        if (switchRole) switchRole(r.role);
                        setShowRoleSwitcher(false);
                        showToast(`Switched preview to ${r.label}`);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-xl transition flex flex-col gap-0.5 cursor-pointer ${
                        currentRole === r.role ? 'bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-bold' : 'hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <span>{r.label}</span>
                      <span className="text-[10px] text-slate-400 font-normal">{r.desc}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Notifications Button with Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowNotificationDropdown(!showNotificationDropdown)}
                className={`p-2.5 rounded-xl transition relative cursor-pointer ${
                  showNotificationDropdown
                    ? 'bg-blue-50 dark:bg-blue-900/40 text-blue-600'
                    : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
                title="Notification Center"
              >
                <Bell className="w-5 h-5" />
                <span className="absolute top-2 right-2 w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
              </button>

              <NotificationDropdown
                isOpen={showNotificationDropdown}
                onClose={() => setShowNotificationDropdown(false)}
                onOpenNotificationsPage={() => setActiveNav('notifications')}
                onOpenStudio={onOpenStudio}
              />
            </div>

            {/* Launch Studio */}
            <button
              type="button"
              onClick={() => onOpenStudio && onOpenStudio('5marla')}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-xs sm:text-sm rounded-xl transition shadow-md shadow-blue-500/20 flex items-center gap-2 cursor-pointer hover:scale-[1.01]"
            >
              <Sparkles className="w-4 h-4 text-cyan-300" />
              <span className="hidden sm:inline">Launch Studio</span>
            </button>

            {/* User Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowUserDropdown(!showUserDropdown)}
                className="flex items-center gap-2 p-1 rounded-xl hover:bg-slate-100 transition cursor-pointer"
              >
                <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-xs text-white shadow-sm">
                  {user?.name ? user.name.charAt(0).toUpperCase() : 'S'}
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden sm:block" />
              </button>

              {showUserDropdown && (
                <div className="absolute right-0 mt-2 w-64 bg-white border border-slate-200 rounded-2xl p-2.5 shadow-2xl z-50 text-sm">
                  <div className="p-3 border-b border-slate-100 mb-1">
                    <p className="font-bold text-slate-900 text-sm truncate">{user?.name || 'Saad Ali Qureshi'}</p>
                    <p className="text-xs text-slate-500 truncate mt-0.5">{user?.email || 'saad@archai.design'}</p>
                    <span className="inline-block mt-2 px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 font-mono text-xs font-bold border border-blue-200">
                      {ROLE_DRAWER_CONFIG[currentRole]?.badgeLabel || currentRole}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      setActiveNav('settings');
                      setShowUserDropdown(false);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-xl transition text-left cursor-pointer font-medium text-xs"
                  >
                    <User className="w-4 h-4 text-slate-500" />
                    <span>Account Settings</span>
                  </button>

                  <div className="my-1 border-t border-slate-100"></div>

                  <button
                    type="button"
                    onClick={() => {
                      logout();
                      setActiveTab('landing');
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition text-left cursor-pointer font-medium text-xs"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>

          </div>
        </header>

        {/* DYNAMIC VIEW ROUTER */}
        <div className="flex-1 overflow-y-auto p-5 md:p-8">
          
          {/* 1. DASHBOARD VIEW */}
          {activeNav === 'dashboard' && (
            user?.role === ROLES.SYSTEM_ADMIN ? (
              <AdminDashboardModule />
            ) : (
              <div className="max-w-7xl mx-auto space-y-7 md:space-y-9 pb-12">
                
                {/* 1. HERO GREETING BANNER WITH AI PROMPT SYNTHESIZER */}
                <HeroGreetingBanner 
                  architectName={user?.name?.split(' ')[0] || 'Saad'}
                  userRole={currentRole}
                  onStartNewProject={() => setActiveNav('new-design')}
                  onQuickGenerate={(prompt) => {
                    setQuickPrompt(prompt);
                    handleQuickSynthesis();
                  }}
                />

                {/* 2. REAL-TIME TELEMETRY & 4 KPI METRIC CARDS */}
                <TelemetryKpiGrid 
                  userRole={currentRole}
                  onSelectKpi={(kpiId) => {
                    if (kpiId === 'projects' || kpiId === 'templates' || kpiId === 'sites') setActiveNav('projects');
                    else if (kpiId === 'generations' || kpiId === 'new-design') setActiveNav('new-design');
                    else if (kpiId === 'cost-estimate' || kpiId === 'cost-estimation') setActiveNav('cost-estimation');
                    else if (kpiId === 'usage-hours' || kpiId === 'analytics') setActiveNav('analytics');
                  }}
                />

                {/* ROLE-SPECIFIC SPECIALIZED EXECUTIVE DASHBOARDS */}
                {currentRole === ROLES.ARCHITECT && (
                  <ArchitectDashboardView onOpenStudio={onOpenStudio} setActiveNav={setActiveNav} />
                )}
                {currentRole === ROLES.CONSTRUCTION_PRO && (
                  <ConstructionDashboardView onOpenStudio={onOpenStudio} setActiveNav={setActiveNav} />
                )}
                {currentRole === ROLES.DESIGNER && (
                  <DesignerDashboardView onOpenStudio={onOpenStudio} setActiveNav={setActiveNav} />
                )}
                {currentRole === ROLES.REAL_ESTATE_DEV && (
                  <DeveloperDashboardView onOpenStudio={onOpenStudio} setActiveNav={setActiveNav} />
                )}

                {/* VISUAL ANALYTICS, BUDGET SPREADS & TIMELINE CHARTS */}
                <DashboardCharts />

                {/* CURATED ARCHITECTURAL DESIGN TEMPLATES */}
                <TemplateGallerySection 
                  onSelectTemplate={(tpl) => {
                    if (onOpenStudio) onOpenStudio(tpl.model || '5marla');
                  }}
                  onUseTemplate={(tpl) => {
                    setQuickPrompt(`${tpl.name} - ${tpl.plotSize} architecture for residential plot in Pakistan`);
                    setActiveNav('new-design');
                  }}
                />

                {/* 3. CORE STUDIO CAPABILITIES (WHAT THE DASHBOARD IS & DOES) */}
                <div className="bg-white border border-slate-200/90 rounded-3xl p-6 md:p-8 shadow-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-5">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span>
                        <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-blue-600">ArchAI Studio Command Center</span>
                      </div>
                      <h2 className="text-lg md:text-xl font-extrabold text-slate-900 mt-0.5">What You Can Do in ArchAI Studio</h2>
                      <p className="text-xs text-slate-500 mt-1">
                        An end-to-end intelligent architecture platform designed specifically for Pakistani plot standards and international CAD/BIM regulations.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-semibold px-3 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                        ⚡ v2.4 Multi-Agent Neural BIM
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-5">
                    {[
                      {
                        title: 'AI Floor Plan Synthesis',
                        desc: 'Prompt-to-blueprint in 30 seconds with AIA layering, wall thickness, and OTS lightwells.',
                        icon: Wand2,
                        action: () => setActiveNav('new-design'),
                        btnText: 'Start Generation',
                        color: 'blue'
                      },
                      {
                        title: 'Society Bylaws Verification',
                        desc: 'Automatic setback compliance checks for CDA Islamabad, LDA Lahore, Bahria Town, and DHA.',
                        icon: ShieldCheck,
                        action: () => setActiveNav('notifications'),
                        btnText: 'Audit Bylaws',
                        color: 'emerald'
                      },
                      {
                        title: 'Live Construction BOQ',
                        desc: 'Real-time Pakistani market steel, cement, bricks, and labor rate breakdowns with PDF exports.',
                        icon: Calculator,
                        action: () => setActiveNav('cost-estimation'),
                        btnText: 'Calculate Cost',
                        color: 'amber'
                      },
                      {
                        title: '3D WebGL & CAD Exports',
                        desc: 'Interactive 3D walkthroughs, layered AutoCAD .DXF blueprints, and Blender 3D solids.',
                        icon: Box,
                        action: () => onOpenStudio && onOpenStudio('5marla'),
                        btnText: 'Open 3D Studio',
                        color: 'indigo'
                      }
                    ].map((cap, cIdx) => {
                      const Icon = cap.icon;
                      return (
                        <div 
                          key={cIdx}
                          onClick={cap.action}
                          className="p-5 rounded-2xl bg-slate-50/70 hover:bg-white border border-slate-200/80 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
                        >
                          <div>
                            <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 shadow-2xs flex items-center justify-center text-slate-700 group-hover:text-blue-600 group-hover:scale-110 transition-all">
                              <Icon className="w-5 h-5" />
                            </div>
                            <h3 className="text-sm font-bold text-slate-900 mt-3.5 group-hover:text-blue-600 transition-colors">
                              {cap.title}
                            </h3>
                            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                              {cap.desc}
                            </p>
                          </div>
                          <div className="pt-4 mt-3 border-t border-slate-200/60 flex items-center justify-between text-xs font-bold text-blue-600 group-hover:text-blue-700">
                            <span>{cap.btnText}</span>
                            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* 4. PAKISTANI RESIDENTIAL PLOT MATRIX */}
                <div className="p-6 md:p-8 bg-white border border-slate-200/90 rounded-3xl shadow-xs space-y-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <Home className="w-5 h-5 text-blue-600" />
                        <h2 className="text-lg md:text-xl font-extrabold text-slate-900">Standard Pakistani Plot Blueprints</h2>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">Pre-verified residential blueprints compliant with CDA (Islamabad) & LDA (Lahore) building bylaws.</p>
                    </div>
                    <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-3.5 py-1.5 rounded-full border border-emerald-200 shrink-0 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>CDA, LDA & Bahria Bylaws Synced</span>
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { 
                        size: '3 Marla', 
                        dimensions: '20′ × 34′ (680 sq ft)', 
                        specs: '2 Story • 3 Bed Ensuite • Car Porch', 
                        cost: '₨ 4.8M - 5.5M', 
                        coveredArea: '1,250 sq ft',
                        bylaw: 'Front 3ft Setback • 80% Coverage',
                        model: '3marla' 
                      },
                      { 
                        size: '5 Marla', 
                        dimensions: '25′ × 45′ (1,125 sq ft)', 
                        specs: 'Double Story • 4 Bed Ensuite • Lawn & OTS', 
                        cost: '₨ 7.5M - 8.6M', 
                        coveredArea: '2,150 sq ft',
                        bylaw: 'Front 5ft, Rear 3ft Setback',
                        model: '5marla', 
                        popular: true 
                      },
                      { 
                        size: '10 Marla', 
                        dimensions: '35′ × 65′ (2,275 sq ft)', 
                        specs: 'Executive Villa • 5 Bed • Servant Qtr', 
                        cost: '₨ 14.8M - 17.2M', 
                        coveredArea: '3,800 sq ft',
                        bylaw: 'Front 8ft, Rear 5ft, Side 4ft',
                        model: '10marla' 
                      },
                      { 
                        size: '1 Kanal', 
                        dimensions: '50′ × 90′ (4,500 sq ft)', 
                        specs: 'Master Estate • 5-6 Bed • Pool & Portico', 
                        cost: '₨ 28M - 34M', 
                        coveredArea: '6,500 sq ft',
                        bylaw: 'Front 10ft, Rear 8ft, Both Sides 5ft',
                        model: '1kanal' 
                      },
                    ].map((plot, pIdx) => (
                      <div
                        key={pIdx}
                        onClick={() => {
                          setQuickPrompt(`${plot.size} luxury modern residential house plan with ${plot.specs} in Islamabad`);
                          if (onOpenStudio) onOpenStudio(plot.model);
                        }}
                        className={`p-5 rounded-2xl border transition-all cursor-pointer group hover:-translate-y-1 relative flex flex-col justify-between ${
                          plot.popular
                            ? 'bg-gradient-to-br from-blue-50/70 via-indigo-50/40 to-white border-blue-400 shadow-md shadow-blue-500/10 ring-1 ring-blue-400'
                            : 'bg-slate-50/70 hover:bg-white border-slate-200/90 hover:border-blue-300 hover:shadow-md'
                        }`}
                      >
                        {plot.popular && (
                          <span className="absolute -top-2.5 right-4 text-[10px] font-mono font-bold bg-blue-600 text-white px-2.5 py-0.5 rounded-full shadow-xs">
                            ★ Most Popular
                          </span>
                        )}

                        <div>
                          <div className="flex items-center justify-between">
                            <span className="text-lg font-extrabold text-slate-900 group-hover:text-blue-600 transition-colors">
                              {plot.size}
                            </span>
                            <span className="text-xs font-mono text-slate-500 font-semibold">{plot.dimensions}</span>
                          </div>

                          <p className="text-xs text-slate-700 mt-2 font-medium leading-relaxed">
                            {plot.specs}
                          </p>

                          <div className="mt-3 space-y-1.5 text-[11px] text-slate-500">
                            <div className="flex items-center justify-between">
                              <span>Covered Area:</span>
                              <span className="font-mono font-bold text-slate-700">{plot.coveredArea}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span>Bylaws:</span>
                              <span className="font-mono text-emerald-700 font-semibold">{plot.bylaw}</span>
                            </div>
                          </div>
                        </div>

                        <div className="mt-4 pt-3.5 border-t border-slate-200/80 flex items-center justify-between">
                          <div>
                            <span className="text-[10px] text-slate-400 uppercase font-mono block">Estimated Cost</span>
                            <span className="font-extrabold text-slate-900 text-sm font-mono">{plot.cost}</span>
                          </div>
                          <span className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-xs group-hover:scale-105">
                            Launch 3D →
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 5. LIVE CONSTRUCTION RATES & MATERIAL MARKET TICKER */}
                  <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 text-white shadow-xl space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="relative flex h-2.5 w-2.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400"></span>
                        </span>
                        <span className="font-bold text-sm">Pakistan Real-Time Construction Material Indices (Islamabad & Lahore)</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setActiveNav('cost-estimation')}
                        className="text-xs font-bold text-cyan-300 hover:text-white flex items-center gap-1 cursor-pointer"
                      >
                        <span>Calculate Full BOQ with Labor Rates</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
                      <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-[10px] text-slate-400 font-mono block">Steel (60-Grade)</span>
                        <span className="text-sm font-bold text-white font-mono mt-0.5 block">₨ 264 / kg</span>
                        <span className="text-[10px] text-emerald-400">Amreli / Mughal</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-[10px] text-slate-400 font-mono block">Cement (Grade 53)</span>
                        <span className="text-sm font-bold text-white font-mono mt-0.5 block">₨ 1,320 / bag</span>
                        <span className="text-[10px] text-emerald-400">Bestway / Fauji</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-[10px] text-slate-400 font-mono block">A-Grade Bricks</span>
                        <span className="text-sm font-bold text-white font-mono mt-0.5 block">₨ 14.5 / pc</span>
                        <span className="text-[10px] text-slate-400">Gutka / Kiln Red</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-[10px] text-slate-400 font-mono block">Chenab Sand</span>
                        <span className="text-sm font-bold text-white font-mono mt-0.5 block">₨ 45 / cu ft</span>
                        <span className="text-[10px] text-slate-400">Screened Coarse</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-[10px] text-slate-400 font-mono block">Grey Structure</span>
                        <span className="text-sm font-bold text-cyan-300 font-mono mt-0.5 block">₨ 2,950 / sqft</span>
                        <span className="text-[10px] text-cyan-400">Turnkey Direct</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-[10px] text-slate-400 font-mono block">A-Grade Finishing</span>
                        <span className="text-sm font-bold text-indigo-300 font-mono mt-0.5 block">₨ 5,200 / sqft</span>
                        <span className="text-[10px] text-indigo-400">Tiles & Sanitary</span>
                      </div>
                    </div>
                  </div>

                </div>

                {/* 6. RECENT STUDIO BLUEPRINTS & SAVED PROJECTS */}
                <div className="bg-white border border-slate-200/90 rounded-3xl p-6 md:p-8 shadow-xs space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                      <h2 className="text-lg md:text-xl font-extrabold text-slate-900 flex items-center gap-2">
                        <FolderKanban className="w-5 h-5 text-blue-600" />
                        <span>Recent Studio Blueprints & Saved House Plans</span>
                      </h2>
                      <p className="text-xs text-slate-500 mt-0.5">Explore your active architectural designs, inspect 3D models, and export DXF blueprints.</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setActiveNav('projects')}
                      className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
                    >
                      <span>View All Projects</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      {
                        title: '5 Marla Contemporary Villa',
                        location: 'Sector G-13, Islamabad',
                        specs: '3 Bed Ensuite • Car Porch • Open Kitchen • OTS',
                        status: 'BIM LOD-300 Ready',
                        statusColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
                        bylaw: '100% CDA Compliant',
                        cost: '₨ 7.85M',
                        date: 'Generated Today',
                        model: '5marla'
                      },
                      {
                        title: '10 Marla Spanish Hacienda',
                        location: 'DHA Phase 6, Lahore',
                        specs: '4 Master Suites • Double Height Lounge • Front Lawn',
                        status: 'In Synthesis',
                        statusColor: 'bg-blue-50 text-blue-700 border-blue-200',
                        bylaw: 'LDA Setbacks OK',
                        cost: '₨ 16.2M',
                        date: 'Yesterday',
                        model: '10marla'
                      },
                      {
                        title: '3 Marla Modern Urban Infill',
                        location: 'Bahria Town Phase 8, Rawalpindi',
                        specs: '3 Bed • Rooftop Patio • Compact Parking',
                        status: 'Cost Verified',
                        statusColor: 'bg-purple-50 text-purple-700 border-purple-200',
                        bylaw: 'Bahria Bylaws OK',
                        cost: '₨ 5.15M',
                        date: '3 days ago',
                        model: '3marla'
                      }
                    ].map((proj, idx) => (
                      <div 
                        key={idx}
                        className="p-5 rounded-2xl border border-slate-200 hover:border-blue-400 hover:shadow-lg transition-all bg-slate-50/50 hover:bg-white flex flex-col justify-between group"
                      >
                        <div>
                          <div className="flex items-center justify-between gap-2">
                            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border ${proj.statusColor}`}>
                              {proj.status}
                            </span>
                            <span className="text-[11px] font-mono text-slate-400">{proj.date}</span>
                          </div>

                          <h3 className="text-base font-bold text-slate-900 mt-2.5 group-hover:text-blue-600 transition-colors">
                            {proj.title}
                          </h3>
                          <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-0.5">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            <span>{proj.location}</span>
                          </div>

                          <p className="text-xs text-slate-600 mt-2.5 font-medium leading-relaxed">
                            {proj.specs}
                          </p>

                          <div className="mt-4 pt-3 border-t border-slate-200/70 flex items-center justify-between text-xs">
                            <span className="text-slate-500">Est. Budget:</span>
                            <span className="font-extrabold text-slate-900 font-mono">{proj.cost}</span>
                          </div>
                        </div>

                        <div className="mt-4 pt-3 border-t border-slate-200/70 flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => onOpenStudio && onOpenStudio(proj.model)}
                            className="flex-1 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition cursor-pointer text-center shadow-xs"
                          >
                            Open in 3D
                          </button>
                          <button
                            type="button"
                            onClick={() => setActiveNav('cost-estimation')}
                            className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition cursor-pointer"
                            title="Inspect BOQ"
                          >
                            BOQ
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 7. SPATIAL VIEWPORT & INTERACTIVE CANVAS DOCK */}
                <div className="bg-white border border-slate-200/90 rounded-3xl overflow-hidden shadow-xs">
                  <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 bg-slate-50/70">
                    <div className="flex items-center gap-2 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
                      <button
                        type="button"
                        onClick={() => setActiveCanvasView('view3d')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-2 ${
                          activeCanvasView === 'view3d'
                            ? 'bg-blue-600 text-white shadow-xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        <Box className="w-4 h-4" />
                        <span>3D WebGL Scene</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setActiveCanvasView('editor2d')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-2 ${
                          activeCanvasView === 'editor2d'
                            ? 'bg-blue-600 text-white shadow-xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        <LayoutGrid className="w-4 h-4" />
                        <span>2D Floor Editor</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setActiveCanvasView('compare')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-2 ${
                          activeCanvasView === 'compare'
                            ? 'bg-blue-600 text-white shadow-xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        <Scale className="w-4 h-4" />
                        <span>Design Matrix</span>
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onOpenStudio && onOpenStudio('5marla')}
                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer shadow-xs hover:scale-[1.01]"
                      >
                        <Sparkles className="w-4 h-4 text-cyan-300" />
                        <span>Launch Full-Screen Studio</span>
                      </button>
                    </div>
                  </div>

                  <div className="min-h-[520px] bg-slate-50 p-6">
                    {activeCanvasView === 'view3d' && (
                      <BuildingViewport3D 
                        selectedModel="5marla" 
                        onOpenStudio={() => onOpenStudio && onOpenStudio('5marla')}
                      />
                    )}
                    {activeCanvasView === 'editor2d' && (
                      <FloorPlanEditor2D />
                    )}
                    {activeCanvasView === 'compare' && (
                      <DesignComparisonMatrix />
                    )}
                  </div>
                </div>

              </div>
            )
          )}

          {/* 2. REQUIREMENTS GENERATOR (AI Floor Plan & 3D Wizard) */}
          {activeNav === 'new-design' && (
            <div className="space-y-4">
              {/* Back to Dashboard Navigation Strip */}
              <div className="flex flex-wrap items-center justify-between gap-3 bg-white/95 backdrop-blur-sm p-3.5 px-5 rounded-2xl border border-slate-200/90 shadow-2xs">
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setActiveNav('dashboard')}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-800 text-xs font-bold transition cursor-pointer border border-slate-200/80 shadow-2xs"
                  >
                    <ChevronLeft className="w-4 h-4 text-blue-600" />
                    <span>← Back to Dashboard Overview</span>
                  </button>
                  <span className="text-slate-300 hidden sm:inline">|</span>
                  <span className="text-xs text-slate-500 font-medium hidden sm:inline">
                    Currently viewing: <strong className="text-slate-800">New Design Generator &amp; AI Floor Plan Wizard</strong>
                  </span>
                </div>
                
                <button
                  type="button"
                  onClick={() => setActiveNav('dashboard')}
                  className="text-xs text-blue-600 hover:text-blue-700 font-bold flex items-center gap-1.5 cursor-pointer bg-blue-50 hover:bg-blue-100/80 px-3 py-1.5 rounded-xl transition"
                >
                  <LayoutDashboard className="w-3.5 h-3.5" />
                  <span>Show Full Dashboard</span>
                </button>
              </div>

              <RequirementsGenerator 
                onOpenStudio={onOpenStudio} 
                onSaveProject={() => setActiveNav('projects')}
              />
            </div>
          )}

          {/* 3. SAVED PROJECTS */}
          {activeNav === 'projects' && (
            <ProjectsModule 
              onOpenStudio={onOpenStudio}
              onNewDesign={() => setActiveNav('new-design')}
            />
          )}

          {/* 4. LOCATION-AWARE COST ESTIMATION & RATES */}
          {activeNav === 'cost-estimation' && (
            <CostEstimatorPage 
              setActiveTab={setActiveTab}
              onOpenStudio={onOpenStudio}
            />
          )}


          {/* 5. TEAM COLLABORATION (Protected for Architects, Admins & Developers) */}
          {activeNav === 'team' && (
            <ProtectedRoute allowedRoles={[ROLES.SYSTEM_ADMIN, ROLES.ARCHITECT, ROLES.REAL_ESTATE_DEV]}>
              <TeamModule />
            </ProtectedRoute>
          )}

          {/* 5. ANALYTICS & REPORTS (Protected for Technical/Management Roles) */}
          {activeNav === 'analytics' && (
            <ProtectedRoute allowedRoles={[ROLES.SYSTEM_ADMIN, ROLES.ARCHITECT, ROLES.CONSTRUCTION_PRO, ROLES.REAL_ESTATE_DEV]}>
              <AnalyticsModule onOpenStudio={onOpenStudio} />
            </ProtectedRoute>
          )}

          {/* 6. NOTIFICATION CENTER */}
          {activeNav === 'notifications' && (
            <NotificationsModule onOpenStudio={onOpenStudio} />
          )}

          {/* 7. FEEDBACK & REVIEWS */}
          {activeNav === 'feedback' && (
            <FeedbackModule />
          )}

          {/* 8. SETTINGS & PROFILE */}
          {activeNav === 'settings' && <SettingsModule defaultTab="profile" />}

          {/* 9. TEMPLATES DISCOVERY GALLERY */}
          {activeNav === 'templates' && (
            <div className="max-w-7xl mx-auto space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xs">
                <div>
                  <h1 className="text-xl font-black text-slate-900 dark:text-white">Architectural Design Templates</h1>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Explore pre-tested residential, villa, and modern infill templates compliant with Pakistani building authorities.</p>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveNav('dashboard')}
                  className="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 text-xs font-bold transition cursor-pointer self-start sm:self-auto"
                >
                  ← Back to Dashboard
                </button>
              </div>

              <TemplateGallerySection 
                onSelectTemplate={(tpl) => {
                  if (onOpenStudio) onOpenStudio(tpl.model || '5marla');
                }}
                onUseTemplate={(tpl) => {
                  setQuickPrompt(`${tpl.name} - ${tpl.plotSize} architecture for residential plot in Pakistan`);
                  setActiveNav('new-design');
                }}
              />
            </div>
          )}

          {/* 10. ARCHIVE & VERSION HISTORY */}
          {activeNav === 'archive' && (
            <ArchiveModule onRestore={(item) => {
              showToast(`Restored design blueprint: ${item?.title || 'Project'}`);
              setActiveNav('projects');
            }} />
          )}

          {/* 11. ADMIN CONSOLE (Exclusively for SYSTEM_ADMIN) */}
          {activeNav === 'admin-console' && (
            <ProtectedRoute allowedRoles={[ROLES.SYSTEM_ADMIN]}>
              <AdminDashboardModule />
            </ProtectedRoute>
          )}

        </div>
      </div>

      {/* GLOBAL COMMAND PALETTE (Cmd+K / Ctrl+K) */}
      <CommandPaletteModal 
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onNavigate={(target) => {
          if (target === 'studio-5marla' || target === 'studio-10marla') {
            onOpenStudio && onOpenStudio(target.replace('studio-', ''));
          } else {
            setActiveNav(target);
          }
        }}
        onOpenStudio={onOpenStudio}
      />

      {/* FLOATING TOAST NOTIFICATION */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 bg-slate-900/95 dark:bg-slate-100/95 text-white dark:text-slate-900 rounded-2xl shadow-2xl backdrop-blur-md border border-white/10 dark:border-slate-200 text-xs font-semibold animate-in fade-in slide-in-from-bottom-4 duration-200">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span>{toastMessage}</span>
          <button 
            type="button"
            onClick={() => setToastMessage('')}
            className="ml-2 text-slate-400 hover:text-white dark:hover:text-slate-900 cursor-pointer text-sm"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}

