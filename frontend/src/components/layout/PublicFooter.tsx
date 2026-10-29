import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, AlertCircle, MapPin, Mail, Phone, ExternalLink, ShieldCheck } from 'lucide-react';

export const PublicFooter: React.FC = () => {
  return (
    <footer className="bg-slate-950 text-slate-400 border-t border-slate-800">
      {/* Disclaimer Banner */}
      <div className="bg-amber-950/30 border-b border-amber-900/40 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-start gap-3 text-xs text-amber-300/90 leading-relaxed">
          <AlertCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
          <p>
            <strong className="text-amber-200">Architectural & Regulatory Notice:</strong> ArchiCraft AI generates conceptual 2D floor plans, spatial adjacencies, and preliminary construction cost estimates for architectural planning. All structural drawings, plumbing risers, electrical schematics, and load-bearing designs must be stamped and validated by a licensed architect registered with the Pakistan Council of Architects and Town Planners (PCATP) and the Pakistan Engineering Council (PEC) prior to municipal submission (CDA, LDA, DHA, KDA, RDA).
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand Col */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="h-9 w-9 rounded-lg bg-teal-500/20 text-teal-400 flex items-center justify-center border border-teal-500/30">
                <Compass className="h-5 w-5" />
              </div>
              <span className="font-heading font-bold text-xl text-white">ArchiCraft AI</span>
            </Link>
            <p className="text-sm text-slate-400 max-w-sm leading-relaxed">
              Final Year Project (FYP): AI-Driven Building Architectural Design & Construction Cost Estimation Platform. Empowering homeowners and architects with smart layouts tailored for Pakistani residential standards.
            </p>
            <div className="pt-2 text-xs text-slate-400 space-y-1.5">
              <p className="flex items-center gap-2">
                <MapPin className="h-3.5 w-3.5 text-teal-400" /> Department of Computer Science & Engineering, Pakistan
              </p>
              <p className="flex items-center gap-2">
                <Mail className="h-3.5 w-3.5 text-teal-400" /> fyp.support@archicraft.edu.pk
              </p>
              <p className="flex items-center gap-2">
                <Phone className="h-3.5 w-3.5 text-teal-400" /> +92 (51) 9265555 (Academic Hotline)
              </p>
            </div>
          </div>

          {/* Pakistani Plot Presets */}
          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-4 font-heading">
              Plot Dimensions
            </h4>
            <ul className="space-y-2.5 text-sm">
              <li>
                <Link to="/templates?preset=5_marla" className="hover:text-teal-400 transition-colors">
                  5 Marla (25' × 45') Plans
                </Link>
              </li>
              <li>
                <Link to="/templates?preset=7_marla" className="hover:text-teal-400 transition-colors">
                  7 Marla (30' × 52.5') Plans
                </Link>
              </li>
              <li>
                <Link to="/templates?preset=10_marla" className="hover:text-teal-400 transition-colors">
                  10 Marla (35' × 65') Plans
                </Link>
              </li>
              <li>
                <Link to="/templates?preset=1_kanal" className="hover:text-teal-400 transition-colors">
                  1 Kanal (50' × 90') Plans
                </Link>
              </li>
              <li>
                <Link to="/templates" className="hover:text-teal-400 transition-colors">
                  Custom Plot Configurations
                </Link>
              </li>
            </ul>
          </div>

          {/* Platform Workflows */}
          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-4 font-heading">
              System Modules
            </h4>
            <ul className="space-y-2.5 text-sm">
              <li>
                <Link to="/app/designs/new" className="hover:text-teal-400 transition-colors">
                  AI Design Workspace
                </Link>
              </li>
              <li>
                <Link to="/cost-estimation-preview" className="hover:text-teal-400 transition-colors">
                  PKR Preliminary BOQ Estimator
                </Link>
              </li>
              <li>
                <Link to="/app/compare" className="hover:text-teal-400 transition-colors">
                  Design Comparison Matrix
                </Link>
              </li>
              <li>
                <Link to="/templates" className="hover:text-teal-400 transition-colors">
                  Residential Template Library
                </Link>
              </li>
              <li>
                <Link to="/app/dashboard" className="hover:text-teal-400 transition-colors">
                  Role-Based Workspaces
                </Link>
              </li>
            </ul>
          </div>

          {/* Compliance & Academic */}
          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider mb-4 font-heading">
              Bylaws & Reference
            </h4>
            <ul className="space-y-2.5 text-sm">
              <li>
                <Link to="/help#cda" className="hover:text-teal-400 transition-colors">
                  CDA Islamabad Building Codes
                </Link>
              </li>
              <li>
                <Link to="/help#lda" className="hover:text-teal-400 transition-colors">
                  LDA Lahore Residential Bylaws
                </Link>
              </li>
              <li>
                <Link to="/help#dha" className="hover:text-teal-400 transition-colors">
                  DHA Town Planning Standards
                </Link>
              </li>
              <li>
                <Link to="/about" className="hover:text-teal-400 transition-colors">
                  System Architecture & AI Docs
                </Link>
              </li>
              <li>
                <Link to="/help" className="hover:text-teal-400 transition-colors">
                  FAQs & Support Center
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom row */}
        <div className="pt-8 mt-8 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
          <p>© {new Date().getFullYear()} ArchiCraft AI Architectural Design System. Academic Final Year Project (FYP).</p>
          <div className="flex items-center gap-6">
            <Link to="/help" className="hover:text-slate-300">Privacy Policy</Link>
            <Link to="/help" className="hover:text-slate-300">Terms of Service</Link>
            <Link to="/help" className="hover:text-slate-300">Disclaimer</Link>
            <span className="flex items-center gap-1 text-teal-400">
              <ShieldCheck className="h-3.5 w-3.5" /> PCATP Standard Guidelines
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
