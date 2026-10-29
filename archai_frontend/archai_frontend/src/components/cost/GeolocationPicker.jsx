import React, { useState, useEffect } from 'react';
import { 
  MapPin, 
  Navigation, 
  Globe, 
  Search, 
  ShieldCheck, 
  Check, 
  ChevronDown, 
  Sparkles, 
  Radio, 
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { REGIONAL_MARKETS, findNearestMarket } from '../../utils/costEngine';

export default function GeolocationPicker({ 
  selectedLocationKey = 'islamabad', 
  onLocationChange,
  onCoordinatesDetected 
}) {
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectionSuccess, setDetectionSuccess] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [activeCoordinates, setActiveCoordinates] = useState(null);
  const [autoDetectMode, setAutoDetectMode] = useState(true);

  // Auto-detect location on initial load
  useEffect(() => {
    handleAutoDetectLocation();
  }, []);

  const handleAutoDetectLocation = () => {
    if (!navigator.geolocation) {
      // Fall back to default Islamabad
      if (onLocationChange) onLocationChange('islamabad');
      return;
    }

    setIsDetecting(true);
    setDetectionSuccess(false);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setActiveCoordinates({ lat: latitude, lng: longitude });

        // Match nearest municipal market hub
        const matchedKey = findNearestMarket(latitude, longitude);
        setIsDetecting(false);
        setDetectionSuccess(true);
        setAutoDetectMode(true);

        if (onLocationChange) onLocationChange(matchedKey);
        if (onCoordinatesDetected) onCoordinatesDetected({ lat: latitude, lng: longitude, key: matchedKey });
      },
      (error) => {
        console.warn('Geolocation access denied or unavailable, using municipal default:', error.message);
        setIsDetecting(false);
        setAutoDetectMode(false);
      },
      { timeout: 8000, enableHighAccuracy: true }
    );
  };

  const handleSelectManual = (key) => {
    setAutoDetectMode(false);
    setDropdownOpen(false);
    const market = REGIONAL_MARKETS[key];
    if (market) {
      setActiveCoordinates(market.coordinates);
      if (onLocationChange) onLocationChange(key);
      if (onCoordinatesDetected) onCoordinatesDetected(market.coordinates);
    }
  };

  const currentMarket = REGIONAL_MARKETS[selectedLocationKey] || REGIONAL_MARKETS.islamabad;

  const filteredMarkets = Object.values(REGIONAL_MARKETS).filter((m) =>
    m.city.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.region.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.authority.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="bg-white border border-slate-200/90 rounded-3xl p-6 shadow-xs space-y-4 select-none">
      
      {/* Header & Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-2xs">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span>Project Geolocation &amp; Municipal Zone</span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                Live Geocoded
              </span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Rates automatically sync with local municipal by-laws &amp; material indices.
            </p>
          </div>
        </div>

        {/* Auto Detect Button */}
        <button
          type="button"
          onClick={handleAutoDetectLocation}
          disabled={isDetecting}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 cursor-pointer border ${
            isDetecting
              ? 'bg-blue-50 text-blue-600 border-blue-200'
              : autoDetectMode
              ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
              : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border-slate-200'
          }`}
          title="Detect current GPS location"
        >
          {isDetecting ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Detecting GPS...</span>
            </>
          ) : (
            <>
              <Navigation className="w-3.5 h-3.5 text-current" />
              <span>Auto-Detect GPS</span>
            </>
          )}
        </button>
      </div>

      {/* Selected Location Card & Manual Dropdown Override */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Active Market Authority Badge Card */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-start justify-between gap-3">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-base font-black text-slate-900 tracking-tight">
                {currentMarket.city}, {currentMarket.country}
              </span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                {currentMarket.region}
              </span>
            </div>
            <p className="text-xs font-semibold text-slate-600 truncate">
              {currentMarket.authority}
            </p>
            <div className="flex items-center gap-3 pt-1 text-[11px] font-mono text-slate-400">
              <span>Lat: {activeCoordinates?.lat ? activeCoordinates.lat.toFixed(4) : currentMarket.coordinates.lat}</span>
              <span>•</span>
              <span>Lng: {activeCoordinates?.lng ? activeCoordinates.lng.toFixed(4) : currentMarket.coordinates.lng}</span>
            </div>
          </div>

          <div className="w-8 h-8 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-emerald-600 shadow-2xs shrink-0">
            <Check className="w-4 h-4" />
          </div>
        </div>

        {/* Searchable Manual Override Selector */}
        <div className="relative">
          <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-500 block mb-1.5">
            Manual Region Override
          </label>

          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="w-full flex items-center justify-between p-3.5 bg-white border border-slate-200 rounded-2xl text-left text-xs font-bold text-slate-900 hover:border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 cursor-pointer shadow-2xs transition"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <Globe className="w-4 h-4 text-blue-600 shrink-0" />
              <span className="truncate">{currentMarket.city} ({currentMarket.authority.split('(')[0].trim()})</span>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 right-0 top-full mt-2 bg-white border border-slate-200 rounded-2xl p-2 shadow-2xl z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              {/* Search Bar inside Dropdown */}
              <div className="relative mb-2 px-1">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search city, province, municipal code..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600"
                />
              </div>

              {/* List */}
              <div className="max-h-56 overflow-y-auto space-y-1">
                {filteredMarkets.map((m) => {
                  const isSelected = m.key === selectedLocationKey;
                  return (
                    <button
                      key={m.key}
                      type="button"
                      onClick={() => handleSelectManual(m.key)}
                      className={`w-full flex items-center justify-between p-2.5 rounded-xl text-xs transition cursor-pointer text-left ${
                        isSelected
                          ? 'bg-blue-50 text-blue-700 font-bold border border-blue-200'
                          : 'text-slate-700 hover:bg-slate-50 font-medium'
                      }`}
                    >
                      <div>
                        <span className="block font-bold">{m.city}, {m.country}</span>
                        <span className="text-[10px] text-slate-500">{m.authority}</span>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-blue-600" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
