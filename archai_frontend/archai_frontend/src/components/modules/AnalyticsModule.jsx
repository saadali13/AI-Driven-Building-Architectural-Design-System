import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Sparkles, 
  Layers, 
  Cpu, 
  HardDrive, 
  Database, 
  DollarSign, 
  Calendar, 
  Download, 
  CheckCircle2, 
  ArrowUpRight, 
  ArrowDownRight, 
  FileCode, 
  FileText, 
  Zap, 
  Clock, 
  Scale, 
  Box, 
  RefreshCw, 
  Activity,
  Sliders,
  Info,
  Check
} from 'lucide-react';

export default function AnalyticsModule({ onOpenStudio }) {
  const [timeframe, setTimeframe] = useState('1Y');
  const [isExporting, setIsExporting] = useState(false);
  const [exportNotice, setExportNotice] = useState('');

  const monthlyTrends = [
    { month: 'Jan', queries: 2150, projects: 84, exports: 62, costEstM: 32.5 },
    { month: 'Feb', queries: 2480, projects: 96, exports: 74, costEstM: 36.8 },
    { month: 'Mar', queries: 2890, projects: 110, exports: 88, costEstM: 41.2 },
    { month: 'Apr', queries: 3120, projects: 124, exports: 95, costEstM: 44.0 },
    { month: 'May', queries: 3450, projects: 135, exports: 108, costEstM: 46.5 },
    { month: 'Jun', queries: 3200, projects: 120, exports: 92, costEstM: 39.8 },
    { month: 'Jul', queries: 3680, projects: 142, exports: 118, costEstM: 52.4 },
    { month: 'Aug', queries: 4100, projects: 158, exports: 134, costEstM: 58.1 },
    { month: 'Sep', queries: 3950, projects: 146, exports: 122, costEstM: 49.3 },
    { month: 'Oct', queries: 4300, projects: 165, exports: 140, costEstM: 61.2 },
    { month: 'Nov', queries: 4720, projects: 178, exports: 156, costEstM: 65.5 },
    { month: 'Dec', queries: 4900, projects: 190, exports: 172, costEstM: 69.8 },
  ];

  const handleExport = (type) => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      setExportNotice(`ArchAI Comprehensive ${type.toUpperCase()} Analytics Report downloaded!`);
      setTimeout(() => setExportNotice(''), 4000);
    }, 800);
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 text-slate-900 font-sans">
      
      {/* Toast Notification */}
      {exportNotice && (
        <div className="fixed top-6 right-6 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-xl flex items-center gap-2.5 text-xs font-semibold animate-in fade-in">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{exportNotice}</span>
        </div>
      )}

      {/* Header Bar */}
      <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">AI Spatial Generation &amp; Cost Intelligence</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time inference query statistics, dense vector match rates, and Pakistani market construction cost distributions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handleExport('pdf')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow-md shadow-blue-500/20 flex items-center gap-2 cursor-pointer hover:scale-[1.01]"
          >
            <Download className="w-4 h-4" />
            <span>Export Analytics Report</span>
          </button>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <span className="text-[11px] font-mono uppercase text-slate-500 font-bold">Total Spatial Queries</span>
          <h3 className="text-2xl font-black text-slate-900 mt-1">42,040</h3>
          <span className="text-[10px] text-emerald-600 font-bold flex items-center gap-1 mt-1">
            <TrendingUp className="w-3 h-3" /> +18.4% vs last quarter
          </span>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <span className="text-[11px] font-mono uppercase text-slate-500 font-bold">Vector Cosine Match</span>
          <h3 className="text-2xl font-black text-slate-900 mt-1">98.4%</h3>
          <span className="text-[10px] text-blue-600 font-bold flex items-center gap-1 mt-1">
            <Zap className="w-3 h-3" /> 384-Dim MiniLM
          </span>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <span className="text-[11px] font-mono uppercase text-slate-500 font-bold">Blueprints Exported</span>
          <h3 className="text-2xl font-black text-slate-900 mt-1">1,450 CAD/PDF</h3>
          <span className="text-[10px] text-emerald-600 font-bold flex items-center gap-1 mt-1">
            <HardDrive className="w-3 h-3" /> DXF Vectorized
          </span>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <span className="text-[11px] font-mono uppercase text-slate-500 font-bold">Total PKR Estimated</span>
          <h3 className="text-2xl font-black text-slate-900 mt-1">₨ 587.2M</h3>
          <span className="text-[10px] text-purple-600 font-bold flex items-center gap-1 mt-1">
            <DollarSign className="w-3 h-3" /> Concrete &amp; Steel Index
          </span>
        </div>

      </div>

      {/* 12-Month Generation Trends Chart Simulation */}
      <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">12-Month AI Generation &amp; Synthesis Trends</h3>
            <p className="text-xs text-slate-500">Monthly query volume and project export throughput</p>
          </div>
          <span className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full font-mono text-[10px] font-bold border border-blue-200">
            2026 Live Metrics
          </span>
        </div>

        {/* Visual Bar Chart */}
        <div className="pt-4 h-64 flex items-end justify-between gap-2 border-b border-slate-200 pb-2">
          {monthlyTrends.map((m) => {
            const heightPct = (m.queries / 5000) * 100;
            return (
              <div key={m.month} className="flex-1 flex flex-col items-center gap-1 group">
                <div className="text-[10px] font-mono text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
                  {m.queries}
                </div>
                <div 
                  className="w-full max-w-[36px] bg-blue-100 hover:bg-blue-600 group-hover:shadow-md rounded-t-lg transition-all"
                  style={{ height: `${heightPct}%` }}
                ></div>
                <span className="text-[10px] font-bold text-slate-600 mt-1">{m.month}</span>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}
