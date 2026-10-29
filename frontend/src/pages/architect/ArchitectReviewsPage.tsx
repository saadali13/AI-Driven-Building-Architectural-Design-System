import React, { useState } from 'react';
import {
  FileSearch,
  CheckCircle2,
  AlertTriangle,
  Compass,
  MessageSquare,
  ShieldCheck,
  Send,
  Building,
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { FloorPlanViewer } from '../../components/architectural/FloorPlanViewer';

export const ArchitectReviewsPage: React.FC = () => {
  const { projects } = useProjects();
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projects[0]?.id || '');
  const [annotation, setAnnotation] = useState('');
  const [annotationsList, setAnnotationsList] = useState<string[]>([
    'Verified: 7.5 ft front setback aligns with DHA Phase 2 Town Planning regulations.',
    'Recommendation: Relocate kitchen dirty wash basin 2 feet north to improve natural cross-breeze from rear lightwell.',
    'Municipal Note: Ensure rainwater harvesting recharge well is marked on boundary wall details.',
  ]);

  const activeProject = projects.find((p) => p.id === selectedProjectId) || projects[0];

  const handleAddAnnotation = (e: React.FormEvent) => {
    e.preventDefault();
    if (annotation.trim()) {
      setAnnotationsList([annotation.trim(), ...annotationsList]);
      setAnnotation('');
    }
  };

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-[#E2E7E1] pb-5">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE] mb-2">
          <FileSearch className="h-3.5 w-3.5 text-[#23483D]" />
          <span>PCATP Technical Redline Audit</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
          Floor Plan Architectural Review Queue
        </h1>
        <p className="text-xs text-[#68736C] mt-1">
          Review spatial layout integrity, door clearance swing radii, and municipal setback compliance.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Floor plan viewer */}
        <div className="lg:col-span-8 space-y-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-4 shadow-xs flex items-center justify-between text-xs">
            <span className="font-semibold text-[#202923]">Inspecting Plan:</span>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title} ({p.plotPreset.replace('_', ' ')} • {p.plotWidthFt}×{p.plotLengthFt}')
                </option>
              ))}
            </select>
          </div>

          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs">
            <FloorPlanViewer
              type={activeProject?.designAlternatives?.[0]?.floorPlanSvgType || '10_marla_luxury'}
              rooms={activeProject?.designAlternatives?.[0]?.rooms || []}
            />
          </div>
        </div>

        {/* Annotations & Review Column */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-4">
            <h3 className="font-bold text-xs uppercase tracking-wider text-[#68736C]">
              Add Technical Redline Note
            </h3>

            <form onSubmit={handleAddAnnotation} className="space-y-3">
              <textarea
                rows={3}
                value={annotation}
                onChange={(e) => setAnnotation(e.target.value)}
                placeholder="Add architectural observation, structural clearance note, or setback remark..."
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl p-3 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
              <button
                type="submit"
                className="w-full py-2.5 bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 shadow-xs"
              >
                <Send className="h-3.5 w-3.5" />
                <span>Record Architect Annotation</span>
              </button>
            </form>
          </div>

          {/* Existing Review Log */}
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-[#68736C]">
              Recorded Annotations ({annotationsList.length})
            </h3>

            <div className="space-y-2.5 max-h-72 overflow-y-auto">
              {annotationsList.map((note, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] text-xs space-y-1">
                  <div className="flex items-center justify-between text-[10px] text-[#68736C]">
                    <span className="font-bold text-[#23483D]">PCATP Architect #A-4892</span>
                    <span>Just now</span>
                  </div>
                  <p className="text-[#202923]">{note}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
