import React, { useState } from 'react';
import { 
  Building2, 
  Layers, 
  Calculator, 
  ShieldCheck, 
  Wand2, 
  FolderKanban, 
  Hammer, 
  Palette, 
  Briefcase, 
  TrendingUp, 
  CheckCircle2, 
  Clock, 
  MapPin, 
  Box, 
  FileText, 
  Download, 
  Sparkles, 
  ArrowRight, 
  Home, 
  Plus, 
  AlertCircle,
  HardHat,
  Compass,
  FileCode,
  DollarSign,
  Maximize2,
  Sliders,
  RefreshCw,
  Eye
} from 'lucide-react';
import { ROLES } from '../../context/AuthContext';

/* =========================================================================
   1. ARCHITECT DASHBOARD VIEW
   ========================================================================= */
export function ArchitectDashboardView({ onOpenStudio, onNewDesign, setActiveNav }) {
  return (
    <div className="space-y-6">
      {/* Quick Tool Strips */}
      <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 flex items-center justify-center font-bold">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Parametric CAD & BIM Workspace</h3>
            <p className="text-xs text-slate-500">Layer management, vector CAD drafting, and spatial compliance schedules.</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onNewDesign}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-xs cursor-pointer"
          >
            <Wand2 className="w-3.5 h-3.5" />
            <span>AI Plan Generator</span>
          </button>
          <button
            type="button"
            onClick={() => onOpenStudio && onOpenStudio('5marla')}
            className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl transition flex items-center gap-1.5 cursor-pointer"
          >
            <Box className="w-3.5 h-3.5 text-blue-600" />
            <span>3D Model Studio</span>
          </button>
        </div>
      </div>

      {/* Architect Project Revisions & BIM Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Revisions & CAD Versions */}
        <div className="lg:col-span-2 p-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileCode className="w-4 h-4 text-blue-600" />
              <span>Active Architectural Revisions & IFC/DWG Exports</span>
            </h4>
            <span className="text-xs font-mono text-slate-400">4 Active Projects</span>
          </div>

          <div className="space-y-3">
            {[
              { name: '5 Marla Villa - Sector G-13 Islamabad', rev: 'Rev 2.1 (AIA Standard)', layers: '8 CAD Layers', status: 'Approved for BIM', date: '2h ago', model: '5marla' },
              { name: '10 Marla Spanish Villa - DHA Lahore', rev: 'Rev 1.4 (Cantilever Added)', layers: '12 CAD Layers', status: 'In Review', date: 'Yesterday', model: '10marla' },
              { name: '1 Kanal Farmhouse - Gulberg Greens', rev: 'Rev 3.0 (Courtyard Verified)', layers: '14 CAD Layers', status: 'Approved for BIM', date: '3 days ago', model: '1kanal' },
            ].map((proj, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-700 flex items-center justify-between gap-3 text-xs">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-white truncate">{proj.name}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-bold shrink-0">{proj.rev}</span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                    <span>{proj.layers}</span>
                    <span>•</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{proj.status}</span>
                    <span>•</span>
                    <span>{proj.date}</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onOpenStudio && onOpenStudio(proj.model)}
                  className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-700 hover:bg-slate-100 text-slate-700 dark:text-slate-200 font-semibold text-xs border border-slate-200 dark:border-slate-600 transition cursor-pointer shrink-0"
                >
                  Inspect CAD
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* CDA/LDA Architectural Checklist */}
        <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs space-y-4">
          <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>CDA / LDA Bylaw Checklist</span>
          </h4>

          <div className="space-y-3 text-xs">
            {[
              { rule: 'Front 5ft Clear Setback', status: 'Verified OK', pass: true },
              { rule: 'Rear 3ft Setback for Ventilation', status: 'Verified OK', pass: true },
              { rule: 'Max Ground Coverage <= 80%', status: '74.2% Compliant', pass: true },
              { rule: 'OTS Lightwell Minimum 8 sq ft', status: '12 sq ft OK', pass: true },
              { rule: 'Car Porch Clearance >= 8ft 6in', status: '9ft 0in Clear', pass: true },
            ].map((chk, cIdx) => (
              <div key={cIdx} className="flex items-center justify-between text-xs">
                <span className="text-slate-600 dark:text-slate-300">{chk.rule}</span>
                <span className="font-mono text-emerald-600 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{chk.status}</span>
                </span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

/* =========================================================================
   2. CONSTRUCTION PROFESSIONAL DASHBOARD VIEW
   ========================================================================= */
export function ConstructionDashboardView({ setActiveNav, onOpenStudio }) {
  const [steelPrice, setSteelPrice] = useState(264);
  const [cementPrice, setCementPrice] = useState(1320);
  const [brickPrice, setBrickPrice] = useState(14.5);

  // Dynamic 5 Marla calculation based on custom input
  const totalGreyEst = Math.round((2150 * 1350) + (steelPrice * 4200) + (cementPrice * 620));

  return (
    <div className="space-y-6">
      {/* Site Header */}
      <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 flex items-center justify-center font-bold">
            <HardHat className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Site Operations & Material BOQ Center</h3>
            <p className="text-xs text-slate-500">Live steel & cement market rates with real-time bill of quantities overrides.</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setActiveNav && setActiveNav('cost-estimation')}
          className="px-4 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 text-white font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-xs cursor-pointer"
        >
          <Calculator className="w-3.5 h-3.5" />
          <span>Open Full BOQ Estimator</span>
        </button>
      </div>

      {/* Editable Material Rates Interactive Bar */}
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-950 text-white rounded-3xl shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-amber-400" />
              <span>Interactive Material Price Override (Pakistani Rupees)</span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">Adjust market rates to immediately update 5 Marla grey structure estimates.</p>
          </div>
          <span className="text-xs font-mono font-bold text-amber-300">
            Est. Grey Total: ₨ {(totalGreyEst / 1000000).toFixed(2)}M
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Steel (60-Grade):</span>
              <span className="font-mono text-white font-bold">₨ {steelPrice} / kg</span>
            </div>
            <input 
              type="range" 
              min="240" 
              max="300" 
              value={steelPrice} 
              onChange={e => setSteelPrice(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer" 
            />
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Cement (Grade-53):</span>
              <span className="font-mono text-white font-bold">₨ {cementPrice} / bag</span>
            </div>
            <input 
              type="range" 
              min="1200" 
              max="1500" 
              value={cementPrice} 
              onChange={e => setCementPrice(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer" 
            />
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Red Bricks:</span>
              <span className="font-mono text-white font-bold">₨ {brickPrice} / pc</span>
            </div>
            <input 
              type="range" 
              min="12" 
              max="18" 
              step="0.5" 
              value={brickPrice} 
              onChange={e => setBrickPrice(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer" 
            />
          </div>
        </div>
      </div>

      {/* Active Construction Sites */}
      <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs space-y-4">
        <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
          <FolderKanban className="w-4 h-4 text-amber-600" />
          <span>Active Construction Sites & Pour Schedules</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { site: 'Sector F-8/3 Villa', phase: 'Roof Slab 2 Pouring', progress: 68, contractor: 'Kamran & Sons Civil', due: 'Thursday, 9:00 AM' },
            { site: 'DHA Phase 2 Estate', phase: 'Brick Masonry & Lintels', progress: 42, contractor: 'Apex Builders LHR', due: 'Next Monday' },
          ].map((site, sIdx) => (
            <div key={sIdx} className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 dark:text-white text-sm">{site.site}</span>
                <span className="text-[11px] font-mono font-bold text-amber-600">{site.progress}% Complete</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">Stage: {site.phase}</p>
              <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full" style={{ width: `${site.progress}%` }} />
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                <span>Contractor: {site.contractor}</span>
                <span className="font-mono text-slate-600 dark:text-slate-300 font-semibold">{site.due}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

/* =========================================================================
   3. INTERIOR DESIGNER DASHBOARD VIEW
   ========================================================================= */
export function DesignerDashboardView({ onOpenStudio }) {
  return (
    <div className="space-y-6">
      <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 flex items-center justify-center font-bold">
            <Palette className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Spatial Staging & Material Palettes</h3>
            <p className="text-xs text-slate-500">2.5D staging, photometric PBR material libraries, and lighting moodboards.</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => onOpenStudio && onOpenStudio('5marla')}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-xs cursor-pointer"
        >
          <Box className="w-3.5 h-3.5" />
          <span>Launch 3D Staging</span>
        </button>
      </div>

      {/* Curated Material Swatches */}
      <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs space-y-4">
        <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
          <Sparkles className="w-4 h-4 text-cyan-600" />
          <span>Curated PBR Material Textures (Living & Bedroom)</span>
        </h4>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { name: 'Italian Carrara Marble', tone: 'Polished 120x60', color: 'bg-slate-100 border-slate-300' },
            { name: 'Fluted American Oak', tone: 'Warm Natural Wood', color: 'bg-amber-100 border-amber-300' },
            { name: 'Matte Charcoal Metal', tone: 'Powder-coated 2mm', color: 'bg-slate-800 border-slate-700 text-white' },
            { name: 'Backlit Emerald Onyx', tone: 'Translucent 18mm', color: 'bg-emerald-100 border-emerald-300' },
          ].map((mat, mIdx) => (
            <div key={mIdx} className="p-4 rounded-2xl border bg-slate-50 dark:bg-slate-800/60 flex flex-col justify-between group hover:border-cyan-400 transition cursor-pointer">
              <div className={`h-20 rounded-xl mb-3 border shadow-inner flex items-center justify-center font-bold text-xs ${mat.color}`}>
                Texture Preview
              </div>
              <h5 className="font-bold text-xs text-slate-900 dark:text-white">{mat.name}</h5>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5">{mat.tone}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* =========================================================================
   4. REAL ESTATE DEVELOPER DASHBOARD VIEW
   ========================================================================= */
export function DeveloperDashboardView({ onOpenStudio, setActiveNav }) {
  return (
    <div className="space-y-6">
      <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 flex items-center justify-center font-bold">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Commercial Land & Sector Master Planning</h3>
            <p className="text-xs text-slate-500">Multi-plot subdivision yield, plot inventory, and gross development feasibility.</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setActiveNav && setActiveNav('new-design')}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-xs cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add New Sector Plan</span>
        </button>
      </div>

      {/* Sector Subdivisions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {[
          { name: 'Al-Haram Enclave (50 Kanal)', plots: '84 Units', status: 'CDA Approved', yield: '₨ 840M GDV' },
          { name: 'Pine Valley Heights (20 Kanal)', plots: '36 Luxury Villas', status: 'Under Infrastructure', yield: '₨ 520M GDV' },
          { name: 'Margalla View Commercial Podium', plots: '12 Retail Units', status: 'Feasibility Review', yield: '₨ 310M GDV' },
        ].map((sec, idx) => (
          <div key={idx} className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-600 border border-indigo-200">
              {sec.status}
            </span>
            <h4 className="font-bold text-slate-900 dark:text-white text-sm">{sec.name}</h4>
            <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800">
              <span>{sec.plots}</span>
              <strong className="text-slate-900 dark:text-white font-mono">{sec.yield}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
