import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * A rotatable 3D view of the building, drawn on a plain canvas from the solids the backend sends
 * (three_d_model.nodes: boxes in feet, centre-based, y is up). Drag to turn, drag up / down to tilt.
 * It is the same model the front elevation and the 3D images are drawn from.
 */

interface Opening {
  kind: string;
  face: 'front' | 'back' | 'left' | 'right';
  a0: number;
  a1: number;
  z0: number;
  z1: number;
}

interface MassNode {
  role: string;
  x: number;
  y: number;
  z: number;
  width: number;
  height: number;
  depth: number;
  openings?: Opening[];
}

interface Box {
  role: string;
  x0: number; x1: number; y0: number; y1: number; z0: number; z1: number;
  open: Opening[];
}

// role -> [top, face toward the light, face away from it]
const COLORS: Record<string, [string, string, string]> = {
  wall: ['#CFC8B8', '#F4EFE4', '#D9D2C2'],
  plinth: ['#9AA0A8', '#B4B9C0', '#8E949C'],
  slab: ['#D8D2C4', '#E9E4D8', '#C6BFB0'],
  column: ['#D8D2C4', '#E9E4D8', '#C6BFB0'],
  parapet: ['#D8D2C4', '#EFEADF', '#CFC8B8'],
  mumty: ['#B9B2A3', '#F4EFE4', '#D9D2C2'],
  cap: ['#8A8478', '#A39C8E', '#7C766B'],
  rail: ['#5B6470', '#6B7480', '#4A525D'],
  lawn: ['#8DBB6E', '#7BA85E', '#6E9954'],
  paving: ['#C7CBD1', '#B5B9BF', '#A6AAB0'],
  water: ['#7CC4E8', '#6BB2D6', '#5FA3C6'],
};
const GLASS = '#86BEDD';
const FRAME = '#2F3B4B';
const DOOR = '#8A5A36';

function toBoxes(nodes: MassNode[]): Box[] {
  return nodes
    .filter((n) => n && n.width > 0 && n.height > 0 && n.depth > 0)
    .map((n) => ({
      role: n.role,
      x0: n.x - n.width / 2, x1: n.x + n.width / 2,
      y0: n.z - n.depth / 2, y1: n.z + n.depth / 2,     // plan depth (street at y = 0)
      z0: n.y - n.height / 2, z1: n.y + n.height / 2,   // height
      open: Array.isArray(n.openings) ? n.openings : [],
    }));
}

/** Back-to-front order: two boxes that a plane separates have a fixed order; a topological sort joins the pairs. */
function drawOrder(boxes: Box[], sinA: number, cosA: number): Box[] {
  const n = boxes.length;
  const after: number[][] = Array.from({ length: n }, () => []);
  const indeg = new Array(n).fill(0);
  const e = 1e-3;
  const first = (a: Box, b: Box): number => {
    if (cosA >= 0) {
      if (a.y0 >= b.y1 - e) return -1;
      if (b.y0 >= a.y1 - e) return 1;
    } else {
      if (a.y1 <= b.y0 + e) return -1;
      if (b.y1 <= a.y0 + e) return 1;
    }
    if (sinA >= 0) {
      if (a.x1 <= b.x0 + e) return -1;
      if (b.x1 <= a.x0 + e) return 1;
    } else {
      if (a.x0 >= b.x1 - e) return -1;
      if (b.x0 >= a.x1 - e) return 1;
    }
    if (a.z1 <= b.z0 + e) return -1;
    if (b.z1 <= a.z0 + e) return 1;
    return 0;
  };
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 1; j < n; j += 1) {
      const c = first(boxes[i], boxes[j]);
      if (c < 0) { after[i].push(j); indeg[j] += 1; } else if (c > 0) { after[j].push(i); indeg[i] += 1; }
    }
  }
  const depth = (b: Box) => -((b.x0 + b.x1) / 2) * sinA + ((b.y0 + b.y1) / 2) * cosA - b.z0 * 0.3;
  const out: Box[] = [];
  const done = new Array(n).fill(false);
  let ready: number[] = [];
  for (let i = 0; i < n; i += 1) if (indeg[i] === 0) ready.push(i);
  while (out.length < n) {
    if (ready.length === 0) {
      let far = -1;
      for (let i = 0; i < n; i += 1) if (!done[i] && (far < 0 || depth(boxes[i]) > depth(boxes[far]))) far = i;
      ready = [far];
    }
    ready.sort((p, q) => depth(boxes[q]) - depth(boxes[p]));
    const i = ready.shift() as number;
    if (done[i]) continue;
    done[i] = true;
    out.push(boxes[i]);
    for (const j of after[i]) {
      indeg[j] -= 1;
      if (indeg[j] === 0 && !done[j]) ready.push(j);
    }
  }
  return out;
}

export default function Massing3DViewer({ nodes, plotWidth, plotLength }: { nodes: MassNode[]; plotWidth: number; plotLength: number }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [az, setAz] = useState(38);       // degrees: turn around the building
  const [tilt, setTilt] = useState(27);   // degrees: how far the camera looks down
  const [mag, setMag] = useState(1);      // wheel zoom on top of the automatic fit
  const [spin, setSpin] = useState(false); // turn slowly on its own
  const drag = useRef<{ x: number; y: number; az: number; tilt: number } | null>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const cw = canvas.clientWidth || 800;
    const ch = canvas.clientHeight || 520;
    if (canvas.width !== Math.round(cw * dpr) || canvas.height !== Math.round(ch * dpr)) {
      canvas.width = Math.round(cw * dpr);
      canvas.height = Math.round(ch * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cw, ch);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, cw, ch);

    const boxes = toBoxes(nodes || []);
    if (boxes.length === 0) return;
    const a = (az * Math.PI) / 180;
    const t = (tilt * Math.PI) / 180;
    const sinA = Math.sin(a), cosA = Math.cos(a), sinT = Math.sin(t), cosT = Math.cos(t);
    const cx = plotWidth / 2, cy = plotLength / 2;
    const P = (x: number, y: number, z: number): [number, number] => {
      const dx = x - cx, dy = y - cy;
      const sx = dx * cosA + dy * sinA;
      const d = -dx * sinA + dy * cosA;
      return [sx, z * cosT + d * sinT];
    };

    // fit everything (ground included) into the canvas
    const top = Math.max(...boxes.map((b) => b.z1));
    const corners: [number, number][] = [];
    for (const x of [-6, plotWidth + 6]) for (const y of [-12, plotLength + 6]) for (const z of [0, top]) corners.push(P(x, y, z));
    const minX = Math.min(...corners.map((c) => c[0])), maxX = Math.max(...corners.map((c) => c[0]));
    const minY = Math.min(...corners.map((c) => c[1])), maxY = Math.max(...corners.map((c) => c[1]));
    const s = Math.min((cw - 24) / (maxX - minX), (ch - 24) / (maxY - minY)) * mag;
    const ox = (cw - (maxX - minX) * s) / 2 - minX * s;
    const oy = (ch - (maxY - minY) * s) / 2 + maxY * s;
    const S = (p: [number, number]): [number, number] => [ox + p[0] * s, oy - p[1] * s];

    const poly = (pts: [number, number, number][], fill: string, stroke: string | null, lw = 0.6) => {
      ctx.beginPath();
      pts.forEach((p, i) => {
        const [px, py] = S(P(p[0], p[1], p[2]));
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.closePath();
      ctx.fillStyle = fill;
      ctx.fill();
      if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke(); }
    };

    // ground: street strip (in front of y = 0), then the plot
    poly([[-6, -12, 0], [plotWidth + 6, -12, 0], [plotWidth + 6, -2, 0], [-6, -2, 0]], '#B9BDC4', null);
    poly([[-6, -2, 0], [plotWidth + 6, -2, 0], [plotWidth + 6, plotLength + 6, 0], [-6, plotLength + 6, 0]], '#E7E9EC', null);
    poly([[0, 0, 0], [plotWidth, 0, 0], [plotWidth, plotLength, 0], [0, plotLength, 0]], '#D7DADF', '#3A3F47', 0.6);

    // which vertical faces look at the camera
    const seeFront = cosA > 0;   // the y0 face (street side)
    const seeRight = sinA > 0;   // the x1 face
    for (const b of drawOrder(boxes, sinA, cosA)) {
      const c = COLORS[b.role] || COLORS.wall;
      const thin = b.z1 - b.z0 < 0.5;
      const lw = thin ? 0.3 : 0.6;
      const xs = seeRight ? b.x1 : b.x0;
      const ys = seeFront ? b.y0 : b.y1;
      // the street-side face is the lit one; faces turned away from the street are in shade
      poly([[xs, b.y0, b.z0], [xs, b.y1, b.z0], [xs, b.y1, b.z1], [xs, b.y0, b.z1]], c[2], '#3A3F47', lw);
      poly([[b.x0, ys, b.z0], [b.x1, ys, b.z0], [b.x1, ys, b.z1], [b.x0, ys, b.z1]], seeFront ? c[1] : c[2], '#3A3F47', lw);
      poly([[b.x0, b.y0, b.z1], [b.x1, b.y0, b.z1], [b.x1, b.y1, b.z1], [b.x0, b.y1, b.z1]], c[0], '#3A3F47', lw);
      for (const o of b.open) {
        let q: [number, number, number][] | null = null;
        if ((o.face === 'front' && seeFront) || (o.face === 'back' && !seeFront)) {
          q = [[o.a0, ys, o.z0], [o.a1, ys, o.z0], [o.a1, ys, o.z1], [o.a0, ys, o.z1]];
        } else if ((o.face === 'right' && seeRight) || (o.face === 'left' && !seeRight)) {
          q = [[xs, o.a0, o.z0], [xs, o.a1, o.z0], [xs, o.a1, o.z1], [xs, o.a0, o.z1]];
        }
        if (q) poly(q, o.kind === 'door' || o.kind === 'main' ? DOOR : GLASS, FRAME, 0.9);
      }
    }
  }, [nodes, plotWidth, plotLength, az, tilt, mag]);

  useEffect(() => { draw(); }, [draw]);
  // wheel = zoom (non-passive so the page does not scroll)
  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      setMag((m) => Math.min(6, Math.max(0.5, +(m * (e.deltaY < 0 ? 1.15 : 1 / 1.15)).toFixed(3))));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, []);
  // auto-rotate
  useEffect(() => {
    if (!spin) return;
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      setAz((a) => a + ((now - last) / 1000) * 18);
      last = now;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [spin]);
  useEffect(() => {
    const onResize = () => draw();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [draw]);

  return (
    <div className="space-y-2">
      <canvas
        ref={canvasRef}
        className="w-full h-[520px] rounded-lg cursor-grab active:cursor-grabbing touch-none select-none bg-white"
        onPointerDown={(ev) => {
          (ev.target as HTMLCanvasElement).setPointerCapture(ev.pointerId);
          setSpin(false);
          drag.current = { x: ev.clientX, y: ev.clientY, az, tilt };
        }}
        onPointerMove={(ev) => {
          if (!drag.current) return;
          setAz(drag.current.az + (ev.clientX - drag.current.x) * 0.5);
          setTilt(Math.max(8, Math.min(80, drag.current.tilt + (ev.clientY - drag.current.y) * 0.3)));
        }}
        onPointerUp={() => { drag.current = null; }}
        onPointerCancel={() => { drag.current = null; }}
      />
      <div className="flex flex-wrap items-center gap-2 text-[11px] text-[#68736C]">
        <span>Drag to turn, drag up or down to tilt, scroll to zoom.</span>
        <button
          onClick={() => setSpin((v) => !v)}
          className={`px-2 py-0.5 rounded-lg border font-semibold ${spin ? 'bg-[#23483D] text-white border-[#23483D]' : 'border-[#DCE7DE] bg-[#EEF4F0] text-[#23483D] hover:bg-[#DCE7DE]'}`}
        >
          {spin ? 'Stop turning' : 'Turn automatically'}
        </button>
        {([['Front', 0], ['Front-right', 38], ['Right', 90], ['Back', 180], ['Left', -90], ['Front-left', -38]] as const).map(([label, v]) => (
          <button
            key={label}
            onClick={() => { setSpin(false); setAz(v); setTilt(27); setMag(1); }}
            className="px-2 py-0.5 rounded-lg border border-[#DCE7DE] bg-[#EEF4F0] text-[#23483D] font-semibold hover:bg-[#DCE7DE]"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
