/**
 * ArchAI Automated Design Validation Engine (CUST Specs - Dr. Aamer Nadeem)
 * Evaluates room bounding boxes for:
 * 1. Minimum room dimensions (Bedroom min 10x10ft, Bath min 5x6ft, Kitchen min 7x8ft, Living min 12x14ft)
 * 2. Structural Room Overlap (AABB intersection algorithm)
 * 3. Boundary setbacks & plot constraints
 */

const MIN_ROOM_LIMITS = {
  BEDROOM: { minW: 100, minH: 100, label: 'Bedroom (Min 10×10 ft)' },
  BATHROOM: { minW: 50, minH: 60, label: 'Bathroom (Min 5×6 ft)' },
  KITCHEN: { minW: 70, minH: 80, label: 'Kitchen (Min 7×8 ft)' },
  LIVING_ROOM: { minW: 120, minH: 140, label: 'Living Hall (Min 12×14 ft)' },
};

export function validateFloorPlan(floorPlanJson) {
  const errors = [];
  const warnings = [];
  const rooms = floorPlanJson?.rooms || [];

  if (!rooms.length) {
    return {
      isValid: false,
      errors: ['Floor plan contains no active rooms.'],
      warnings: [],
    };
  }

  // 1. Check minimum dimension constraints
  rooms.forEach((room) => {
    const limits = MIN_ROOM_LIMITS[room.type];
    if (limits) {
      if (room.w < limits.minW || room.h < limits.minH) {
        errors.push(`"${room.name}" violates minimum dimension standard: ${limits.label}`);
      }
    }
  });

  // 2. Structural Overlap / Collision Check (Axis-Aligned Bounding Box)
  for (let i = 0; i < rooms.length; i++) {
    for (let j = i + 1; j < rooms.length; j++) {
      const r1 = rooms[i];
      const r2 = rooms[j];

      const overlap = !(
        r1.x + r1.w <= r2.x ||
        r2.x + r2.w <= r1.x ||
        r1.y + r1.h <= r2.y ||
        r2.y + r2.h <= r1.y
      );

      if (overlap) {
        errors.push(`Structural Overlap Detected between "${r1.name}" and "${r2.name}".`);
      }
    }
  }

  // 3. Boundary / Setback Check
  const MAX_PLOT_WIDTH = 550;
  const MAX_PLOT_HEIGHT = 380;
  rooms.forEach((room) => {
    if (room.x + room.w > MAX_PLOT_WIDTH || room.y + room.h > MAX_PLOT_HEIGHT) {
      warnings.push(`"${room.name}" exceeds standard setback boundary.`);
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}
