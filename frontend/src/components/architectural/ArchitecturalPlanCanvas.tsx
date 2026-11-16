import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, Maximize2, Minimize2, Move, Grid, Download, ExternalLink } from 'lucide-react';

interface ArchitecturalPlanCanvasProps {
  imageSrc?: string | null;
  alt?: string;
  levelLabel?: string;
  dimensionsText?: string;
  renderMode?: 'backend_png' | 'interactive_svg';
  onSwitchMode?: () => void;
  children?: React.ReactNode;
}

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 12;

/**
 * The drawing viewer. The whole sheet is fitted into the viewport when it opens (zoom 100% = whole sheet visible),
 * the mouse wheel zooms towards the pointer, dragging pans, and the sheet can be opened full size in a new tab.
 */
export const ArchitecturalPlanCanvas: React.FC<ArchitecturalPlanCanvasProps> = ({
  imageSrc,
  alt = 'Architectural Floor Plan',
  levelLabel = 'GROUND FLOOR',
  dimensionsText = '35×65 ft • Scale 1:100',
  renderMode = 'backend_png',
  onSwitchMode,
  children,
}) => {
  const [zoom, setZoom] = useState<number>(1);                       // 1 = the whole sheet fits the viewport
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [showGrid, setShowGrid] = useState<boolean>(false);
  const [imageError, setImageError] = useState<boolean>(false);
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);
  const [box, setBox] = useState<{ w: number; h: number }>({ w: 900, h: 600 });

  const viewportRef = useRef<HTMLDivElement>(null);
  const view = useRef({ zoom: 1, pan: { x: 0, y: 0 } });
  const dragStart = useRef({ x: 0, y: 0 });
  view.current = { zoom, pan };

  const reset = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  // a new sheet (another floor, another design) opens fitted
  useEffect(() => {
    setImageError(false);
    setNatural(null);
    reset();
  }, [imageSrc, reset]);

  // viewport size (for fitting the sheet)
  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const measure = () => setBox({ w: el.clientWidth, h: el.clientHeight });
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [isFullscreen]);

  /** Zoom keeping the point under (cx, cy) - measured from the viewport centre - where it is. */
  const zoomAt = useCallback((factor: number, cx = 0, cy = 0) => {
    const { zoom: z, pan: p } = view.current;
    const next = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, +(z * factor).toFixed(3)));
    if (next === z) return;
    const k = next / z;
    setZoom(next);
    setPan(next <= 1 ? { x: 0, y: 0 } : { x: cx - (cx - p.x) * k, y: cy - (cy - p.y) * k });
  }, []);

  // wheel zoom towards the pointer (non-passive, so the page does not scroll)
  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      zoomAt(e.deltaY < 0 ? 1.2 : 1 / 1.2, e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [zoomAt]);

  // keyboard: + / - / 0 / Escape
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomAt(1.25); }
      else if (e.key === '-' || e.key === '_') { e.preventDefault(); zoomAt(1 / 1.25); }
      else if (e.key === '0') { e.preventDefault(); reset(); }
      else if (e.key === 'Escape' && isFullscreen) { setIsFullscreen(false); reset(); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isFullscreen, zoomAt, reset]);

  const onPointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    setIsDragging(true);
    dragStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y });
  };
  const onPointerUp = () => setIsDragging(false);

  const onDoubleClick = (e: React.MouseEvent) => {
    const el = viewportRef.current;
    if (!el) return;
    if (zoom > 1.05) { reset(); return; }
    const r = el.getBoundingClientRect();
    zoomAt(3, e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2));
  };

  const fileName = `${(levelLabel || 'floor_plan').toLowerCase().replace(/\s+/g, '_')}.png`;
  const handleDownloadImage = async () => {
    if (!imageSrc) return;
    try {
      const resp = await fetch(imageSrc);
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      window.open(imageSrc, '_blank', 'noopener');
    }
  };

  const hasImage = renderMode === 'backend_png' && Boolean(imageSrc) && !imageError;
  // the size at which the whole sheet fits the viewport
  const fit = natural ? Math.min((box.w - 24) / natural.w, (box.h - 24) / natural.h) : 1;
  const shownW = natural ? Math.max(1, natural.w * fit) : undefined;
  const shownH = natural ? Math.max(1, natural.h * fit) : undefined;

  return (
    <div
      className={`relative select-none overflow-hidden ${
        isFullscreen
          ? 'fixed inset-0 z-50 bg-white flex flex-col'
          : 'border border-[#E2E7E1] rounded-2xl bg-[#FBFBFA] flex flex-col shadow-xs'
      }`}
    >
      {/* header */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 border-b border-[#E2E7E1] bg-white">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-bold tracking-wide uppercase text-[#23483D]">{levelLabel}</span>
          <span className="text-[10px] text-[#68736C] border-l border-[#DCE7DE] pl-2 font-mono">{dimensionsText}</span>
        </div>
        <div className="flex items-center gap-1.5">
          {onSwitchMode && (
            <button
              onClick={onSwitchMode}
              title="Toggle between the CAD drawing and the vector sketch"
              className="px-2.5 py-1 text-[11px] font-semibold text-[#23483D] hover:bg-[#EEF4F0] rounded-lg border border-transparent hover:border-[#DCE7DE]"
            >
              {renderMode === 'backend_png' ? 'Vector sketch' : 'CAD drawing'}
            </button>
          )}
          {hasImage && (
            <>
              <a
                href={imageSrc!}
                target="_blank"
                rel="noreferrer"
                title="Open the drawing at full size in a new tab"
                className="px-2.5 py-1 text-[11px] font-semibold text-[#23483D] bg-[#EEF4F0] hover:bg-[#DCE7DE] rounded-lg border border-[#DCE7DE] flex items-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Open full size</span>
              </a>
              <button
                onClick={handleDownloadImage}
                title="Download this drawing (PNG)"
                className="px-2.5 py-1 text-[11px] font-semibold text-[#23483D] bg-[#EEF4F0] hover:bg-[#DCE7DE] rounded-lg border border-[#DCE7DE] flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download</span>
              </button>
            </>
          )}
          <button
            onClick={() => setShowGrid(!showGrid)}
            title="Toggle background grid"
            className={`p-1.5 rounded-lg ${showGrid ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:bg-[#EEF4F0]'}`}
          >
            <Grid className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => { setIsFullscreen((p) => !p); reset(); }}
            title={isFullscreen ? 'Exit full screen (Esc)' : 'Full screen'}
            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold text-[#23483D] hover:bg-[#EEF4F0] flex items-center gap-1.5"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            <span>{isFullscreen ? 'Exit' : 'Full screen'}</span>
          </button>
        </div>
      </div>

      {/* viewport */}
      <div
        ref={viewportRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={onDoubleClick}
        className={`relative flex items-center justify-center overflow-hidden w-full touch-none bg-white ${
          isDragging ? 'cursor-grabbing' : 'cursor-grab'
        } ${showGrid ? 'bg-[radial-gradient(#DCE7DE_1px,transparent_1px)] [background-size:20px_20px]' : ''}`}
        style={{ height: isFullscreen ? 'calc(100vh - 104px)' : 'min(78vh, 900px)', minHeight: 520 }}
      >
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.1s ease-out',
          }}
          className="flex items-center justify-center"
        >
          {hasImage ? (
            <img
              src={imageSrc!}
              alt={alt}
              onLoad={(e) => setNatural({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })}
              onError={() => setImageError(true)}
              draggable={false}
              style={{ width: shownW, height: shownH, maxWidth: 'none', visibility: natural ? 'visible' : 'hidden' }}
              className="pointer-events-none"
            />
          ) : (
            <div className="w-full max-w-[740px] flex items-center justify-center pointer-events-auto">{children}</div>
          )}
        </div>
      </div>

      {/* footer */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 border-t border-[#E2E7E1] bg-white">
        <div className="flex items-center gap-1.5 text-[11px] text-[#68736C]">
          <Move className="w-3.5 h-3.5" />
          <span>Scroll to zoom where you point &bull; drag to move &bull; double-click to zoom in / back to fit</span>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => zoomAt(1 / 1.25)} disabled={zoom <= MIN_ZOOM} title="Zoom out (-)"
            className="p-1.5 text-[#23483D] hover:bg-[#EEF4F0] disabled:opacity-30 rounded-lg">
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="px-2 py-0.5 text-[11px] font-mono font-bold text-[#23483D] min-w-[52px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button onClick={() => zoomAt(1.25)} disabled={zoom >= MAX_ZOOM} title="Zoom in (+)"
            className="p-1.5 text-[#23483D] hover:bg-[#EEF4F0] disabled:opacity-30 rounded-lg">
            <ZoomIn className="w-4 h-4" />
          </button>
          <div className="w-px h-4 bg-[#DCE7DE] mx-1" />
          {[2, 4].map((z) => (
            <button key={z} onClick={() => { setZoom(z); setPan({ x: 0, y: 0 }); }} title={`Zoom to ${z * 100}%`}
              className="px-2 py-1 text-[11px] font-semibold text-[#68736C] hover:text-[#202923] hover:bg-[#EEF4F0] rounded-lg">
              {z * 100}%
            </button>
          ))}
          <button onClick={reset} title="Show the whole drawing (0)"
            className="px-2 py-1 text-[11px] font-semibold text-[#23483D] bg-[#EEF4F0] hover:bg-[#DCE7DE] rounded-lg">
            Fit
          </button>
        </div>
      </div>
    </div>
  );
};
