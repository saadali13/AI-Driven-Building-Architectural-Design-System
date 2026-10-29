import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderGit2, Search, ArrowRight, Eye, ShieldCheck, Filter } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { formatPKR } from '../../services/costEstimatorService';

export const AdminProjectsPage: React.FC = () => {
  const { projects } = useProjects();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filtered = projects.filter((p) => {
    if (searchTerm && !p.title.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (statusFilter !== 'all' && p.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#202923] font-heading">
            Platform Project Directory
          </h1>
          <p className="text-xs text-[#68736C] mt-1">
            Global repository of residential blueprints, floor plans, and spatial generation telemetry.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded-lg bg-[#DCE7DE] text-[#23483D]">
            {projects.length} Total Projects
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-[#E2E7E1] shadow-xs">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#68736C]" />
          <input
            type="text"
            placeholder="Search projects by title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl pl-9 pr-3 py-1.5 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-1.5 text-xs text-[#202923]"
          >
            <option value="all">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="review">In Review</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      {/* Projects Table */}
      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 text-xs shadow-xs space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="pb-3 font-medium">Project Name</th>
                <th className="pb-3 font-medium">Plot Dimensions</th>
                <th className="pb-3 font-medium">Floors</th>
                <th className="pb-3 font-medium">Rooms</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Last Modified</th>
                <th className="pb-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#68736C]">
              {filtered.map((p) => (
                <tr key={p.id} className="hover:bg-[#F7F7F2]/60 transition-colors">
                  <td className="py-3 font-semibold text-[#202923]">{p.title}</td>
                  <td className="py-3 font-mono text-[#23483D] font-medium">
                    {p.plotWidthFt} &times; {p.plotLengthFt} ft ({p.plotAreaSqFt} sq ft)
                  </td>
                  <td className="py-3">{p.floors} Storey</td>
                  <td className="py-3">{p.bedrooms} Beds / {p.bathrooms} Baths</td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[#DCE7DE] text-[#23483D]">
                      {p.status}
                    </span>
                  </td>
                  <td className="py-3 font-mono text-[11px]">{p.updatedAt}</td>
                  <td className="py-3 text-right">
                    <Link
                      to={`/app/designs/${p.id}`}
                      className="px-3 py-1 rounded-lg bg-[#23483D] hover:bg-[#1a362d] text-white font-semibold inline-flex items-center gap-1 text-[11px] transition-colors"
                    >
                      <Eye className="h-3 w-3" />
                      <span>Inspect CAD</span>
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
};
