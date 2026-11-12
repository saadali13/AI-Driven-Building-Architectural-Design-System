import React from 'react';
import { FileSpreadsheet, Download, Printer, CheckCircle2, TrendingUp } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { formatPKR } from '../../services/costEstimatorService';

export const ArchitectReportsPage: React.FC = () => {
  const { projects, costEstimates } = useProjects();

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#202923] font-heading">
            Architectural Feasibility & BOQ Reports
          </h1>
          <p className="text-xs text-[#68736C] mt-1">
            Consolidated project metrics, covered area calculations, and construction estimates.
          </p>
        </div>

        <button
          onClick={() => window.print()}
          className="px-3.5 py-1.5 rounded-xl border border-[#E2E7E1] bg-white hover:bg-[#F7F7F2] text-[#202923] text-xs font-semibold flex items-center gap-1.5 self-start sm:self-auto transition-colors shadow-xs"
        >
          <Printer className="h-3.5 w-3.5 text-[#23483D]" />
          <span>Print Summary</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
        <div className="bg-white border border-[#E2E7E1] rounded-3xl p-5 space-y-2 shadow-xs">
          <span className="text-[#68736C] text-[11px]">Total Managed Projects</span>
          <p className="text-2xl font-bold text-[#202923] font-heading">{projects.length}</p>
          <p className="text-[#23483D] font-medium">Covering {projects.reduce((acc, p) => acc + p.plotAreaSqFt, 0).toLocaleString()} sq ft plot area</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-3xl p-5 space-y-2 shadow-xs">
          <span className="text-[#68736C] text-[11px]">Cumulative Construction Value</span>
          <p className="text-2xl font-bold text-[#23483D] font-heading">
            {formatPKR(costEstimates.reduce((acc, c) => acc + c.totalEstimatedCostPKR, 0))}
          </p>
          <p className="text-[#68736C]">Based on current market rates</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-3xl p-5 space-y-2 shadow-xs">
          <span className="text-[#68736C] text-[11px]">Average Cost Per Sq Ft</span>
          <p className="text-2xl font-bold text-[#202923] font-heading">PKR 7,780</p>
          <p className="text-[#68736C]">DHA & Bahria Town standards</p>
        </div>
      </div>

      {/* Projects Table */}
      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 text-xs shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-[#202923] font-heading">Feasibility Summary Table</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="pb-3 font-medium">Project</th>
                <th className="pb-3 font-medium">Plot Dims</th>
                <th className="pb-3 font-medium">Storey</th>
                <th className="pb-3 font-medium">Beds / Baths</th>
                <th className="pb-3 font-medium">Covered Area</th>
                <th className="pb-3 font-medium text-right">Est. Construction</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#68736C]">
              {projects.map((p) => (
                <tr key={p.id} className="hover:bg-[#F7F7F2]/60 transition-colors">
                  <td className="py-3 font-semibold text-[#202923]">{p.title}</td>
                  <td className="py-3 font-mono text-[#23483D]">{p.plotWidthFt} &times; {p.plotLengthFt} ft</td>
                  <td className="py-3">{p.floors} Storey</td>
                  <td className="py-3">{p.bedrooms} Beds / {p.bathrooms} Baths</td>
                  <td className="py-3 font-mono">{Math.round(p.plotAreaSqFt * (p.floors === 1 ? 0.75 : 1.55))} sq ft</td>
                  <td className="py-3 text-right font-mono font-bold text-[#202923]">
                    {formatPKR(p.designAlternatives[0]?.estimatedCostPKR || 25000000)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
