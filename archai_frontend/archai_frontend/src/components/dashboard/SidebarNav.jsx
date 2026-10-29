import React from 'react';
import { 
  LayoutDashboard, 
  FolderKanban, 
  Sparkles, 
  Layers, 
  Calculator, 
  BarChart3, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  ShieldCheck,
  Cpu,
  Lock
} from 'lucide-react';
import BrandLogo from '../common/BrandLogo';


export const NAVIGATION_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: null },
  { id: 'projects', label: 'Projects', icon: FolderKanban, badge: '28' },
  { id: 'ai-generator', label: 'AI Generator', icon: Sparkles, badge: 'v2.4' },
  { id: 'templates', label: 'Templates', icon: Layers, badge: '42' },
  { id: 'cost-estimation', label: 'Cost Estimation', icon: Calculator, badge: null },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, badge: null },
  { id: 'settings', label: 'Settings', icon: Settings, badge: null },
];

export default function SidebarNav({ 
  activeNav = 'dashboard', 
  onSelectNav, 
  collapsed = false, 
  onToggleCollapse,
  userRole = 'ARCHITECT'
}) {
  return (
    <aside 
      className={`relative flex flex-col h-full bg-white border-r border-slate-200/90 transition-all duration-300 ease-in-out shrink-0 select-none z-30 ${
        collapsed ? 'w-20' : 'w-72'
      }`}
    >
      {/* Brand Header */}
      <div className="h-20 flex items-center justify-between px-5 border-b border-slate-100">
        <BrandLogo size="md" collapsed={collapsed} />
        
        <button
          type="button"
          onClick={onToggleCollapse}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer border border-transparent hover:border-slate-200"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          aria-label="Toggle Sidebar"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Main Navigation Menu */}
      <nav className="flex-1 py-6 px-3.5 space-y-1.5 overflow-y-auto">
        <div className={`px-3 mb-2 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 ${collapsed ? 'hidden' : 'block'}`}>
          Core Modules
        </div>

        {NAVIGATION_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeNav === item.id;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectNav && onSelectNav(item.id)}
              className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-2xl text-base font-bold transition-all duration-150 cursor-pointer group relative ${
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
              }`}
              title={collapsed ? item.label : undefined}
            >
              {/* Left Active Indicator Glow */}
              {isActive && (
                <span className="absolute left-0 top-2.5 bottom-2.5 w-1.5 rounded-r-md bg-white shadow-xs" />
              )}

              <Icon className={`w-6 h-6 shrink-0 transition-transform group-hover:scale-105 ${
                isActive ? 'text-white' : 'text-slate-400 group-hover:text-blue-600'
              }`} />

              {!collapsed && (
                <span className="truncate flex-1 text-left">
                  {item.label}
                </span>
              )}

              {!collapsed && item.badge && (
                <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded-full uppercase ${
                  isActive 
                    ? 'bg-white/20 text-white' 
                    : 'bg-slate-100 text-slate-600 group-hover:bg-blue-50 group-hover:text-blue-600'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>

          );
        })}
      </nav>

      {/* System Status & License Clearance Footer */}
      <div className="p-3.5 border-t border-slate-100 bg-slate-50/60">
        {!collapsed ? (
          <div
            onClick={() => onSelectNav && onSelectNav('settings')}
            className="p-3 bg-white hover:bg-blue-50/50 border border-slate-200/80 hover:border-blue-300 rounded-2xl shadow-2xs space-y-2.5 cursor-pointer transition-all group"
            title="Click to view Settings & Profile"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-[11px] font-mono font-bold text-slate-700 group-hover:text-blue-600 transition-colors">Architext_v1 Active</span>
              </div>
              <span className="text-[10px] font-mono text-emerald-600 font-bold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                14ms
              </span>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span className="flex items-center gap-1 font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                Profile Settings
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
            </div>
          </div>

        ) : (
          <div className="flex flex-col items-center gap-2 py-1">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 ring-4 ring-emerald-100" title="Engine Online (14ms)" />
          </div>
        )}
      </div>
    </aside>
  );
}
