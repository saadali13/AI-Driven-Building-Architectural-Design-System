import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Compass, ArrowRight, Layers, Trash2, Home, Sparkles } from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { formatPKR } from '../../services/costEstimatorService';

export const FavoritesPage: React.FC = () => {
  const { projects, templates, toggleFavoriteProject, toggleFavoriteTemplate } = useProjects();

  const favoriteProjects = projects.filter((p) => p.isFavorite);
  const favoriteTemplates = templates.filter((t) => t.isFavorite);

  return (
    <div className="space-y-8 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5">
        <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
          Favorite Projects & Templates
        </h1>
        <p className="text-xs text-[#68736C] mt-1">
          Quickly access your bookmarked residential floor plans, elevation concepts, and blueprint templates.
        </p>
      </div>

      {/* Favorite Projects Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-[#202923] font-heading flex items-center gap-2">
            <Heart className="h-4 w-4 text-rose-500 fill-current" />
            Bookmarked Projects ({favoriteProjects.length})
          </h2>
          <Link
            to="/app/designs"
            className="text-xs font-semibold text-[#23483D] hover:underline flex items-center gap-1"
          >
            <span>View All Projects</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {favoriteProjects.length === 0 ? (
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-8 text-center text-xs text-[#68736C] shadow-xs">
            No favorite projects yet. Click the heart icon on any design card in My Designs to bookmark it here.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {favoriteProjects.map((p) => (
              <div
                key={p.id}
                className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden hover:border-[#23483D]/40 transition-all shadow-xs flex flex-col group"
              >
                <div className="p-4 border-b border-[#E2E7E1] bg-[#F7F7F2]/50 flex items-center justify-between">
                  <span className="text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-[#DCE7DE] text-[#23483D]">
                    {p.plotWidthFt} &times; {p.plotLengthFt} ft &bull; {p.floors} Storey
                  </span>
                  <button
                    onClick={() => toggleFavoriteProject(p.id)}
                    className="h-7 w-7 rounded-lg bg-rose-50 text-rose-500 hover:bg-rose-100 flex items-center justify-center transition-colors"
                    title="Remove from favorites"
                  >
                    <Heart className="h-4 w-4 fill-current" />
                  </button>
                </div>

                <div className="p-5 flex-1 space-y-3">
                  <div>
                    <h3 className="font-bold text-[#202923] text-sm group-hover:text-[#23483D] transition-colors">
                      {p.title}
                    </h3>
                    <p className="text-[11px] text-[#68736C] line-clamp-2 mt-1">
                      {p.promptText || `${p.bedrooms} Beds, ${p.bathrooms} Baths residential layout in Pakistan.`}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-[#68736C] pt-2 border-t border-[#E2E7E1]/60">
                    <span>{p.bedrooms} Beds</span>
                    <span>&bull;</span>
                    <span>{p.bathrooms} Baths</span>
                    <span>&bull;</span>
                    <span className="font-semibold text-[#23483D]">{p.plotAreaSqFt.toLocaleString()} sq ft</span>
                  </div>
                </div>

                <div className="p-4 bg-[#F7F7F2]/30 border-t border-[#E2E7E1] flex items-center justify-between">
                  <Link
                    to={`/app/designs/${p.id}`}
                    className="text-xs font-semibold text-[#23483D] hover:underline flex items-center gap-1"
                  >
                    <span>Open CAD Studio</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                  <span className="text-[10px] text-[#68736C]">{p.updatedAt}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Favorite Templates Section */}
      <div className="space-y-4 pt-4 border-t border-[#E2E7E1]">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-[#202923] font-heading flex items-center gap-2">
            <Compass className="h-4 w-4 text-[#23483D]" />
            Bookmarked Architectural Templates ({favoriteTemplates.length})
          </h2>
          <Link
            to="/app/templates"
            className="text-xs font-semibold text-[#23483D] hover:underline flex items-center gap-1"
          >
            <span>Explore All Templates</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {favoriteTemplates.length === 0 ? (
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-8 text-center text-xs text-[#68736C] shadow-xs">
            No favorite templates bookmarked yet. Explore the Architectural Template Gallery to bookmark your preferred standards.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {favoriteTemplates.map((t) => (
              <div
                key={t.id}
                className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden hover:border-[#23483D]/40 transition-all shadow-xs flex flex-col"
              >
                <div className="p-4 border-b border-[#E2E7E1] bg-[#F7F7F2]/50 flex items-center justify-between">
                  <span className="text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-[#DCE7DE] text-[#23483D]">
                    {t.plotDimensions} &bull; {t.floors} Storey
                  </span>
                  <button
                    onClick={() => toggleFavoriteTemplate(t.id)}
                    className="h-7 w-7 rounded-lg bg-rose-50 text-rose-500 hover:bg-rose-100 flex items-center justify-center transition-colors"
                  >
                    <Heart className="h-4 w-4 fill-current" />
                  </button>
                </div>

                <div className="p-5 flex-1 space-y-2">
                  <h3 className="font-bold text-[#202923] text-sm">{t.name}</h3>
                  <p className="text-[11px] text-[#68736C]">{t.description}</p>
                  <p className="text-xs font-mono font-bold text-[#23483D] pt-2">
                    Est. {formatPKR(t.budgetPKR)}
                  </p>
                </div>

                <div className="p-4 bg-[#F7F7F2]/30 border-t border-[#E2E7E1]">
                  <Link
                    to={`/app/new-design?template=${t.id}`}
                    className="w-full py-2 rounded-xl bg-[#23483D] hover:bg-[#1a362d] text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Use Template in New Design</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
