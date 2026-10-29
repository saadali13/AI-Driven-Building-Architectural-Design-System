"""
Phase 12: Production-Grade Layered AutoCAD DXF Exporter.
Exports CanonicalFloorPlan to professional industry-standard DXF (R2018) adhering strictly
to American Institute of Architects (AIA) CAD Layer Guidelines:

AIA Layer Standards:
- A-WALL-EXTR: Outer thermal envelope (Lineweight 0.50mm, Color 4 Cyan)
- A-WALL-INTR: Interior partition walls (Lineweight 0.25mm, Color 7 White)
- A-DOOR: Door leaves, frames, and 90-degree swing arcs (Lineweight 0.25mm, Color 1 Red)
- A-GLAZ: Window frames, glazing lines, and sills (Lineweight 0.25mm, Color 3 Green)
- A-STRS: Stair treads, risers, stringers, breaklines, and balustrade vectors (Lineweight 0.35mm, Color 6 Magenta)
- A-FURN: Architectural furniture blocks: beds, nightstands, sanitary fixtures, kitchen counters, dining set, vehicles (Lineweight 0.18mm, Color 8 Gray)
- A-ANNO-TEXT: Room names, dimension callouts, and area tags (Lineweight 0.25mm, Color 2 Yellow)
- A-ANNO-DIMS: Exterior dimension strings, witness lines, and tick marks (Lineweight 0.18mm, Color 5 Blue)
- A-AREA: Closed room boundary polylines (Lineweight 0.18mm, Color 8 Gray)
- A-TITLE-BLOCK: Drawing title and scale annotations (Lineweight 0.50mm, Color 6 Magenta)
"""

import os
import math
from typing import Optional, List, Dict, Any, Tuple
import ezdxf
from ezdxf.enums import TextEntityAlignment
from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, WallModel, OpeningModel


class DXFGenerator:
    """
    Industry-standard AutoCAD DXF Generator supporting multi-floor residential architecture.
    """
    def __init__(self, dxf_version: str = "R2018"):
        self.dxf_version = dxf_version

    def _setup_layers(self, doc):
        """Initializes standardized AIA CAD layers with specified colors and lineweights."""
        doc.layers.add("A-WALL-EXTR", color=4, lineweight=50)    # Cyan, 0.50mm
        doc.layers.add("A-WALL-INTR", color=7, lineweight=25)    # White, 0.25mm
        doc.layers.add("A-DOOR", color=1, lineweight=25)         # Red, 0.25mm
        doc.layers.add("A-GLAZ", color=3, lineweight=25)         # Green, 0.25mm
        doc.layers.add("A-STRS", color=6, lineweight=35)         # Magenta, 0.35mm
        doc.layers.add("A-FURN", color=8, lineweight=18)         # Gray, 0.18mm
        doc.layers.add("A-ANNO-TEXT", color=2, lineweight=25)    # Yellow, 0.25mm
        doc.layers.add("A-ANNO-DIMS", color=5, lineweight=18)    # Blue, 0.18mm
        doc.layers.add("A-AREA", color=8, lineweight=18)         # Gray, 0.18mm
        doc.layers.add("A-TITLE-BLOCK", color=6, lineweight=50)  # Magenta, 0.50mm
        doc.layers.add("A-COLS", color=6, lineweight=50)         # Magenta, 0.50mm Structural RCC Columns

    def _draw_columns(self, msp, plan: CanonicalFloorPlan, level_index: Optional[int] = None, offset_x: float = 0.0, offset_y: float = 0.0):
        """Renders 9\"x18\" RCC column nodes at primary structural grid intersections on A-COLS."""
        cols = plan.metadata.provenance.get("columns", [])
        for c in cols:
            if level_index is not None and "serves_levels" in c:
                if level_index not in c["serves_levels"]:
                    continue
            pos = c.get("position_2d", [0.0, 0.0])
            dims = c.get("dimensions_m", [0.229, 0.457])
            cw, cd = dims[0], dims[1]
            x0 = pos[0] - cw / 2.0 + offset_x
            y0 = pos[1] - cd / 2.0 + offset_y
            poly = [(x0, y0), (x0 + cw, y0), (x0 + cw, y0 + cd), (x0, y0 + cd)]
            msp.add_lwpolyline(poly, close=True, dxfattribs={"layer": "A-COLS"})
            msp.add_line((x0, y0), (x0 + cw, y0 + cd), dxfattribs={"layer": "A-COLS"})
            msp.add_line((x0, y0 + cd), (x0 + cw, y0), dxfattribs={"layer": "A-COLS"})

    def _draw_walls(self, msp, walls: List[WallModel], offset_x: float = 0.0, offset_y: float = 0.0):
        for wall in walls:
            layer = "A-WALL-EXTR" if wall.wall_type == "exterior" else "A-WALL-INTR"
            p1 = wall.centerline[0]
            p2 = wall.centerline[1]
            msp.add_line(
                (p1[0] + offset_x, p1[1] + offset_y),
                (p2[0] + offset_x, p2[1] + offset_y),
                dxfattribs={"layer": layer}
            )

    def _draw_openings(self, msp, openings: List[OpeningModel], walls: List[WallModel], offset_x: float = 0.0, offset_y: float = 0.0):
        for op in openings:
            pos = [op.position[0] + offset_x, op.position[1] + offset_y]
            w = op.width_m

            # Determine wall orientation
            is_vertical = False
            best_dist = 999.0
            for wall in walls:
                p1 = [wall.centerline[0][0] + offset_x, wall.centerline[0][1] + offset_y]
                p2 = [wall.centerline[1][0] + offset_x, wall.centerline[1][1] + offset_y]
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                lsq = dx*dx + dy*dy
                if lsq < 1e-4:
                    continue
                t = max(0.0, min(1.0, ((pos[0] - p1[0])*dx + (pos[1] - p1[1])*dy) / lsq))
                proj_x = p1[0] + t * dx
                proj_y = p1[1] + t * dy
                dist = math.hypot(pos[0] - proj_x, pos[1] - proj_y)
                if dist < best_dist:
                    best_dist = dist
                    is_vertical = abs(dy) > abs(dx)

            if op.opening_type == "door":
                # Standard architectural door leaf and 90-degree swing arc
                if is_vertical:
                    msp.add_line((pos[0], pos[1]), (pos[0] + w, pos[1]), dxfattribs={"layer": "A-DOOR"})
                    msp.add_arc(center=(pos[0], pos[1]), radius=w, start_angle=0, end_angle=90, dxfattribs={"layer": "A-DOOR"})
                else:
                    msp.add_line((pos[0], pos[1]), (pos[0], pos[1] + w), dxfattribs={"layer": "A-DOOR"})
                    msp.add_arc(center=(pos[0], pos[1]), radius=w, start_angle=0, end_angle=90, dxfattribs={"layer": "A-DOOR"})
            elif op.opening_type == "window":
                half_w = w / 2.0
                if is_vertical:
                    msp.add_line((pos[0], pos[1] - half_w), (pos[0], pos[1] + half_w), dxfattribs={"layer": "A-GLAZ"})
                    msp.add_line((pos[0] + 0.06, pos[1] - half_w), (pos[0] + 0.06, pos[1] + half_w), dxfattribs={"layer": "A-GLAZ"})
                    msp.add_line((pos[0] - 0.06, pos[1] - half_w), (pos[0] - 0.06, pos[1] + half_w), dxfattribs={"layer": "A-GLAZ"})
                else:
                    msp.add_line((pos[0] - half_w, pos[1]), (pos[0] + half_w, pos[1]), dxfattribs={"layer": "A-GLAZ"})
                    msp.add_line((pos[0] - half_w, pos[1] + 0.06), (pos[0] + half_w, pos[1] + 0.06), dxfattribs={"layer": "A-GLAZ"})
                    msp.add_line((pos[0] - half_w, pos[1] - 0.06), (pos[0] + half_w, pos[1] - 0.06), dxfattribs={"layer": "A-GLAZ"})

    def _draw_stairs(self, msp, stair_rooms: List[RoomModel], is_first_floor: bool, offset_x: float = 0.0, offset_y: float = 0.0):
        for room in stair_rooms:
            pts = room.polygon
            min_x = min(pt[0] for pt in pts) + offset_x
            max_x = max(pt[0] for pt in pts) + offset_x
            min_y = min(pt[1] for pt in pts) + offset_y
            max_y = max(pt[1] for pt in pts) + offset_y
            rw = max_x - min_x
            rh = max_y - min_y

            half_w = rw / 2.0
            flight_h = rh * 0.72
            steps = 9
            step_h = flight_h / steps

            # Central dividing spine
            msp.add_line((min_x + half_w, min_y), (min_x + half_w, min_y + flight_h), dxfattribs={"layer": "A-STRS"})

            # Intermediate Landing
            msp.add_line((min_x, min_y + flight_h), (min_x + rw, min_y + flight_h), dxfattribs={"layer": "A-STRS"})

            # Flight 1 treads
            for i in range(steps + 1):
                sy = min_y + i * step_h
                msp.add_line((min_x, sy), (min_x + half_w, sy), dxfattribs={"layer": "A-STRS"})

            # Flight 2 treads
            for i in range(steps + 1):
                sy = min_y + i * step_h
                msp.add_line((min_x + half_w, sy), (min_x + rw, sy), dxfattribs={"layer": "A-STRS"})

            # Double-line balustrade along floor void (Level 1)
            if is_first_floor:
                msp.add_line((min_x + rw, min_y), (min_x + rw, min_y + flight_h), dxfattribs={"layer": "A-STRS"})
                msp.add_line((min_x + rw - 0.08, min_y), (min_x + rw - 0.08, min_y + flight_h), dxfattribs={"layer": "A-STRS"})
                # Terminal posts
                msp.add_circle((min_x + rw, min_y), 0.06, dxfattribs={"layer": "A-STRS"})
                msp.add_circle((min_x + rw, min_y + flight_h), 0.06, dxfattribs={"layer": "A-STRS"})
                msp.add_text("BALUSTRADE (1050mm)", dxfattribs={"layer": "A-ANNO-TEXT", "height": 0.16}).set_placement((min_x + rw - 0.15, min_y + flight_h * 0.5), align=TextEntityAlignment.MIDDLE_RIGHT)

    def _draw_furniture(self, msp, rooms: List[RoomModel], level_index: int, offset_x: float = 0.0, offset_y: float = 0.0):
        for room in rooms:
            pts = room.polygon
            min_x = min(pt[0] for pt in pts) + offset_x
            max_x = max(pt[0] for pt in pts) + offset_x
            min_y = min(pt[1] for pt in pts) + offset_y
            max_y = max(pt[1] for pt in pts) + offset_y
            rw = max_x - min_x
            rh = max_y - min_y
            cx = room.centroid[0] + offset_x
            cy = room.centroid[1] + offset_y
            r_lower = room.room_name.lower()
            is_master = bool(room.metadata.get("master") or "master" in r_lower)

            if room.room_type == "bedroom":
                # Master or Secondary Bed Suite with nightstands
                bed_w = 2.00 if is_master else 1.70
                bed_l = 2.10
                bx = cx - bed_w / 2.0
                by = cy + 0.30 - bed_l / 2.0
                bed_poly = [(bx, by), (bx + bed_w, by), (bx + bed_w, by + bed_l), (bx, by + bed_l)]
                msp.add_lwpolyline(bed_poly, close=True, dxfattribs={"layer": "A-FURN"})
                # Padded Headboard
                msp.add_lwpolyline([(bx - 0.06, by + bed_l - 0.15), (bx + bed_w + 0.06, by + bed_l - 0.15), (bx + bed_w + 0.06, by + bed_l), (bx - 0.06, by + bed_l)], close=True, dxfattribs={"layer": "A-FURN"})
                # Duvet fold
                msp.add_line((bx, by + bed_l * 0.40), (bx + bed_w, by + bed_l * 0.40), dxfattribs={"layer": "A-FURN", "linetype": "DASHED"})
                # Pillows (2 or 4)
                p_w = (bed_w - 0.30) / 2.0
                msp.add_lwpolyline([(bx + 0.10, by + bed_l - 0.55), (bx + 0.10 + p_w, by + bed_l - 0.55), (bx + 0.10 + p_w, by + bed_l - 0.20), (bx + 0.10, by + bed_l - 0.20)], close=True, dxfattribs={"layer": "A-FURN"})
                msp.add_lwpolyline([(bx + bed_w - 0.10 - p_w, by + bed_l - 0.55), (bx + bed_w - 0.10, by + bed_l - 0.55), (bx + bed_w - 0.10, by + bed_l - 0.20), (bx + bed_w - 0.10 - p_w, by + bed_l - 0.20)], close=True, dxfattribs={"layer": "A-FURN"})
                # Nightstands
                ns_size = 0.50 if is_master else 0.42
                msp.add_lwpolyline([(bx - ns_size - 0.08, by + bed_l - ns_size), (bx - 0.08, by + bed_l - ns_size), (bx - 0.08, by + bed_l), (bx - ns_size - 0.08, by + bed_l)], close=True, dxfattribs={"layer": "A-FURN"})
                msp.add_lwpolyline([(bx + bed_w + 0.08, by + bed_l - ns_size), (bx + bed_w + ns_size + 0.08, by + bed_l - ns_size), (bx + bed_w + ns_size + 0.08, by + bed_l), (bx + bed_w + 0.08, by + bed_l)], close=True, dxfattribs={"layer": "A-FURN"})
                if is_master:
                    # End of bed bench
                    bench_w, bench_d = bed_w * 0.85, 0.40
                    msp.add_lwpolyline([(cx - bench_w / 2.0, by - bench_d - 0.06), (cx + bench_w / 2.0, by - bench_d - 0.06), (cx + bench_w / 2.0, by - 0.06), (cx - bench_w / 2.0, by - 0.06)], close=True, dxfattribs={"layer": "A-FURN"})

            elif room.room_type == "bathroom":
                is_5_fixture = bool(room.metadata.get("double_vanity") or "5-fixture" in r_lower or "spa" in r_lower or (is_master and rw >= 2.0))
                is_powder = bool("powder" in r_lower)

                if is_powder:
                    # Powder room: Floating Vanity + Concealed Wall-Hung WC
                    vx, vy = min_x + 0.15, min_y + rh - 0.65
                    msp.add_lwpolyline([(vx, vy), (vx + 0.80, vy), (vx + 0.80, vy + 0.50), (vx, vy + 0.50)], close=True, dxfattribs={"layer": "A-FURN"})
                    msp.add_circle((vx + 0.40, vy + 0.25), 0.18, dxfattribs={"layer": "A-FURN"})
                    # Wall-hung WC
                    wc_x, wc_y = min_x + (rw - 0.40) / 2.0, min_y + 0.12
                    msp.add_lwpolyline([(wc_x - 0.05, min_y + 0.04), (wc_x + 0.45, min_y + 0.04), (wc_x + 0.45, min_y + 0.12), (wc_x - 0.05, min_y + 0.12)], close=True, dxfattribs={"layer": "A-FURN"})
                    msp.add_lwpolyline([(wc_x, wc_y), (wc_x + 0.40, wc_y), (wc_x + 0.40, wc_y + 0.55), (wc_x, wc_y + 0.55)], close=True, dxfattribs={"layer": "A-FURN"})

                elif is_5_fixture and rw >= 2.0 and rh >= 2.0:
                    # 1. Double Vanity Counter along East Wall
                    vx = min_x + rw - 0.70
                    vy = min_y + 0.20
                    v_len = min(2.0, rh * 0.60)
                    msp.add_lwpolyline([(vx, vy), (vx + 0.60, vy), (vx + 0.60, vy + v_len), (vx, vy + v_len)], close=True, dxfattribs={"layer": "A-FURN"})
                    msp.add_circle((vx + 0.30, vy + v_len * 0.25), 0.18, dxfattribs={"layer": "A-FURN"})
                    msp.add_circle((vx + 0.30, vy + v_len * 0.75), 0.18, dxfattribs={"layer": "A-FURN"})

                    # 2. Freestanding Oval Soaking Tub along North Wall
                    tx, ty = min_x + 0.20, min_y + rh - 0.95
                    tub_w, tub_d = min(1.65, rw * 0.55), 0.78
                    # Octagonal approximation of luxury oval freestanding tub
                    dt_x, dt_y = tub_w * 0.20, tub_d * 0.25
                    tub_pts = [
                        (tx + dt_x, ty), (tx + tub_w - dt_x, ty),
                        (tx + tub_w, ty + dt_y), (tx + tub_w, ty + tub_d - dt_y),
                        (tx + tub_w - dt_x, ty + tub_d), (tx + dt_x, ty + tub_d),
                        (tx, ty + tub_d - dt_y), (tx, ty + dt_y)
                    ]
                    msp.add_lwpolyline(tub_pts, close=True, dxfattribs={"layer": "A-FURN"})
                    msp.add_circle((tx + tub_w / 2.0, ty + tub_d - 0.08), 0.04, dxfattribs={"layer": "A-FURN"})

                    # 3. Frameless Glass Walk-in Shower Enclosure with Linear Drain
                    sh_w, sh_d = 1.15, 1.15
                    sx, sy = min_x + 0.15, min_y + 0.20
                    msp.add_lwpolyline([(sx, sy), (sx + sh_w, sy), (sx + sh_w, sy + sh_d), (sx, sy + sh_d)], close=True, dxfattribs={"layer": "A-FURN", "linetype": "DASHED"})
                    msp.add_line((sx + 0.10, sy + 0.12), (sx + sh_w - 0.10, sy + 0.12), dxfattribs={"layer": "A-FURN"})
                    msp.add_circle((sx + sh_w / 2.0, sy + sh_d / 2.0), 0.06, dxfattribs={"layer": "A-FURN"})

                    # 4. Enclosed Wall-Hung WC
                    wc_x, wc_y = min_x + 0.25, sy + sh_d + 0.35
                    msp.add_lwpolyline([(wc_x, wc_y), (wc_x + 0.38, wc_y), (wc_x + 0.38, wc_y + 0.55), (wc_x, wc_y + 0.55)], close=True, dxfattribs={"layer": "A-FURN"})

                else:
                    # Secondary 3-fixture bath
                    vx = min_x + rw - 0.70
                    vy = min_y + 0.15
                    msp.add_lwpolyline([(vx, vy), (vx + 0.60, vy), (vx + 0.60, vy + 0.75), (vx, vy + 0.75)], close=True, dxfattribs={"layer": "A-FURN"})
                    msp.add_circle((vx + 0.30, vy + 0.375), 0.18, dxfattribs={"layer": "A-FURN"})
                    wc_x, wc_y = min_x + 0.18, min_y + 0.15
                    msp.add_lwpolyline([(wc_x, wc_y), (wc_x + 0.38, wc_y), (wc_x + 0.38, wc_y + 0.55), (wc_x, wc_y + 0.55)], close=True, dxfattribs={"layer": "A-FURN"})
                    sh_s = min(1.05, rw * 0.45, rh * 0.45)
                    msp.add_lwpolyline([(min_x + 0.15, min_y + rh - sh_s - 0.15), (min_x + 0.15 + sh_s, min_y + rh - sh_s - 0.15), (min_x + 0.15 + sh_s, min_y + rh - 0.15), (min_x + 0.15, min_y + rh - 0.15)], close=True, dxfattribs={"layer": "A-FURN", "linetype": "DASHED"})

            elif room.room_type == "kitchen":
                is_scullery = bool("dirty" in r_lower or "scullery" in r_lower or "wet" in r_lower)
                if not is_scullery:
                    # Gourmet Show Kitchen: Central Waterfall Island (8ft x 4ft = 2.44m x 1.22m) + Stools
                    isl_w = min(2.44, rw * 0.75)
                    isl_h = min(1.22, rh * 0.45)
                    ix = min_x + (rw - isl_w) / 2.0
                    iy = min_y + (rh - isl_h) / 2.0
                    msp.add_lwpolyline([(ix, iy), (ix + isl_w, iy), (ix + isl_w, iy + isl_h), (ix, iy + isl_h)], close=True, dxfattribs={"layer": "A-FURN"})
                    # Waterfall return double lines
                    msp.add_line((ix + 0.09, iy), (ix + 0.09, iy + isl_h), dxfattribs={"layer": "A-FURN"})
                    msp.add_line((ix + isl_w - 0.09, iy), (ix + isl_w - 0.09, iy + isl_h), dxfattribs={"layer": "A-FURN"})
                    # Prep sink & faucet
                    msp.add_lwpolyline([(ix + 0.35, iy + (isl_h - 0.42) / 2.0), (ix + 0.85, iy + (isl_h - 0.42) / 2.0), (ix + 0.85, iy + (isl_h + 0.42) / 2.0), (ix + 0.35, iy + (isl_h + 0.42) / 2.0)], close=True, dxfattribs={"layer": "A-FURN"})
                    msp.add_circle((ix + 0.60, iy + isl_h / 2.0 + 0.15), 0.035, dxfattribs={"layer": "A-FURN"})
                    # 4 Bar Stools outside walkway line
                    for k in range(4):
                        st_x = ix + 0.35 + k * ((isl_w - 0.70) / 3.0)
                        st_y = iy + isl_h + 0.28
                        msp.add_circle((st_x, st_y), 0.18, dxfattribs={"layer": "A-FURN"})
                else:
                    # Heavy Cooking Wet Kitchen: 24" perimeter counters, double sink, 5-burner hob, fridge
                    depth = 0.61  # 24"
                    msp.add_lwpolyline([(min_x + 0.08, min_y + 0.08), (max_x - 0.08, min_y + 0.08), (max_x - 0.08, min_y + depth + 0.08), (min_x + depth + 0.08, min_y + depth + 0.08), (min_x + depth + 0.08, max_y - 0.08), (min_x + 0.08, max_y - 0.08)], close=True, dxfattribs={"layer": "A-FURN"})
                    # Double sink
                    sx = min_x + rw * 0.22
                    msp.add_lwpolyline([(sx, min_y + 0.12), (sx + 0.90, min_y + 0.12), (sx + 0.90, min_y + 0.58), (sx, min_y + 0.58)], close=True, dxfattribs={"layer": "A-FURN"})
                    # 5-burner hob
                    hx = min_x + rw * 0.60
                    msp.add_lwpolyline([(hx, min_y + 0.12), (hx + 0.80, min_y + 0.12), (hx + 0.80, min_y + 0.58), (hx, min_y + 0.58)], close=True, dxfattribs={"layer": "A-FURN"})
                    for bx, by in [(hx + 0.18, min_y + 0.24), (hx + 0.62, min_y + 0.24), (hx + 0.18, min_y + 0.44), (hx + 0.62, min_y + 0.44), (hx + 0.40, min_y + 0.34)]:
                        msp.add_circle((bx, by), 0.06, dxfattribs={"layer": "A-FURN"})

            elif room.room_type == "dining_room" or "dining" in r_lower:
                # 8-Seater Formal Dining Table (2.44m x 1.10m = 8ft x 3.6ft)
                tw, th = 2.44, 1.10
                tx, ty = cx - tw / 2.0, cy - th / 2.0
                msp.add_lwpolyline([(tx, ty), (tx + tw, ty), (tx + tw, ty + th), (tx, ty + th)], close=True, dxfattribs={"layer": "A-FURN"})
                # 3ft (0.91m) pull-out clearance boundary (dashed buffer)
                clr_d = 0.91
                msp.add_lwpolyline([(tx - clr_d * 0.65, ty - clr_d), (tx + tw + clr_d * 0.65, ty - clr_d), (tx + tw + clr_d * 0.65, ty + th + clr_d), (tx - clr_d * 0.65, ty + th + clr_d)], close=True, dxfattribs={"layer": "A-FURN", "linetype": "DASHED"})
                # 8 individual chairs
                ch_w, ch_d = 0.45, 0.40
                spacing = tw / 3.0
                for i in range(3):
                    # Top chairs
                    cx_i = tx + i * spacing + (spacing - ch_w) / 2.0
                    msp.add_lwpolyline([(cx_i, ty + th + 0.05), (cx_i + ch_w, ty + th + 0.05), (cx_i + ch_w, ty + th + ch_d + 0.05), (cx_i, ty + th + ch_d + 0.05)], close=True, dxfattribs={"layer": "A-FURN"})
                    # Bottom chairs
                    msp.add_lwpolyline([(cx_i, ty - ch_d - 0.05), (cx_i + ch_w, ty - ch_d - 0.05), (cx_i + ch_w, ty - 0.05), (cx_i, ty - 0.05)], close=True, dxfattribs={"layer": "A-FURN"})
                # End head chairs
                msp.add_lwpolyline([(tx - ch_d - 0.05, cy - ch_w / 2.0), (tx - 0.05, cy - ch_w / 2.0), (tx - 0.05, cy + ch_w / 2.0), (tx - ch_d - 0.05, cy + ch_w / 2.0)], close=True, dxfattribs={"layer": "A-FURN"})
                msp.add_lwpolyline([(tx + tw + 0.05, cy - ch_w / 2.0), (tx + tw + ch_d + 0.05, cy - ch_w / 2.0), (tx + tw + ch_d + 0.05, cy + ch_w / 2.0), (tx + tw + 0.05, cy + ch_w / 2.0)], close=True, dxfattribs={"layer": "A-FURN"})

            elif room.room_type == "garage" or "porch" in r_lower:
                # Authentic 1:100 CAD Vehicles: Luxury SUV (5.03m x 1.98m) & Passenger Sedan (4.57m x 1.83m)
                car_slots = [
                    (min_x + rw * 0.28, 5.03, 1.98, "SUV"),
                    (min_x + rw * 0.72, 4.57, 1.83, "SEDAN")
                ] if rw >= 4.5 else [(min_x + rw * 0.50, 4.80, 1.90, "VEHICLE")]

                for car_cx, v_len, v_w, v_type in car_slots:
                    bx = car_cx - v_w / 2.0
                    by = min_y + 0.60
                    # 1. 2.5ft (0.76m) Door Opening Clearance Buffer (Dashed)
                    buf = 0.76
                    msp.add_lwpolyline([(bx - buf, by - 0.35), (bx + v_w + buf, by - 0.35), (bx + v_w + buf, by + v_len + 0.35), (bx - buf, by + v_len + 0.35)], close=True, dxfattribs={"layer": "A-FURN", "linetype": "DASHED"})
                    # 2. Outer Body Contour
                    msp.add_lwpolyline([(bx, by), (bx + v_w, by), (bx + v_w, by + v_len), (bx, by + v_len)], close=True, dxfattribs={"layer": "A-FURN"})
                    # 3. Windshields
                    msp.add_line((bx + 0.20, by + v_len * 0.22), (bx + v_w - 0.20, by + v_len * 0.22), dxfattribs={"layer": "A-FURN"})
                    msp.add_line((bx + 0.20, by + v_len * 0.78), (bx + v_w - 0.20, by + v_len * 0.78), dxfattribs={"layer": "A-FURN"})
                    # 4. Sunroof / Roof rail
                    msp.add_lwpolyline([(bx + 0.25, by + v_len * 0.35), (bx + v_w - 0.25, by + v_len * 0.35), (bx + v_w - 0.25, by + v_len * 0.65), (bx + 0.25, by + v_len * 0.65)], close=True, dxfattribs={"layer": "A-FURN"})
                    # 5. Side mirrors
                    msp.add_lwpolyline([(bx - 0.12, by + v_len * 0.70), (bx, by + v_len * 0.70), (bx, by + v_len * 0.76), (bx - 0.12, by + v_len * 0.76)], close=True, dxfattribs={"layer": "A-FURN"})
                    msp.add_lwpolyline([(bx + v_w, by + v_len * 0.70), (bx + v_w + 0.12, by + v_len * 0.70), (bx + v_w + 0.12, by + v_len * 0.76), (bx + v_w, by + v_len * 0.76)], close=True, dxfattribs={"layer": "A-FURN"})

            elif room.room_type == "living_room" or "lounge" in r_lower or "drawing" in r_lower:
                is_formal = bool("drawing" in r_lower or "salon" in r_lower)
                if is_formal:
                    # Formal Drawing Suite: Sofa + Armchairs + Coffee Table
                    sw, sd = min(2.50, rw * 0.55), 0.90
                    sx, sy = cx - sw / 2.0, cy - rh * 0.30
                    msp.add_lwpolyline([(sx, sy), (sx + sw, sy), (sx + sw, sy + sd), (sx, sy + sd)], close=True, dxfattribs={"layer": "A-FURN"})
                    # Coffee Table
                    msp.add_lwpolyline([(cx - 0.65, cy - 0.35), (cx + 0.65, cy - 0.35), (cx + 0.65, cy + 0.35), (cx - 0.65, cy + 0.35)], close=True, dxfattribs={"layer": "A-FURN"})
                else:
                    # Modular L-Shaped Sectional Sofa
                    sofa_w = min(3.00, rw * 0.60)
                    sofa_h = min(2.60, rh * 0.60)
                    sx = cx - sofa_w / 2.0
                    sy = cy - sofa_h / 2.0
                    msp.add_lwpolyline([(sx, sy), (sx + sofa_w, sy), (sx + sofa_w, sy + 0.90), (sx + 0.90, sy + 0.90), (sx + 0.90, sy + sofa_h), (sx, sy + sofa_h)], close=True, dxfattribs={"layer": "A-FURN"})
                    # Coffee Table
                    msp.add_lwpolyline([(sx + 1.20, sy + 1.20), (sx + 2.30, sy + 1.20), (sx + 2.30, sy + 1.85), (sx + 1.20, sy + 1.85)], close=True, dxfattribs={"layer": "A-FURN"})
                    # 4.5" TV Baffle Wall & Console (min 7ft viewing distance)
                    tv_wall_x = cx + rw * 0.32
                    tv_wall_y = cy - 0.90
                    msp.add_lwpolyline([(tv_wall_x, tv_wall_y), (tv_wall_x + 0.115, tv_wall_y), (tv_wall_x + 0.115, tv_wall_y + 1.80), (tv_wall_x, tv_wall_y + 1.80)], close=True, dxfattribs={"layer": "A-FURN"})
                    msp.add_lwpolyline([(tv_wall_x - 0.35, tv_wall_y + 0.15), (tv_wall_x, tv_wall_y + 0.15), (tv_wall_x, tv_wall_y + 1.65), (tv_wall_x - 0.35, tv_wall_y + 1.65)], close=True, dxfattribs={"layer": "A-FURN"})

    def _draw_room_labels(self, msp, rooms: List[RoomModel], offset_x: float = 0.0, offset_y: float = 0.0):
        for room in rooms:
            if "stair" in room.room_name.lower():
                continue

            pts = room.polygon
            min_x = min(pt[0] for pt in pts) + offset_x
            max_x = max(pt[0] for pt in pts) + offset_x
            min_y = min(pt[1] for pt in pts) + offset_y
            max_y = max(pt[1] for pt in pts) + offset_y
            rw = max_x - min_x
            rh = max_y - min_y
            cx = room.centroid[0] + offset_x
            cy = room.centroid[1] + offset_y
            r_lower = room.room_name.lower()

            # Dynamic centroid offsets matching visualizer
            if room.room_type == "bedroom":
                label_x = cx
                label_y = min_y + 0.65
            elif room.room_type == "kitchen":
                label_x = min_x + rw * 0.72
                label_y = min_y + rh * 0.78
            elif room.room_type == "living_room" or "lounge" in r_lower:
                label_x = cx + 0.30
                label_y = min_y + rh * 0.72
            elif room.room_type == "dining_room" or "dining" in r_lower:
                label_x = cx
                label_y = min_y + rh * 0.82
            elif room.room_type == "bathroom":
                label_x = cx
                label_y = min_y + rh * 0.68
            elif room.room_type in ("garage", "balcony") or "porch" in r_lower or "terrace" in r_lower:
                label_x = cx
                label_y = min_y + 0.50
            else:
                label_x = cx
                label_y = cy

            w_ft = rw * 3.28084
            h_ft = rh * 3.28084
            w_str = f"{int(w_ft)}'-{int(round((w_ft % 1) * 12)):02d}\""
            h_str = f"{int(h_ft)}'-{int(round((h_ft % 1) * 12)):02d}\""

            msp.add_text(
                room.room_name,
                dxfattribs={"layer": "A-ANNO-TEXT", "height": 0.24}
            ).set_placement((label_x, label_y + 0.16), align=TextEntityAlignment.MIDDLE_CENTER)

            msp.add_text(
                f"{w_str} x {h_str} ({room.area_m2:.1f} m²)",
                dxfattribs={"layer": "A-ANNO-TEXT", "height": 0.17}
            ).set_placement((label_x, label_y - 0.16), align=TextEntityAlignment.MIDDLE_CENTER)

    def _draw_dimensions(self, msp, rooms: List[RoomModel], offset_x: float = 0.0, offset_y: float = 0.0):
        if not rooms:
            return
        all_xs = [pt[0] + offset_x for r in rooms for pt in r.polygon]
        all_ys = [pt[1] + offset_y for r in rooms for pt in r.polygon]
        b_min_x, b_max_x = min(all_xs), max(all_xs)
        b_min_y, b_max_y = min(all_ys), max(all_ys)

        # 1. Width Dimension along bottom
        dim_y = b_min_y - 1.0
        msp.add_line((b_min_x, dim_y), (b_max_x, dim_y), dxfattribs={"layer": "A-ANNO-DIMS"})
        # Witness lines
        msp.add_line((b_min_x, b_min_y - 0.2), (b_min_x, dim_y - 0.2), dxfattribs={"layer": "A-ANNO-DIMS"})
        msp.add_line((b_max_x, b_min_y - 0.2), (b_max_x, dim_y - 0.2), dxfattribs={"layer": "A-ANNO-DIMS"})
        # 45-degree architectural ticks
        msp.add_line((b_min_x - 0.12, dim_y - 0.12), (b_min_x + 0.12, dim_y + 0.12), dxfattribs={"layer": "A-ANNO-DIMS"})
        msp.add_line((b_max_x - 0.12, dim_y - 0.12), (b_max_x + 0.12, dim_y + 0.12), dxfattribs={"layer": "A-ANNO-DIMS"})
        w_ft = (b_max_x - b_min_x) * 3.28084
        msp.add_text(
            f"WIDTH: {w_ft:.0f}'-0\" ({b_max_x - b_min_x:.2f}m)",
            dxfattribs={"layer": "A-ANNO-DIMS", "height": 0.25}
        ).set_placement(((b_min_x + b_max_x)/2.0, dim_y - 0.35), align=TextEntityAlignment.MIDDLE_CENTER)

        # 2. Depth Dimension along right
        dim_x = b_max_x + 1.0
        msp.add_line((dim_x, b_min_y), (dim_x, b_max_y), dxfattribs={"layer": "A-ANNO-DIMS"})
        # Witness lines
        msp.add_line((b_max_x + 0.2, b_min_y), (dim_x + 0.2, b_min_y), dxfattribs={"layer": "A-ANNO-DIMS"})
        msp.add_line((b_max_x + 0.2, b_max_y), (dim_x + 0.2, b_max_y), dxfattribs={"layer": "A-ANNO-DIMS"})
        # 45-degree architectural ticks
        msp.add_line((dim_x - 0.12, b_min_y - 0.12), (dim_x + 0.12, b_min_y + 0.12), dxfattribs={"layer": "A-ANNO-DIMS"})
        msp.add_line((dim_x - 0.12, b_max_y - 0.12), (dim_x + 0.12, b_max_y + 0.12), dxfattribs={"layer": "A-ANNO-DIMS"})
        d_ft = (b_max_y - b_min_y) * 3.28084
        msp.add_text(
            f"DEPTH: {d_ft:.0f}'-0\" ({b_max_y - b_min_y:.2f}m)",
            dxfattribs={"layer": "A-ANNO-DIMS", "height": 0.25, "rotation": 270}
        ).set_placement((dim_x + 0.35, (b_min_y + b_max_y)/2.0), align=TextEntityAlignment.MIDDLE_CENTER)

    def _draw_level_to_msp(self, msp, plan: CanonicalFloorPlan, level_index: Optional[int] = None, offset_x: float = 0.0, offset_y: float = 0.0):
        walls = [w for w in plan.walls if level_index is None or w.level_index == level_index]
        rooms = [r for r in plan.rooms if level_index is None or r.level_index == level_index]
        openings = [o for o in plan.openings if level_index is None or o.level_index == level_index]
        stair_rooms = [r for r in rooms if "stair" in r.room_name.lower() or "landing" in r.room_name.lower()]

        # 1. Closed Room Boundary Polylines on A-AREA
        for room in rooms:
            pts = [(pt[0] + offset_x, pt[1] + offset_y) for pt in room.polygon]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-AREA"})

        # 2. Structural RCC Columns (A-COLS)
        self._draw_columns(msp, plan, level_index, offset_x, offset_y)

        # 3. Structural & Partition Walls (A-WALL-EXTR, A-WALL-INTR)
        self._draw_walls(msp, walls, offset_x, offset_y)

        # 4. Doors & Glazing Openings (A-DOOR, A-GLAZ)
        self._draw_openings(msp, openings, walls, offset_x, offset_y)

        # 5. Staircases & Balustrades (A-STRS)
        self._draw_stairs(msp, stair_rooms, is_first_floor=(level_index == 1), offset_x=offset_x, offset_y=offset_y)

        # 6. Furniture & Sanitary Fixtures (A-FURN)
        self._draw_furniture(msp, rooms, level_index if level_index is not None else 0, offset_x, offset_y)

        # 7. Room Text Labels (A-ANNO-TEXT)
        self._draw_room_labels(msp, rooms, offset_x, offset_y)

        # 8. Exterior Dimension Strings (A-ANNO-DIMS)
        self._draw_dimensions(msp, rooms, offset_x, offset_y)

        # 9. Floor Title Block Annotation (A-TITLE-BLOCK)
        if rooms:
            all_ys = [pt[1] + offset_y for r in rooms for pt in r.polygon]
            all_xs = [pt[0] + offset_x for r in rooms for pt in r.polygon]
            min_y = min(all_ys)
            mid_x = (min(all_xs) + max(all_xs)) / 2.0
            lvl_name = "GROUND FLOOR PLAN | LEVEL 0" if level_index == 0 else ("FIRST FLOOR PLAN | LEVEL 1" if level_index == 1 else ("SECOND FLOOR / PENTHOUSE | LEVEL 2" if level_index == 2 else f"LEVEL {level_index} PLAN"))
            title_text = f"{lvl_name} [SCALE 1:100]"
            msp.add_text(
                title_text,
                dxfattribs={"layer": "A-TITLE-BLOCK", "height": 0.45}
            ).set_placement((mid_x, min_y - 2.0), align=TextEntityAlignment.MIDDLE_CENTER)

    def export_dxf(self, plan: CanonicalFloorPlan, output_path: str, level_index: Optional[int] = None) -> str:
        doc = ezdxf.new(self.dxf_version, setup=True)
        msp = doc.modelspace()
        self._setup_layers(doc)
        self._draw_level_to_msp(msp, plan, level_index=level_index)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc.saveas(output_path)
        return output_path

    def export_composite_dxf(self, plan: CanonicalFloorPlan, output_path: str) -> str:
        """
        Exports coordinated Ground Floor and First Floor side-by-side on a single modelspace.
        """
        doc = ezdxf.new(self.dxf_version, setup=True)
        msp = doc.modelspace()
        self._setup_layers(doc)

        levels = plan.metadata.levels if plan.metadata.levels else [0, 1]
        cur_offset_x = 0.0

        for lvl in levels:
            lvl_rooms = [r for r in plan.rooms if r.level_index == lvl]
            max_w = 12.0
            if lvl_rooms:
                all_xs = [pt[0] for r in lvl_rooms for pt in r.polygon]
                max_w = max(all_xs) - min(all_xs)

            self._draw_level_to_msp(msp, plan, level_index=lvl, offset_x=cur_offset_x)
            cur_offset_x += max_w + 6.0  # 6m clear spacing between floor plans

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc.saveas(output_path)
        return output_path

    def export_all_floor_dxfs(self, plan: CanonicalFloorPlan, output_dir: str) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        exported = {}
        levels = plan.metadata.levels if plan.metadata.levels else [0]

        for lvl in levels:
            lvl_slug = "ground_floor" if lvl == 0 else f"floor_{lvl}"
            f_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_{lvl_slug}.dxf")
            self.export_dxf(plan, f_path, level_index=lvl)
            exported[lvl_slug] = f_path

        if len(levels) > 1:
            comb_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_composite_both_floors.dxf")
            self.export_composite_dxf(plan, comb_path)
            exported["both_floors"] = comb_path

        return exported


def export_to_dxf(plan: CanonicalFloorPlan, filepath: str) -> str:
    """
    Top-level convenience endpoint for exporting a CanonicalFloorPlan to an AIA-compliant DXF file.
    """
    generator = DXFGenerator()
    levels = plan.metadata.levels if plan.metadata.levels else [0]
    if len(levels) > 1:
        return generator.export_composite_dxf(plan, filepath)
    return generator.export_dxf(plan, filepath, level_index=0)
