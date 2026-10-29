import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Wand2, 
  ArrowRight, 
  Cpu, 
  Building2, 
  RefreshCw,
  Layers,
  MapPin,
  CheckCircle2,
  HardHat,
  Palette,
  Briefcase,
  ShieldCheck,
  Home,
  Compass,
  FileCode,
  Zap,
  Sliders,
  ChevronRight,
  TrendingUp,
  Clock,
  Activity,
  Award
} from 'lucide-react';
import heroRenderImage from '../../assets/login_brand.png';
import { ROLES } from '../../context/AuthContext';

// Comprehensive Plot Presets with Professional Architectural Specifications
const PLOT_PRESETS = [
  { 
    size: '3 Marla', 
    dims: '20′×35′',
    label: '3 Marla Compact Urban', 
    prompt: '3 Marla (20x35 ft) compact modern 3-story urban residence with 3 ensuite bedrooms, lightwell OTS, open American kitchen, and rooftop terrace in Islamabad' 
  },
  { 
    size: '5 Marla', 
    dims: '25′×45′',
    label: '5 Marla Contemporary Villa', 
    prompt: '5 Marla (25x45 ft) luxury contemporary double-story villa with 3 ensuite bedrooms, open American kitchen, car porch, rear ventilation lawn, and OTS' 
  },
  { 
    size: '7 Marla', 
    dims: '30′×53′',
    label: '7 Marla Executive Townhouse', 
    prompt: '7 Marla (30x53 ft) executive double-story townhouse with 4 bedrooms, double-height family lounge, dining room, covered car porch, and rear patio in DHA' 
  },
  { 
    size: '10 Marla', 
    dims: '35′×65′',
    label: '10 Marla Spanish Executive', 
    prompt: '10 Marla (35x65 ft) Spanish hacienda estate with 4 master suites, courtyard fountain, servant quarter, 2-car garage, and front landscaped lawn' 
  },
  { 
    size: '15 Marla', 
    dims: '40′×85′',
    label: '15 Marla Classical Mansion', 
    prompt: '15 Marla (40x85 ft) classical modern mansion with 5 luxury suites, double-height foyer, formal drawing room, dual kitchen, and landscaped BBQ lawn' 
  },
  { 
    size: '1 Kanal', 
    dims: '50′×90′',
    label: '1 Kanal Luxury Estate', 
    prompt: '1 Kanal (50x90 ft) ultra-modern luxury villa with 5 ensuite bedrooms, swimming pool, home theater, basement, dual car porch, and servant quarters in Bahria Town' 
  }
];

// Popular Architectural Styles
const POPULAR_STYLES = [
  'Modern Contemporary',
  'Spanish Hacienda',
  'Minimalist Japandi',
  'Classic Victorian',
  'Brutalist Concrete',
  'Neo-Classical Luxury',
  'Tropical Modern'
];

export default function HeroGreetingBanner({ 
  architectName = 'Saad',
  userRole = ROLES.HOMEOWNER,
  onStartNewProject,
  onQuickGenerate
}) {
  const [prompt, setPrompt] = useState(PLOT_PRESETS[1].prompt);
  const [selectedPlot, setSelectedPlot] = useState('5 Marla');
  const [selectedStyle, setSelectedStyle] = useState('Modern Contemporary');
  const [isGenerating, setIsGenerating] = useState(false);

  // Update prompt whenever plot preset or style is clicked
  const handleSelectPlotPreset = (preset) => {
    setSelectedPlot(preset.size);
    // Replace or set prompt with current selected style
    const basePrompt = preset.prompt;
    setPrompt(`${basePrompt} [Style: ${selectedStyle}]`);
  };

  const handleSelectStyle = (styleName) => {
    setSelectedStyle(styleName);
    // Dynamically update prompt text with the new style
    let updated = prompt;
    if (updated.includes('[Style:')) {
      updated = updated.replace(/\[Style:[^\]]+\]/, `[Style: ${styleName}]`);
    } else {
      updated = `${updated.trim()} [Style: ${styleName}]`;
    }
    setPrompt(updated);
  };

  const handleSynthesize = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      if (onQuickGenerate) {
        onQuickGenerate(prompt);
      }
    }, 800);
  };

  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#0B132B] via-[#0E1A38] to-[#12224A] border border-blue-500/25 shadow-2xl text-white transition-all">
      
      {/* Background Architectural Watermark & Glow */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-15 mix-blend-luminosity pointer-events-none scale-105"
        style={{ backgroundImage: `url(${heroRenderImage})` }}
      />
      <div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Content Container with Medium Proportions */}
      <div className="relative p-5 sm:p-7 z-10 space-y-5">
        
        {/* Top Meta Header: Status Pills & Live Market Indicators */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-xs font-bold text-blue-200 backdrop-blur-md">
              <Home className="w-3.5 h-3.5 text-cyan-400" />
              <span>Residential Studio</span>
            </span>

            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-400/30 text-[11px] font-mono text-emerald-300 backdrop-blur-md">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>CDA / LDA / Bahria Bylaws Synced</span>
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] font-mono text-cyan-200/90 bg-slate-900/60 px-3 py-1 rounded-full border border-cyan-500/20 backdrop-blur-md">
            <Zap className="w-3 h-3 text-cyan-400 shrink-0" />
            <span>PKR Index: Steel ₨ 264/kg • Cement ₨ 1,320/bag</span>
          </div>
        </div>

        {/* Studio Headline (Balanced, Medium Proportions) & Live Project Status Card */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-center">
          
          {/* Left: Greeting & Description */}
          <div className="lg:col-span-8 space-y-1.5">
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight leading-snug">
              Welcome to your architectural command center,{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 via-sky-200 to-teal-200">
                {architectName}
              </span>.
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal max-w-2xl">
              Synthesize generative 2D CAD floor plans, verify municipal setback bylaws, and compute live Pakistani construction budgets in PKR.
            </p>
          </div>

          {/* Right: Live Project Status & Progress Tracker Card */}
          <div className="lg:col-span-4 bg-white/5 border border-white/10 rounded-2xl p-3.5 backdrop-blur-md space-y-2.5">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                <span>Active Project Status</span>
              </div>
              <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold border border-emerald-500/30">
                85% Complete
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs text-white font-bold">
                <span className="truncate">5 Marla Contemporary Villa</span>
                <span className="text-[10px] text-slate-400 font-mono">BIM LOD-300</span>
              </div>
              {/* Progress Bar */}
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-1.5 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-teal-400 h-1.5 rounded-full transition-all duration-500" 
                  style={{ width: '85%' }}
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-[10px] text-slate-300 pt-1 border-t border-white/10">
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" /> CDA Setback Approved
              </span>
              <span className="font-mono text-cyan-300 font-semibold">₨ 7.85M Est.</span>
            </div>
          </div>

        </div>

        {/* 1. Common Plot Sizes: 3 Marla, 5 Marla, 7 Marla, 10 Marla, 15 Marla, 1 Kanal */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs text-slate-300 font-medium">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span className="font-bold text-white">Common Plot Sizes &amp; Instant Presets:</span>
            <span className="text-slate-400 text-[11px] hidden sm:inline">(Click to auto-populate prompt)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {PLOT_PRESETS.map((preset) => {
              const isSelected = selectedPlot === preset.size;
              return (
                <button
                  key={preset.size}
                  type="button"
                  onClick={() => handleSelectPlotPreset(preset)}
                  className={`px-3 py-2 rounded-xl text-left transition-all cursor-pointer border ${
                    isSelected
                      ? 'bg-blue-600/30 border-blue-400 text-white shadow-xs ring-1 ring-blue-400'
                      : 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300 hover:text-white'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-black text-xs text-white">{preset.size}</span>
                    <span className="text-[10px] font-mono text-cyan-300">{preset.dims}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 block truncate mt-0.5">{preset.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. Architectural Prompt Bar & Style Selector */}
        <div className="bg-slate-900/95 backdrop-blur-2xl border border-white/15 rounded-2xl p-3 shadow-xl space-y-2.5">
          
          {/* Main Prompt Text Input */}
          <div className="flex items-center gap-3 px-2 py-0.5 text-slate-300">
            <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-400/30 flex items-center justify-center shrink-0 text-cyan-300">
              <Wand2 className="w-3.5 h-3.5" />
            </div>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSynthesize();
              }}
              placeholder="Enter architectural requirements or select a preset above..."
              className="bg-transparent text-white text-xs sm:text-sm placeholder-slate-400 w-full focus:outline-none font-medium py-1"
            />
          </div>

          {/* Sub-toolbar: Popular Styles & Action Buttons */}
          <div className="pt-2 border-t border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            
            {/* Style Selector Chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0 scrollbar-none">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider shrink-0 mr-1 flex items-center gap-1">
                <Sliders className="w-3 h-3 text-cyan-400" />
                Popular Styles:
              </span>
              {POPULAR_STYLES.map((style) => (
                <button
                  key={style}
                  type="button"
                  onClick={() => handleSelectStyle(style)}
                  className={`text-[11px] px-2.5 py-1 rounded-lg transition-all font-medium shrink-0 cursor-pointer ${
                    selectedStyle === style
                      ? 'bg-blue-600 text-white font-bold shadow-xs border border-blue-400'
                      : 'bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5'
                  }`}
                >
                  {style}
                </button>
              ))}
            </div>

            {/* Actions: 4-Step Wizard & Generate Blueprint */}
            <div className="flex items-center gap-2 w-full md:w-auto justify-end shrink-0">
              <button
                type="button"
                onClick={onStartNewProject}
                className="px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs flex items-center justify-center gap-1.5 transition border border-white/15 cursor-pointer hover:border-white/30 shrink-0"
                title="Launch guided step-by-step form"
              >
                <span>4-Step Form</span>
              </button>

              <button
                type="button"
                onClick={handleSynthesize}
                disabled={isGenerating}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-teal-600 hover:from-blue-500 hover:to-teal-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-blue-600/30 cursor-pointer disabled:opacity-50 active:scale-95 shrink-0"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-200" />
                    <span>Synthesizing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
                    <span>Generate Blueprint</span>
                    <ArrowRight className="w-3 h-3 text-blue-200" />
                  </>
                )}
              </button>
            </div>

          </div>

        </div>

      </div>

    </div>
  );
}
