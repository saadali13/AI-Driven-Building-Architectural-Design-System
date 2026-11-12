import React, { useState } from 'react';
import { LayoutGrid, PlusCircle, Trash2, Eye, CheckCircle2 } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { formatPKR } from '../../services/costEstimatorService';

export const TemplateManagementPage: React.FC = () => {
  const { templates } = useProjects();
  const [tplList, setTplList] = useState(templates);

  const togglePublished = (id: string) => {
    setTplList((prev) =>
      prev.map((t) => (t.id === id ? { ...t, published: !t.published } : t))
    );
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#202923] font-heading">Design Template Management (CMS)</h1>
          <p className="text-xs text-[#68736C] mt-1">
            Publish, edit metadata, and configure public architectural blueprint templates.
          </p>
        </div>
      </div>

      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 text-xs shadow-xs space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="pb-3 font-medium">Template Name</th>
                <th className="pb-3 font-medium">Dimensions</th>
                <th className="pb-3 font-medium">Style</th>
                <th className="pb-3 font-medium">Area</th>
                <th className="pb-3 font-medium">Budget Benchmark</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium text-right">Toggle Publication</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#68736C]">
              {tplList.map((t) => (
                <tr key={t.id} className="hover:bg-[#F7F7F2]/60 transition-colors">
                  <td className="py-3 font-semibold text-[#202923]">{t.name}</td>
                  <td className="py-3 font-mono text-[#23483D] font-medium">{t.plotDimensions}</td>
                  <td className="py-3">{t.style}</td>
                  <td className="py-3 font-mono">{t.areaSqFt} sq ft</td>
                  <td className="py-3 font-mono font-bold text-[#202923]">{formatPKR(t.budgetPKR)}</td>
                  <td className="py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        t.published
                          ? 'bg-[#DCE7DE] text-[#23483D]'
                          : 'bg-slate-100 text-[#68736C]'
                      }`}
                    >
                      {t.published ? 'Published' : 'Archived'}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => togglePublished(t.id)}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                        t.published
                          ? 'bg-slate-100 hover:bg-slate-200 text-[#202923]'
                          : 'bg-[#23483D] hover:bg-[#1a362d] text-white'
                      }`}
                    >
                      {t.published ? 'Unpublish' : 'Publish'}
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
