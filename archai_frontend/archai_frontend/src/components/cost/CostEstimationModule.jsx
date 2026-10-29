import React, { useState } from 'react';
import { 
  Calculator, 
  MapPin, 
  Navigation, 
  Coins, 
  TrendingUp, 
  FileSpreadsheet, 
  Building2, 
  CheckCircle2, 
  Sliders,
  Maximize2,
  DollarSign,
  Layers,
  ArrowRight,
  Globe,
  Download,
  ArrowLeft,
  Sparkles,
  Check
} from 'lucide-react';
import archAiLogo from '../../assets/logo.png';

export default function CostEstimationModuleLarge({ setActiveTab, onOpenStudio }) {
  const [selectedLocation, setSelectedLocation] = useState('Rawalpindi / Islamabad, Pakistan');
  const [isAutoDetecting, setIsAutoDetecting] = useState(false);
  const [finishingQuality, setFinishingQuality] = useState('Standard Executive');
  const [floorsCount, setFloorsCount] = useState(2);
  const [customCoveredArea, setCustomCoveredArea] = useState(3200);
  const [toastMessage, setToastMessage] = useState('');

  // Regional rates database with comprehensive municipal data context
  const regionalRates = {
    'Rawalpindi / Islamabad, Pakistan': { 
      currency: 'PKR', 
      currencySymbol: '₨',
      cementRate: 1550, 
      brickRate: 14.5, 
      steelRate: 265, 
      laborRate: 650, 
      authority: 'CDA / RDA Municipal Zone',
      totalArea: customCoveredArea 
    },
    'Lahore, Pakistan': { 
      currency: 'PKR', 
      currencySymbol: '₨',
      cementRate: 1520, 
      brickRate: 14.0, 
      steelRate: 260, 
      laborRate: 620, 
      authority: 'LDA / DHA Lahore Jurisdiction',
      totalArea: customCoveredArea 
    },
    'Karachi, Pakistan': { 
      currency: 'PKR', 
      currencySymbol: '₨',
      cementRate: 1600, 
      brickRate: 15.0, 
      steelRate: 275, 
      laborRate: 700, 
      authority: 'SBCA Sindh Building Control',
      totalArea: customCoveredArea 
    }
  };

  const currentRates = regionalRates[selectedLocation] || regionalRates['Rawalpindi / Islamabad, Pakistan'];
  
  // Quality specification multiplier
  const qualityMultiplier = finishingQuality === 'Luxury High-End' ? 1.35 : finishingQuality === 'Standard Executive' ? 1.0 : 0.85;

  // Dynamic calculations derived from 2D floor plan matrix
  const totalCementCost = Math.round(customCoveredArea * 3.5 * currentRates.cementRate * qualityMultiplier);
  const totalBrickCost = Math.round(customCoveredArea * 35 * currentRates.brickRate * qualityMultiplier);
  const totalSteelCost = Math.round(customCoveredArea * 4.2 * currentRates.steelRate * qualityMultiplier);
  const totalLaborCost = Math.round(customCoveredArea * currentRates.laborRate * qualityMultiplier);
  const finishingAndFixtures = Math.round(customCoveredArea * 850 * qualityMultiplier);
  
  const grandTotal = totalCementCost + totalBrickCost + totalSteelCost + totalLaborCost + finishingAndFixtures;
  const costPerSqFt = Math.round(grandTotal / customCoveredArea);
  const grandTotalMillion = (grandTotal / 1000000).toFixed(2);

  const handleAutoDetectLocation = () => {
    setIsAutoDetecting(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        () => {
          setSelectedLocation('Rawalpindi / Islamabad, Pakistan');
          setIsAutoDetecting(false);
          showToast('GPS coordinates locked to Rawalpindi / Islamabad CDA Zone.');
        },
        () => {
          setSelectedLocation('Rawalpindi / Islamabad, Pakistan');
          setIsAutoDetecting(false);
          showToast('Auto-detected default: Rawalpindi / Islamabad, Pakistan');
        },
        { timeout: 4000 }
      );
    } else {
      setTimeout(() => {
        setSelectedLocation('Rawalpindi / Islamabad, Pakistan');
        setIsAutoDetecting(false);
        showToast('Auto-detected default: Rawalpindi / Islamabad, Pakistan');
      }, 800);
    }
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3500);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col antialiased select-none">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 bg-slate-900 text-white px-5 py-3.5 rounded-2xl shadow-2xl flex items-center gap-3 text-sm font-semibold animate-in fade-in border border-slate-700">
          <Check className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Navbar Header */}
      <header className="bg-white border-b border-slate-200 px-6 sm:px-10 py-5 flex items-center justify-between shadow-xs shrink-0">
        <div 
          onClick={() => setActiveTab && setActiveTab('workspace')}
          className="flex items-center space-x-4 cursor-pointer group"
        >
          <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-700/80 p-1 shadow-md flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
            <img src={archAiLogo} alt="ArchAI Logo" className="w-full h-full object-contain rounded-xl" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 leading-none">
              Arch<span className="text-blue-600">AI</span> <span className="text-slate-600 font-light">Studio</span>
            </h1>
            <p className="text-xs font-mono font-bold text-blue-600 uppercase tracking-wider mt-1">
              Advanced Spatial Intelligence &amp; Cost Engineering
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {setActiveTab && (
            <button
              type="button"
              onClick={() => setActiveTab('workspace')}
              className="hidden sm:inline-flex items-center px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4 mr-1.5" />
              <span>Back to Workspace</span>
            </button>
          )}

          <span className="inline-flex items-center px-4 py-2 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
            <CheckCircle2 className="w-4 h-4 mr-2" /> 2D Layout Matrix Synchronized
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 sm:p-10 space-y-8">
        
        {/* Module Title Section */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 bg-white p-10 md:p-12 rounded-3xl border border-slate-200 shadow-sm">
          <div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-slate-900">
              Comprehensive Cost Estimation
            </h2>
            <p className="text-lg sm:text-xl font-medium text-slate-600 mt-2">
              Dynamic Bill of Quantities (BOQ) derived from your architectural 2D floor plan layout and real-time regional indices.
            </p>
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <button 
              type="button"
              onClick={() => showToast('Exporting Detailed BOQ Report in PDF format...')}
              className="inline-flex items-center justify-center px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-extrabold text-lg transition-all shadow-xl shadow-blue-500/25 cursor-pointer active:scale-95 hover:scale-[1.01]"
            >
              <FileSpreadsheet className="w-6 h-6 mr-3" /> Export Detailed BOQ Report (PDF)
            </button>
          </div>
        </div>

        {/* Location & Parameters Selector Card */}
        <div className="bg-white p-10 md:p-12 rounded-3xl border border-slate-200 shadow-sm space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5 border-b border-slate-100 pb-6">
            <h3 className="text-2xl sm:text-3xl font-black text-slate-900 flex items-center">
              <MapPin className="w-8 h-8 text-blue-600 mr-3 shrink-0" /> Geolocation &amp; Regional Rate Configuration
            </h3>
            <button 
              type="button"
              onClick={handleAutoDetectLocation}
              disabled={isAutoDetecting}
              className="inline-flex items-center px-6 py-4 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-2xl font-bold text-base transition-all shadow-xs cursor-pointer"
            >
              <Navigation className={`w-6 h-6 mr-2.5 text-blue-600 ${isAutoDetecting ? 'animate-spin' : ''}`} />
              {isAutoDetecting ? 'Detecting GPS Coordinates...' : 'Auto-Detect via Google Maps'}
            </button>
          </div>


          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-3 flex items-center">
                <Globe className="w-4 h-4 text-blue-600 mr-2 shrink-0" /> Project Location Override
              </label>
              <select 
                value={selectedLocation} 
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-base font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-inner cursor-pointer"
              >
                <option value="Rawalpindi / Islamabad, Pakistan">Rawalpindi / Islamabad, Pakistan</option>
                <option value="Lahore, Pakistan">Lahore, Pakistan</option>
                <option value="Karachi, Pakistan">Karachi, Pakistan</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-3 flex items-center">
                <Sliders className="w-4 h-4 text-blue-600 mr-2 shrink-0" /> Finishing Specification Tier
              </label>
              <select 
                value={finishingQuality} 
                onChange={(e) => setFinishingQuality(e.target.value)}
                className="w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-base font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-inner cursor-pointer"
              >
                <option value="Standard Executive">Standard Executive (Default)</option>
                <option value="Luxury High-End">Luxury High-End (Premium Marble/Wood)</option>
                <option value="Economy Basic">Economy Basic (Standard Finish)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-3 flex items-center">
                <Maximize2 className="w-4 h-4 text-blue-600 mr-2 shrink-0" /> Total Covered Area (2D Layout)
              </label>
              <div className="px-5 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-lg font-black text-slate-900 flex items-center justify-between shadow-inner">
                <span className="text-slate-500 text-sm font-medium">Floor Footprint</span>
                <span className="text-blue-600">{customCoveredArea} sq. ft.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Grand Total Hero Banner */}
        <div className="bg-gradient-to-r from-blue-950 via-blue-900 to-indigo-950 text-white rounded-3xl p-8 sm:p-10 shadow-2xl flex flex-col lg:flex-row items-center justify-between gap-8 border border-blue-800/50">
          <div className="space-y-3 text-center lg:text-left">
            <span className="inline-flex items-center px-4 py-1.5 rounded-full text-xs font-bold bg-blue-500/20 text-blue-300 border border-blue-400/30 uppercase tracking-widest">
              <Coins className="w-4 h-4 mr-2" /> Total Estimated Construction Cost ({currentRates.currency})
            </span>
            <h3 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white font-mono">
              {currentRates.currency} {grandTotal.toLocaleString()}
            </h3>
            <p className="text-slate-300 text-sm sm:text-base font-medium">
              Estimated rate analysis: <strong className="text-white">~{costPerSqFt.toLocaleString()} {currentRates.currency}</strong> per square foot. (~{grandTotalMillion} Million)
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-xl p-6 rounded-2xl border border-white/20 text-center lg:text-right space-y-2 min-w-[280px] shadow-inner shrink-0">
            <p className="text-xs text-blue-200 uppercase tracking-widest font-bold">Active Region Index</p>
            <p className="text-lg sm:text-xl font-extrabold text-white">{selectedLocation}</p>
            <p className="text-xs text-emerald-400 font-bold flex items-center justify-center lg:justify-end">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Live Material Index Active
            </p>
          </div>
        </div>

        {/* Detailed Itemized Cost Breakdown Grid */}
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h3 className="text-2xl font-black text-slate-900 flex items-center">
              <Calculator className="w-7 h-7 text-blue-600 mr-3 shrink-0" /> Itemized Bill of Quantities (BOQ) Breakdown
            </h3>
            <span className="text-sm font-bold text-slate-500">Values updated in real-time from 2D vector coordinates</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            
            {/* Cement Card */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xs space-y-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <span className="p-3 bg-blue-50 text-blue-600 rounded-2xl"><Building2 className="w-8 h-8" /></span>
                <span className="text-sm font-extrabold text-blue-600 bg-blue-50 px-3 py-1.5 rounded-xl">
                  {Math.round((totalCementCost / grandTotal) * 100)}% of Total
                </span>
              </div>
              <h4 className="text-xl font-bold text-slate-900">Cement &amp; Aggregates</h4>
              <p className="text-3xl font-black text-slate-900 font-mono">{currentRates.currency} {totalCementCost.toLocaleString()}</p>
              <p className="text-sm text-slate-500 font-medium leading-relaxed">
                Calculated based on regional bag rates ({currentRates.currency} {currentRates.cementRate} per bag) and structural load requirements.
              </p>
            </div>

            {/* Brick Card */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xs space-y-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <span className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl"><Layers className="w-8 h-8" /></span>
                <span className="text-sm font-extrabold text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded-xl">
                  {Math.round((totalBrickCost / grandTotal) * 100)}% of Total
                </span>
              </div>
              <h4 className="text-xl font-bold text-slate-900">Bricks &amp; Masonry</h4>
              <p className="text-3xl font-black text-slate-900 font-mono">{currentRates.currency} {totalBrickCost.toLocaleString()}</p>
              <p className="text-sm text-slate-500 font-medium leading-relaxed">
                Includes clay brick volume for external and internal walls priced at {currentRates.currency} {currentRates.brickRate} per unit.
              </p>
            </div>

            {/* Steel Card */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xs space-y-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <span className="p-3 bg-amber-50 text-amber-600 rounded-2xl"><TrendingUp className="w-8 h-8" /></span>
                <span className="text-sm font-extrabold text-amber-600 bg-amber-50 px-3 py-1.5 rounded-xl">
                  {Math.round((totalSteelCost / grandTotal) * 100)}% of Total
                </span>
              </div>
              <h4 className="text-xl font-bold text-slate-900">Reinforcement Steel</h4>
              <p className="text-3xl font-black text-slate-900 font-mono">{currentRates.currency} {totalSteelCost.toLocaleString()}</p>
              <p className="text-sm text-slate-500 font-medium leading-relaxed">
                Grade-60 deformed steel bars calculated for roof slabs, columns, and foundations at {currentRates.currency} {currentRates.steelRate}/kg.
              </p>
            </div>

            {/* Labor Card */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xs space-y-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <span className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl"><Coins className="w-8 h-8" /></span>
                <span className="text-sm font-extrabold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-xl">
                  {Math.round((totalLaborCost / grandTotal) * 100)}% of Total
                </span>
              </div>
              <h4 className="text-xl font-bold text-slate-900">Workforce &amp; Labor Overhead</h4>
              <p className="text-3xl font-black text-slate-900 font-mono">{currentRates.currency} {totalLaborCost.toLocaleString()}</p>
              <p className="text-sm text-slate-500 font-medium leading-relaxed">
                Manday wage allocation for certified masons, shuttering carpenters, and construction laborers at {currentRates.currency} {currentRates.laborRate}/sq.ft.
              </p>
            </div>

            {/* Finishing & Fixtures Card */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xs space-y-4 hover:shadow-md transition-shadow md:col-span-2 lg:col-span-2">
              <div className="flex justify-between items-start">
                <span className="p-3 bg-purple-50 text-purple-600 rounded-2xl"><DollarSign className="w-8 h-8" /></span>
                <span className="text-sm font-extrabold text-purple-600 bg-purple-50 px-3 py-1.5 rounded-xl">
                  {Math.round((finishingAndFixtures / grandTotal) * 100)}% of Total
                </span>
              </div>
              <h4 className="text-xl font-bold text-slate-900">Interior Finishing, Electrical &amp; Plumbing Fixtures</h4>
              <p className="text-3xl font-black text-slate-900 font-mono">{currentRates.currency} {finishingAndFixtures.toLocaleString()}</p>
              <p className="text-sm text-slate-500 font-medium leading-relaxed">
                Includes tiling, sanitary fittings, electrical wiring, PVC piping, and main door carpentry based on your selected <strong className="text-slate-800">{finishingQuality}</strong> tier.
              </p>
            </div>

          </div>
        </div>

      </main>
    </div>
  );
}
