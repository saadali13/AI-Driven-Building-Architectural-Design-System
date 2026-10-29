import React, { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  GitCompare,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Building,
  Layers,
  Sparkles,
  Info,
  Maximize2,
  ArrowLeft,
  Check,
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { Project } from '../../types';
import { formatPKR } from '../../services/costEstimatorService';
import { FloorPlanViewer } from '../../components/architectural/FloorPlanViewer';

export const CompareDesignsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { projects } = useProjects();

  const p1Param = searchParams.get('p1');
  const p2Param = searchParams.get('p2');

  const [projectAId, setProjectAId] = useState<string>(p1Param || projects[0]?.id || '');
  const [projectBId, setProjectBId] = useState<string>(p2Param || projects[1]?.id || projects[0]?.id || '');

  const projectA = projects.find((p) => p.id === projectAId) || projects[0];
  const projectB = projects.find((p) => p.id === projectBId) || projects[1] || projects[0];

  const altA = projectA?.designAlternatives?.[0] || null;
  const altB = projectB?.designAlternatives?.[0] || null;

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-[#E2E7E1] pb-5">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE] mb-2">
          <GitCompare className="h-3.5 w-3.5" />
          <span>Spatial & Economic Evaluation</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
          Side-by-Side Design Comparison Matrix
        </h1>
        <p className="text-xs text-[#68736C] mt-1">
          Objectively evaluate plot dimensions, covered areas, cultural privacy zoning, and preliminary construction budgets.
        </p>
      </div>

      {/* Selectors Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs text-xs">
        <div>
          <label className="block text-[#202923] font-bold mb-1.5">Select First Project (Option A)</label>
          <select
            value={projectAId}
            onChange={(e) => setProjectAId(e.target.value)}
            className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title} ({p.plotPreset.replace('_', ' ')} • {p.plotWidthFt}×{p.plotLengthFt}')
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[#202923] font-bold mb-1.5">Select Second Project (Option B)</label>
          <select
            value={projectBId}
            onChange={(e) => setProjectBId(e.target.value)}
            className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title} ({p.plotPreset.replace('_', ' ')} • {p.plotWidthFt}×{p.plotLengthFt}')
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Visual Blueprint Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#EEF4F0] text-[#23483D]">
                OPTION A
              </span>
              <h3 className="font-bold text-sm text-[#202923] mt-1">{projectA?.title}</h3>
            </div>
            <Link to={`/app/designs/${projectA?.id}`} className="text-xs font-semibold text-[#23483D] hover:underline">
              Open Studio →
            </Link>
          </div>
          <FloorPlanViewer
            type={altA?.floorPlanSvgType || '10_marla_luxury'}
            rooms={altA?.rooms || []}
          />
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#FDF3EB] text-[#B86F50]">
                OPTION B
              </span>
              <h3 className="font-bold text-sm text-[#202923] mt-1">{projectB?.title}</h3>
            </div>
            <Link to={`/app/designs/${projectB?.id}`} className="text-xs font-semibold text-[#23483D] hover:underline">
              Open Studio →
            </Link>
          </div>
          <FloorPlanViewer
            type={altB?.floorPlanSvgType || '10_marla_luxury'}
            rooms={altB?.rooms || []}
          />
        </div>
      </div>

      {/* Side-by-Side Architectural Metric Table */}
      <div className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden shadow-xs">
        <div className="p-4 bg-[#F7F7F2] border-b border-[#E2E7E1] font-bold text-xs text-[#202923]">
          Detailed Specification Diff
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="p-3.5 font-semibold w-1/3">Architectural Parameter</th>
                <th className="p-3.5 font-semibold text-[#23483D] w-1/3">{projectA?.title}</th>
                <th className="p-3.5 font-semibold text-[#B86F50] w-1/3">{projectB?.title}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#202923]">
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium text-[#68736C]">Plot Dimensions</td>
                <td className="p-3.5 font-mono font-bold">{projectA?.plotWidthFt} × {projectA?.plotLengthFt} ft</td>
                <td className="p-3.5 font-mono font-bold">{projectB?.plotWidthFt} × {projectB?.plotLengthFt} ft</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium text-[#68736C]">Total Plot Area</td>
                <td className="p-3.5">{projectA?.plotAreaSqFt} sq ft ({projectA?.plotAreaMarla} Marla)</td>
                <td className="p-3.5">{projectB?.plotAreaSqFt} sq ft ({projectB?.plotAreaMarla} Marla)</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium text-[#68736C]">Storeys & Covered Area</td>
                <td className="p-3.5">{projectA?.floors} Storeys • ~{altA?.coveredAreaSqFt || 2100} sq ft</td>
                <td className="p-3.5">{projectB?.floors} Storeys • ~{altB?.coveredAreaSqFt || 2400} sq ft</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium text-[#68736C]">Bedrooms / Bathrooms</td>
                <td className="p-3.5 font-bold">{projectA?.bedrooms} Beds, {projectA?.bathrooms} Baths</td>
                <td className="p-3.5 font-bold">{projectB?.bedrooms} Beds, {projectB?.bathrooms} Baths</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium text-[#68736C]">Car Porch Capacity</td>
                <td className="p-3.5">{projectA?.pakistaniSpecs?.carPorchCapacity || 1} Vehicle(s)</td>
                <td className="p-3.5">{projectB?.pakistaniSpecs?.carPorchCapacity || 2} Vehicle(s)</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium text-[#68736C]">Architectural Style</td>
                <td className="p-3.5">{projectA?.style}</td>
                <td className="p-3.5">{projectB?.style}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium text-[#68736C]">Estimated Construction BOQ</td>
                <td className="p-3.5 font-mono font-bold text-[#23483D]">{formatPKR(altA?.estimatedCostPKR || projectA?.budgetMinPKR || 0)}</td>
                <td className="p-3.5 font-mono font-bold text-[#23483D]">{formatPKR(altB?.estimatedCostPKR || projectB?.budgetMinPKR || 0)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
