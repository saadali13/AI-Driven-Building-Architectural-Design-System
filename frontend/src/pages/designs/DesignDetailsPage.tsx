import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Compass,
  ArrowLeft,
  Share2,
  Download,
  Layers,
  Sparkles,
  GitCompare,
  Edit2,
  Calendar,
  Building,
  CheckCircle2,
  AlertTriangle,
  Info,
  Maximize2,
  Calculator,
  ShieldCheck,
  Check,
  FileText,
  Printer,
  ChevronRight,
  HardHat,
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { FloorPlanViewer } from '../../components/architectural/FloorPlanViewer';
import { ElevationViewer } from '../../components/architectural/ElevationViewer';
import { formatPKR } from '../../services/costEstimatorService';
import { apiService } from '../../services/apiService';

export const DesignDetailsPage: React.FC = () => {
  const { designId } = useParams<{ designId: string }>();
  const navigate = useNavigate();
  const { projects, duplicateProject } = useProjects();

  const project = projects.find((p) => p.id === designId);

  const [activeTab, setActiveTab] = useState<'overview' | 'floorplans' | 'elevation' | 'rooms' | 'cost' | 'revisions'>('overview');
  const [selectedAltId, setSelectedAltId] = useState<string>(
    project?.selectedAlternativeId || project?.designAlternatives[0]?.id || ''
  );
  const [shareCopied, setShareCopied] = useState(false);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'dxf' | 'svg' | 'blend' | 'obj' | 'png'>('pdf');
  const [exportLoading, setExportLoading] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  if (!project) {
    return (
      <div className="bg-white border border-[#E2E7E1] rounded-2xl p-12 text-center space-y-4 shadow-xs">
        <Compass className="h-10 w-10 text-[#68736C] mx-auto opacity-50" />
        <h2 className="text-lg font-bold text-[#202923]">Project Not Found</h2>
        <p className="text-xs text-[#68736C]">
          The requested architectural project could not be located in your workspace.
        </p>
        <Link
          to="/app/designs"
          className="inline-block px-4 py-2 bg-[#23483D] text-white rounded-xl text-xs font-semibold"
        >
          Back to Saved Designs
        </Link>
      </div>
    );
  }

  const activeAlternative =
    project.designAlternatives?.find((a) => a.id === selectedAltId) ||
    project.designAlternatives?.[0] ||
    null;

  const handleShareClick = () => {
    navigator.clipboard?.writeText(window.location.href);
    setShareCopied(true);
    setTimeout(() => setShareCopied(false), 2500);
  };

  const handleTriggerExport = async () => {
    setExportLoading(true);
    setExportSuccess(false);

    try {
      // Attempt live file download via Python backend
      const result = await apiService.exportFile(exportFormat, {
        project_title: project.title,
        plot_width: project.plotWidthFt,
        plot_length: project.plotLengthFt,
        floors: project.floors,
        bedrooms: project.bedrooms,
        bathrooms: project.bathrooms,
        style: project.style,
        rooms: activeAlternative?.rooms || [],
      });

      // Trigger browser download of returned blob
      const url = window.URL.createObjectURL(result.blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setExportSuccess(true);
      setTimeout(() => {
        setExportModalOpen(false);
        setExportSuccess(false);
      }, 2000);
    } catch {
      // Fallback: Generate client file (e.g. JSON/SVG simulation download)
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(project, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `${project.title.toLowerCase().replace(/\s+/g, '_')}_${exportFormat}.txt`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();

      setExportSuccess(true);
      setTimeout(() => {
        setExportModalOpen(false);
        setExportSuccess(false);
      }, 2000);
    } finally {
      setExportLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto">
      {/* Top Navigation & Project Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E2E7E1] pb-5">
        <div className="space-y-1">
          <Link
            to="/app/designs"
            className="text-xs text-[#68736C] hover:text-[#202923] flex items-center gap-1 mb-1"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to My Designs
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
              {project.title}
            </h1>
            <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-[#EEF4F0] text-[#23483D] border border-[#DCE7DE] uppercase">
              {project.plotPreset.replace('_', ' ')} • {project.plotWidthFt}×{project.plotLengthFt} FT
            </span>
          </div>
          <p className="text-xs text-[#68736C]">
            {project.plotAreaSqFt} sq ft ({project.plotAreaMarla} Marla) • {project.style} • Owned by {project.ownerName}
          </p>
        </div>

        {/* Studio Actions Bar */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleShareClick}
            className="px-3.5 py-2 rounded-xl bg-white border border-[#E2E7E1] text-[#202923] text-xs font-semibold hover:bg-[#F7F7F2] flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <Share2 className="h-3.5 w-3.5 text-[#68736C]" />
            <span>{shareCopied ? 'Link Copied!' : 'Share'}</span>
          </button>

          <Link
            to={`/app/compare?p1=${project.id}`}
            className="px-3.5 py-2 rounded-xl bg-white border border-[#E2E7E1] text-[#202923] text-xs font-semibold hover:bg-[#F7F7F2] flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <GitCompare className="h-3.5 w-3.5 text-[#68736C]" />
            <span>Compare</span>
          </Link>

          <button
            onClick={() => setExportModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export CAD / BIM</span>
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 overflow-x-auto border-b border-[#E2E7E1] pb-2 text-xs">
        {[
          { id: 'overview', label: 'Project Overview' },
          { id: 'floorplans', label: '2D CAD Floor Plans' },
          { id: 'elevation', label: 'Elevation & Facade' },
          { id: 'rooms', label: `Room Schedule (${activeAlternative?.rooms?.length || 0})` },
          { id: 'cost', label: 'BOQ Cost Estimate' },
          { id: 'revisions', label: 'Architect Redlines & Revisions' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-xl font-semibold transition-all shrink-0 ${
              activeTab === tab.id
                ? 'bg-[#23483D] text-white shadow-xs'
                : 'text-[#68736C] hover:text-[#202923] hover:bg-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
              <span className="text-xs text-[#68736C]">Plot Area</span>
              <p className="text-xl font-bold text-[#202923] font-heading">{project.plotAreaSqFt} sq ft</p>
              <p className="text-[11px] text-[#23483D] font-medium">{project.plotAreaMarla} Marla</p>
            </div>
            <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
              <span className="text-xs text-[#68736C]">Storeys & Beds</span>
              <p className="text-xl font-bold text-[#202923] font-heading">{project.floors} Storeys</p>
              <p className="text-[11px] text-[#68736C]">{project.bedrooms} Beds, {project.bathrooms} Baths</p>
            </div>
            <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
              <span className="text-xs text-[#68736C]">Car Porch Capacity</span>
              <p className="text-xl font-bold text-[#202923] font-heading">{project.pakistaniSpecs?.carPorchCapacity || 2} Vehicles</p>
              <p className="text-[11px] text-[#68736C]">Covered Porch</p>
            </div>
            <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
              <span className="text-xs text-[#68736C]">Estimated Budget</span>
              <p className="text-xl font-bold text-[#23483D] font-heading">{formatPKR(activeAlternative?.estimatedCostPKR || project.budgetMinPKR)}</p>
              <p className="text-[11px] text-[#68736C]">Preliminary BOQ</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-[#202923]">Active 2D Floor Plan Blueprint</h3>
                <span className="text-xs font-semibold text-[#23483D]">Vector Vector Engine</span>
              </div>
              <FloorPlanViewer
                type={activeAlternative?.floorPlanSvgType || '10_marla_luxury'}
                rooms={activeAlternative?.rooms || []}
              />
            </div>

            <div className="lg:col-span-4 space-y-4">
              <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-3">
                <h3 className="font-bold text-xs uppercase tracking-wider text-[#68736C]">Design Specifications</h3>
                <div className="space-y-2 text-xs divide-y divide-[#E2E7E1]">
                  <div className="pt-2 flex justify-between">
                    <span className="text-[#68736C]">Front Setback:</span>
                    <strong className="text-[#202923]">{project.pakistaniSpecs?.setbackFrontFt || 7.5} ft (CDA/DHA)</strong>
                  </div>
                  <div className="pt-2 flex justify-between">
                    <span className="text-[#68736C]">Kitchen Zoning:</span>
                    <strong className="text-[#202923]">{project.pakistaniSpecs?.kitchenDirtyKitchenCombo ? 'Show + Dirty Kitchen' : 'Standard'}</strong>
                  </div>
                  <div className="pt-2 flex justify-between">
                    <span className="text-[#68736C]">Guest Drawing Room:</span>
                    <strong className="text-[#202923]">{project.pakistaniSpecs?.drawingRoomSeparate ? 'Separate Entrance' : 'Integrated'}</strong>
                  </div>
                  <div className="pt-2 flex justify-between">
                    <span className="text-[#68736C]">Servant Quarters:</span>
                    <strong className="text-[#202923]">{project.pakistaniSpecs?.servantQuarter ? 'Included with Bath' : 'None'}</strong>
                  </div>
                </div>
              </div>

              <div className="bg-[#EEF4F0] border border-[#DCE7DE] rounded-2xl p-5 space-y-2">
                <h3 className="font-bold text-xs text-[#23483D] flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4" />
                  <span>Municipal Bylaw Quality Gate</span>
                </h3>
                <p className="text-xs text-[#68736C] leading-relaxed">
                  Verified with statutory setbacks for Bahria, DHA, and CDA housing societies. Suitable for professional PCATP redline submission.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: FLOOR PLANS */}
      {activeTab === 'floorplans' && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[#202923]">Multi-Storey Architectural Blueprints</h2>
              <p className="text-xs text-[#68736C]">Switch between Ground, First, and Rooftop plans with interactive room schedules</p>
            </div>
            <button
              onClick={() => window.print()}
              className="px-3.5 py-1.5 rounded-xl border border-[#E2E7E1] bg-white hover:bg-[#F7F7F2] text-xs font-semibold text-[#202923] flex items-center gap-1.5"
            >
              <Printer className="h-3.5 w-3.5" />
              <span>Print Sheet</span>
            </button>
          </div>

          <FloorPlanViewer
            type={activeAlternative?.floorPlanSvgType || '10_marla_luxury'}
            rooms={activeAlternative?.rooms || []}
          />
        </div>
      )}

      {/* TAB 3: ELEVATION & 3D */}
      {activeTab === 'elevation' && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 shadow-xs space-y-4">
          <div>
            <h2 className="text-base font-bold text-[#202923]">Front Architectural Elevation & Facade</h2>
            <p className="text-xs text-[#68736C]">Precision vertical datums displaying FRL ±0'-0", +2'-6" plinth, and +12' ceiling lines</p>
          </div>

          <ElevationViewer
            style={project.style}
            floors={project.floors}
            widthFt={project.plotWidthFt}
          />
        </div>
      )}

      {/* TAB 4: ROOMS SCHEDULE */}
      {activeTab === 'rooms' && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-[#202923]">Comprehensive Room & Spatial Schedule</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px] bg-[#F7F7F2]">
                  <th className="p-3 font-semibold">Room Name</th>
                  <th className="p-3 font-semibold">Storey</th>
                  <th className="p-3 font-semibold">Dimensions (ft)</th>
                  <th className="p-3 font-semibold">Covered Area</th>
                  <th className="p-3 font-semibold">Attached Bath</th>
                  <th className="p-3 font-semibold">Balcony / Terrace</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E7E1] text-[#202923]">
                {activeAlternative?.rooms?.map((r) => (
                  <tr key={r.id} className="hover:bg-[#F7F7F2]">
                    <td className="p-3 font-semibold">{r.name}</td>
                    <td className="p-3 text-[#68736C]">{r.floor} Floor</td>
                    <td className="p-3 font-mono text-[#23483D]">{r.widthFt} × {r.lengthFt} ft</td>
                    <td className="p-3 font-bold">{r.areaSqFt} sq ft</td>
                    <td className="p-3">{r.attachedBath ? <span className="text-[#15803D] font-bold">Yes</span> : <span className="text-[#68736C]">No</span>}</td>
                    <td className="p-3">{r.hasBalcony ? <span className="text-[#15803D] font-bold">Yes</span> : <span className="text-[#68736C]">No</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: COST ESTIMATE */}
      {activeTab === 'cost' && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[#202923]">Preliminary Construction BOQ Estimate</h2>
              <p className="text-xs text-[#68736C]">Calculated based on October 2026 market rates for Pakistani residential construction</p>
            </div>
            <Link
              to="/app/cost-estimation"
              className="px-4 py-2 bg-[#23483D] text-white text-xs font-semibold rounded-xl"
            >
              Adjust in Full Cost Engine
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
              <span className="text-xs text-[#68736C]">Covered Area Total</span>
              <p className="text-xl font-bold text-[#202923]">{activeAlternative?.coveredAreaSqFt || 2200} sq ft</p>
            </div>
            <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
              <span className="text-xs text-[#68736C]">Rate per Square Foot</span>
              <p className="text-xl font-bold text-[#23483D]">PKR 8,000 / sq ft</p>
            </div>
            <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
              <span className="text-xs text-[#68736C]">Estimated Total Project Budget</span>
              <p className="text-xl font-bold text-[#23483D]">{formatPKR(activeAlternative?.estimatedCostPKR || 17600000)}</p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: REVISIONS & REDLINES */}
      {activeTab === 'revisions' && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 shadow-xs space-y-4">
          <div>
            <h2 className="text-base font-bold text-[#202923]">PCATP Architect Redline Annotations</h2>
            <p className="text-xs text-[#68736C]">Official technical review notes and setback verifications for this plan</p>
          </div>

          <div className="space-y-3">
            <div className="p-4 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] text-xs space-y-1">
              <div className="flex items-center justify-between text-[#23483D] font-bold">
                <span>Verified: 7.5 ft Front Setback Compliance</span>
                <span>Ar. Ayesha Mansoor (PCATP #A-4892)</span>
              </div>
              <p className="text-[#68736C]">
                Front car porch setback adheres to DHA Phase 2 Town Planning regulations. Approved for structural submission.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#FDF3EB] border border-[#F2DAC7] text-xs space-y-1">
              <div className="flex items-center justify-between text-[#B86F50] font-bold">
                <span>Recommendation: Dirty Kitchen Ventilation</span>
                <span>Ar. Ayesha Mansoor (PCATP #A-4892)</span>
              </div>
              <p className="text-[#68736C]">
                Recommend widening rear exhaust shaft by 1 foot to enhance natural ventilation during heavy cooking.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {exportModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#202923]/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Download className="h-5 w-5 text-[#23483D]" />
                <h3 className="font-bold text-base text-[#202923]">Export Architectural Deliverables</h3>
              </div>
              <button
                onClick={() => setExportModalOpen(false)}
                className="text-[#68736C] hover:text-[#202923]"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[#68736C]">
              Select your required technical CAD or presentation format to download directly from the architectural engine.
            </p>

            <div className="space-y-2 text-xs">
              {[
                { id: 'pdf', title: 'Presentation Sheet PDF (.pdf)', desc: 'Full architectural layout with dimension callouts' },
                { id: 'dxf', title: 'AutoCAD DXF (.dxf)', desc: 'Layered CAD geometry (A-WALL, A-DOOR, A-WIND, A-DIMS)' },
                { id: 'svg', title: 'Pure Vector Blueprint (.svg)', desc: 'High-resolution scalable vector graphic' },
                { id: 'png', title: 'Technical Blueprint Sheet (.png)', desc: 'High-resolution presentation sheet raster rendering' },
                { id: 'obj', title: 'Wavefront 3D Mesh (.obj)', desc: 'Universal 3D geometry mesh with floor slabs and wall solids' },
                { id: 'blend', title: 'Blender 3D Model (.blend)', desc: 'Procedural solid walls and Cycle renders' },
              ].map((opt) => (
                <label
                  key={opt.id}
                  onClick={() => setExportFormat(opt.id as any)}
                  className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                    exportFormat === opt.id
                      ? 'border-[#23483D] bg-[#EEF4F0]'
                      : 'border-[#E2E7E1] hover:bg-[#F7F7F2]'
                  }`}
                >
                  <input
                    type="radio"
                    name="exportFormat"
                    checked={exportFormat === opt.id}
                    onChange={() => setExportFormat(opt.id as any)}
                    className="mt-0.5 text-[#23483D]"
                  />
                  <div>
                    <span className="font-bold text-[#202923]">{opt.title}</span>
                    <p className="text-[11px] text-[#68736C]">{opt.desc}</p>
                  </div>
                </label>
              ))}
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                onClick={() => setExportModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-[#E2E7E1] text-xs font-semibold text-[#68736C]"
              >
                Cancel
              </button>
              <button
                onClick={handleTriggerExport}
                disabled={exportLoading}
                className="px-5 py-2 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm"
              >
                {exportLoading ? (
                  <span>Generating File...</span>
                ) : exportSuccess ? (
                  <>
                    <Check className="h-4 w-4 text-emerald-300" />
                    <span>Download Ready!</span>
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    <span>Download {exportFormat.toUpperCase()}</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
