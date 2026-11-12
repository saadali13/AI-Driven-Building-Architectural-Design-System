import React, { useState } from 'react';
import { Layers, Info, CheckCircle2 } from 'lucide-react';
import { RoomSpec } from '../../types';

interface FloorPlanViewerProps {
  type: '5_marla_modern' | '10_marla_luxury' | '1_kanal_estate' | '7_marla_compact';
  title?: string;
  rooms?: RoomSpec[];
  showControls?: boolean;
  selectedFloor?: 'Ground' | 'First' | 'Rooftop';
  onFloorChange?: (floor: 'Ground' | 'First' | 'Rooftop') => void;
}

export const FloorPlanViewer: React.FC<FloorPlanViewerProps> = ({
  type = '10_marla_luxury',
  title = 'Architectural 2D Floor Plan',
  rooms = [],
  showControls = true,
  selectedFloor,
  onFloorChange,
}) => {
  const [internalFloor, setInternalFloor] = useState<'Ground' | 'First' | 'Rooftop'>(selectedFloor || 'Ground');
  const activeFloor = selectedFloor !== undefined ? selectedFloor : internalFloor;

  const setActiveFloor = (floor: 'Ground' | 'First' | 'Rooftop') => {
    setInternalFloor(floor);
    if (onFloorChange) onFloorChange(floor);
  };

  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);
  const [showGrid, setShowGrid] = useState(true);

  // Coordinated Architectural Floor Plan SVGs
  const renderFloorPlanSvg = () => {
    const isRooftop = activeFloor === 'Rooftop';
    const isFirst = activeFloor === 'First';

    return (
      <svg viewBox="0 0 740 920" className="w-full h-full max-h-[620px] drop-shadow-sm select-none">
        <defs>
          <pattern id="archGrid" width="24" height="24" patternUnits="userSpaceOnUse">
            <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#E2E7E1" strokeWidth="0.75" />
          </pattern>
          <pattern id="tileHatch" width="16" height="16" patternUnits="userSpaceOnUse">
            <path d="M 16 0 L 0 0 0 16" fill="none" stroke="#D1D5DB" strokeWidth="0.5" strokeDasharray="2 2" />
          </pattern>
          <pattern id="woodSlat" width="8" height="20" patternUnits="userSpaceOnUse">
            <rect width="6" height="20" fill="#FDE68A" fillOpacity="0.4" />
            <line x1="7" y1="0" x2="7" y2="20" stroke="#B45309" strokeWidth="0.8" />
          </pattern>
        </defs>

        {/* Paper Canvas Background */}
        <rect width="740" height="920" fill="#FFFFFF" rx="8" />
        {showGrid && <rect width="740" height="920" fill="url(#archGrid)" />}

        {/* Main Building Frame */}
        <g transform="translate(70, 70)">
          {/* Outer Statutory Plot Boundary (35ft x 65ft -> 600 x 780) */}
          <rect x="0" y="0" width="600" height="780" fill="#FAFAF8" stroke="#23483D" strokeWidth="2.5" />
          <text x="300" y="-18" fill="#23483D" textAnchor="middle" fontSize="12" fontFamily="JetBrains Mono, monospace" fontWeight="700">
            ROAD / STREET FRONTAGE (30 FT WIDE) &bull; NORTH FACING
          </text>

          {/* ---------------- ROOFTOP SLAB & MUMTY PLAN ---------------- */}
          {isRooftop ? (
            <g>
              {/* Parapet Wall Perimeter */}
              <rect x="25" y="25" width="550" height="730" fill="url(#tileHatch)" stroke="#1E293B" strokeWidth="4.5" />
              <rect x="33" y="33" width="534" height="714" fill="none" stroke="#64748B" strokeWidth="1.2" strokeDasharray="4 2" />

              {/* Mumty Stair Tower (West Side) */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Mumty Tower')}>
                <rect x="40" y="260" width="180" height="220" fill="#EEF4F0" stroke="#1E293B" strokeWidth="3" />
                <rect x="50" y="270" width="160" height="70" fill="#FFFFFF" stroke="#94A3B8" strokeWidth="1" />
                {/* Stair arrival flight lines */}
                {[0, 1, 2, 3, 4, 5].map((i) => (
                  <line key={i} x1="50" y1={270 + i * 14} x2="210" y2={270 + i * 14} stroke="#475569" strokeWidth="1" />
                ))}
                <text x="130" y="312" fill="#23483D" textAnchor="middle" fontSize="10" fontWeight="bold">DN &darr;</text>
                <text x="130" y="375" fill="#202923" textAnchor="middle" fontSize="13" fontWeight="bold">MUMTY STAIR TOWER</text>
                <text x="130" y="395" fill="#68736C" textAnchor="middle" fontSize="10" fontFamily="mono">12'-0" &times; 16'-0" &bull; FFL +22'-6"</text>
                {/* Weatherproof Door Swing */}
                <path d="M 170 480 A 40 40 0 0 0 210 440" fill="none" stroke="#23483D" strokeWidth="1.5" strokeDasharray="3 2" />
                <line x1="170" y1="480" x2="210" y2="480" stroke="#23483D" strokeWidth="2" />
              </g>

              {/* Overhead Concrete Water Tank (OHT) */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Water Tank')}>
                <rect x="40" y="100" width="180" height="130" fill="#E0F2FE" stroke="#0369A1" strokeWidth="2" />
                <line x1="40" y1="100" x2="220" y2="230" stroke="#0284C7" strokeWidth="0.8" strokeDasharray="3 3" />
                <line x1="40" y1="230" x2="220" y2="100" stroke="#0284C7" strokeWidth="0.8" strokeDasharray="3 3" />
                <text x="130" y="160" fill="#0369A1" textAnchor="middle" fontSize="12" fontWeight="bold">OVERHEAD WATER TANK</text>
                <text x="130" y="180" fill="#0284C7" textAnchor="middle" fontSize="10">RCC 1,500 GALLONS &bull; TOP LEVEL</text>
              </g>

              {/* Shaded Timber Pergola & Outdoor BBQ Terrace */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Pergola Lounge')}>
                <rect x="250" y="260" width="310" height="240" fill="url(#woodSlat)" stroke="#B45309" strokeWidth="2.5" />
                <rect x="260" y="270" width="290" height="30" fill="#78350F" stroke="#451A03" strokeWidth="1" />
                <text x="405" y="290" fill="#FFFFFF" textAnchor="middle" fontSize="10" fontWeight="bold">BUILT-IN GRANITE BBQ &amp; SINK COUNTER</text>

                {/* Outdoor Patio Table & 4 Chairs */}
                <circle cx="405" cy="380" r="34" fill="#FFFFFF" stroke="#B45309" strokeWidth="1.8" />
                <text x="405" y="384" fill="#B45309" textAnchor="middle" fontSize="9" fontWeight="bold">PATIO TABLE</text>
                <circle cx="405" cy="335" r="10" fill="#FEF3C7" stroke="#B45309" strokeWidth="1" />
                <circle cx="405" cy="425" r="10" fill="#FEF3C7" stroke="#B45309" strokeWidth="1" />
                <circle cx="360" cy="380" r="10" fill="#FEF3C7" stroke="#B45309" strokeWidth="1" />
                <circle cx="450" cy="380" r="10" fill="#FEF3C7" stroke="#B45309" strokeWidth="1" />

                <text x="405" y="475" fill="#78350F" textAnchor="middle" fontSize="12" fontWeight="bold">SHADED TIMBER PERGOLA &amp; ROOFTOP BBQ DECK</text>
                <text x="405" y="492" fill="#92400E" textAnchor="middle" fontSize="10">Anti-Skid Weatherproof Pavers &bull; 19'-0" &times; 15'-0"</text>
              </g>

              {/* Solar PV Array (10kW - 15kW Tier-1 Monocrystalline) */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Solar Array')}>
                <rect x="250" y="100" width="310" height="130" fill="#EFF6FF" stroke="#1D4ED8" strokeWidth="2" strokeDasharray="5 3" />
                {/* 12 Solar Panels Grid */}
                {[0, 1, 2, 3, 4, 5].map((c) => (
                  <React.Fragment key={c}>
                    <rect x={260 + c * 48} y="110" width="44" height="50" fill="#1E3A8A" stroke="#60A5FA" strokeWidth="0.8" />
                    <rect x={260 + c * 48} y="166" width="44" height="50" fill="#1E3A8A" stroke="#60A5FA" strokeWidth="0.8" />
                  </React.Fragment>
                ))}
                <text x="405" y="90" fill="#1D4ED8" textAnchor="middle" fontSize="11" fontWeight="bold">
                  12.5kW HIGH-EFFICIENCY SOLAR PV ARRAY (25&deg; SOUTH TILT)
                </text>
              </g>

              {/* Open Sky Terrace Deck & Rainwater Drainage */}
              <g>
                <text x="300" y="580" fill="#475569" textAnchor="middle" fontSize="16" fontWeight="bold" letterSpacing="1.5">
                  OPEN SKY TERRACE &bull; PORCELAIN TILES
                </text>
                <text x="300" y="605" fill="#64748B" textAnchor="middle" fontSize="11">
                  1:100 Rainwater Slope &rarr; 4" PVC Rainwater Downspouts at Corners
                </text>
                {/* Drainage arrows */}
                <path d="M 120 700 L 60 730 M 60 730 L 75 725 M 60 730 L 70 715" stroke="#0284C7" strokeWidth="1.5" fill="none" />
                <path d="M 480 700 L 540 730 M 540 730 L 525 725 M 540 730 L 530 715" stroke="#0284C7" strokeWidth="1.5" fill="none" />
              </g>

              {/* Rooftop Laundry & Servant Area (Rear) */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Rooftop Laundry')}>
                <rect x="40" y="600" width="180" height="135" fill="#F8FAFC" stroke="#475569" strokeWidth="2" />
                <rect x="50" y="615" width="60" height="45" fill="#E2E8F0" stroke="#64748B" strokeWidth="1" />
                <rect x="120" y="615" width="60" height="45" fill="#CBD5E1" stroke="#64748B" strokeWidth="1" />
                <text x="130" y="685" fill="#1E293B" textAnchor="middle" fontSize="11" fontWeight="bold">ROOFTOP LAUNDRY</text>
                <text x="130" y="702" fill="#64748B" textAnchor="middle" fontSize="9">Washing &amp; Drying Deck</text>
              </g>

              {/* OTS Void Curb */}
              <rect x="250" y="620" width="120" height="115" fill="#FFFFFF" stroke="#0284C7" strokeWidth="2" strokeDasharray="3 3" />
              <line x1="250" y1="620" x2="370" y2="735" stroke="#94A3B8" strokeWidth="1" />
              <line x1="250" y1="735" x2="370" y2="620" stroke="#94A3B8" strokeWidth="1" />
              <text x="310" y="675" fill="#0284C7" textAnchor="middle" fontSize="10" fontWeight="bold">OTS SHAFT VOID</text>
              <text x="310" y="692" fill="#0369A1" textAnchor="middle" fontSize="8">Raised 12" Curb</text>
            </g>
          ) : isFirst ? (
            /* ---------------- FIRST FLOOR PLAN ---------------- */
            <g>
              <rect x="25" y="25" width="550" height="730" fill="#FFFFFF" stroke="#1E293B" strokeWidth="3" />
              {/* Front Terrace */}
              <rect x="40" y="40" width="280" height="180" fill="#F0FDF4" stroke="#16A34A" strokeWidth="1.5" strokeDasharray="4 2" />
              <text x="180" y="130" fill="#16A34A" textAnchor="middle" fontSize="13" fontWeight="bold">FRONT SKY TERRACE</text>
              <text x="180" y="150" fill="#68736C" textAnchor="middle" fontSize="10">Over Car Porch &bull; Glass Railing</text>

              {/* Bedroom 3 (Upper Front Suite) */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Bedroom 3')}>
                <rect x="330" y="40" width="230" height="230" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="445" y="145" fill="#202923" textAnchor="middle" fontSize="14" fontWeight="bold">BEDROOM 3 (FRONT SUITE)</text>
                <text x="445" y="165" fill="#68736C" textAnchor="middle" fontSize="11">14'-0" &times; 15'-6" &bull; Attached Bath</text>
              </g>

              {/* Central Family Living Lobby */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Upper Lounge')}>
                <rect x="40" y="280" width="520" height="200" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="300" y="375" fill="#202923" textAnchor="middle" fontSize="15" fontWeight="bold">UPPER FAMILY LIVING &amp; LOBBY</text>
                <text x="300" y="398" fill="#68736C" textAnchor="middle" fontSize="11">24'-0" &times; 13'-6" &bull; Overlooking Lightwell</text>
              </g>

              {/* Bedroom 4 (Rear Master Suite) */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Bedroom 4')}>
                <rect x="40" y="490" width="250" height="245" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="165" y="605" fill="#202923" textAnchor="middle" fontSize="14" fontWeight="bold">BEDROOM 4 (MASTER)</text>
                <text x="165" y="625" fill="#68736C" textAnchor="middle" fontSize="11">15'-0" &times; 16'-0" &bull; Walk-In Closet</text>
              </g>

              {/* Bedroom 5 (Rear Suite) */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Bedroom 5')}>
                <rect x="300" y="490" width="260" height="245" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="430" y="605" fill="#202923" textAnchor="middle" fontSize="14" fontWeight="bold">BEDROOM 5</text>
                <text x="430" y="625" fill="#68736C" textAnchor="middle" fontSize="11">14'-0" &times; 15'-0" &bull; Attached Bath</text>
              </g>
            </g>
          ) : (
            /* ---------------- GROUND FLOOR PLAN ---------------- */
            <g>
              <rect x="25" y="25" width="550" height="730" fill="#FFFFFF" stroke="#1E293B" strokeWidth="3" />
              {/* Double Car Porch */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Car Porch')}>
                <rect x="40" y="40" width="310" height="220" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="195" y="145" fill="#202923" textAnchor="middle" fontSize="14" fontWeight="bold">CAR PORCH (2 SEDANS/SUVs)</text>
                <text x="195" y="165" fill="#68736C" textAnchor="middle" fontSize="11">19'-0" &times; 15'-0" &bull; Clearance 9'-6"</text>
              </g>

              {/* Formal Drawing Room & Powder */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Drawing Room')}>
                <rect x="360" y="40" width="200" height="220" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="460" y="145" fill="#202923" textAnchor="middle" fontSize="14" fontWeight="bold">DRAWING ROOM</text>
                <text x="460" y="165" fill="#68736C" textAnchor="middle" fontSize="11">13'-0" &times; 16'-0" &bull; Powder Room</text>
              </g>

              {/* Central Family Living & Open Gourmet Kitchen */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Living Lounge')}>
                <rect x="40" y="270" width="520" height="210" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="230" y="370" fill="#202923" textAnchor="middle" fontSize="15" fontWeight="bold">CENTRAL FAMILY TV LOUNGE</text>
                <text x="230" y="392" fill="#68736C" textAnchor="middle" fontSize="11">22'-0" &times; 14'-0" &bull; Double Height Void</text>

                {/* Open Show Kitchen Island & Dirty Scullery */}
                <rect x="380" y="285" width="165" height="180" fill="#EEF4F0" stroke="#23483D" strokeWidth="1.5" />
                <text x="462" y="365" fill="#23483D" textAnchor="middle" fontSize="12" fontWeight="bold">GOURMET KITCHEN</text>
                <text x="462" y="385" fill="#68736C" textAnchor="middle" fontSize="9">+ Dirty Cooking Scullery</text>
              </g>

              {/* Ground Master Bedroom Suite */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Ground Master')}>
                <rect x="40" y="490" width="250" height="245" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="165" y="605" fill="#202923" textAnchor="middle" fontSize="14" fontWeight="bold">GROUND MASTER SUITE</text>
                <text x="165" y="625" fill="#68736C" textAnchor="middle" fontSize="11">15'-0" &times; 16'-0" &bull; Luxury Dressing/Bath</text>
              </g>

              {/* Bedroom 2 Suite */}
              <g className="cursor-pointer" onClick={() => setSelectedRoom('Bedroom 2')}>
                <rect x="300" y="490" width="260" height="245" fill="#F8FAFC" stroke="#1E293B" strokeWidth="2.5" />
                <text x="430" y="605" fill="#202923" textAnchor="middle" fontSize="14" fontWeight="bold">GUEST BEDROOM 2</text>
                <text x="430" y="625" fill="#68736C" textAnchor="middle" fontSize="11">14'-0" &times; 15'-0" &bull; Ensuite Bath</text>
              </g>
            </g>
          )}

          {/* North Compass Rose */}
          <g transform="translate(530, 45)">
            <circle cx="0" cy="0" r="20" fill="#FFFFFF" stroke="#23483D" strokeWidth="1.5" />
            <polygon points="0,-14 4,-2 0,-5 -4,-2" fill="#23483D" />
            <polygon points="0,14 4,2 0,5 -4,2" fill="#94A3B8" />
            <text x="0" y="-18" fill="#23483D" textAnchor="middle" fontSize="9" fontWeight="bold">N</text>
          </g>

          {/* Architectural Graphic Scale (1:100 Metric & Imperial) */}
          <g transform="translate(40, 755)">
            <rect x="0" y="0" width="140" height="3" fill="#23483D" />
            <text x="0" y="-5" fill="#68736C" fontSize="9" fontFamily="mono">0'</text>
            <text x="70" y="-5" fill="#68736C" fontSize="9" fontFamily="mono">15'</text>
            <text x="140" y="-5" fill="#68736C" fontSize="9" fontFamily="mono">30' (SCALE 1:100)</text>
          </g>
        </g>
      </svg>
    );
  };

  return (
    <div className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden shadow-xs flex flex-col w-full">
      {/* Top Architectural Toolbar */}
      <div className="px-4 py-2.5 bg-[#F7F7F2] border-b border-[#E2E7E1] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-[#23483D] animate-pulse" />
          <span className="text-xs font-bold text-[#202923] tracking-wide">{title}</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#EEF4F0] text-[#23483D] font-mono border border-[#DCE7DE] font-semibold">
            ARCHITECTURAL CAD VECTOR
          </span>
        </div>

        {/* Floor Switcher */}
        <div className="flex items-center bg-white rounded-xl p-1 border border-[#E2E7E1] text-xs">
          {(['Ground', 'First', 'Rooftop'] as const).map((floor) => (
            <button
              key={floor}
              onClick={() => setActiveFloor(floor)}
              className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                activeFloor === floor
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'text-[#68736C] hover:text-[#202923] hover:bg-[#EEF4F0]'
              }`}
            >
              {floor} {floor === 'Rooftop' ? 'Slab' : 'Floor'}
            </button>
          ))}
        </div>

        {/* Tools */}
        {showControls && (
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowGrid(!showGrid)}
              title="Toggle Architectural Grid"
              className={`p-1.5 rounded-lg text-xs transition-colors ${
                showGrid ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:bg-[#EEF4F0]'
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* SVG Canvas Container */}
      <div className="p-4 flex items-center justify-center bg-[#FAFAF8] overflow-hidden min-h-[460px]">
        {renderFloorPlanSvg()}
      </div>

      {/* Selected Room Detail Strip */}
      {selectedRoom && (
        <div className="px-4 py-2 bg-[#EEF4F0] border-t border-[#DCE7DE] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-[#23483D] font-semibold">
            <CheckCircle2 className="h-4 w-4" />
            <span>Selected Element: {selectedRoom}</span>
          </div>
          <button
            onClick={() => setSelectedRoom(null)}
            className="text-[11px] text-[#68736C] hover:text-[#202923] font-medium"
          >
            Clear selection
          </button>
        </div>
      )}
    </div>
  );
};
