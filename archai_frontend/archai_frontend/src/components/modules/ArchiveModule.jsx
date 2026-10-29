import React, { useState } from 'react';
import { 
  Archive, 
  Search, 
  RotateCcw, 
  Download, 
  Trash2, 
  FileCode, 
  FileText, 
  CheckCircle2, 
  Calendar, 
  Home, 
  Box, 
  ExternalLink,
  Layers,
  Check
} from 'lucide-react';

const ARCHIVED_PROJECTS = [
  {
    id: 'arch_1',
    name: '10 Marla Executive Estate Design',
    type: '10-Marla Residential',
    archiveDate: 'Aug 04, 2024',
    dimensions: '35ft x 65ft',
    roomsCount: 6,
    estCost: 'PKR 26,400,000',
    exportedFormats: ['DWG', 'DXF', 'PDF', 'OBJ'],
    author: 'Lead Architectural Director',
    thumbnail: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'arch_2',
    name: '1 Kanal Modern Luxury Villa Layout',
    type: '1-Kanal Luxury Villa',
    archiveDate: 'Jul 28, 2024',
    dimensions: '50ft x 90ft',
    roomsCount: 9,
    estCost: 'PKR 48,500,000',
    exportedFormats: ['DWG', 'PDF', 'GLB'],
    author: 'BIM & Parametric Specialist',
    thumbnail: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'arch_3',
    name: 'Contemporary Farmhouse Spatial Blueprint',
    type: '2-Kanal Farmhouse',
    archiveDate: 'Jul 15, 2024',
    dimensions: '75ft x 120ft',
    roomsCount: 8,
    estCost: 'PKR 65,000,000',
    exportedFormats: ['DWG', 'DXF', 'PDF'],
    author: 'Senior Project Engineer',
    thumbnail: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'arch_4',
    name: '5 Marla Compact Residential Elevation',
    type: '5-Marla Compact',
    archiveDate: 'Jun 30, 2024',
    dimensions: '25ft x 50ft',
    roomsCount: 4,
    estCost: 'PKR 14,850,000',
    exportedFormats: ['DWG', 'PDF'],
    author: 'Lead Architectural Director',
    thumbnail: 'https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=400&q=80'
  }
];

export default function ArchiveModule({ onOpenStudio }) {
  const [projects, setProjects] = useState(ARCHIVED_PROJECTS);
  const [searchQuery, setSearchQuery] = useState('');
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3500);
  };

  const handleRestore = (project) => {
    setProjects(projects.filter(p => p.id !== project.id));
    showToast(`"${project.name}" restored to active workspace.`);
  };

  const handleDownloadZip = (projectName) => {
    showToast(`Downloading CAD & PDF bundle for "${projectName}"...`);
  };

  const handleDeletePermanent = (projectId, projectName) => {
    setProjects(projects.filter(p => p.id !== projectId));
    showToast(`Archive for "${projectName}" deleted.`);
  };

  const filtered = projects.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.author.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 text-slate-900 font-sans">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-xl flex items-center gap-2.5 text-xs font-semibold animate-in fade-in">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Archive className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Blueprint Archive &amp; Version Vault
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Historical design iterations, superseded floor plans, and exported architectural CAD artifacts.
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search archived blueprints..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white shadow-2xs"
          />
        </div>
      </div>

      {/* Archived Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filtered.map((proj) => (
          <div
            key={proj.id}
            className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden hover:shadow-md hover:scale-[1.01] transition-all duration-200 flex flex-col group"
          >
            <div className="relative h-48 bg-slate-900 overflow-hidden">
              <img
                src={proj.thumbnail}
                alt={proj.name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-transparent to-transparent"></div>
              <div className="absolute top-3.5 left-3.5">
                <span className="px-2.5 py-1 rounded-full bg-white/90 text-slate-800 text-[10px] font-mono font-bold border border-slate-200 shadow-2xs">
                  {proj.type}
                </span>
              </div>
              <div className="absolute bottom-3.5 left-3.5 right-3.5 flex items-center justify-between text-white">
                <span className="font-bold text-sm truncate">{proj.name}</span>
                <span className="font-mono text-xs font-bold text-emerald-300">{proj.estCost}</span>
              </div>
            </div>

            <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
              <div className="space-y-1.5 text-xs text-slate-600">
                <div className="flex justify-between">
                  <span className="text-slate-400">Dimensions:</span>
                  <span className="font-mono font-semibold text-slate-800">{proj.dimensions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Author:</span>
                  <span className="font-medium text-slate-800">{proj.author}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Archived Date:</span>
                  <span className="font-mono text-slate-500">{proj.archiveDate}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleRestore(proj)}
                  className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition flex items-center justify-center gap-1.5 cursor-pointer shadow-xs shadow-blue-500/20"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Restore</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleDownloadZip(proj.name)}
                  className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition cursor-pointer"
                  title="Download CAD Bundle"
                >
                  <Download className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  onClick={() => handleDeletePermanent(proj.id, proj.name)}
                  className="p-2 bg-rose-50 hover:bg-rose-100 text-rose-600 rounded-xl transition cursor-pointer"
                  title="Delete Permanently"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
