import React, { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Search,
  Filter,
  Grid,
  List,
  Heart,
  Eye,
  SlidersHorizontal,
  X,
  Compass,
  Building,
  CheckCircle2,
  Maximize2,
  ArrowRight,
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { DesignTemplate, PlotPreset } from '../../types';
import { formatPKR } from '../../services/costEstimatorService';
import { FloorPlanViewer } from '../../components/architectural/FloorPlanViewer';

export const TemplatesPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialPreset = searchParams.get('preset') as PlotPreset | null;

  const { templates, toggleFavoriteTemplate } = useProjects();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPreset, setSelectedPreset] = useState<PlotPreset | 'all'>(initialPreset || 'all');
  const [selectedStyle, setSelectedStyle] = useState<string>('all');
  const [selectedFloors, setSelectedFloors] = useState<string>('all');
  const [inspectTemplate, setInspectTemplate] = useState<DesignTemplate | null>(null);

  const filteredTemplates = useMemo(() => {
    return templates.filter((t) => {
      if (selectedPreset !== 'all' && t.plotCategory !== selectedPreset) return false;
      if (selectedStyle !== 'all' && t.style !== selectedStyle) return false;
      if (selectedFloors !== 'all' && t.floors.toString() !== selectedFloors) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = t.name.toLowerCase().includes(q);
        const matchesDesc = t.description.toLowerCase().includes(q);
        const matchesDims = t.plotDimensions.toLowerCase().includes(q);
        if (!matchesName && !matchesDesc && !matchesDims) return false;
      }
      return true;
    });
  }, [templates, selectedPreset, selectedStyle, selectedFloors, searchQuery]);

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7E1] pb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE] mb-2">
            <Compass className="h-3.5 w-3.5" />
            <span>Pre-Engineered Master Blueprints</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
            Architectural Design Templates
          </h1>
          <p className="text-xs text-[#68736C] mt-0.5">
            Explore ready-to-use Pakistani residential house plans. Click "Use Template" to customize in New Design.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-[#E2E7E1] rounded-2xl p-4 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between text-xs">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#68736C]" />
          <input
            type="text"
            placeholder="Search templates by name, plot dimensions (e.g. 25x45)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl pl-9 pr-4 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <select
            value={selectedPreset}
            onChange={(e) => setSelectedPreset(e.target.value as any)}
            className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          >
            <option value="all">All Plot Sizes</option>
            <option value="5_marla">5 Marla (25×45)</option>
            <option value="7_marla">7 Marla (30×52.5)</option>
            <option value="10_marla">10 Marla (35×65)</option>
            <option value="1_kanal">1 Kanal (50×90)</option>
          </select>

          <select
            value={selectedStyle}
            onChange={(e) => setSelectedStyle(e.target.value)}
            className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          >
            <option value="all">All Architectural Styles</option>
            <option value="Modern Contemporary">Modern Contemporary</option>
            <option value="Minimalist">Minimalist</option>
          </select>
        </div>
      </div>

      {/* Gallery Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((tpl) => (
          <div
            key={tpl.id}
            className="bg-white border border-[#E2E7E1] hover:border-[#23483D] rounded-2xl p-5 shadow-xs transition-all hover:shadow-md flex flex-col justify-between space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-[#EEF4F0] text-[#23483D] border border-[#DCE7DE] uppercase">
                  {tpl.plotCategory.replace('_', ' ')} • {tpl.plotDimensions}
                </span>

                <button
                  onClick={() => toggleFavoriteTemplate(tpl.id)}
                  className="p-1 text-[#68736C] hover:text-[#B86F50]"
                  title="Favorite"
                >
                  <Heart className={`h-4 w-4 ${tpl.isFavorite ? 'fill-[#B86F50] text-[#B86F50]' : ''}`} />
                </button>
              </div>

              <div>
                <h3 className="font-bold text-sm text-[#202923]">{tpl.name}</h3>
                <p className="text-xs text-[#68736C] mt-1 line-clamp-2">{tpl.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs py-2 border-y border-[#E2E7E1] text-[#68736C]">
                <div>
                  <span className="text-[10px] uppercase font-semibold text-[#68736C]/70">Bedrooms</span>
                  <p className="font-semibold text-[#202923]">{tpl.bedrooms} Beds, {tpl.bathrooms} Baths</p>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-semibold text-[#68736C]/70">Budget Benchmark</span>
                  <p className="font-semibold text-[#23483D]">{formatPKR(tpl.budgetPKR)}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5 pt-1">
                {tpl.features.slice(0, 3).map((f, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-[#F7F7F2] border border-[#E2E7E1] text-[#68736C]">
                    {f}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between gap-2">
              <button
                onClick={() => setInspectTemplate(tpl)}
                className="px-3 py-1.5 rounded-xl border border-[#E2E7E1] hover:bg-[#F7F7F2] text-xs font-semibold text-[#202923]"
              >
                Inspect Plan
              </button>

              <Link
                to={`/app/designs/new?templateId=${tpl.id}`}
                className="px-4 py-1.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs"
              >
                <span>Use Template</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Inspect Modal */}
      {inspectTemplate && (
        <div className="fixed inset-0 z-50 bg-[#202923]/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono font-bold uppercase text-[#23483D]">{inspectTemplate.plotDimensions}</span>
                <h3 className="font-bold text-base text-[#202923]">{inspectTemplate.name}</h3>
              </div>
              <button onClick={() => setInspectTemplate(null)} className="text-[#68736C] hover:text-[#202923]">
                ✕
              </button>
            </div>

            <FloorPlanViewer type={inspectTemplate.floorPlanSvgType} />

            <div className="flex justify-end gap-2 pt-2 border-t border-[#E2E7E1]">
              <button
                onClick={() => setInspectTemplate(null)}
                className="px-4 py-2 rounded-xl border border-[#E2E7E1] text-xs font-semibold text-[#68736C]"
              >
                Close
              </button>
              <Link
                to={`/app/designs/new?templateId=${inspectTemplate.id}`}
                className="px-5 py-2 rounded-xl bg-[#23483D] text-white text-xs font-semibold hover:bg-[#1A372E]"
              >
                Use This Template
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
