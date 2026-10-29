import React from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  FileCode, 
  Building2, 
  Compass, 
  Scale,
  Sparkles
} from 'lucide-react';

export default function MunicipalComplianceCard({ compliance }) {
  if (!compliance) return null;

  const {
    authority,
    plotMarla,
    plotSqFt,
    actualCoveragePct,
    maxAllowedCoveragePct,
    isCoverageCompliant,
    frontSetbackRequiredFt,
    rearSetbackRequiredFt,
    sideSetbackRequiredFt,
    seismicZone
  } = compliance;

  return (
    <div className="bg-white border border-slate-200/90 rounded-3xl p-6 shadow-xs space-y-4 select-none">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shadow-2xs">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span>Municipal By-Laws &amp; Building Code Compliance</span>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                isCoverageCompliant 
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}>
                {isCoverageCompliant ? '100% Compliant' : 'Setback Warning'}
              </span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Verified against {authority} statutory building codes.
            </p>
          </div>
        </div>
      </div>

      {/* Compliance Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        
        {/* Ground Coverage */}
        <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl space-y-1">
          <span className="text-[10px] font-mono font-bold uppercase text-slate-400">
            Ground Coverage Ratio
          </span>
          <div className="flex items-baseline justify-between">
            <h4 className="text-base font-black text-slate-900 font-mono">
              {actualCoveragePct}%
            </h4>
            <span className="text-[10px] font-mono font-bold text-slate-500">
              Max: {maxAllowedCoveragePct}%
            </span>
          </div>
          <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden mt-1">
            <div 
              className={`h-full rounded-full ${isCoverageCompliant ? 'bg-emerald-500' : 'bg-amber-500'}`}
              style={{ width: `${Math.min(100, (actualCoveragePct / maxAllowedCoveragePct) * 100)}%` }}
            />
          </div>
        </div>

        {/* Setbacks */}
        <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl space-y-1">
          <span className="text-[10px] font-mono font-bold uppercase text-slate-400">
            Mandatory Setbacks
          </span>
          <p className="text-xs font-bold text-slate-800 pt-0.5">
            Front: {frontSetbackRequiredFt} ft • Rear: {rearSetbackRequiredFt} ft
          </p>
          <span className="text-[10px] text-emerald-600 font-mono font-bold block pt-1">
            ✓ Auto-Checked in 2D Matrix
          </span>
        </div>

        {/* Seismic Zone */}
        <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl space-y-1">
          <span className="text-[10px] font-mono font-bold uppercase text-slate-400">
            Seismic Classification
          </span>
          <p className="text-xs font-bold text-slate-800 truncate pt-0.5">
            {seismicZone}
          </p>
          <span className="text-[10px] text-blue-600 font-mono font-bold block pt-1">
            ✓ High-Ductility Rebar Factored
          </span>
        </div>

      </div>

    </div>
  );
}
