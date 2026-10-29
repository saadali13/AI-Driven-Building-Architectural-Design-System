import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  Wand2, 
  FolderKanban, 
  Calculator, 
  ShieldCheck, 
  Settings, 
  Box, 
  Sparkles, 
  ArrowRight, 
  Compass, 
  Clock, 
  FileText, 
  X,
  Layers,
  ChevronRight,
  Home,
  Users,
  Bell
} from 'lucide-react';

export default function CommandPaletteModal({
  isOpen,
  onClose,
  onNavigate,
  onOpenStudio,
  userRole = 'HOMEOWNER',
  projects = []
}) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);

  const QUICK_ACTIONS = [
    { id: 'new-design', title: 'Generate AI Floor Plan & 3D', category: 'Creation', icon: Wand2, badge: 'AI Generator' },
    { id: 'projects', title: 'View Saved Blueprints & Projects', category: 'Navigation', icon: FolderKanban, badge: 'Portfolio' },
    { id: 'cost-estimation', title: 'Open Pakistani Construction BOQ', category: 'Finance', icon: Calculator, badge: 'PKR Rates' },
    { id: 'studio-5marla', title: 'Launch 3D WebGL Building Studio', category: 'Studio', icon: Box, badge: '3D Viewport', action: () => onOpenStudio && onOpenStudio('5marla') },
    { id: 'notifications', title: 'Society & Municipal Bylaws Alerts', category: 'Compliance', icon: ShieldCheck, badge: 'CDA / LDA' },
    { id: 'settings', title: 'Profile, Units & Security Settings', category: 'Settings', icon: Settings, badge: 'Account' },
  ];

  // Pre-seed search items
  const allItems = [
    ...QUICK_ACTIONS.map(a => ({ ...a, type: 'action' })),
    ...projects.map(p => ({
      id: `proj_${p.id}`,
      title: p.name || p.title,
      category: 'Project',
      icon: FolderKanban,
      badge: p.plotSize || p.plot_size || 'Residential',
      type: 'project',
      action: () => {
        if (onOpenStudio) onOpenStudio('5marla');
      }
    })),
    { id: 'plot-3m', title: '3 Marla Compact Urban Infill Blueprint (20x34)', category: 'Templates', icon: Home, badge: '680 sq ft', type: 'template', action: () => onOpenStudio && onOpenStudio('3marla') },
    { id: 'plot-5m', title: '5 Marla Double Story Luxury Villa (25x45)', category: 'Templates', icon: Home, badge: '1,125 sq ft', type: 'template', action: () => onOpenStudio && onOpenStudio('5marla') },
    { id: 'plot-10m', title: '10 Marla Spanish Hacienda Villa (35x65)', category: 'Templates', icon: Home, badge: '2,275 sq ft', type: 'template', action: () => onOpenStudio && onOpenStudio('10marla') },
    { id: 'plot-1k', title: '1 Kanal Modern Executive Estate (50x90)', category: 'Templates', icon: Home, badge: '4,500 sq ft', type: 'template', action: () => onOpenStudio && onOpenStudio('1kanal') },
  ];

  const filteredItems = allItems.filter(item => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return item.title.toLowerCase().includes(q) || item.category.toLowerCase().includes(q) || item.badge.toLowerCase().includes(q);
  });

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus();
      }, 50);
    }
  }, [isOpen]);

  // Handle keyboard events (Up, Down, Enter, Escape)
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % (filteredItems.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + filteredItems.length) % (filteredItems.length || 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const selected = filteredItems[selectedIndex];
        if (selected) {
          executeItem(selected);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredItems]);

  const executeItem = (item) => {
    onClose();
    if (item.action) {
      item.action();
    } else if (onNavigate) {
      onNavigate(item.id);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 sm:pt-28 px-4 bg-slate-950/70 backdrop-blur-md animate-in fade-in duration-150">
      <div 
        className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[75vh]"
        onClick={e => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
          <Search className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command, search projects, or explore templates..."
            className="flex-1 bg-transparent text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none font-medium"
          />
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredItems.length === 0 ? (
            <div className="py-12 text-center text-slate-400 dark:text-slate-500 text-sm">
              <Compass className="w-8 h-8 mx-auto mb-2 opacity-40 text-blue-500" />
              <p className="font-semibold text-slate-700 dark:text-slate-300">No matching results found</p>
              <p className="text-xs text-slate-400 mt-1">Try searching for "5 Marla", "BOQ", "3D", or "Floor Plan".</p>
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id + idx}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  onClick={() => executeItem(item)}
                  className={`flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl cursor-pointer transition text-xs sm:text-sm font-medium ${
                    isSelected 
                      ? 'bg-blue-600 text-white shadow-xs' 
                      : 'text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      isSelected 
                        ? 'bg-white/20 text-white' 
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 truncate">
                      <span className="truncate block font-semibold">{item.title}</span>
                      <span className={`text-[10px] uppercase font-mono tracking-wider block ${
                        isSelected ? 'text-blue-100' : 'text-slate-400'
                      }`}>
                        {item.category}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md border ${
                      isSelected 
                        ? 'bg-white/20 text-white border-white/30' 
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                    }`}>
                      {item.badge}
                    </span>
                    <ArrowRight className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Keyboard Navigation Shortcuts */}
        <div className="px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <div className="flex items-center gap-3">
            <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border rounded shadow-2xs">↑</kbd> <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border rounded shadow-2xs">↓</kbd> to navigate</span>
            <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border rounded shadow-2xs">↵</kbd> to select</span>
            <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border rounded shadow-2xs">ESC</kbd> to close</span>
          </div>
          <span className="hidden sm:inline text-blue-600 dark:text-blue-400 font-bold">ArchAI Command v2.4</span>
        </div>
      </div>
    </div>
  );
}
