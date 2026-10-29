import React from 'react';
import { 
  Coins, 
  Hammer, 
  TrendingUp, 
  Layers, 
  FileSpreadsheet, 
  CheckCircle2, 
  Wrench,
  Sparkles
} from 'lucide-react';
import { SPEC_TIERS, formatCurrency } from '../../utils/costEngine';

export default function MaterialRatesBreakdown({ 
  market, 
  tierIndex = 1, 
  onTierChange, 
  boqItems = [],
  coveredArea = 2250 
}) {
  const currentTier = SPEC_TIERS[tierIndex] || SPEC_TIERS[1];
  const rates = market?.materials || {};

  // Separate parallel streams
  const materialItems = boqItems.filter(i => i.category === 'Grey Structure');
  const workforceItems = boqItems.filter(i => i.category !== 'Grey Structure' && i.category !== 'Risk Reserve');
  const contingencyItem = boqItems.find(i => i.category === 'Risk Reserve');

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-8 sm:p-12 shadow-sm space-y-10 select-none">
      
      {/* Header & Quality Spec Grades */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-slate-100 pb-8">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 shrink-0 shadow-xs">
            <Coins className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
              <span>Parallel Cost Streams &amp; Rate Breakdown</span>
              <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                {market?.city} Verified
              </span>
            </h2>
            <p className="text-base font-medium text-slate-500 mt-1">
              Real-time regional retail prices partitioned by Material Procurement vs. Workforce Overheads.
            </p>
          </div>
        </div>

        {/* Quality Tiers */}
        <div className="flex items-center gap-2 p-2 bg-slate-100 rounded-2xl border border-slate-200">
          {[
            { id: 0, label: 'Economy' },
            { id: 1, label: 'Standard' },
            { id: 2, label: 'Luxury' }
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => onTierChange && onTierChange(t.id)}
              className={`px-5 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer ${
                tierIndex === t.id
                  ? 'bg-white text-blue-700 shadow-xs border border-slate-200 font-black'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Live Regional Price Tickers */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
        <div className="p-6 bg-slate-50 border border-slate-200 rounded-2xl">
          <span className="text-sm font-mono font-bold uppercase text-slate-500 block">
            Cement (50kg OPC)
          </span>
          <h3 className="text-2xl font-black text-slate-900 font-mono mt-2">
            {formatCurrency(rates.cementBagPkr, market?.currency)}
          </h3>
          <span className="text-sm text-emerald-600 font-bold flex items-center gap-1.5 mt-2">
            <TrendingUp className="w-4 h-4" /> Live Index
          </span>
        </div>

        <div className="p-6 bg-slate-50 border border-slate-200 rounded-2xl">
          <span className="text-sm font-mono font-bold uppercase text-slate-500 block">
            Steel Rebar (Grade 60)
          </span>
          <h3 className="text-2xl font-black text-slate-900 font-mono mt-2">
            {formatCurrency(rates.steelTonPkr, market?.currency)}/Ton
          </h3>
          <span className="text-sm text-blue-600 font-bold flex items-center gap-1.5 mt-2">
            <TrendingUp className="w-4 h-4" /> High-Yield
          </span>
        </div>

        <div className="p-6 bg-slate-50 border border-slate-200 rounded-2xl">
          <span className="text-sm font-mono font-bold uppercase text-slate-500 block">
            Kiln Clay Bricks
          </span>
          <h3 className="text-2xl font-black text-slate-900 font-mono mt-2">
            {formatCurrency(rates.bricksPer1000Pkr, market?.currency)}/k
          </h3>
          <span className="text-sm text-slate-600 font-mono font-bold block mt-2">
            First-Class
          </span>
        </div>

        <div className="p-6 bg-slate-50 border border-slate-200 rounded-2xl">
          <span className="text-sm font-mono font-bold uppercase text-slate-500 block">
            Civil Labor Wage
          </span>
          <h3 className="text-2xl font-black text-slate-900 font-mono mt-2">
            {formatCurrency(rates.laborSqFtPkr, market?.currency)}/Sq.Ft
          </h3>
          <span className="text-sm text-purple-600 font-bold flex items-center gap-1.5 mt-2">
            <Hammer className="w-4 h-4" /> Master Mason
          </span>
        </div>
      </div>

      {/* Stream 1: Material Procurement */}
      <div className="space-y-5">
        <div className="flex items-center gap-3">
          <Layers className="w-6 h-6 text-blue-600" />
          <h3 className="text-xl sm:text-2xl font-bold text-slate-900">
            Stream 1: Raw Material Procurement
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {materialItems.map((item) => (
            <div 
              key={item.id}
              className="p-6 bg-slate-50/80 border border-slate-200 rounded-2xl hover:bg-white hover:border-blue-300 transition-all space-y-3"
            >
              <div className="flex justify-between items-start">
                <span className="font-bold text-base text-slate-900">{item.name}</span>
                <span className="font-black text-lg text-slate-900 font-mono">
                  {formatCurrency(item.totalCost, market?.currency)}
                </span>
              </div>
              <p className="text-sm text-slate-600 font-medium">{item.notes}</p>
              <div className="flex items-center justify-between text-sm font-mono text-slate-700 pt-2 border-t border-slate-200/60">
                <span>{item.quantity.toLocaleString()} {item.unit}</span>
                <span className="font-bold text-blue-600">{item.pct}% Budget</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Stream 2: Workforce & Engineering Overhead */}
      <div className="space-y-5 pt-3">
        <div className="flex items-center gap-3">
          <Wrench className="w-6 h-6 text-indigo-600" />
          <h3 className="text-xl sm:text-2xl font-bold text-slate-900">
            Stream 2: Workforce &amp; Engineering Overheads
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {workforceItems.map((item) => (
            <div 
              key={item.id}
              className="p-6 bg-slate-50/80 border border-slate-200 rounded-2xl hover:bg-white hover:border-indigo-300 transition-all space-y-3"
            >
              <div className="flex justify-between items-start">
                <span className="font-bold text-base text-slate-900">{item.name}</span>
                <span className="font-black text-lg text-slate-900 font-mono">
                  {formatCurrency(item.totalCost, market?.currency)}
                </span>
              </div>
              <p className="text-sm text-slate-600 font-medium">{item.notes}</p>
              <div className="flex items-center justify-between text-sm font-mono text-slate-700 pt-2 border-t border-slate-200/60">
                <span>{item.quantity.toLocaleString()} {item.unit}</span>
                <span className="font-bold text-indigo-600">{item.pct}% Budget</span>
              </div>
            </div>
          ))}
        </div>
      </div>


      {/* Contingency Buffer */}
      {contingencyItem && (
        <div className="p-4 bg-cyan-50/50 border border-cyan-200 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="space-y-0.5">
            <span className="text-xs font-bold text-cyan-900 uppercase block">
              {contingencyItem.name}
            </span>
            <p className="text-xs text-cyan-700">{contingencyItem.notes}</p>
          </div>
          <span className="text-base font-black text-cyan-900 font-mono">
            {formatCurrency(contingencyItem.totalCost, market?.currency)}
          </span>
        </div>
      )}

    </div>
  );
}
