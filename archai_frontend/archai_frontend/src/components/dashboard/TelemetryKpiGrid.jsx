import React from 'react';
import { 
  FolderKanban, 
  Sparkles, 
  Layers, 
  Cpu, 
  TrendingUp, 
  Clock, 
  HardDrive,
  Zap,
  Home,
  Calculator,
  CheckCircle2,
  Building2,
  MapPin,
  Scale,
  ShieldCheck,
  ArrowUpRight
} from 'lucide-react';
import { ROLES } from '../../context/AuthContext';

export default function TelemetryKpiGrid({ 
  userRole = ROLES.HOMEOWNER,
  onSelectKpi 
}) {
  const roleKpiMap = {
    [ROLES.HOMEOWNER]: [
      {
        id: 'plot-size',
        title: 'Target Plot & Location',
        value: '5 Marla',
        unit: '1,125 sq ft',
        trend: 'CDA / LDA Zone',
        subtext: 'Double-Story Approved (G+1)',
        icon: Home,
        accentColor: 'blue',
        badge: 'Islamabad / RWP',
        progress: 85
      },
      {
        id: 'generations',
        title: 'House Layouts Explored',
        value: '6',
        unit: 'Designs',
        trend: '+2 variations',
        subtext: '3D Walkthrough & 2D CAD Ready',
        icon: Sparkles,
        accentColor: 'indigo',
        badge: 'Architext AI',
        progress: 60
      },
      {
        id: 'cost-estimate',
        title: 'Est. Construction Cost',
        value: '₨ 7.85M',
        unit: 'Total Budget',
        trend: '₨ 4,850/sqft',
        subtext: 'A-Grade Finished Turnkey Villa',
        icon: Calculator,
        accentColor: 'emerald',
        badge: 'Live Market Rate',
        progress: 92
      },
      {
        id: 'bylaws',
        title: 'Society Bylaw Safety',
        value: '100%',
        unit: 'Compliant',
        trend: 'Zero Violations',
        subtext: 'Front 5ft, Rear 3ft Setbacks OK',
        icon: CheckCircle2,
        accentColor: 'violet',
        badge: 'CDA / LDA Verified',
        progress: 100
      }
    ],
    [ROLES.ARCHITECT]: [
      {
        id: 'projects',
        title: 'Active Studio Projects',
        value: '28',
        unit: 'BIM Projects',
        trend: '+4 this month',
        subtext: '3 Pending Client Reviews',
        icon: FolderKanban,
        accentColor: 'blue',
        badge: 'Active CAD',
        progress: 78
      },
      {
        id: 'generations',
        title: 'AI Floor Plans Synthesized',
        value: '184',
        unit: 'Syntheses',
        trend: '+18.4% vs last week',
        subtext: '98.2% Spatial Feasibility',
        icon: Sparkles,
        accentColor: 'indigo',
        badge: 'Architext Engine',
        progress: 94
      },
      {
        id: 'templates',
        title: 'BIM & CAD Blueprints',
        value: '42',
        unit: 'Blueprints',
        trend: '+6 added',
        subtext: 'Revit, IFC & DWG Export Ready',
        icon: Layers,
        accentColor: 'emerald',
        badge: 'BIM LOD-300',
        progress: 82
      },
      {
        id: 'usage-hours',
        title: 'Spatial GPU Compute',
        value: '96.4',
        unit: 'Hrs',
        trend: '+12.5 hrs active',
        subtext: 'Neural Vector GPU Cluster Active',
        icon: Cpu,
        accentColor: 'violet',
        badge: 'Compute v2',
        progress: 88
      }
    ],
    [ROLES.CONSTRUCTION_PRO]: [
      {
        id: 'steel-rate',
        title: 'Steel 60-Grade Rate',
        value: '₨ 264',
        unit: 'per kg',
        trend: '+₨ 3/kg this week',
        subtext: 'Mughal / Amreli / AFCO Prime',
        icon: HardDrive,
        accentColor: 'blue',
        badge: 'Live Market',
        progress: 74
      },
      {
        id: 'cement-rate',
        title: 'Grade-53 Cement Rate',
        value: '₨ 1,320',
        unit: 'per bag',
        trend: 'Stable in LHR/ISB',
        subtext: 'Bestway / Fauji / Maple Leaf',
        icon: Layers,
        accentColor: 'indigo',
        badge: 'OPC / SRC Synced',
        progress: 85
      },
      {
        id: 'sites',
        title: 'Active Construction Sites',
        value: '6',
        unit: 'Sites Active',
        trend: '2 Slab Pours Scheduled',
        subtext: 'Daily Engineering Log Verified',
        icon: FolderKanban,
        accentColor: 'emerald',
        badge: 'On Schedule',
        progress: 90
      },
      {
        id: 'cost-estimation',
        title: 'Active Material BOQ Total',
        value: '₨ 48.2M',
        unit: 'PKR',
        trend: '₨ 2,950/sqft grey',
        subtext: 'Direct Verified Contractor Rate',
        icon: Calculator,
        accentColor: 'violet',
        badge: 'BOQ Engine',
        progress: 95
      }
    ],
    [ROLES.DESIGNER]: [
      {
        id: 'moodboards',
        title: 'Active Spatial Concepts',
        value: '18',
        unit: 'Rooms Staged',
        trend: '+4 staged this week',
        subtext: 'Living, Kitchen & Master Suites',
        icon: Sparkles,
        accentColor: 'blue',
        badge: '2.5D Studio',
        progress: 80
      },
      {
        id: 'palettes',
        title: 'PBR Material Palettes',
        value: '34',
        unit: 'Curated Sets',
        trend: '+8 curated tiles',
        subtext: 'Italian Porcelain & Oak Wood',
        icon: Layers,
        accentColor: 'indigo',
        badge: 'PBR Library',
        progress: 85
      },
      {
        id: 'approvals',
        title: 'Client Sign-Offs',
        value: '9',
        unit: 'Approved',
        trend: '3 In Client Review',
        subtext: 'High Satisfaction (4.9★)',
        icon: CheckCircle2,
        accentColor: 'emerald',
        badge: 'Client Portal',
        progress: 92
      },
      {
        id: 'interior-budget',
        title: 'Finishing Material Budget',
        value: '₨ 4.2M',
        unit: 'PKR',
        trend: '₨ 1,850/sqft interior',
        subtext: 'Lighting, Joinery & Sanitary',
        icon: Calculator,
        accentColor: 'violet',
        badge: 'Finishing BOQ',
        progress: 70
      }
    ],
    [ROLES.REAL_ESTATE_DEV]: [
      {
        id: 'land',
        title: 'Commercial Land Portfolio',
        value: '140',
        unit: 'Kanals',
        trend: '3 Master Sectors',
        subtext: 'Islamabad / Rawalpindi Zone',
        icon: FolderKanban,
        accentColor: 'blue',
        badge: 'Master Planning',
        progress: 90
      },
      {
        id: 'units',
        title: 'Planned Housing Units',
        value: '84',
        unit: 'Plots',
        trend: '5M, 10M & 1K mix',
        subtext: 'High-Density Spatial Enclave',
        icon: Layers,
        accentColor: 'indigo',
        badge: 'Plot Yield',
        progress: 82
      },
      {
        id: 'projected-roi',
        title: 'Projected Net Margin',
        value: '34.2%',
        unit: 'Projected ROI',
        trend: '+2.4% vs benchmark',
        subtext: 'Optimized Road & Green Ratios',
        icon: TrendingUp,
        accentColor: 'emerald',
        badge: 'Yield Engine',
        progress: 96
      },
      {
        id: 'feasibility',
        title: 'Commercial Feasibilities',
        value: '₨ 1.2B',
        unit: 'Gross GDV',
        trend: 'CDA Planning Approved',
        subtext: 'High-Rise Mixed-Use Podium',
        icon: Building2,
        accentColor: 'violet',
        badge: 'Bank Feasibility',
        progress: 88
      }
    ],
    [ROLES.SYSTEM_ADMIN]: [
      {
        id: 'vector-indices',
        title: 'ChromaDB Spatial Vectors',
        value: '14,280',
        unit: 'Embeddings',
        trend: '12.4ms query latency',
        subtext: 'All society bylaws indexed',
        icon: HardDrive,
        accentColor: 'blue',
        badge: 'Vector DB',
        progress: 98
      },
      {
        id: 'api-uptime',
        title: 'System Uptime SLA',
        value: '99.98%',
        unit: 'Last 90 Days',
        trend: 'Zero downtime incidents',
        subtext: 'High availability clusters',
        icon: ShieldCheck,
        accentColor: 'indigo',
        badge: 'Multi-AZ',
        progress: 100
      },
      {
        id: 'syntheses-admin',
        title: 'Throughput Volume',
        value: '4,850',
        unit: 'Calls/Day',
        trend: 'Zero dropped requests',
        subtext: 'FastAPI + Uvicorn Cluster',
        icon: Zap,
        accentColor: 'emerald',
        badge: 'High Scale',
        progress: 86
      },
      {
        id: 'storage',
        title: 'Cloud Vector Storage',
        value: '2.4',
        unit: 'TB Stored',
        trend: '+120 GB this month',
        subtext: 'Encrypted CAD & 3D Meshes',
        icon: Cpu,
        accentColor: 'violet',
        badge: 'AWS S3 / Supa',
        progress: 75
      }
    ]
  };

  const kpiData = roleKpiMap[userRole] || roleKpiMap[ROLES.HOMEOWNER];

  const colorVariants = {
    blue: {
      borderHover: 'hover:border-blue-400',
      shadowHover: 'hover:shadow-blue-500/10',
      iconBg: 'bg-blue-50 text-blue-600 border border-blue-100',
      badgeBg: 'bg-blue-50 text-blue-700 border-blue-200',
      progressBar: 'bg-blue-600',
      glow: 'group-hover:bg-blue-500/5'
    },
    indigo: {
      borderHover: 'hover:border-indigo-400',
      shadowHover: 'hover:shadow-indigo-500/10',
      iconBg: 'bg-indigo-50 text-indigo-600 border border-indigo-100',
      badgeBg: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      progressBar: 'bg-indigo-600',
      glow: 'group-hover:bg-indigo-500/5'
    },
    emerald: {
      borderHover: 'hover:border-emerald-400',
      shadowHover: 'hover:shadow-emerald-500/10',
      iconBg: 'bg-emerald-50 text-emerald-600 border border-emerald-100',
      badgeBg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      progressBar: 'bg-emerald-600',
      glow: 'group-hover:bg-emerald-500/5'
    },
    violet: {
      borderHover: 'hover:border-purple-400',
      shadowHover: 'hover:shadow-purple-500/10',
      iconBg: 'bg-purple-50 text-purple-600 border border-purple-100',
      badgeBg: 'bg-purple-50 text-purple-700 border-purple-200',
      progressBar: 'bg-purple-600',
      glow: 'group-hover:bg-purple-500/5'
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
      {kpiData.map((kpi) => {
        const Icon = kpi.icon;
        const style = colorVariants[kpi.accentColor] || colorVariants.blue;

        return (
          <div
            key={kpi.id}
            onClick={() => onSelectKpi && onSelectKpi(kpi.id)}
            className={`relative p-5 md:p-6 bg-white border border-slate-200/90 rounded-2xl shadow-xs transition-all duration-300 hover:-translate-y-1 hover:shadow-lg cursor-pointer group flex flex-col justify-between overflow-hidden ${style.borderHover} ${style.shadowHover}`}
          >
            {/* Subtle background glow on hover */}
            <div className={`absolute inset-0 transition-colors duration-300 pointer-events-none ${style.glow}`} />

            {/* Top row: Title and Icon */}
            <div className="relative flex items-start justify-between gap-3">
              <div className="space-y-1 min-w-0 flex-1">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-500 truncate block">
                  {kpi.title}
                </span>

                <div className="flex items-baseline gap-2 pt-1 flex-wrap">
                  <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {kpi.value}
                  </h3>
                  <span className="text-xs font-semibold text-slate-400">
                    {kpi.unit}
                  </span>
                </div>
              </div>

              <div className={`w-11 h-11 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110 shrink-0 shadow-2xs ${style.iconBg}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>

            {/* Middle: Subtext description */}
            <p className="relative text-xs text-slate-500 font-medium mt-3 mb-4 line-clamp-1">
              {kpi.subtext}
            </p>

            {/* Progress bar visual indicator */}
            <div className="relative w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-3.5">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${style.progressBar}`}
                style={{ width: `${kpi.progress || 80}%` }}
              />
            </div>

            {/* Bottom Row: Trend and Badge (clean separation, no clipping) */}
            <div className="relative pt-3 border-t border-slate-100 flex items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-1.5 text-emerald-600 font-bold min-w-0">
                <TrendingUp className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate text-[11px]">{kpi.trend}</span>
              </div>

              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border shrink-0 ${style.badgeBg}`}>
                {kpi.badge}
              </span>
            </div>

            {/* Floating arrow affordance on hover */}
            <ArrowUpRight className="absolute top-4 right-4 w-4 h-4 text-slate-300 opacity-0 group-hover:opacity-100 group-hover:text-slate-600 transition-all duration-200 pointer-events-none" />
          </div>
        );
      })}
    </div>
  );
}
