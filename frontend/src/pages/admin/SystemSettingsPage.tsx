import React, { useState } from 'react';
import { Settings, RefreshCcw, CheckCircle2, ShieldCheck, Database, Sliders } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';

export const SystemSettingsPage: React.FC = () => {
  const { resetDemoData } = useProjects();
  const [resetDone, setResetDone] = useState(false);
  const [aiTolerance, setAiTolerance] = useState(0.85);

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all sandbox demo data to factory defaults?')) {
      resetDemoData();
      setResetDone(true);
      setTimeout(() => setResetDone(false), 3000);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5">
        <h1 className="text-2xl font-bold text-[#202923] font-heading">Platform & System Settings</h1>
        <p className="text-xs text-[#68736C] mt-1">
          Global application configuration, AI spatial model parameters, and testing sandboxes.
        </p>
      </div>

      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 sm:p-8 space-y-6 text-xs shadow-xs">
        {/* Reset Demo Data Card */}
        <div className="p-4 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="font-bold text-[#202923] text-sm flex items-center gap-2">
              <Database className="h-4 w-4 text-[#23483D]" />
              Reset Demo Sandbox to Factory Defaults
            </h3>
            <p className="text-[#68736C] mt-0.5">
              Restores initial mock Pakistani projects (5M, 10M, 1 Kanal), templates, and material rates.
            </p>
          </div>
          <button
            onClick={handleReset}
            className="px-4 py-2 rounded-xl bg-[#23483D] hover:bg-[#1a362d] text-white font-semibold flex items-center gap-1.5 shrink-0 transition-colors shadow-xs"
          >
            <RefreshCcw className="h-3.5 w-3.5" />
            <span>{resetDone ? 'Reset Complete!' : 'Reset Demo Data'}</span>
          </button>
        </div>

        {/* AI Spatial Model Parameters */}
        <div className="space-y-4 pt-4 border-t border-[#E2E7E1]">
          <h3 className="font-bold text-[#202923] text-sm flex items-center gap-2">
            <Sliders className="h-4 w-4 text-[#23483D]" />
            AI Spatial Synthesis Parameters
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[#202923] font-medium mb-1">Setback Boundary Tolerance</label>
              <input
                type="number"
                step="0.05"
                min="0.5"
                max="1.0"
                value={aiTolerance}
                onChange={(e) => setAiTolerance(Number(e.target.value))}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] font-mono focus:outline-none focus:border-[#23483D]"
              />
              <span className="text-[10px] text-[#68736C]">Strict adherence factor for CDA/LDA setback clearances</span>
            </div>

            <div>
              <label className="block text-[#202923] font-medium mb-1">Max Design Alternatives per Batch</label>
              <select className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]">
                <option value="2">2 Alternatives (Recommended)</option>
                <option value="3">3 Alternatives</option>
                <option value="4">4 Alternatives</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
