import React, { useState } from 'react';
import { X, Sun, Moon, Sparkles, Download, Layers, Check, Eye, Box, Sliders, Building2, MapPin } from 'lucide-react';
import { LOGO_URL } from './BrandLogo';

export default function StudioModal({ isOpen, onClose, initialModel = '5marla' }) {
  const [selectedModel, setSelectedModel] = useState(initialModel);
  const [lighting, setLighting] = useState('golden');
  const [material, setMaterial] = useState('concrete');
  const [isExporting, setIsExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState('');

  if (!isOpen) return null;

  const modelsData = {
    '5marla': {
      title: '5 Marla Contemporary Elevation',
      code: 'ISB-C5',
      location: 'Islamabad Capital Territory (DHA Phase 2)',
      dimensions: '25 ft × 50 ft (1,250 sq ft)',
      coveredArea: '2,250 sq ft (Double Storey)',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCIZ_gzlHItvEkrd_s2oLvHIwQxwxLF-zH0t6YySLx1ZJBEGYjdyqu5-kI4eg-hr8FzPMt4cejc2h5NDTJoBSh6k8R8eKnbNGm_gG9TnmfZH2yGsPGDgdeUJaKa-92TL3rUeZHPicwdP9E_WTDYEtI8XIeAxC54IYUKOAVWxS2WKdlSW4F5gzlSqWRLeMH_3a2agV5WO3D9SFUht1FsjD2LGuEMPEoeZA11y6KVNXEFQ3VHK7_pBq4p',
      estimatePKR: '₨ 14.85 Million',
    },
    '10marla': {
      title: '10 Marla Luxury Executive Villa',
      code: 'LHE-X10',
      location: 'Bahria Town Phase 8, Rawalpindi',
      dimensions: '35 ft × 65 ft (2,275 sq ft)',
      coveredArea: '4,100 sq ft (Triple Storey + Terrace)',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDkO77NXNsWDIxKQ2suXtvRo7MISROQiw8I29FgnoaH6Lj-zCWM-27IYbX9gYFukt6rr9Wg6C82Rg_x8B4BtgzOQShv5JkBeI8ZONz0bx17emZS_LN4pxS2cU26RyCD94zhN4jCyG5Ihg3RhLWCGE3GV52zKhr4qZbSoUT7YD7ubg44JpwTDO-LNtp7h7gWlOi0NGTpW7l4aGON1nbL7v2cmyX6-Nu5AxWsgrXQEgRGjWct3Ybem6Ni',
      estimatePKR: '₨ 26.40 Million',
    },
  };

  const current = modelsData[selectedModel] || modelsData['5marla'];

  const handleExport = (format) => {
    setIsExporting(true);
    setExportMessage(`Generating ${format} vector CAD package for ${current.code}...`);
    setTimeout(() => {
      setIsExporting(false);
      setExportMessage(`Successfully exported ${current.code}_architectural_plan.${format.toLowerCase()}`);
      setTimeout(() => setExportMessage(''), 4000);
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-900/70 backdrop-blur-sm font-sans">
      <div className="bg-white border border-slate-200 rounded-3xl shadow-2xl w-full max-w-6xl max-h-[92vh] overflow-hidden flex flex-col animate-in fade-in">
        
        {/* Modal Header */}
        <div className="px-8 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/90">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 p-1 shadow-xs flex items-center justify-center font-bold">
              <img src={LOGO_URL} alt="ArchAI Logo" className="w-full h-full object-contain rounded-lg" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h3 className="font-bold text-xl text-slate-900">{current.title}</h3>
                <span className="text-xs font-mono px-3 py-1 rounded-md bg-blue-50 text-blue-700 font-bold border border-blue-200">{current.code}</span>
              </div>
              <p className="text-sm font-medium text-slate-500 mt-0.5">{current.location} • {current.dimensions}</p>
            </div>
          </div>

          <button 
            type="button"
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-900 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 gap-0">
          
          {/* Main 3D Elevation Preview */}
          <div className="lg:col-span-8 bg-slate-900 relative p-6 flex flex-col justify-between min-h-[420px] lg:min-h-[520px]">
            
            {/* Model switcher tabs */}
            <div className="absolute top-6 left-6 z-10 flex gap-3">
              <button 
                type="button"
                onClick={() => setSelectedModel('5marla')} 
                className={`px-4 py-2.5 rounded-xl text-sm font-bold transition shadow-md cursor-pointer ${
                  selectedModel === '5marla' ? 'bg-blue-600 text-white shadow-blue-500/30' : 'bg-slate-900/90 text-slate-300 hover:text-white border border-slate-700'
                }`}
              >
                5-Marla Elevation
              </button>
              <button 
                type="button"
                onClick={() => setSelectedModel('10marla')} 
                className={`px-4 py-2.5 rounded-xl text-sm font-bold transition shadow-md cursor-pointer ${
                  selectedModel === '10marla' ? 'bg-blue-600 text-white shadow-blue-500/30' : 'bg-slate-900/90 text-slate-300 hover:text-white border border-slate-700'
                }`}
              >
                10-Marla Estate
              </button>
            </div>


            {/* Lighting Overlay */}
            <div className="absolute top-6 right-6 z-10 flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/80 text-white text-xs font-mono border border-slate-700">
              <Sun className="w-3.5 h-3.5 text-amber-400" />
              <span>{lighting === 'golden' ? 'Golden Hour 17:30' : lighting === 'morning' ? 'Diffused Morning 09:00' : 'Twilight 19:45'}</span>
            </div>

            {/* Preview Image */}
            <div className="relative w-full h-full rounded-2xl overflow-hidden group my-auto flex items-center justify-center">
              <img 
                src={current.image} 
                alt={current.title}
                className={`w-full h-full object-cover transition-all duration-500 ${
                  lighting === 'golden' ? 'brightness-105 contrast-105 saturate-110' :
                  lighting === 'morning' ? 'brightness-100 contrast-100' : 'brightness-75 contrast-125'
                }`}
              />

              <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur px-4 py-2 rounded-xl text-slate-900 border border-slate-200 shadow-sm max-w-sm">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block">Material Palette</span>
                <span className="text-xs font-bold text-slate-900 block">
                  {material === 'concrete' ? 'White Architectural Concrete + Dark Walnut Accents' :
                   material === 'stone' ? 'Vertical Slate Cladding + Bronze Anodized Frames' : 'Monolithic Brutalist Marble + Frameless Glass'}
                </span>
              </div>
            </div>

            {/* Notification Banner */}
            {exportMessage && (
              <div className="mt-3 p-3 rounded-xl bg-blue-600 text-white text-xs font-semibold flex items-center gap-2 animate-in fade-in z-20 shadow-md">
                <Check className="w-4 h-4 text-emerald-300" />
                <span>{exportMessage}</span>
              </div>
            )}
          </div>

          {/* Right Control Sidebar */}
          <div className="lg:col-span-4 bg-white p-6 flex flex-col justify-between border-l border-slate-200 space-y-6">
            <div>
              <h4 className="text-xs font-bold text-slate-900 uppercase font-mono tracking-wider mb-4 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-blue-600" />
                <span>Synthesis Controls</span>
              </h4>

              {/* Lighting controls */}
              <div className="mb-5">
                <label className="text-xs font-bold text-slate-700 block mb-2">Sunlight &amp; Atmosphere</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'golden', label: 'Golden Hour' },
                    { id: 'morning', label: 'Morning' },
                    { id: 'twilight', label: 'Twilight' },
                  ].map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setLighting(item.id)}
                      className={`px-3 py-2 rounded-xl text-xs font-bold border text-center transition cursor-pointer ${
                        lighting === item.id 
                          ? 'bg-blue-600 text-white border-blue-600 shadow-xs' 
                          : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Material selector */}
              <div className="mb-5">
                <label className="text-xs font-bold text-slate-700 block mb-2">Exterior Material Palette</label>
                <div className="space-y-2">
                  {[
                    { id: 'concrete', label: 'White Concrete & Wood', desc: 'Modern minimalist render' },
                    { id: 'stone', label: 'Vertical Slate & Bronze', desc: 'Textured stone facade' },
                    { id: 'marble', label: 'Brutalist Light Marble', desc: 'Luxury stone finish' },
                  ].map((mat) => (
                    <button
                      key={mat.id}
                      type="button"
                      onClick={() => setMaterial(mat.id)}
                      className={`w-full text-left p-3 rounded-xl border text-xs transition cursor-pointer flex items-center justify-between ${
                        material === mat.id
                          ? 'border-blue-600 bg-blue-50/50 text-blue-900 font-bold ring-1 ring-blue-500/20'
                          : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      <div>
                        <span className="block font-bold">{mat.label}</span>
                        <span className="text-[10px] text-slate-500">{mat.desc}</span>
                      </div>
                      {material === mat.id && <Check className="w-4 h-4 text-blue-600 shrink-0" />}
                    </button>
                  ))}
                </div>
              </div>

              {/* Cost Highlight */}
              <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block">Estimated Budget</span>
                <h4 className="text-base font-black text-emerald-700 font-mono">{current.estimatePKR}</h4>
              </div>
            </div>

            {/* Export Buttons */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => handleExport('DXF')}
                disabled={isExporting}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow-md shadow-blue-500/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 hover:scale-[1.01]"
              >
                <Download className="w-4 h-4" />
                <span>Export CAD Vector (DXF / DWG)</span>
              </button>
              <button
                type="button"
                onClick={() => handleExport('PDF')}
                disabled={isExporting}
                className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs rounded-xl transition flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Export Architectural PDF Plan</span>
              </button>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
}
