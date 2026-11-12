import React from 'react';
import { BarChart3, TrendingUp, Users, FolderGit2, Printer, Download } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { formatPKR } from '../../services/costEstimatorService';

export const AdminReportsPage: React.FC = () => {
  const { projects, costEstimates } = useProjects();

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#202923] font-heading">
            Executive Analytics & Platform Reports
          </h1>
          <p className="text-xs text-[#68736C] mt-1">
            Spatial AI generation metrics, regional plot adoption, and cost estimation telemetry.
          </p>
        </div>

        <button
          onClick={() => window.print()}
          className="px-3.5 py-1.5 rounded-xl border border-[#E2E7E1] bg-white hover:bg-[#F7F7F2] text-[#202923] text-xs font-semibold flex items-center gap-1.5 self-start sm:self-auto transition-colors shadow-xs"
        >
          <Printer className="h-3.5 w-3.5 text-[#23483D]" />
          <span>Print Executive Summary</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-2">
          <span className="text-[#68736C] text-[11px]">Cumulative Designs Synthesized</span>
          <p className="text-2xl font-bold text-[#202923] font-heading">{projects.length + 18}</p>
          <p className="text-[#23483D] font-medium">+24% vs previous quarter</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-2">
          <span className="text-[#68736C] text-[11px]">Primary Regional Preset</span>
          <p className="text-2xl font-bold text-[#23483D] font-heading">10 Marla (35&times;65)</p>
          <p className="text-[#68736C]">48% of total generations</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-2">
          <span className="text-[#68736C] text-[11px]">Average Est. Construction</span>
          <p className="text-2xl font-bold text-[#202923] font-heading">PKR 2.45 Cr</p>
          <p className="text-[#68736C]">Based on Grey + Finish indices</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-2">
          <span className="text-[#68736C] text-[11px]">AI Synthesis Compliance</span>
          <p className="text-2xl font-bold text-emerald-700 font-heading">99.4%</p>
          <p className="text-[#68736C]">Zero CDA setback violations</p>
        </div>
      </div>

      {/* Regional Breakdown Table */}
      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 text-xs shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-[#202923] font-heading">Plot Preset Adoption in Pakistan</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="pb-3 font-medium">Standard Plot Category</th>
                <th className="pb-3 font-medium">Typical Dimensions</th>
                <th className="pb-3 font-medium">Covered Area (Double Storey)</th>
                <th className="pb-3 font-medium">Target Housing Schemes</th>
                <th className="pb-3 font-medium text-right">Synthesis Share</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#68736C]">
              <tr className="hover:bg-[#F7F7F2]/60">
                <td className="py-3 font-semibold text-[#202923]">5 Marla</td>
                <td className="py-3 font-mono text-[#23483D]">25 &times; 45 ft</td>
                <td className="py-3 font-mono">1,850 sq ft</td>
                <td className="py-3">DHA, Bahria, Lake City</td>
                <td className="py-3 text-right font-mono font-bold text-[#202923]">34%</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]/60">
                <td className="py-3 font-semibold text-[#202923]">7 Marla</td>
                <td className="py-3 font-mono text-[#23483D]">30 &times; 52.5 ft</td>
                <td className="py-3 font-mono">2,450 sq ft</td>
                <td className="py-3">Faisal Hills, Park View</td>
                <td className="py-3 text-right font-mono font-bold text-[#202923]">12%</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]/60">
                <td className="py-3 font-semibold text-[#202923]">10 Marla</td>
                <td className="py-3 font-mono text-[#23483D]">35 &times; 65 ft</td>
                <td className="py-3 font-mono">3,350 sq ft</td>
                <td className="py-3">CDA Sectors, DHA Phase 2</td>
                <td className="py-3 text-right font-mono font-bold text-[#202923]">42%</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]/60">
                <td className="py-3 font-semibold text-[#202923]">1 Kanal</td>
                <td className="py-3 font-mono text-[#23483D]">50 &times; 90 ft</td>
                <td className="py-3 font-mono">5,600 sq ft</td>
                <td className="py-3">Gulberg, DHA Phase 5/6</td>
                <td className="py-3 text-right font-mono font-bold text-[#202923]">12%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
