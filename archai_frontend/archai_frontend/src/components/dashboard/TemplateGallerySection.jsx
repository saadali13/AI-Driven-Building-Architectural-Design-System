import React, { useState } from 'react';
import { 
  Sparkles, 
  Box, 
  Heart, 
  ArrowRight, 
  Check, 
  Layers, 
  MapPin, 
  Home, 
  SlidersHorizontal,
  Maximize2
} from 'lucide-react';

export const ARCHITECTURAL_TEMPLATES = [
  {
    id: 'tpl_modern_5m',
    name: 'Modern Contemporary Residence',
    category: 'Modern Contemporary',
    plotSize: '5 Marla (25′ × 45′)',
    coveredArea: '2,150 sq ft',
    floors: '2 Story (G+1)',
    specs: '3-4 Bed Ensuite • Open Lounge • Car Porch',
    bylaws: 'CDA / LDA Verified (Front 5ft, Rear 3ft)',
    costEst: '₨ 7.85M - 8.6M',
    modelKey: '5marla',
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=700&q=80',
    description: 'Clean linear elevation with double-glazed cantilever glass, integrated lightwell OTS, and landscaped compact terrace.',
    prompt: '5 Marla luxury contemporary 2-story elevation with cantilever terrace, lightwell, and 3 ensuite baths in Islamabad'
  },
  {
    id: 'tpl_spanish_10m',
    name: 'Spanish Hacienda Executive Villa',
    category: 'Spanish Hacienda',
    plotSize: '10 Marla (35′ × 65′)',
    coveredArea: '3,800 sq ft',
    floors: '2 Story + Servant Qtr',
    specs: '5 Master Suites • Double Height Hall • Front Lawn',
    bylaws: 'Front 8ft, Rear 5ft, Side 4ft OK',
    costEst: '₨ 14.8M - 17.2M',
    modelKey: '10marla',
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=700&q=80',
    description: 'Warm stucco facade with terracotta roof tiles, arched colonnade patio, wooden exposed beams, and internal courtyard.',
    prompt: '10 Marla Spanish hacienda villa with front lawn, 4 master suites, and double-height lounge in DHA Lahore'
  },
  {
    id: 'tpl_japandi_1k',
    name: 'Minimalist Japandi Zen Estate',
    category: 'Minimalist Japandi',
    plotSize: '1 Kanal (50′ × 90′)',
    coveredArea: '6,500 sq ft',
    floors: '2 Story + Basement',
    specs: '5 Bed Suites • Central Reflecting Pool • 3-Car Portico',
    bylaws: 'Front 10ft, Rear 8ft, Sides 5ft OK',
    costEst: '₨ 28M - 34M',
    modelKey: '1kanal',
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=700&q=80',
    description: 'Harmonious fusion of Scandinavian functionality and Japanese wabi-sabi minimalism with slatted cedar screens and reflecting pool.',
    prompt: '1 Kanal modern luxury farmhouse with central swimming pool, cantilever portico, and servant quarters in Gulberg Islamabad'
  },
  {
    id: 'tpl_urban_3m',
    name: 'Compact Urban Infill Townhouse',
    category: 'Compact Urban',
    plotSize: '3 Marla (20′ × 34′)',
    coveredArea: '1,250 sq ft',
    floors: '2 Story (G+1)',
    specs: '3 Bed • Rooftop Patio • Compact Car Porch',
    bylaws: 'Front 3ft Setback • 80% Coverage OK',
    costEst: '₨ 4.8M - 5.5M',
    modelKey: '3marla',
    image: 'https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=700&q=80',
    description: 'Optimized spatial layout for narrow urban street frontage with vertical light shaft, open kitchen, and rooftop entertainment deck.',
    prompt: '3 Marla compact modern urban house 20x35 with 3 bedrooms, lightwell OTS, and covered parking'
  },
  {
    id: 'tpl_farmhouse_2k',
    name: 'Luxury Country Farmhouse',
    category: 'Farmhouses',
    plotSize: '2 Kanal+ Estate',
    coveredArea: '8,200 sq ft',
    floors: 'Single Story Sprawl',
    specs: '4 Master Pavilions • Infinity Pool • Gazebo',
    bylaws: 'Generous 20ft Periphery Buffers',
    costEst: '₨ 42M - 50M',
    modelKey: '1kanal',
    image: 'https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=700&q=80',
    description: 'Expansive single-level pavilion layout with floor-to-ceiling glass walls, wrap-around verandas, and panoramic mountain views.',
    prompt: '2 Kanal luxury resort farmhouse with wrap-around veranda, infinity swimming pool, and detached guest pavilion'
  },
  {
    id: 'tpl_traditional_7m',
    name: 'Neo-Classical Executive Residence',
    category: 'Classic Traditional',
    plotSize: '7 Marla (30′ × 53′)',
    coveredArea: '3,100 sq ft',
    floors: '2 Story (G+1)',
    specs: '4 Bed Ensuite • Formal Drawing • Front Balcony',
    bylaws: 'Front 5ft, Rear 4ft Setbacks OK',
    costEst: '₨ 11.5M - 13.2M',
    modelKey: '5marla',
    image: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=700&q=80',
    description: 'Timeless architectural detailing featuring fluted exterior pilasters, decorative cornices, cast-iron railings, and marble foyer.',
    prompt: '7 Marla Neo-classical luxury house plan with 4 ensuite bedrooms, classical columns, and marble porch'
  }
];

export default function TemplateGallerySection({
  onSelectTemplate,
  onOpenStudio
}) {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [favorites, setFavorites] = useState(['tpl_modern_5m', 'tpl_spanish_10m']);

  const categories = ['ALL', 'Modern Contemporary', 'Spanish Hacienda', 'Minimalist Japandi', 'Compact Urban', 'Farmhouses', 'Classic Traditional'];

  const toggleFavorite = (id, e) => {
    e.stopPropagation();
    setFavorites(prev => 
      prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]
    );
  };

  const filteredTemplates = selectedCategory === 'ALL'
    ? ARCHITECTURAL_TEMPLATES
    : ARCHITECTURAL_TEMPLATES.filter(t => t.category === selectedCategory);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-3xl p-6 md:p-8 shadow-xs space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg md:text-xl font-extrabold text-slate-900 dark:text-white">
              Architectural Design Template Gallery
            </h2>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Curated blueprints and 3D elevations designed to Pakistani CDA, LDA, and Bahria bylaws.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {categories.map(cat => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredTemplates.map(tpl => {
          const isFav = favorites.includes(tpl.id);
          return (
            <div
              key={tpl.id}
              className="group border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden bg-white dark:bg-slate-900/60 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-xl transition-all duration-300 flex flex-col justify-between"
            >
              {/* Image Thumbnail with Overlay Badges */}
              <div className="relative h-48 overflow-hidden bg-slate-100 dark:bg-slate-800">
                <img
                  src={tpl.image}
                  alt={tpl.name}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-black/20" />

                {/* Top Badges */}
                <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
                  <span className="px-2.5 py-1 rounded-lg bg-slate-900/80 backdrop-blur-md text-white text-[11px] font-mono font-semibold border border-white/20">
                    {tpl.plotSize}
                  </span>

                  <button
                    type="button"
                    onClick={(e) => toggleFavorite(tpl.id, e)}
                    className={`w-8 h-8 rounded-full flex items-center justify-center backdrop-blur-md transition cursor-pointer ${
                      isFav 
                        ? 'bg-rose-500 text-white shadow-sm' 
                        : 'bg-black/40 text-white hover:bg-black/60'
                    }`}
                  >
                    <Heart className={`w-4 h-4 ${isFav ? 'fill-current' : ''}`} />
                  </button>
                </div>

                {/* Bottom Overlay Title */}
                <div className="absolute bottom-3 left-3 right-3 text-white">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-300 font-bold block">
                    {tpl.category}
                  </span>
                  <h3 className="text-base font-bold truncate leading-tight">
                    {tpl.name}
                  </h3>
                </div>
              </div>

              {/* Body */}
              <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
                <div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed">
                    {tpl.description}
                  </p>

                  <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-1.5 text-[11px]">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                      <span>Covered Area:</span>
                      <strong className="text-slate-800 dark:text-slate-200 font-mono">{tpl.coveredArea}</strong>
                    </div>
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                      <span>Specs:</span>
                      <strong className="text-slate-800 dark:text-slate-200">{tpl.specs}</strong>
                    </div>
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                      <span>Bylaw Status:</span>
                      <strong className="text-emerald-600 dark:text-emerald-400 font-medium">{tpl.bylaws}</strong>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-mono block">Estimated PKR</span>
                    <span className="text-xs font-bold text-slate-900 dark:text-white font-mono">{tpl.costEst}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => onOpenStudio && onOpenStudio(tpl.modelKey)}
                      className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition cursor-pointer"
                      title="Inspect in 3D WebGL Scene"
                    >
                      <Box className="w-4 h-4 text-blue-600" />
                    </button>

                    <button
                      type="button"
                      onClick={() => onSelectTemplate && onSelectTemplate(tpl)}
                      className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition flex items-center gap-1 shadow-xs cursor-pointer hover:scale-[1.02]"
                    >
                      <span>Use Template</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

            </div>
          );
        })}
      </div>

    </div>
  );
}
