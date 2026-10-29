import React from 'react';
import { Link } from 'react-router-dom';
import {
  Compass,
  Layers,
  Cpu,
  ShieldCheck,
  CheckCircle,
  FileCode,
  ArrowRight,
  BookOpen,
  Award,
  Terminal,
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Header */}
      <div className="text-center space-y-4">
        <span className="text-xs font-mono font-semibold px-3 py-1 rounded-full bg-teal-950 text-teal-300 border border-teal-800">
          FINAL YEAR PROJECT (FYP) DOCUMENTATION
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-heading">
          AI-Driven Building Architectural Design System
        </h1>
        <p className="text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
          An intelligent computer-aided architectural design system bridging generative spatial algorithms with Pakistani residential bylaws, cultural privacy guidelines, and preliminary construction economics.
        </p>
      </div>

      {/* Abstract & Motivation */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4">
        <h2 className="text-xl font-bold text-white font-heading flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-teal-400" />
          Project Abstract & Motivation
        </h2>
        <p className="text-sm text-slate-300 leading-relaxed">
          In Pakistan, urban housing construction across societies such as DHA, Bahria Town, CDA (Islamabad), and LDA (Lahore) often suffers from a disconnection between homeowner spatial aspirations and technical architectural compliance. Homeowners frequently struggle to communicate their cultural lifestyle needs—such as separate drawing room purdah circulation, dirty kitchens, prayer spaces, and natural cross-ventilation—while managing tight construction budgets.
        </p>
        <p className="text-sm text-slate-300 leading-relaxed">
          <strong>ArchiCraft AI</strong> addresses this challenge by providing an end-to-end web system that ingests natural-language design briefs or structured requirements, generates compliant 2D CAD floor plans, and delivers synchronized preliminary Bill of Quantities (BOQ) with realistic Pakistani market material rates.
        </p>
      </div>

      {/* System Architecture Diagram */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
        <h2 className="text-xl font-bold text-white font-heading flex items-center gap-2">
          <Cpu className="h-5 w-5 text-teal-400" />
          Technical System Architecture
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <span className="text-[11px] font-mono text-teal-400 uppercase font-bold">Layer 1: Frontend UI/UX</span>
            <h4 className="text-sm font-bold text-white">React 19 + TypeScript + Vite</h4>
            <p className="text-slate-400">
              Responsive SaaS application featuring interactive 2D vector CAD canvas, role-based dashboards, and multi-step requirement wizards.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <span className="text-[11px] font-mono text-teal-400 uppercase font-bold">Layer 2: AI & Spatial Engine</span>
            <h4 className="text-sm font-bold text-white">Spatial Synthesis Pipeline</h4>
            <p className="text-slate-400">
              Multi-phase constraint satisfaction algorithm computing setback matrices, lightwells, door clearances, and privacy zoning.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <span className="text-[11px] font-mono text-teal-400 uppercase font-bold">Layer 3: Economics & BOQ</span>
            <h4 className="text-sm font-bold text-white">Construction Cost Engine</h4>
            <p className="text-slate-400">
              Parametric cost modeling using monthly regional indices for OPC cement, Grade-60 steel, masonry bricks, and PEC labour ratios.
            </p>
          </div>
        </div>
      </div>

      {/* Technical Boundaries & Disclaimers */}
      <div className="bg-amber-950/20 border border-amber-900/50 rounded-3xl p-6 sm:p-8 space-y-4">
        <div className="flex items-center gap-2 text-amber-300 font-bold font-heading text-lg">
          <ShieldCheck className="h-5 w-5 text-amber-400" />
          Technical Scope & AI Integration Boundaries
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">
          This platform strictly serves as an <strong>architectural planning, spatial exploration, and preliminary cost assistance system</strong>. It is designed to empower human architects and homeowners, not replace professional civil and structural engineering:
        </p>
        <ul className="space-y-2 text-xs text-slate-300">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
            <span>All generated floor plans require independent site soil testing and load-bearing verification by a PEC-registered structural engineer.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
            <span>Preliminary cost calculations are planning estimates and do not constitute legal contractor tender bids or fixed price agreements.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
            <span>In production, the frontend connects to backend AI generation microservices via clean REST/JSON boundaries.</span>
          </li>
        </ul>
      </div>

      {/* Academic Credits */}
      <div className="text-center pt-4">
        <Link
          to="/app/designs/new"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-sm shadow-xl transition-all"
        >
          <span>Launch AI Design System</span>
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
};
