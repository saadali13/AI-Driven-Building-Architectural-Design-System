import React from 'react';
import { Link } from 'react-router-dom';
import {
  PlusCircle,
  FolderKanban,
  Calculator,
  LayoutGrid,
  Sparkles,
  ArrowRight,
  Clock,
  CheckCircle2,
  Building,
  HardHat,
  FileSpreadsheet,
  FileSearch,
  ShieldCheck,
  Users,
  Activity,
  Layers,
  ChevronRight,
  Maximize2,
  Edit3,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useProjects } from '../../context/ProjectContext';
import { formatPKR } from '../../services/costEstimatorService';

export const DashboardPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { projects, templates, costEstimates, auditLogs } = useProjects();

  const role = currentUser?.role || 'customer';

  // ==========================================
  // HOMEOWNER DASHBOARD VIEW
  // ==========================================
  if (role === 'customer') {
    const totalProjects = projects.length;
    const inProgress = projects.filter((p) => p.status === 'draft' || p.status === 'generating' || p.status === 'ready_for_review').length;
    const completed = projects.filter((p) => p.status === 'completed').length;
    const latestEstimate = costEstimates[0];
    const recentProjects = projects.slice(0, 3);
    const suggestedTemplates = templates.slice(0, 2);

    return (
      <div className="space-y-8">
        {/* Welcome Section */}
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xs">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE]">
              <Sparkles className="h-3.5 w-3.5 text-[#B86F50]" />
              <span>Residential Architectural Studio</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading tracking-tight">
              Welcome back, {currentUser?.name || 'Homeowner'}
            </h1>
            <p className="text-sm text-[#68736C] max-w-xl leading-relaxed">
              Design your dream home with intelligent Pakistani plot blueprints (5 Marla to 1 Kanal), compliant with CDA/DHA setbacks, and real-time construction BOQ estimates.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Link
              to="/app/designs/new"
              className="px-5 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2 transition-all hover:-translate-y-0.5"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Create New Design</span>
            </Link>
            <Link
              to="/app/cost-estimation"
              className="px-4 py-3 rounded-xl bg-white hover:bg-[#F7F7F2] border border-[#E2E7E1] text-[#202923] text-xs font-semibold transition-colors flex items-center gap-2"
            >
              <Calculator className="h-4 w-4 text-[#23483D]" />
              <span>Calculate BOQ</span>
            </Link>
          </div>
        </div>

        {/* 4 High-Value Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Total Designs</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">{totalProjects}</span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <FolderKanban className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#23483D] font-medium">Pakistani Residential Plots</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">In Progress</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#B86F50] font-heading">{inProgress}</span>
              <div className="p-2 rounded-xl bg-[#FDF3EB] text-[#B86F50]">
                <Clock className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#68736C]">Pending review & revisions</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Completed Plans</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">{completed}</span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <CheckCircle2 className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#23483D] font-medium">CAD & BOQ Ready</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Latest BOQ Estimate</span>
            <div className="flex items-center justify-between">
              <span className="text-lg sm:text-xl font-bold text-[#23483D] font-heading truncate">
                {latestEstimate ? formatPKR(latestEstimate.totalEstimatedCostPKR) : 'PKR 1.25 Cr'}
              </span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <Calculator className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#68736C]">October 2026 Index</p>
          </div>
        </div>

        {/* Recent Projects Gallery */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-[#202923] font-heading">Recent Architectural Projects</h2>
              <p className="text-xs text-[#68736C]">Continue working on your saved Pakistani house plans</p>
            </div>
            <Link
              to="/app/designs"
              className="text-xs font-semibold text-[#23483D] hover:underline flex items-center gap-1"
            >
              <span>View All ({projects.length})</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {recentProjects.map((p) => {
              const alt = p.designAlternatives?.[0];
              return (
                <div
                  key={p.id}
                  className="bg-white border border-[#E2E7E1] hover:border-[#23483D] rounded-2xl p-5 space-y-4 shadow-xs transition-all hover:shadow-md flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-[10px] font-mono font-semibold px-2.5 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] border border-[#DCE7DE] uppercase">
                        {p.plotPreset.replace('_', ' ')}
                      </span>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        p.status === 'completed'
                          ? 'bg-[#EEF4F0] text-[#15803D]'
                          : 'bg-[#FDF3EB] text-[#B86F50]'
                      }`}>
                        {p.status.replace('_', ' ')}
                      </span>
                    </div>

                    <div>
                      <h3 className="font-bold text-[#202923] text-sm group-hover:text-[#23483D] line-clamp-1">
                        {p.title}
                      </h3>
                      <p className="text-xs text-[#68736C] mt-0.5">
                        {p.plotWidthFt} × {p.plotLengthFt} ft • {p.plotAreaSqFt} sq ft • {p.style}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs py-2 border-y border-[#E2E7E1] text-[#68736C]">
                      <div>
                        <span className="text-[10px] uppercase font-semibold text-[#68736C]/70">Bedrooms</span>
                        <p className="font-semibold text-[#202923]">{p.bedrooms} Beds, {p.bathrooms} Baths</p>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-semibold text-[#68736C]/70">Est. Budget</span>
                        <p className="font-semibold text-[#23483D]">{formatPKR(alt?.estimatedCostPKR || p.budgetMinPKR)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="pt-1 flex items-center justify-between gap-2">
                    <span className="text-[11px] text-[#68736C]">Updated {p.updatedAt}</span>
                    <Link
                      to={`/app/designs/${p.id}`}
                      className="px-3.5 py-1.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold flex items-center gap-1 transition-colors"
                    >
                      <span>Open Studio</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Suggested Templates Preview */}
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[#202923] font-heading">Popular Master Templates</h2>
              <p className="text-xs text-[#68736C]">Engineered residential blueprints ready for 1-click customization</p>
            </div>
            <Link to="/app/templates" className="text-xs font-semibold text-[#23483D] hover:underline flex items-center gap-1">
              <span>Explore All Templates</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggestedTemplates.map((t) => (
              <div
                key={t.id}
                className="p-4 rounded-xl border border-[#E2E7E1] hover:border-[#23483D] bg-[#F7F7F2] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#EEF4F0] text-[#23483D]">
                      {t.plotDimensions}
                    </span>
                    <span className="text-xs font-semibold text-[#202923]">{t.name}</span>
                  </div>
                  <p className="text-xs text-[#68736C] line-clamp-1">{t.description}</p>
                  <p className="text-xs font-semibold text-[#23483D]">{formatPKR(t.budgetPKR)} benchmark</p>
                </div>

                <Link
                  to={`/app/designs/new?templateId=${t.id}`}
                  className="px-4 py-2 rounded-xl bg-white border border-[#E2E7E1] hover:bg-[#23483D] hover:text-white text-xs font-semibold text-[#202923] transition-colors shrink-0"
                >
                  Use Template
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // PCATP ARCHITECT DASHBOARD VIEW
  // ==========================================
  if (role === 'architect') {
    return (
      <div className="space-y-8">
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xs">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE]">
              <HardHat className="h-3.5 w-3.5 text-[#23483D]" />
              <span>PCATP Licensed Architect Portal</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading tracking-tight">
              Architect Studio: {currentUser?.name}
            </h1>
            <p className="text-sm text-[#68736C] max-w-xl">
              Audit AI-generated floor plans, inspect CDA/DHA setback clearances, record technical redline annotations, and approve client submissions.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link
              to="/app/architect/reviews"
              className="px-5 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2 transition-colors"
            >
              <FileSearch className="h-4 w-4" />
              <span>Open Review Queue</span>
            </Link>
          </div>
        </div>

        {/* Architect KPI Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Assigned Projects</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">{projects.length}</span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <FolderKanban className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#23483D]">Client designs</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Pending Reviews</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#B86F50] font-heading">
                {projects.filter((p) => p.status === 'ready_for_review').length || 2}
              </span>
              <div className="p-2 rounded-xl bg-[#FDF3EB] text-[#B86F50]">
                <FileSearch className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#68736C]">Awaiting redline markup</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Approved Submissions</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">
                {projects.filter((p) => p.status === 'completed').length || 1}
              </span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <CheckCircle2 className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#23483D]">Bylaws verified</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Audit Reports</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">4</span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <Activity className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#68736C]">Compliance sheets</p>
          </div>
        </div>

        {/* Pending Reviews Queue Table */}
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[#202923] font-heading">Client Blueprint Review Queue</h2>
            <Link to="/app/architect/reviews" className="text-xs font-semibold text-[#23483D] hover:underline">
              Inspect All Plans
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                  <th className="pb-3 font-semibold">Project Title</th>
                  <th className="pb-3 font-semibold">Plot Size</th>
                  <th className="pb-3 font-semibold">Client</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E7E1] text-[#202923]">
                {projects.map((p) => (
                  <tr key={p.id} className="hover:bg-[#F7F7F2]">
                    <td className="py-3 font-semibold text-[#202923]">{p.title}</td>
                    <td className="py-3 font-mono text-[#23483D]">{p.plotWidthFt} × {p.plotLengthFt} ft</td>
                    <td className="py-3 text-[#68736C]">{p.ownerName}</td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#FDF3EB] text-[#B86F50]">
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <Link
                        to="/app/architect/reviews"
                        className="px-3 py-1.5 rounded-lg bg-[#23483D] text-white text-[11px] font-semibold hover:bg-[#1A372E]"
                      >
                        Redline Audit
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // SYSTEM ADMINISTRATOR DASHBOARD VIEW
  // ==========================================
  if (role === 'admin') {
    return (
      <div className="space-y-8">
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xs">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F4EFF7] text-[#5C2D6D] text-xs font-semibold border border-[#E0D0E7]">
              <ShieldCheck className="h-3.5 w-3.5 text-[#5C2D6D]" />
              <span>Platform Administration & Operations</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading tracking-tight">
              System Admin Console
            </h1>
            <p className="text-sm text-[#68736C] max-w-xl">
              Moderate user accounts, calibrate regional construction material rates, manage design templates, and review platform security audit trails.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link
              to="/app/admin/users"
              className="px-5 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2 transition-colors"
            >
              <Users className="h-4 w-4" />
              <span>User Directory</span>
            </Link>
          </div>
        </div>

        {/* Admin Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Registered Users</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">142</span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <Users className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#23483D]">4 active roles</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Platform Projects</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">{projects.length}</span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <FolderKanban className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#68736C]">In database</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Active Templates</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">{templates.length}</span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <LayoutGrid className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#23483D]">CMS Published</p>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
            <span className="text-xs text-[#68736C] font-medium">Security Events</span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-[#202923] font-heading">{auditLogs.length}</span>
              <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
                <Activity className="h-5 w-5" />
              </div>
            </div>
            <p className="text-[11px] text-[#68736C]">Audit trail logs</p>
          </div>
        </div>

        {/* Administration Action Shortcuts */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/app/admin/cost-settings"
            className="p-5 rounded-2xl bg-white border border-[#E2E7E1] hover:border-[#23483D] shadow-xs space-y-2 transition-all hover:shadow-md"
          >
            <div className="p-2.5 rounded-xl bg-[#EEF4F0] text-[#23483D] w-fit">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-[#202923] text-sm">Material Rate Management</h3>
            <p className="text-xs text-[#68736C]">Calibrate market rates for cement, grade-60 steel rebar, and bricks across Pakistani cities.</p>
          </Link>

          <Link
            to="/app/admin/templates"
            className="p-5 rounded-2xl bg-white border border-[#E2E7E1] hover:border-[#23483D] shadow-xs space-y-2 transition-all hover:shadow-md"
          >
            <div className="p-2.5 rounded-xl bg-[#EEF4F0] text-[#23483D] w-fit">
              <LayoutGrid className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-[#202923] text-sm">Template Library CMS</h3>
            <p className="text-xs text-[#68736C]">Publish, archive, and update standard 5M, 7M, 10M, and 1K residential blueprints.</p>
          </Link>

          <Link
            to="/app/admin/audit-logs"
            className="p-5 rounded-2xl bg-white border border-[#E2E7E1] hover:border-[#23483D] shadow-xs space-y-2 transition-all hover:shadow-md"
          >
            <div className="p-2.5 rounded-xl bg-[#EEF4F0] text-[#23483D] w-fit">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-[#202923] text-sm">Security & Audit Trail</h3>
            <p className="text-xs text-[#68736C]">Inspect real-time logs of design creations, rate edits, and user role elevation events.</p>
          </Link>
        </div>
      </div>
    );
  }

  // ==========================================
  // BUILDER / CONTRACTOR DASHBOARD VIEW
  // ==========================================
  return (
    <div className="space-y-8">
      <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xs">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FDF3EB] text-[#8C4A1A] text-xs font-semibold border border-[#F2DAC7]">
            <Calculator className="h-3.5 w-3.5 text-[#8C4A1A]" />
            <span>Builder & Contractor BOQ Workspace</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading tracking-tight">
            Contractor Hub: {currentUser?.name}
          </h1>
          <p className="text-sm text-[#68736C] max-w-xl">
            Execute detailed Bill of Quantities (BOQ), monitor real-time material price fluctuations, and generate itemized client estimates.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link
            to="/app/cost-estimation"
            className="px-5 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2 transition-colors"
          >
            <Calculator className="h-4 w-4" />
            <span>Run BOQ Estimator</span>
          </Link>
        </div>
      </div>

      {/* Contractor KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
          <span className="text-xs text-[#68736C] font-medium">Assigned Cost Jobs</span>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-[#202923] font-heading">{projects.length}</span>
            <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
              <FolderKanban className="h-5 w-5" />
            </div>
          </div>
          <p className="text-[11px] text-[#23483D]">Estimation projects</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
          <span className="text-xs text-[#68736C] font-medium">Market Rate Index</span>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-[#23483D] font-heading">16</span>
            <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
          </div>
          <p className="text-[11px] text-[#68736C]">Materials tracked</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
          <span className="text-xs text-[#68736C] font-medium">Saved Estimates</span>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-[#202923] font-heading">{costEstimates.length}</span>
            <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
              <Calculator className="h-5 w-5" />
            </div>
          </div>
          <p className="text-[11px] text-[#23483D]">Ready for print</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
          <span className="text-xs text-[#68736C] font-medium">Regional Factor</span>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-[#202923] font-heading">1.03×</span>
            <div className="p-2 rounded-xl bg-[#EEF4F0] text-[#23483D]">
              <Building className="h-5 w-5" />
            </div>
          </div>
          <p className="text-[11px] text-[#68736C]">Islamabad / RWP</p>
        </div>
      </div>
    </div>
  );
};
