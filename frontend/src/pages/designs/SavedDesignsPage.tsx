import React, { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Search,
  Filter,
  Grid,
  List,
  PlusCircle,
  Copy,
  Edit2,
  Trash2,
  Heart,
  GitCompare,
  ArrowRight,
  FolderKanban,
  CheckCircle2,
  Clock,
  MoreVertical,
  X,
  Compass,
  Building,
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { Project, PlotPreset } from '../../types';
import { formatPKR } from '../../services/costEstimatorService';
import { FloorPlanViewer } from '../../components/architectural/FloorPlanViewer';

export const SavedDesignsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryParam = searchParams.get('q') || '';

  const {
    projects,
    deleteProject,
    duplicateProject,
    updateProject,
    toggleFavoriteProject,
  } = useProjects();

  const [searchQuery, setSearchQuery] = useState(queryParam);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [presetFilter, setPresetFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'updated' | 'created' | 'title'>('updated');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Modals & Menu states
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [renameModalProj, setRenameModalProj] = useState<Project | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [deleteModalProj, setDeleteModalProj] = useState<Project | null>(null);

  // Filter & sort
  const filteredProjects = useMemo(() => {
    return projects
      .filter((p) => {
        if (statusFilter !== 'all' && p.status !== statusFilter) return false;
        if (presetFilter !== 'all' && p.plotPreset !== presetFilter) return false;
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchesTitle = p.title.toLowerCase().includes(q);
          const matchesStyle = p.style.toLowerCase().includes(q);
          const matchesDims = `${p.plotWidthFt}x${p.plotLengthFt}`.includes(q);
          if (!matchesTitle && !matchesStyle && !matchesDims) return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'title') return a.title.localeCompare(b.title);
        if (sortBy === 'created') return b.createdAt.localeCompare(a.createdAt);
        return b.updatedAt.localeCompare(a.updatedAt);
      });
  }, [projects, statusFilter, presetFilter, searchQuery, sortBy]);

  const handleRenameSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (renameModalProj && newTitle.trim()) {
      updateProject(renameModalProj.id, { title: newTitle.trim() });
      setRenameModalProj(null);
    }
  };

  const handleDeleteConfirm = () => {
    if (deleteModalProj) {
      deleteProject(deleteModalProj.id);
      setDeleteModalProj(null);
    }
  };

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7E1] pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
            My Architectural Designs
          </h1>
          <p className="text-xs text-[#68736C] mt-1">
            Manage your personal residential house plans, CAD blueprints, and construction budgets.
          </p>
        </div>

        <Link
          to="/app/designs/new"
          className="px-5 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <PlusCircle className="h-4 w-4" />
          <span>New Design</span>
        </Link>
      </div>

      {/* Search, Filter & View Controls */}
      <div className="bg-white border border-[#E2E7E1] rounded-2xl p-4 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between text-xs">
        {/* Search Input */}
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#68736C]" />
          <input
            type="text"
            placeholder="Search projects by title, plot dimensions (e.g. 35x65), style..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl pl-9 pr-4 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#68736C] hover:text-[#202923]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <select
            value={presetFilter}
            onChange={(e) => setPresetFilter(e.target.value)}
            className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          >
            <option value="all">All Plot Sizes</option>
            <option value="5_marla">5 Marla (25×45)</option>
            <option value="7_marla">7 Marla (30×52.5)</option>
            <option value="10_marla">10 Marla (35×65)</option>
            <option value="1_kanal">1 Kanal (50×90)</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          >
            <option value="all">All Statuses</option>
            <option value="draft">Drafts</option>
            <option value="ready_for_review">Ready for Review</option>
            <option value="completed">Completed</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          >
            <option value="updated">Recently Updated</option>
            <option value="created">Recently Created</option>
            <option value="title">Alphabetical</option>
          </select>

          {/* Grid / List View Toggle */}
          <div className="flex items-center rounded-xl border border-[#E2E7E1] p-0.5 bg-[#F7F7F2]">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-white text-[#23483D] shadow-xs' : 'text-[#68736C]'}`}
              title="Grid View"
            >
              <Grid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-white text-[#23483D] shadow-xs' : 'text-[#68736C]'}`}
              title="List View"
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Projects Display */}
      {filteredProjects.length === 0 ? (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-12 text-center space-y-4 shadow-xs">
          <FolderKanban className="h-10 w-10 text-[#68736C] mx-auto opacity-40" />
          <h3 className="font-bold text-[#202923] text-base">No designs match your criteria</h3>
          <p className="text-xs text-[#68736C] max-w-sm mx-auto">
            Try adjusting your search query, clearing filters, or start a new residential floor plan design.
          </p>
          <Link
            to="/app/designs/new"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#23483D] text-white text-xs font-semibold"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Create New Design</span>
          </Link>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((p) => {
            const alt = p.designAlternatives?.[0];
            const isMenuOpen = activeMenuId === p.id;

            return (
              <div
                key={p.id}
                className="bg-white border border-[#E2E7E1] hover:border-[#23483D] rounded-2xl p-5 shadow-xs transition-all hover:shadow-md flex flex-col justify-between space-y-4 relative"
              >
                <div className="space-y-3">
                  {/* Top Badges & Contextual Menu */}
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-[#EEF4F0] text-[#23483D] border border-[#DCE7DE] uppercase">
                      {p.plotPreset.replace('_', ' ')} • {p.plotWidthFt}×{p.plotLengthFt} FT
                    </span>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => toggleFavoriteProject(p.id)}
                        className="p-1 rounded-lg text-[#68736C] hover:text-[#B86F50]"
                        title={p.isFavorite ? 'Remove from favorites' : 'Mark as favorite'}
                      >
                        <Heart className={`h-4 w-4 ${p.isFavorite ? 'fill-[#B86F50] text-[#B86F50]' : ''}`} />
                      </button>

                      <div className="relative">
                        <button
                          onClick={() => setActiveMenuId(isMenuOpen ? null : p.id)}
                          className="p-1 rounded-lg text-[#68736C] hover:text-[#202923] hover:bg-[#F7F7F2]"
                          title="More options"
                        >
                          <MoreVertical className="h-4 w-4" />
                        </button>

                        {isMenuOpen && (
                          <div className="absolute right-0 mt-1 w-36 rounded-xl bg-white border border-[#E2E7E1] shadow-lg py-1 z-20 text-xs text-[#202923]">
                            <button
                              onClick={() => {
                                setRenameModalProj(p);
                                setNewTitle(p.title);
                                setActiveMenuId(null);
                              }}
                              className="w-full px-3 py-1.5 text-left hover:bg-[#F7F7F2] flex items-center gap-2"
                            >
                              <Edit2 className="h-3.5 w-3.5" /> Rename
                            </button>
                            <button
                              onClick={() => {
                                duplicateProject(p.id);
                                setActiveMenuId(null);
                              }}
                              className="w-full px-3 py-1.5 text-left hover:bg-[#F7F7F2] flex items-center gap-2"
                            >
                              <Copy className="h-3.5 w-3.5" /> Duplicate
                            </button>
                            <Link
                              to={`/app/compare?p1=${p.id}`}
                              className="w-full px-3 py-1.5 text-left hover:bg-[#F7F7F2] flex items-center gap-2"
                            >
                              <GitCompare className="h-3.5 w-3.5" /> Compare
                            </Link>
                            <button
                              onClick={() => {
                                setDeleteModalProj(p);
                                setActiveMenuId(null);
                              }}
                              className="w-full px-3 py-1.5 text-left text-[#DC2626] hover:bg-[#FEF2F2] flex items-center gap-2 border-t border-[#E2E7E1]"
                            >
                              <Trash2 className="h-3.5 w-3.5" /> Delete
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Title & Metadata */}
                  <div>
                    <h3 className="font-bold text-sm text-[#202923] line-clamp-1">{p.title}</h3>
                    <p className="text-xs text-[#68736C] mt-0.5">
                      {p.plotAreaSqFt} sq ft • {p.style}
                    </p>
                  </div>

                  {/* Quick specs */}
                  <div className="grid grid-cols-2 gap-2 text-xs py-2 border-y border-[#E2E7E1] text-[#68736C]">
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-[#68736C]/70">Bedrooms</span>
                      <p className="font-semibold text-[#202923]">{p.bedrooms} Beds, {p.bathrooms} Baths</p>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-[#68736C]/70">Est. Budget</span>
                      <p className="font-semibold text-[#23483D]">{formatPKR(alt?.estimatedCostPKR || p.budgetMinPKR)}</p>
                    </div>
                  </div>
                </div>

                {/* Footer action */}
                <div className="pt-1 flex items-center justify-between">
                  <span className="text-[11px] text-[#68736C]">Updated {p.updatedAt}</span>
                  <Link
                    to={`/app/designs/${p.id}`}
                    className="px-4 py-2 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <span>Open Studio</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* List View */
        <div className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px] bg-[#F7F7F2]">
                  <th className="p-3 font-semibold">Project Title</th>
                  <th className="p-3 font-semibold">Plot Size</th>
                  <th className="p-3 font-semibold">Style</th>
                  <th className="p-3 font-semibold">Bedrooms</th>
                  <th className="p-3 font-semibold">Budget</th>
                  <th className="p-3 font-semibold">Status</th>
                  <th className="p-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E7E1] text-[#202923]">
                {filteredProjects.map((p) => (
                  <tr key={p.id} className="hover:bg-[#F7F7F2]">
                    <td className="p-3 font-semibold text-[#202923]">{p.title}</td>
                    <td className="p-3 font-mono text-[#23483D]">{p.plotWidthFt} × {p.plotLengthFt} ft</td>
                    <td className="p-3 text-[#68736C]">{p.style}</td>
                    <td className="p-3 text-[#202923]">{p.bedrooms} Beds</td>
                    <td className="p-3 font-semibold text-[#23483D]">{formatPKR(p.budgetMinPKR)}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#EEF4F0] text-[#23483D]">
                        {p.status}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        to={`/app/designs/${p.id}`}
                        className="px-3 py-1.5 rounded-lg bg-[#23483D] text-white text-[11px] font-semibold hover:bg-[#1A372E]"
                      >
                        Open Studio
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {renameModalProj && (
        <div className="fixed inset-0 z-50 bg-[#202923]/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-[#202923]">Rename Architectural Design</h3>
            <form onSubmit={handleRenameSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#68736C] mb-1">Project Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
                  autoFocus
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRenameModalProj(null)}
                  className="px-4 py-2 rounded-xl border border-[#E2E7E1] text-xs font-semibold text-[#68736C]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-[#23483D] text-white text-xs font-semibold hover:bg-[#1A372E]"
                >
                  Save Title
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalProj && (
        <div className="fixed inset-0 z-50 bg-[#202923]/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-[#DC2626]">
              <Trash2 className="h-6 w-6" />
              <h3 className="font-bold text-base text-[#202923]">Delete Architectural Project?</h3>
            </div>
            <p className="text-xs text-[#68736C] leading-relaxed">
              Are you sure you want to delete <strong className="text-[#202923]">{deleteModalProj.title}</strong>? All generated floor plan alternatives and BOQ sheets associated with this project will be permanently removed.
            </p>

            <div className="flex justify-end gap-2 pt-3">
              <button
                type="button"
                onClick={() => setDeleteModalProj(null)}
                className="px-4 py-2 rounded-xl border border-[#E2E7E1] text-xs font-semibold text-[#68736C]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                className="px-4 py-2 rounded-xl bg-[#DC2626] text-white text-xs font-semibold hover:bg-red-700"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
