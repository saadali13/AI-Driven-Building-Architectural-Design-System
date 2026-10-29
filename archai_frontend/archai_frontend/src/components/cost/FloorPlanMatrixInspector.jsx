import React from 'react';
import { 
  Layers, 
  LayoutGrid, 
  Home, 
  Ruler, 
  Building2, 
  Sparkles, 
  Bed, 
  Bath, 
  Maximize2,
  ChevronRight
} from 'lucide-react';
import { FLOOR_PLAN_PRESETS } from '../../utils/costEngine';

export default function FloorPlanMatrixInspector({ 
  selectedPresetId = '5marla', 
  coveredArea = 2250, 
  plotMarla = 5.0,
  numFloors = 2,
  onPresetChange,
  onAreaChange,
  onPlotChange,
  onFloorsChange,
  onOpenStudio
}) {
  const currentPreset = FLOOR_PLAN_PRESETS.find(p => p.id === selectedPresetId) || FLOOR_PLAN_PRESETS[0];

  const handleSelectPreset = (preset) => {
    if (onPresetChange) onPresetChange(preset.id);
    if (onAreaChange) onAreaChange(preset.coveredAreaSqFt);
    if (onPlotChange) onPlotChange(preset.plotMarla);
    if (onFloorsChange) onFloorsChange(preset.floors);
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-3xl p-6 shadow-xs space-y-5 select-none">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-2xs">
            <LayoutGrid className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span>Active 2D Floor Plan Matrix Ingestion</span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                Parametric JSON
              </span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Material quantities and structural loads compute dynamically from floor dimensions.
            </p>
          </div>
        </div>

        {/* 3D Studio Synchronizer */}
        <button
          type="button"
          onClick={() => onOpenStudio && onOpenStudio(selectedPresetId)}
          className="px-3.5 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-bold text-slate-700 transition flex items-center gap-2 cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          <span>Inspect 3D WebGL</span>
        </button>
      </div>

      {/* Preset Blueprint Selectors */}
      <div className="space-y-2">
        <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-500 block">
          ArchAI Synthesized Blueprint Presets
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {FLOOR_PLAN_PRESETS.map((preset) => {
            const isSelected = preset.id === selectedPresetId;
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => handleSelectPreset(preset)}
                className={`p-4 rounded-2xl border text-left transition cursor-pointer flex flex-col justify-between gap-3 ${
                  isSelected
                    ? 'bg-blue-50/70 border-blue-400 ring-2 ring-blue-500/20 shadow-xs'
                    : 'bg-slate-50 border-slate-200/80 hover:bg-white hover:border-slate-300'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-bold text-xs text-slate-900">{preset.label}</span>
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-white text-slate-700 border border-slate-200">
                      {preset.plotMarla} Marla
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 leading-snug">
                    {preset.dimensions} • {preset.coveredAreaSqFt} Sq.Ft
                  </p>
                </div>

                <div className="flex items-center gap-3 pt-2 border-t border-slate-200/60 text-[10px] text-slate-600 font-mono font-semibold">
                  <span className="flex items-center gap-1">
                    <Bed className="w-3 h-3 text-blue-600" /> {preset.bedCount} Bed
                  </span>
                  <span className="flex items-center gap-1">
                    <Bath className="w-3 h-3 text-indigo-600" /> {preset.bathCount} Bath
                  </span>
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3 h-3 text-emerald-600" /> {preset.floors} Storey
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Interactive Covered Area Slider & Parameter Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        
        {/* Covered Area Slider */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 md:col-span-2">
          <div className="flex justify-between items-center">
            <span className="text-xs font-bold text-slate-800 uppercase flex items-center gap-1.5">
              <Ruler className="w-4 h-4 text-blue-600" />
              Total Covered Built-Up Area
            </span>
            <span className="text-sm font-mono font-black text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-lg border border-blue-200">
              {coveredArea} Sq.Ft
            </span>
          </div>

          <input
            type="range"
            min="1000"
            max="8000"
            step="50"
            value={coveredArea}
            onChange={(e) => onAreaChange && onAreaChange(Number(e.target.value))}
            className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200 rounded-lg appearance-none"
          />

          <div className="flex justify-between text-[10px] text-slate-400 font-mono pt-1">
            <span>5 Marla (~2,250 Sq.Ft)</span>
            <span>10 Marla (~4,200 Sq.Ft)</span>
            <span>1 Kanal (~6,800 Sq.Ft)</span>
          </div>
        </div>

        {/* Storeys & Floors Selector */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
          <span className="text-xs font-bold text-slate-800 uppercase block">
            Number of Storeys
          </span>

          <div className="grid grid-cols-3 gap-1.5">
            {[1, 2, 3].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => onFloorsChange && onFloorsChange(f)}
                className={`py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                  numFloors === f
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {f === 1 ? 'Single' : f === 2 ? 'Double' : 'Triple'}
              </button>
            ))}
          </div>

          <span className="text-[10px] text-slate-400 font-mono block text-center pt-1">
            Ground Coverage: ~{Math.round(coveredArea / numFloors)} Sq.Ft / Floor
          </span>
        </div>

      </div>

    </div>
  );
}
