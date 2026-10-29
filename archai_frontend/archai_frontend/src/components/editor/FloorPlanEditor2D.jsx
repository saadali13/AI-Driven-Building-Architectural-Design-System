import React, { useState, useRef, useEffect } from 'react';
import { LayoutGrid, Plus, Trash2, Move, RotateCcw, Save, Sparkles, Layers } from 'lucide-react';

const ROOM_TYPES = [
  { type: 'BEDROOM', name: 'Bedroom', color: 'rgba(37, 99, 235, 0.15)', stroke: '#2563eb', textColor: '#1e3a8a' },
  { type: 'BATHROOM', name: 'Bathroom', color: 'rgba(16, 185, 129, 0.15)', stroke: '#10b981', textColor: '#065f46' },
  { type: 'LIVING_ROOM', name: 'Living Lounge', color: 'rgba(245, 158, 11, 0.15)', stroke: '#f59e0b', textColor: '#92400e' },
  { type: 'KITCHEN', name: 'Kitchen', color: 'rgba(239, 68, 68, 0.15)', stroke: '#ef4444', textColor: '#991b1b' },
];

export default function FloorPlanEditor2D({ layoutData, onChange }) {
  const canvasRef = useRef(null);
  const [rooms, setRooms] = useState(layoutData?.rooms || [
    { id: 'r1', type: 'BEDROOM', name: 'Master Bedroom', x: 40, y: 40, w: 180, h: 140 },
    { id: 'r2', type: 'BATHROOM', name: 'Ensuite Bath', x: 230, y: 40, w: 90, h: 90 },
    { id: 'r3', type: 'LIVING_ROOM', name: 'Main Lounge', x: 40, y: 190, w: 280, h: 170 },
    { id: 'r4', type: 'KITCHEN', name: 'American Kitchen', x: 330, y: 190, w: 130, h: 170 },
  ]);
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const GRID_SIZE = 20;

  useEffect(() => {
    drawCanvas();
    if (onChange) onChange({ rooms });
  }, [rooms, selectedRoomId]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Background fill
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw Architectural Grid
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += GRID_SIZE) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += GRID_SIZE) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Draw Rooms
    rooms.forEach((room) => {
      const roomDef = ROOM_TYPES.find((t) => t.type === room.type) || ROOM_TYPES[0];
      const isSelected = room.id === selectedRoomId;

      ctx.fillStyle = roomDef.color;
      ctx.strokeStyle = isSelected ? '#2563eb' : roomDef.stroke;
      ctx.lineWidth = isSelected ? 3 : 2;

      ctx.fillRect(room.x, room.y, room.w, room.h);
      ctx.strokeRect(room.x, room.y, room.w, room.h);

      // Door Indicator Line
      ctx.strokeStyle = '#0f172a';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(room.x + 20, room.y + room.h);
      ctx.lineTo(room.x + 50, room.y + room.h);
      ctx.stroke();

      // Label Text & Dimensions
      ctx.fillStyle = '#0f172a';
      ctx.font = 'bold 12px system-ui, sans-serif';
      ctx.fillText(`${room.name}`, room.x + 10, room.y + 22);
      ctx.fillStyle = '#64748b';
      ctx.font = '500 10px monospace';
      const widthFt = Math.round(room.w / 10);
      const heightFt = Math.round(room.h / 10);
      ctx.fillText(`${widthFt}' × ${heightFt}' (${widthFt * heightFt} sq ft)`, room.x + 10, room.y + 38);
    });
  };

  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const clicked = rooms.slice().reverse().find(r => 
      mx >= r.x && mx <= r.x + r.w && my >= r.y && my <= r.y + r.h
    );

    if (clicked) {
      setSelectedRoomId(clicked.id);
      setIsDragging(true);
      setDragOffset({ x: mx - clicked.x, y: my - clicked.y });
    } else {
      setSelectedRoomId(null);
    }
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !selectedRoomId) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const rawX = mx - dragOffset.x;
    const rawY = my - dragOffset.y;
    const snappedX = Math.max(0, Math.round(rawX / GRID_SIZE) * GRID_SIZE);
    const snappedY = Math.max(0, Math.round(rawY / GRID_SIZE) * GRID_SIZE);

    setRooms(rooms.map(r => r.id === selectedRoomId ? { ...r, x: snappedX, y: snappedY } : r));
  };

  const handleMouseUp = () => setIsDragging(false);

  const addRoom = (type) => {
    const roomDef = ROOM_TYPES.find(t => t.type === type);
    const newRoom = {
      id: `r_${Date.now()}`,
      type,
      name: `${roomDef.name} ${rooms.length + 1}`,
      x: 60, y: 60, w: 140, h: 120
    };
    setRooms([...rooms, newRoom]);
    setSelectedRoomId(newRoom.id);
  };

  const deleteSelectedRoom = () => {
    if (!selectedRoomId) return;
    setRooms(rooms.filter(r => r.id !== selectedRoomId));
    setSelectedRoomId(null);
  };

  return (
    <div className="flex flex-col gap-4 bg-white p-5 rounded-2xl text-slate-900 border border-slate-200 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
            <LayoutGrid className="w-5 h-5 text-blue-600" /> Interactive 2D Floor Plan Editor
          </h3>
          <p className="text-xs text-slate-500">Drag rooms on grid to reposition. Walls and door openings calculate dynamically.</p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {ROOM_TYPES.map(t => (
            <button
              key={t.type}
              onClick={() => addRoom(t.type)}
              className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-xs font-bold text-slate-700 rounded-xl flex items-center gap-1.5 border border-slate-200 transition cursor-pointer shadow-2xs"
            >
              <Plus className="w-3.5 h-3.5 text-blue-600" /> Add {t.name}
            </button>
          ))}
          {selectedRoomId && (
            <button
              onClick={deleteSelectedRoom}
              className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-xs font-bold text-rose-600 rounded-xl flex items-center gap-1.5 border border-rose-200 transition cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" /> Remove Room
            </button>
          )}
        </div>
      </div>

      <div className="relative border border-slate-200 rounded-xl overflow-hidden bg-slate-50 shadow-inner">
        <canvas
          ref={canvasRef}
          width={600}
          height={380}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          className="cursor-crosshair block w-full"
        />
      </div>
    </div>
  );
}
