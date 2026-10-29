import React from 'react';
import { Building2, Globe, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import { LOGO_URL } from './BrandLogo';

export default function Footer({ setActiveTab }) {
  return (
    <footer className="bg-white border-t border-slate-200 py-12 font-sans text-slate-900">
      <div className="max-w-7xl mx-auto px-4 md:px-8 grid grid-cols-1 md:grid-cols-4 gap-8">
        
        {/* Brand */}
        <div className="md:col-span-2 space-y-3">
          <div 
            onClick={() => setActiveTab('landing')}
            className="flex items-center gap-3 cursor-pointer group w-fit"
          >
            <div className="w-8 h-8 rounded-xl bg-white border border-slate-200 p-0.5 shadow-xs flex items-center justify-center shrink-0">
              <img src={LOGO_URL} alt="ArchAI Logo" className="w-full h-full object-contain rounded-lg" />
            </div>
            <span className="text-base font-bold text-slate-900 tracking-tight">ArchAI Studio</span>
          </div>
          
          <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
            Generative architectural intelligence for residential estates. Synthesizing 5-Marla and 10-Marla elevations, CAD DXF packages, and localized PKR cost models.
          </p>

          <div className="flex items-center gap-2 pt-1 text-xs text-slate-400 font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
            <span>Supervised by Dr. Aamer Nadeem • CUST AI Lab</span>
          </div>
        </div>

        {/* Quick Links */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3">Platform Views</h4>
          <ul className="space-y-2 text-xs text-slate-500 font-medium">
            <li>
              <button onClick={() => setActiveTab('landing')} className="hover:text-blue-600 transition cursor-pointer">
                Overview &amp; Elevations
              </button>
            </li>
            <li>
              <button onClick={() => setActiveTab('workspace')} className="hover:text-blue-600 transition cursor-pointer">
                AI Workspace Hub
              </button>
            </li>
            <li>
              <button onClick={() => setActiveTab('cost-estimator')} className="hover:text-blue-600 transition cursor-pointer">
                PKR Construction Matrix
              </button>
            </li>
            <li>
              <button onClick={() => setActiveTab('auth')} className="hover:text-blue-600 transition cursor-pointer">
                Sign In &amp; Register
              </button>
            </li>
          </ul>
        </div>

        {/* Legal & Standards */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3">Standards &amp; Bylaws</h4>
          <ul className="space-y-2 text-xs text-slate-500 font-medium">
            <li>Islamabad CDA Building Bylaws</li>
            <li>Rawalpindi RDA Setback Rules</li>
            <li>Lahore LDA &amp; DHA Residential Codes</li>
            <li>Karachi SBCA Structural Guidelines</li>
          </ul>
        </div>

      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-8 mt-8 pt-6 border-t border-slate-100 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-slate-400">
        <span>© 2026 ArchAI Generative Spatial Architecture. All rights reserved.</span>
        <div className="flex gap-4 font-mono text-[11px]">
          <span className="hover:text-slate-600 cursor-pointer">Privacy Policy</span>
          <span className="hover:text-slate-600 cursor-pointer">Terms of Service</span>
          <span className="hover:text-slate-600 cursor-pointer">ChromaDB Vector v2.4</span>
        </div>
      </div>
    </footer>
  );
}
