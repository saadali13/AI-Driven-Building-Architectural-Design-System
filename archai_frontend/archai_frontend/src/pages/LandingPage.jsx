import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Box, 
  ArrowRight, 
  Check, 
  CheckCircle2, 
  Layers, 
  Compass, 
  Download, 
  BarChart3, 
  ShieldCheck, 
  Ruler, 
  Eye, 
  Sliders, 
  Zap, 
  MapPin, 
  Building, 
  Building2, 
  Image, 
  RotateCw, 
  ChevronDown, 
  ChevronLeft,
  ChevronRight, 
  LayoutGrid, 
  DollarSign, 
  FileText, 
  Calculator, 
  PenTool, 
  HardHat, 
  CheckSquare2,
  Hammer,
  Star,
  LayoutDashboard,
  Wand2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LandingPage({ setActiveTab, onOpenStudio }) {
  const { user, isAuthenticated } = useAuth();
  // ---------------------------------------------------------------------------
  // 1. HERO FANNED CARDS STACK (Exact floorplanai.net Architecture with 5 Cards)
  // ---------------------------------------------------------------------------
  const HERO_CARDS = [
    {
      id: 'technical',
      title: 'Technical 2D CAD',
      tag: 'TECHNICAL',
      status: 'READY',
      dotColor: 'bg-blue-600',
      image: '/images/styles/technical.png',
      spec: 'Dimensioned structural floor plan with wall thicknesses & spans',
      plot: 'AIA Layered DWG'
    },
    {
      id: 'twopointfive',
      title: '2.5D Furnished Plan',
      tag: '2.5D COLOR',
      status: 'READY',
      dotColor: 'bg-emerald-500',
      image: '/images/styles/2-5d.png',
      spec: 'Color-illustrated presentation plan with wood & marble textures',
      plot: '10 Marla Executive'
    },
    {
      id: 'cutaway',
      title: '3D Cutaway Villa',
      tag: '3D VILLA',
      status: 'READY',
      dotColor: 'bg-indigo-500',
      image: '/images/styles/ex-3br.png',
      spec: '3-bedroom residence with open patio, ensuite baths, and porch',
      plot: '3 Beds · 110 m²'
    },
    {
      id: 'loft',
      title: 'Architectural Loft',
      tag: 'ARCH LOFT',
      status: 'READY',
      dotColor: 'bg-purple-500',
      image: '/images/styles/ex-loft.png',
      spec: 'Double-height ceiling mezzanine with industrial wood trusses',
      plot: 'Urban Penthouse'
    },
    {
      id: 'isometric',
      title: '3D Isometric Model',
      tag: '3D ISOMETRY',
      status: 'READY',
      dotColor: 'bg-amber-500',
      image: '/images/styles/isometric.png',
      spec: 'Procedural 3D solid mesh with ambient daylight shadows',
      plot: '5 Marla Contemporary'
    }
  ];

  const [activeCardIdx, setActiveCardIdx] = useState(0);
  const [isAutoPlayPaused, setIsAutoPlayPaused] = useState(false);

  // Auto-changing floor plans on a smooth timer (pauses when user hovers/interacts)
  useEffect(() => {
    if (isAutoPlayPaused) return;
    const interval = setInterval(() => {
      setActiveCardIdx(prev => (prev + 1) % HERO_CARDS.length);
    }, 3200);
    return () => clearInterval(interval);
  }, [isAutoPlayPaused, HERO_CARDS.length]);

  // Card navigation handlers
  const handlePrevCard = () => {
    setActiveCardIdx(prev => (prev - 1 + HERO_CARDS.length) % HERO_CARDS.length);
  };
  const handleNextCard = () => {
    setActiveCardIdx(prev => (prev + 1) % HERO_CARDS.length);
  };

  // ---------------------------------------------------------------------------
  // 2. LIVE GENERATOR SANDBOX (floorplanai.net 3 Styles: technical, 2-5d, isometric)
  // ---------------------------------------------------------------------------
  const [generatorMode, setGeneratorMode] = useState('floorplan'); // 'floorplan' | '3d'
  const [templateMode, setTemplateMode] = useState('custom'); // 'template' | 'custom'
  const [promptText, setPromptText] = useState(
    'Create a 5 Marla modern double-story residence with 3 bedrooms, open American kitchen, drawing room, attached baths, and front car porch.'
  );
  const [selectedStyle, setSelectedStyle] = useState('2-5d'); // 'technical' | '2-5d' | 'isometric'
  const [selectedPlot, setSelectedPlot] = useState('5marla'); // '3marla' | '5marla' | '10marla' | '1kanal'
  const [aspectRatio, setAspectRatio] = useState('4:3');
  const [resolution, setResolution] = useState('2K');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showPlotDetails, setShowPlotDetails] = useState(false);
  const [bedrooms, setBedrooms] = useState(3);
  const [bathrooms, setBathrooms] = useState(3);
  const [generationCount, setGenerationCount] = useState(1);

  // Quick preset pills for prompt
  const PROMPT_PRESETS = [
    { label: '5 Marla Modern', text: '5 Marla modern double-story residence with 3 bedrooms, open American kitchen, drawing room, attached baths, and front car porch.', plot: '5marla', beds: 3, baths: 3 },
    { label: '10 Marla Luxury', text: '10 Marla executive villa, 4 bedrooms, double-height lounge, dirty kitchen, maid room, 2-car garage, and landscaped terrace.', plot: '10marla', beds: 4, baths: 5 },
    { label: '1 Kanal Estate', text: '1 Kanal luxury mansion with 5 master suites, swimming pool, home theater, central courtyard lawn, and guard quarters.', plot: '1kanal', beds: 5, baths: 6 },
    { label: '3 Marla Smart', text: '3 Marla compact urban townhouse, 2 bedrooms, open galley kitchen, rooftop patio, and covered motorbike parking.', plot: '3marla', beds: 2, baths: 2 },
    { label: 'Studio Apartment', text: 'Open plan modern studio apartment, Murphy bed, kitchen island, private balcony, walk-in bath.', plot: '3marla', beds: 1, baths: 1 },
  ];

  const handleApplyPreset = (preset) => {
    setPromptText(preset.text);
    setSelectedPlot(preset.plot);
    setBedrooms(preset.beds);
    setBathrooms(preset.baths);
  };

  const handleSimulateGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      setGenerationCount(prev => prev + 1);
    }, 750);
  };

  // ---------------------------------------------------------------------------
  // 3. ARCHAI REAL FEATURE 1: Interactive 2D CAD & Spatial Zoning Studio
  // ---------------------------------------------------------------------------
  const [activeZone, setActiveZone] = useState('lounge');

  const SPATIAL_ZONES = [
    { id: 'lounge', name: 'Living Lounge', dimensions: "22' × 16'", area: '352 sq ft', bylaw: 'CDA Clear Span', wall: '9" Double Brick' },
    { id: 'master', name: 'Master Suite', dimensions: "14' × 16'", area: '224 sq ft', bylaw: 'Rear Ventilation Setback', wall: '9" Exterior Wall' },
    { id: 'kitchen', name: 'American Kitchen', dimensions: "12' × 14'", area: '168 sq ft', bylaw: 'Shaft Ventilation Pass', wall: '4.5" Partition' },
    { id: 'drawing', name: 'Guest Drawing', dimensions: "14' × 14'", area: '196 sq ft', bylaw: 'Direct Foyer Entrance', wall: '9" Structural Brick' },
    { id: 'porch', name: 'Front Car Porch', dimensions: "14' × 20'", area: '280 sq ft', bylaw: '5ft Compulsory Front Setback', wall: 'Reinforced Column' }
  ];

  // ---------------------------------------------------------------------------
  // 4. ARCHAI REAL FEATURE 2: Pakistani Construction Cost & BOQ Calculator (PKR)
  // ---------------------------------------------------------------------------
  const [boqPlotCategory, setBoqPlotCategory] = useState('5marla');

  const BOQ_DATA = {
    '3marla': {
      label: '3 Marla (675 sq ft)',
      coveredArea: '1,350 sq ft (Double Story)',
      steelTons: '3.8 Tons Grade-60',
      steelCost: '₨ 1,045,000',
      cementBags: '420 Bags DG/Fauji',
      cementCost: '₨ 596,400',
      sandBricks: '₨ 720,000 (Ravi Sand + 24k Bricks)',
      greyTotal: '₨ 3,150,000',
      turnkeyTotal: '₨ 5,400,000'
    },
    '5marla': {
      label: '5 Marla (1,125 sq ft)',
      coveredArea: '2,250 sq ft (Double Story)',
      steelTons: '6.2 Tons Grade-60',
      steelCost: '₨ 1,705,000',
      cementBags: '710 Bags DG/Fauji',
      cementCost: '₨ 1,008,200',
      sandBricks: '₨ 1,180,000 (Chenab Aggregate + 38k Bricks)',
      greyTotal: '₨ 4,850,000',
      turnkeyTotal: '₨ 8,900,000'
    },
    '10marla': {
      label: '10 Marla (2,250 sq ft)',
      coveredArea: '3,800 sq ft (Executive Villa)',
      steelTons: '10.5 Tons Grade-60',
      steelCost: '₨ 2,887,500',
      cementBags: '1,200 Bags DG/Fauji',
      cementCost: '₨ 1,704,000',
      sandBricks: '₨ 1,950,000 (62k A-Grade Bricks)',
      greyTotal: '₨ 8,400,000',
      turnkeyTotal: '₨ 15,600,000'
    },
    '1kanal': {
      label: '1 Kanal (4,500 sq ft)',
      coveredArea: '5,500 sq ft (Luxury Mansion)',
      steelTons: '16.8 Tons Grade-60',
      steelCost: '₨ 4,620,000',
      cementBags: '1,850 Bags DG/Fauji',
      cementCost: '₨ 2,627,000',
      sandBricks: '₨ 2,900,000 (95k A-Grade Bricks)',
      greyTotal: '₨ 13,200,000',
      turnkeyTotal: '₨ 24,500,000'
    }
  };

  const activeBoq = BOQ_DATA[boqPlotCategory];

  return (
    <div className="min-h-screen bg-paper text-slate-900 font-sans select-none overflow-x-hidden">
      
      {/* Blueprint Grid Atmosphere Background */}
      <div className="fixed inset-0 blueprint-grid pointer-events-none opacity-45 z-0"></div>

      <main className="relative z-10 pt-28 pb-20">

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 1: HERO (FloorPlanAI.net Exact Fanned Cards Stack)         */}
        {/* ------------------------------------------------------------------ */}
        <section className="relative px-5 md:px-8 max-w-7xl mx-auto pb-16 md:pb-24 border-b border-line">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-10 items-center">
            
            {/* Left Column: Headlines & Action Buttons */}
            <div className="lg:col-span-6 space-y-6 text-left">
              
              {/* Engineering Pill Badge */}
              <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-blue-200 bg-blue-50/90 text-xs font-mono text-blue-800 shadow-2xs">
                <Sparkles className="w-3.5 h-3.5 text-blue-600 animate-pulse" />
                <span className="font-semibold uppercase tracking-wider">Text to Floor Plan AI + 3D Model Generator · v2.4</span>
              </div>

              {/* Main Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-[62px] font-bold text-slate-950 tracking-tight leading-[1.05]">
                Type a sentence.<br />
                Get a{' '}
                <span className="relative inline-block whitespace-nowrap text-blue-700">
                  floor plan AI
                  <svg className="absolute -bottom-2 left-0 w-full" viewBox="0 0 220 12" fill="none">
                    <path d="M2 8 Q 60 2 110 6 T 218 5" stroke="#10b981" strokeWidth="3.2" strokeLinecap="round" />
                  </svg>
                </span>.
              </h1>

              {/* Subtitle */}
              <p className="text-base sm:text-lg text-slate-600 max-w-xl leading-relaxed">
                AI floor plan generator and 3D architectural model creator. Turn a sentence into a 2D CAD plan or a realistic 3D model in seconds — built for homeowners, architects, and builders with automated Pakistani construction BOQ calculations.
              </p>

              {/* CTAs */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5 pt-2">
                {isAuthenticated ? (
                  <>
                    <button
                      type="button"
                      onClick={() => setActiveTab('workspace', 'dashboard')}
                      className="group inline-flex items-center justify-center gap-2.5 h-12 px-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-sm transition-all shadow-md shadow-blue-500/25 hover:-translate-y-0.5 cursor-pointer"
                    >
                      <LayoutDashboard className="w-4 h-4 text-cyan-300" />
                      <span>Open Workspace Dashboard</span>
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                    </button>

                    <button
                      type="button"
                      onClick={() => setActiveTab('workspace', 'new-design')}
                      className="inline-flex items-center justify-center gap-2 h-12 px-5 rounded-xl border border-blue-200 bg-blue-50 hover:bg-blue-100/80 text-blue-800 font-semibold text-sm transition-all shadow-2xs hover:-translate-y-0.5 cursor-pointer"
                    >
                      <Wand2 className="w-4 h-4 text-blue-600" />
                      <span>Start New Design Generator</span>
                    </button>
                  </>
                ) : (
                  <a
                    href="#generator"
                    className="group inline-flex items-center justify-center gap-2.5 h-12 px-6 rounded-xl bg-slate-950 hover:bg-blue-700 text-white font-semibold text-sm transition-all shadow-blueprint hover:-translate-y-0.5 cursor-pointer"
                  >
                    <span>Generate your first plan</span>
                    <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                  </a>
                )}

                <a
                  href="#examples"
                  className="inline-flex items-center justify-center gap-2 h-12 px-5 rounded-xl border border-line bg-white hover:border-blue-400 hover:text-blue-700 text-slate-800 font-semibold text-sm transition-all shadow-2xs hover:-translate-y-0.5 cursor-pointer"
                >
                  <span>See examples</span>
                </a>
              </div>

              {/* Specs Pills */}
              <div className="pt-2 flex flex-wrap items-center gap-x-3.5 gap-y-2 font-mono text-xs uppercase tracking-wider text-slate-500">
                <span className="inline-flex items-center gap-1.5 font-bold text-emerald-700">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  {isAuthenticated ? 'Pro AI Studio Active' : '1 free plan on sign-in'}
                </span>
                <span className="text-slate-300">·</span>
                <span>2D plans + 3D models</span>
                <span className="text-slate-300">·</span>
                <span>Download PNG, DXF or GLB</span>
              </div>
            </div>

            {/* Right Column: 3 Fanned Cards Stack (Matches User Screenshot Exactly) */}
            <div className="lg:col-span-6 relative flex flex-col items-center">
              
              <div 
                className="relative w-full max-w-lg lg:max-w-xl mx-auto select-none pt-4 pb-2"
                onMouseEnter={() => setIsAutoPlayPaused(true)}
                onMouseLeave={() => setIsAutoPlayPaused(false)}
              >
                
                {/* Subtle Atmosphere Backdrop Glow */}
                <div className="absolute -inset-4 -z-10 rounded-[32px] bg-gradient-to-br from-blue-100/50 via-paper to-emerald-100/40 blur-2xl pointer-events-none"></div>

                {/* 5 Fanned Cards Stack (Slides smoothly across positions just like floorplanai.net) */}
                <div className="relative aspect-[5/4] w-full flex items-center justify-center">
                  {HERO_CARDS.map((card, idx) => {
                    const isActive = idx === activeCardIdx;
                    const isRight = idx === (activeCardIdx + 1) % HERO_CARDS.length;
                    const isLeft = idx === (activeCardIdx - 1 + HERO_CARDS.length) % HERO_CARDS.length;

                    // Exact floorplanai.net dynamic slide & rotation classes:
                    let cardPosition = '';
                    if (isActive) {
                      cardPosition = 'z-30 left-1/2 top-[16%] w-[65%] -translate-x-1/2 rotate-0 scale-100 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.22)] opacity-100';
                    } else if (isRight) {
                      cardPosition = 'z-20 right-0 top-[6%] w-[58%] origin-bottom-left rotate-[11deg] scale-95 shadow-card opacity-90 hover:opacity-100 hover:scale-98';
                    } else if (isLeft) {
                      cardPosition = 'z-20 left-0 top-[6%] w-[58%] origin-bottom-right -rotate-[11deg] scale-95 shadow-card opacity-90 hover:opacity-100 hover:scale-98';
                    } else {
                      cardPosition = 'z-10 left-1/2 top-[2%] w-[52%] -translate-x-1/2 rotate-0 scale-85 opacity-0 pointer-events-none';
                    }

                    return (
                      <div
                        key={card.id}
                        onClick={() => {
                          if (isActive) {
                            setActiveCardIdx((activeCardIdx + 1) % HERO_CARDS.length);
                          } else {
                            setActiveCardIdx(idx);
                          }
                        }}
                        title={isActive ? "Click to view next style" : `Switch to ${card.title}`}
                        className={`absolute transition-all duration-700 ease-out cursor-pointer ${cardPosition}`}
                      >
                        <div className="block w-full overflow-hidden rounded-[26px] border-2 border-slate-200/90 bg-white text-left transition-transform hover:-translate-y-1 p-3 shadow-lg">
                          {/* Card Image Viewport */}
                          <div className="relative aspect-[4/3] bg-white rounded-2xl overflow-hidden flex items-center justify-center">
                            <img
                              src={card.image}
                              alt={card.title}
                              className="w-full h-full object-contain transition-transform duration-500 hover:scale-102"
                            />
                            {isActive && (
                              <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-2xl">
                                <div className="w-full h-8 bg-gradient-to-b from-transparent via-cyan-400/25 to-transparent animate-scan-beam"></div>
                              </div>
                            )}
                          </div>

                          {/* Card Footer Bar */}
                          <div className="flex items-center justify-between border-t border-slate-100 mt-2.5 pt-2 px-1 font-mono text-xs uppercase tracking-wider text-slate-800">
                            <span className="flex items-center gap-1.5 font-bold text-slate-900">
                              <span className={`w-2 h-2 rounded-full ${card.dotColor}`}></span>
                              {card.tag}
                            </span>
                            <span className="flex items-center gap-1 font-bold text-emerald-700 text-[11px]">
                              {isActive ? (
                                <span className="relative flex h-2 w-2 mr-0.5">
                                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                                </span>
                              ) : (
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-0.5"></span>
                              )}
                              {card.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Bottom Navigation Indicator Dots (With Animated Progress Bar Fill) */}
                <div className="flex items-center justify-center gap-2 pt-3">
                  {HERO_CARDS.map((card, idx) => (
                    <button
                      key={card.id}
                      type="button"
                      aria-label={`Switch to ${card.title}`}
                      onClick={() => setActiveCardIdx(idx)}
                      className={`relative h-2 rounded-full overflow-hidden transition-all cursor-pointer ${
                        activeCardIdx === idx 
                          ? 'w-8 bg-slate-200 shadow-xs' 
                          : 'w-2 bg-slate-300 hover:bg-slate-400'
                      }`}
                    >
                      {activeCardIdx === idx && (
                        <span 
                          key={`progress-${activeCardIdx}-${isAutoPlayPaused}`}
                          className={`absolute inset-0 bg-blue-600 rounded-full ${
                            isAutoPlayPaused ? 'w-full' : 'animate-progress-fill'
                          }`}
                        />
                      )}
                    </button>
                  ))}
                </div>

                <div className="flex items-center justify-center gap-2 pt-1.5 text-slate-500 font-mono text-[11px]">
                  <span className={`w-1.5 h-1.5 rounded-full ${isAutoPlayPaused ? 'bg-amber-400' : 'bg-emerald-500 animate-pulse'}`}></span>
                  <span>{isAutoPlayPaused ? 'Paused on hover · Click to switch' : `Auto-sliding styles (${activeCardIdx + 1} of ${HERO_CARDS.length}) · Click to advance`}</span>
                </div>

              </div>

            </div>

          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 2: ANIMATED MARQUEE TICKER                                 */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-6 border-b border-line bg-paper-2/60 overflow-hidden">
          <div className="animate-marquee font-mono text-xs uppercase tracking-wider text-slate-600 flex items-center gap-12 font-semibold">
            <span>📐 AIA CAD Vector Standards</span>
            <span className="text-blue-500">●</span>
            <span>🏛️ CDA, RDA & LDA Society Bylaws Compliant</span>
            <span className="text-emerald-500">●</span>
            <span>🏢 Procedural 3D Solid Model Generator</span>
            <span className="text-blue-500">●</span>
            <span>💰 Live Pakistani PKR Construction BOQ</span>
            <span className="text-emerald-500">●</span>
            <span>🧱 Grade-60 Steel Rebar & DG Cement Schedules</span>
            <span className="text-blue-500">●</span>
            <span>🚀 5 Marla, 10 Marla & 1 Kanal Optimization</span>
            <span className="text-emerald-500">●</span>
            <span>📦 Instant AutoCAD DXF, DWG & PDF Export</span>
            {/* Loop duplicate */}
            <span className="text-blue-500">●</span>
            <span>📐 AIA CAD Vector Standards</span>
            <span className="text-emerald-500">●</span>
            <span>🏛️ CDA, RDA & LDA Society Bylaws Compliant</span>
            <span className="text-blue-500">●</span>
            <span>🏢 Procedural 3D Solid Model Generator</span>
            <span className="text-emerald-500">●</span>
            <span>💰 Live Pakistani PKR Construction BOQ</span>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 3: ARCHAI FEATURE 1 - 2D CAD & SPATIAL ZONING STUDIO       */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-5 md:px-8 max-w-7xl mx-auto border-b border-line text-left">
          <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-200 bg-blue-50 text-xs font-mono font-bold text-blue-800 uppercase tracking-wider">
              <PenTool className="w-3.5 h-3.5 text-blue-600" />
              <span>Core ArchAI Engine · Feature 01</span>
            </div>
            <h2 className="text-3xl md:text-5xl font-bold text-slate-950 tracking-tight">
              Interactive 2D Spatial CAD Studio & Smart Snapping
            </h2>
            <p className="text-sm md:text-base text-slate-600">
              Unlike static image generators, ArchAI creates editable, vector-accurate architectural drawings with dynamic grid snapping, wall thickness parameters, and municipal setback validation.
            </p>
          </div>

          <div className="rounded-3xl border border-line bg-white p-6 sm:p-8 shadow-card grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* Left Interactive 2D Blueprint Canvas Display */}
            <div className="lg:col-span-7 relative aspect-[16/10] bg-blue-950 blueprint-grid-fine rounded-2xl overflow-hidden border-2 border-cyan-500/40 p-4 text-cyan-200 font-mono shadow-2xl">
              
              {/* Header Bar */}
              <div className="flex justify-between items-center z-20 relative text-xs">
                <span className="flex items-center gap-2 bg-blue-900/80 px-2.5 py-1 rounded-lg border border-cyan-400/50">
                  <Ruler className="w-3.5 h-3.5 text-cyan-300" />
                  <span>SNAP-TO-GRID: ACTIVE (1/4" = 1'-0")</span>
                </span>
                <span className="text-emerald-400 font-bold bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-400/40">
                  CDA / LDA BYLAW PASS ✓
                </span>
              </div>

              {/* Interactive Room Grid Vector Layout */}
              <div className="mt-4 grid grid-cols-3 gap-2.5 h-44 sm:h-52 text-[10px]">
                
                {/* Master Bed Box */}
                <div 
                  onClick={() => setActiveZone('master')}
                  className={`border-2 p-2 rounded transition cursor-pointer flex flex-col justify-between ${
                    activeZone === 'master' ? 'border-amber-400 bg-blue-900/80 ring-2 ring-amber-400/50' : 'border-dashed border-cyan-400/60 bg-blue-900/30 hover:border-cyan-300'
                  }`}
                >
                  <div className="flex justify-between font-bold text-white">
                    <span>M. BEDROOM</span>
                    <span className="text-amber-400">14' × 16'</span>
                  </div>
                  <span className="text-cyan-300 text-[8px]">9" Double Brick Core</span>
                  <span className="text-[8px] text-emerald-300">Attached Bath + Wardrobe</span>
                </div>

                {/* Central Living Lounge */}
                <div 
                  onClick={() => setActiveZone('lounge')}
                  className={`col-span-2 border-2 p-2.5 rounded transition cursor-pointer flex flex-col justify-between ${
                    activeZone === 'lounge' ? 'border-amber-400 bg-blue-900/80 ring-2 ring-amber-400/50' : 'border-cyan-400/80 bg-blue-900/50 hover:border-cyan-300'
                  }`}
                >
                  <div className="flex justify-between font-bold text-white text-xs">
                    <span>CENTRAL LIVING LOUNGE & DINING</span>
                    <span className="text-amber-400">22' × 16'</span>
                  </div>
                  <div className="flex gap-2 text-[8px] text-cyan-200">
                    <span className="bg-blue-950 px-1.5 py-0.5 rounded">CLEAR HT: 10'-6"</span>
                    <span className="bg-blue-950 px-1.5 py-0.5 rounded">BEAM SPAN: 18'-0"</span>
                  </div>
                  <span className="text-[8px] text-emerald-300">Natural Ventilation Shaft ✓</span>
                </div>

                {/* Open Kitchen */}
                <div 
                  onClick={() => setActiveZone('kitchen')}
                  className={`border-2 p-2 rounded transition cursor-pointer flex flex-col justify-between ${
                    activeZone === 'kitchen' ? 'border-amber-400 bg-blue-900/80 ring-2 ring-amber-400/50' : 'border-dashed border-cyan-400/60 bg-blue-900/30 hover:border-cyan-300'
                  }`}
                >
                  <div className="flex justify-between font-bold text-white">
                    <span>KITCHEN</span>
                    <span className="text-amber-400">12' × 14'</span>
                  </div>
                  <span className="text-cyan-300 text-[8px]">Island Counter Ready</span>
                </div>

                {/* Formal Drawing Room */}
                <div 
                  onClick={() => setActiveZone('drawing')}
                  className={`border-2 p-2 rounded transition cursor-pointer flex flex-col justify-between ${
                    activeZone === 'drawing' ? 'border-amber-400 bg-blue-900/80 ring-2 ring-amber-400/50' : 'border-dashed border-cyan-400/60 bg-blue-900/30 hover:border-cyan-300'
                  }`}
                >
                  <div className="flex justify-between font-bold text-white">
                    <span>DRAWING</span>
                    <span className="text-amber-400">14' × 14'</span>
                  </div>
                  <span className="text-cyan-300 text-[8px]">Independent Entrance</span>
                </div>

                {/* Car Porch & Lawn */}
                <div 
                  onClick={() => setActiveZone('porch')}
                  className={`border-2 p-2 rounded transition cursor-pointer flex flex-col justify-between ${
                    activeZone === 'porch' ? 'border-amber-400 bg-emerald-950/80 ring-2 ring-amber-400/50' : 'border-emerald-400/70 bg-emerald-950/40 hover:border-emerald-300'
                  }`}
                >
                  <div className="flex justify-between font-bold text-emerald-300">
                    <span>CAR PORCH</span>
                    <span className="text-amber-400">14' × 20'</span>
                  </div>
                  <span className="text-emerald-400 text-[8px]">5ft CDA Front Setback ✓</span>
                </div>

              </div>

              {/* Bottom Vector Bar */}
              <div className="flex justify-between items-center text-[10px] text-cyan-400 pt-2 border-t border-cyan-500/30">
                <span>CLICK ROOM TO INSPECT SPATIAL SPECS</span>
                <span className="text-emerald-300 font-bold">AIA CAD LAYERS INCLUDED</span>
              </div>
            </div>

            {/* Right Feature Explanations */}
            <div className="lg:col-span-5 space-y-5">
              <h3 className="text-2xl font-bold text-slate-900">
                How ArchAI's 2D Floor Plan Engine Works
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                When you input spatial requirements, ArchAI doesn't just draw pixels — it creates an interconnected topological graph where walls, door swings, and window spans adhere to structural civil engineering rules.
              </p>

              {/* Active Zone Detail Card */}
              {(() => {
                const currentZone = SPATIAL_ZONES.find(z => z.id === activeZone) || SPATIAL_ZONES[0];
                return (
                  <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/70 space-y-2 font-mono text-xs">
                    <div className="flex justify-between items-center font-bold text-blue-900">
                      <span>Selected Zone: {currentZone.name}</span>
                      <span className="text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">{currentZone.area}</span>
                    </div>
                    <div className="text-slate-600 space-y-1 text-[11px]">
                      <p><strong>Dimensions:</strong> {currentZone.dimensions}</p>
                      <p><strong>Wall Thickness:</strong> {currentZone.wall}</p>
                      <p><strong>Municipal Standard:</strong> {currentZone.bylaw}</p>
                    </div>
                  </div>
                );
              })()}

              <div className="pt-1 flex gap-3">
                <button
                  type="button"
                  onClick={() => setActiveTab('workspace')}
                  className="px-6 py-3 rounded-xl bg-slate-950 hover:bg-blue-600 text-white font-bold text-xs transition cursor-pointer shadow-blueprint"
                >
                  Launch 2D Workspace
                </button>
                <button
                  type="button"
                  onClick={() => onOpenStudio && onOpenStudio('5marla')}
                  className="px-5 py-3 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs transition cursor-pointer"
                >
                  Extrude to 3D Solids
                </button>
              </div>
            </div>

          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 4: LIVE GENERATOR (floorplanai.net Inspired Core)          */}
        {/* ------------------------------------------------------------------ */}
        <section id="generator" className="scroll-mt-24 py-16 px-5 md:px-8 max-w-7xl mx-auto border-b border-line">
          
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-line bg-paper text-xs font-mono font-bold text-blue-800 uppercase tracking-wider">
              <Zap className="w-3.5 h-3.5 text-blue-600" />
              <span>Live Generator Sandbox</span>
            </div>
            <h2 className="text-3xl md:text-5xl font-bold text-slate-950 tracking-tight">
              Floor Plan AI Generator · Free Live Trial
            </h2>
            <p className="text-sm md:text-base text-slate-600">
              Pick a residential template or write your custom spatial requirements. Select an architectural rendering style and synthesize a verified floor plan right on this page.
            </p>

            {/* Generator Mode Switcher: 2D vs 3D */}
            <div className="pt-4 flex justify-center">
              <div className="inline-flex p-1 rounded-2xl border border-line bg-white shadow-2xs">
                <button
                  type="button"
                  onClick={() => setGeneratorMode('floorplan')}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer ${
                    generatorMode === 'floorplan' 
                      ? 'bg-slate-950 text-white shadow-sm' 
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <LayoutGrid className="w-4 h-4" />
                  <span>Floor Plan AI (2D)</span>
                </button>

                <button
                  type="button"
                  onClick={() => setGeneratorMode('3d')}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer ${
                    generatorMode === '3d' 
                      ? 'bg-slate-950 text-white shadow-sm' 
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Box className="w-4 h-4" />
                  <span>3D Visualization</span>
                  <span className="text-[10px] font-mono bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded-full font-bold">Live</span>
                </button>
              </div>
            </div>
          </div>

          {/* Generator Interactive Workspace: Split Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            {/* LEFT COLUMN: Controls & Input Studio */}
            <div className="lg:col-span-5 rounded-2xl border border-line bg-white p-6 shadow-card space-y-6 text-left">
              
              {/* Template vs Custom Toggle */}
              <div className="grid grid-cols-2 gap-1 p-1 rounded-xl border border-line bg-paper">
                <button
                  type="button"
                  onClick={() => setTemplateMode('template')}
                  className={`py-2 text-xs font-bold font-mono uppercase tracking-wider rounded-lg transition cursor-pointer ${
                    templateMode === 'template' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Catalog Template
                </button>
                <button
                  type="button"
                  onClick={() => setTemplateMode('custom')}
                  className={`py-2 text-xs font-bold font-mono uppercase tracking-wider rounded-lg transition cursor-pointer ${
                    templateMode === 'custom' ? 'bg-blue-600 text-white shadow-2xs' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Custom NLP Prompt
                </button>
              </div>

              {/* Natural Language Prompt Textarea */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold font-mono uppercase tracking-wider text-slate-800">
                    Spatial Requirements Prompt
                  </label>
                  <span className="text-[11px] font-mono text-blue-700 font-semibold">Natural Language</span>
                </div>

                <textarea
                  rows={4}
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  className="w-full p-3.5 text-sm text-slate-800 bg-paper border border-line rounded-xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition resize-none leading-relaxed font-sans"
                  placeholder="Describe your desired rooms, floors, and dimensions..."
                />

                {/* Example Quick-Pick Pills */}
                <div className="pt-1 flex flex-wrap items-center gap-1.5">
                  <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold mr-1">Presets:</span>
                  {PROMPT_PRESETS.map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => handleApplyPreset(preset)}
                      className="px-2.5 py-1 rounded-full border border-line bg-paper-2 hover:border-blue-400 hover:text-blue-700 text-[11px] font-medium text-slate-700 transition cursor-pointer"
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Choose Rendering Style: Using FloorplanAI.net 3 Real Image Thumbnails */}
              <div className="space-y-2.5">
                <label className="text-xs font-bold font-mono uppercase tracking-wider text-slate-800">
                  Select Architectural Style (FloorPlanAI.net Styles)
                </label>

                <div className="grid grid-cols-3 gap-2.5">
                  {/* Style 1: Technical */}
                  <button
                    type="button"
                    onClick={() => setSelectedStyle('technical')}
                    className={`group relative overflow-hidden rounded-xl border-2 text-left transition-all cursor-pointer ${
                      selectedStyle === 'technical'
                        ? 'border-blue-600 ring-2 ring-blue-200 shadow-md'
                        : 'border-line hover:border-blue-400'
                    }`}
                  >
                    <div className="relative aspect-[4/3] overflow-hidden bg-slate-900">
                      <img 
                        src="/images/styles/technical.png" 
                        alt="Technical Blueprint" 
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-300" 
                      />
                      {selectedStyle === 'technical' && (
                        <span className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center shadow">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </span>
                      )}
                    </div>
                    <div className="p-2 bg-paper border-t border-line">
                      <p className="text-xs font-bold text-slate-900">Technical</p>
                      <p className="text-[10px] text-slate-500 font-mono">2D CAD</p>
                    </div>
                  </button>

                  {/* Style 2: 2.5D */}
                  <button
                    type="button"
                    onClick={() => setSelectedStyle('2-5d')}
                    className={`group relative overflow-hidden rounded-xl border-2 text-left transition-all cursor-pointer ${
                      selectedStyle === '2-5d'
                        ? 'border-blue-600 ring-2 ring-blue-200 shadow-md'
                        : 'border-line hover:border-blue-400'
                    }`}
                  >
                    <div className="relative aspect-[4/3] overflow-hidden bg-slate-100">
                      <img 
                        src="/images/styles/2-5d.png" 
                        alt="2.5D Furnished Plan" 
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-300" 
                      />
                      {selectedStyle === '2-5d' && (
                        <span className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center shadow">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </span>
                      )}
                    </div>
                    <div className="p-2 bg-paper border-t border-line">
                      <p className="text-xs font-bold text-slate-900">2.5D Color</p>
                      <p className="text-[10px] text-slate-500 font-mono">Furnished</p>
                    </div>
                  </button>

                  {/* Style 3: 3D Isometric */}
                  <button
                    type="button"
                    onClick={() => setSelectedStyle('isometric')}
                    className={`group relative overflow-hidden rounded-xl border-2 text-left transition-all cursor-pointer ${
                      selectedStyle === 'isometric'
                        ? 'border-blue-600 ring-2 ring-blue-200 shadow-md'
                        : 'border-line hover:border-blue-400'
                    }`}
                  >
                    <div className="relative aspect-[4/3] overflow-hidden bg-slate-900">
                      <img 
                        src="/images/styles/isometric.png" 
                        alt="3D Isometric Solid" 
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-300" 
                      />
                      {selectedStyle === 'isometric' && (
                        <span className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center shadow">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </span>
                      )}
                    </div>
                    <div className="p-2 bg-paper border-t border-line">
                      <p className="text-xs font-bold text-slate-900">3D Isometric</p>
                      <p className="text-[10px] text-slate-500 font-mono">Cutaway</p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Collapsible Plot & Municipal Controls */}
              <div className="rounded-xl border border-line bg-paper overflow-hidden">
                <button
                  type="button"
                  onClick={() => setShowPlotDetails(!showPlotDetails)}
                  className="w-full flex items-center justify-between p-3.5 text-xs font-bold font-mono uppercase tracking-wider text-slate-800 cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-blue-600" />
                    Plot Dimensions & Schedule ({selectedPlot.toUpperCase()})
                  </span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${showPlotDetails ? 'rotate-180' : ''}`} />
                </button>

                {showPlotDetails && (
                  <div className="p-4 pt-1 border-t border-line space-y-4">
                    <div>
                      <label className="text-[11px] font-mono text-slate-500 block mb-1">Standard Plot Category</label>
                      <div className="grid grid-cols-4 gap-1.5 text-center text-xs font-bold font-mono">
                        {['3marla', '5marla', '10marla', '1kanal'].map((plot) => (
                          <button
                            key={plot}
                            type="button"
                            onClick={() => setSelectedPlot(plot)}
                            className={`py-1.5 rounded-lg border transition cursor-pointer ${
                              selectedPlot === plot 
                                ? 'bg-blue-600 text-white border-blue-600' 
                                : 'bg-white text-slate-700 border-line hover:border-slate-300'
                            }`}
                          >
                            {plot.replace('marla', 'M').replace('kanal', 'K').toUpperCase()}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <label className="text-[11px] font-mono text-slate-500 block mb-1">Bedrooms</label>
                        <div className="flex items-center justify-between bg-white border border-line rounded-lg p-1.5">
                          <button 
                            type="button" 
                            onClick={() => setBedrooms(Math.max(1, bedrooms - 1))}
                            className="w-6 h-6 rounded bg-slate-100 font-bold hover:bg-slate-200"
                          >-</button>
                          <span className="font-mono font-bold">{bedrooms} Beds</span>
                          <button 
                            type="button" 
                            onClick={() => setBedrooms(bedrooms + 1)}
                            className="w-6 h-6 rounded bg-slate-100 font-bold hover:bg-slate-200"
                          >+</button>
                        </div>
                      </div>

                      <div>
                        <label className="text-[11px] font-mono text-slate-500 block mb-1">Bathrooms</label>
                        <div className="flex items-center justify-between bg-white border border-line rounded-lg p-1.5">
                          <button 
                            type="button" 
                            onClick={() => setBathrooms(Math.max(1, bathrooms - 1))}
                            className="w-6 h-6 rounded bg-slate-100 font-bold hover:bg-slate-200"
                          >-</button>
                          <span className="font-mono font-bold">{bathrooms} Baths</span>
                          <button 
                            type="button" 
                            onClick={() => setBathrooms(bathrooms + 1)}
                            className="w-6 h-6 rounded bg-slate-100 font-bold hover:bg-slate-200"
                          >+</button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Aspect Ratio & Resolution Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-bold font-mono uppercase tracking-wider text-slate-700 mb-1.5">
                    Aspect Ratio
                  </label>
                  <div className="grid grid-cols-3 gap-1 rounded-xl border border-line bg-paper p-1 text-center text-xs font-mono font-bold">
                    {['4:3', '16:9', '1:1'].map((ratio) => (
                      <button
                        key={ratio}
                        type="button"
                        onClick={() => setAspectRatio(ratio)}
                        className={`py-1 rounded-lg transition cursor-pointer ${
                          aspectRatio === ratio ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        {ratio}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-bold font-mono uppercase tracking-wider text-slate-700 mb-1.5">
                    Resolution
                  </label>
                  <div className="grid grid-cols-3 gap-1 rounded-xl border border-line bg-paper p-1 text-center text-xs font-mono font-bold">
                    {['1K', '2K', '4K'].map((res) => (
                      <button
                        key={res}
                        type="button"
                        onClick={() => setResolution(res)}
                        className={`py-1 rounded-lg transition cursor-pointer ${
                          resolution === res ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        {res}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Generate Action Button */}
              <button
                type="button"
                onClick={handleSimulateGenerate}
                disabled={isGenerating}
                className="w-full h-13 rounded-xl bg-slate-950 hover:bg-blue-700 text-white font-bold text-sm transition-all shadow-blueprint flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <RotateCw className="w-4 h-4 animate-spin text-cyan-300" />
                    <span>Synthesizing Architectural Geometry...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    <span>Generate Floor Plan</span>
                    <span className="ml-1 text-[10px] font-mono uppercase bg-white/20 px-2 py-0.5 rounded-full">
                      Free Credit
                    </span>
                  </>
                )}
              </button>

              <p className="text-center font-mono text-[11px] text-slate-500 uppercase tracking-wider">
                Instant CAD Synthesis · AIA Standards · CDA/RDA Compliant
              </p>
            </div>

            {/* RIGHT COLUMN: Live Interactive Viewport with Real High-Res Style Images */}
            <div className="lg:col-span-7 rounded-2xl border border-line bg-white p-5 shadow-card space-y-4 text-left">
              
              {/* Viewport Top Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 font-mono text-xs border-b border-line pb-3">
                <div className="flex items-center gap-2 text-blue-900 font-bold">
                  <Image className="w-4 h-4 text-blue-600" />
                  <span>OUTPUT PREVIEW</span>
                  <span className="text-slate-400">·</span>
                  <span className="text-slate-600 uppercase">{selectedStyle}</span>
                  <span className="text-slate-400">·</span>
                  <span className="text-slate-600">{aspectRatio}</span>
                  <span className="text-slate-400">·</span>
                  <span className="text-slate-600">{resolution}</span>
                </div>

                <div className="flex items-center gap-2 text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="text-emerald-800 font-bold">SYNTHESIZED #{generationCount}</span>
                </div>
              </div>

              {/* Viewport Canvas Screen with REAL HIGH-RESOLUTION IMAGE */}
              <div className="relative aspect-[4/3] rounded-xl border border-line overflow-hidden bg-slate-950 shadow-inner">
                
                {/* Architectural Stamp */}
                <div className="absolute top-3 left-3 z-20 flex items-center gap-2 bg-white/95 backdrop-blur border border-slate-200 px-3 py-1 rounded-full font-mono text-[10px] font-bold text-slate-800 shadow-xs">
                  <Compass className="w-3 h-3 text-blue-600" />
                  <span>NORTH ORIENTED • {selectedPlot.toUpperCase()} · {selectedStyle.toUpperCase()}</span>
                </div>

                {/* Real FloorPlanAI Image Display */}
                <div className="absolute inset-0 flex items-center justify-center overflow-hidden">
                  <img 
                    src={
                      selectedStyle === 'technical' 
                        ? '/images/styles/technical.png' 
                        : selectedStyle === '2-5d' 
                        ? '/images/styles/2-5d.png' 
                        : '/images/styles/isometric.png'
                    }
                    alt={selectedStyle}
                    className="w-full h-full object-cover transition-all duration-500"
                  />
                </div>

                {/* Watermark Overlay */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none">
                  <span className="font-mono font-black text-white/20 text-5xl sm:text-7xl -rotate-15 uppercase tracking-widest">
                    ARCHAI SAMPLE
                  </span>
                </div>

                {/* Bottom Overlay Bar */}
                <div className="absolute bottom-3 right-3 flex items-center gap-2 z-20">
                  <span className="px-2.5 py-1 rounded bg-black/80 backdrop-blur text-white text-[10px] font-mono border border-white/20">
                    PKR EST: ₨ 4,850,000 (GREY STRUCTURE)
                  </span>
                </div>
              </div>

              {/* Action Toolbar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveTab('workspace')}
                  className="flex items-center justify-center gap-2 h-11 px-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition cursor-pointer"
                >
                  <Layers className="w-4 h-4" />
                  <span>Open in Workspace</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('cost-estimator')}
                  className="flex items-center justify-center gap-2 h-11 px-3 rounded-xl border border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 font-bold text-xs transition cursor-pointer"
                >
                  <BarChart3 className="w-4 h-4 text-emerald-700" />
                  <span>Detailed BOQ</span>
                </button>

                <button
                  type="button"
                  onClick={() => onOpenStudio && onOpenStudio('5marla')}
                  className="flex items-center justify-center gap-2 h-11 px-3 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs transition cursor-pointer"
                >
                  <Box className="w-4 h-4 text-blue-600" />
                  <span>Launch 3D Studio</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab(isAuthenticated ? 'workspace' : 'auth')}
                  className="flex items-center justify-center gap-2 h-11 px-3 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs transition cursor-pointer"
                >
                  <Download className="w-4 h-4 text-slate-600" />
                  <span>Export DXF / DWG</span>
                </button>
              </div>

            </div>

          </div>

        </section>

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 5: ARCHAI FEATURE 2 - PAKISTANI CONSTRUCTION BOQ & RATES   */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-5 md:px-8 max-w-7xl mx-auto border-b border-line text-left">
          <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-200 bg-emerald-50 text-xs font-mono font-bold text-emerald-800 uppercase tracking-wider">
              <Calculator className="w-3.5 h-3.5 text-emerald-600" />
              <span>Core ArchAI Engine · Feature 02</span>
            </div>
            <h2 className="text-3xl md:text-5xl font-bold text-slate-950 tracking-tight">
              Automated Pakistani Construction BOQ & Cost Engine (PKR)
            </h2>
            <p className="text-sm md:text-base text-slate-600">
              Generic global floor plan tools provide useless square-foot estimates. ArchAI calculates real Pakistani construction budgets based on live market prices for Fauji Cement, Mughal Grade-60 Steel, and Ravi Sand.
            </p>
          </div>

          <div className="rounded-3xl border border-line bg-white p-6 sm:p-10 shadow-card grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* Left Controls & Plot Switcher */}
            <div className="lg:col-span-5 space-y-5">
              <h3 className="text-2xl font-bold text-slate-900">
                Transparent Material Schedules & Budgets
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Select your plot size to inspect exact steel tonnage, cement bag counts, brick volumes, and labour costs for grey structure and turnkey premium finishing.
              </p>

              {/* Plot Category Pills */}
              <div className="grid grid-cols-2 gap-2 font-mono text-xs font-bold">
                {Object.keys(BOQ_DATA).map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setBoqPlotCategory(cat)}
                    className={`p-3 rounded-xl border text-center transition cursor-pointer ${
                      boqPlotCategory === cat
                        ? 'border-emerald-600 bg-emerald-50 text-emerald-900 shadow-xs'
                        : 'border-line bg-paper text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    <span>{cat.replace('marla', ' Marla').replace('kanal', ' Kanal').toUpperCase()}</span>
                  </button>
                ))}
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setActiveTab('cost-estimator')}
                  className="px-6 py-3 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs transition cursor-pointer shadow-md"
                >
                  Open Full BOQ Breakdown
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('workspace')}
                  className="px-5 py-3 rounded-xl border border-line bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs transition cursor-pointer"
                >
                  Adjust Wall Spans
                </button>
              </div>
            </div>

            {/* Right BOQ Itemized Schedule Card */}
            <div className="lg:col-span-7">
              <div className="rounded-2xl border-2 border-emerald-500/40 bg-emerald-950 text-emerald-100 p-6 sm:p-7 shadow-blueprint font-mono space-y-4">
                
                <div className="flex justify-between items-center border-b border-emerald-800 pb-3">
                  <div>
                    <h4 className="font-bold text-white text-base">{activeBoq.label}</h4>
                    <span className="text-xs text-emerald-300">{activeBoq.coveredArea}</span>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-emerald-800 text-white font-bold text-xs">
                    PKR RATES 2026
                  </span>
                </div>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between items-center py-1.5 border-b border-emerald-900/60">
                    <span className="text-emerald-300">Grade-60 Deformed Steel Rebar:</span>
                    <span className="font-bold text-white">{activeBoq.steelTons} ({activeBoq.steelCost})</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-emerald-900/60">
                    <span className="text-emerald-300">DG Khan / Fauji Portland Cement:</span>
                    <span className="font-bold text-white">{activeBoq.cementBags} ({activeBoq.cementCost})</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-emerald-900/60">
                    <span className="text-emerald-300">Sand, Crushed Aggregates & Bricks:</span>
                    <span className="font-bold text-white">{activeBoq.sandBricks}</span>
                  </div>
                </div>

                <div className="pt-2 grid grid-cols-2 gap-3">
                  <div className="bg-emerald-900/60 border border-emerald-700/60 p-3 rounded-xl">
                    <span className="text-[10px] text-emerald-300 uppercase block font-semibold">Grey Structure Total</span>
                    <span className="text-lg font-bold text-white">{activeBoq.greyTotal}</span>
                  </div>

                  <div className="bg-emerald-900/90 border border-emerald-500/80 p-3 rounded-xl">
                    <span className="text-[10px] text-emerald-300 uppercase block font-semibold">Turnkey Complete Total</span>
                    <span className="text-lg font-bold text-emerald-200">{activeBoq.turnkeyTotal}</span>
                  </div>
                </div>

              </div>
            </div>

          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 6: FLOORPLANAI.NET REAL EXAMPLES GALLERY                   */}
        {/* ------------------------------------------------------------------ */}
        <section id="examples" className="py-16 px-5 md:px-8 max-w-7xl mx-auto border-b border-line text-left bg-paper-2/40">
          <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-4 mb-12">
            <div>
              <div className="font-mono text-xs uppercase tracking-wider text-blue-700 font-bold">
                Examples · 4 Architectural Styles + 3D Solid Models
              </div>
              <h2 className="mt-2 text-3xl md:text-4xl font-bold text-slate-950 tracking-tight">
                AI Generated Floor Plans · High Resolution Showcase
              </h2>
              <p className="mt-2 text-slate-600 text-sm md:text-base max-w-xl">
                Real architectural generation outputs from single-sentence prompts. Click any plan to open in the interactive 2D editor or 3D solid viewer.
              </p>
            </div>
            <a 
              href="#generator" 
              className="inline-flex items-center gap-2 text-xs font-bold text-blue-700 hover:text-blue-900 font-mono"
            >
              <span>Try with your own prompt</span>
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            
            {/* Example 1: Technical Studio */}
            <div className="group rounded-2xl border border-line bg-white overflow-hidden shadow-card hover:-translate-y-1 hover:shadow-blueprint transition-all">
              <div className="relative aspect-[4/3] bg-slate-950 overflow-hidden">
                <img 
                  src="/images/styles/ex-studio.png" 
                  alt="Technical Studio Plan" 
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500" 
                />
                <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded bg-blue-950/80 backdrop-blur border border-cyan-400 text-[10px] font-mono text-cyan-200">
                  Technical 2D CAD
                </span>
              </div>
              <div className="p-4 space-y-2">
                <h4 className="font-bold text-sm text-slate-900">Cozy Studio Apartment</h4>
                <p className="text-xs text-slate-500 italic">"Studio with Murphy bed, mini kitchen and ensuite bath, ~40 m²"</p>
                <div className="pt-2 border-t border-line flex justify-between items-center text-[11px] font-mono">
                  <span className="text-slate-500">PKR: ₨ 1,850,000</span>
                  <button 
                    type="button" 
                    onClick={() => setActiveTab('workspace')}
                    className="text-blue-600 font-bold hover:underline"
                  >
                    Open 2D →
                  </button>
                </div>
              </div>
            </div>

            {/* Example 2: 2.5D 2-Bedroom */}
            <div className="group rounded-2xl border border-line bg-white overflow-hidden shadow-card hover:-translate-y-1 hover:shadow-blueprint transition-all">
              <div className="relative aspect-[4/3] bg-slate-100 overflow-hidden">
                <img 
                  src="/images/styles/ex-2br.png" 
                  alt="2.5D 2-Bedroom Plan" 
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500" 
                />
                <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded bg-white/90 backdrop-blur border border-amber-400 text-[10px] font-mono text-amber-900 font-bold">
                  2.5D Color Plan
                </span>
              </div>
              <div className="p-4 space-y-2">
                <h4 className="font-bold text-sm text-slate-900">2-Bedroom Modern Flat</h4>
                <p className="text-xs text-slate-500 italic">"Modern 2-bedroom with island kitchen and spacious balcony, ~65 m²"</p>
                <div className="pt-2 border-t border-line flex justify-between items-center text-[11px] font-mono">
                  <span className="text-slate-500">PKR: ₨ 3,250,000</span>
                  <button 
                    type="button" 
                    onClick={() => setActiveTab('workspace')}
                    className="text-blue-600 font-bold hover:underline"
                  >
                    Open 2D →
                  </button>
                </div>
              </div>
            </div>

            {/* Example 3: 3D Isometric 3-Bedroom */}
            <div className="group rounded-2xl border border-line bg-white overflow-hidden shadow-card hover:-translate-y-1 hover:shadow-blueprint transition-all">
              <div className="relative aspect-[4/3] bg-slate-950 overflow-hidden">
                <img 
                  src="/images/styles/ex-3br.png" 
                  alt="3D Isometric Cutaway Plan" 
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500" 
                />
                <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded bg-emerald-950/80 backdrop-blur border border-emerald-400 text-[10px] font-mono text-emerald-300 font-bold">
                  3D Isometric
                </span>
              </div>
              <div className="p-4 space-y-2">
                <h4 className="font-bold text-sm text-slate-900">3-Bedroom Family House</h4>
                <p className="text-xs text-slate-500 italic">"3-bedroom house with 2 baths, dining terrace and porch, ~110 m²"</p>
                <div className="pt-2 border-t border-line flex justify-between items-center text-[11px] font-mono">
                  <span className="text-slate-500">PKR: ₨ 5,400,000</span>
                  <button 
                    type="button" 
                    onClick={() => onOpenStudio && onOpenStudio('5marla')}
                    className="text-emerald-700 font-bold hover:underline"
                  >
                    Walk in 3D →
                  </button>
                </div>
              </div>
            </div>

            {/* Example 4: Architectural Loft */}
            <div className="group rounded-2xl border border-line bg-white overflow-hidden shadow-card hover:-translate-y-1 hover:shadow-blueprint transition-all">
              <div className="relative aspect-[4/3] bg-stone-900 overflow-hidden">
                <img 
                  src="/images/styles/ex-loft.png" 
                  alt="Architectural Loft Plan" 
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500" 
                />
                <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded bg-slate-900/80 backdrop-blur border border-purple-400 text-[10px] font-mono text-purple-300 font-bold">
                  Watercolor / Loft
                </span>
              </div>
              <div className="p-4 space-y-2">
                <h4 className="font-bold text-sm text-slate-900">Double-Height Mezzanine Loft</h4>
                <p className="text-xs text-slate-500 italic">"Industrial loft with mezzanine bedroom and skylights, ~84 m²"</p>
                <div className="pt-2 border-t border-line flex justify-between items-center text-[11px] font-mono">
                  <span className="text-slate-500">PKR: ₨ 4,100,000</span>
                  <button 
                    type="button" 
                    onClick={() => onOpenStudio && onOpenStudio('5marla')}
                    className="text-purple-700 font-bold hover:underline"
                  >
                    Walk in 3D →
                  </button>
                </div>
              </div>
            </div>

          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 7: HOW IT WORKS STEP-BY-STEP                               */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-5 md:px-8 max-w-7xl mx-auto border-b border-line text-left">
          <div className="text-center max-w-3xl mx-auto mb-14 space-y-3">
            <span className="inline-block px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-xs font-mono font-bold uppercase tracking-wider">
              Simple 3-Step Process
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-950 tracking-tight">
              From Concept to Construction Contract in 10 Minutes
            </h2>
            <p className="text-slate-600 text-sm md:text-base">
              No complicated desktop CAD software required. Run everything in your web browser.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Step 1 */}
            <div className="rounded-2xl border border-line bg-white p-6 shadow-card space-y-4 relative">
              <span className="text-4xl font-black font-mono text-blue-100 absolute top-4 right-4">01</span>
              <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">1. Describe Your Requirements</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Type your room wishes in natural English or select a standard plot category (3M, 5M, 10M, 1K). Our spatial algorithm handles dimensions and structural zoning.
              </p>
            </div>

            {/* Step 2 */}
            <div className="rounded-2xl border border-line bg-white p-6 shadow-card space-y-4 relative">
              <span className="text-4xl font-black font-mono text-emerald-100 absolute top-4 right-4">02</span>
              <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
                <Sliders className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">2. Customize in 2D &amp; Walk in 3D</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Fine-tune wall positions, doors, windows, and room schedules with smart grid snapping. Seamlessly toggle to Three.js 3D solid mode for orbital walkthroughs.
              </p>
            </div>

            {/* Step 3 */}
            <div className="rounded-2xl border border-line bg-white p-6 shadow-card space-y-4 relative">
              <span className="text-4xl font-black font-mono text-amber-100 absolute top-4 right-4">03</span>
              <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
                <Download className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">3. Export CAD &amp; Verified BOQ</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Download ready-to-permit AutoCAD DXF drawings, PDF presentation sheets, and an itemized Bill of Quantities with local Pakistani market cement and steel rates.
              </p>
            </div>

          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 8: USER REVIEWS & SOCIAL PROOF                             */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-5 md:px-8 max-w-7xl mx-auto border-b border-line text-left">
          <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-950 tracking-tight">
              Trusted by Architects, Builders &amp; Homeowners
            </h2>
            <div className="flex items-center justify-center gap-1 text-amber-400">
              <Star className="w-4 h-4 fill-amber-400" />
              <Star className="w-4 h-4 fill-amber-400" />
              <Star className="w-4 h-4 fill-amber-400" />
              <Star className="w-4 h-4 fill-amber-400" />
              <Star className="w-4 h-4 fill-amber-400" />
              <span className="text-xs font-mono font-bold text-slate-700 ml-2">4.9 / 5.0 Rating</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 rounded-2xl border border-line bg-white shadow-card space-y-3">
              <div className="flex gap-1 text-amber-400">
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
              </div>
              <p className="text-xs text-slate-700 leading-relaxed italic">
                "ArchAI generates real Pakistani society bylaw checks (CDA/DHA) and accurate steel/cement BOQs. Saved us weeks on client presentations."
              </p>
              <div className="border-t border-line pt-2">
                <p className="text-xs font-bold text-slate-900">Ar. Daniyal Qureshi</p>
                <p className="text-[10px] font-mono text-slate-500">Lead Architect, Studio Urban Islamabad</p>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-line bg-white shadow-card space-y-3">
              <div className="flex gap-1 text-amber-400">
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
              </div>
              <p className="text-xs text-slate-700 leading-relaxed italic">
                "Being able to generate a 10 Marla plan from a single sentence and immediately see the estimated construction cost in PKR gave my clients total budget clarity before breaking ground."
              </p>
              <div className="border-t border-line pt-2">
                <p className="text-xs font-bold text-slate-900">Engr. Tariq Mehmood</p>
                <p className="text-[10px] font-mono text-slate-500">Construction Contractor, Lahore</p>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-line bg-white shadow-card space-y-3">
              <div className="flex gap-1 text-amber-400">
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                <Star className="w-3.5 h-3.5 fill-amber-400" />
              </div>
              <p className="text-xs text-slate-700 leading-relaxed italic">
                "As a homeowner building my first 5 Marla house in Rawalpindi, ArchAI helped me visualize my rooms in 3D and know exactly how many cement bags and steel tons I need to purchase."
              </p>
              <div className="border-t border-line pt-2">
                <p className="text-xs font-bold text-slate-900">Hamza Siddiqui</p>
                <p className="text-[10px] font-mono text-slate-500">Homeowner Client, Bahria Town</p>
              </div>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* SECTION 9: FINAL CTA BLUEPRINT CONTAINER                           */}
        {/* ------------------------------------------------------------------ */}
        <section className="pt-8 px-5 md:px-8 max-w-7xl mx-auto">
          <div className="rounded-3xl bg-slate-950 text-white p-8 sm:p-14 relative overflow-hidden shadow-2xl blueprint-grid-fine animate-glow">
            
            {/* Background Glows */}
            <div className="absolute top-0 right-0 w-80 h-80 bg-blue-600/25 rounded-full blur-3xl pointer-events-none"></div>
            <div className="absolute bottom-0 left-0 w-80 h-80 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none"></div>

            <div className="relative z-10 max-w-2xl mx-auto text-center space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-900/60 border border-blue-400 text-xs font-mono text-cyan-300">
                <Sparkles className="w-3.5 h-3.5 text-cyan-300 animate-pulse" />
                <span>{isAuthenticated ? 'AI Studio Ready' : 'Start Designing Now'}</span>
              </div>

              <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
                {isAuthenticated 
                  ? `Welcome back, ${user?.name ? user.name.split(' ')[0] : 'Architect'}! Ready for a new design?` 
                  : 'Ready to generate your architectural floor plan?'}
              </h2>

              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                {isAuthenticated
                  ? 'Launch your 2D CAD canvas with intelligent grid snapping, generate procedural 3D solid models, or calculate updated Pakistani construction BOQ budgets.'
                  : 'Join architects, builders, and homeowners across Pakistan using ArchAI to draft floor plans, explore 3D elevations, and calculate verified PKR construction costs.'}
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
                {isAuthenticated ? (
                  <div className="flex flex-col sm:flex-row items-center justify-center gap-3 w-full sm:w-auto">
                    <button
                      type="button"
                      onClick={() => setActiveTab('workspace', 'dashboard')}
                      className="w-full sm:w-auto h-13 px-8 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm transition-all shadow-lg shadow-blue-600/30 cursor-pointer flex items-center justify-center gap-2 group"
                    >
                      <LayoutDashboard className="w-4 h-4 text-cyan-300" />
                      <span>Open Workspace Dashboard</span>
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                    </button>

                    <button
                      type="button"
                      onClick={() => setActiveTab('workspace', 'new-design')}
                      className="w-full sm:w-auto h-13 px-7 rounded-xl border border-blue-400/40 bg-blue-950/40 hover:bg-blue-900/60 text-cyan-300 font-bold text-sm transition cursor-pointer flex items-center justify-center gap-2"
                    >
                      <Wand2 className="w-4 h-4 text-cyan-400" />
                      <span>Start New Design Generator</span>
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setActiveTab('auth')}
                    className="w-full sm:w-auto h-13 px-8 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-all shadow-lg shadow-blue-600/30 cursor-pointer"
                  >
                    Create Free Account
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => onOpenStudio && onOpenStudio('5marla')}
                  className="w-full sm:w-auto h-13 px-7 rounded-xl border border-slate-700 bg-slate-900/80 hover:bg-slate-800 text-white font-bold text-sm transition cursor-pointer"
                >
                  Explore 3D Studio
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('cost-estimator')}
                  className="w-full sm:w-auto h-13 px-7 rounded-xl border border-emerald-500/50 bg-emerald-950/60 hover:bg-emerald-900 text-emerald-300 font-bold text-sm transition cursor-pointer"
                >
                  PKR Cost Rates
                </button>
              </div>

              <div className="pt-2">
                {isAuthenticated ? (
                  <p className="text-xs font-mono text-cyan-300/80 flex items-center justify-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>Active Session · Signed in as {user?.email || user?.name || 'Architect'} · Full CAD Workspace Ready</span>
                  </p>
                ) : (
                  <p className="text-xs font-mono text-slate-400">
                    No credit card required • Instant demo credentials available
                  </p>
                )}
              </div>
            </div>

          </div>
        </section>

      </main>

    </div>
  );
}
