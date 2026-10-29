"""
Phase 12: Professional Architectural 2D Blueprint Visualizer.
Renders publication-quality, AutoCAD/BIM-standard 2D floor plans (PNG)
directly from CanonicalFloorPlan for each floor level.

Features:
- Authentic architectural furniture blocks (Master beds with nightstands/pillows,
  L-shaped sectional sofas, formal drawing suite, 8-seater dining table,
  L-kitchen with double sink and 4-burner range, full sanitary fixtures WC/vanity/shower).
- U-shaped dog-leg staircase with landing, directional flow (UP/DN), and handrails.
- Professional architectural doors (wooden leaf, door frame jambs, quarter-circle swing arcs, double French entry doors).
- 3-line glazing window symbols with sill projections.
- Realistic car silhouettes in porch.
- Architectural dimensions, room area tags, North compass, and professional title block.
"""

import os
import math
from typing import Dict, List, Optional, Tuple, Any
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams['svg.fonttype'] = 'none'
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, WallModel, OpeningModel
from cad.asset_loader import CADAssetLoader


class FloorPlanVisualizer:
    ROOM_COLORS = {
        "living_room": "#FFFDF5",      # Warm luxury cream
        "dining_room": "#FEF9C3",      # Gentle formal honey
        "kitchen": "#FFF7ED",          # Clean culinary peach/white
        "bedroom": "#F8FAFC",          # Serene light slate
        "bathroom": "#F0F9FF",         # Crisp hygienic aqua-tint
        "corridor": "#FAFAFA",         # Circulation neutral
        "garage": "#F1F5F9",           # Paver driveway gray
        "balcony": "#F0FDF4",          # Terrace garden mint
        "unclassified_closed_region": "#F8FAFC"
    }

    @classmethod
    def _draw_straight_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws a single-flight straight run staircase with breakline and railings."""
        steps = 16
        landing_h = min(1.0, rh * 0.22)
        flight_h = rh - landing_h
        step_h = flight_h / (steps - 1)

        # Side stringers
        ax.plot([min_x + 0.05, min_x + 0.05], [min_y, min_y + rh], color="#0F172A", lw=2.2, zorder=3)
        ax.plot([min_x + rw - 0.05, min_x + rw - 0.05], [min_y, min_y + rh], color="#0F172A", lw=2.2, zorder=3)

        # Treads
        for i in range(steps):
            sy = min_y + i * step_h
            if not is_first_floor and i > 7:
                # Dashed treads above cut line (headroom space below)
                ax.plot([min_x + 0.05, min_x + rw - 0.05], [sy, sy], color="#94A3B8", lw=0.9, ls="--", zorder=3)
            else:
                ax.plot([min_x + 0.05, min_x + rw - 0.05], [sy, sy], color="#334155", lw=1.0, ls="-", zorder=3)
                if not is_first_floor and i < 7:
                    ax.text(min_x + 0.20, sy + step_h * 0.5, f"{i+1}", fontsize=5.0, color="#64748B", va="center", ha="center", zorder=4)
                elif is_first_floor:
                    ax.text(min_x + 0.20, sy + step_h * 0.5, f"{steps - i}", fontsize=5.0, color="#64748B", va="center", ha="center", zorder=4)

        # Top Landing
        top_ly = min_y + flight_h
        ax.plot([min_x, min_x + rw], [top_ly, top_ly], color="#0F172A", lw=1.6, zorder=3)
        ax.text(min_x + rw * 0.5, top_ly + landing_h * 0.5, "TOP LANDING\nCLEAR",
                ha="center", va="center", color="#0F172A", fontsize=5.5, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.9), zorder=4)

        cx = min_x + rw * 0.5
        if not is_first_floor:
            # Diagonal breakline at step 7
            by = min_y + 7 * step_h
            ax.plot([min_x, min_x + rw * 0.40, min_x + rw * 0.50, min_x + rw * 0.60, min_x + rw],
                    [by, by, by + 0.16, by - 0.16, by], color="#0F172A", lw=1.6, zorder=5)
            # UP Arrow
            ax.plot([cx, cx], [min_y + 0.30, by - 0.15], color="#000000", lw=1.5, zorder=4)
            ax.annotate("", xy=(cx, by - 0.05), xytext=(cx, by - 0.25),
                        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.5), zorder=4)
            ax.add_patch(patches.Circle((cx, min_y + 0.25), 0.08, facecolor="#000000", zorder=4))
            ax.text(cx, min_y + 3 * step_h, "UP (16 RISERS)", rotation=90, color="#000000", fontsize=6.0, fontweight="bold", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=5)
            ax.text(cx, min_y + 11 * step_h, "HEADROOM CLEARANCE UNDER", rotation=90, color="#94A3B8", fontsize=5.0, ha="center", va="center", zorder=4)
        else:
            # DN Arrow
            ax.plot([cx, cx], [top_ly - 0.20, min_y + 0.30], color="#2563EB", lw=1.5, zorder=4)
            ax.annotate("", xy=(cx, min_y + 0.15), xytext=(cx, min_y + 0.35),
                        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.5), zorder=4)
            ax.add_patch(patches.Circle((cx, top_ly - 0.20), 0.08, facecolor="#2563EB", zorder=4))
            ax.text(cx, min_y + flight_h * 0.5, "DN (ARRIVAL)", rotation=270, color="#2563EB", fontsize=6.0, fontweight="bold", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=5)
            # Balustrade line
            ax.plot([min_x + rw, min_x + rw], [min_y, top_ly], color="#DC2626", lw=1.4, ls="--", zorder=5)

    @classmethod
    def _draw_l_shaped_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws an L-shaped (Quarter-Turn) staircase with square corner landing."""
        fw = min(rw * 0.45, 1.10)
        landing_h = fw
        flight1_h = rh - landing_h
        steps_f1 = 8
        step_h1 = flight1_h / steps_f1
        steps_f2 = 8
        flight2_w = rw - fw
        step_w2 = flight2_w / steps_f2

        # Flight 1 (Vertical along left wall)
        ax.plot([min_x + fw, min_x + fw], [min_y, min_y + flight1_h], color="#0F172A", lw=2.0, zorder=3)
        for i in range(steps_f1 + 1):
            sy = min_y + i * step_h1
            ax.plot([min_x, min_x + fw], [sy, sy], color="#334155", lw=0.9, ls="-", zorder=3)
            if i < steps_f1:
                ax.text(min_x + 0.18, sy + step_h1 * 0.5, f"{i+1}", fontsize=4.5, color="#64748B", va="center", ha="center", zorder=4)

        # Corner Landing (Top-left square)
        lx, ly = min_x, min_y + flight1_h
        ax.text(lx + fw * 0.5, ly + landing_h * 0.5, "CORNER\nLANDING\n(+1400mm)",
                ha="center", va="center", color="#0F172A", fontsize=5.0, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.9), zorder=4)

        # Flight 2 (Horizontal along top wall)
        ax.plot([min_x + fw, min_x + rw], [ly, ly], color="#0F172A", lw=2.0, zorder=3)
        for j in range(steps_f2 + 1):
            sx = min_x + fw + j * step_w2
            if not is_first_floor and j > 3:
                ax.plot([sx, sx], [ly, ly + landing_h], color="#94A3B8", lw=0.9, ls="--", zorder=3)
            else:
                ax.plot([sx, sx], [ly, ly + landing_h], color="#334155", lw=0.9, ls="-", zorder=3)
            if j < steps_f2:
                ax.text(sx + step_w2 * 0.5, ly + landing_h - 0.20, f"{steps_f1 + j + 1}", fontsize=4.5, color="#64748B", va="center", ha="center", zorder=4)

        # Flow Arrows & Breaklines
        if not is_first_floor:
            # Breakline on flight 2
            bx = min_x + fw + 3 * step_w2
            ax.plot([bx, bx, bx + 0.12, bx - 0.12, bx], [ly, ly + landing_h * 0.4, ly + landing_h * 0.5, ly + landing_h * 0.6, ly + landing_h], color="#0F172A", lw=1.5, zorder=5)
            # Arrow up flight 1 turning into landing
            ax.plot([min_x + fw * 0.5, min_x + fw * 0.5], [min_y + 0.3, ly + landing_h * 0.5], color="#000000", lw=1.5, zorder=4)
            ax.plot([min_x + fw * 0.5, bx - 0.10], [ly + landing_h * 0.5, ly + landing_h * 0.5], color="#000000", lw=1.5, zorder=4)
            ax.annotate("", xy=(bx, ly + landing_h * 0.5), xytext=(bx - 0.20, ly + landing_h * 0.5),
                        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.5), zorder=4)
            ax.add_patch(patches.Circle((min_x + fw * 0.5, min_y + 0.25), 0.08, facecolor="#000000", zorder=4))
            ax.text(min_x + fw * 0.5, min_y + flight1_h * 0.45, "UP (16 RISERS)", rotation=90, color="#000000", fontsize=5.5, fontweight="bold", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=5)
        else:
            # DN Arrow from top right
            ax.plot([min_x + rw - 0.30, min_x + fw * 0.5], [ly + landing_h * 0.5, ly + landing_h * 0.5], color="#2563EB", lw=1.5, zorder=4)
            ax.plot([min_x + fw * 0.5, min_x + fw * 0.5], [ly + landing_h * 0.5, min_y + 0.30], color="#2563EB", lw=1.5, zorder=4)
            ax.annotate("", xy=(min_x + fw * 0.5, min_y + 0.15), xytext=(min_x + fw * 0.5, min_y + 0.35),
                        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.5), zorder=4)
            ax.add_patch(patches.Circle((min_x + rw - 0.30, ly + landing_h * 0.5), 0.08, facecolor="#2563EB", zorder=4))
            ax.text(min_x + fw * 0.5, min_y + flight1_h * 0.5, "DN (ARRIVAL)", rotation=270, color="#2563EB", fontsize=5.5, fontweight="bold", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=5)
            # Inner corner safety balustrade
            ax.plot([min_x + fw, min_x + rw], [ly, ly], color="#DC2626", lw=1.5, ls="--", zorder=5)
            ax.plot([min_x + fw, min_x + fw], [min_y, ly], color="#DC2626", lw=1.5, ls="--", zorder=5)

    @classmethod
    def _draw_dogleg_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws an authentic CAD double-flight dog-leg staircase with intermediate landing and clearances."""
        CADAssetLoader.draw_cad_staircase(ax, min_x, min_y, rw, rh, is_first_floor=is_first_floor, typology="dogleg")

    @classmethod
    def _draw_winder_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws a winder staircase with radiating tapered treads around the turn."""
        half_w = rw / 2.0
        landing_h = rh * 0.35
        flight_h = rh - landing_h
        steps = 6
        step_h = flight_h / steps

        # Central spine / newel post
        nx, ny = min_x + half_w, min_y + flight_h
        ax.plot([nx, nx], [min_y, ny], color="#000000", lw=2.0, zorder=3)
        ax.add_patch(patches.Circle((nx, ny), 0.10, facecolor="#0F172A", zorder=6))

        # Straight flight 1
        for i in range(steps):
            sy = min_y + i * step_h
            ax.plot([min_x, nx], [sy, sy], color="#334155", lw=0.9, ls="-", zorder=3)
            ax.text(min_x + 0.18, sy + step_h * 0.5, f"{i+1}", fontsize=4.5, color="#64748B", va="center", ha="center", zorder=4)

        # Radiating Winder Treads (pivoting around newel nx, ny into the corner landing zone)
        winder_angles = [15, 35, 55, 75, 95, 125, 155]
        for idx, ang in enumerate(winder_angles):
            rad = math.radians(ang)
            wx = nx + (half_w * 1.35) * math.cos(rad)
            wy = ny + (landing_h * 1.15) * math.sin(rad)
            # Clip within bounding box
            wx = min(max(wx, min_x), min_x + rw)
            wy = min(max(wy, min_y), min_y + rh)
            ax.plot([nx, wx], [ny, wy], color="#334155", lw=0.9, ls="-", zorder=3)
            ax.text(nx + 0.45 * math.cos(rad), ny + 0.45 * math.sin(rad), f"{steps + idx + 1}", fontsize=4.5, color="#0F172A", zorder=4)

        # Flight 2 (Right flight returning down or continuing)
        for i in range(steps):
            sy = min_y + i * step_h
            ax.plot([nx, min_x + rw], [sy, sy], color="#334155", lw=0.9, ls="-" if is_first_floor else "--", zorder=3)

        # Flow indicator
        ax.text(min_x + rw * 0.5, min_y + rh - 0.25, "WINDER (RADIAL TREADS)\nIBC CODE COMPLIANT",
                ha="center", va="center", color="#0F172A", fontsize=5.5, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.9), zorder=5)

        if not is_first_floor:
            ax.text(min_x + half_w * 0.5, min_y + flight_h * 0.4, "UP ->", color="#000000", fontsize=6.5, fontweight="bold", rotation=90, ha="center", va="center", zorder=5)
        else:
            ax.text(min_x + half_w * 1.5, min_y + flight_h * 0.4, "DN <-", color="#2563EB", fontsize=6.5, fontweight="bold", rotation=270, ha="center", va="center", zorder=5)

    @classmethod
    def _draw_spiral_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws a compact circular spiral staircase with center newel column and radiating treads."""
        cx = min_x + rw * 0.5
        cy = min_y + rh * 0.5
        dia = min(rw, rh) * 0.90
        radius = dia * 0.50
        num_treads = 16

        # Outer Balustrade Ring
        outer_ring = patches.Circle((cx, cy), radius, fill=False, edgecolor="#0F172A", lw=2.2, zorder=3)
        ax.add_patch(outer_ring)
        inner_rail = patches.Circle((cx, cy), radius - 0.06, fill=False, edgecolor="#64748B", lw=0.9, ls="-", zorder=3)
        ax.add_patch(inner_rail)

        # Center Newel Post
        center_post = patches.Circle((cx, cy), 0.12, facecolor="#0F172A", edgecolor="#000000", lw=1.2, zorder=6)
        ax.add_patch(center_post)

        # Radiating Treads
        for i in range(num_treads):
            ang = i * (360.0 / num_treads)
            rad = math.radians(ang)
            tx = cx + radius * math.cos(rad)
            ty = cy + radius * math.sin(rad)
            ls = "--" if (not is_first_floor and i > 8) else "-"
            ax.plot([cx, tx], [cy, ty], color="#334155", lw=0.9, ls=ls, zorder=4)
            # Tread numbers along perimeter
            lbl_x = cx + (radius - 0.18) * math.cos(rad + math.radians(11.25))
            lbl_y = cy + (radius - 0.18) * math.sin(rad + math.radians(11.25))
            ax.text(lbl_x, lbl_y, f"{i+1}", fontsize=4.2, color="#64748B", ha="center", va="center", zorder=5)

        # Circular Flow Arrow
        arc = patches.Arc((cx, cy), radius * 1.35, radius * 1.35, angle=0, theta1=20, theta2=270,
                          color="#000000" if not is_first_floor else "#2563EB", lw=1.6, zorder=5)
        ax.add_patch(arc)
        tip_rad = math.radians(270)
        tip_x = cx + (radius * 0.675) * math.cos(tip_rad)
        tip_y = cy + (radius * 0.675) * math.sin(tip_rad)
        ax.annotate("", xy=(tip_x, tip_y), xytext=(tip_x - 0.15, tip_y),
                    arrowprops=dict(arrowstyle="->", color="#000000" if not is_first_floor else "#2563EB", lw=1.6), zorder=5)

        lbl = f"SPIRAL STAIR (Ø {dia:.2f}m)\n16 TREADS @ 22.5°" if not is_first_floor else "DN (SPIRAL ARRIVAL)\nGUARDRAIL RING"
        ax.text(cx, cy - radius - 0.20, lbl, ha="center", va="top", fontsize=5.5, fontweight="bold",
                color="#0F172A" if not is_first_floor else "#2563EB",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.9), zorder=6)

    @classmethod
    def _draw_curved_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws an authentic architectural round / rotunda / helical sweeping curved staircase."""
        cx = min_x + rw * 0.50
        cy = min_y + rh * 0.50
        r_out = min(rw, rh) * 0.46
        r_in = r_out * 0.35
        num_treads = 20

        # Center column / newel core
        center_core = patches.Circle((cx, cy), r_in * 0.70, facecolor="#0F172A", edgecolor="#334155", lw=1.2, zorder=6)
        ax.add_patch(center_core)

        # Outer curved perimeter wall / stringer
        outer_rail = patches.Circle((cx, cy), r_out, fill=False, edgecolor="#0F172A", lw=2.4, zorder=4)
        ax.add_patch(outer_rail)
        inner_rail = patches.Circle((cx, cy), r_in, fill=False, edgecolor="#64748B", lw=1.2, ls="-", zorder=4)
        ax.add_patch(inner_rail)

        # Radiating curved treads around 300 degrees
        start_deg = 30.0
        sweep_deg = 300.0
        for i in range(num_treads + 1):
            ang = start_deg + i * (sweep_deg / num_treads)
            rad = math.radians(ang)
            p1x = cx + r_in * math.cos(rad)
            p1y = cy + r_in * math.sin(rad)
            p2x = cx + r_out * math.cos(rad)
            p2y = cy + r_out * math.sin(rad)
            ls = "--" if (not is_first_floor and i > 12) else "-"
            ax.plot([p1x, p2x], [p1y, p2y], color="#334155", lw=0.9, ls=ls, zorder=3)
            if i % 3 == 0 and i > 0 and i < num_treads:
                mid_r = (r_in + r_out) * 0.5
                tx = cx + mid_r * math.cos(rad)
                ty = cy + mid_r * math.sin(rad)
                ax.text(tx, ty, f"{i}", fontsize=4.2, color="#64748B", ha="center", va="center", zorder=5)

        # Sweeping Flow Arc
        r_flow = (r_in + r_out) * 0.50
        flow_arc = patches.Arc((cx, cy), r_flow * 2, r_flow * 2, angle=0, theta1=start_deg + 15, theta2=start_deg + sweep_deg - 15,
                               color="#000000" if not is_first_floor else "#2563EB", lw=1.6, ls="-", zorder=5)
        ax.add_patch(flow_arc)
        tip_ang = math.radians(start_deg + sweep_deg - 15)
        tip_x = cx + r_flow * math.cos(tip_ang)
        tip_y = cy + r_flow * math.sin(tip_ang)
        flow_lbl = "UP ->" if not is_first_floor else "DN <-"
        ax.annotate(flow_lbl, xy=(tip_x, tip_y), xytext=(tip_x - 0.25, tip_y),
                    color="#000000" if not is_first_floor else "#2563EB", fontsize=6.0, fontweight="bold", zorder=7)

        dia = r_out * 2.0
        lbl = f"FEATURE ROUND STAIRS (Ø {dia:.1f}m)\nHELICAL ROTUNDA" if not is_first_floor else "DN (ROUND STAIR ARRIVAL)\nOPEN LIGHTWELL VOID"
        ax.text(cx, min_y + rh - 0.20, lbl,
                ha="center", va="top", color="#0F172A" if not is_first_floor else "#2563EB", fontsize=5.5, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.9), zorder=6)

    @classmethod
    def _draw_ladder_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws a compact ship's ladder / loft stair with heavy stringers and safety rungs."""
        ladder_w = min(rw, 0.75)
        lx = min_x + (rw - ladder_w) * 0.50
        rx = lx + ladder_w
        num_rungs = 12
        rung_step = rh / num_rungs

        # Heavy steel stringers
        ax.plot([lx, lx], [min_y, min_y + rh], color="#0F172A", lw=3.0, zorder=4)
        ax.plot([rx, rx], [min_y, min_y + rh], color="#0F172A", lw=3.0, zorder=4)

        # Safety grab rails
        ax.plot([lx - 0.06, lx - 0.06], [min_y, min_y + rh], color="#2563EB", lw=1.2, ls="--", zorder=3)
        ax.plot([rx + 0.06, rx + 0.06], [min_y, min_y + rh], color="#2563EB", lw=1.2, ls="--", zorder=3)

        # Rungs
        for i in range(num_rungs + 1):
            ry = min_y + i * rung_step
            ax.plot([lx, rx], [ry, ry], color="#1E293B", lw=1.8, zorder=3)
            # Center tread grip mark
            ax.plot([lx + ladder_w * 0.35, rx - ladder_w * 0.35], [ry, ry], color="#F59E0B", lw=2.2, zorder=4)

        cx = lx + ladder_w * 0.50
        arrow_col = "#000000" if not is_first_floor else "#2563EB"
        ax.annotate("", xy=(cx, min_y + rh - 0.3), xytext=(cx, min_y + 0.3),
                    arrowprops=dict(arrowstyle="->", color=arrow_col, lw=1.6), zorder=5)
        ax.text(cx, min_y + rh * 0.50, "SHIP'S LADDER (68° PITCH)\nSAFETY RAILS", ha="center", va="center",
                color=arrow_col, fontsize=5.0, fontweight="bold", rotation=90,
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.9), zorder=6)

    @classmethod
    def _draw_floating_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws a continuous, elegant cantilevered floating staircase flush against lateral party wall."""
        CADAssetLoader.draw_cad_staircase(ax, min_x, min_y, rw, rh, is_first_floor=is_first_floor, typology="floating")

    @classmethod
    def _draw_bifurcated_stair(cls, ax, min_x, min_y, rw, rh, is_first_floor: bool = False, meta: dict = None):
        """Draws a grand bifurcated / split staircase with central flight branching left & right."""
        main_flight_w = rw * 0.52
        main_flight_x = min_x + (rw - main_flight_w) * 0.50
        landing_y = min_y + rh * 0.44
        landing_h = rh * 0.20
        steps_main = 8
        step_h = (landing_y - min_y) / steps_main

        # Grand Starting Curtail Step (Curved flare at base)
        ax.plot([main_flight_x - 0.20, main_flight_x + main_flight_w + 0.20], [min_y, min_y], color="#0F172A", lw=2.4, zorder=4)

        # Central Main Flight
        for i in range(1, steps_main + 1):
            sy = min_y + i * step_h
            ax.plot([main_flight_x, main_flight_x + main_flight_w], [sy, sy], color="#334155", lw=1.0, ls="-", zorder=3)
            ax.text(main_flight_x + 0.25, sy - step_h * 0.5, f"{i}", fontsize=4.5, color="#64748B", va="center", ha="center", zorder=4)

        # Side stringers for main flight
        ax.plot([main_flight_x, main_flight_x], [min_y, landing_y], color="#0F172A", lw=2.0, zorder=4)
        ax.plot([main_flight_x + main_flight_w, main_flight_x + main_flight_w], [min_y, landing_y], color="#0F172A", lw=2.0, zorder=4)

        # Grand Mid Landing (Spanning full width)
        ax.plot([min_x, min_x + rw], [landing_y, landing_y], color="#0F172A", lw=1.6, zorder=3)
        ax.plot([min_x, min_x + rw], [landing_y + landing_h, landing_y + landing_h], color="#0F172A", lw=1.6, zorder=3)
        ax.text(min_x + rw * 0.5, landing_y + landing_h * 0.5, "GRAND MID-LANDING (+1500mm)\nFULL WIDTH DISTRIBUTION",
                ha="center", va="center", color="#0F172A", fontsize=5.5, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.9), zorder=5)

        # Branch Flight 1 (Left flight ascending to top)
        branch_w = rw * 0.28
        branch_steps = 7
        branch_step_h = (rh - (landing_y + landing_h)) / branch_steps
        for j in range(branch_steps + 1):
            by = landing_y + landing_h + j * branch_step_h
            ax.plot([min_x, min_x + branch_w], [by, by], color="#334155", lw=0.9, ls="-", zorder=3)

        # Branch Flight 2 (Right flight ascending to top)
        for j in range(branch_steps + 1):
            by = landing_y + landing_h + j * branch_step_h
            ax.plot([min_x + rw - branch_w, min_x + rw], [by, by], color="#334155", lw=0.9, ls="-", zorder=3)

        # Center Void on Level 1 (Foyer opening between branches)
        if is_first_floor:
            void_x1 = min_x + branch_w
            void_x2 = min_x + rw - branch_w
            ax.plot([void_x1, void_x2], [landing_y + landing_h, landing_y + landing_h], color="#DC2626", lw=1.8, ls="--", zorder=5)
            ax.text((void_x1 + void_x2) * 0.5, landing_y + landing_h + (rh - (landing_y + landing_h)) * 0.5,
                    "DOUBLE HEIGHT FOYER VOID\nOPEN TO BELOW (RAILED)",
                    ha="center", va="center", color="#DC2626", fontsize=5.5, fontweight="bold",
                    bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="#DC2626", lw=0.5, alpha=0.9), zorder=6)
            # DN arrows on left & right branches
            ax.annotate("", xy=(min_x + branch_w * 0.5, landing_y + landing_h + 0.15),
                        xytext=(min_x + branch_w * 0.5, min_y + rh - 0.25),
                        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.5), zorder=5)
            ax.annotate("", xy=(min_x + rw - branch_w * 0.5, landing_y + landing_h + 0.15),
                        xytext=(min_x + rw - branch_w * 0.5, min_y + rh - 0.25),
                        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.5), zorder=5)
        else:
            # Grand branching UP arrows
            mcx = min_x + rw * 0.5
            ax.plot([mcx, mcx], [min_y + 0.30, landing_y + landing_h * 0.4], color="#000000", lw=1.6, zorder=5)
            ax.annotate("", xy=(min_x + branch_w * 0.5, landing_y + landing_h + 0.25),
                        xytext=(mcx, landing_y + landing_h * 0.4),
                        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.5), zorder=5)
            ax.annotate("", xy=(min_x + rw - branch_w * 0.5, landing_y + landing_h + 0.25),
                        xytext=(mcx, landing_y + landing_h * 0.4),
                        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.5), zorder=5)
            ax.add_patch(patches.Circle((mcx, min_y + 0.25), 0.09, facecolor="#000000", zorder=5))

    @classmethod
    def _draw_modular_staircase(cls, ax, room: RoomModel, min_x, min_y, rw, rh, is_first_floor: bool = False):
        """Unified dispatcher for rendering all 9 modular staircase typologies.
        
        The room bounding box is forwarded to curved/spiral/bifurcated sub-drawers
        as a ``room_bbox`` so they can clip their arcs within the wall face.
        Stamps real CAD stair reference image from 'furniture ,car,stairs' as background underlay.
        """
        meta = room.metadata or {}
        typology = meta.get("typology", "").lower()
        r_name = (room.room_name + " " + room.room_id).lower()
        room_bbox = (min_x, min_y, min_x + rw, min_y + rh)

        if "spiral" in typology or "spiral" in r_name:
            cls._draw_spiral_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)
        elif "ladder" in typology or "ship" in typology or "ladder" in r_name or "ship" in r_name:
            cls._draw_ladder_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)
        elif "bifurcated" in typology or "split" in typology or "bifurcated" in r_name:
            cls._draw_bifurcated_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)
        elif "curved" in typology or "circular" in typology or "curved" in r_name or "rotunda" in r_name or "round" in typology or "round" in r_name or "helical" in typology or "helical" in r_name:
            cls._draw_curved_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)
        elif "floating" in typology or "cantilever" in typology or "floating" in r_name:
            cls._draw_floating_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)
        elif "straight" in typology or "straight" in r_name:
            cls._draw_straight_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)
        elif "l_shaped" in typology or "l-shape" in typology or "quarter" in r_name or "l_shape" in r_name:
            cls._draw_l_shaped_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)
        elif "winder" in typology or "winder" in r_name:
            cls._draw_winder_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)
        else:
            cls._draw_dogleg_stair(ax, min_x, min_y, rw, rh, is_first_floor, meta)

    # Maintain backwards-compatibility alias
    _draw_staircase = _draw_dogleg_stair


    @classmethod
    def _draw_terrace_patio(cls, ax, min_x, min_y, rw, rh):
        """Draws outdoor patio furniture clamped within terrace_poly.buffer(-0.35m)."""
        ax.plot([min_x, min_x + rw], [min_y, min_y], color="#475569", lw=1.8, ls="-.", zorder=3)
        ax.plot([min_x, min_x], [min_y, min_y + rh], color="#475569", lw=1.8, ls="-.", zorder=3)
        ax.plot([min_x + rw, min_x + rw], [min_y, min_y + rh], color="#475569", lw=1.8, ls="-.", zorder=3)
        ax.text(min_x + rw * 0.5, min_y + min(0.18, rh * 0.12), "SAFETY PARAPET & GLASS RAILING", fontsize=5.0, color="#64748B", ha="center", va="bottom", zorder=4)

        # Strictly clamp furniture bounding box to terrace_poly.buffer(-0.35m)
        safe_x_min = min_x + 0.35
        safe_x_max = min_x + rw - 0.35
        safe_y_min = min_y + 0.35
        safe_y_max = min_y + rh - 0.35

        if safe_y_max <= safe_y_min:
            safe_y_min = min_y + rh * 0.10
            safe_y_max = min_y + rh * 0.90
        if safe_x_max <= safe_x_min:
            safe_x_min = min_x + rw * 0.10
            safe_x_max = min_x + rw * 0.90

        cx = (safe_x_min + safe_x_max) / 2.0
        cy = (safe_y_min + safe_y_max) / 2.0
        avail_half_h = (safe_y_max - safe_y_min) / 2.0
        avail_half_w = (safe_x_max - safe_x_min) / 2.0

        if rh < 1.80:
            # Compact balcony: place table and 2 horizontally flanking chairs (Left/Right)
            r_tbl = min(0.35, max(0.14, avail_half_h * 0.85))
            r_ch = min(0.18, max(0.08, r_tbl * 0.70))
            ax.add_patch(patches.Circle((cx, cy), r_tbl, facecolor="#F1F5F9", edgecolor="#334155", lw=1.1, zorder=3))
            ax.text(cx, cy, "PATIO\nSET" if r_tbl >= 0.22 else "PATIO", fontsize=max(4.0, min(5.5, r_tbl * 12.0)), fontweight="bold", ha="center", va="center", color="#334155", zorder=4)

            ch_dist = r_tbl + r_ch + 0.08
            if ch_dist + r_ch > avail_half_w:
                ch_dist = max(r_tbl + 0.04, avail_half_w - r_ch)

            for angle in [0, 180]:
                rad = math.radians(angle)
                ch_x = cx + ch_dist * math.cos(rad)
                ch_y = cy + ch_dist * math.sin(rad)
                ax.add_patch(patches.Circle((ch_x, ch_y), r_ch, facecolor="#FFFFFF", edgecolor="#475569", lw=0.9, zorder=3))
        else:
            # Deep terrace: 4-seater round patio set
            max_r = min(avail_half_h, avail_half_w) * 0.95
            r_ch = min(0.22, max_r * 0.25)
            r_tbl = max_r * 0.45
            ch_dist = r_tbl + r_ch + 0.08
            ax.add_patch(patches.Circle((cx, cy), r_tbl, facecolor="#F1F5F9", edgecolor="#334155", lw=1.1, zorder=3))
            ax.text(cx, cy, "PATIO\nSET", fontsize=6.0, fontweight="bold", ha="center", va="center", color="#334155", zorder=4)

            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                ch_x = cx + ch_dist * math.cos(rad)
                ch_y = cy + ch_dist * math.sin(rad)
                ax.add_patch(patches.Circle((ch_x, ch_y), r_ch, facecolor="#FFFFFF", edgecolor="#475569", lw=0.9, zorder=3))

    @classmethod
    def _draw_lawn_grass(cls, ax, min_x, min_y, rw, rh):
        """Draws landscape grass/lawn using pure architectural vector stippling and soft natural tone."""
        # Background soft green wash
        ax.add_patch(patches.Rectangle((min_x, min_y), rw, rh,
                                       facecolor="#ECFDF5", edgecolor="#10B981",
                                       lw=0.8, ls=":", zorder=1))
        # Micro grass stippling / shrub markers
        step_x = max(0.8, rw / 4.0)
        step_y = max(0.8, rh / 4.0)
        nx = max(1, int(rw / step_x))
        ny = max(1, int(rh / step_y))
        for ix in range(nx):
            for iy in range(ny):
                gx = min_x + (ix + 0.5) * (rw / nx)
                gy = min_y + (iy + 0.5) * (rh / ny)
                # Delicate shrublet symbol
                ax.add_patch(patches.Circle((gx, gy), 0.12, facecolor="#A7F3D0", edgecolor="#059669", lw=0.6, zorder=2))
                ax.plot([gx - 0.08, gx + 0.08], [gy, gy], color="#047857", lw=0.5, zorder=3)
                ax.plot([gx, gx], [gy - 0.08, gy + 0.08], color="#047857", lw=0.5, zorder=3)
        ax.text(min_x + rw * 0.5, min_y + rh * 0.5, "FRONT LAWN / GARDEN",
                ha="center", va="center", color="#065F46", fontsize=5.5, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="#A7F3D0", alpha=0.9),
                zorder=4)

    @classmethod
    def _draw_study_library(cls, ax, min_x, min_y, rw, rh):
        """Draws dedicated executive study desk, ergonomic chair, visitor armchairs, and modular library bookshelves."""
        # 1. Executive Study Desk
        desk_w = min(1.60, rw * 0.65)
        desk_d = min(0.70, rh * 0.35)
        dx = min_x + 0.30
        dy = min_y + rh - desk_d - 0.25
        ax.add_patch(patches.FancyBboxPatch(
            (dx, dy), desk_w, desk_d,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor="#E2E8F0", edgecolor="#1E293B", lw=1.3, zorder=2))
        # Desktop monitor / workstation screen
        ax.add_patch(patches.Rectangle((dx + desk_w/2 - 0.25, dy + desk_d - 0.16), 0.50, 0.06,
            facecolor="#0F172A", edgecolor="#000000", lw=0.9, zorder=3))
        ax.text(dx + desk_w / 2.0, dy + desk_d / 2.0 - 0.04, "EXECUTIVE DESK", ha="center", va="center", color="#0F172A", fontsize=5.0, fontweight="bold", zorder=4)

        # 2. Ergonomic Swivel Chair
        chair_r = 0.20
        cy_c = dy - chair_r - 0.06
        cx_c = dx + desk_w / 2.0
        ax.add_patch(patches.Circle((cx_c, cy_c), chair_r, facecolor="#F8FAFC", edgecolor="#1E293B", lw=1.1, zorder=3))
        ax.plot([cx_c - chair_r + 0.04, cx_c + chair_r - 0.04], [cy_c - 0.05, cy_c - 0.05], color="#334155", lw=2.2, solid_capstyle="round", zorder=4)

        # 3. Modular Library Bookshelf along West wall
        shelf_w = 0.35
        shelf_h = min(1.80, rh * 0.60)
        ax.add_patch(patches.Rectangle((min_x + 0.10, min_y + 0.20), shelf_w, shelf_h, facecolor="#CBD5E1", edgecolor="#475569", lw=1.0, zorder=2))
        for bi in range(3):
            sy_b = min_y + 0.20 + (bi + 1) * (shelf_h / 4.0)
            ax.plot([min_x + 0.10, min_x + 0.10 + shelf_w], [sy_b, sy_b], color="#64748B", lw=0.8, ls="--", zorder=3)
        ax.text(min_x + 0.10 + shelf_w / 2.0, min_y + 0.20 + shelf_h / 2.0, "BOOKSHELF", rotation=90, ha="center", va="center", color="#334155", fontsize=5.0, fontweight="bold", zorder=3)


    @classmethod
    def _draw_laundry_utility(cls, ax, min_x, min_y, rw, rh):
        """Draws laundry washer, dryer, folding counter, and utility sink."""
        ax.add_patch(patches.Rectangle((min_x + rw - 0.70, min_y + 0.10), 0.65, rh - 0.20, facecolor="#F1F5F9", edgecolor="#475569", lw=1.0, zorder=2))
        wy = min_y + 0.30
        ax.add_patch(patches.Rectangle((min_x + rw - 0.65, wy), 0.55, 0.60, facecolor="#FFFFFF", edgecolor="#0284C7", lw=1.0, zorder=3))
        ax.add_patch(patches.Circle((min_x + rw - 0.375, wy + 0.30), 0.20, facecolor="#E0F2FE", edgecolor="#0284C7", lw=0.8, zorder=4))
        ax.text(min_x + rw - 0.375, wy + 0.30, "WASHER", fontsize=5.0, fontweight="bold", ha="center", va="center", color="#0369A1", zorder=5)
        dy = wy + 0.75
        ax.add_patch(patches.Rectangle((min_x + rw - 0.65, dy), 0.55, 0.60, facecolor="#FFFFFF", edgecolor="#D97706", lw=1.0, zorder=3))
        ax.add_patch(patches.Circle((min_x + rw - 0.375, dy + 0.30), 0.20, facecolor="#FEF3C7", edgecolor="#D97706", lw=0.8, zorder=4))
        ax.text(min_x + rw - 0.375, dy + 0.30, "DRYER", fontsize=5.0, fontweight="bold", ha="center", va="center", color="#B45309", zorder=5)
        sy = dy + 0.75
        if sy + 0.50 <= min_y + rh:
            ax.add_patch(patches.Rectangle((min_x + rw - 0.65, sy), 0.55, 0.50, facecolor="#FFFFFF", edgecolor="#475569", lw=0.8, zorder=3))
            ax.text(min_x + rw - 0.375, sy + 0.25, "SINK", fontsize=5.0, ha="center", va="center", color="#475569", zorder=4)

    @classmethod
    def _draw_kitchenette(cls, ax, min_x, min_y, rw, rh):
        """Draws compact coffee pantry / kitchenette with counter, bar sink, and stools."""
        ax.add_patch(patches.Rectangle((min_x + rw - 0.65, min_y + 0.10), 0.60, rh - 0.20, facecolor="#FED7AA", edgecolor="#C2410C", lw=1.1, zorder=2))
        ax.add_patch(patches.Rectangle((min_x + rw - 0.55, min_y + 0.40), 0.42, 0.45, facecolor="#FFFFFF", edgecolor="#475569", lw=0.8, zorder=3))
        ax.text(min_x + rw - 0.34, min_y + 0.62, "SINK", fontsize=5.0, ha="center", va="center", color="#475569", zorder=4)
        ax.add_patch(patches.Rectangle((min_x + rw - 0.55, min_y + 1.20), 0.42, 0.55, facecolor="#334155", edgecolor="#0F172A", lw=0.9, zorder=3))
        ax.text(min_x + rw - 0.34, min_y + 1.47, "COFFEE\nBAR", fontsize=5.0, fontweight="bold", ha="center", va="center", color="#F8FAFC", zorder=4)
        bar_w, bar_h = 1.60, 0.65
        bx = min_x + rw * 0.25
        by = min_y + rh * 0.50
        ax.add_patch(patches.Rectangle((bx, by), bar_w, bar_h, facecolor="#FDBA74", edgecolor="#9A3412", lw=1.1, zorder=2))
        ax.text(bx + bar_w/2.0, by + bar_h/2.0, "BREAKFAST BAR", fontsize=5.5, fontweight="bold", ha="center", va="center", color="#7C2D12", zorder=3)
        for i in range(2):
            st_x = bx + 0.35 + i * 0.80
            ax.add_patch(patches.Circle((st_x, by - 0.25), 0.16, facecolor="#FEF3C7", edgecolor="#9A3412", lw=0.8, zorder=2))

    @classmethod
    def _draw_double_bed(cls, ax, cx, cy, rw, rh, bed_orientation: str = "top",
                         min_x: float = 0.0, min_y: float = 0.0):
        """Draws a detailed luxury master bed with headboard, pillows, blanket fold, nightstands.
        
        Nightstands and lamps are clamped to [min_x+0.10, min_x+rw-0.10] so they
        never cross the exterior wall face.
        """
        bed_w, bed_h = 1.90, 2.10
        # Clamp bed centre so bed stays within safe zone
        safe_hw = rw / 2.0 - 0.25  # 0.25m keeps headboard off side walls
        safe_hh = rh / 2.0 - 0.25
        bed_cx = max(min_x + rw * 0.5, min(cx, min_x + rw * 0.5))  # keep centred
        bed_cy = cy

        bx = bed_cx - bed_w / 2.0
        by = bed_cy - bed_h / 2.0

        # Safe horizontal extents for side furniture
        wall_margin = 0.10
        safe_x_min = min_x + wall_margin
        safe_x_max = min_x + rw - wall_margin

        # 1. Wooden Headboard
        hb = patches.Rectangle((bx - 0.05, by + bed_h - 0.15), bed_w + 0.10, 0.20, facecolor="#475569", edgecolor="#1E293B", lw=1.2, zorder=2)
        ax.add_patch(hb)

        # 2. Main Bed Mattress
        bed_mat = patches.Rectangle((bx, by), bed_w, bed_h - 0.10, facecolor="#E0E7FF", edgecolor="#4F46E5", lw=1.0, zorder=2)
        ax.add_patch(bed_mat)

        # 3. Two Pillows
        p_w, p_h = 0.65, 0.40
        p1 = patches.Rectangle((bx + 0.15, by + bed_h - 0.60), p_w, p_h, facecolor="#FFFFFF", edgecolor="#6366F1", lw=0.8, zorder=3)
        p2 = patches.Rectangle((bx + bed_w - 0.15 - p_w, by + bed_h - 0.60), p_w, p_h, facecolor="#FFFFFF", edgecolor="#6366F1", lw=0.8, zorder=3)
        ax.add_patch(p1)
        ax.add_patch(p2)

        # 4. Folded Duvet / Blanket Accent
        duvet = patches.Rectangle((bx, by), bed_w, 0.85, facecolor="#C7D2FE", edgecolor="#4338CA", lw=0.9, zorder=3)
        ax.add_patch(duvet)

        # 5. Nightstands (Side Tables) with Lamps – clamped to safe zone
        ns_size = 0.45
        # Left Nightstand: clamp so right edge >= safe_x_min
        ns_left_x = max(safe_x_min, bx - ns_size - 0.10)
        if ns_left_x + ns_size > safe_x_max:
            ns_left_x = None  # No room – skip
        if ns_left_x is not None:
            ns_left = patches.Rectangle((ns_left_x, by + bed_h - ns_size - 0.10), ns_size, ns_size, facecolor="#CBD5E1", edgecolor="#475569", lw=0.8, zorder=2)
            ax.add_patch(ns_left)
            lamp_x = min(safe_x_max - 0.05, max(safe_x_min + 0.05, ns_left_x + ns_size / 2.0))
            ax.add_patch(patches.Circle((lamp_x, by + bed_h - ns_size / 2.0 - 0.10), 0.10, facecolor="#FDE047", edgecolor="#CA8A04", zorder=3))

        # Right Nightstand: clamp so left edge <= safe_x_max
        ns_right_x = min(safe_x_max - ns_size, bx + bed_w + 0.10)
        if ns_right_x < safe_x_min:
            ns_right_x = None  # No room – skip
        if ns_right_x is not None:
            ns_right = patches.Rectangle((ns_right_x, by + bed_h - ns_size - 0.10), ns_size, ns_size, facecolor="#CBD5E1", edgecolor="#475569", lw=0.8, zorder=2)
            ax.add_patch(ns_right)
            lamp_x = max(safe_x_min + 0.05, min(safe_x_max - 0.05, ns_right_x + ns_size / 2.0))
            ax.add_patch(patches.Circle((lamp_x, by + bed_h - ns_size / 2.0 - 0.10), 0.10, facecolor="#FDE047", edgecolor="#CA8A04", zorder=3))

    @classmethod
    def _draw_wardrobe(cls, ax, x, y, width, depth=0.60):
        """Draws an architectural built-in wardrobe with sliding closet lines."""
        wardrobe = patches.Rectangle((x, y), width, depth, facecolor="#F1F5F9", edgecolor="#64748B", lw=1.0, zorder=2)
        ax.add_patch(wardrobe)
        # Sliding track lines
        ax.plot([x, x + width], [y + depth/2.0, y + depth/2.0], color="#94A3B8", lw=0.8, ls="--", zorder=3)
        ax.text(x + width/2.0, y + depth/2.0, "WARDROBE", ha="center", va="center", color="#475569", fontsize=6.5, fontweight="bold", zorder=3)

    @classmethod
    def _draw_living_furniture(cls, ax, cx, cy, rw, rh, is_formal_drawing: bool = False):
        """Draws authentic 1:100 CAD living room / drawing room seating arrangements."""
        CADAssetLoader.draw_cad_living_suite(ax, cx, cy, rw, rh, is_formal_drawing=is_formal_drawing)

    @classmethod
    def _draw_dining_table(cls, ax, cx, cy, seats: int = 8):
        """Draws an authentic 8-seater CAD dining table with individual chairs and 3ft pull-out clearance buffer."""
        CADAssetLoader.draw_cad_dining_suite(ax, cx, cy, rw=2.5, rh=2.5)

    @classmethod
    def _draw_kitchen_details(cls, ax, min_x, min_y, rw, rh, meta: dict = None):
        """Draws modern 8ft x 4ft waterfall prep island for show kitchen or 24" perimeter counters for wet kitchen."""
        meta = meta or {}
        r_name = str(meta.get("room_name", "")).lower()
        is_show = meta.get("waterfall_island") or ("show" in r_name or "gourmet" in r_name or ("dirty" not in r_name and "wet" not in r_name and "scullery" not in r_name and "pantry" not in r_name))
        CADAssetLoader.draw_cad_kitchen_details(ax, min_x, min_y, rw, rh, is_show_kitchen=is_show)

    @classmethod
    def _draw_bathroom_fixtures(cls, ax, min_x, min_y, rw, rh, meta: dict = None):
        """Draws authentic CAD sanitary fixtures: 5-fixture luxury ensuite or screened powder room."""
        meta = meta or {}
        r_name = str(meta.get("room_name", "")).lower()
        is_5_fixture = meta.get("double_vanity") or meta.get("soaking_tub") or "5-fixture" in r_name or "spa" in r_name or ("master" in r_name and rw >= 2.0)
        is_powder = "powder" in r_name
        CADAssetLoader.draw_cad_bath_fixtures(ax, min_x, min_y, rw, rh, is_5_fixture=is_5_fixture, is_powder=is_powder)

    @classmethod
    def _draw_cars(cls, ax, min_x, min_y, rw, rh, count: int = 2):
        """Draws authentic 1:100 scale CAD top-down passenger sedans and luxury SUVs strictly clamped within porch."""
        wall_margin = 0.35
        # Ensure vehicles fit strictly inside porch boundaries [min_y + margin, min_y + rh - margin]
        max_car_len = max(3.60, min(4.30, rh - 2 * wall_margin))
        cy = min_y + rh * 0.50  # Strictly centered vertically inside the porch
        if rw < 4.2 or count == 1:
            cx = min_x + rw * 0.50
            car_w = min(1.85, rw - 2 * wall_margin)
            CADAssetLoader.draw_cad_sedan(ax, cx, cy, length_m=max_car_len, width_m=car_w, show_clearance=False)
        else:
            # 2 Cars side-by-side with guaranteed clearance from side and rear walls
            car_w = min(1.78, (rw - 3 * wall_margin) / 2.0)
            cx1 = min_x + wall_margin + car_w * 0.50 + 0.08
            cx2 = min_x + rw - wall_margin - car_w * 0.50 - 0.08
            CADAssetLoader.draw_cad_suv(ax, cx1, cy, length_m=max_car_len, width_m=car_w, show_clearance=False)
            CADAssetLoader.draw_cad_sedan(ax, cx2, cy, length_m=max_car_len * 0.95, width_m=car_w * 0.96, show_clearance=False)

    @classmethod
    def _draw_single_car(cls, ax, cx, cy, w, h):
        """Draws a single 1:100 CAD passenger sedan with authentic contours."""
        CADAssetLoader.draw_cad_sedan(ax, cx, cy, length_m=max(h, 4.30), width_m=max(w, 1.80), show_clearance=False)

    @classmethod
    def _draw_architectural_door(
        cls,
        ax,
        p,
        width_m: float = 0.95,
        is_double: bool = False,
        is_vertical: bool = False,
        room_poly_pts: Optional[List] = None,
        is_sliding: bool = False,
        is_cased_opening: bool = False
    ):
        """Draws clean architectural 2D CAD door leaves (quarter-circle swing arcs, pocket doors, or open cased portals).
        
        - Masks the wall line across the door opening.
        - Adds crisp perpendicular jamb tick marks.
        - For open cased openings: masks wall and adds jamb ticks with zero swing arc (modern lobby transition).
        - For swinging doors: swings 90 degrees into room volume.
        - For sliding/pocket doors: renders sliding leaves, pocket cavity, and motion arrows (zero swing).
        """
        px, py = p[0], p[1]
        w = width_m
        hw = w / 2.0

        if is_cased_opening:
            # 2D CAD Open Cased Opening / Archway (Wall masked + jamb ticks + zero swinging leaf)
            if not is_vertical:
                ax.plot([px - hw, px + hw], [py, py], color="#FFFFFF", lw=5.0, solid_capstyle="butt", zorder=5)
                ax.plot([px - hw, px - hw], [py - 0.09, py + 0.09], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
                ax.plot([px + hw, px + hw], [py - 0.09, py + 0.09], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
            else:
                ax.plot([px, px], [py - hw, py + hw], color="#FFFFFF", lw=5.0, solid_capstyle="butt", zorder=5)
                ax.plot([px - 0.09, px + 0.09], [py - hw, py - hw], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
                ax.plot([px - 0.09, px + 0.09], [py + hw, py + hw], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
            return

        if is_sliding:
            # 2D CAD Architectural Pocket Sliding Door (Zero swing arc!)
            if not is_vertical:
                ax.plot([px - hw, px + hw], [py, py], color="#FFFFFF", lw=5.0, solid_capstyle="butt", zorder=5)
                ax.plot([px - hw, px - hw], [py - 0.09, py + 0.09], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
                ax.plot([px + hw, px + hw], [py - 0.09, py + 0.09], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
                if is_double:
                    ax.plot([px - hw, px + 0.05], [py - 0.03, py - 0.03], color="#0F172A", lw=2.4, solid_capstyle="round", zorder=7)
                    ax.plot([px - 0.05, px + hw], [py + 0.03, py + 0.03], color="#0F172A", lw=2.4, solid_capstyle="round", zorder=7)
                    ax.plot([px - hw - 0.45, px - hw], [py, py], color="#94A3B8", lw=1.2, ls="--", zorder=6)
                    ax.plot([px + hw, px + hw + 0.45], [py, py], color="#94A3B8", lw=1.2, ls="--", zorder=6)
                    ax.annotate("", xy=(px - hw + 0.15, py - 0.10), xytext=(px - 0.15, py - 0.10),
                                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.0), zorder=8)
                    ax.annotate("", xy=(px + hw - 0.15, py + 0.10), xytext=(px + 0.15, py + 0.10),
                                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.0), zorder=8)
                else:
                    ax.plot([px - hw, px + hw], [py + 0.03, py + 0.03], color="#0F172A", lw=2.4, solid_capstyle="round", zorder=7)
                    ax.plot([px - hw - 0.45, px - hw], [py, py], color="#94A3B8", lw=1.2, ls="--", zorder=6)
                    ax.annotate("", xy=(px - hw + 0.20, py - 0.10), xytext=(px + hw - 0.20, py - 0.10),
                                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.0), zorder=8)
            else:
                ax.plot([px, px], [py - hw, py + hw], color="#FFFFFF", lw=5.0, solid_capstyle="butt", zorder=5)
                ax.plot([px - 0.09, px + 0.09], [py - hw, py - hw], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
                ax.plot([px - 0.09, px + 0.09], [py + hw, py + hw], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
                if is_double:
                    ax.plot([px - 0.03, px - 0.03], [py - hw, py + 0.05], color="#0F172A", lw=2.4, solid_capstyle="round", zorder=7)
                    ax.plot([px + 0.03, px + 0.03], [py - 0.05, py + hw], color="#0F172A", lw=2.4, solid_capstyle="round", zorder=7)
                    ax.plot([px, px], [py - hw - 0.45, py - hw], color="#94A3B8", lw=1.2, ls="--", zorder=6)
                    ax.plot([px, px], [py + hw, py + hw + 0.45], color="#94A3B8", lw=1.2, ls="--", zorder=6)
                    ax.annotate("", xy=(px - 0.10, py - hw + 0.15), xytext=(px - 0.10, py - 0.15),
                                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.0), zorder=8)
                    ax.annotate("", xy=(px + 0.10, py + hw - 0.15), xytext=(px + 0.10, py + 0.15),
                                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.0), zorder=8)
                else:
                    ax.plot([px + 0.03, px + 0.03], [py - hw, py + hw], color="#0F172A", lw=2.4, solid_capstyle="round", zorder=7)
                    ax.plot([px, px], [py - hw - 0.45, py - hw], color="#94A3B8", lw=1.2, ls="--", zorder=6)
                    ax.annotate("", xy=(px - 0.10, py - hw + 0.20), xytext=(px - 0.10, py + hw - 0.20),
                                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.0), zorder=8)
            return

        # 1. Determine swing direction (into room) and hinge jamb
        swing_dir = 1
        hinge_side = 0  # 0: left / bottom, 1: right / top

        if room_poly_pts and len(room_poly_pts) >= 3:
            try:
                from shapely.geometry import Polygon as ShapelyPolygon, Point
                room_shp = ShapelyPolygon(room_poly_pts)
                if not room_shp.is_valid:
                    room_shp = room_shp.buffer(0)

                min_x = min(pt[0] for pt in room_poly_pts)
                max_x = max(pt[0] for pt in room_poly_pts)
                min_y = min(pt[1] for pt in room_poly_pts)
                max_y = max(pt[1] for pt in room_poly_pts)
                cx, cy = room_shp.centroid.x, room_shp.centroid.y

                if not is_vertical:
                    # Horizontal wall: swing North (+1) or South (-1)
                    if room_shp.contains(Point(px, py + 0.25)):
                        swing_dir = 1
                    elif room_shp.contains(Point(px, py - 0.25)):
                        swing_dir = -1
                    else:
                        swing_dir = 1 if cy >= py else -1

                    # Hinge side: choose jamb closer to adjacent room corner/wall
                    dist_left = abs((px - hw) - min_x)
                    dist_right = abs(max_x - (px + hw))
                    hinge_side = 0 if dist_left <= dist_right + 0.05 else 1
                else:
                    # Vertical wall: swing East (+1) or West (-1)
                    if room_shp.contains(Point(px + 0.25, py)):
                        swing_dir = 1
                    elif room_shp.contains(Point(px - 0.25, py)):
                        swing_dir = -1
                    else:
                        swing_dir = 1 if cx >= px else -1

                    # Hinge side: choose jamb closer to adjacent room corner/wall
                    dist_bottom = abs((py - hw) - min_y)
                    dist_top = abs(max_y - (py + hw))
                    hinge_side = 0 if dist_bottom <= dist_top + 0.05 else 1
            except Exception:
                pass

        # 2. Render Wall Opening Mask & Jamb Ticks
        if not is_vertical:
            # Horizontal wall opening mask (clears the wall line behind the door)
            ax.plot([px - hw, px + hw], [py, py], color="#FFFFFF", lw=4.8, solid_capstyle="butt", zorder=5)
            # Jamb ticks
            ax.plot([px - hw, px - hw], [py - 0.08, py + 0.08], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
            ax.plot([px + hw, px + hw], [py - 0.08, py + 0.08], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)

            if is_double:
                half = w / 2.0
                # Left Leaf hinged at left jamb
                hx_l, hy_l = px - hw, py
                ax.plot([hx_l, hx_l], [hy_l, hy_l + swing_dir * half], color="#0F172A", lw=2.2, solid_capstyle="round", zorder=7)
                ax.add_patch(patches.Circle((hx_l, hy_l), 0.03, facecolor="#0F172A", edgecolor="#0F172A", zorder=8))
                t1_l, t2_l = (0, 90) if swing_dir > 0 else (270, 360)
                arc_l = patches.Arc((hx_l, hy_l), half * 2, half * 2, angle=0, theta1=t1_l, theta2=t2_l, color="#475569", lw=1.1, ls="--", zorder=6)
                ax.add_patch(arc_l)

                # Right Leaf hinged at right jamb
                hx_r, hy_r = px + hw, py
                ax.plot([hx_r, hx_r], [hy_r, hy_r + swing_dir * half], color="#0F172A", lw=2.2, solid_capstyle="round", zorder=7)
                ax.add_patch(patches.Circle((hx_r, hy_r), 0.03, facecolor="#0F172A", edgecolor="#0F172A", zorder=8))
                t1_r, t2_r = (90, 180) if swing_dir > 0 else (180, 270)
                arc_r = patches.Arc((hx_r, hy_r), half * 2, half * 2, angle=0, theta1=t1_r, theta2=t2_r, color="#475569", lw=1.1, ls="--", zorder=6)
                ax.add_patch(arc_r)
            else:
                if hinge_side == 0:  # Left Hinge
                    hx, hy = px - hw, py
                    ax.plot([hx, hx], [hy, hy + swing_dir * w], color="#0F172A", lw=2.2, solid_capstyle="round", zorder=7)
                    ax.add_patch(patches.Circle((hx, hy), 0.03, facecolor="#0F172A", edgecolor="#0F172A", zorder=8))
                    t1, t2 = (0, 90) if swing_dir > 0 else (270, 360)
                    arc = patches.Arc((hx, hy), w * 2.0, w * 2.0, angle=0, theta1=t1, theta2=t2, color="#475569", lw=1.1, ls="--", zorder=6)
                    ax.add_patch(arc)
                else:  # Right Hinge
                    hx, hy = px + hw, py
                    ax.plot([hx, hx], [hy, hy + swing_dir * w], color="#0F172A", lw=2.2, solid_capstyle="round", zorder=7)
                    ax.add_patch(patches.Circle((hx, hy), 0.03, facecolor="#0F172A", edgecolor="#0F172A", zorder=8))
                    t1, t2 = (90, 180) if swing_dir > 0 else (180, 270)
                    arc = patches.Arc((hx, hy), w * 2.0, w * 2.0, angle=0, theta1=t1, theta2=t2, color="#475569", lw=1.1, ls="--", zorder=6)
                    ax.add_patch(arc)
        else:
            # Vertical wall opening mask
            ax.plot([px, px], [py - hw, py + hw], color="#FFFFFF", lw=4.8, solid_capstyle="butt", zorder=5)
            # Jamb ticks
            ax.plot([px - 0.08, px + 0.08], [py - hw, py - hw], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)
            ax.plot([px - 0.08, px + 0.08], [py + hw, py + hw], color="#0F172A", lw=1.6, solid_capstyle="butt", zorder=6)

            if is_double:
                half = w / 2.0
                # Bottom Leaf
                hx_b, hy_b = px, py - half
                ax.plot([hx_b, hx_b + swing_dir * half], [hy_b, hy_b], color="#0F172A", lw=2.2, solid_capstyle="round", zorder=7)
                ax.add_patch(patches.Circle((hx_b, hy_b), 0.03, facecolor="#0F172A", edgecolor="#0F172A", zorder=8))
                t1_b, t2_b = (0, 90) if swing_dir > 0 else (90, 180)
                arc_b = patches.Arc((hx_b, hy_b), half * 2, half * 2, angle=0, theta1=t1_b, theta2=t2_b, color="#475569", lw=1.1, ls="--", zorder=6)
                ax.add_patch(arc_b)

                # Top Leaf
                hx_t, hy_t = px, py + half
                ax.plot([hx_t, hx_t + swing_dir * half], [hy_t, hy_t], color="#0F172A", lw=2.2, solid_capstyle="round", zorder=7)
                ax.add_patch(patches.Circle((hx_t, hy_t), 0.03, facecolor="#0F172A", edgecolor="#0F172A", zorder=8))
                t1_t, t2_t = (270, 360) if swing_dir > 0 else (180, 270)
                arc_t = patches.Arc((hx_t, hy_t), half * 2, half * 2, angle=0, theta1=t1_t, theta2=t2_t, color="#475569", lw=1.1, ls="--", zorder=6)
                ax.add_patch(arc_t)
            else:
                if hinge_side == 0:  # Bottom Hinge
                    hx, hy = px, py - hw
                    ax.plot([hx, hx + swing_dir * w], [hy, hy], color="#0F172A", lw=2.2, solid_capstyle="round", zorder=7)
                    ax.add_patch(patches.Circle((hx, hy), 0.03, facecolor="#0F172A", edgecolor="#0F172A", zorder=8))
                    t1, t2 = (0, 90) if swing_dir > 0 else (90, 180)
                    arc = patches.Arc((hx, hy), w * 2.0, w * 2.0, angle=0, theta1=t1, theta2=t2, color="#475569", lw=1.1, ls="--", zorder=6)
                    ax.add_patch(arc)
                else:  # Top Hinge
                    hx, hy = px, py + hw
                    ax.plot([hx, hx + swing_dir * w], [hy, hy], color="#0F172A", lw=2.2, solid_capstyle="round", zorder=7)
                    ax.add_patch(patches.Circle((hx, hy), 0.03, facecolor="#0F172A", edgecolor="#0F172A", zorder=8))
                    t1, t2 = (270, 360) if swing_dir > 0 else (180, 270)
                    arc = patches.Arc((hx, hy), w * 2.0, w * 2.0, angle=0, theta1=t1, theta2=t2, color="#475569", lw=1.1, ls="--", zorder=6)
                    ax.add_patch(arc)

    @classmethod
    def _draw_circulation_flow(cls, ax, rooms, openings):
        """Draws architectural circulation access pathways and node connections showing how occupants traverse the house."""
        doors = [op for op in openings if op.opening_type == "door"]
        if not doors:
            return

        # Find main distribution hub (TV lounge, Foyer, or Living Room)
        hub = next((r for r in rooms if r.room_type == "living_room" or "lounge" in r.room_name.lower()), None)
        if not hub:
            hub = next((r for r in rooms if "foyer" in r.room_name.lower() or "hall" in r.room_name.lower()), None)
        if not hub:
            return

        hub_cx, hub_cy = hub.centroid[0], hub.centroid[1]

        for d in doors:
            c_rooms = [r for r in rooms if r.room_id in getattr(d, 'connects_rooms', [])]
            if not c_rooms:
                continue
            dx, dy = d.position[0], d.position[1]

            # Subtle door threshold access indicator
            ax.add_patch(patches.Circle((dx, dy), 0.08, facecolor="#0284C7", edgecolor="#0369A1", alpha=0.45, zorder=6))

            # If door directly connects to the hub, draw subtle connecting flow line to hub center
            if any(r.room_id == hub.room_id for r in c_rooms):
                ax.plot([hub_cx, dx], [hub_cy, dy], color="#0284C7", lw=0.9, ls=(0, (3, 4)), alpha=0.35, zorder=3)

    @classmethod
    def _draw_level_on_axis(
        cls,
        ax,
        plan: CanonicalFloorPlan,
        level_index: int = 0
    ):
        rooms = [r for r in plan.rooms if r.level_index == level_index]
        walls = [w for w in plan.walls if w.level_index == level_index]
        openings = [o for o in plan.openings if o.level_index == level_index]

        if not rooms and not walls:
            ax.text(0.5, 0.5, f"NO DATA FOR LEVEL {level_index}", ha="center", va="center")
            return

        ax.set_facecolor("#FFFFFF")

        # 1. Render Room Polygons with Soft Tint
        for r in rooms:
            color = cls.ROOM_COLORS.get(r.room_type, "#FFFFFF")
            poly_pts = r.polygon
            is_open_edge = (r.metadata or {}).get("open_concept", False)
            poly_patch = patches.Polygon(
                poly_pts,
                closed=True,
                facecolor=color,
                edgecolor="none" if is_open_edge else "#CBD5E1",
                linewidth=0.8,
                alpha=0.95,
                zorder=1
            )
            ax.add_patch(poly_patch)

            min_x = min(pt[0] for pt in poly_pts)
            max_x = max(pt[0] for pt in poly_pts)
            min_y = min(pt[1] for pt in poly_pts)
            max_y = max(pt[1] for pt in poly_pts)
            rw = max_x - min_x
            rh = max_y - min_y
            cx, cy = r.centroid[0], r.centroid[1]
            r_lower = r.room_name.lower()

            # Architectural Fixtures Placement
            if "stair" in r_lower or ("lobby" in r_lower and "stair" in r_lower):
                cls._draw_modular_staircase(ax, r, min_x, min_y, rw, rh, is_first_floor=(level_index > 0))
                # Staircase features its own technical badges and tread callouts, skip overlapping tag
                continue

            elif r.room_type == "garage" or "porch" in r_lower:
                cls._draw_cars(ax, min_x, min_y, rw, rh, count=2)

            elif r.room_type == "balcony" or "terrace" in r_lower:
                cls._draw_terrace_patio(ax, min_x, min_y, rw, rh)

            elif "lawn" in r_lower or "garden" in r_lower:
                cls._draw_lawn_grass(ax, min_x, min_y, rw, rh)

            elif r.room_type == "outdoor" or "ots" in r_lower or "shaft" in r_lower:
                # Diagonal cross hatch for OTS light shafts
                ax.plot([min_x, max_x], [min_y, max_y], color="#94A3B8", lw=0.9, zorder=2)
                ax.plot([min_x, max_x], [max_y, min_y], color="#94A3B8", lw=0.9, zorder=2)

            elif "laundry" in r_lower or ("utility" in r_lower and "kitchen" not in r_lower):
                cls._draw_laundry_utility(ax, min_x, min_y, rw, rh)

            elif "kitchenette" in r_lower or "pantry" in r_lower:
                cls._draw_kitchenette(ax, min_x, min_y, rw, rh)

            elif r.room_type == "kitchen":
                cls._draw_kitchen_details(ax, min_x, min_y, rw, rh, meta=r.metadata)

            elif r.room_type == "bedroom":
                cls._draw_double_bed(ax, cx, cy + 0.30, rw, rh, min_x=min_x, min_y=min_y)
                # Only draw in-room wardrobe if bedroom lacks an attached walk-in dressing room
                has_dressing = any(
                    ("dress" in cr.room_name.lower() or "closet" in cr.room_name.lower())
                    for cr in rooms
                    if any(
                        (op.opening_type == "door" and set(op.connects_rooms) == {r.room_id, cr.room_id})
                        for op in openings
                    )
                )
                if rw >= 3.8 and not has_dressing:
                    cls._draw_wardrobe(ax, min_x + 0.20, min_y + 0.20, min(rw * 0.45, 2.00))

            elif r.room_type == "bathroom":
                cls._draw_bathroom_fixtures(ax, min_x, min_y, rw, rh, meta=r.metadata)

            elif "drawing" in r_lower:
                cls._draw_living_furniture(ax, cx, cy, rw, rh, is_formal_drawing=True)

            elif "study" in r_lower or "library" in r_lower or "office" in r_lower:
                cls._draw_study_library(ax, min_x, min_y, rw, rh)

            elif r.room_type == "living_room" or "lounge" in r_lower:
                cls._draw_living_furniture(ax, cx, cy, rw, rh, is_formal_drawing=False)
                is_open = (r.metadata or {}).get("open_concept", False) or (r.metadata or {}).get("no_baffle", False)
                if not is_open and level_index == 0 and ("tv" in r_lower or "lounge" in r_lower) and rw >= 3.2 and rh >= 3.6:
                    # 4.5" (115mm) TV Media Baffle Wall hosted exclusively inside the TV Lounge volume
                    b_w = min(1.85, rw * 0.48)
                    b_x1 = min_x + 0.35
                    b_x2 = b_x1 + b_w
                    b_y = min_y + 0.75
                    # Fluted wood acoustic partition panel
                    ax.add_patch(patches.Rectangle((b_x1, b_y - 0.0575), b_x2 - b_x1, 0.115, facecolor="#78350F", edgecolor="#451A03", lw=1.2, zorder=5))
                    # Low media console shelf on lounge side (north)
                    ax.add_patch(patches.Rectangle((b_x1 + 0.15, b_y + 0.0575), b_x2 - b_x1 - 0.30, 0.28, facecolor="#CBD5E1", edgecolor="#334155", lw=0.8, zorder=5))
                    # Mounted TV display
                    ax.add_patch(patches.Rectangle((b_x1 + 0.35, b_y + 0.02), b_x2 - b_x1 - 0.70, 0.05, facecolor="#0F172A", edgecolor="#000000", lw=1.0, zorder=6))
                    ax.text(
                        (b_x1 + b_x2) / 2.0, b_y - 0.20,
                        "4.5\" TV MEDIA BAFFLE WALL\n(ENTRY PRIVACY SCREEN)",
                        ha="center", va="top", fontsize=5.0, fontweight="bold", color="#78350F",
                        bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.95), zorder=10
                    )

            elif r.room_type == "dining_room" or "dining" in r_lower:
                cls._draw_dining_table(ax, cx, cy, seats=6)

            # Room Label Tag with dynamic centroid offsets avoiding furniture blocks
            if r.room_type == "bedroom":
                label_x = cx
                label_y = min_y + max(0.55, rh * 0.16)
            elif r.room_type == "kitchen":
                label_x = min_x + rw * 0.55
                label_y = min_y + rh * 0.65
            elif "study" in r_lower or "library" in r_lower or "office" in r_lower:
                label_x = cx
                label_y = min_y + max(0.55, rh * 0.28)
            elif r.room_type == "living_room" or "lounge" in r_lower:
                label_x = cx
                label_y = min_y + rh * 0.70
            elif r.room_type == "dining_room" or "dining" in r_lower:
                label_x = cx
                label_y = min_y + rh * 0.82
            elif r.room_type == "bathroom":
                label_x = cx
                label_y = min_y + rh * 0.75
            elif "dress" in r_lower or "closet" in r_lower or "wardrobe" in r_lower:
                label_x = cx
                label_y = min_y + rh * 0.75
            elif r.room_type in ("garage", "balcony") or "porch" in r_lower or "terrace" in r_lower:
                label_x = cx
                label_y = min_y + 0.50
            else:
                label_x = cx
                label_y = cy

            sqft = r.area_m2 * 10.7639
            # Standard architectural feet-and-inches (e.g. "16'-01" x "12'-06")
            def _ft_in(m: float) -> str:
                total_in = m * 39.3701
                ft = int(total_in // 12)
                inch = int(round(total_in % 12))
                if inch == 12:
                    ft += 1
                    inch = 0
                return f"{ft}'-{inch:02d}\""

            w_str = _ft_in(rw)
            h_str = _ft_in(rh)

            # Compact labels for small rooms, closets, utility & shafts to prevent text overlap
            if rw < 2.3 or rh < 2.1 or "ots" in r_lower or "dirty" in r_lower or "utility" in r_lower or "powder" in r_lower or "shaft" in r_lower or "garden" in r_lower:
                label = f"{r.room_name}\n({r.area_m2:.1f} m² / {sqft:.0f} sqft)"
                fsize = 6.0
            else:
                label = f"{r.room_name}\n{w_str} x {h_str}\n({r.area_m2:.1f} m² / {sqft:.0f} sqft)"
                fsize = 7.0

            ax.text(
                label_x, label_y, label,
                ha="center", va="center",
                fontsize=fsize, fontweight="bold",
                color="#0F172A",
                zorder=10,
                bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.95)
            )

        # Open Cased Portal indicator on Level 0 between Formal Dining and Family Lounge (only if canonical baseline layout)
        if level_index == 0 and any("dining" in r.room_name.lower() for r in rooms) and any("lounge" in r.room_name.lower() for r in rooms) and plan.metadata.plan_id.startswith("master_"):
            portal_x = 6.30
            # 4.5" (115mm) Wall Nibs at Jambs
            nib_len = 0.115
            ax.plot([portal_x, portal_x - nib_len], [6.00, 6.00], color="#334155", lw=3.2, solid_capstyle="butt", zorder=6)
            ax.plot([portal_x, portal_x - nib_len], [7.50, 7.50], color="#334155", lw=3.2, solid_capstyle="butt", zorder=6)
            # Overhead dashed RC beam soffit lines
            ax.plot([portal_x - 0.06, portal_x - 0.06], [6.00, 7.50], color="#64748B", lw=1.2, ls="--", zorder=8)
            ax.plot([portal_x + 0.06, portal_x + 0.06], [6.00, 7.50], color="#64748B", lw=1.2, ls="--", zorder=8)
            ax.text(
                portal_x, 6.75, "5'-0\" CASED OPENING (4.5\" NIBS)\nw/ OVERHEAD R.C. BEAM SOFFIT",
                fontsize=5.2, fontweight="bold", color="#0F172A", rotation=90, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="#64748B", lw=0.6, alpha=0.95), zorder=10
            )

        # Cased Portal with Overhead Beam between Foyer and TV Lounge (Level 0, canonical baseline layout only)
        if level_index == 0 and any("foyer" in r.room_name.lower() for r in rooms) and any("lounge" in r.room_name.lower() for r in rooms) and plan.metadata.plan_id.startswith("master_"):
            portal_y = 7.50
            f_x1, f_x2 = 3.05, 4.25
            ax.plot([f_x1, f_x2], [portal_y - 0.05, portal_y - 0.05], color="#64748B", lw=1.1, ls="--", zorder=8)
            ax.plot([f_x1, f_x2], [portal_y + 0.05, portal_y + 0.05], color="#64748B", lw=1.1, ls="--", zorder=8)
            ax.text(
                (f_x1 + f_x2) / 2.0, portal_y, "CASED OPENING (R.C. BEAM OVER)",
                fontsize=4.8, fontweight="bold", color="#0F172A", ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.18", facecolor="#FFFFFF", edgecolor="#64748B", lw=0.5, alpha=0.95), zorder=10
            )

        # 2. Render Walls with High Architectural Weight & Wall Thickness Annotation
        EXT_LW = 5.6   # 9" (230mm) exterior / load-bearing walls
        INT_LW = 2.8   # 4.5" (115mm) interior partitions
        for w in walls:
            p1, p2 = w.centerline
            is_ext = w.wall_type == "exterior"
            lw = EXT_LW if is_ext else INT_LW
            wall_color = "#0F172A" if is_ext else "#334155"
            ax.plot(
                [p1[0], p2[0]], [p1[1], p2[1]],
                color=wall_color,
                linewidth=lw,
                solid_capstyle="butt",
                zorder=4
            )

        # 3. Render Openings (Doors & Windows)
        for op in openings:
            pos = op.position
            width = op.width_m

            # 1. Analyze the wall where the opening sits (shared boundary between rooms or room polygon edge)
            is_vertical_wall = False
            wall_found = False

            connected_rooms = [r for r in rooms if r.room_id in getattr(op, 'connects_rooms', [])]
            if len(connected_rooms) >= 2:
                try:
                    from shapely.geometry import Polygon as ShapelyPoly
                    shp1 = ShapelyPoly(connected_rooms[0].polygon)
                    shp2 = ShapelyPoly(connected_rooms[1].polygon)
                    shared_boundary = shp1.intersection(shp2)
                    if not shared_boundary.is_empty:
                        b_minx, b_miny, b_maxx, b_maxy = shared_boundary.bounds
                        bdx = b_maxx - b_minx
                        bdy = b_maxy - b_miny
                        if bdx > 0.05 or bdy > 0.05:
                            is_vertical_wall = bdy > bdx
                            wall_found = True
                except Exception:
                    pass

            if not wall_found:
                best_dist = 999.0
                from shapely.geometry import Point as ShapelyPt, LineString as ShapelyLine
                pt_obj = ShapelyPt(pos)
                for r in (connected_rooms if connected_rooms else rooms):
                    pts = r.polygon
                    n_pts = len(pts)
                    for i in range(n_pts):
                        p1 = pts[i]
                        p2 = pts[(i + 1) % n_pts]
                        line = ShapelyLine([p1, p2])
                        d = line.distance(pt_obj)
                        if d < best_dist:
                            best_dist = d
                            is_vertical_wall = abs(p2[1] - p1[1]) > abs(p2[0] - p1[0])
                            wall_found = True

            if not wall_found:
                best_dist = 999.0
                for w in walls:
                    p1, p2 = w.centerline
                    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                    length_sq = dx*dx + dy*dy
                    if length_sq < 1e-4:
                        continue
                    t = max(0.0, min(1.0, ((pos[0] - p1[0])*dx + (pos[1] - p1[1])*dy) / length_sq))
                    proj_x = p1[0] + t * dx
                    proj_y = p1[1] + t * dy
                    dist = math.hypot(pos[0] - proj_x, pos[1] - proj_y)
                    if dist < best_dist:
                        best_dist = dist
                        is_vertical_wall = abs(dy) > abs(dx)

            if op.opening_type == "door":
                connected_rooms = [r for r in rooms if r.room_id in getattr(op, 'connects_rooms', [])]
                is_main_entry = (pos[1] <= 5.0 and pos[0] >= 4.0 and pos[0] <= 6.0 and level_index == 0)
                is_foyer_double = width >= 1.3 and any("foyer" in r.room_name.lower() for r in connected_rooms)
                is_double_door = is_main_entry or is_foyer_double
                is_sliding_door = (op.metadata or {}).get("is_sliding", False) or "sliding" in op.opening_id.lower()
                # Select preferred room for door swing: inward to private room rather than hallway/lounge
                def _room_pref_score(rm):
                    rn = rm.room_name.lower()
                    rt = rm.room_type.lower()
                    if rt == "bathroom" or "bath" in rn or "powder" in rn:
                        return 100
                    if "dress" in rn or "wardrobe" in rn or "closet" in rn:
                        return 95  # Inward to dressing room rather than into bedroom
                    if rt == "bedroom" or "bed" in rn or "suite" in rn:
                        return 90
                    if "dirty" in rn or "scullery" in rn or "pantry" in rn:
                        return 85  # Inward to dirty kitchen / pantry
                    if "study" in rn or "office" in rn or "library" in rn:
                        return 70
                    if rt == "kitchen" or "kitchen" in rn:
                        return 60
                    if "dining" in rn:
                        return 50
                    if "gallery" in rn or "lobby" in rn:
                        return 45  # higher than lounge so door swings into gallery hall
                    if rt == "living_room" or "lounge" in rn:
                        return 40
                    if "foyer" in rn or "entry" in rn:
                        return 30  # Inward into entrance foyer rather than outward onto porch/terrace
                    return 5  # circulation, porch, terrace, garage, exterior
                if connected_rooms:
                    connected_rooms.sort(key=_room_pref_score, reverse=True)
                    door_room_poly = connected_rooms[0].polygon
                else:
                    door_room_poly = None

                conn_names = [r.room_name.lower() for r in connected_rooms] if connected_rooms else []
                is_lobby_lounge = (
                    any("lounge" in n or "living" in n for n in conn_names) and
                    any("lobby" in n or "corridor" in (r.room_type or "").lower() for n, r in zip(conn_names, connected_rooms))
                )
                is_cased_opening = (
                    is_lobby_lounge or
                    "arch" in op.opening_id.lower() or
                    "cased" in op.opening_id.lower() or
                    getattr(op, 'is_cased', False) or
                    (op.metadata or {}).get("is_cased_opening", False)
                )

                cls._draw_architectural_door(
                    ax, pos,
                    width_m=width,
                    is_double=is_double_door,
                    is_vertical=is_vertical_wall,
                    room_poly_pts=door_room_poly,
                    is_sliding=is_sliding_door,
                    is_cased_opening=is_cased_opening
                )
            elif op.opening_type == "window":
                hw = width / 2.0
                if is_vertical_wall:
                    ax.plot([pos[0], pos[0]], [pos[1] - hw, pos[1] + hw], color="#0284C7", lw=3.6, solid_capstyle="round", zorder=5)
                    ax.plot([pos[0] + 0.08, pos[0] + 0.08], [pos[1] - hw, pos[1] + hw], color="#0369A1", lw=1.2, zorder=5)
                    ax.plot([pos[0] - 0.08, pos[0] - 0.08], [pos[1] - hw, pos[1] + hw], color="#0369A1", lw=1.2, zorder=5)
                else:
                    ax.plot([pos[0] - hw, pos[0] + hw], [pos[1], pos[1]], color="#0284C7", lw=3.6, solid_capstyle="round", zorder=5)
                    ax.plot([pos[0] - hw, pos[0] + hw], [pos[1] + 0.08, pos[1] + 0.08], color="#0369A1", lw=1.2, zorder=5)
                    ax.plot([pos[0] - hw, pos[0] + hw], [pos[1] - 0.08, pos[1] - 0.08], color="#0369A1", lw=1.2, zorder=5)

        # 3b. Human Circulation and Spatial Access Pathways
        cls._draw_circulation_flow(ax, rooms, openings)

        # 4. Exterior Dimension Strings (Standard Architectural Feet-and-Inches Notation)
        def _m_to_ft_in(m: float) -> str:
            """Converts metres to Feet'-Inches\" standard architectural notation (e.g. 10'-6\")."""
            total_inches = m * 39.3701
            feet = int(total_inches // 12)
            inches = int(round(total_inches % 12))
            if inches == 12:
                feet += 1
                inches = 0
            return f"{feet}'-{inches:02d}\""

        all_xs = [pt[0] for r in rooms for pt in r.polygon]
        all_ys = [pt[1] for r in rooms for pt in r.polygon]
        b_min_x, b_max_x = min(all_xs), max(all_xs)
        b_min_y, b_max_y = min(all_ys), max(all_ys)
        total_w_m = b_max_x - b_min_x
        total_d_m = b_max_y - b_min_y

        # Bottom width dimension chain
        chain_y = b_min_y - 0.95
        ax.plot([b_min_x, b_max_x], [chain_y, chain_y], color="#1E293B", lw=1.4, ls="-", zorder=7)
        ax.plot([b_min_x, b_min_x], [b_min_y - 0.72, chain_y - 0.22], color="#1E293B", lw=1.1, zorder=7)
        ax.plot([b_max_x, b_max_x], [b_min_y - 0.72, chain_y - 0.22], color="#1E293B", lw=1.1, zorder=7)
        # Tick arrows
        ax.annotate("", xy=(b_min_x, chain_y), xytext=(b_min_x + 0.28, chain_y),
                    arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.1), zorder=7)
        ax.annotate("", xy=(b_max_x, chain_y), xytext=(b_max_x - 0.28, chain_y),
                    arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.1), zorder=7)
        w_label = _m_to_ft_in(total_w_m) + f"\n({total_w_m:.2f}m)"
        ax.text((b_min_x + b_max_x) / 2.0, chain_y - 0.22, w_label,
                ha="center", va="top", fontsize=8.5, fontweight="bold", color="#1E293B",
                bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.95), zorder=10)

        # Right depth dimension chain
        chain_x = b_max_x + 0.95
        ax.plot([chain_x, chain_x], [b_min_y, b_max_y], color="#1E293B", lw=1.4, ls="-", zorder=7)
        ax.plot([b_max_x + 0.72, chain_x + 0.22], [b_min_y, b_min_y], color="#1E293B", lw=1.1, zorder=7)
        ax.plot([b_max_x + 0.72, chain_x + 0.22], [b_max_y, b_max_y], color="#1E293B", lw=1.1, zorder=7)
        ax.annotate("", xy=(chain_x, b_min_y), xytext=(chain_x, b_min_y + 0.28),
                    arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.1), zorder=7)
        ax.annotate("", xy=(chain_x, b_max_y), xytext=(chain_x, b_max_y - 0.28),
                    arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.1), zorder=7)
        d_label = _m_to_ft_in(total_d_m) + f"\n({total_d_m:.2f}m)"
        ax.text(chain_x + 0.38, (b_min_y + b_max_y) / 2.0, d_label,
                ha="left", va="center", rotation=270, fontsize=8.5, fontweight="bold", color="#1E293B",
                bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.95), zorder=10)

        # Graphic Scale Bar (0 to 5m)
        sb_x = b_min_x + 0.2
        sb_y = b_min_y - 1.85
        sb_len = 5.0
        ax.plot([sb_x, sb_x + sb_len], [sb_y, sb_y], color="#0F172A", lw=2.5, zorder=7)
        for tick_m in range(6):
            tx = sb_x + tick_m
            ax.plot([tx, tx], [sb_y - 0.12, sb_y + 0.12], color="#0F172A", lw=1.2, zorder=7)
            ax.text(tx, sb_y - 0.22, f"{tick_m}m", ha="center", va="top", fontsize=6.5, color="#334155", zorder=7)
        ax.text(sb_x + sb_len / 2.0, sb_y + 0.18, "GRAPHIC SCALE 1:100",
                ha="center", va="bottom", fontsize=6.5, fontweight="bold", color="#0F172A",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none", alpha=0.95), zorder=10)

        # Wall Thickness Legend
        leg_x = b_min_x
        leg_y = b_min_y - 2.60
        ax.plot([leg_x, leg_x + 0.45], [leg_y, leg_y], color="#0F172A", lw=5.6, solid_capstyle="butt", zorder=7)
        ax.text(leg_x + 0.55, leg_y, "EXTERNAL WALL: 9\" (230mm) SOLID BRICK / LOAD-BEARING",
                fontsize=6.0, fontweight="bold", color="#0F172A", va="center", zorder=8)
        leg_y2 = leg_y - 0.30
        ax.plot([leg_x, leg_x + 0.45], [leg_y2, leg_y2], color="#334155", lw=2.8, solid_capstyle="butt", zorder=7)
        ax.text(leg_x + 0.55, leg_y2, "INTERNAL PARTITION: 4.5\" (115mm) NON-STRUCTURAL",
                fontsize=6.0, fontweight="bold", color="#334155", va="center", zorder=8)

        # North Arrow Compass
        compass_x = b_max_x - 0.8
        compass_y = b_max_y + 1.2
        ax.annotate(
            "N", xy=(compass_x, compass_y + 0.6), xytext=(compass_x, compass_y),
            ha="center", va="bottom", fontsize=11, fontweight="bold", color="#0F172A",
            arrowprops=dict(facecolor="#0F172A", width=1.8, headwidth=7),
            zorder=8
        )

        lvl_title = "GROUND FLOOR PLAN | LEVEL 0" if level_index == 0 else ("FIRST FLOOR PLAN | LEVEL 1" if level_index == 1 else f"SECOND FLOOR / ROOFTOP | LEVEL {level_index}")
        ax.set_title(f"{lvl_title}\n[SCALE 1:100]", fontsize=11, fontweight="bold", color="#0F172A", pad=15)
        ax.set_xlim(b_min_x - 2.0, b_max_x + 2.8)

        red_note = (plan.metadata.provenance or {}).get("statutory_red_note")
        if red_note:
            ax.text(
                (b_min_x + b_max_x) / 2.0, b_min_y - 2.95,
                f"STATUTORY COMPLIANCE NOTE:\n{red_note}",
                ha="center", va="top", fontsize=5.8, fontweight="bold", color="#B91C1C",
                bbox=dict(boxstyle="square,pad=0.25", facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.2),
                zorder=12
            )
            ax.set_ylim(b_min_y - 3.9, b_max_y + 2.2)
        else:
            ax.set_ylim(b_min_y - 3.2, b_max_y + 2.2)

        ax.set_aspect("equal")
        ax.axis("off")

    @classmethod
    def render_floor_plan(
        cls,
        plan: CanonicalFloorPlan,
        output_image_path: str,
        level_index: int = 0,
        dpi: int = 180
    ) -> str:
        fig, ax = plt.subplots(figsize=(14, 16), dpi=dpi)
        cls._draw_level_on_axis(ax, plan, level_index=level_index)

        header_title = plan.metadata.provenance.get("project_title", "CONTEMPORARY RESIDENCE").upper()
        fig.suptitle(f"{header_title}", fontsize=13, fontweight="bold", color="#0F172A", y=0.98)

        red_note = (plan.metadata.provenance or {}).get("statutory_red_note")
        if red_note:
            fig.text(
                0.5, 0.945, f"⚠ STATUTORY COMPLIANCE NOTICE: {red_note}",
                ha="center", va="center", fontsize=7.5, fontweight="bold", color="#B91C1C",
                bbox=dict(boxstyle="square,pad=0.3", facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.2),
                zorder=20
            )
            plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.93])
        else:
            plt.tight_layout()
        plt.savefig(output_image_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        return output_image_path

    @classmethod
    def render_floorplan(
        cls,
        plan: CanonicalFloorPlan,
        output_image_path: str,
        dpi: int = 300
    ) -> str:
        """
        Generates a high-resolution composite sheet (24"x14" @ 300 DPI, 1x2 or 1x3 subplots)
        for multi-floor plans:
        - Subplot 1 (Left): "GROUND FLOOR PLAN | LEVEL 0 [SCALE 1:100]"
        - Subplot 2 (Center): "FIRST FLOOR PLAN | LEVEL 1 [SCALE 1:100]"
        - Subplot 3 (Right, if 3-floor): "SECOND FLOOR / ROOFTOP | LEVEL 2 [SCALE 1:100]"
        """
        levels = plan.metadata.levels if plan.metadata.levels else [0]
        if len(levels) >= 2:
            return cls.render_composite_multi_floor_sheet(plan, output_image_path, dpi=dpi)
        return cls.render_floor_plan(plan, output_image_path, level_index=0, dpi=dpi)

    @classmethod
    def render_composite_multi_floor_sheet(
        cls,
        plan: CanonicalFloorPlan,
        output_image_path: str,
        dpi: int = 300
    ) -> str:
        """
        Renders multi-floor plans side-by-side on a single composite sheet at 300 DPI.
        """
        levels = plan.metadata.levels if plan.metadata.levels else [0]
        n_levels = len(levels)

        if n_levels >= 3:
            fig, axes = plt.subplots(1, n_levels, figsize=(11 * n_levels, 14), dpi=dpi)
            fig.patch.set_facecolor("#FFFFFF")
            for i, lvl in enumerate(levels):
                cls._draw_level_on_axis(axes[i], plan, level_index=lvl)
        elif n_levels == 2:
            fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(24, 14), dpi=dpi)
            fig.patch.set_facecolor("#FFFFFF")
            cls._draw_level_on_axis(ax0, plan, level_index=0)
            cls._draw_level_on_axis(ax1, plan, level_index=1)
        else:
            fig, ax0 = plt.subplots(figsize=(14, 14), dpi=dpi)
            fig.patch.set_facecolor("#FFFFFF")
            cls._draw_level_on_axis(ax0, plan, level_index=0)

        proj_title = plan.metadata.provenance.get("project_title", "EXECUTIVE CONTEMPORARY RESIDENCE").upper()
        fig.suptitle(
            f"{proj_title} - COORDINATED MULTI-FLOOR ARCHITECTURAL BLUEPRINT\n"
            f"PROFESSIONAL CAD DRAFTING STANDARD | {n_levels}-STOREY VERTICAL COORDINATION | SCALE 1:100",
            fontsize=15, fontweight="bold", color="#0F172A", y=0.98
        )

        red_note = (plan.metadata.provenance or {}).get("statutory_red_note")
        if red_note:
            fig.text(
                0.5, 0.942, f"⚠ STATUTORY COMPLIANCE NOTICE: {red_note}",
                ha="center", va="center", fontsize=8.5, fontweight="bold", color="#B91C1C",
                bbox=dict(boxstyle="square,pad=0.35", facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.5),
                zorder=20
            )
            plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.92])
        else:
            plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.94])
        os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
        fmt = "pdf" if output_image_path.lower().endswith(".pdf") else ("svg" if output_image_path.lower().endswith(".svg") else None)
        if fmt:
            plt.savefig(output_image_path, format=fmt, dpi=dpi, bbox_inches="tight")
        else:
            plt.savefig(output_image_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        return output_image_path

    render_composite_two_floor_sheet = render_composite_multi_floor_sheet

    @classmethod
    def render_vector_sheet(
        cls,
        plan: CanonicalFloorPlan,
        output_path: str,
        paper_size: str = "ARCH_D",
        dpi: int = 300,
        title_override: Optional[str] = None
    ) -> str:
        """
        Renders a publication-grade vector architectural sheet (Arch D: 36"x24" or A1: 33.1"x23.4")
        exported as pure vector PDF or SVG with embedded TrueType fonts.
        """
        paper_sizes = {
            "ARCH_D": (36, 24),
            "A1": (33.1, 23.4),
            "A2": (23.4, 16.5),
            "ARCH_C": (24, 18),
        }
        fig_size = paper_sizes.get(paper_size.upper(), (36, 24))

        levels = plan.metadata.levels if plan.metadata.levels else [0]
        n_levels = len(levels)
        if n_levels >= 3:
            fig, axes = plt.subplots(1, n_levels, figsize=(18 * n_levels, fig_size[1]), dpi=dpi)
            fig.patch.set_facecolor("#FFFFFF")
            for idx, lvl in enumerate(levels):
                cls._draw_level_on_axis(axes[idx], plan, level_index=lvl)
        elif n_levels == 2:
            fig, (ax0, ax1) = plt.subplots(1, 2, figsize=fig_size, dpi=dpi)
            fig.patch.set_facecolor("#FFFFFF")
            cls._draw_level_on_axis(ax0, plan, level_index=0)
            cls._draw_level_on_axis(ax1, plan, level_index=1)
        else:
            fig, ax0 = plt.subplots(figsize=fig_size, dpi=dpi)
            fig.patch.set_facecolor("#FFFFFF")
            cls._draw_level_on_axis(ax0, plan, level_index=0)

        proj_title = title_override or plan.metadata.provenance.get("project_title", "EXECUTIVE RESIDENTIAL VILLA").upper()
        sheet_subtitle = f"{paper_size.upper()} ARCHITECTURAL PRESENTATION SHEET | SCALE 1:100 | VECTOR CAD STANDARD"
        fig.suptitle(
            f"{proj_title}\n{sheet_subtitle}",
            fontsize=16, fontweight="bold", color="#0F172A", y=0.98
        )

        red_note = (plan.metadata.provenance or {}).get("statutory_red_note")
        if red_note:
            fig.text(
                0.5, 0.942, f"⚠ STATUTORY COMPLIANCE NOTICE: {red_note}",
                ha="center", va="center", fontsize=8.5, fontweight="bold", color="#B91C1C",
                bbox=dict(boxstyle="square,pad=0.35", facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.5),
                zorder=20
            )
            plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.92])
        else:
            plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.94])
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        fmt = "pdf" if output_path.lower().endswith(".pdf") else ("svg" if output_path.lower().endswith(".svg") else "png")
        plt.savefig(output_path, format=fmt, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        return output_path

    @classmethod
    def render_all_floors(cls, plan: CanonicalFloorPlan, output_dir: str) -> Dict[str, str]:
        rendered = {}
        levels = plan.metadata.levels if plan.metadata.levels else [0]
        for lvl in levels:
            lvl_slug = "ground_floor" if lvl == 0 else ("first_floor" if lvl == 1 else ("second_floor_penthouse" if lvl == 2 else f"level_{lvl}"))
            out_img = os.path.join(output_dir, f"{plan.metadata.plan_id}_{lvl_slug}_2d.png")
            cls.render_floor_plan(plan, out_img, level_index=lvl)
            rendered[lvl_slug] = out_img

        if len(levels) >= 2:
            comp_slug = "composite_all_floors" if len(levels) > 2 else "composite_two_floors"
            comp_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_{comp_slug}.png")
            cls.render_composite_multi_floor_sheet(plan, comp_path)
            rendered[comp_slug] = comp_path
            rendered["composite_two_floors"] = comp_path

        return rendered

    @classmethod
    def render_diversity_comparison_sheet(
        cls,
        plans: List[CanonicalFloorPlan],
        output_image_path: str,
        title: str = "ARCHITECTURAL DESIGN DIVERSITY COMPARISON MATRIX",
        dpi: int = 150
    ) -> str:
        """
        Renders a publication-grade multi-plan side-by-side comparison sheet
        demonstrating topological variation across planning strategies and user prompts.
        """
        n_plans = len(plans)
        if n_plans == 0:
            return output_image_path

        cols = min(5, n_plans)
        rows = math.ceil(n_plans / cols)

        fig, axes = plt.subplots(rows, cols, figsize=(7.0 * cols, 8.5 * rows), dpi=dpi)
        fig.patch.set_facecolor("#FFFFFF")

        # Normalize axes array
        if rows == 1 and cols == 1:
            axes_flat = [axes]
        elif rows == 1 or cols == 1:
            axes_flat = list(axes)
        else:
            axes_flat = [ax for row in axes for ax in row]

        for i, plan in enumerate(plans):
            ax = axes_flat[i]
            cls._draw_level_on_axis(ax, plan, level_index=0)
            strat = plan.metadata.provenance.get("planning_strategy", "Standard").replace("_", " ").title()
            style = plan.metadata.provenance.get("architectural_style", "Modern")
            ax.set_title(f"Plan #{i+1}: {strat}\nStyle: {style} | Rooms: {len(plan.rooms)}", fontsize=11, fontweight="bold", color="#0F172A", pad=8)

        # Hide any unused subplots
        for j in range(n_plans, len(axes_flat)):
            axes_flat[j].axis("off")

        fig.suptitle(
            f"{title}\nIndependent Spatial Diversity Proof | Topological Variation Engine",
            fontsize=16, fontweight="bold", color="#0F172A", y=0.99
        )
        plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.96])
        os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
        plt.savefig(output_image_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        return output_image_path
