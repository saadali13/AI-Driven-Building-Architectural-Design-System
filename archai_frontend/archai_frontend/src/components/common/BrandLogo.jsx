import React from 'react';
import logoImage from '../../assets/logo.png';



export const LOGO_URL = logoImage;

export default function BrandLogo({ 
  size = "md", 
  showSubtitle = true, 
  subtitleText = "Spatial Intelligence", 
  isDark = false,
  collapsed = false 
}) {
  const sizeClasses = {
    sm: "w-8 h-8",
    md: "w-10 h-10",
    lg: "w-12 h-12",
  };

  const titleSizes = {
    sm: "text-base",
    md: "text-lg",
    lg: "text-2xl",
  };

  return (
    <div className="flex items-center space-x-3 select-none group">
      {/* Official Silver "A" Brand Logo */}
      <div className={`relative ${sizeClasses[size] || sizeClasses.md} rounded-xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-950 p-1 shadow-sm border border-slate-700/60 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform`}>
        <img 
          src={logoImage} 
          alt="ArchAI Logo" 
          className="w-full h-full object-contain rounded-lg" 
        />
      </div>

      {!collapsed && (
        <div className="flex flex-col min-w-0">
          <span className={`${titleSizes[size] || titleSizes.md} font-black tracking-tight leading-none ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Arch<span className="text-blue-600">AI</span> <span className={isDark ? 'text-slate-300 font-light' : 'text-slate-600 font-light'}>Studio</span>
          </span>
          {showSubtitle && (
            <span className={`text-[10px] font-mono font-bold uppercase tracking-wider mt-1 ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>
              {subtitleText}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
