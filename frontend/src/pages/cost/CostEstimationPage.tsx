import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Calculator,
  Printer,
  Save,
  CheckCircle2,
  TrendingUp,
  FileSpreadsheet,
  Check,
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { calculatePreliminaryCost, formatPKR } from '../../services/costEstimatorService';

export const CostEstimationPage: React.FC = () => {
  const { costEstimates, addCostEstimate } = useProjects();

  const [coveredArea, setCoveredArea] = useState<number>(3650);
  const [floors, setFloors] = useState<number>(2);
  const [category, setCategory] = useState<'economy' | 'standard' | 'premium' | 'luxury'>('premium');
  const [city, setCity] = useState<'Islamabad/Rawalpindi' | 'Lahore' | 'Karachi' | 'Peshawar' | 'Multan' | 'Faisalabad'>('Islamabad/Rawalpindi');
  const [estimateSaved, setEstimateSaved] = useState(false);

  const currentEstimate = calculatePreliminaryCost({
    projectId: `proj_custom_${Date.now()}`,
    projectTitle: `${coveredArea} sq ft Custom Residence`,
    coveredAreaSqFt: coveredArea,
    floors,
    category,
    city,
  });

  const handleSaveEstimate = () => {
    addCostEstimate(currentEstimate);
    setEstimateSaved(true);
    setTimeout(() => setEstimateSaved(false), 3000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E2E7E1] pb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE] mb-2">
            <Calculator className="h-3.5 w-3.5 text-[#23483D]" />
            <span>Parametric BOQ Cost Engine • Pakistan</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
            Construction Cost Planning & BOQ
          </h1>
          <p className="text-xs text-[#68736C] mt-0.5">
            Calibrated with real-time Pakistani material market rates (cement, deformed steel, brick masonry, labour wages).
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={handlePrint}
            className="px-3.5 py-2 rounded-xl bg-white border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <Printer className="h-4 w-4 text-[#68736C]" />
            <span>Print Report</span>
          </button>
          <button
            onClick={handleSaveEstimate}
            className="px-4 py-2 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
          >
            {estimateSaved ? <CheckCircle2 className="h-4 w-4 text-emerald-300" /> : <Save className="h-4 w-4" />}
            <span>{estimateSaved ? 'Estimate Saved!' : 'Save Estimate'}</span>
          </button>
        </div>
      </div>

      {/* SECTION A: PROJECT INPUTS */}
      <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 shadow-xs space-y-5">
        <h2 className="text-sm font-bold text-[#202923] uppercase tracking-wider">A. Project Parameters & Regional City Index</h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="block text-[#68736C] font-semibold mb-1">Total Covered Area (sq ft)</label>
            <input
              type="number"
              step={50}
              value={coveredArea}
              onChange={(e) => setCoveredArea(Math.max(500, parseInt(e.target.value) || 0))}
              className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] font-bold font-mono focus:outline-none focus:border-[#23483D]"
            />
          </div>

          <div>
            <label className="block text-[#68736C] font-semibold mb-1">Number of Storeys</label>
            <select
              value={floors}
              onChange={(e) => setFloors(parseInt(e.target.value))}
              className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
            >
              <option value={1}>Single Storey (Ground Floor)</option>
              <option value={2}>Double Storey (Ground + 1st)</option>
              <option value={3}>Triple Storey (G + 1st + Mumty)</option>
            </select>
          </div>

          <div>
            <label className="block text-[#68736C] font-semibold mb-1">Finishing Specification Tier</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as any)}
              className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
            >
              <option value="economy">Economy (5,200 PKR/sq ft)</option>
              <option value="standard">Standard (6,600 PKR/sq ft)</option>
              <option value="premium">Premium (8,000 PKR/sq ft)</option>
              <option value="luxury">Luxury (10,400 PKR/sq ft)</option>
            </select>
          </div>

          <div>
            <label className="block text-[#68736C] font-semibold mb-1">Regional Location</label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value as any)}
              className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
            >
              <option value="Islamabad/Rawalpindi">Islamabad / Rawalpindi (1.03×)</option>
              <option value="Lahore">Lahore (1.00× Baseline)</option>
              <option value="Karachi">Karachi (1.05× Coastal Index)</option>
              <option value="Peshawar">Peshawar (0.96×)</option>
              <option value="Multan">Multan (0.95×)</option>
              <option value="Faisalabad">Faisalabad (0.94×)</option>
            </select>
          </div>
        </div>
      </div>

      {/* SECTION B: ESTIMATE SUMMARY */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-1">
          <span className="text-xs text-[#68736C] font-semibold">Total Estimated Budget</span>
          <p className="text-2xl font-bold text-[#23483D] font-heading">
            {formatPKR(currentEstimate.totalEstimatedCostPKR)}
          </p>
          <p className="text-[11px] text-[#68736C]">PKR {currentEstimate.totalEstimatedCostPKR.toLocaleString()}</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-1">
          <span className="text-xs text-[#68736C] font-semibold">Grey Structure Total</span>
          <p className="text-2xl font-bold text-[#202923] font-heading">
            {formatPKR(currentEstimate.breakdown.greyStructure)}
          </p>
          <p className="text-[11px] text-[#68736C]">Foundation, RCC, Rebar & Bricks</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
          <span className="text-xs text-[#68736C] font-semibold">Finishing Total</span>
          <p className="text-2xl font-bold text-[#202923] font-heading">
            {formatPKR(currentEstimate.totalEstimatedCostPKR - currentEstimate.breakdown.greyStructure)}
          </p>
          <p className="text-[11px] text-[#68736C]">Tiles, Woodwork, Electric & Paint</p>
        </div>

        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 space-y-1 shadow-xs">
          <span className="text-xs text-[#68736C] font-semibold">Unit Rate per Sq Ft</span>
          <p className="text-2xl font-bold text-[#23483D] font-heading">
            PKR {currentEstimate.costPerSqFtPKR.toLocaleString()}
          </p>
          <p className="text-[11px] text-[#68736C]">{city} Index Applied</p>
        </div>
      </div>

      {/* SECTION C: DETAILED BOQ BREAKDOWN */}
      <div className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden shadow-xs">
        <div className="p-4 bg-[#F7F7F2] border-b border-[#E2E7E1] flex items-center justify-between">
          <h2 className="text-xs font-bold text-[#202923] uppercase tracking-wider">C. Itemized Bill of Quantities (BOQ)</h2>
          <span className="text-[11px] text-[#68736C]">PEC Construction Formula Calibrated</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="p-3.5 font-semibold">Construction Trade & Scope</th>
                <th className="p-3.5 font-semibold">Material Benchmark</th>
                <th className="p-3.5 font-semibold text-right">Allocation (PKR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#202923]">
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">Foundation, Earthwork & Excavation</td>
                <td className="p-3.5 text-[#68736C]">Termite proofing, lean concrete & plinth beam</td>
                <td className="p-3.5 font-mono font-bold text-right">{formatPKR(currentEstimate.breakdown.foundationAndEarthwork)}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">Grade-60 Deformed Steel Rebar</td>
                <td className="p-3.5 text-[#68736C]">Columns, beams, and RCC suspended slabs</td>
                <td className="p-3.5 font-mono font-bold text-right text-[#23483D]">{formatPKR(currentEstimate.breakdown.steelRebar)}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">OPC Cement, Sand & Aggregate Crush</td>
                <td className="p-3.5 text-[#68736C]">Standard batching ratio 1:2:4</td>
                <td className="p-3.5 font-mono font-bold text-right">{formatPKR(currentEstimate.breakdown.cementSandCrush)}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">Burnt Red Clay Brick Masonry</td>
                <td className="p-3.5 text-[#68736C]">9-inch external load-bearing & 4.5-inch partition walls</td>
                <td className="p-3.5 font-mono font-bold text-right">{formatPKR(currentEstimate.breakdown.brickworkMasonry)}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">Flooring, Porcelain Tiles & Marbles</td>
                <td className="p-3.5 text-[#68736C]">{category.toUpperCase()} grade porcelain & skirting</td>
                <td className="p-3.5 font-mono font-bold text-right">{formatPKR(currentEstimate.breakdown.flooringTilesMarbles)}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">Doors, Windows, Woodwork & Aluminum</td>
                <td className="p-3.5 text-[#68736C]">Solid wood main door, UPVC / aluminum glazed windows</td>
                <td className="p-3.5 font-mono font-bold text-right">{formatPKR(currentEstimate.breakdown.doorsWindowsWoodMetal)}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">Plumbing, Piping & Sanitary Fixtures</td>
                <td className="p-3.5 text-[#68736C]">PPRC pipes, master sanitary ware & chrome mixers</td>
                <td className="p-3.5 font-mono font-bold text-right">{formatPKR(currentEstimate.breakdown.plumbingSanitary)}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">Direct Labour Wages & Supervision</td>
                <td className="p-3.5 text-[#68736C]">Masons, carpenters, steel fixers, and daily labour</td>
                <td className="p-3.5 font-mono font-bold text-right text-[#23483D]">{formatPKR(currentEstimate.breakdown.labourCost)}</td>
              </tr>
              <tr className="hover:bg-[#F7F7F2]">
                <td className="p-3.5 font-medium">Contingency Margin (5%)</td>
                <td className="p-3.5 text-[#68736C]">Reserve against short-term material inflation</td>
                <td className="p-3.5 font-mono font-bold text-right text-[#B86F50]">{formatPKR(currentEstimate.breakdown.contingencyAllowance)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
