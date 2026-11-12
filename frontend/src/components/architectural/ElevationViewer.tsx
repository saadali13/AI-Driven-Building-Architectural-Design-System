import React from 'react';
import { Sun, ShieldCheck } from 'lucide-react';
import { ArchitecturalStyle } from '../../types';

interface ElevationViewerProps {
  style?: ArchitecturalStyle;
  floors?: number;
  widthFt?: number;
}

export const ElevationViewer: React.FC<ElevationViewerProps> = ({
  style = 'Modern Contemporary',
  floors = 2,
  widthFt = 35,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col">
      <div className="px-4 py-3 bg-slate-950 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-amber-400" />
          <span className="text-sm font-semibold text-white">2D Front Elevation & Facade</span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
            {style} ({widthFt} ft Frontage)
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Sun className="h-4 w-4 text-amber-400" />
          <span>Natural Daylight Vector: 10:30 AM East</span>
        </div>
      </div>

      <div className="relative p-6 flex items-center justify-center bg-gradient-to-b from-sky-950/40 via-slate-900 to-slate-950 min-h-[460px]">
        {/* Architectural Elevation SVG */}
        <svg viewBox="0 0 700 500" className="w-full max-w-2xl drop-shadow-2xl select-none">
          <defs>
            {/* Cladding texture pattern */}
            <pattern id="stoneCladding" width="40" height="20" patternUnits="userSpaceOnUse">
              <rect width="40" height="20" fill="#334155" />
              <line x1="0" y1="10" x2="40" y2="10" stroke="#1e293b" strokeWidth="1" />
              <line x1="20" y1="0" x2="20" y2="10" stroke="#1e293b" strokeWidth="1" />
              <line x1="40" y1="10" x2="40" y2="20" stroke="#1e293b" strokeWidth="1" />
            </pattern>
            {/* Wooden louver pattern */}
            <pattern id="woodLouvers" width="10" height="40" patternUnits="userSpaceOnUse">
              <rect width="10" height="40" fill="#78350f" />
              <line x1="0" y1="0" x2="0" y2="40" stroke="#451a03" strokeWidth="2" />
            </pattern>
            {/* Glass gradient */}
            <linearGradient id="glassReflection" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
              <stop offset="50%" stopColor="#0284c7" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#0369a1" stopOpacity="0.5" />
            </linearGradient>
          </defs>

          {/* Sky background backdrop */}
          <rect x="0" y="0" width="700" height="450" fill="none" />

          {/* Ground Base / Street Line */}
          <line x1="40" y1="440" x2="660" y2="440" stroke="#64748b" strokeWidth="4" />
          <rect x="40" y="442" width="620" height="20" fill="#1e293b" />
          <text x="350" y="456" fill="#94a3b8" textAnchor="middle" fontSize="10" fontFamily="JetBrains Mono">
            FINISH ROAD LEVEL (FRL: ±0'-0")
          </text>

          {/* House Plinth: +2'-6" level */}
          <rect x="90" y="420" width="520" height="20" fill="#475569" stroke="#64748b" strokeWidth="1.5" />
          <text x="70" y="433" fill="#38bdf8" textAnchor="end" fontSize="9" fontFamily="JetBrains Mono">
            +2'-6" PLINTH
          </text>

          {/* GROUND FLOOR MASS (Height: 11 ft -> 130px) */}
          <rect x="100" y="270" width="500" height="150" fill="#1e293b" stroke="#0f172a" strokeWidth="2" />

          {/* Ground Porch Canopy / Cantilever */}
          <rect x="100" y="290" width="220" height="130" fill="#0f172a" fillOpacity="0.7" stroke="#334155" strokeWidth="2" />
          {/* Main Car Porch Gate */}
          <rect x="110" y="320" width="190" height="100" fill="#1e293b" stroke="#14b8a6" strokeWidth="2" />
          <line x1="110" y1="345" x2="300" y2="345" stroke="#0d9488" strokeWidth="1.5" />
          <line x1="110" y1="370" x2="300" y2="370" stroke="#0d9488" strokeWidth="1.5" />
          <line x1="110" y1="395" x2="300" y2="395" stroke="#0d9488" strokeWidth="1.5" />
          <text x="205" y="375" fill="#5eead4" textAnchor="middle" fontSize="11" fontWeight="bold">STEEL MAIN GATE</text>

          {/* Ground Floor Drawing Room Window with Stone Cladding Feature */}
          <rect x="340" y="270" width="260" height="150" fill="url(#stoneCladding)" stroke="#475569" strokeWidth="2" />
          <rect x="360" y="295" width="160" height="100" fill="url(#glassReflection)" stroke="#0ea5e9" strokeWidth="3" />
          <line x1="440" y1="295" x2="440" y2="395" stroke="#0284c7" strokeWidth="2" />
          <text x="440" y="350" fill="#f8fafc" textAnchor="middle" fontSize="10" fontWeight="bold">TEMPERED TINTED GLASS</text>

          {/* FIRST FLOOR MASS (Height: 11 ft -> 130px) */}
          {floors >= 2 && (
            <>
              {/* Floor Slab Division Line */}
              <rect x="80" y="260" width="540" height="15" fill="#0f172a" stroke="#38bdf8" strokeWidth="1.5" />
              <text x="70" y="272" fill="#38bdf8" textAnchor="end" fontSize="9" fontFamily="JetBrains Mono">
                +13'-6" FIRST FLR
              </text>

              {/* First Floor Walls */}
              <rect x="100" y="125" width="500" height="135" fill="#0f172a" stroke="#1e293b" strokeWidth="2" />

              {/* Master Bedroom Balcony with Glass Railing */}
              <rect x="110" y="145" width="200" height="115" fill="none" stroke="#64748b" strokeWidth="1" />
              {/* Glass Slider */}
              <rect x="125" y="145" width="170" height="90" fill="url(#glassReflection)" stroke="#0284c7" strokeWidth="2" />
              {/* Glass Balcony Railing */}
              <rect x="110" y="215" width="200" height="45" fill="#38bdf8" fillOpacity="0.3" stroke="#38bdf8" strokeWidth="1.5" />
              <text x="210" y="242" fill="#e0f2fe" textAnchor="middle" fontSize="10" fontWeight="bold">CANTILEVER GLASS BALCONY</text>

              {/* Wooden Louver Architectural Screen (Right Elevation) */}
              <rect x="330" y="125" width="120" height="135" fill="url(#woodLouvers)" stroke="#92400e" strokeWidth="2" />
              <text x="390" y="195" fill="#fef3c7" textAnchor="middle" fontSize="10" fontWeight="bold">TIMBER LOUVERS</text>

              {/* High Slim Picture Windows */}
              <rect x="470" y="145" width="110" height="90" fill="url(#glassReflection)" stroke="#38bdf8" strokeWidth="2" />
            </>
          )}

          {/* ROOFTOP PARAPET & MUMTY (+24'-6" level) */}
          <rect x="80" y="110" width="540" height="18" fill="#1e293b" stroke="#94a3b8" strokeWidth="1" />
          <text x="70" y="122" fill="#38bdf8" textAnchor="end" fontSize="9" fontFamily="JetBrains Mono">
            +25'-0" ROOF SLAB
          </text>

          {/* Mumty Tower */}
          <rect x="160" y="45" width="150" height="65" fill="#0f172a" stroke="#38bdf8" strokeWidth="2" />
          <text x="235" y="80" fill="#38bdf8" textAnchor="middle" fontSize="11" fontWeight="bold">MUMTY STAIR TOWER</text>
          {/* Parapet Wall */}
          <rect x="90" y="80" width="520" height="30" fill="none" stroke="#64748b" strokeWidth="2" strokeDasharray="6 3" />
          <text x="540" y="70" fill="#94a3b8" textAnchor="end" fontSize="9">3'-6" PARAPET</text>

          {/* Dimension Guidelines & Levels */}
          <line x1="625" y1="50" x2="625" y2="440" stroke="#475569" strokeWidth="1" strokeDasharray="3 3" />
          <text x="635" y="250" fill="#cbd5e1" fontSize="11" fontFamily="JetBrains Mono">H = 34' TOTAL</text>
        </svg>

        {/* Floating Facade Highlights */}
        <div className="absolute top-6 right-6 bg-slate-950/90 backdrop-blur border border-slate-800 rounded-xl p-3 text-xs space-y-1.5 shadow-xl">
          <p className="font-semibold text-teal-400 flex items-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5" /> Verified Architectural Elements
          </p>
          <div className="text-slate-300 space-y-0.5">
            <p>• Textured Travertine Stone Accent</p>
            <p>• Double-Glazed Low-E Aluminum Windows</p>
            <p>• Weather-Shield Asian White Paint</p>
            <p>• Concealed Rooftop Gutter Downspouts</p>
          </div>
        </div>
      </div>
    </div>
  );
};
