import React from 'react';
import { 
  PieChart, 
  BarChart3, 
  TrendingUp, 
  Layers, 
  Activity, 
  Calendar,
  CheckCircle2,
  Clock
} from 'lucide-react';

export default function DashboardCharts({
  userRole = 'HOMEOWNER'
}) {
  // 1. Budget Breakdown data (Pakistani residential average)
  const budgetData = [
    { label: 'Grey Structure (Civil)', pct: 44, color: 'bg-blue-600', stroke: '#2563eb' },
    { label: 'Finishing & Tiles', pct: 32, color: 'bg-teal-500', stroke: '#14b8a6' },
    { label: 'Labor & Supervision', pct: 14, color: 'bg-amber-500', stroke: '#f59e0b' },
    { label: 'MEP (Plumbing & Elec)', pct: 10, color: 'bg-indigo-500', stroke: '#6366f1' },
  ];

  // 2. Weekly Activity Syntheses
  const weeklyActivity = [
    { day: 'Mon', count: 12, height: '45%' },
    { day: 'Tue', count: 19, height: '65%' },
    { day: 'Wed', count: 28, height: '90%' },
    { day: 'Thu', count: 22, height: '75%' },
    { day: 'Fri', count: 34, height: '100%' },
    { day: 'Sat', count: 16, height: '55%' },
    { day: 'Sun', count: 8, height: '30%' },
  ];

  // 3. Project Workflow Stages
  const stages = [
    { name: 'Initial NLP Spatial Synthesis', status: 'Completed', date: 'Oct 14' },
    { name: 'CDA / LDA Bylaw Setback Audit', status: 'Completed', date: 'Oct 15' },
    { name: 'AIA Layered DXF CAD Blueprint', status: 'In Progress', date: 'Oct 16' },
    { name: 'Client 3D Walkthrough Sign-off', status: 'Pending', date: 'Next Up' },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      
      {/* Chart 1: Material & Cost Allocation */}
      <div className="p-5 md:p-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
                Cost Allocation
              </span>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                Pakistani Residential BOQ Split
              </h3>
            </div>
            <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center">
              <PieChart className="w-4 h-4" />
            </div>
          </div>

          {/* Stacked Progress Bar */}
          <div className="mt-5 space-y-2">
            <div className="h-3 w-full rounded-full overflow-hidden flex bg-slate-100 dark:bg-slate-800 shadow-inner">
              {budgetData.map((item, i) => (
                <div
                  key={i}
                  style={{ width: `${item.pct}%` }}
                  className={`${item.color} h-full transition-all duration-500`}
                  title={`${item.label}: ${item.pct}%`}
                />
              ))}
            </div>

            <div className="pt-3 space-y-2.5">
              {budgetData.map((item, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                    <span className="text-slate-600 dark:text-slate-300 font-medium">{item.label}</span>
                  </div>
                  <span className="font-mono font-bold text-slate-900 dark:text-white">{item.pct}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Target Budget: <strong>₨ 8.5M</strong></span>
          <span className="text-emerald-600 font-bold">Within 2.4% Margin</span>
        </div>
      </div>

      {/* Chart 2: Weekly Design Syntheses Trend */}
      <div className="p-5 md:p-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
                Engine Activity
              </span>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                Weekly Floor Plan Syntheses
              </h3>
            </div>
            <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 flex items-center justify-center">
              <BarChart3 className="w-4 h-4" />
            </div>
          </div>

          {/* Bar Chart Visual */}
          <div className="mt-6 flex items-end justify-between gap-2 h-32 px-1">
            {weeklyActivity.map((bar, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group">
                <span className="text-[10px] font-mono text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
                  {bar.count}
                </span>
                <div 
                  className="w-full max-w-[28px] rounded-t-lg bg-gradient-to-t from-blue-600 to-indigo-500 group-hover:from-blue-500 group-hover:to-cyan-400 transition-all duration-300 shadow-2xs"
                  style={{ height: bar.height }}
                />
                <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400 font-medium">
                  {bar.day}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Weekly Total: <strong>135 Designs</strong></span>
          <span className="text-emerald-600 font-bold flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            <span>+18.4%</span>
          </span>
        </div>
      </div>

      {/* Chart 3: Active Milestone Progress Tracker */}
      <div className="p-5 md:p-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
                Workflow Progress
              </span>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                Active Villa Milestone Tracker
              </h3>
            </div>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
          </div>

          {/* Stepper Timeline */}
          <div className="mt-4 space-y-3">
            {stages.map((stg, i) => (
              <div key={i} className="flex items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2.5 min-w-0">
                  {stg.status === 'Completed' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  ) : stg.status === 'In Progress' ? (
                    <div className="w-4 h-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-slate-300 dark:border-slate-700 shrink-0" />
                  )}
                  <span className={`truncate font-medium ${
                    stg.status === 'Completed' 
                      ? 'text-slate-800 dark:text-slate-200' 
                      : stg.status === 'In Progress' 
                        ? 'text-blue-600 dark:text-blue-400 font-bold' 
                        : 'text-slate-400'
                  }`}>
                    {stg.name}
                  </span>
                </div>

                <span className="text-[10px] font-mono text-slate-400 shrink-0">{stg.date}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Overall Phase: <strong>Stage 3 of 4</strong></span>
          <span className="text-blue-600 font-bold font-mono">75% Complete</span>
        </div>
      </div>

    </div>
  );
}
