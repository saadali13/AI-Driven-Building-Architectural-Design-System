import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, Maximize2, Minimize2, Move, Grid, RotateCcw } from 'lucide-react';

interface ArchitecturalPlanCanvasProps {
  imageSrc?: string | null;
  alt?: string;
  levelLabel?: string;
  dimensionsText?: string;
  renderMode?: 'backend_png' | 'interactive_svg';
  onSwitchMode?: () => void;
  children?: React.ReactNode;
}

export const ArchitecturalPlanCanvas: React.FC<ArchitecturalPlanCanvasProps> = ({
  imageSrc,
  alt = 'Architectural Floor Plan',
  levelLabel = 'GROUND FLOOR',
  dimensionsText = '35×65 ft • Scale 1:100',
  renderMode = 'backend_png',
  onSwitchMode,
  children,
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [showGrid, setShowGrid] = useState<boolean>(false);
  const [imageError, setImageError] = useState<boolean>(false);

  useEffect(() => {
    setImageError(false);
  }, [imageSrc]);

  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Smooth Zoom In / Out
  const handleZoomIn = () => {
    setZoom((prev) => Math.min(4.0, +(prev + 0.25).toFixed(2)));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(0.5, +(prev - 0.25).toFixed(2)));
  };

  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleFit = () => {
    setZoom(0.9);
    setPan({ x: 0, y: 0 });
  };

  // Double click to zoom in / reset
  const handleDoubleClick = () => {
    if (zoom > 1.2) {
      handleReset();
    } else {
      setZoom(1.75);
    }
  };

  // Native non-passive wheel listener to allow smooth zoom without page scroll
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.15 : -0.15;
      setZoom((prev) => {
        const next = +(prev + delta).toFixed(2);
        return Math.min(4.0, Math.max(0.5, next));
      });
    };

    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, []);

  // Keyboard navigation (+, -, 0, Escape)
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        handleZoomIn();
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        handleZoomOut();
      } else if (e.key === '0') {
        e.preventDefault();
        handleReset();
      } else if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
        handleReset();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isFullscreen]);

  // Mouse pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Touch pan handlers
  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      setIsDragging(true);
      setDragStart({
        x: e.touches[0].clientX - pan.x,
        y: e.touches[0].clientY - pan.y,
      });
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging || e.touches.length !== 1) return;
    setPan({
      x: e.touches[0].clientX - dragStart.x,
      y: e.touches[0].clientY - dragStart.y,
    });
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
  };

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev);
    handleReset();
  };

  const hasImage = renderMode === 'backend_png' && Boolean(imageSrc) && !imageError;

  return (
    <div
      ref={containerRef}
      className={`relative select-none overflow-hidden transition-all duration-300 ${
        isFullscreen
          ? 'fixed inset-0 z-50 bg-[#141C18] flex flex-col justify-between p-4'
          : 'border border-[#E2E7E1] rounded-2xl bg-[#FBFBFA] min-h-[500px] flex flex-col justify-between shadow-xs'
      }`}
    >
      {/* Top Floating Header Bar */}
      <div className="flex items-center justify-between p-3 z-20 pointer-events-none">
        {/* Left Status Badge */}
        <div className="pointer-events-auto flex items-center gap-2 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-[#DCE7DE] shadow-xs">
          <span className="w-2 h-2 rounded-full bg-[#23483D] animate-pulse"></span>
          <span className="text-[11px] font-bold tracking-wide uppercase text-[#23483D]">
            {levelLabel}
          </span>
          <span className="text-[10px] text-[#68736C] border-l border-[#DCE7DE] pl-2 font-mono">
            {dimensionsText}
          </span>
        </div>

        {/* Right Tools */}
        <div className="pointer-events-auto flex items-center gap-1.5 bg-white/95 backdrop-blur-md p-1 rounded-xl border border-[#DCE7DE] shadow-xs">
          {onSwitchMode && (
            <button
              onClick={onSwitchMode}
              title="Toggle between Technical Blueprint PNG and Vector SVG"
              className="px-2.5 py-1 text-[11px] font-semibold text-[#23483D] hover:bg-[#EEF4F0] rounded-lg transition-colors border border-transparent hover:border-[#DCE7DE]"
            >
              {renderMode === 'backend_png' ? 'Switch to Vector SVG' : 'Switch to Blueprint PNG'}
            </button>
          )}

          <button
            onClick={() => setShowGrid(!showGrid)}
            title="Toggle Blueprint Grid"
            className={`p-1.5 rounded-lg text-xs transition-colors ${
              showGrid ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:bg-[#EEF4F0]'
            }`}
          >
            <Grid className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleFullscreen}
            title={isFullscreen ? 'Exit Fullscreen' : 'View Fullscreen'}
            className="p-1.5 rounded-lg text-xs text-[#68736C] hover:bg-[#EEF4F0] transition-colors"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Main Interactive Zoom & Pan Viewport */}
      <div
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onDoubleClick={handleDoubleClick}
        className={`relative flex-1 flex items-center justify-center overflow-hidden w-full ${
          isDragging ? 'cursor-grabbing' : 'cursor-grab'
        } ${showGrid ? 'bg-[radial-gradient(#DCE7DE_1px,transparent_1px)] [background-size:20px_20px]' : ''}`}
        style={{ minHeight: isFullscreen ? 'calc(100vh - 120px)' : '460px' }}
      >
        <div
          ref={contentRef}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.12s cubic-bezier(0.2, 0, 0, 1)',
          }}
          className="flex items-center justify-center transition-none pointer-events-auto"
        >
          {hasImage ? (
            <img
              src={imageSrc!}
              alt={alt}
              onError={() => setImageError(true)}
              draggable={false}
              className="max-w-[760px] w-auto h-auto object-contain rounded-lg shadow-xs pointer-events-none"
            />
          ) : (
            <div className="w-full max-w-[740px] flex items-center justify-center pointer-events-auto">
              {children}
            </div>
          )}
        </div>
      </div>

      {/* Bottom Floating Control HUD */}
      <div className="flex items-center justify-between p-3 z-20 pointer-events-none">
        {/* Left Instruction Tooltip */}
        <div className="pointer-events-auto flex items-center gap-1.5 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-[#DCE7DE] shadow-xs text-xs">
          <Move className="w-3.5 h-3.5 text-[#68736C]" />
          <span className="text-[11px] text-[#68736C]">
            Drag to pan &bull; Scroll to zoom &bull; Double-click to toggle 175%
          </span>
        </div>

        {/* Right Zoom Controls */}
        <div className="pointer-events-auto flex items-center gap-1 bg-white/95 backdrop-blur-md p-1 rounded-xl border border-[#DCE7DE] shadow-xs">
          <button
            onClick={handleZoomOut}
            disabled={zoom <= 0.5}
            title="Zoom Out (-)"
            className="p-1.5 text-[#23483D] hover:bg-[#EEF4F0] disabled:opacity-30 rounded-lg transition-colors"
          >
            <ZoomOut className="w-4 h-4" />
          </button>

          <span className="px-2 py-0.5 text-[11px] font-mono font-bold text-[#23483D] min-w-[50px] text-center">
            {Math.round(zoom * 100)}%
          </span>

          <button
            onClick={handleZoomIn}
            disabled={zoom >= 4.0}
            title="Zoom In (+)"
            className="p-1.5 text-[#23483D] hover:bg-[#EEF4F0] disabled:opacity-30 rounded-lg transition-colors"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          <div className="w-px h-4 bg-[#DCE7DE] mx-1"></div>

          <button
            onClick={handleReset}
            title="Reset Zoom to 100%"
            className="px-2 py-1 text-[11px] font-semibold text-[#68736C] hover:text-[#202923] hover:bg-[#EEF4F0] rounded-lg transition-colors"
          >
            100%
          </button>

          <button
            onClick={handleFit}
            title="Fit to Screen"
            className="px-2 py-1 text-[11px] font-semibold text-[#23483D] bg-[#EEF4F0] hover:bg-[#DCE7DE] rounded-lg transition-colors"
          >
            Fit
          </button>
        </div>
      </div>
    </div>
  );
};
