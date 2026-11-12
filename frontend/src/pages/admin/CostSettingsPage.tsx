import React, { useState } from 'react';
import {
  Save,
  CheckCircle2,
  TrendingUp,
  FileSpreadsheet,
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { MaterialRateItem } from '../../types';

export const CostSettingsPage: React.FC = () => {
  const { materialRates, updateMaterialRate } = useProjects();
  const [rates, setRates] = useState<MaterialRateItem[]>(materialRates);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleRateChange = (id: string, newRate: number) => {
    setRates((prev) =>
      prev.map((r) => (r.id === id ? { ...r, currentRatePKR: newRate } : r))
    );
  };

  const handleSaveAll = () => {
    rates.forEach((r) => updateMaterialRate(r.id, r.currentRatePKR));
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-[#E2E7E1] pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE] mb-2">
            <FileSpreadsheet className="h-3.5 w-3.5 text-[#23483D]" />
            <span>Economic Calibration Module</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
            Construction Material & Rate Management
          </h1>
          <p className="text-xs text-[#68736C] mt-0.5">
            Calibrate regional benchmark prices for Pakistan (OPC cement, steel rebar, clay bricks, labour wages).
          </p>
        </div>

        <button
          onClick={handleSaveAll}
          className="px-5 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors self-start sm:self-auto"
        >
          {savedSuccess ? <CheckCircle2 className="h-4 w-4 text-emerald-300" /> : <Save className="h-4 w-4" />}
          <span>{savedSuccess ? 'Rates Saved!' : 'Save All Rate Changes'}</span>
        </button>
      </div>

      {savedSuccess && (
        <div className="p-3.5 rounded-2xl bg-[#EEF4F0] border border-[#DCE7DE] text-[#23483D] text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>Regional benchmark rates updated successfully across the cost calculation engine.</span>
        </div>
      )}

      {/* Rates Table */}
      <div className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px] bg-[#F7F7F2]">
                <th className="p-3.5 font-semibold">Material / Trade Item</th>
                <th className="p-3.5 font-semibold">Category</th>
                <th className="p-3.5 font-semibold">Unit of Measurement</th>
                <th className="p-3.5 font-semibold">Benchmark Source</th>
                <th className="p-3.5 font-semibold text-right">Current Rate (PKR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#202923]">
              {rates.map((m) => (
                <tr key={m.id} className="hover:bg-[#F7F7F2]">
                  <td className="p-3.5 font-semibold text-[#202923]">{m.material}</td>
                  <td className="p-3.5">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#F7F7F2] border border-[#E2E7E1] text-[#68736C] uppercase">
                      {m.category}
                    </span>
                  </td>
                  <td className="p-3.5 font-mono text-[#68736C]">{m.unit}</td>
                  <td className="p-3.5 text-[#68736C]">{m.benchmarkSource}</td>
                  <td className="p-3.5 text-right">
                    <input
                      type="number"
                      value={m.currentRatePKR}
                      onChange={(e) => handleRateChange(m.id, parseFloat(e.target.value) || 0)}
                      className="w-32 bg-[#F7F7F2] border border-[#E2E7E1] rounded-lg px-2.5 py-1 text-right font-mono font-bold text-[#23483D] focus:outline-none focus:border-[#23483D]"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
