import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Compass,
  ArrowRight,
  Layers,
  Sparkles,
  Calculator,
  ShieldCheck,
  CheckCircle,
  Building,
  Maximize2,
  Users,
  FileCheck,
  ChevronRight,
  HelpCircle,
  Eye,
  Sliders,
  DollarSign,
  Flame,
} from 'lucide-react';
import { FloorPlanViewer } from '../../components/architectural/FloorPlanViewer';
import { ElevationViewer } from '../../components/architectural/ElevationViewer';
import { MOCK_TEMPLATES } from '../../data/mockData';
import { formatPKR } from '../../services/costEstimatorService';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [activePlotTab, setActivePlotTab] = useState<'5_marla' | '7_marla' | '10_marla' | '1_kanal'>('10_marla');
  const [activeFaq, setActiveFaq] = useState<number | null>(0);

  // Mini live cost calculator on landing page
  const [calcArea, setCalcArea] = useState(2200);
  const [calcTier, setCalcTier] = useState<'standard' | 'premium' | 'luxury'>('premium');
  const rateMap = { standard: 6600, premium: 8000, luxury: 10400 };
  const estCost = calcArea * rateMap[calcTier];

  const faqs = [
    {
      q: 'Does ArchiCraft AI generate designs compliant with Pakistani society bylaws?',
      a: 'Yes. The system incorporates dimensional guidelines and standard setbacks for major authorities including CDA (Islamabad), LDA (Lahore), DHA (all chapters), and Bahria Town. However, municipal bylaws undergo periodic revisions, so designs must be verified and stamped by a licensed PCATP architect before submission.',
    },
    {
      q: 'How accurate is the preliminary construction cost estimation?',
      a: 'The cost module utilizes monthly benchmark rates for cement (OPC), grade-60 steel rebar, red clay bricks, river sand, aggregate, and regional labour wages across Pakistani cities. It provides realistic preliminary planning estimates with 90-95% market accuracy, including a recommended 5% contingency margin.',
    },
    {
      q: 'Can I generate designs using a natural-language description?',
      a: 'Yes! ArchiCraft AI features an intelligent dual-mode workspace. You can describe your dream house in plain English (e.g. "Double storey 10 Marla house with separate drawing room, dirty kitchen, and 2-car porch"), or switch to our Guided Structured Form mode.',
    },
    {
      q: 'What is the role of licensed architects on this platform?',
      a: 'Architects registered with PCATP have a dedicated workspace to review client AI drafts, inspect structural setback constraints, add professional redline annotations, manage revisions, and convert preliminary designs into technical CAD/BIM submission packages.',
    },
    {
      q: 'Is this a Final Year Project (FYP)?',
      a: 'Yes. ArchiCraft AI is developed as an academic Final Year Software Engineering Project demonstrating the fusion of computer-aided architectural design, AI spatial layout synthesis, and preliminary construction economics.',
    },
  ];

  return (
    <div className="space-y-24 pb-20">
      {/* HERO SECTION */}
      <section className="relative overflow-hidden pt-12 md:pt-20 lg:pt-28">
        {/* Architectural Glow Effect */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-teal-500/15 blur-[120px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-950/70 border border-teal-800 text-teal-300 text-xs font-medium">
              <Sparkles className="h-3.5 w-3.5 text-teal-400" />
              <span>Next-Gen Architectural AI for Pakistani Residential Plots</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-tight font-heading">
              Design Your Dream Home <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 via-teal-300 to-emerald-400">
                with Intelligent AI Assistance
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto">
              Transform your ideas, plot dimensions, and architectural requirements into personalized building designs with intelligent design assistance and preliminary construction cost estimation.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
              <Link
                to="/app/designs/new"
                className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-sm shadow-xl shadow-teal-900/40 flex items-center justify-center gap-2 transition-all hover:-translate-y-0.5"
              >
                <span>Create Your First Design</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/templates"
                className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-200 font-semibold text-sm flex items-center justify-center gap-2 transition-all"
              >
                <Layers className="h-4 w-4 text-teal-400" />
                <span>Explore Templates</span>
              </Link>
            </div>

            {/* Micro badges */}
            <div className="pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400">
              <span className="flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-teal-400" /> CDA & LDA Setbacks
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-teal-400" /> 5, 7, 10 Marla & 1 Kanal
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-teal-400" /> Instant PKR BOQ Estimates
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-teal-400" /> PCATP Architectural Roles
              </span>
            </div>
          </div>

          {/* Interactive Architectural Preview Showcase */}
          <div className="mt-12 lg:mt-16 max-w-5xl mx-auto">
            <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-3 sm:p-5 shadow-2xl backdrop-blur-sm">
              <div className="flex items-center justify-between pb-3 px-2 border-b border-slate-800 mb-4 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-red-500/80" />
                  <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
                  <div className="h-3 w-3 rounded-full bg-green-500/80" />
                  <span className="text-xs text-slate-400 ml-2 font-mono">
                    archicraft_engine_v2.0 :: 10 Marla Luxury Villa (35' x 65')
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800 font-mono">
                    95% Privacy Rating
                  </span>
                  <span className="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800 font-mono">
                    92% Natural Daylight
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
                {/* 2D CAD Layout */}
                <div className="lg:col-span-7 flex flex-col">
                  <FloorPlanViewer type="10_marla_luxury" title="Interactive 2D Floor Plan (Ground Floor)" />
                </div>
                {/* 2D Elevation & Specifications */}
                <div className="lg:col-span-5 flex flex-col gap-4">
                  <ElevationViewer style="Modern Contemporary" floors={2} widthFt={35} />
                  <div className="bg-slate-950 rounded-2xl p-4 border border-slate-800 text-xs space-y-2">
                    <div className="flex items-center justify-between text-slate-300 font-semibold border-b border-slate-800/80 pb-1.5">
                      <span>Preliminary Construction Summary</span>
                      <span className="text-teal-400 font-mono">DHA Islamabad</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-slate-400 pt-1">
                      <div>Covered Area: <strong className="text-white">3,650 sq ft</strong></div>
                      <div>Floors: <strong className="text-white">Double Storey</strong></div>
                      <div>Bedrooms: <strong className="text-white">5 En-Suite</strong></div>
                      <div>Parking: <strong className="text-white">2 SUV Porch</strong></div>
                    </div>
                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                      <span className="text-slate-400">Preliminary Estimate:</span>
                      <span className="text-base font-bold text-teal-300 font-heading">PKR 2.85 Crore</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <p className="text-xs font-semibold text-teal-400 uppercase tracking-wider font-mono">
            Guided Multi-Step Workflow
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-heading">
            How ArchiCraft AI Works
          </h2>
          <p className="text-slate-400 text-sm">
            From plot measurements to detailed floor plans and budget breakdowns in four streamlined steps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              step: '01',
              title: 'Input Dimensions & Needs',
              desc: 'Select standard Pakistani plot presets (5, 7, 10 Marla, 1 Kanal) or custom dimensions. Add room requirements, floors, and drawing room privacy needs.',
              icon: Building,
            },
            {
              step: '02',
              title: 'AI Spatial Synthesis',
              desc: 'Intelligent spatial algorithms calculate door swings, lightwells, cross-ventilation, and front/rear setbacks complying with regional bylaws.',
              icon: Sparkles,
            },
            {
              step: '03',
              title: 'Interactive 2D & Elevation',
              desc: 'Inspect vector CAD blueprints with clickable rooms, dimensions, compass orientation, and front exterior architectural elevations.',
              icon: Maximize2,
            },
            {
              step: '04',
              title: 'Preliminary BOQ & Review',
              desc: 'Receive immediate Pakistani construction cost estimates (grey structure, finishing, materials) and collaborate with licensed PCATP architects.',
              icon: Calculator,
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="bg-slate-900/60 border border-slate-800 hover:border-teal-500/40 rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 group"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="font-mono text-2xl font-extrabold text-teal-400/40 group-hover:text-teal-400 transition-colors">
                    {item.step}
                  </span>
                  <div className="p-2.5 rounded-xl bg-slate-800/80 group-hover:bg-teal-500/20 text-slate-300 group-hover:text-teal-300 transition-colors">
                    <Icon className="h-5 w-5" />
                  </div>
                </div>
                <h3 className="text-base font-bold text-white mb-2 font-heading">{item.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* PAKISTANI RESIDENTIAL PLOT TEMPLATES SHOWCASE */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
            <div>
              <p className="text-xs font-semibold text-teal-400 uppercase tracking-wider font-mono">
                Standard Plot Configurations
              </p>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mt-1 font-heading">
                Pakistani Residential Plot Blueprints
              </h2>
              <p className="text-slate-400 text-sm mt-1">
                Pre-configured for Bahria Town, DHA, CDA Islamabad, and LDA Lahore societies.
              </p>
            </div>

            {/* Plot Tabs */}
            <div className="flex items-center bg-slate-950 p-1.5 rounded-xl border border-slate-800 gap-1 overflow-x-auto">
              {[
                { id: '5_marla', label: '5 Marla (25×45)' },
                { id: '7_marla', label: '7 Marla (30×52.5)' },
                { id: '10_marla', label: '10 Marla (35×65)' },
                { id: '1_kanal', label: '1 Kanal (50×90)' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActivePlotTab(tab.id as any)}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                    activePlotTab === tab.id
                      ? 'bg-teal-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content Display */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {MOCK_TEMPLATES.filter((t) => t.plotCategory === activePlotTab).map((tpl) => (
              <div
                key={tpl.id}
                className="bg-slate-950 border border-slate-800/80 hover:border-teal-500/50 rounded-2xl p-5 flex flex-col justify-between transition-all group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
                      {tpl.plotDimensions}
                    </span>
                    <span className="text-xs text-slate-400 font-semibold">{tpl.floors} Storey</span>
                  </div>

                  <h3 className="text-base font-bold text-white font-heading group-hover:text-teal-300 transition-colors">
                    {tpl.name}
                  </h3>
                  <p className="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed">
                    {tpl.description}
                  </p>

                  <div className="grid grid-cols-3 gap-2 py-4 my-4 border-y border-slate-900 text-center text-xs">
                    <div>
                      <p className="text-slate-400">Bedrooms</p>
                      <p className="font-bold text-white mt-0.5">{tpl.bedrooms}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Bathrooms</p>
                      <p className="font-bold text-white mt-0.5">{tpl.bathrooms}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Covered Area</p>
                      <p className="font-bold text-white mt-0.5">{tpl.areaSqFt} sq ft</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {tpl.features.slice(0, 3).map((f) => (
                      <span key={f} className="text-[11px] px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between gap-2">
                  <div>
                    <p className="text-[10px] text-slate-400 uppercase">Est. Construction</p>
                    <p className="text-sm font-bold text-teal-300 font-heading">{formatPKR(tpl.budgetPKR)}</p>
                  </div>
                  <Link
                    to={`/app/designs/new?templateId=${tpl.id}`}
                    className="px-3.5 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold shadow-md transition-colors"
                  >
                    Use Template
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* INTERACTIVE PRELIMINARY COST ESTIMATION WIDGET */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left explanation */}
            <div className="lg:col-span-5 space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 text-xs font-semibold">
                <Calculator className="h-3.5 w-3.5" /> Preliminary BOQ Engine
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-white font-heading">
                Instant Pakistani Construction Cost Estimation
              </h2>
              <p className="text-sm text-slate-300 leading-relaxed">
                Estimate realistic construction costs based on current Pakistani market rates for cement, steel, bricks, plumbing, electrical, and finishing materials.
              </p>

              <div className="space-y-2 pt-2 text-xs text-slate-400">
                <p className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-teal-400" /> Ground + First Floor Double Storey calculation
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-teal-400" /> Grade-60 Deformed Rebar & OPC Cement benchmarking
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-teal-400" /> Includes 5% Inflation & Material Contingency
                </p>
              </div>

              <div className="pt-4">
                <Link
                  to="/app/cost-estimation"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold shadow-lg transition-colors"
                >
                  <span>Open Full Cost Estimation Module</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>

            {/* Right Interactive Card */}
            <div className="lg:col-span-7 bg-slate-950 border border-slate-800 rounded-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <span className="text-xs font-semibold text-white uppercase tracking-wider">Interactive Cost Sandbox</span>
                <span className="text-xs text-teal-400 font-mono">Rates: October 2026</span>
              </div>

              {/* Slider for Covered Area */}
              <div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="text-slate-300 font-medium">Covered Construction Area</span>
                  <span className="font-mono font-bold text-teal-300 text-sm">{calcArea.toLocaleString()} sq ft</span>
                </div>
                <input
                  type="range"
                  min="900"
                  max="6500"
                  step="50"
                  value={calcArea}
                  onChange={(e) => setCalcArea(Number(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-mono">
                  <span>900 sq ft (5 Marla)</span>
                  <span>2,200 sq ft (10 Marla)</span>
                  <span>4,500+ sq ft (1 Kanal)</span>
                </div>
              </div>

              {/* Finishing Quality Buttons */}
              <div>
                <label className="block text-xs text-slate-300 font-medium mb-2">Finishing Specification Level</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'standard', name: 'Standard', rate: 'PKR 6,600/sqft', desc: 'Local tiles & standard fittings' },
                    { id: 'premium', name: 'Premium', rate: 'PKR 8,000/sqft', desc: 'Spanish porcelain & solid wood' },
                    { id: 'luxury', name: 'Luxury', rate: 'PKR 10,400/sqft', desc: 'Imported marble & smart home' },
                  ].map((tier) => (
                    <button
                      key={tier.id}
                      type="button"
                      onClick={() => setCalcTier(tier.id as any)}
                      className={`p-3 rounded-xl text-left border transition-all ${
                        calcTier === tier.id
                          ? 'bg-teal-950/60 border-teal-500 text-white'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <p className="text-xs font-bold">{tier.name}</p>
                      <p className="text-[11px] text-teal-400 font-mono mt-0.5">{tier.rate}</p>
                      <p className="text-[10px] text-slate-400 mt-1">{tier.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Live Output */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div>
                  <p className="text-xs text-slate-400">Total Preliminary Estimated Cost</p>
                  <p className="text-2xl sm:text-3xl font-extrabold text-white font-heading mt-0.5">
                    {formatPKR(estCost)}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Grey structure: ~{formatPKR(calcArea * 3500)} | Finishing: ~{formatPKR(estCost - calcArea * 3500)}
                  </p>
                </div>
                <Link
                  to={`/app/designs/new?area=${calcArea}`}
                  className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold transition-colors shrink-0"
                >
                  Create Matching Plan
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ROLE BENEFITS: HOMEOWNERS & ARCHITECTS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <p className="text-xs font-semibold text-teal-400 uppercase tracking-wider font-mono">
            Designed for Collaboration
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-heading">
            Dual Workflows for Clients & Architects
          </h2>
          <p className="text-slate-400 text-sm">
            Bridging the communication gap between family requirements and technical architectural documentation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* For Homeowners */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-6">
            <div className="h-12 w-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white font-heading">For Homeowners & Families</h3>
              <p className="text-xs text-slate-400 mt-1">
                Explore architectural possibilities before investing in expensive revisions.
              </p>
            </div>
            <ul className="space-y-3 text-xs text-slate-300">
              <li className="flex items-start gap-2.5">
                <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Describe your living style in natural Urdu/English and view instant 2D floor plans.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Ensure proper cultural zoning: separate guest drawing room and family privacy.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Simulate construction budgets to prevent cost overruns during grey structure phases.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Export presentation summaries to review with your family and contractor.</span>
              </li>
            </ul>
          </div>

          {/* For Architects */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-6">
            <div className="h-12 w-12 rounded-2xl bg-teal-500/20 text-teal-400 flex items-center justify-center border border-teal-500/30">
              <FileCheck className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white font-heading">For Professional Architects & Studios</h3>
              <p className="text-xs text-slate-400 mt-1">
                Accelerate conceptual ideation and streamline client onboarding.
              </p>
            </div>
            <ul className="space-y-3 text-xs text-slate-300">
              <li className="flex items-start gap-2.5">
                <CheckCircle className="h-4 w-4 text-teal-400 shrink-0 mt-0.5" />
                <span>Inspect automated setback compliance checks against CDA, LDA, and DHA guidelines.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle className="h-4 w-4 text-teal-400 shrink-0 mt-0.5" />
                <span>Add professional redline review annotations directly on client-generated floor plans.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle className="h-4 w-4 text-teal-400 shrink-0 mt-0.5" />
                <span>Export standardized room schedules, areas, and preliminary BOQs for AutoCAD/Revit.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle className="h-4 w-4 text-teal-400 shrink-0 mt-0.5" />
                <span>Maintain project revision histories and side-by-side alternative comparisons.</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* FREQUENTLY ASKED QUESTIONS */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12 space-y-3">
          <p className="text-xs font-semibold text-teal-400 uppercase tracking-wider font-mono">
            Clear Answers
          </p>
          <h2 className="text-3xl font-bold text-white font-heading">Frequently Asked Questions</h2>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, idx) => (
            <div
              key={idx}
              className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden transition-all"
            >
              <button
                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                className="w-full p-5 text-left flex items-center justify-between text-sm font-semibold text-white hover:text-teal-300 transition-colors"
              >
                <span>{faq.q}</span>
                <ChevronRight
                  className={`h-4 w-4 text-slate-400 transition-transform ${
                    activeFaq === idx ? 'rotate-90 text-teal-400' : ''
                  }`}
                />
              </button>
              {activeFaq === idx && (
                <div className="px-5 pb-5 text-xs text-slate-300 leading-relaxed border-t border-slate-800/60 pt-3">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* FINAL CALL TO ACTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-tr from-teal-950 via-slate-900 to-slate-950 border border-teal-800/60 rounded-3xl p-8 sm:p-14 text-center space-y-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-blueprint opacity-30 pointer-events-none" />
          <div className="relative z-10 max-w-2xl mx-auto space-y-4">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-heading">
              Ready to Plan Your Next Architectural Project?
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Explore intelligent Pakistani plot layouts, customize room requirements, and generate preliminary construction budgets in minutes.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Link
                to="/app/designs/new"
                className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-sm shadow-xl shadow-teal-900/50 transition-all hover:-translate-y-0.5"
              >
                Start Designing Now
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all"
              >
                Sign In to Workspace
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
