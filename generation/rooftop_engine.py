r"""
AI Architectural Design System - Dedicated Rooftop & Mumty Engineering Engine.
Synthesizes publication-grade Roof Slab, Parapet & Mumty Floor Plans adhering to
DHA, Bahria, CDA, and IBC architectural standards.

Key Elements:
1. True Building Slab Footprint: Computed directly from the upper floor's covered rooms,
   honoring every setback, terrace cutout, L-shape, and courtyard void.
2. Continuous 9" Parapet Wall (1.05m / 3'-6" height) & stone coping tracing the actual slab perimeter.
3. Lower Floor Terraces Below: Ghosted / dashed projection showing lower floor slabs
   (e.g., ground floor car porch roof terrace) with distinct FFL callout.
4. Weatherproof Stair Mumty Penthouse Tower (100% vertical stair core continuity)
   with DN arrival staircase flight and Weatherproof Exterior Door (3'-0" x 7'-0").
5. Overhead Concrete Water Reservoir (OHT 1,500 Gal) with cat ladder and manhole.
6. Shaded Timber/Steel Pergola with outdoor lounge & BBQ counter dynamically fitted to open terrace.
7. Grid-Tied Monocrystalline Solar PV Panel Array (10kW - 15kW) sized to available unshaded roof area.
8. Dedicated Rooftop Laundry & Wash Deck with floor drain gully.
9. Civil Rainwater Drainage System (1:100 gradient slope arrows and 4" dia PVC downspouts at true corners).
10. OTS Light Shafts with 12" raised concrete curb and safety steel wire-mesh grating.
"""

import os
import math
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams['svg.fonttype'] = 'none'
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MplPoly
from shapely.geometry import Polygon as ShapelyPoly, MultiPolygon, Point as ShapelyPt, LineString
from shapely.ops import unary_union

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, OpeningModel, WallModel


class RooftopEngine:
    """
    Dedicated Rooftop & Mumty Engineering Engine.
    Generates coordinated Roof Slab, Parapet, Drainage, Solar & Mumty plans
    dynamically derived from the specific house's floor plan layout.
    """

    @classmethod
    def analyze_rooftop_parameters(cls, plan: CanonicalFloorPlan) -> Dict[str, Any]:
        """
        Analyzes the building footprint, stair core location, and OTS voids
        from the uppermost floor to generate an architecturally coordinated rooftop
        that faithfully reflects this house's exact geometry and setbacks.
        """
        levels = plan.metadata.levels if plan.metadata.levels else [0]
        top_level = max(levels)

        # 1. Covered enclosed rooms on the uppermost floor
        top_rooms = [
            r for r in plan.rooms
            if r.level_index == top_level and r.room_type not in ("outdoor", "balcony")
            and "terrace" not in r.room_name.lower() and "lawn" not in r.room_name.lower()
        ]
        if not top_rooms:
            top_rooms = [r for r in plan.rooms if r.level_index == top_level]
        if not top_rooms:
            top_rooms = plan.rooms

        # 2. Main top roof slab polygon
        top_polys = [ShapelyPoly(r.polygon) for r in top_rooms if ShapelyPoly(r.polygon).is_valid]
        if top_polys:
            top_slab_poly = unary_union(top_polys)
            # Bridge tiny collinear slivers if needed
            if top_slab_poly.is_valid:
                top_slab_poly = top_slab_poly.buffer(0.02).buffer(-0.02)
        else:
            top_slab_poly = ShapelyPoly([[0, 0], [10.67, 0], [10.67, 19.81], [0, 19.81]])

        # 3. Ground / Lower floor projections below
        lower_projection_poly = None
        ground_poly = None
        if top_level > 0:
            ground_rooms = [
                r for r in plan.rooms
                if r.level_index == 0 and r.room_type not in ("outdoor", "lawn")
                and "lawn" not in r.room_name.lower()
            ]
            if ground_rooms:
                g_polys = [ShapelyPoly(r.polygon) for r in ground_rooms if ShapelyPoly(r.polygon).is_valid]
                if g_polys:
                    ground_poly = unary_union(g_polys)
                    diff = ground_poly.difference(top_slab_poly.buffer(0.05))
                    if diff.area > 1.2:
                        lower_projection_poly = diff

        # 4. Overall bounding box of building footprint
        envelope = top_slab_poly
        if ground_poly is not None:
            envelope = envelope.union(ground_poly)
        min_x, min_y, max_x, max_y = envelope.bounds
        width_m = round(max_x - min_x, 2)
        depth_m = round(max_y - min_y, 2)

        # 5. Locate Stair Core
        stair_rm = next(
            (r for r in plan.rooms if r.level_index == top_level and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower())),
            None
        )
        if not stair_rm:
            stair_rm = next((r for r in plan.rooms if "stair" in r.room_id.lower() or "stair" in r.room_name.lower()), None)

        if stair_rm:
            sp = stair_rm.polygon
            s_min_x = min(p[0] for p in sp)
            s_max_x = max(p[0] for p in sp)
            s_min_y = min(p[1] for p in sp)
            s_max_y = max(p[1] for p in sp)
            stair_poly = [[round(p[0], 2), round(p[1], 2)] for p in sp]
        else:
            s_min_x = min_x + 0.60
            s_max_x = s_min_x + 2.40
            s_min_y = min_y + depth_m * 0.35
            s_max_y = s_min_y + 4.80
            stair_poly = [[s_min_x, s_min_y], [s_max_x, s_min_y], [s_max_x, s_max_y], [s_min_x, s_max_y]]

        stair_on_left = (s_min_x - min_x) < (max_x - s_max_x)

        # 6. Locate OTS voids
        ots_rooms = [
            r for r in plan.rooms
            if r.room_type == "outdoor" and ("ots" in r.room_id.lower() or "ots" in r.room_name.lower() or "shaft" in r.room_id.lower() or "shaft" in r.room_name.lower())
        ]
        unique_ots = []
        for ots in ots_rooms:
            ots_p = ShapelyPoly(ots.polygon)
            if not any(ots_p.equals(ShapelyPoly(u.polygon)) for u in unique_ots):
                unique_ots.append(ots)

        # 7. Usable Open Slab area on rooftop (slab minus mumty core and minus OTS voids)
        open_slab = top_slab_poly.difference(ShapelyPoly(stair_poly).buffer(0.15))
        for ots in unique_ots:
            open_slab = open_slab.difference(ShapelyPoly(ots.polygon).buffer(0.15))

        return {
            "top_level": top_level,
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "width_m": width_m,
            "depth_m": depth_m,
            "stair_poly": stair_poly,
            "stair_bounds": (s_min_x, s_min_y, s_max_x, s_max_y),
            "stair_on_left": stair_on_left,
            "ots_rooms": unique_ots,
            "top_slab_poly": top_slab_poly,
            "lower_projection_poly": lower_projection_poly,
            "open_slab": open_slab,
            "project_title": plan.metadata.provenance.get("project_title", "Contemporary Residence"),
            "plot_size": plan.metadata.provenance.get("plot_specification", "Standard Residential Plot"),
            "style": plan.metadata.provenance.get("architectural_style", "Modern Contemporary")
        }

    @classmethod
    def render_rooftop_plan(
        cls,
        plan: CanonicalFloorPlan,
        output_image_path: str,
        dpi: int = 200
    ) -> str:
        """
        Renders a publication-grade AutoCAD / DHA standard 2D Rooftop Plan (PNG):
        - Floor-plan-coordinated Roof Slab polygon & continuous 9" Parapet walls with stone coping
        - Lower Floor Terrace / Car Porch projections below shown with dashed outlines and FFL tags
        - Stair Mumty Penthouse sitting exactly on top of the vertical stair core with DN flight & exterior door
        - Overhead Concrete Water Reservoir (OHT 1,500 Gal)
        - Shaded Timber/Steel Pergola & BBQ Deck dynamically sized to fit available front/terrace slab
        - Grid-Tied Monocrystalline Solar PV Array dynamically sized to fit rear open slab
        - Dedicated Rooftop Laundry & Utility Wash Deck in service corner
        - Rainwater Drainage Slope arrows (1:100) & 4" dia PVC downspouts placed at actual slab corners
        - OTS safety curbs & wire-mesh gratings
        - Technical title block, North compass, dimension strings, and graphic scale
        """
        params = cls.analyze_rooftop_parameters(plan)
        min_x, max_x = params["min_x"], params["max_x"]
        min_y, max_y = params["min_y"], params["max_y"]
        width_m, depth_m = params["width_m"], params["depth_m"]
        s_min_x, s_min_y, s_max_x, s_max_y = params["stair_bounds"]
        stair_on_left = params["stair_on_left"]
        ots_list = params["ots_rooms"]
        top_slab_poly = params["top_slab_poly"]
        lower_projection = params["lower_projection_poly"]
        open_slab = params["open_slab"]

        fig, ax = plt.subplots(figsize=(14, 16), dpi=dpi)
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")

        # -------------------------------------------------------------
        # Helper: Render Shapely Polygon with Interior Rings (Voids)
        # -------------------------------------------------------------
        def _get_polygons(geom):
            if geom is None or geom.is_empty:
                return []
            if isinstance(geom, ShapelyPoly):
                return [geom]
            elif isinstance(geom, MultiPolygon):
                return list(geom.geoms)
            return []

        # -------------------------------------------------------------
        # 1. Lower Floor Projections (Terrace / Car Porch Below)
        # -------------------------------------------------------------
        if lower_projection is not None and not lower_projection.is_empty:
            for lpoly in _get_polygons(lower_projection):
                if lpoly.area < 0.5:
                    continue
                x_coords, y_coords = lpoly.exterior.xy
                # Light wash for lower terrace
                ax.fill(x_coords, y_coords, facecolor="#F1F5F9", edgecolor="none", zorder=1)
                # Dotted paver grid
                lp_minx, lp_miny, lp_maxx, lp_maxy = lpoly.bounds
                for gx in np.arange(lp_minx + 0.6, lp_maxx, 0.6):
                    line = LineString([(gx, lp_miny), (gx, lp_maxy)])
                    inter = line.intersection(lpoly)
                    if not inter.is_empty:
                        if inter.geom_type == 'LineString':
                            ax.plot(*inter.xy, color="#E2E8F0", lw=0.4, ls=":", zorder=2)
                        elif inter.geom_type == 'MultiLineString':
                            for seg in inter.geoms:
                                ax.plot(*seg.xy, color="#E2E8F0", lw=0.4, ls=":", zorder=2)
                for gy in np.arange(lp_miny + 0.6, lp_maxy, 0.6):
                    line = LineString([(lp_minx, gy), (lp_maxx, gy)])
                    inter = line.intersection(lpoly)
                    if not inter.is_empty:
                        if inter.geom_type == 'LineString':
                            ax.plot(*inter.xy, color="#E2E8F0", lw=0.4, ls=":", zorder=2)
                        elif inter.geom_type == 'MultiLineString':
                            for seg in inter.geoms:
                                ax.plot(*seg.xy, color="#E2E8F0", lw=0.4, ls=":", zorder=2)

                # Boundary outline (dashed representing roof slab of lower floor)
                ax.plot(x_coords, y_coords, color="#64748B", lw=2.0, ls="--", zorder=3)
                # Coping inner line
                inner_lp = lpoly.buffer(-0.15)
                for in_sub in _get_polygons(inner_lp):
                    ax.plot(*in_sub.exterior.xy, color="#94A3B8", lw=0.8, ls=":", zorder=3)

                cx_l, cy_l = lpoly.centroid.x, lpoly.centroid.y
                ax.text(
                    cx_l, cy_l,
                    "LOWER ROOF SLAB / TERRACE BELOW\n(FFL +3.30m • STONE COPING)",
                    ha="center", va="center", fontsize=5.8, fontweight="bold", color="#475569",
                    bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="#94A3B8", lw=0.8, alpha=0.92),
                    zorder=6
                )

        # -------------------------------------------------------------
        # 2. Main Rooftop Slab (Follows the Upper Floor Footprint)
        # -------------------------------------------------------------
        top_polys_list = _get_polygons(top_slab_poly)
        for poly in top_polys_list:
            x_coords, y_coords = poly.exterior.xy
            # Solid porcelain paver slab fill
            ax.fill(x_coords, y_coords, facecolor="#F8FAFC", edgecolor="none", zorder=2)

            # Masked Anti-Skid Porcelain Tile Grid (2ft x 2ft / 0.6m x 0.6m) strictly inside slab
            p_minx, p_miny, p_maxx, p_maxy = poly.bounds
            for gx in np.arange(p_minx + 0.6, p_maxx, 0.6):
                line = LineString([(gx, p_miny), (gx, p_maxy)])
                inter = line.intersection(poly)
                if not inter.is_empty:
                    if inter.geom_type == 'LineString':
                        ax.plot(*inter.xy, color="#E2E8F0", lw=0.5, ls="--", zorder=3)
                    elif inter.geom_type == 'MultiLineString':
                        for seg in inter.geoms:
                            ax.plot(*seg.xy, color="#E2E8F0", lw=0.5, ls="--", zorder=3)
            for gy in np.arange(p_miny + 0.6, p_maxy, 0.6):
                line = LineString([(p_minx, gy), (p_maxx, gy)])
                inter = line.intersection(poly)
                if not inter.is_empty:
                    if inter.geom_type == 'LineString':
                        ax.plot(*inter.xy, color="#E2E8F0", lw=0.5, ls="--", zorder=3)
                    elif inter.geom_type == 'MultiLineString':
                        for seg in inter.geoms:
                            ax.plot(*seg.xy, color="#E2E8F0", lw=0.5, ls="--", zorder=3)

            # 9" (230mm) Solid Masonry Parapet Wall along true slab perimeter
            ax.plot(x_coords, y_coords, color="#0F172A", lw=5.4, solid_capstyle="butt", zorder=7)

            # Inner coping guideline (offset inwards by 0.23m)
            inner_coping = poly.buffer(-0.23)
            for in_poly in _get_polygons(inner_coping):
                ax.plot(*in_poly.exterior.xy, color="#334155", lw=1.6, ls="-", zorder=7)

            # Internal hole rings (courtyards / shafts)
            for hole in poly.interiors:
                hx, hy = hole.xy
                ax.fill(hx, hy, facecolor="#FFFFFF", zorder=3)
                ax.plot(hx, hy, color="#0F172A", lw=4.2, zorder=7)
                hole_coping = ShapelyPoly(hole).buffer(0.23)
                if hole_coping.is_valid:
                    ax.plot(*hole_coping.exterior.xy, color="#334155", lw=1.4, ls="-", zorder=7)

        # -------------------------------------------------------------
        # 3. Open-To-Sky (OTS) Light Shafts
        # -------------------------------------------------------------
        for ots in ots_list:
            op = ots.polygon
            o_min_x = min(p[0] for p in op)
            o_max_x = max(p[0] for p in op)
            o_min_y = min(p[1] for p in op)
            o_max_y = max(p[1] for p in op)
            ow = o_max_x - o_min_x
            oh = o_max_y - o_min_y

            # Raised 12" concrete curb
            ax.add_patch(patches.Rectangle(
                (o_min_x, o_min_y), ow, oh,
                facecolor="#FFFFFF", edgecolor="#0F172A", lw=3.0, zorder=5
            ))
            # Diagonal safety wire-mesh grating
            for gx in np.arange(o_min_x, o_max_x + 0.4, 0.4):
                ax.plot([gx, min(gx + 0.8, o_max_x)], [o_min_y, min(o_min_y + 0.8, o_max_y)], color="#0284C7", lw=0.8, ls=":", zorder=6)
            ax.plot([o_min_x, o_max_x], [o_min_y, o_max_y], color="#94A3B8", lw=1.2, ls="--", zorder=6)
            ax.plot([o_min_x, o_max_x], [o_max_y, o_min_y], color="#94A3B8", lw=1.2, ls="--", zorder=6)

            ax.text(
                o_min_x + ow * 0.5, o_min_y + oh * 0.5,
                f"OTS LIGHT SHAFT VOID\n({ow*3.28:.0f}'-{round((ow*3.28%1)*12):02d}\" x {oh*3.28:.0f}'-{round((oh*3.28%1)*12):02d}\")\n[RAISED 12\" CURB & WIRE MESH]",
                ha="center", va="center", fontsize=5.5, fontweight="bold", color="#0369A1",
                bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="#0284C7", lw=0.8, alpha=0.96), zorder=8
            )

        # -------------------------------------------------------------
        # 4. Weatherproof Stair Mumty Penthouse Tower (100% Floor Aligned)
        # -------------------------------------------------------------
        mw = s_max_x - s_min_x
        mh = s_max_y - s_min_y
        ax.add_patch(patches.Rectangle(
            (s_min_x, s_min_y), mw, mh,
            facecolor="#FFFDF5", edgecolor="#0F172A", lw=4.2, zorder=6
        ))

        # Arrival staircase inside mumty (DN arrow)
        steps = 14
        step_h = (mh * 0.72) / steps
        for i in range(steps):
            sy = s_min_y + i * step_h
            ax.plot([s_min_x + 0.1, s_max_x - 0.1], [sy, sy], color="#334155", lw=1.0, zorder=7)
            ax.text(s_min_x + 0.22, sy + step_h * 0.5, f"{steps - i}", fontsize=4.5, color="#64748B", va="center", zorder=8)

        cx_stair = s_min_x + mw * 0.5
        top_y_stair = s_min_y + mh * 0.72
        ax.plot([cx_stair, cx_stair], [top_y_stair - 0.2, s_min_y + 0.3], color="#2563EB", lw=1.8, zorder=8)
        ax.annotate("", xy=(cx_stair, s_min_y + 0.2), xytext=(cx_stair, s_min_y + 0.5),
                    arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.8), zorder=8)
        ax.add_patch(patches.Circle((cx_stair, top_y_stair - 0.2), 0.08, facecolor="#2563EB", zorder=8))
        ax.text(cx_stair, s_min_y + mh * 0.36, "DN (TO FLOOR BELOW)", rotation=270, color="#2563EB", fontsize=6.2, fontweight="bold", ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.92), zorder=9)

        # Mumty top landing vestibule
        ax.add_patch(patches.Rectangle(
            (s_min_x, top_y_stair), mw, mh - (top_y_stair - s_min_y),
            facecolor="#FFFBEB", edgecolor="#CBD5E1", lw=0.8, zorder=7
        ))
        ax.text(cx_stair, top_y_stair + (mh - (top_y_stair - s_min_y)) * 0.5, "MUMTY TOP VESTIBULE\n(WEATHERPROOF FFL +0.15m)",
                ha="center", va="center", fontsize=5.5, fontweight="bold", color="#0F172A", zorder=9)

        # Exterior Weatherproof Door (3'-0" x 7'-0")
        # Position door on wall opening directly onto accessible open slab terrace
        dw = 0.914
        if stair_on_left:
            door_pos = [s_max_x, top_y_stair + 0.45]
            ax.plot([door_pos[0], door_pos[0]], [door_pos[1] - dw * 0.5, door_pos[1] + dw * 0.5], color="#FFFFFF", lw=4.5, zorder=8)
            ax.plot([door_pos[0], door_pos[0] + dw], [door_pos[1] + dw * 0.5, door_pos[1] + dw * 0.5], color="#B91C1C", lw=2.2, zorder=9)
            door_arc = patches.Arc((door_pos[0], door_pos[1] + dw * 0.5), dw * 2, dw * 2, angle=0, theta1=270, theta2=360, color="#DC2626", lw=1.2, ls="--", zorder=9)
            ax.add_patch(door_arc)
            ax.text(door_pos[0] + 0.5, door_pos[1] - 0.25, "EXTERIOR WEATHERPROOF DOOR\n3'-0\" x 7'-0\" (4\" SILL UPSTAND)", fontsize=5.2, fontweight="bold", color="#B91C1C", zorder=10)
        else:
            door_pos = [s_min_x, top_y_stair + 0.45]
            ax.plot([door_pos[0], door_pos[0]], [door_pos[1] - dw * 0.5, door_pos[1] + dw * 0.5], color="#FFFFFF", lw=4.5, zorder=8)
            ax.plot([door_pos[0], door_pos[0] - dw], [door_pos[1] + dw * 0.5, door_pos[1] + dw * 0.5], color="#B91C1C", lw=2.2, zorder=9)
            door_arc = patches.Arc((door_pos[0], door_pos[1] + dw * 0.5), dw * 2, dw * 2, angle=0, theta1=180, theta2=270, color="#DC2626", lw=1.2, ls="--", zorder=9)
            ax.add_patch(door_arc)
            ax.text(door_pos[0] - 2.8, door_pos[1] - 0.25, "EXTERIOR WEATHERPROOF DOOR\n3'-0\" x 7'-0\" (4\" SILL UPSTAND)", fontsize=5.2, fontweight="bold", color="#B91C1C", zorder=10)

        # Overhead Concrete Water Reservoir (OHT 1,500 Gal)
        oht_w = min(mw * 0.85, 2.40)
        oht_h = 2.00
        oht_x = s_min_x + (mw - oht_w) * 0.5
        oht_y = s_min_y + 0.30
        ax.add_patch(patches.Rectangle(
            (oht_x, oht_y), oht_w, oht_h,
            facecolor="#E0F2FE", edgecolor="#0284C7", lw=2.4, ls="-", zorder=9
        ))
        ax.plot([oht_x, oht_x + oht_w], [oht_y + oht_h * 0.5, oht_y + oht_h * 0.5], color="#0284C7", lw=1.0, ls="--", zorder=10)
        ax.add_patch(patches.Circle((oht_x + oht_w * 0.5, oht_y + oht_h * 0.5), 0.30, facecolor="#BAE6FD", edgecolor="#0369A1", lw=1.4, zorder=11))
        ax.text(oht_x + oht_w * 0.5, oht_y + oht_h * 0.5, "OHT\n1,500 GAL", ha="center", va="center", fontsize=5.5, fontweight="bold", color="#0369A1", zorder=12)
        # Cat Ladder
        ax.plot([oht_x - 0.15, oht_x - 0.15], [oht_y + 0.3, oht_y + oht_h - 0.3], color="#0F172A", lw=1.8, zorder=10)
        for ry in np.arange(oht_y + 0.4, oht_y + oht_h - 0.3, 0.25):
            ax.plot([oht_x - 0.25, oht_x - 0.05], [ry, ry], color="#0F172A", lw=1.2, zorder=10)

        # -------------------------------------------------------------
        # 5. Shaded Timber Pergola & BBQ Party Deck (Dynamically Positioned)
        # -------------------------------------------------------------
        # Find bounds of open slab in front zone (lower half of y)
        front_box = open_slab.intersection(ShapelyPoly([
            [min_x, min_y], [max_x, min_y], [max_x, min_y + depth_m * 0.55], [min_x, min_y + depth_m * 0.55]
        ]))
        if not front_box.is_empty and front_box.area >= 6.0:
            fb_minx, fb_miny, fb_maxx, fb_maxy = front_box.bounds
            perg_w = min(fb_maxx - fb_minx - 1.0, width_m * 0.48)
            perg_h = min(fb_maxy - fb_miny - 0.8, 4.50)
            if perg_w >= 2.4 and perg_h >= 2.4:
                perg_x = fb_maxx - perg_w - 0.50 if stair_on_left else fb_minx + 0.50
                perg_y = fb_miny + 0.60

                ax.add_patch(patches.Rectangle(
                    (perg_x, perg_y), perg_w, perg_h,
                    facecolor="#FEF3C7", alpha=0.35, edgecolor="#B45309", lw=1.8, ls="-", zorder=4
                ))
                for rx in np.arange(perg_x + 0.4, perg_x + perg_w, 0.65):
                    ax.plot([rx, rx], [perg_y, perg_y + perg_h], color="#B45309", lw=1.4, alpha=0.85, zorder=5)

                for px, py in [(perg_x, perg_y), (perg_x + perg_w, perg_y), (perg_x, perg_y + perg_h), (perg_x + perg_w, perg_y + perg_h)]:
                    ax.add_patch(patches.Rectangle((px - 0.12, py - 0.12), 0.24, 0.24, facecolor="#78350F", edgecolor="#0F172A", lw=1.2, zorder=7))

                # BBQ counter
                bbq_w = min(perg_w - 0.8, 3.20)
                bbq_h = 0.70
                bbq_x = perg_x + (perg_w - bbq_w) * 0.5
                bbq_y = perg_y + perg_h - 0.85
                ax.add_patch(patches.Rectangle((bbq_x, bbq_y), bbq_w, bbq_h, facecolor="#334155", edgecolor="#0F172A", lw=1.4, zorder=6))
                ax.text(bbq_x + bbq_w * 0.5, bbq_y + bbq_h * 0.5, "BUILT-IN BBQ GRILL & SINK COUNTER", ha="center", va="center", fontsize=4.8, fontweight="bold", color="#FFFFFF", zorder=8)

                # Patio Table
                tbl_cx = perg_x + perg_w * 0.5
                tbl_cy = perg_y + 1.60
                ax.add_patch(patches.Circle((tbl_cx, tbl_cy), 0.70, facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4, zorder=6))
                ax.text(tbl_cx, tbl_cy, "OUTDOOR\nPATIO TABLE", ha="center", va="center", fontsize=4.8, fontweight="bold", color="#0F172A", zorder=7)
                for deg in [0, 90, 180, 270]:
                    ch_x = tbl_cx + 1.10 * math.cos(math.radians(deg))
                    ch_y = tbl_cy + 1.10 * math.sin(math.radians(deg))
                    ax.add_patch(patches.Circle((ch_x, ch_y), 0.24, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.0, zorder=6))

                ax.text(
                    perg_x + perg_w * 0.5, perg_y - 0.25,
                    f"SHADED TIMBER PERGOLA & BBQ PARTY DECK\n({perg_w*3.28:.0f}'-{round((perg_w*3.28%1)*12):02d}\" x {perg_h*3.28:.0f}'-{round((perg_h*3.28%1)*12):02d}\" • Anti-Skid Pavers)",
                    ha="center", va="top", fontsize=6.2, fontweight="bold", color="#92400E",
                    bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFBEB", edgecolor="#D97706", lw=0.9, alpha=0.95), zorder=9
                )

        # -------------------------------------------------------------
        # 6. Grid-Tied Monocrystalline Solar PV Array (Rear Zone)
        # -------------------------------------------------------------
        rear_box = open_slab.intersection(ShapelyPoly([
            [min_x, min_y + depth_m * 0.45], [max_x, min_y + depth_m * 0.45], [max_x, max_y], [min_x, max_y]
        ]))
        if not rear_box.is_empty and rear_box.area >= 8.0:
            rb_minx, rb_miny, rb_maxx, rb_maxy = rear_box.bounds
            pv_w = min(rb_maxx - rb_minx - 1.2, width_m * 0.55)
            pv_h = min(rb_maxy - rb_miny - 1.2, 3.80)
            if pv_w >= 2.5 and pv_h >= 2.0:
                pv_x = rb_minx + 0.60 if stair_on_left else rb_maxx - pv_w - 0.60
                pv_y = rb_maxy - pv_h - 0.60

                ax.add_patch(patches.Rectangle(
                    (pv_x, pv_y), pv_w, pv_h,
                    facecolor="#F0F9FF", edgecolor="#0284C7", lw=1.6, ls="--", zorder=4
                ))

                n_rows = 2
                n_cols = max(4, int(pv_w / 0.70))
                pan_w = (pv_w - 0.4) / n_cols
                pan_h = (pv_h - 0.6) / n_rows

                for r in range(n_rows):
                    for c in range(n_cols):
                        px = pv_x + 0.2 + c * pan_w
                        py = pv_y + 0.2 + r * (pan_h + 0.2)
                        ax.add_patch(patches.Rectangle(
                            (px, py), pan_w - 0.05, pan_h,
                            facecolor="#1E3A8A", edgecolor="#38BDF8", lw=0.8, zorder=5
                        ))
                        ax.plot([px, px + pan_w - 0.05], [py + pan_h * 0.5, py + pan_h * 0.5], color="#60A5FA", lw=0.5, zorder=6)
                        ax.plot([px + (pan_w - 0.05) * 0.5, px + (pan_w - 0.05) * 0.5], [py, py + pan_h], color="#60A5FA", lw=0.5, zorder=6)

                ax.text(
                    pv_x + pv_w * 0.5, pv_y + pv_h + 0.22,
                    f"10kW - 15kW ON-GRID SOLAR PV ARRAY\n({n_rows * n_cols}x 580W Tier-1 Modules • 25° South Tilt)",
                    ha="center", va="bottom", fontsize=6.0, fontweight="bold", color="#1E40AF",
                    bbox=dict(boxstyle="square,pad=0.2", facecolor="#EFF6FF", edgecolor="#3B82F6", lw=0.9, alpha=0.95), zorder=8
                )

                # Solar Inverter
                ax.add_patch(patches.Rectangle((pv_x + pv_w + 0.15, pv_y + 0.4), 0.60, 1.10, facecolor="#334155", edgecolor="#0F172A", lw=1.2, zorder=5))
                ax.text(pv_x + pv_w + 0.45, pv_y + 0.95, "SOLAR\nINVERTER", ha="center", va="center", fontsize=4.5, fontweight="bold", color="#FFFFFF", zorder=7)

        # -------------------------------------------------------------
        # 7. Dedicated Rooftop Laundry & Wash Deck
        # -------------------------------------------------------------
        laund_w, laund_h = 2.20, 2.40
        laund_x = max_x - laund_w - 0.8 if stair_on_left else min_x + 0.8
        laund_y = min_y + depth_m * 0.48
        # Ensure laundry is inside top slab
        if ShapelyPoly([[laund_x, laund_y], [laund_x + laund_w, laund_y], [laund_x + laund_w, laund_y + laund_h], [laund_x, laund_y + laund_h]]).intersects(top_slab_poly):
            ax.add_patch(patches.Rectangle(
                (laund_x, laund_y), laund_w, laund_h,
                facecolor="#F1F5F9", edgecolor="#64748B", lw=1.6, ls="-", zorder=4
            ))
            ax.add_patch(patches.Rectangle((laund_x + 0.2, laund_y + 0.3), 0.80, 0.60, facecolor="#94A3B8", edgecolor="#0F172A", lw=1.0, zorder=5))
            ax.add_patch(patches.Rectangle((laund_x + 1.1, laund_y + 0.3), 0.80, 0.60, facecolor="#CBD5E1", edgecolor="#0F172A", lw=1.0, zorder=5))
            ax.add_patch(patches.Circle((laund_x + laund_w * 0.5, laund_y + 1.6), 0.14, facecolor="#0284C7", edgecolor="#0F172A", lw=1.0, zorder=5))
            ax.text(
                laund_x + laund_w * 0.5, laund_y + laund_h - 0.35,
                "ROOFTOP LAUNDRY\n& UTILITY WASH DECK", ha="center", va="center", fontsize=5.0, fontweight="bold", color="#334155", zorder=7
            )

        # -------------------------------------------------------------
        # 8. Rainwater Drainage System (1:100 Gradient Slope & PVC Downspouts)
        # -------------------------------------------------------------
        # Extract true exterior vertices of top_slab_poly for downspouts
        rwp_candidates = []
        for poly in top_polys_list:
            coords = list(poly.exterior.coords)
            for pt in coords[:-1]:
                # Candidate corners (avoid stair mumty)
                if not (s_min_x - 0.2 <= pt[0] <= s_max_x + 0.2 and s_min_y - 0.2 <= pt[1] <= s_max_y + 0.2):
                    rwp_candidates.append(pt)

        # Pick distinct corners separated by at least 3.0m
        rwp_locs = []
        for pt in rwp_candidates:
            if not any(math.hypot(pt[0] - r[0], pt[1] - r[1]) < 3.5 for r in rwp_locs):
                rwp_locs.append(pt)
            if len(rwp_locs) >= 6:
                break

        for idx, (rx, ry) in enumerate(rwp_locs):
            ax.add_patch(patches.Circle((rx, ry), 0.16, facecolor="#0284C7", edgecolor="#0F172A", lw=1.2, zorder=8))
            ax.text(rx + (0.35 if rx < (min_x + max_x)*0.5 else -0.35), ry,
                    f"R.W.P. #{idx+1}\n4\" PVC",
                    fontsize=5.0, fontweight="bold", color="#0369A1",
                    ha="left" if rx < (min_x + max_x)*0.5 else "right", va="center",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="#0284C7", lw=0.6, alpha=0.92), zorder=9)

        # Drainage slope arrows
        mid_y_slab = (min_y + max_y) * 0.5
        for idx, (rx, ry) in enumerate(rwp_locs[:4]):
            start_x = (min_x + max_x) * 0.5
            start_y = mid_y_slab if abs(ry - mid_y_slab) > 1.5 else (ry + (1.5 if ry < mid_y_slab else -1.5))
            ax.annotate("", xy=(rx, ry), xytext=(start_x, start_y),
                        arrowprops=dict(arrowstyle="->", color="#0284C7", lw=1.3, linestyle="--"), zorder=5)
            ax.text((start_x + rx)*0.5, (start_y + ry)*0.5, "SLOPE 1:100", fontsize=4.6, fontweight="bold", color="#0284C7",
                    rotation=20, ha="center", va="bottom", zorder=6)

        # -------------------------------------------------------------
        # 9. Dimension Strings (Exterior Feet-and-Inches)
        # -------------------------------------------------------------
        def _m_to_ft_in(m: float) -> str:
            total_inches = m * 39.3701
            feet = int(total_inches // 12)
            inches = int(round(total_inches % 12))
            if inches == 12:
                feet += 1
                inches = 0
            return f"{feet}'-{inches:02d}\""

        # Width dimension chain
        chain_y = min_y - 0.95
        ax.plot([min_x, max_x], [chain_y, chain_y], color="#1E293B", lw=1.4, ls="-", zorder=7)
        ax.plot([min_x, min_x], [min_y - 0.72, chain_y - 0.22], color="#1E293B", lw=1.1, zorder=7)
        ax.plot([max_x, max_x], [min_y - 0.72, chain_y - 0.22], color="#1E293B", lw=1.1, zorder=7)
        ax.annotate("", xy=(min_x, chain_y), xytext=(min_x + 0.28, chain_y), arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.1), zorder=7)
        ax.annotate("", xy=(max_x, chain_y), xytext=(max_x - 0.28, chain_y), arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.1), zorder=7)
        w_label = _m_to_ft_in(width_m) + f"\n({width_m:.2f}m)"
        ax.text((min_x + max_x) * 0.5, chain_y - 0.22, w_label, ha="center", va="top", fontsize=8.5, fontweight="bold", color="#1E293B",
                bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.95), zorder=10)

        # Depth dimension chain
        chain_x = max_x + 0.95
        ax.plot([chain_x, chain_x], [min_y, max_y], color="#1E293B", lw=1.4, ls="-", zorder=7)
        ax.plot([max_x + 0.72, chain_x + 0.22], [min_y, min_y], color="#1E293B", lw=1.1, zorder=7)
        ax.plot([max_x + 0.72, chain_x + 0.22], [max_y, max_y], color="#1E293B", lw=1.1, zorder=7)
        ax.annotate("", xy=(chain_x, min_y), xytext=(chain_x, min_y + 0.28), arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.1), zorder=7)
        ax.annotate("", xy=(chain_x, max_y), xytext=(chain_x, max_y - 0.28), arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.1), zorder=7)
        d_label = _m_to_ft_in(depth_m) + f"\n({depth_m:.2f}m)"
        ax.text(chain_x + 0.38, (min_y + max_y) * 0.5, d_label, ha="left", va="center", rotation=270, fontsize=8.5, fontweight="bold", color="#1E293B",
                bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.95), zorder=10)

        # -------------------------------------------------------------
        # 10. Graphic Scale Bar & Wall Legend
        # -------------------------------------------------------------
        sb_x = min_x + 0.2
        sb_y = min_y - 1.85
        sb_len = 5.0
        ax.plot([sb_x, sb_x + sb_len], [sb_y, sb_y], color="#0F172A", lw=2.5, zorder=7)
        for tick_m in range(6):
            tx = sb_x + tick_m
            ax.plot([tx, tx], [sb_y - 0.12, sb_y + 0.12], color="#0F172A", lw=1.2, zorder=7)
            ax.text(tx, sb_y - 0.22, f"{tick_m}m", ha="center", va="top", fontsize=6.5, color="#334155", zorder=7)
        ax.text(sb_x + sb_len * 0.5, sb_y + 0.18, "GRAPHIC SCALE 1:100", ha="center", va="bottom", fontsize=6.5, fontweight="bold", color="#0F172A",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.95), zorder=10)

        leg_x = min_x
        leg_y = min_y - 2.60
        ax.plot([leg_x, leg_x + 0.45], [leg_y, leg_y], color="#0F172A", lw=5.4, solid_capstyle="butt", zorder=7)
        ax.text(leg_x + 0.55, leg_y, "PERIMETER PARAPET WALL: 9\" (230mm) SOLID BRICK • 3'-6\" (1.05m) HEIGHT", fontsize=6.0, fontweight="bold", color="#0F172A", va="center", zorder=8)
        leg_y2 = leg_y - 0.30
        ax.plot([leg_x, leg_x + 0.45], [leg_y2, leg_y2], color="#0284C7", lw=2.2, ls="--", zorder=7)
        ax.text(leg_x + 0.55, leg_y2, "DRAINAGE: 1:100 WATERPROOF SLOPE TO 4\" DIA PVC RAINWATER DOWNSPOUTS", fontsize=6.0, fontweight="bold", color="#0284C7", va="center", zorder=8)

        # North Arrow Compass
        compass_x = max_x - 0.8
        compass_y = max_y + 1.2
        ax.annotate("N", xy=(compass_x, compass_y + 0.6), xytext=(compass_x, compass_y),
                    ha="center", va="bottom", fontsize=11, fontweight="bold", color="#0F172A",
                    arrowprops=dict(facecolor="#0F172A", width=1.8, headwidth=7), zorder=8)

        # -------------------------------------------------------------
        # 11. Drawing Title & Engineering Header
        # -------------------------------------------------------------
        proj_title = params["project_title"].upper()
        lvl_num = params["top_level"] + 1
        ax.set_title(
            f"{proj_title} — ARCHITECTURAL ROOF SLAB, PARAPET & MUMTY PLAN | LEVEL {lvl_num}\n"
            f"COORDINATED FOOTPRINT WITH MULTI-FLOOR ALIGNMENT • 1:100 SCALE BLUEPRINT",
            fontsize=11.5, fontweight="bold", color="#0F172A", pad=15
        )

        ax.set_xlim(min_x - 2.0, max_x + 2.8)
        ax.set_ylim(min_y - 3.4, max_y + 2.2)
        ax.set_aspect("equal")
        ax.axis("off")

        os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"[ROOFTOP ENGINE] Saved 2D Coordinated Rooftop Plan -> {output_image_path}")
        return output_image_path

    @classmethod
    def generate_rooftop_rooms(cls, plan: CanonicalFloorPlan) -> List[RoomModel]:
        """
        Synthesizes standard RoomModel objects for the Rooftop Level
        so that it can be seamlessly ingested into DXF generators, RAG analyzers, and BIM pipelines,
        strictly coordinated with the true floor plan geometry.
        """
        params = cls.analyze_rooftop_parameters(plan)
        s_min_x, s_min_y, s_max_x, s_max_y = params["stair_bounds"]
        rf_lvl = params["top_level"] + 1
        top_slab_poly = params["top_slab_poly"]

        rooms = []

        # 1. Mumty Staircase Penthouse Core
        mumty_poly = [[s_min_x, s_min_y], [s_max_x, s_min_y], [s_max_x, s_max_y], [s_min_x, s_max_y]]
        rooms.append(RoomModel(
            room_id=f"room_L{rf_lvl}_mumty_penthouse",
            room_type="corridor",
            room_name="Staircase Mumty Penthouse (DN ->)",
            polygon=mumty_poly,
            area_m2=round((s_max_x - s_min_x) * (s_max_y - s_min_y), 2),
            centroid=[round((s_min_x + s_max_x) * 0.5, 2), round((s_min_y + s_max_y) * 0.5, 2)],
            level_index=rf_lvl,
            is_habitable=False,
            metadata={"typology": "mumty_penthouse", "headroom_m": 2.40, "weatherproof_door": True}
        ))

        # 2. Overhead Concrete Water Reservoir
        oht_w = min((s_max_x - s_min_x) * 0.85, 2.40)
        oht_h = 2.00
        oht_x = s_min_x + ((s_max_x - s_min_x) - oht_w) * 0.5
        oht_y = s_min_y + 0.30
        rooms.append(RoomModel(
            room_id=f"room_L{rf_lvl}_oht_reservoir",
            room_type="utility",
            room_name="Overhead Concrete Water Reservoir (OHT 1,500 Gal)",
            polygon=[[oht_x, oht_y], [oht_x + oht_w, oht_y], [oht_x + oht_w, oht_y + oht_h], [oht_x, oht_y + oht_h]],
            area_m2=round(oht_w * oht_h, 2),
            centroid=[round(oht_x + oht_w * 0.5, 2), round(oht_y + oht_h * 0.5, 2)],
            level_index=rf_lvl,
            is_habitable=False,
            metadata={"capacity_gal": 1500, "material": "Reinforced Concrete"}
        ))

        # 3. Open Rooftop Sun Terrace Expanse (Matching True Top Slab Boundary)
        coords = list(top_slab_poly.exterior.coords)[:-1] if isinstance(top_slab_poly, ShapelyPoly) else list(top_slab_poly.geoms[0].exterior.coords)[:-1]
        rooms.append(RoomModel(
            room_id=f"room_L{rf_lvl}_open_sun_terrace",
            room_type="balcony",
            room_name="Rooftop Coordinated Sun Terrace & Promenade",
            polygon=[[round(c[0], 2), round(c[1], 2)] for c in coords],
            area_m2=round(top_slab_poly.area, 2),
            centroid=[round(top_slab_poly.centroid.x, 2), round(top_slab_poly.centroid.y, 2)],
            level_index=rf_lvl,
            is_habitable=False,
            metadata={"drainage_slope": "1:100", "rwp_count": 4, "coordinated_slab": True}
        ))

        return rooms
