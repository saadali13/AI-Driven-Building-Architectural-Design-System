import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Calculator,
  ArrowRight,
  ShieldAlert,
  Download,
  Building,
  Coins,
  CheckCircle,
  HelpCircle,
  FileSpreadsheet,
} from 'lucide-react';
import { calculatePreliminaryCost, formatPKR } from '../../services/costEstimatorService';

export const CostEstimationPreviewPage: React.FC = () => {
  const [coveredArea, setCoveredArea] = useState<number>(2275);
  const [floors, setFloors] = useState<number>(2);
  const [category, setCategory] = useState<'economy' | 'standard' | 'premium' | 'luxury'>('premium');
  const [city, setCity] = useState<'Islamabad/Rawalpindi' | 'Lahore' | 'Karachi' | 'Peshawar' | 'Multan' | 'Faisalabad'>('Islamabad/Rawalpindi');

  const estimate = calculatePreliminaryCost({
    projectId: 'preview_proj',
    projectTitle: 'Public Preliminary Estimation Preview',
    coveredAreaSqFt: coveredArea,
    floors,
    category,
    city,
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Title */}
      <div className="border-b border-slate-800 pb-6">
        <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-teal-950 text-teal-300 border border-teal-800">
          PRELIMINARY BOQ ENGINE • PAKISTAN
        </span>
        <h1 className="text-3xl font-bold text-white mt-2 font-heading">
          Preliminary Construction Cost Estimator
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Calculate estimated grey structure and finishing costs based on regional city indices and material benchmark rates.
        </p>
      </div>

      {/* Prominent Mandatory Disclaimer Alert */}
      <div className="bg-amber-950/30 border border-amber-900/60 rounded-2xl p-4 flex items-start gap-3 text-xs text-amber-200">
        <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Planning Notice:</strong> These figures are preliminary planning estimates, not contractor quotations or guaranteed construction costs. Actual costs vary by location, market rates, design specifications, soil conditions, structural requirements, and finishing quality.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Controls Column */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6">
          <h2 className="text-base font-bold text-white font-heading border-b border-slate-800 pb-3">
            Project Dimensions & Parameters
          </h2>

          {/* Covered Area */}
          <div>
            <div className="flex justify-between items-center text-xs mb-1.5">
              <label className="text-slate-300 font-medium">Covered Construction Area</label>
              <span className="font-mono font-bold text-teal-300">{coveredArea.toLocaleString()} sq ft</span>
            </div>
            <input
              type="range"
              min="800"
              max="7000"
              step="50"
              value={coveredArea}
              onChange={(e) => setCoveredArea(Number(e.target.value))}
              className="w-full accent-teal-500 cursor-pointer h-2 bg-slate-950 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-mono">
              <span>800 sq ft</span>
              <span>2,275 (10 Marla)</span>
              <span>7,000 sq ft</span>
            </div>
          </div>

          {/* Number of Floors */}
          <div>
            <label className="block text-xs text-slate-300 font-medium mb-1.5">Storey Structure</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { val: 1, label: 'Single Storey' },
                { val: 2, label: 'Double Storey (G+1)' },
              ].map((f) => (
                <button
                  key={f.val}
                  type="button"
                  onClick={() => setFloors(f.val)}
                  className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all ${
                    floors === f.val
                      ? 'bg-teal-600 text-white border-teal-500 shadow-sm'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* City / Location */}
          <div>
            <label className="block text-xs text-slate-300 font-medium mb-1.5">Regional City Location</label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
            >
              <option value="Islamabad/Rawalpindi">Islamabad / Rawalpindi (CDA / RDA)</option>
              <option value="Lahore">Lahore (LDA / DHA Lahore)</option>
              <option value="Karachi">Karachi (KDA / DHA Karachi)</option>
              <option value="Peshawar">Peshawar (PDA / Hayatabad)</option>
              <option value="Multan">Multan (MDA / DHA Multan)</option>
              <option value="Faisalabad">Faisalabad (FDA)</option>
            </select>
          </div>

          {/* Finishing Quality */}
          <div>
            <label className="block text-xs text-slate-300 font-medium mb-1.5">Finishing Specification</label>
            <div className="space-y-2">
              {[
                { id: 'economy', name: 'Economy Class', rate: '~PKR 5,200/sqft', desc: 'Standard local tiles, basic sanitaryware, commercial ply doors' },
                { id: 'standard', name: 'Standard A-Class', rate: '~PKR 6,600/sqft', desc: 'Good local porcelain, Master/Sonex fittings, semi-solid doors' },
                { id: 'premium', name: 'Premium Executive', rate: '~PKR 8,000/sqft', desc: 'Spanish porcelain tiles, imported grohe fittings, solid ash wood' },
                { id: 'luxury', name: 'High-End Luxury', rate: '~PKR 10,400+/sqft', desc: 'Italian marble, smart automation, double-glazed soundproof' },
              ].map((tier) => (
                <button
                  key={tier.id}
                  type="button"
                  onClick={() => setCategory(tier.id as any)}
                  className={`w-full p-3 rounded-xl text-left border transition-all ${
                    category === tier.id
                      ? 'bg-teal-950/70 border-teal-500 text-white'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold">{tier.name}</span>
                    <span className="text-[11px] font-mono text-teal-400">{tier.rate}</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">{tier.desc}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results & BOQ Breakdown Column */}
        <div className="lg:col-span-7 space-y-6">
          {/* Main Total Highlight Card */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-teal-400">
                  Total Preliminary Estimate
                </span>
                <h3 className="text-3xl sm:text-4xl font-extrabold text-white font-heading mt-1">
                  {formatPKR(estimate.totalEstimatedCostPKR)}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Effective Rate: <strong className="text-teal-300 font-mono">PKR {estimate.costPerSqFtPKR.toLocaleString()} / sq ft</strong>
                </p>
              </div>

              <div className="flex flex-col gap-2">
                <Link
                  to="/app/designs/new"
                  className="px-4 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold text-center shadow-lg transition-colors flex items-center justify-center gap-1.5"
                >
                  <span>Generate Custom Plan</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>

            {/* Min / Typical / Max Scenario Cards */}
            <div className="grid grid-cols-3 gap-3 pt-5 text-center text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase">Low Range (-8%)</span>
                <span className="font-bold text-emerald-400 font-heading text-sm mt-0.5 block">
                  {formatPKR(estimate.scenarioMinPKR)}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-teal-500/40">
                <span className="text-teal-400 block text-[10px] uppercase font-bold">Typical Benchmark</span>
                <span className="font-bold text-white font-heading text-sm mt-0.5 block">
                  {formatPKR(estimate.scenarioTypicalPKR)}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase">High Range (+14%)</span>
                <span className="font-bold text-amber-400 font-heading text-sm mt-0.5 block">
                  {formatPKR(estimate.scenarioMaxPKR)}
                </span>
              </div>
            </div>
          </div>

          {/* Itemized BOQ Breakdown Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white font-heading flex items-center justify-between">
              <span>Itemized Construction Breakdown</span>
              <span className="text-xs font-mono font-normal text-slate-400">Currency: PKR</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                    <th className="pb-2 font-medium">Phase / Material Category</th>
                    <th className="pb-2 font-medium text-right">Approx. Share</th>
                    <th className="pb-2 font-medium text-right">Estimated PKR</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  <tr>
                    <td className="py-2.5 font-medium text-white">Grey Structure (Total Base)</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">~44%</td>
                    <td className="py-2.5 text-right font-mono font-bold text-white">{formatPKR(estimate.breakdown.greyStructure)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Foundation & Earthwork Excavation</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">8%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.foundationAndEarthwork)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Cement, River Sand & Crushed Aggregate</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">11%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.cementSandCrush)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Grade-60 Deformed Steel Rebar</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">15%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.steelRebar)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Red Kiln Burnt Brick Masonry</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">10%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.brickworkMasonry)}</td>
                  </tr>

                  {/* Finishing */}
                  <tr>
                    <td className="py-2.5 font-medium text-white pt-4">Finishing Works & Fixtures</td>
                    <td className="py-2.5 text-right font-mono text-slate-400 pt-4">~51%</td>
                    <td className="py-2.5 text-right font-mono font-bold text-white pt-4">{formatPKR(estimate.totalEstimatedCostPKR - estimate.breakdown.greyStructure)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Flooring Tiles, Marbles & Skirting</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">12%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.flooringTilesMarbles)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Solid Wood Doors & Aluminum Windows</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">11%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.doorsWindowsWoodMetal)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Sanitary Fixtures, Showers & Vanities</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">9%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.kitchenBathFixtures)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Electrical Wiring, Switches & LED Conduits</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">7%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.electricalWiringConduits)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Sanitary Plumbing & Underground Piping</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">6%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.plumbingSanitary)}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pl-4 text-slate-400">↳ Wall Putty, Asian Paint & False Ceilings</td>
                    <td className="py-2.5 text-right font-mono text-slate-400">7%</td>
                    <td className="py-2.5 text-right font-mono">{formatPKR(estimate.breakdown.paintFinishingFalseCeiling)}</td>
                  </tr>

                  {/* Contingency */}
                  <tr className="bg-slate-950/60 font-semibold">
                    <td className="py-2.5 text-amber-300">Inflation Contingency Allowance (+5%)</td>
                    <td className="py-2.5 text-right font-mono text-amber-300">5%</td>
                    <td className="py-2.5 text-right font-mono text-amber-300">{formatPKR(estimate.breakdown.contingencyAllowance)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
