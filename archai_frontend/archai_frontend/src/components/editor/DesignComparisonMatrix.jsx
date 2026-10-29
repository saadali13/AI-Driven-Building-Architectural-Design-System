import React from 'react';
import { CheckCircle2, AlertTriangle, Scale, DollarSign, Layers } from 'lucide-react';
import { validateFloorPlan } from '../../utils/DesignValidator';


export default function DesignComparisonMatrix({ designA, designB }) {
  const defaultDesignA = designA || {
    title: '5 Marla Standard Layout',
    plotSizeMarla: 5,
    coveredAreaSqFt: 1850,
    bedCount: 3,
    bathCount: 3,
    similarityScore: 94.2,
    estimatedCostPkr: 12850000,
    floorPlanJson: {
      rooms: [
        { id: '1', type: 'BEDROOM', name: 'Master Bed', x: 40, y: 40, w: 180, h: 140 },
        { id: '2', type: 'BATHROOM', name: 'Bath 1', x: 230, y: 40, w: 90, h: 90 },
        { id: '3', type: 'LIVING_ROOM', name: 'Main Lounge', x: 40, y: 190, w: 280, h: 170 },
      ]
    }
  };

  const defaultDesignB = designB || {
    title: '5 Marla Executive Layout',
    plotSizeMarla: 5,
    coveredAreaSqFt: 2100,
    bedCount: 4,
    bathCount: 4,
    similarityScore: 88.7,
    estimatedCostPkr: 15200000,
    floorPlanJson: {
      rooms: [
        { id: '1', type: 'BEDROOM', name: 'Master Bed', x: 40, y: 40, w: 180, h: 140 },
        { id: '2', type: 'BATHROOM', name: 'Bath 1', x: 200, y: 40, w: 90, h: 90 },
        { id: '3', type: 'LIVING_ROOM', name: 'Main Lounge', x: 40, y: 190, w: 280, h: 170 },
      ]
    }
  };

  const valA = validateFloorPlan(defaultDesignA.floorPlanJson);
  const valB = validateFloorPlan(defaultDesignB.floorPlanJson);

  const formatPKR = (val) => new Intl.NumberFormat('en-PK', { style: 'currency', currency: 'PKR', maximumFractionDigits: 0 }).format(val);

  return (
    <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 text-slate-900 shadow-sm space-y-6 w-full max-w-5xl mx-auto font-sans">
      {/* Matrix Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-5 gap-4">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2.5 text-slate-900 tracking-tight">
            <Scale className="w-5 h-5 text-blue-600 shrink-0" />
            <span>Side-by-Side Design Comparison &amp; Validation Matrix</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Evaluating spatial concepts against plot area, similarity vectors, cost models, and structural integrity bylaws.
          </p>
        </div>
        <div className="text-xs px-3.5 py-1.5 bg-blue-50 text-blue-700 rounded-xl border border-blue-200 font-mono font-bold shrink-0 self-start sm:self-auto">
          CUST Architectural Validation Engine
        </div>
      </div>

      {/* Matrix Column Headers */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-b border-slate-100 pb-4 text-xs font-bold uppercase tracking-wider">
        <div className="text-slate-400 font-mono hidden md:block">Evaluation Parameter</div>
        <div className="p-3 bg-blue-50 rounded-xl border border-blue-200 text-blue-900 font-bold text-sm flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
          <span>{defaultDesignA.title}</span>
        </div>
        <div className="p-3 bg-indigo-50 rounded-xl border border-indigo-200 text-indigo-900 font-bold text-sm flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
          <span>{defaultDesignB.title}</span>
        </div>
      </div>

      {/* Comparison Rows */}
      <div className="space-y-3 text-xs sm:text-sm">
        
        {/* Row 1: Plot Size */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 items-center">
          <div className="font-bold text-slate-700">Plot Size &amp; Covered Area</div>
          <div className="text-slate-900 font-semibold">{defaultDesignA.plotSizeMarla} Marla ({defaultDesignA.coveredAreaSqFt} sq ft)</div>
          <div className="text-slate-900 font-semibold">{defaultDesignB.plotSizeMarla} Marla ({defaultDesignB.coveredAreaSqFt} sq ft)</div>
        </div>

        {/* Row 2: Config */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 items-center">
          <div className="font-bold text-slate-700">Bed / Bath Configuration</div>
          <div className="text-slate-900 font-semibold">{defaultDesignA.bedCount} Beds / {defaultDesignA.bathCount} Baths</div>
          <div className="text-slate-900 font-semibold">{defaultDesignB.bedCount} Beds / {defaultDesignB.bathCount} Baths</div>
        </div>

        {/* Row 3: Cosine Similarity */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 items-center">
          <div className="font-bold text-slate-700">NLP Vector Similarity</div>
          <div className="font-mono text-blue-600 font-bold text-base">{defaultDesignA.similarityScore}% Match</div>
          <div className="font-mono text-indigo-600 font-bold text-base">{defaultDesignB.similarityScore}% Match</div>
        </div>

        {/* Row 4: Est Cost */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 items-center">
          <div className="font-bold text-slate-700">Est. Construction Cost (PKR)</div>
          <div className="font-mono font-bold text-emerald-700 text-base">{formatPKR(defaultDesignA.estimatedCostPkr)}</div>
          <div className="font-mono font-bold text-emerald-700 text-base">{formatPKR(defaultDesignB.estimatedCostPkr)}</div>
        </div>

        {/* Row 5: Automated Rule Validation */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-200 items-start">
          <div className="font-bold text-slate-700">Automated Rule Validation</div>
          <div>
            {valA.isValid ? (
              <span className="text-emerald-800 text-xs font-bold flex items-center gap-1.5 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                <span>Structural Check Passed</span>
              </span>
            ) : (
              <div className="space-y-1.5">
                {valA.errors.map((err, i) => (
                  <div key={i} className="text-rose-700 text-xs font-medium flex items-center gap-1.5 bg-rose-50 px-3 py-1.5 rounded-xl border border-rose-200">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
                    <span>{err}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            {valB.isValid ? (
              <span className="text-emerald-800 text-xs font-bold flex items-center gap-1.5 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                <span>Structural Check Passed</span>
              </span>
            ) : (
              <div className="space-y-1.5">
                {valB.errors.map((err, i) => (
                  <div key={i} className="text-rose-700 text-xs font-medium flex items-center gap-1.5 bg-rose-50 px-3 py-1.5 rounded-xl border border-rose-200">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
                    <span>{err}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
