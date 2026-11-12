import React from 'react';
import { Link } from 'react-router-dom';
import { FolderKanban, Search, ArrowRight, Eye, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { formatPKR } from '../../services/costEstimatorService';

export const ArchitectProjectsPage: React.FC = () => {
  const { projects } = useProjects();

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#202923] font-heading">
            Architectural Project Portfolio
          </h1>
          <p className="text-xs text-[#68736C] mt-1">
            Projects assigned to PCATP architects for compliance review, structural vetting, and redlining.
          </p>
        </div>

        <Link
          to="/app/reviews"
          className="px-4 py-2 bg-[#23483D] hover:bg-[#1a362d] text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 self-start sm:self-auto shadow-xs transition-colors"
        >
          <ShieldCheck className="h-4 w-4" />
          <span>Open Review Workstation</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {projects.map((p) => (
          <div
            key={p.id}
            className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden hover:border-[#23483D]/40 transition-all shadow-xs flex flex-col"
          >
            <div className="p-4 border-b border-[#E2E7E1] bg-[#F7F7F2]/60 flex items-center justify-between">
              <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-[#DCE7DE] text-[#23483D]">
                {p.plotWidthFt} &times; {p.plotLengthFt} ft &bull; {p.floors} Fl
              </span>
              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                {p.status}
              </span>
            </div>

            <div className="p-5 flex-1 space-y-3 text-xs">
              <div>
                <h3 className="font-bold text-[#202923] text-sm">{p.title}</h3>
                <p className="text-[#68736C] text-[11px] mt-1 line-clamp-2">
                  {p.promptText || 'Custom residential floor plan layout.'}
                </p>
              </div>

              <div className="flex items-center gap-3 text-[#68736C] pt-2 border-t border-[#E2E7E1]/60">
                <span>{p.bedrooms} Beds</span>
                <span>&bull;</span>
                <span>{p.bathrooms} Baths</span>
                <span>&bull;</span>
                <span className="font-semibold text-[#202923]">{p.plotAreaSqFt.toLocaleString()} sq ft</span>
              </div>
            </div>

            <div className="p-4 bg-[#F7F7F2]/30 border-t border-[#E2E7E1] flex items-center justify-between text-xs">
              <Link
                to={`/app/designs/${p.id}`}
                className="font-semibold text-[#68736C] hover:text-[#202923] flex items-center gap-1"
              >
                <Eye className="h-3.5 w-3.5" />
                <span>View CAD</span>
              </Link>
              <Link
                to="/app/reviews"
                className="font-semibold text-[#23483D] hover:underline flex items-center gap-1"
              >
                <span>Review & Annotate</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
