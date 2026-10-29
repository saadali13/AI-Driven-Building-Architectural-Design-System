import React, { useState } from 'react';
import SidebarNav from './SidebarNav';
import HeaderCommandCenter from './HeaderCommandCenter';
import HeroGreetingBanner from './HeroGreetingBanner';
import TelemetryKpiGrid from './TelemetryKpiGrid';
import { 
  Box, 
  LayoutGrid, 
  Scale, 
  Download, 
  Sparkles, 
  ChevronRight,
  PlusCircle,
  FileCode,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function ArchAiStudioDashboard({ 
  user = { name: 'Sarah Vance', role: 'Principal Architect', email: 's.vance@archai.design' },
  onOpenStudioModal,
  onNavigateModule
}) {
  const [activeNav, setActiveNav] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCanvasTab, setActiveCanvasTab] = useState('3d-scene'); // '3d-scene' | '2d-blueprint' | 'matrix'

  const mockRecentProjects = [
    { id: 'p1', title: '5 Marla Contemporary Villa', area: '1,125 sq ft', style: 'Cantilever Terrace', status: 'Ready for BIM', date: 'Today, 11:20 AM' },
    { id: 'p2', title: '10 Marla Dual Family Residence', area: '2,250 sq ft', style: 'Modern Brutalist', status: 'In Synthesis', date: 'Yesterday' },
    { id: 'p3', title: '1 Kanal Executive Estate', area: '4,500 sq ft', style: 'Minimalist Courtyard', status: 'Cost Verified', date: '3 days ago' },
  ];

  const handleNavSelect = (navId) => {
    setActiveNav(navId);
    if (onNavigateModule) onNavigateModule(navId);
  };

  return (
    <div className="flex h-screen w-full bg-[#ffffff] text-slate-900 font-sans overflow-hidden select-none">
      
      {/* 1. Fixed / Collapsible Left Sidebar */}
      <SidebarNav
        activeNav={activeNav}
        onSelectNav={handleNavSelect}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        userRole={user?.role || 'ARCHITECT'}
      />

      {/* 2. Main Viewport */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-slate-50/50">
        
        {/* Top Header Command Center */}
        <HeaderCommandCenter
          user={user}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onOpenNewProject={() => handleNavSelect('ai-generator')}
          onOpenNotifications={() => handleNavSelect('notifications')}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        />

        {/* Scrollable Main Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8">
          <div className="max-w-7xl mx-auto space-y-8">
            
            {/* High-Impact Hero Greeting Banner with Semi-Transparent Architectural Render */}
            <HeroGreetingBanner 
              architectName={user?.name?.split(' ')[0] || 'Architect'}
              onStartNewProject={() => handleNavSelect('ai-generator')}
              onQuickGenerate={(prompt) => {
                if (onOpenStudioModal) onOpenStudioModal('5marla');
              }}
            />

            {/* Real-Time Telemetry & 4 KPI Metric Cards */}
            <TelemetryKpiGrid 
              onSelectKpi={(kpiId) => handleNavSelect(kpiId)}
            />

            {/* Interactive Spatial Canvas Preview Container */}
            <div className="bg-white border border-slate-200/90 rounded-3xl overflow-hidden shadow-xs">
              
              {/* Canvas Header */}
              <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 bg-slate-50/60">
                <div className="flex items-center gap-1.5 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
                  <button
                    type="button"
                    onClick={() => setActiveCanvasTab('3d-scene')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
                      activeCanvasTab === '3d-scene'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Box className="w-4 h-4" />
                    <span>3D WebGL Scene</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveCanvasTab('2d-blueprint')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
                      activeCanvasTab === '2d-blueprint'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <LayoutGrid className="w-4 h-4" />
                    <span>2D Floor Editor</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveCanvasTab('matrix')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
                      activeCanvasTab === 'matrix'
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
                    onClick={() => onOpenStudioModal && onOpenStudioModal('5marla')}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200/80 text-slate-700 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer border border-slate-200"
                  >
                    <Download className="w-3.5 h-3.5 text-blue-600" />
                    <span>Export CAD (DXF / IFC)</span>
                  </button>
                </div>
              </div>

              {/* Canvas Interactive Launchpad */}
              <div className="min-h-[380px] bg-slate-50 p-8 flex items-center justify-center">
                <div className="text-center space-y-4 max-w-md">
                  <div className="w-16 h-16 rounded-3xl bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center mx-auto shadow-sm">
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-slate-900">Spatial Intelligence Viewport Ready</h4>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                      Launch the parametric 3D WebGL viewport or 2D floor editor to manipulate walls, daylight openings, and structural cantilevers.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onOpenStudioModal && onOpenStudioModal('5marla')}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition shadow-md shadow-blue-500/20 cursor-pointer inline-flex items-center gap-2 active:scale-95"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Launch Interactive 3D Studio</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Live Blueprints Feed */}
            <div className="bg-white border border-slate-200/90 rounded-3xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Active AI Blueprints</h3>
                  <p className="text-xs text-slate-500">Live architectural projects generated during this session.</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleNavSelect('projects')}
                  className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
                >
                  <span>View all 28</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                {mockRecentProjects.map((proj) => (
                  <div 
                    key={proj.id}
                    onClick={() => onOpenStudioModal && onOpenStudioModal('5marla')}
                    className="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl hover:bg-white hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
                  >
                    <div className="flex items-start justify-between">
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                        {proj.status}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">{proj.date}</span>
                    </div>

                    <h4 className="font-bold text-sm text-slate-900 mt-2.5 group-hover:text-blue-600 transition-colors">
                      {proj.title}
                    </h4>

                    <div className="flex items-center justify-between text-xs text-slate-500 mt-2">
                      <span>{proj.area}</span>
                      <span className="font-mono text-[11px] text-slate-400">{proj.style}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </main>
      </div>

    </div>
  );
}
