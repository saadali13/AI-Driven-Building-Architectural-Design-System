import React, { useState, useMemo } from 'react';
import { 
  Building2, 
  Layers, 
  Search, 
  Plus, 
  MoreVertical, 
  Eye, 
  Copy, 
  Trash2, 
  Download, 
  Share2, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  Sparkles, 
  ExternalLink,
  Filter,
  Check,
  FolderKanban,
  MapPin,
  Maximize2,
  DollarSign,
  LayoutGrid,
  List,
  Heart,
  Edit2,
  Archive,
  ArrowUpDown,
  X,
  Compass,
  FileCode
} from 'lucide-react';
import { useAuth, ROLES } from '../../context/AuthContext';

const INITIAL_PROJECTS = [
  {
    id: 'proj_1',
    name: '5 Marla Contemporary Residence',
    plotSize: '5-Marla (25 × 50)',
    coveredArea: '2,250 Sq.Ft',
    location: 'DHA Phase 2, Islamabad',
    status: 'Ready',
    progress: 100,
    costEstM: 14.85,
    style: 'Modern Contemporary',
    updatedAt: '2 hours ago',
    timestamp: Date.now() - 2 * 3600 * 1000,
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCIZ_gzlHItvEkrd_s2oLvHIwQxwxLF-zH0t6YySLx1ZJBEGYjdyqu5-kI4eg-hr8FzPMt4cejc2h5NDTJoBSh6k8R8eKnbNGm_gG9TnmfZH2yGsPGDgdeUJaKa-92TL3rUeZHPicwdP9E_WTDYEtI8XIeAxC54IYUKOAVWxS2WKdlSW4F5gzlSqWRLeMH_3a2agV5WO3D9SFUht1FsjD2LGuEMPEoeZA11y6KVNXEFQ3VHK7_pBq4p',
    roomsCount: '3 Bed • 3 Bath • 1 Kitchen',
    isFavorite: true,
    model: '5marla'
  },
  {
    id: 'proj_2',
    name: '10 Marla Luxury Executive Estate',
    plotSize: '10-Marla (35 × 65)',
    coveredArea: '4,100 Sq.Ft',
    location: 'Bahria Town Phase 8, Rawalpindi',
    status: 'Review',
    progress: 85,
    costEstM: 26.40,
    style: 'Spanish Villa',
    updatedAt: 'Yesterday',
    timestamp: Date.now() - 24 * 3600 * 1000,
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDkO77NXNsWDIxKQ2suXtvRo7MISROQiw8I29FgnoaH6Lj-zCWM-27IYbX9gYFukt6rr9Wg6C82Rg_x8B4BtgzOQShv5JkBeI8ZONz0bx17emZS_LN4pxS2cU26RyCD94zhN4jCyG5Ihg3RhLWCGE3GV52zKhr4qZbSoUT7YD7ubg44JpwTDO-LNtp7h7gWlOi0NGTpW7l4aGON1nbL7v2cmyX6-Nu5AxWsgrXQEgRGjWct3Ybem6Ni',
    roomsCount: '5 Bed • 6 Bath • 2 Kitchens',
    isFavorite: false,
    model: '10marla'
  },
  {
    id: 'proj_3',
    name: 'Modern Minimalist Villa Layout',
    plotSize: '1-Kanal (50 × 90)',
    coveredArea: '6,800 Sq.Ft',
    location: 'Gulberg Greens, Islamabad',
    status: 'In Progress',
    progress: 45,
    costEstM: 48.50,
    style: 'Minimalist Concrete',
    updatedAt: '3 days ago',
    timestamp: Date.now() - 72 * 3600 * 1000,
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&q=80',
    roomsCount: '6 Bed • 7 Bath • Pool',
    isFavorite: true,
    model: '1kanal'
  },
  {
    id: 'proj_4',
    name: '7 Marla Urban Townhouse Design',
    plotSize: '7-Marla (30 × 53)',
    coveredArea: '3,100 Sq.Ft',
    location: 'Sector F-7/2, Islamabad',
    status: 'Ready',
    progress: 100,
    costEstM: 21.20,
    style: 'Scandinavian Glass',
    updatedAt: '1 week ago',
    timestamp: Date.now() - 168 * 3600 * 1000,
    image: 'https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=600&q=80',
    roomsCount: '4 Bed • 4 Bath • Terrace',
    isFavorite: false,
    model: '5marla'
  }
];

export default function ProjectsModule({ onOpenStudio, onNewDesign }) {
  const { user } = useAuth();
  const [projects, setProjects] = useState(INITIAL_PROJECTS);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('latest'); // 'latest' | 'name' | 'cost-high' | 'cost-low'
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'
  const [activeMenuId, setActiveMenuId] = useState(null);
  const [toastMsg, setToastMsg] = useState('');
  
  // Modals for Rename & Delete
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null);

  const showNotification = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3500);
  };

  const toggleFavorite = (id, e) => {
    e.stopPropagation();
    setProjects(prev => prev.map(p => {
      if (p.id === id) {
        const nextFav = !p.isFavorite;
        showNotification(nextFav ? `Added "${p.name}" to favorites` : `Removed from favorites`);
        return { ...p, isFavorite: nextFav };
      }
      return p;
    }));
  };

  const handleDuplicateProject = (proj) => {
    const duplicated = {
      ...proj,
      id: `proj_${Date.now()}`,
      name: `${proj.name} (Copy)`,
      updatedAt: 'Just now',
      timestamp: Date.now(),
      isFavorite: false
    };
    setProjects([duplicated, ...projects]);
    setActiveMenuId(null);
    showNotification(`Duplicated: ${duplicated.name}`);
  };

  const openRenameModal = (proj) => {
    setRenameTarget(proj);
    setRenameValue(proj.name);
    setActiveMenuId(null);
  };

  const submitRename = () => {
    if (!renameValue.trim() || !renameTarget) return;
    setProjects(prev => prev.map(p => {
      if (p.id === renameTarget.id) {
        return { ...p, name: renameValue.trim(), updatedAt: 'Just now', timestamp: Date.now() };
      }
      return p;
    }));
    showNotification(`Renamed to "${renameValue.trim()}"`);
    setRenameTarget(null);
    setRenameValue('');
  };

  const confirmDelete = () => {
    if (!deleteTarget) return;
    setProjects(prev => prev.filter(p => p.id !== deleteTarget.id));
    showNotification(`Permanently deleted: ${deleteTarget.name}`);
    setDeleteTarget(null);
    setActiveMenuId(null);
  };

  const handleArchiveProject = (proj) => {
    setProjects(prev => prev.filter(p => p.id !== proj.id));
    setActiveMenuId(null);
    showNotification(`Archived "${proj.name}". Access in Version History.`);
  };

  const filteredAndSortedProjects = useMemo(() => {
    let result = projects.filter((p) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch = 
        p.name.toLowerCase().includes(q) ||
        p.location.toLowerCase().includes(q) ||
        p.plotSize.toLowerCase().includes(q) ||
        p.style.toLowerCase().includes(q);
      const matchesStatus = statusFilter === 'ALL' || 
        (statusFilter === 'FAVORITES' ? p.isFavorite : p.status === statusFilter);
      return matchesSearch && matchesStatus;
    });

    result.sort((a, b) => {
      if (sortBy === 'latest') return (b.timestamp || 0) - (a.timestamp || 0);
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'cost-high') return b.costEstM - a.costEstM;
      if (sortBy === 'cost-low') return a.costEstM - b.costEstM;
      return 0;
    });

    return result;
  }, [projects, searchQuery, statusFilter, sortBy]);

  return (
    <div className="w-full max-w-7xl mx-auto space-y-7 text-slate-900 dark:text-slate-100 font-sans pb-12">
      
      {/* Toast Feedback */}
      {toastMsg && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2.5 px-5 py-3.5 bg-slate-900 text-white rounded-2xl shadow-xl text-sm font-semibold animate-in fade-in">
          <Check className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header Bar */}
      <div className="p-6 md:p-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center gap-3.5 mb-1.5">
            <div className="p-2.5 rounded-2xl bg-blue-50 dark:bg-blue-900/40 border border-blue-100 dark:border-blue-800 text-blue-600 dark:text-blue-400 shadow-2xs">
              <FolderKanban className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Saved Projects &amp; Blueprints</h2>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Manage your 2D blueprints, 3D WebGL scenes, cost estimates, and CAD packages.
              </p>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onNewDesign}
          className="px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-2xl transition shadow-md shadow-blue-500/25 flex items-center gap-2 cursor-pointer shrink-0 hover:scale-[1.01]"
        >
          <Plus className="w-4 h-4" />
          <span>Synthesize New Design</span>
        </button>
      </div>

      {/* Search, Filter, Sort, View Controls */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-4 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xs">
        
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by title, location, or plot size..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white font-medium placeholder-slate-400 focus:outline-none focus:border-blue-600"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 lg:pb-0">
          {[
            { id: 'ALL', label: 'All Projects' },
            { id: 'Ready', label: 'BIM Ready' },
            { id: 'In Progress', label: 'In Progress' },
            { id: 'Review', label: 'Under Review' },
            { id: 'FAVORITES', label: '★ Pinned' },
          ].map((st) => (
            <button
              key={st.id}
              type="button"
              onClick={() => setStatusFilter(st.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                statusFilter === st.id
                  ? 'bg-blue-600 text-white shadow-2xs'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>

        {/* Sorting & Grid/List View Toggle */}
        <div className="flex items-center gap-2.5 shrink-0 border-t lg:border-t-0 pt-3 lg:pt-0 border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-transparent text-slate-700 dark:text-slate-200 font-bold focus:outline-none cursor-pointer"
            >
              <option value="latest" className="dark:bg-slate-900">Latest First</option>
              <option value="name" className="dark:bg-slate-900">Project Name (A-Z)</option>
              <option value="cost-high" className="dark:bg-slate-900">Budget: High to Low</option>
              <option value="cost-low" className="dark:bg-slate-900">Budget: Low to High</option>
            </select>
          </div>

          <div className="flex items-center p-1 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition cursor-pointer ${
                viewMode === 'grid'
                  ? 'bg-white dark:bg-slate-700 text-blue-600 shadow-2xs'
                  : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
              }`}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition cursor-pointer ${
                viewMode === 'list'
                  ? 'bg-white dark:bg-slate-700 text-blue-600 shadow-2xs'
                  : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Projects Render (Grid or List) */}
      {filteredAndSortedProjects.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl space-y-3">
          <FolderKanban className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-700 dark:text-slate-200">No architectural projects matched your query</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Try adjusting your search terms, changing the status filter, or create a brand new design synthesis.
          </p>
          <button
            type="button"
            onClick={() => { setSearchQuery(''); setStatusFilter('ALL'); }}
            className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-bold hover:bg-slate-200 transition cursor-pointer"
          >
            Clear Filters
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredAndSortedProjects.map((proj) => {
            const isMenuOpen = activeMenuId === proj.id;
            return (
              <div
                key={proj.id}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-xs hover:shadow-lg hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-200 flex flex-col group relative"
              >
                {/* Elevation Preview Cover */}
                <div 
                  className="w-full h-52 bg-cover bg-center relative border-b border-slate-100 dark:border-slate-800"
                  style={{ backgroundImage: `url('${proj.image}')` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/85 via-slate-950/20 to-transparent"></div>
                  
                  {/* Badges & Favorite */}
                  <div className="absolute top-3 left-3 flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border backdrop-blur-md ${
                      proj.status === 'Ready'
                        ? 'bg-emerald-500/90 text-white border-emerald-400'
                        : proj.status === 'Review'
                        ? 'bg-amber-500/90 text-white border-amber-400'
                        : 'bg-blue-600/90 text-white border-blue-400'
                    }`}>
                      {proj.status}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full bg-white/95 dark:bg-slate-900/95 text-slate-900 dark:text-white text-[10px] font-mono font-bold border border-slate-200 dark:border-slate-700 shadow-2xs">
                      {proj.plotSize}
                    </span>
                  </div>

                  {/* Actions & Heart */}
                  <div className="absolute top-3 right-3 flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={(e) => toggleFavorite(proj.id, e)}
                      className={`p-2 rounded-xl backdrop-blur-md border transition cursor-pointer ${
                        proj.isFavorite
                          ? 'bg-rose-500 text-white border-rose-400'
                          : 'bg-black/40 hover:bg-black/60 text-white border-white/20'
                      }`}
                      title={proj.isFavorite ? "Remove from Favorites" : "Add to Favorites"}
                    >
                      <Heart className="w-3.5 h-3.5 fill-current" />
                    </button>

                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setActiveMenuId(isMenuOpen ? null : proj.id)}
                        className="p-2 rounded-xl bg-black/40 hover:bg-black/60 text-white border border-white/20 backdrop-blur-md transition cursor-pointer"
                        title="Project Options"
                      >
                        <MoreVertical className="w-3.5 h-3.5" />
                      </button>

                      {/* Dropdown Menu */}
                      {isMenuOpen && (
                        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-1.5 shadow-2xl z-30 text-xs">
                          <button
                            type="button"
                            onClick={() => {
                              onOpenStudio && onOpenStudio(proj.model || '5marla');
                              setActiveMenuId(null);
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-xl text-left cursor-pointer"
                          >
                            <Eye className="w-3.5 h-3.5 text-blue-600" />
                            <span>Open 3D Studio</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => openRenameModal(proj)}
                            className="w-full flex items-center gap-2 px-3 py-2 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-xl text-left cursor-pointer"
                          >
                            <Edit2 className="w-3.5 h-3.5 text-amber-600" />
                            <span>Rename Project</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleDuplicateProject(proj)}
                            className="w-full flex items-center gap-2 px-3 py-2 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-xl text-left cursor-pointer"
                          >
                            <Copy className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Duplicate Project</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => {
                              showNotification(`Exporting DXF package for ${proj.name}...`);
                              setActiveMenuId(null);
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-xl text-left cursor-pointer"
                          >
                            <Download className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Export CAD (DXF)</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleArchiveProject(proj)}
                            className="w-full flex items-center gap-2 px-3 py-2 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-xl text-left cursor-pointer"
                          >
                            <Archive className="w-3.5 h-3.5 text-slate-500" />
                            <span>Archive Blueprint</span>
                          </button>

                          <div className="my-1 border-t border-slate-100 dark:border-slate-800"></div>

                          <button
                            type="button"
                            onClick={() => {
                              setDeleteTarget(proj);
                              setActiveMenuId(null);
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-xl text-left cursor-pointer font-bold"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Delete Project</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Title & Location on Cover */}
                  <div className="absolute bottom-3 left-4 right-4 text-white">
                    <h3 className="text-base font-extrabold tracking-tight drop-shadow-sm truncate">{proj.name}</h3>
                    <p className="text-[11px] text-slate-200 flex items-center gap-1.5 mt-0.5">
                      <MapPin className="w-3 h-3 text-cyan-300" />
                      <span>{proj.location}</span>
                      <span className="text-slate-400">•</span>
                      <span className="text-slate-300">{proj.updatedAt}</span>
                    </p>
                  </div>
                </div>

                {/* Card Body Specs */}
                <div className="p-5 space-y-4 flex-1 flex flex-col justify-between">
                  <div className="grid grid-cols-2 gap-2.5 text-xs bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700/60">
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-mono block">Covered Area</span>
                      <strong className="text-slate-900 dark:text-white font-mono">{proj.coveredArea}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-mono block">Rooms Schedule</span>
                      <strong className="text-slate-900 dark:text-white truncate block">{proj.roomsCount}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-mono block">Style</span>
                      <strong className="text-slate-900 dark:text-white">{proj.style}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-mono block">Est. Cost (PKR)</span>
                      <strong className="text-emerald-600 dark:text-emerald-400 font-mono font-bold">₨ {proj.costEstM}M</strong>
                    </div>
                  </div>

                  {/* Bottom Action Strip */}
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => onOpenStudio && onOpenStudio(proj.model || '5marla')}
                      className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow-sm shadow-blue-500/20 flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Open in 3D</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => showNotification(`CAD package exported for ${proj.name}`)}
                      className="p-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl transition border border-slate-200 dark:border-slate-700 cursor-pointer"
                      title="Download CAD Blueprint"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

              </div>
            );
          })}
        </div>
      ) : (
        /* List View */
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-xs divide-y divide-slate-100 dark:divide-slate-800">
          {filteredAndSortedProjects.map((proj) => (
            <div 
              key={proj.id}
              className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition"
            >
              <div className="flex items-center gap-4">
                <div 
                  className="w-16 h-16 rounded-2xl bg-cover bg-center shrink-0 border border-slate-200 dark:border-slate-700 shadow-2xs relative"
                  style={{ backgroundImage: `url('${proj.image}')` }}
                >
                  {proj.isFavorite && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 text-white rounded-full flex items-center justify-center text-[9px] shadow-xs">
                      ★
                    </span>
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-white">{proj.name}</h3>
                    <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-[10px] font-mono text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                      {proj.plotSize}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
                    <MapPin className="w-3 h-3 text-slate-400" />
                    <span>{proj.location}</span>
                    <span>•</span>
                    <span>{proj.coveredArea}</span>
                    <span>•</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold font-mono">PKR {proj.costEstM}M</span>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                <button
                  type="button"
                  onClick={() => onOpenStudio && onOpenStudio(proj.model || '5marla')}
                  className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow-2xs flex items-center gap-1.5 cursor-pointer"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Open 3D</span>
                </button>
                <button
                  type="button"
                  onClick={() => openRenameModal(proj)}
                  className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl transition border border-slate-200 dark:border-slate-700 cursor-pointer"
                  title="Rename"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => handleDuplicateProject(proj)}
                  className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl transition border border-slate-200 dark:border-slate-700 cursor-pointer"
                  title="Duplicate"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setDeleteTarget(proj)}
                  className="p-2 bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 text-rose-600 rounded-xl transition border border-rose-200 dark:border-rose-900 cursor-pointer"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* RENAME MODAL */}
      {renameTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-extrabold text-slate-900 dark:text-white">Rename Project Blueprint</h3>
              <button 
                type="button" 
                onClick={() => setRenameTarget(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white cursor-pointer"
              >
                ✕
              </button>
            </div>
            
            <p className="text-xs text-slate-500">Provide an architectural label or plot address for this blueprint.</p>
            
            <input 
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white font-bold text-sm focus:outline-none focus:border-blue-600"
              placeholder="e.g. 5 Marla Executive Modern"
              autoFocus
            />

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setRenameTarget(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitRename}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white transition cursor-pointer shadow-xs"
              >
                Save Name
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-900 flex items-center justify-center text-rose-600">
              <Trash2 className="w-6 h-6" />
            </div>

            <div>
              <h3 className="text-base font-extrabold text-slate-900 dark:text-white">Delete Project Permanently?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Are you sure you want to permanently remove <strong className="text-slate-800 dark:text-slate-200">"{deleteTarget.name}"</strong>? All associated 3D models and CAD blueprints will be deleted.
              </p>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white transition cursor-pointer shadow-xs"
              >
                Yes, Delete Project
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
