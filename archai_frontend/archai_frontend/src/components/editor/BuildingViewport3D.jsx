import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { Box, Compass, Sparkles, RotateCw } from 'lucide-react';

export default function BuildingViewport3D({ rooms = [] }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene setup with pristine clean white/light studio background
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#f8fafc');
    scene.fog = new THREE.FogExp2('#f8fafc', 0.003);

    // 2. Camera setup
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(40, 48, 60);
    camera.lookAt(0, 0, 0);

    // 3. Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // 4. Studio Lighting setup
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(40, 60, 30);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 150;
    dirLight.shadow.camera.left = -50;
    dirLight.shadow.camera.right = 50;
    dirLight.shadow.camera.top = 50;
    dirLight.shadow.camera.bottom = -50;
    scene.add(dirLight);

    // Soft subtle blue accent light
    const fillLight = new THREE.DirectionalLight(0xdbeafe, 0.6);
    fillLight.position.set(-30, 25, -30);
    scene.add(fillLight);

    // 5. Ground Floor Slab & Grid
    const gridHelper = new THREE.GridHelper(100, 50, 0x2563eb, 0xe2e8f0);
    gridHelper.position.y = 0.01;
    scene.add(gridHelper);

    const floorGeo = new THREE.PlaneGeometry(120, 120);
    const floorMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9 });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.rotation.x = -Math.PI / 2;
    floorMesh.receiveShadow = true;
    scene.add(floorMesh);

    // 6. Wall & Room Materials
    const WALL_HEIGHT = 5.5;
    const SCALE = 0.08;

    const wallMaterial = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.35, metalness: 0.05 });
    const bedroomMat = new THREE.MeshStandardMaterial({ color: 0x93c5fd, roughness: 0.4 });
    const bathroomMat = new THREE.MeshStandardMaterial({ color: 0xa7f3d0, roughness: 0.4 });
    const livingMat = new THREE.MeshStandardMaterial({ color: 0xfde68a, roughness: 0.4 });
    const kitchenMat = new THREE.MeshStandardMaterial({ color: 0xfecaca, roughness: 0.4 });

    const getRoomMat = (type) => {
      if (type === 'BEDROOM') return bedroomMat;
      if (type === 'BATHROOM') return bathroomMat;
      if (type === 'LIVING_ROOM') return livingMat;
      if (type === 'KITCHEN') return kitchenMat;
      return bedroomMat;
    };

    const defaultRooms = rooms.length > 0 ? rooms : [
      { id: 'r1', type: 'BEDROOM', name: 'Master Bed', x: 40, y: 40, w: 180, h: 140 },
      { id: 'r2', type: 'BATHROOM', name: 'Bath', x: 230, y: 40, w: 90, h: 90 },
      { id: 'r3', type: 'LIVING_ROOM', name: 'Lounge', x: 40, y: 190, w: 280, h: 170 },
      { id: 'r4', type: 'KITCHEN', name: 'Kitchen', x: 330, y: 190, w: 130, h: 170 },
    ];

    defaultRooms.forEach((room) => {
      const rx = (room.x - 280) * SCALE;
      const rz = (room.y - 180) * SCALE;
      const rw = room.w * SCALE;
      const rh = room.h * SCALE;

      // Floor Slab
      const roomFloorGeo = new THREE.BoxGeometry(rw, 0.2, rh);
      const roomFloorMesh = new THREE.Mesh(roomFloorGeo, getRoomMat(room.type));
      roomFloorMesh.position.set(rx + rw / 2, 0.1, rz + rh / 2);
      roomFloorMesh.receiveShadow = true;
      scene.add(roomFloorMesh);

      // 4 perimeter walls
      const wallThick = 0.35;
      const walls = [
        { w: rw, h: WALL_HEIGHT, d: wallThick, x: rx + rw / 2, y: WALL_HEIGHT / 2, z: rz },
        { w: rw, h: WALL_HEIGHT, d: wallThick, x: rx + rw / 2, y: WALL_HEIGHT / 2, z: rz + rh },
        { w: wallThick, h: WALL_HEIGHT, d: rh, x: rx, y: WALL_HEIGHT / 2, z: rz + rh / 2 },
        { w: wallThick, h: WALL_HEIGHT, d: rh, x: rx + rw, y: WALL_HEIGHT / 2, z: rz + rh / 2 },
      ];

      walls.forEach((w) => {
        const geo = new THREE.BoxGeometry(w.w, w.h, w.d);
        const mesh = new THREE.Mesh(geo, wallMaterial);
        mesh.position.set(w.x, w.y, w.z);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        scene.add(mesh);
      });
    });

    // 7. Mouse Orbit interaction
    let isMouseDown = false;
    let prevMousePos = { x: 0, y: 0 };
    let theta = Math.PI / 4;
    let phi = Math.PI / 4;
    const radius = 70;

    const updateCameraPos = () => {
      camera.position.x = radius * Math.sin(theta) * Math.cos(phi);
      camera.position.y = radius * Math.sin(phi);
      camera.position.z = radius * Math.cos(theta) * Math.cos(phi);
      camera.lookAt(0, 2, 0);
    };

    const handleMouseDown = (e) => {
      isMouseDown = true;
      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e) => {
      if (!isMouseDown) return;
      const deltaX = e.clientX - prevMousePos.x;
      const deltaY = e.clientY - prevMousePos.y;

      theta -= deltaX * 0.008;
      phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, phi + deltaY * 0.008));

      prevMousePos = { x: e.clientX, y: e.clientY };
      updateCameraPos();
    };

    const handleMouseUp = () => {
      isMouseDown = false;
    };

    const domElem = renderer.domElement;
    domElem.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      domElem.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [rooms]);

  return (
    <div className="relative w-full h-[440px] rounded-2xl overflow-hidden border border-slate-200 bg-slate-50 shadow-xs">
      <div className="absolute top-4 left-4 z-10 px-3 py-1.5 bg-white/95 backdrop-blur text-xs font-bold text-slate-800 border border-slate-200 rounded-xl flex items-center gap-2 shadow-xs">
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span>Three.js WebGL 3D Architectural Elevation</span>
      </div>
      <div className="absolute bottom-3 right-4 z-10 text-[10px] text-slate-400 font-mono bg-white/80 px-2 py-1 rounded-lg border border-slate-200">
        Click &amp; Drag to Rotate Studio View
      </div>
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
    </div>
  );
}
