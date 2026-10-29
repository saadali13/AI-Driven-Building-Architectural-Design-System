import React from 'react';
import { History, FileText, Download, CheckCircle2, ArrowRight } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';

export const ArchitectRevisionsPage: React.FC = () => {
  const { projects } = useProjects();

  const revisions = [
    { id: 'rev_1', project: 'Islamabad DHA Phase 2 - 10 Marla Villa', version: 'v1.2', date: '2026-10-25', author: 'Ar. Ayesha Mansoor', notes: 'Setback verification and water tank relocation.', status: 'approved' },
    { id: 'rev_2', project: 'Islamabad DHA Phase 2 - 10 Marla Villa', version: 'v1.0', date: '2026-10-19', author: 'AI Spatial Synthesis', notes: 'Initial generation from client prompt.', status: 'superseded' },
    { id: 'rev_3', project: 'Lahore Lake City - 5 Marla Smart Home', version: 'v2.0', date: '2026-09-12', author: 'Ar. Ayesha Mansoor', notes: 'Finalized architectural layout for grey structure.', status: 'approved' },
  ];

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5">
        <h1 className="text-2xl font-bold text-[#202923] font-heading">Design Version & Revision History</h1>
        <p className="text-xs text-[#68736C] mt-1">
          Audit trail of architectural revisions, client iterations, and CAD submission packages.
        </p>
      </div>

      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 text-xs shadow-xs space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="pb-3 font-medium">Project Name</th>
                <th className="pb-3 font-medium">Version</th>
                <th className="pb-3 font-medium">Revision Date</th>
                <th className="pb-3 font-medium">Author / Architect</th>
                <th className="pb-3 font-medium">Summary Notes</th>
                <th className="pb-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#68736C]">
              {revisions.map((rev) => (
                <tr key={rev.id} className="hover:bg-[#F7F7F2]/60 transition-colors">
                  <td className="py-3 font-semibold text-[#202923]">{rev.project}</td>
                  <td className="py-3 font-mono text-[#23483D] font-bold">{rev.version}</td>
                  <td className="py-3 text-[#68736C] font-mono">{rev.date}</td>
                  <td className="py-3 text-[#202923]">{rev.author}</td>
                  <td className="py-3 text-[#68736C]">{rev.notes}</td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => alert(`CAD submission package downloaded for ${rev.project} (${rev.version})`)}
                      className="px-3 py-1 bg-white hover:bg-[#F7F7F2] border border-[#E2E7E1] text-[#202923] rounded-lg font-semibold inline-flex items-center gap-1 transition-colors shadow-xs"
                    >
                      <Download className="h-3 w-3 text-[#23483D]" />
                      <span>Download</span>
                    </button>
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
