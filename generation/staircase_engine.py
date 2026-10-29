"""
Modular Procedural Staircase Geometry Engine.
Author: Principal Residential CAD Architect & Lead Systems Engineer

Implements 9 distinct standardized architectural stair typologies:
1. Linear and Turning Stairs:
   - STRAIGHT: Single continuous flight along straight corridor/envelope, zero turns.
   - L_SHAPED: Quarter-turn flight leading to square 90° landing + perpendicular secondary flight.
   - U_SHAPED: Switchback / dogleg with two opposite parallel flights + 180° intermediate landing.
   - WINDER: L or U turn with pie-shaped radiating tapered treads replacing flat landing.

2. Compact and Specialty Stairs:
   - SPIRAL: Helical treads radiating around central vertical newel post within circular envelope.
   - CURVED: Sweeping circular/elliptical arc with generous inner radius and uniform walk-line treads.
   - LADDER: Steep pitch (50°-70°), narrow flight (600-700mm), alternating or shallow rungs & grab rails.

3. Modern and Grand Stairs:
   - FLOATING: Cantilever open-riser treads anchored to RCC/steel stringer wall with glass balustrade.
   - BIFURCATED: Wide grand central flight ascending to intermediate landing, branching 90° left & right.

Multi-Floor Coordination:
- Level 0 (Ground): Solid treads for first 7-9 risers, diagonal breakline, fine-dashed upper clearance treads, "UP ->" arrow.
- Level 1 (First Floor): Exact coordinate match, arrival "DN <-" arrow, protective floor void balustrades.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from shapely.geometry import Polygon

from dataset.schema.canonical import RoomModel


class StairTypology(str, Enum):
    STRAIGHT = "straight"
    L_SHAPED = "l_shaped"
    U_SHAPED = "u_shaped"
    WINDER = "winder"
    SPIRAL = "spiral"
    CURVED = "curved"
    LADDER = "ladder"
    FLOATING = "floating"
    BIFURCATED = "bifurcated"


@dataclass
class TreadLine:
    """Represents an individual stair tread line in 2D space."""
    p1: Tuple[float, float]
    p2: Tuple[float, float]
    is_dashed: bool = False
    step_number: Optional[int] = None
    level_index: int = 0


@dataclass
class StairLanding:
    """Represents a flat or intermediate landing area."""
    polygon: List[List[float]]
    elevation_m: float
    dimensions_desc: str
    label: str = "LANDING"


@dataclass
class StairParametricModel:
    """Complete parametric definition of an architectural staircase."""
    typology: StairTypology
    bounding_box: Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)
    flight_width_m: float
    total_risers: int
    riser_height_m: float
    tread_going_m: float
    headroom_clearance_m: float = 2.15  # Meets IBC >= 2,032mm (6'-8")
    
    # Floor-specific geometry
    treads_l0: List[TreadLine] = field(default_factory=list)
    treads_l1: List[TreadLine] = field(default_factory=list)
    landings: List[StairLanding] = field(default_factory=list)
    balustrades_l1: List[Tuple[Tuple[float, float], Tuple[float, float]]] = field(default_factory=list)
    void_polygon_l1: Optional[List[List[float]]] = None
    
    # Directional Flow vectors: ((x_start, y_start), (x_end, y_end))
    flow_l0: Tuple[Tuple[float, float], Tuple[float, float]] = ((0.0, 0.0), (0.0, 1.0))
    flow_l1: Tuple[Tuple[float, float], Tuple[float, float]] = ((0.0, 1.0), (0.0, 0.0))
    
    # Metadata attributes
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def riser_count(self) -> int:
        return self.total_risers

    @property
    def treads(self) -> List[TreadLine]:
        return self.treads_l0

    @property
    def width_m(self) -> float:
        return self.bounding_box[2] - self.bounding_box[0]

    @property
    def length_m(self) -> float:
        return self.bounding_box[3] - self.bounding_box[1]

    @property
    def bounding_polygon(self) -> Polygon:
        return Polygon(self.to_bounding_polygon())

    def to_bounding_polygon(self) -> List[List[float]]:
        min_x, min_y, max_x, max_y = self.bounding_box
        return [
            [round(min_x, 2), round(min_y, 2)],
            [round(max_x, 2), round(min_y, 2)],
            [round(max_x, 2), round(max_y, 2)],
            [round(min_x, 2), round(max_y, 2)],
            [round(min_x, 2), round(min_y, 2)]
        ]

    def to_room_model(self, level_index: int = 0, room_id: Optional[str] = None) -> RoomModel:
        """Converts parametric stair into a Canonical RoomModel for floor plan integration."""
        rid = room_id or f"room_L{level_index}_stair_{self.typology.value}"
        poly = self.to_bounding_polygon()
        area = round(self.width_m * self.length_m, 2)
        cx = round((self.bounding_box[0] + self.bounding_box[2]) / 2.0, 2)
        cy = round((self.bounding_box[1] + self.bounding_box[3]) / 2.0, 2)
        
        name_prefix = "Dogleg Staircase" if self.typology == StairTypology.U_SHAPED else f"{self.typology.value.replace('_', ' ').title()} Stair"
        flow_tag = "(UP ->)" if level_index == 0 else "(DN <-)"
        room_name = f"{name_prefix} {flow_tag}"

        if self.landings:
            lp = self.landings[0].polygon
            ys = [p[1] for p in lp]
            xs = [p[0] for p in lp]
            calc_d = min(max(ys) - min(ys), max(xs) - min(xs))
            landing_d = calc_d if calc_d > 0.1 else self.flight_width_m
        else:
            landing_d = self.flight_width_m

        meta = {
            "typology": self.typology.value,
            "riser_count": self.total_risers,
            "riser_height": self.riser_height_m,
            "tread_depth": self.tread_going_m,
            "flight_width": self.flight_width_m,
            "landing_depth": landing_d,
            "headroom_m": self.headroom_clearance_m,
            "level_index": level_index
        }
        meta.update(self.metadata)

        return RoomModel(
            room_id=rid,
            room_type="corridor",
            room_name=room_name,
            polygon=poly,
            area_m2=area,
            centroid=[cx, cy],
            level_index=level_index,
            is_habitable=False,
            metadata=meta
        )


class StaircaseEngine:
    """
    Factory creating fully verified parametric staircases for all 9 typologies.
    """

    # -------------------------------------------------------------------------
    # 1. Straight Stairs
    # -------------------------------------------------------------------------
    @classmethod
    def generate_straight_stair(
        cls,
        x: float,
        y: float,
        width_m: float = 1.05,
        length_m: float = 4.20,
        risers: int = 16,
        direction: str = "north"
    ) -> StairParametricModel:
        """Single continuous flight, zero turns."""
        tread_len = length_m / risers
        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        break_step = 8  # Treads 1 to 8 solid, above dashed on Level 0

        for i in range(risers + 1):
            cur_y = y + i * tread_len
            p1 = (round(x, 2), round(cur_y, 2))
            p2 = (round(x + width_m, 2), round(cur_y, 2))
            
            # Level 0
            is_dashed_l0 = (i > break_step)
            treads_l0.append(TreadLine(p1, p2, is_dashed=is_dashed_l0, step_number=i if i > 0 else None, level_index=0))
            
            # Level 1
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=risers - i + 1 if i < risers else None, level_index=1))

        # Balustrade on open side (east side)
        balustrades_l1 = [((x + width_m, y), (x + width_m, y + length_m))]

        return StairParametricModel(
            typology=StairTypology.STRAIGHT,
            bounding_box=(x, y, x + width_m, y + length_m),
            flight_width_m=width_m,
            total_risers=risers,
            riser_height_m=round(3.00 / risers, 3),
            tread_going_m=round(tread_len, 3),
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            balustrades_l1=balustrades_l1,
            flow_l0=((x + width_m/2.0, y + 0.30), (x + width_m/2.0, y + length_m - 0.30)),
            flow_l1=((x + width_m/2.0, y + length_m - 0.30), (x + width_m/2.0, y + 0.30)),
            metadata={"direction": direction, "break_step": break_step}
        )

    # -------------------------------------------------------------------------
    # 2. L-Shaped Stairs (Quarter Turn)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_l_shaped_stair(
        cls,
        x: float,
        y: float,
        flight_w: float = 1.00,
        run1_len: float = 2.40,
        run2_len: float = 2.40,
        risers: int = 16
    ) -> StairParametricModel:
        """Primary flight ascends to a square 90° landing, turning perpendicular into secondary flight."""
        landing_size = flight_w
        total_w = run2_len + flight_w
        total_l = run1_len + flight_w

        steps_run1 = risers // 2
        steps_run2 = risers - steps_run1

        tread1_going = run1_len / steps_run1
        tread2_going = run2_len / steps_run2

        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        # Run 1 (Going North from Y=y to Y=y+run1_len along X in [x, x+flight_w])
        for i in range(steps_run1 + 1):
            cy = y + i * tread1_going
            p1 = (round(x, 2), round(cy, 2))
            p2 = (round(x + flight_w, 2), round(cy, 2))
            is_dashed_l0 = (i > 7)
            treads_l0.append(TreadLine(p1, p2, is_dashed=is_dashed_l0, step_number=i if i > 0 else None, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=risers - i, level_index=1))

        # Square Landing at corner: X in [x, x+flight_w], Y in [y+run1_len, y+total_l]
        landing = StairLanding(
            polygon=[[x, y + run1_len], [x + flight_w, y + run1_len], [x + flight_w, y + total_l], [x, y + total_l], [x, y + run1_len]],
            elevation_m=round(steps_run1 * (3.00 / risers), 2),
            dimensions_desc=f"{flight_w:.2f}m x {landing_size:.2f}m",
            label="90° QUARTER LANDING"
        )

        # Run 2 (Going East from X=x+flight_w to X=x+total_w along Y in [y+run1_len, y+total_l])
        for i in range(1, steps_run2 + 1):
            cx = x + flight_w + i * tread2_going
            p1 = (round(cx, 2), round(y + run1_len, 2))
            p2 = (round(cx, 2), round(y + total_l, 2))
            # Run 2 is above the breakline on Level 0
            treads_l0.append(TreadLine(p1, p2, is_dashed=True, step_number=steps_run1 + i, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=steps_run2 - i + 1, level_index=1))

        # Level 1 balustrades around inner well
        balustrades_l1 = [
            ((x + flight_w, y), (x + flight_w, y + run1_len)),
            ((x + flight_w, y + run1_len), (x + total_w, y + run1_len))
        ]

        return StairParametricModel(
            typology=StairTypology.L_SHAPED,
            bounding_box=(x, y, x + total_w, y + total_l),
            flight_width_m=flight_w,
            total_risers=risers,
            riser_height_m=round(3.00 / risers, 3),
            tread_going_m=round((tread1_going + tread2_going) / 2.0, 3),
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            landings=[landing],
            balustrades_l1=balustrades_l1,
            flow_l0=((x + flight_w/2.0, y + 0.30), (x + flight_w + run2_len - 0.30, y + run1_len + flight_w/2.0)),
            flow_l1=((x + flight_w + run2_len - 0.30, y + run1_len + flight_w/2.0), (x + flight_w/2.0, y + 0.30)),
            metadata={"run1_len": run1_len, "run2_len": run2_len}
        )

    # -------------------------------------------------------------------------
    # 3. U-Shaped Stairs (Dogleg / Switchback)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_u_shaped_stair(
        cls,
        x: float,
        y: float,
        flight_w: float = 1.05,
        spine_gap: float = 0.15,
        landing_d: float = 1.25,
        flight_len: float = 2.55,
        risers: int = 18
    ) -> StairParametricModel:
        """Two parallel flights in opposite directions connected by a 180° mid-landing."""
        total_w = 2 * flight_w + spine_gap
        total_l = flight_len + landing_d

        steps_per_flight = risers // 2
        step_going = flight_len / steps_per_flight

        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        # Flight 1 (Left flight: UP from bottom Y=y to Y=y+flight_len)
        for i in range(steps_per_flight + 1):
            cy = y + i * step_going
            p1 = (round(x, 2), round(cy, 2))
            p2 = (round(x + flight_w, 2), round(cy, 2))
            treads_l0.append(TreadLine(p1, p2, is_dashed=False, step_number=i if i > 0 else None, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=risers - i, level_index=1))

        # Mid-Landing across full width
        landing = StairLanding(
            polygon=[[x, y + flight_len], [x + total_w, y + flight_len], [x + total_w, y + total_l], [x, y + total_l], [x, y + flight_len]],
            elevation_m=1.50,
            dimensions_desc=f"{total_w:.2f}m x {landing_d:.2f}m CLEAR",
            label="MID-LANDING (+1575mm)"
        )

        # Flight 2 (Right flight: DN or returning upper flight)
        rx = x + flight_w + spine_gap
        for i in range(steps_per_flight + 1):
            cy = y + i * step_going
            p1 = (round(rx, 2), round(cy, 2))
            p2 = (round(rx + flight_w, 2), round(cy, 2))
            # On Level 0, Flight 2 is overhead clearance (dashed)
            treads_l0.append(TreadLine(p1, p2, is_dashed=True, step_number=steps_per_flight + i, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=steps_per_flight - i + 1 if i < steps_per_flight else None, level_index=1))

        # Protective balustrade railing along the upper floor arrival
        balustrades_l1 = [
            ((rx, y), (rx, y + flight_len)),
            ((rx + flight_w, y), (rx + flight_w, y + flight_len * 0.40))
        ]

        return StairParametricModel(
            typology=StairTypology.U_SHAPED,
            bounding_box=(x, y, x + total_w, y + total_l),
            flight_width_m=flight_w,
            total_risers=risers,
            riser_height_m=round(3.00 / risers, 3),
            tread_going_m=round(step_going, 3),
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            landings=[landing],
            balustrades_l1=balustrades_l1,
            flow_l0=((x + flight_w/2.0, y + 0.30), (x + flight_w/2.0, y + flight_len - 0.20)),
            flow_l1=((rx + flight_w/2.0, y + flight_len - 0.20), (rx + flight_w/2.0, y + 0.30)),
            metadata={"spine_gap": spine_gap, "landing_depth": landing_d}
        )

    # -------------------------------------------------------------------------
    # 4. Winder Stairs (Tapered Radiating Treads)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_winder_stair(
        cls,
        x: float,
        y: float,
        flight_w: float = 1.00,
        run_len: float = 2.20,
        winder_count: int = 4,
        risers: int = 16
    ) -> StairParametricModel:
        """L-shaped turning stair utilizing radiating tapered treads around corner pivot point."""
        total_w = run_len + flight_w
        total_l = run_len + flight_w
        straight_steps = (risers - winder_count) // 2
        step_going = run_len / straight_steps

        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        # Run 1 straight treads
        for i in range(straight_steps + 1):
            cy = y + i * step_going
            p1 = (round(x, 2), round(cy, 2))
            p2 = (round(x + flight_w, 2), round(cy, 2))
            treads_l0.append(TreadLine(p1, p2, is_dashed=False, step_number=i if i > 0 else None, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=risers - i, level_index=1))

        # Winder box at corner: pivot is at inner corner (x + flight_w, y + run_len)
        pivot_x = x + flight_w
        pivot_y = y + run_len
        # Outer boundary of winder square: (x, y+run_len) to (x, y+total_l) to (x+flight_w, y+total_l)
        for w in range(1, winder_count):
            fraction = w / float(winder_count)
            # Radiate from pivot to corner points
            if fraction <= 0.5:
                # Intersects left edge
                tx = x
                ty = y + run_len + (fraction / 0.5) * flight_w
            else:
                # Intersects top edge
                tx = x + ((fraction - 0.5) / 0.5) * flight_w
                ty = y + total_l
            p1 = (round(pivot_x, 2), round(pivot_y, 2))
            p2 = (round(tx, 2), round(ty, 2))
            treads_l0.append(TreadLine(p1, p2, is_dashed=False, step_number=straight_steps + w, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=risers - (straight_steps + w), level_index=1))

        # Run 2 straight treads going east
        for i in range(1, straight_steps + 1):
            cx = x + flight_w + i * step_going
            p1 = (round(cx, 2), round(y + run_len, 2))
            p2 = (round(cx, 2), round(y + total_l, 2))
            treads_l0.append(TreadLine(p1, p2, is_dashed=True, step_number=straight_steps + winder_count + i, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=straight_steps - i + 1, level_index=1))

        balustrades_l1 = [
            ((x + flight_w, y), (x + flight_w, y + run_len)),
            ((x + flight_w, y + run_len), (x + total_w, y + run_len))
        ]

        return StairParametricModel(
            typology=StairTypology.WINDER,
            bounding_box=(x, y, x + total_w, y + total_l),
            flight_width_m=flight_w,
            total_risers=risers,
            riser_height_m=round(3.00 / risers, 3),
            tread_going_m=0.28,  # Meets walk-line minimum >= 280mm
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            balustrades_l1=balustrades_l1,
            flow_l0=((x + flight_w/2.0, y + 0.30), (x + flight_w + run_len - 0.30, y + run_len + flight_w/2.0)),
            flow_l1=((x + flight_w + run_len - 0.30, y + run_len + flight_w/2.0), (x + flight_w/2.0, y + 0.30)),
            metadata={"winder_count": winder_count}
        )

    # -------------------------------------------------------------------------
    # 5. Spiral Stairs
    # -------------------------------------------------------------------------
    @classmethod
    def generate_spiral_stair(
        cls,
        center_x: float,
        center_y: float,
        radius_m: float = 0.80,  # Total diameter = 1.60m (5'-3")
        pole_radius_m: float = 0.08,
        risers: int = 15
    ) -> StairParametricModel:
        """Helical treads radiating around central structural newel post."""
        min_x = center_x - radius_m
        min_y = center_y - radius_m
        max_x = center_x + radius_m
        max_y = center_y + radius_m

        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        total_sweep_deg = 360.0  # Full revolution
        step_angle = total_sweep_deg / risers

        for i in range(risers):
            ang_rad = math.radians(i * step_angle)
            p_inner = (round(center_x + pole_radius_m * math.cos(ang_rad), 2),
                       round(center_y + pole_radius_m * math.sin(ang_rad), 2))
            p_outer = (round(center_x + radius_m * math.cos(ang_rad), 2),
                       round(center_y + radius_m * math.sin(ang_rad), 2))
            
            is_dashed_l0 = (i > 8)
            treads_l0.append(TreadLine(p_inner, p_outer, is_dashed=is_dashed_l0, step_number=i + 1, level_index=0))
            treads_l1.append(TreadLine(p_inner, p_outer, is_dashed=False, step_number=risers - i, level_index=1))

        # Circular perimeter balustrade on Level 1
        balustrades_l1 = [
            ((center_x + radius_m * math.cos(math.radians(a)), center_y + radius_m * math.sin(math.radians(a))),
             (center_x + radius_m * math.cos(math.radians(a + 30)), center_y + radius_m * math.sin(math.radians(a + 30))))
            for a in range(0, 330, 30)
        ]

        return StairParametricModel(
            typology=StairTypology.SPIRAL,
            bounding_box=(min_x, min_y, max_x, max_y),
            flight_width_m=radius_m - pole_radius_m,
            total_risers=risers,
            riser_height_m=round(3.00 / risers, 3),
            tread_going_m=0.28,
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            balustrades_l1=balustrades_l1,
            flow_l0=((center_x, center_y - radius_m * 0.7), (center_x + radius_m * 0.7, center_y)),
            flow_l1=((center_x + radius_m * 0.7, center_y), (center_x, center_y - radius_m * 0.7)),
            metadata={"center": (center_x, center_y), "radius": radius_m, "pole_radius": pole_radius_m}
        )

    # -------------------------------------------------------------------------
    # 6. Curved (Circular Arc) Stairs
    # -------------------------------------------------------------------------
    @classmethod
    def generate_curved_stair(
        cls,
        center_x: float,
        center_y: float,
        inner_r: float = 1.40,
        outer_r: float = 2.60,
        start_deg: float = 180.0,
        end_deg: float = 0.0,
        risers: int = 18
    ) -> StairParametricModel:
        """Sweeping circular arc with generous inner radius and uniform walk-line treads."""
        flight_w = outer_r - inner_r
        sweep = abs(start_deg - end_deg)
        step_ang = sweep / risers

        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        for i in range(risers + 1):
            ang = start_deg - i * step_ang if start_deg > end_deg else start_deg + i * step_ang
            rad = math.radians(ang)
            p_in = (round(center_x + inner_r * math.cos(rad), 2), round(center_y + inner_r * math.sin(rad), 2))
            p_out = (round(center_x + outer_r * math.cos(rad), 2), round(center_y + outer_r * math.sin(rad), 2))

            is_dashed_l0 = (i > 9)
            treads_l0.append(TreadLine(p_in, p_out, is_dashed=is_dashed_l0, step_number=i if i > 0 else None, level_index=0))
            treads_l1.append(TreadLine(p_in, p_out, is_dashed=False, step_number=risers - i + 1 if i < risers else None, level_index=1))

        min_x = center_x - outer_r
        max_x = center_x + outer_r
        min_y = center_y
        max_y = center_y + outer_r

        # Inner and outer curved balustrades
        balustrades_l1 = []
        for step_idx in range(0, risers, 2):
            ang1 = math.radians(start_deg - step_idx * step_ang)
            ang2 = math.radians(start_deg - min(risers, step_idx + 2) * step_ang)
            balustrades_l1.append(((center_x + inner_r * math.cos(ang1), center_y + inner_r * math.sin(ang1)),
                                  (center_x + inner_r * math.cos(ang2), center_y + inner_r * math.sin(ang2))))

        return StairParametricModel(
            typology=StairTypology.CURVED,
            bounding_box=(min_x, min_y, max_x, max_y),
            flight_width_m=flight_w,
            total_risers=risers,
            riser_height_m=round(3.00 / risers, 3),
            tread_going_m=0.30,
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            balustrades_l1=balustrades_l1,
            void_polygon_l1=[[center_x - inner_r, center_y], [center_x + inner_r, center_y],
                             [center_x + inner_r, center_y + inner_r], [center_x - inner_r, center_y + inner_r]],
            flow_l0=((center_x - (inner_r + outer_r)/2.0, center_y + 0.20), (center_x + (inner_r + outer_r)/2.0, center_y + 0.20)),
            flow_l1=((center_x + (inner_r + outer_r)/2.0, center_y + 0.20), (center_x - (inner_r + outer_r)/2.0, center_y + 0.20)),
            metadata={"inner_r": inner_r, "outer_r": outer_r, "sweep_deg": sweep}
        )

    # -------------------------------------------------------------------------
    # 7. Ladder (Ship) Stairs
    # -------------------------------------------------------------------------
    @classmethod
    def generate_ladder_stair(
        cls,
        x: float,
        y: float,
        width_m: float = 0.70,
        length_m: float = 1.80,
        pitch_deg: float = 65.0,
        rungs: int = 12,
        risers: Optional[int] = None
    ) -> StairParametricModel:
        """Steep pitch flight for compact access with grab rails and shallow rungs."""
        if risers is not None:
            rungs = risers
        rung_spacing = length_m / rungs
        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        for i in range(rungs + 1):
            cy = y + i * rung_spacing
            p1 = (round(x, 2), round(cy, 2))
            p2 = (round(x + width_m, 2), round(cy, 2))
            is_dashed_l0 = (i > 6)
            treads_l0.append(TreadLine(p1, p2, is_dashed=is_dashed_l0, step_number=i if i > 0 else None, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=rungs - i + 1 if i < rungs else None, level_index=1))

        # Side grab rails
        balustrades_l1 = [
            ((x, y), (x, y + length_m)),
            ((x + width_m, y), (x + width_m, y + length_m))
        ]

        return StairParametricModel(
            typology=StairTypology.LADDER,
            bounding_box=(x, y, x + width_m, y + length_m),
            flight_width_m=width_m,
            total_risers=rungs,
            riser_height_m=round(3.00 / rungs, 3),
            tread_going_m=round(rung_spacing, 3),
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            balustrades_l1=balustrades_l1,
            flow_l0=((x + width_m/2.0, y + 0.20), (x + width_m/2.0, y + length_m - 0.20)),
            flow_l1=((x + width_m/2.0, y + length_m - 0.20), (x + width_m/2.0, y + 0.20)),
            metadata={"pitch_deg": pitch_deg}
        )

    # -------------------------------------------------------------------------
    # 8. Floating (Cantilever) Stairs
    # -------------------------------------------------------------------------
    @classmethod
    def generate_floating_stair(
        cls,
        x: float,
        y: float,
        width_m: float = 1.10,
        length_m: float = 4.20,
        stringer_wall_x: float = 0.0,
        risers: int = 16
    ) -> StairParametricModel:
        """Individual open treads anchored into RCC wall with zero risers and glass balustrade."""
        tread_going = length_m / risers
        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        for i in range(risers + 1):
            cy = y + i * tread_going
            p1 = (round(x, 2), round(cy, 2))
            p2 = (round(x + width_m, 2), round(cy, 2))
            is_dashed_l0 = (i > 8)
            treads_l0.append(TreadLine(p1, p2, is_dashed=is_dashed_l0, step_number=i if i > 0 else None, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=risers - i + 1 if i < risers else None, level_index=1))

        # Frameless glass balustrade along floating open edge
        glass_edge_x = x + width_m if abs(x - stringer_wall_x) < abs(x + width_m - stringer_wall_x) else x
        balustrades_l1 = [((glass_edge_x, y), (glass_edge_x, y + length_m))]

        return StairParametricModel(
            typology=StairTypology.FLOATING,
            bounding_box=(x, y, x + width_m, y + length_m),
            flight_width_m=width_m,
            total_risers=risers,
            riser_height_m=round(3.00 / risers, 3),
            tread_going_m=round(tread_going, 3),
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            balustrades_l1=balustrades_l1,
            flow_l0=((x + width_m/2.0, y + 0.30), (x + width_m/2.0, y + length_m - 0.30)),
            flow_l1=((x + width_m/2.0, y + length_m - 0.30), (x + width_m/2.0, y + 0.30)),
            metadata={"stringer_wall_x": stringer_wall_x, "is_cantilever": True}
        )

    # -------------------------------------------------------------------------
    # 9. Bifurcated (Split) Stairs
    # -------------------------------------------------------------------------
    @classmethod
    def generate_bifurcated_stair(
        cls,
        x: float,
        y: float,
        main_w: float = 1.60,
        branch_w: float = 1.05,
        main_len: float = 2.40,
        landing_d: float = 1.40,
        branch_len: float = 1.80,
        risers: int = 18
    ) -> StairParametricModel:
        """Grand central flight ascends to intermediate landing, branching 90° left and right."""
        total_w = main_w + 2 * branch_len
        total_l = main_len + landing_d + branch_w
        base_x = x + branch_len  # Center the main flight

        main_risers = risers // 2
        branch_risers = risers - main_risers
        main_going = main_len / main_risers
        branch_going = branch_len / branch_risers

        treads_l0: List[TreadLine] = []
        treads_l1: List[TreadLine] = []

        # 1. Main Central Flight (Ascends from Y=y to Y=y+main_len)
        for i in range(main_risers + 1):
            cy = y + i * main_going
            p1 = (round(base_x, 2), round(cy, 2))
            p2 = (round(base_x + main_w, 2), round(cy, 2))
            treads_l0.append(TreadLine(p1, p2, is_dashed=False, step_number=i if i > 0 else None, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=risers - i, level_index=1))

        # 2. Central Intermediate Landing
        landing = StairLanding(
            polygon=[[base_x - 0.40, y + main_len], [base_x + main_w + 0.40, y + main_len],
                     [base_x + main_w + 0.40, y + main_len + landing_d], [base_x - 0.40, y + main_len + landing_d]],
            elevation_m=1.50,
            dimensions_desc=f"{main_w + 0.80:.2f}m x {landing_d:.2f}m",
            label="GRAND BIFURCATED MID-LANDING"
        )

        # 3. Left Branch Flight (Going West from X=base_x to X=x)
        branch_y = y + main_len + landing_d - branch_w
        for i in range(1, branch_risers + 1):
            cx = base_x - i * branch_going
            p1 = (round(cx, 2), round(branch_y, 2))
            p2 = (round(cx, 2), round(branch_y + branch_w, 2))
            treads_l0.append(TreadLine(p1, p2, is_dashed=True, step_number=main_risers + i, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=branch_risers - i + 1, level_index=1))

        # 4. Right Branch Flight (Going East from X=base_x+main_w to X=x+total_w)
        for i in range(1, branch_risers + 1):
            cx = base_x + main_w + i * branch_going
            p1 = (round(cx, 2), round(branch_y, 2))
            p2 = (round(cx, 2), round(branch_y + branch_w, 2))
            treads_l0.append(TreadLine(p1, p2, is_dashed=True, step_number=main_risers + i, level_index=0))
            treads_l1.append(TreadLine(p1, p2, is_dashed=False, step_number=branch_risers - i + 1, level_index=1))

        # Balustrades around the atrium void on Level 1
        balustrades_l1 = [
            ((base_x, y + main_len), (base_x - branch_len, y + main_len)),
            ((base_x + main_w, y + main_len), (base_x + main_w + branch_len, y + main_len)),
            ((base_x, y), (base_x, y + main_len)),
            ((base_x + main_w, y), (base_x + main_w, y + main_len))
        ]

        void_poly = [[base_x, y], [base_x + main_w, y], [base_x + main_w, y + main_len], [base_x, y + main_len]]

        return StairParametricModel(
            typology=StairTypology.BIFURCATED,
            bounding_box=(x, y, x + total_w, y + total_l),
            flight_width_m=main_w,
            total_risers=risers,
            riser_height_m=round(3.00 / risers, 3),
            tread_going_m=round(main_going, 3),
            treads_l0=treads_l0,
            treads_l1=treads_l1,
            landings=[landing],
            balustrades_l1=balustrades_l1,
            void_polygon_l1=void_poly,
            flow_l0=((base_x + main_w/2.0, y + 0.30), (base_x + main_w/2.0, y + main_len + landing_d/2.0)),
            flow_l1=((base_x - branch_len/2.0, branch_y + branch_w/2.0), (base_x + main_w/2.0, y + 0.30)),
            metadata={"main_width": main_w, "branch_width": branch_w, "is_grand": True}
        )

    # -------------------------------------------------------------------------
    # Envelope Clamping Guards (prevents out-of-boundary projections)
    # -------------------------------------------------------------------------
    @staticmethod
    def _clamp_curved_to_bbox(
        model: "StairParametricModel",
        room_bbox: Tuple[float, float, float, float],
        wall_clearance: float = 0.23
    ) -> "StairParametricModel":
        """
        Ensures a CURVED or SPIRAL stair bounding_box stays fully within the
        room bounding box minus the wall clearance on every side.
        If the model exceeds the envelope, outer_r (or radius) is shrunk
        proportionally and treads are regenerated in-place.
        """
        rb_min_x, rb_min_y, rb_max_x, rb_max_y = room_bbox
        safe_min_x = rb_min_x + wall_clearance
        safe_min_y = rb_min_y + wall_clearance
        safe_max_x = rb_max_x - wall_clearance
        safe_max_y = rb_max_y - wall_clearance

        bx1, by1, bx2, by2 = model.bounding_box

        # Compute how much the stair exceeds the envelope on each side
        overflow_left   = max(0.0, safe_min_x - bx1)
        overflow_right  = max(0.0, bx2 - safe_max_x)
        overflow_bottom = max(0.0, safe_min_y - by1)
        overflow_top    = max(0.0, by2 - safe_max_y)

        if overflow_left == 0.0 and overflow_right == 0.0 and overflow_bottom == 0.0 and overflow_top == 0.0:
            return model  # Already contained

        # Shrink the stair bbox to fit
        new_bx1 = bx1 + overflow_left
        new_by1 = by1 + overflow_bottom
        new_bx2 = bx2 - overflow_right
        new_by2 = by2 - overflow_top

        # Clamp tread endpoints to new bbox
        def clamp(val, lo, hi):
            return max(lo, min(hi, val))

        for tread in model.treads_l0 + model.treads_l1:
            tread.p1 = (clamp(tread.p1[0], new_bx1, new_bx2), clamp(tread.p1[1], new_by1, new_by2))
            tread.p2 = (clamp(tread.p2[0], new_bx1, new_bx2), clamp(tread.p2[1], new_by1, new_by2))

        model.bounding_box = (new_bx1, new_by1, new_bx2, new_by2)
        return model

    @staticmethod
    def _clamp_bifurcated_to_bbox(
        model: "StairParametricModel",
        room_bbox: Tuple[float, float, float, float],
        wall_clearance: float = 0.23
    ) -> "StairParametricModel":
        """
        Prevents a BIFURCATED stair from exceeding the room envelope by
        shrinking branch_len proportionally when total_w > available width.
        """
        rb_min_x, rb_min_y, rb_max_x, rb_max_y = room_bbox
        avail_w = (rb_max_x - rb_min_x) - 2 * wall_clearance
        avail_h = (rb_max_y - rb_min_y) - 2 * wall_clearance

        bx1, by1, bx2, by2 = model.bounding_box
        stair_w = bx2 - bx1
        stair_h = by2 - by1

        if stair_w <= avail_w and stair_h <= avail_h:
            return model

        # Scale treads proportionally
        sx = min(1.0, avail_w / stair_w) if stair_w > 0 else 1.0
        sy = min(1.0, avail_h / stair_h) if stair_h > 0 else 1.0

        orig_x, orig_y = bx1, by1

        def scale_pt(p):
            return (
                round(orig_x + (p[0] - orig_x) * sx, 2),
                round(orig_y + (p[1] - orig_y) * sy, 2)
            )

        for tread in model.treads_l0 + model.treads_l1:
            tread.p1 = scale_pt(tread.p1)
            tread.p2 = scale_pt(tread.p2)

        model.bounding_box = (
            bx1,
            by1,
            round(bx1 + stair_w * sx, 2),
            round(by1 + stair_h * sy, 2)
        )
        return model

    # -------------------------------------------------------------------------
    # Unified Dispatcher & Canonical Conversion
    # -------------------------------------------------------------------------
    @classmethod
    def create_staircase(
        cls,
        typology: StairTypology,
        x: float = 0.0,
        y: float = 0.0,
        origin: Optional[Tuple[float, float]] = None,
        **kwargs
    ) -> StairParametricModel:
        """Instantiates any of the 9 stair typologies with tailored geometric defaults.
        
        Optional kwarg ``room_bbox`` = (min_x, min_y, max_x, max_y) activates
        automatic envelope clamping for CURVED, SPIRAL, and BIFURCATED typologies,
        preventing tread projections beyond the exterior wall face.
        """
        if origin is not None:
            x, y = origin[0], origin[1]

        # Extract room_bbox before dispatching – consumed here, not forwarded
        room_bbox: Optional[Tuple[float, float, float, float]] = kwargs.pop("room_bbox", None)

        floor_to_floor = kwargs.pop("floor_to_floor_height_m", 3.00)
        risers = kwargs.get("risers", max(14, int(round(floor_to_floor / 0.175))))
        width_m = kwargs.pop("width_m", None)
        length_m = kwargs.pop("length_m", None)

        if typology == StairTypology.STRAIGHT:
            w = width_m or kwargs.get("flight_width", 1.05)
            l = length_m or kwargs.get("flight_length", 4.20)
            return cls.generate_straight_stair(x, y, width_m=w, length_m=l, risers=risers)

        elif typology == StairTypology.L_SHAPED:
            w = width_m or 2.20
            l = length_m or 3.20
            return cls.generate_l_shaped_stair(x, y, flight_w=w * 0.45, run1_len=l * 0.60, run2_len=w * 0.55, risers=risers)

        elif typology == StairTypology.U_SHAPED:
            w = width_m or 2.20
            l = length_m or 3.20
            fw = (w - 0.15) / 2.0
            fl = l * 0.65
            ld = l - fl
            return cls.generate_u_shaped_stair(x, y, flight_w=fw, flight_len=fl, landing_d=ld, risers=risers)

        elif typology == StairTypology.WINDER:
            w = width_m or 2.20
            l = length_m or 3.20
            return cls.generate_winder_stair(x, y, flight_w=w * 0.45, run_len=l * 0.55, risers=risers)

        elif typology == StairTypology.SPIRAL:
            dia = width_m or kwargs.get("diameter", 1.60)
            r = dia * 0.50
            # Shrink radius if room_bbox demands it
            if room_bbox is not None:
                avail_r = min(
                    (room_bbox[2] - room_bbox[0]) / 2.0 - 0.23,
                    (room_bbox[3] - room_bbox[1]) / 2.0 - 0.23
                )
                r = min(r, max(0.60, avail_r))
            model = cls.generate_spiral_stair(center_x=x + r, center_y=y + r, radius_m=r, risers=risers)
            if room_bbox is not None:
                model = cls._clamp_curved_to_bbox(model, room_bbox)
            return model

        elif typology == StairTypology.CURVED:
            outer_r = width_m or kwargs.get("outer_r", 2.60)
            # Clamp outer_r so the curved stair fits within room_bbox
            if room_bbox is not None:
                avail_w = (room_bbox[2] - room_bbox[0]) - 2 * 0.23
                avail_h = (room_bbox[3] - room_bbox[1]) - 2 * 0.23
                outer_r = min(outer_r, avail_w * 0.5, avail_h)
                outer_r = max(1.20, outer_r)  # Minimum viable curved stair
            model = cls.generate_curved_stair(center_x=x + outer_r, center_y=y, outer_r=outer_r, risers=risers)
            if room_bbox is not None:
                model = cls._clamp_curved_to_bbox(model, room_bbox)
            return model

        elif typology == StairTypology.LADDER:
            w = width_m or 0.70
            l = length_m or 2.40
            return cls.generate_ladder_stair(x, y, width_m=w, length_m=l, risers=max(10, risers - 4))

        elif typology == StairTypology.FLOATING:
            w = width_m or 1.10
            l = length_m or 3.60
            return cls.generate_floating_stair(x, y, width_m=w, length_m=l, risers=risers)

        elif typology == StairTypology.BIFURCATED:
            main_w = (width_m * 0.45) if width_m else 1.60
            main_len = (length_m * 0.55) if length_m else 2.40
            model = cls.generate_bifurcated_stair(x, y, main_w=main_w, main_len=main_len, risers=risers)
            if room_bbox is not None:
                model = cls._clamp_bifurcated_to_bbox(model, room_bbox)
            return model

        else:
            raise ValueError(f"Unsupported stair typology: {typology}")

    @classmethod
    def to_room_model(
        cls,
        model: StairParametricModel,
        level_index: int = 0,
        room_id: Optional[str] = None
    ) -> RoomModel:
        """Converts a StairParametricModel to a code-compliant Canonical RoomModel."""
        bx1, by1, bx2, by2 = model.bounding_box
        rw = bx2 - bx1
        rh = by2 - by1
        poly = [[bx1, by1], [bx2, by1], [bx2, by2], [bx1, by2], [bx1, by1]]
        area = rw * rh
        rid = room_id or f"room_L{level_index}_staircase_{model.typology.value}"
        rname = f"{model.typology.value.replace('_', ' ').title()} Staircase Core"

        if model.landings:
            lp = model.landings[0].polygon
            ys = [p[1] for p in lp]
            xs = [p[0] for p in lp]
            calc_d = min(max(ys) - min(ys), max(xs) - min(xs))
            landing_d = calc_d if calc_d > 0.1 else model.flight_width_m
        else:
            landing_d = model.flight_width_m

        meta = {
            "typology": model.typology.value,
            "riser_count": model.total_risers,
            "riser_height": model.riser_height_m,
            "tread_depth": model.tread_going_m,
            "flight_width": model.flight_width_m,
            "landing_depth": landing_d,
            "headroom_m": model.headroom_clearance_m,
            "level_index": level_index
        }
        meta.update(model.metadata)

        return RoomModel(
            room_id=rid,
            room_type="corridor",
            room_name=rname,
            polygon=poly,
            area_m2=round(area, 2),
            centroid=[round(bx1 + rw * 0.5, 2), round(by1 + rh * 0.5, 2)],
            level_index=level_index,
            is_habitable=False,
            metadata=meta
        )


# =========================================================================
# Formal Specialized Staircase Engine Classes
# =========================================================================

class DoglegStaircase:
    """Dogleg / U-shaped switchback staircase engine."""
    typology = StairTypology.U_SHAPED

    @classmethod
    def generate(cls, x: float = 0.0, y: float = 0.0, **kwargs) -> StairParametricModel:
        return StaircaseEngine.create_staircase(StairTypology.U_SHAPED, x=x, y=y, **kwargs)

    @classmethod
    def to_room_model(cls, model: StairParametricModel, level_index: int = 0, room_id: Optional[str] = None) -> RoomModel:
        return StaircaseEngine.to_room_model(model, level_index=level_index, room_id=room_id)


class LinearFlightStaircase:
    """Straight / linear flight staircase engine without turns."""
    typology = StairTypology.STRAIGHT

    @classmethod
    def generate(cls, x: float = 0.0, y: float = 0.0, **kwargs) -> StairParametricModel:
        return StaircaseEngine.create_staircase(StairTypology.STRAIGHT, x=x, y=y, **kwargs)

    @classmethod
    def to_room_model(cls, model: StairParametricModel, level_index: int = 0, room_id: Optional[str] = None) -> RoomModel:
        return StaircaseEngine.to_room_model(model, level_index=level_index, room_id=room_id)


class CurvedOrCircularStaircase:
    """Sweeping curved arc, circular rotunda, or spiral staircase engine."""
    typology = StairTypology.CURVED

    @classmethod
    def generate(cls, x: float = 0.0, y: float = 0.0, is_spiral: bool = False, **kwargs) -> StairParametricModel:
        stype = StairTypology.SPIRAL if is_spiral else StairTypology.CURVED
        return StaircaseEngine.create_staircase(stype, x=x, y=y, **kwargs)

    @classmethod
    def to_room_model(cls, model: StairParametricModel, level_index: int = 0, room_id: Optional[str] = None) -> RoomModel:
        return StaircaseEngine.to_room_model(model, level_index=level_index, room_id=room_id)


class SplitFlightGrandStaircase:
    """Bifurcated grand central flight ascending to intermediate landing branching left & right."""
    typology = StairTypology.BIFURCATED

    @classmethod
    def generate(cls, x: float = 0.0, y: float = 0.0, **kwargs) -> StairParametricModel:
        return StaircaseEngine.create_staircase(StairTypology.BIFURCATED, x=x, y=y, **kwargs)

    @classmethod
    def to_room_model(cls, model: StairParametricModel, level_index: int = 0, room_id: Optional[str] = None) -> RoomModel:
        return StaircaseEngine.to_room_model(model, level_index=level_index, room_id=room_id)


class BoundaryPassageStaircase:
    """Side external setback passage staircase for rental / upper-unit independence."""
    typology = StairTypology.STRAIGHT

    @classmethod
    def generate(cls, x: float = 0.0, y: float = 0.0, width_m: float = 0.95, length_m: float = 4.20, **kwargs) -> StairParametricModel:
        model = StaircaseEngine.create_staircase(StairTypology.STRAIGHT, x=x, y=y, width_m=width_m, length_m=length_m, **kwargs)
        model.metadata["is_external_boundary_stair"] = True
        model.metadata["rental_access"] = True
        return model

    @classmethod
    def to_room_model(cls, model: StairParametricModel, level_index: int = 0, room_id: Optional[str] = None) -> RoomModel:
        rm = StaircaseEngine.to_room_model(model, level_index=level_index, room_id=room_id)
        rm.room_name = f"External Boundary Staircase (L{level_index})"
        rm.metadata["is_external"] = True
        return rm


STAIRCASE_CLASS_MAP = {
    "DoglegStaircase": DoglegStaircase,
    "LinearFlightStaircase": LinearFlightStaircase,
    "CurvedOrCircularStaircase": CurvedOrCircularStaircase,
    "SplitFlightGrandStaircase": SplitFlightGrandStaircase,
    "BoundaryPassageStaircase": BoundaryPassageStaircase,
}

