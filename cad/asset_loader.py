"""
CAD Asset Loader & 1:100 Architectural Vector Block Engine.
Ingests real CAD vector assets and reference icon sheets from local storage:
  "furniture ,car,stairs"
Provides authentic, publication-standard 1:100 scale CAD blocks for:
- Vehicles: Passenger Sedans & Luxury SUVs matching top-view outline reference images
- Staircases: Dog-leg, floating, L-shaped - with equal treads, stringers, arrows
- Living/Drawing Room: 3-seat sofa + armchairs + coffee table + credenza
- TV Lounge: L-shaped sectional + coffee table + TV console
- Dining: 8-seater table with individual chairs (backrest rail style)
- Kitchen: U-shaped counters + hob + double sink + fridge + island + bar stools
- Bathrooms: Proper WC (cistern+bowl+seat), vanity basin, bathtub, shower
- Bedrooms: King/queen bed + headboard + pillows + nightstands + bench
All furniture matches the reference images in the "furniture ,car,stairs" folder.
"""

import os
import math
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.lines as lines
import numpy as np


class CADAssetLoader:
    _instance = None
    ASSET_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "furniture ,car,stairs")
    )
    asset_rgba_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CADAssetLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.asset_cache = {}
        self._load_local_assets()

    def _load_local_assets(self):
        """Scans and caches reference raster/vector assets from the local asset directory."""
        if not os.path.exists(self.ASSET_DIR):
            return
        for fname in os.listdir(self.ASSET_DIR):
            fpath = os.path.join(self.ASSET_DIR, fname)
            if not os.path.isfile(fpath) or "copy" in fname:
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in (".jpg", ".jpeg", ".png", ".webp", ".avif"):
                try:
                    im = Image.open(fpath)
                    self.asset_cache[fname] = {
                        "path": fpath, "size": im.size,
                        "format": im.format, "mode": im.mode,
                    }
                    fn_low = fname.lower()
                    cat = None
                    if "sedan" in fn_low or "vehicle" in fn_low:
                        cat = "sedan"
                    elif "stairs" in fn_low or "stair" in fn_low:
                        cat = "stairs"
                    elif "kitchen-floor" in fn_low or "kitchen-set" in fn_low:
                        cat = "kitchen"
                    elif "dining" in fn_low:
                        cat = "dining"
                    elif "living" in fn_low or "big-set" in fn_low:
                        cat = "living"
                    elif "bathroom" in fn_low or "store-vector" in fn_low:
                        cat = "bathroom"
                    if cat and cat not in self.asset_rgba_cache:
                        rgba = im.convert("RGBA")
                        arr = np.array(rgba)
                        white_mask = (arr[:, :, 0] > 235) & (arr[:, :, 1] > 235) & (arr[:, :, 2] > 235)
                        arr[white_mask, 3] = 0
                        self.asset_rgba_cache[cat] = arr
                except Exception:
                    pass

    @classmethod
    def stamp_cad_asset_image(cls, ax, category: str,
                              extent: Tuple[float, float, float, float],
                              alpha: float = 0.25, zorder: int = 2):
        """Disabled to ensure 100% crisp vector architectural rendering without raster image watermarks."""
        return

    # =========================================================================
    # HELPERS
    # =========================================================================

    @classmethod
    def _draw_dining_chair(cls, ax, cx, cy, w=0.44, d=0.42,
                           backside="top", color="#F8FAFC", edge="#78350F", zorder=4):
        """Top-view CAD dining chair with backrest rail on specified side."""
        hw, hd = w / 2, d / 2
        ax.add_patch(patches.FancyBboxPatch(
            (cx - hw, cy - hd), w, d,
            boxstyle="round,pad=0.01,rounding_size=0.07",
            facecolor=color, edgecolor=edge, lw=1.0, zorder=zorder,
        ))
        if backside == "top":
            ax.plot([cx - hw + 0.03, cx + hw - 0.03], [cy + hd, cy + hd],
                    color=edge, lw=2.4, solid_capstyle="round", zorder=zorder + 1)
        elif backside == "bottom":
            ax.plot([cx - hw + 0.03, cx + hw - 0.03], [cy - hd, cy - hd],
                    color=edge, lw=2.4, solid_capstyle="round", zorder=zorder + 1)
        elif backside == "left":
            ax.plot([cx - hw, cx - hw], [cy - hd + 0.03, cy + hd - 0.03],
                    color=edge, lw=2.4, solid_capstyle="round", zorder=zorder + 1)
        elif backside == "right":
            ax.plot([cx + hw, cx + hw], [cy - hd + 0.03, cy + hd - 0.03],
                    color=edge, lw=2.4, solid_capstyle="round", zorder=zorder + 1)

    # =========================================================================
    # 1. VEHICLES
    # =========================================================================

    @classmethod
    def draw_cad_sedan(cls, ax, cx, cy, length_m=4.57, width_m=1.83,
                       rotation_deg=0.0, show_clearance=False):
        """1:100 CAD Passenger Sedan with clean aerodynamic curves, tinted glass, and mirrors."""
        w, l = width_m, length_m
        bx, by = cx - w / 2, cy - l / 2

        # Aerodynamic Car Body with subtle slate tone
        ax.add_patch(patches.FancyBboxPatch(
            (bx, by), w, l,
            boxstyle="round,pad=0.02,rounding_size=0.38",
            facecolor="#F1F5F9", edgecolor="#1E293B", lw=1.6, zorder=4,
        ))
        # Front Bumper & LED Headlights
        ax.plot([bx + 0.12, bx + w - 0.12], [by + l - 0.12, by + l - 0.12],
                color="#334155", lw=1.2, zorder=5)
        ax.add_patch(patches.Polygon(
            [[bx + 0.08, by + l - 0.15], [bx + 0.28, by + l - 0.10], [bx + 0.24, by + l - 0.25], [bx + 0.08, by + l - 0.25]],
            closed=True, facecolor="#FEF08A", edgecolor="#CA8A04", lw=0.8, zorder=6))
        ax.add_patch(patches.Polygon(
            [[bx + w - 0.08, by + l - 0.15], [bx + w - 0.28, by + l - 0.10], [bx + w - 0.24, by + l - 0.25], [bx + w - 0.08, by + l - 0.25]],
            closed=True, facecolor="#FEF08A", edgecolor="#CA8A04", lw=0.8, zorder=6))

        # Hood accent crease lines
        ax.plot([bx + 0.35, bx + 0.40], [by + l - 0.25, by + l * 0.70], color="#94A3B8", lw=0.7, zorder=5)
        ax.plot([bx + w - 0.35, bx + w - 0.40], [by + l - 0.25, by + l * 0.70], color="#94A3B8", lw=0.7, zorder=5)

        # Front Windshield (curved trapezoid)
        fy1, fy2 = by + l * 0.68, by + l - 0.28
        ax.add_patch(patches.Polygon(
            [[bx + 0.18, fy1], [bx + 0.26, fy2], [bx + w - 0.26, fy2], [bx + w - 0.18, fy1]],
            closed=True, facecolor="#BAE6FD", edgecolor="#0284C7", lw=1.0, zorder=5))

        # Cabin Roof with Tinted Panoramic Sunroof
        rw2, ry1, ry2 = w * 0.74, by + l * 0.28, by + l * 0.72
        ax.add_patch(patches.FancyBboxPatch(
            (cx - rw2 / 2, ry1), rw2, ry2 - ry1,
            boxstyle="round,pad=0.01,rounding_size=0.10",
            facecolor="#E2E8F0", edgecolor="#334155", lw=0.9, zorder=5,
        ))
        # Sunroof glass
        sr_w, sr_h = rw2 * 0.70, (ry2 - ry1) * 0.38
        ax.add_patch(patches.Rectangle(
            (cx - sr_w / 2, by + l * 0.44), sr_w, sr_h,
            facecolor="#0284C7", edgecolor="#0369A1", alpha=0.35, lw=0.8, zorder=6))

        # Rear Windshield
        ry_1, ry_2 = by + l * 0.20, by + l * 0.32
        ax.add_patch(patches.Polygon(
            [[bx + 0.20, ry_1], [bx + 0.28, ry_2], [bx + w - 0.28, ry_2], [bx + w - 0.20, ry_1]],
            closed=True, facecolor="#BAE6FD", edgecolor="#0284C7", lw=1.0, zorder=5))

        # Rear Taillights & Trunk lid
        ax.plot([bx + 0.12, bx + w - 0.12], [by + 0.14, by + 0.14], color="#334155", lw=1.0, zorder=5)
        ax.add_patch(patches.Rectangle((bx + 0.08, by + 0.06), 0.24, 0.10, facecolor="#EF4444", edgecolor="#B91C1C", lw=0.7, zorder=6))
        ax.add_patch(patches.Rectangle((bx + w - 0.32, by + 0.06), 0.24, 0.10, facecolor="#EF4444", edgecolor="#B91C1C", lw=0.7, zorder=6))

        # Wheels (Tread-tires tucked in arches)
        tw, tl = 0.18, 0.52
        for wx, wy in [(bx - 0.04, cy + l * 0.26), (bx + w - tw + 0.04, cy + l * 0.26),
                       (bx - 0.04, cy - l * 0.26), (bx + w - tw + 0.04, cy - l * 0.26)]:
            ax.add_patch(patches.Rectangle((wx, wy - tl/2), tw, tl,
                facecolor="#1E293B", edgecolor="#0F172A", lw=0.9, zorder=3))

        # Aerodynamic Side Mirrors
        ax.add_patch(patches.Polygon(
            [[bx, cy + l * 0.18], [bx - 0.14, cy + l * 0.22], [bx - 0.12, cy + l * 0.14], [bx, cy + l * 0.15]],
            closed=True, facecolor="#1E293B", edgecolor="#0F172A", lw=0.8, zorder=6))
        ax.add_patch(patches.Polygon(
            [[bx + w, cy + l * 0.18], [bx + w + 0.14, cy + l * 0.22], [bx + w + 0.12, cy + l * 0.14], [bx + w, cy + l * 0.15]],
            closed=True, facecolor="#1E293B", edgecolor="#0F172A", lw=0.8, zorder=6))

    @classmethod
    def draw_cad_suv(cls, ax, cx, cy, length_m=5.12, width_m=1.98,
                     rotation_deg=0.0, show_clearance=False):
        """1:100 CAD Luxury SUV with roof rails, panoramic glass, and muscular fenders."""
        w, l = width_m, length_m
        bx, by = cx - w / 2, cy - l / 2

        # Muscular SUV Body
        ax.add_patch(patches.FancyBboxPatch(
            (bx, by), w, l,
            boxstyle="round,pad=0.03,rounding_size=0.34",
            facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.8, zorder=4,
        ))
        # Front Grille & LED Headlight clusters
        ax.plot([bx + 0.15, bx + w - 0.15], [by + l - 0.15, by + l - 0.15],
                color="#475569", lw=1.4, zorder=5)
        ax.add_patch(patches.Rectangle((cx - 0.35, by + l - 0.12), 0.70, 0.08, facecolor="#0F172A", edgecolor="#334155", lw=0.8, zorder=6))
        ax.add_patch(patches.Polygon(
            [[bx + 0.10, by + l - 0.14], [bx + 0.32, by + l - 0.10], [bx + 0.28, by + l - 0.26], [bx + 0.10, by + l - 0.26]],
            closed=True, facecolor="#FEF08A", edgecolor="#CA8A04", lw=0.9, zorder=6))
        ax.add_patch(patches.Polygon(
            [[bx + w - 0.10, by + l - 0.14], [bx + w - 0.32, by + l - 0.10], [bx + w - 0.28, by + l - 0.26], [bx + w - 0.10, by + l - 0.26]],
            closed=True, facecolor="#FEF08A", edgecolor="#CA8A04", lw=0.9, zorder=6))

        # Front Windshield
        fy1, fy2 = by + l * 0.66, by + l - 0.26
        ax.add_patch(patches.Polygon(
            [[bx + 0.20, fy1], [bx + 0.28, fy2], [bx + w - 0.28, fy2], [bx + w - 0.20, fy1]],
            closed=True, facecolor="#BAE6FD", edgecolor="#0284C7", lw=1.1, zorder=5))

        # Roof & Roof Rails
        rfw, rfl = w * 0.72, l * 0.44
        rx, ry = cx - rfw/2, by + l * 0.24
        ax.add_patch(patches.FancyBboxPatch(
            (rx, ry), rfw, rfl,
            boxstyle="round,pad=0.02,rounding_size=0.10",
            facecolor="#CBD5E1", edgecolor="#475569", lw=1.0, zorder=5,
        ))
        # Roof rack rails (left & right)
        ax.plot([rx + 0.05, rx + 0.05], [ry + 0.06, ry + rfl - 0.06],
                color="#0F172A", lw=2.0, solid_capstyle="round", zorder=6)
        ax.plot([rx + rfw - 0.05, rx + rfw - 0.05], [ry + 0.06, ry + rfl - 0.06],
                color="#0F172A", lw=2.0, solid_capstyle="round", zorder=6)

        # Rear Windshield
        ax.add_patch(patches.Polygon(
            [[bx + 0.22, by + l * 0.16], [bx + 0.28, by + l * 0.26],
             [bx + w - 0.28, by + l * 0.26], [bx + w - 0.22, by + l * 0.16]],
            closed=True, facecolor="#BAE6FD", edgecolor="#0284C7", lw=1.0, zorder=5))

        # Rear LED Taillight Bar
        ax.add_patch(patches.Rectangle((bx + 0.12, by + 0.06), w - 0.24, 0.09, facecolor="#EF4444", edgecolor="#B91C1C", lw=0.8, zorder=6))

        # Wide SUV Wheels
        tw, tl = 0.22, 0.62
        for wx, wy in [(bx - 0.05, cy + l * 0.27), (bx + w - tw + 0.05, cy + l * 0.27),
                       (bx - 0.05, cy - l * 0.27), (bx + w - tw + 0.05, cy - l * 0.27)]:
            ax.add_patch(patches.Rectangle((wx, wy - tl/2), tw, tl,
                facecolor="#0F172A", edgecolor="#000000", lw=1.1, zorder=3))

        # Side Mirrors
        ax.add_patch(patches.Polygon(
            [[bx, cy + l * 0.19], [bx - 0.16, cy + l * 0.24], [bx - 0.14, cy + l * 0.15], [bx, cy + l * 0.16]],
            closed=True, facecolor="#0F172A", edgecolor="#000000", lw=0.9, zorder=6))
        ax.add_patch(patches.Polygon(
            [[bx + w, cy + l * 0.19], [bx + w + 0.16, cy + l * 0.24], [bx + w + 0.14, cy + l * 0.15], [bx + w, cy + l * 0.16]],
            closed=True, facecolor="#0F172A", edgecolor="#000000", lw=0.9, zorder=6))

    # =========================================================================
    # 2. STAIRCASES
    # =========================================================================

    @classmethod
    def draw_cad_staircase(cls, ax, min_x, min_y, rw, rh,
                            is_first_floor=False, typology="dogleg", lateral_wall="left"):
        """
        Renders an accurate CAD staircase matching the reference stair images.
        Dog-leg: two equal flights with intermediate landing, tread lines, breakline, arrows.
        Floating: cantilevered treads with glass balustrade.
        """
        if typology == "floating" or rw < 1.80:
            cls._draw_floating_stair_cad(ax, min_x, min_y, rw, rh, is_first_floor)
            return

        half_w = rw / 2.0
        mid_t = 0.12
        landing_d = max(1.10, rh * 0.25)
        flight_h = rh - landing_d
        n = 9
        step_h = flight_h / n

        # Flight 1 stringers
        ax.plot([min_x, min_x], [min_y, min_y + flight_h], color="#0F172A", lw=2.2, zorder=4)
        ax.plot([min_x + half_w - mid_t, min_x + half_w - mid_t],
                [min_y, min_y + flight_h], color="#0F172A", lw=2.2, zorder=4)
        ax.add_patch(patches.Rectangle(
            (min_x + half_w - mid_t, min_y), mid_t, flight_h,
            facecolor="#334155", edgecolor="none", lw=0, zorder=3))

        # Tread lines flight 1
        for i in range(n + 1):
            sy = min_y + i * step_h
            above = not is_first_floor and i > 5
            ax.plot([min_x, min_x + half_w - mid_t], [sy, sy],
                    color="#94A3B8" if above else "#334155",
                    lw=0.8 if above else 1.0, ls="--" if above else "-", zorder=4)
            if i < n and not above and not is_first_floor:
                ax.text(min_x + 0.22, sy + step_h * 0.5, str(i + 1),
                        fontsize=4.8, color="#475569", va="center", ha="center", zorder=5)
            elif i < n and is_first_floor:
                ax.text(min_x + 0.22, sy + step_h * 0.5, str(n * 2 - i),
                        fontsize=4.8, color="#2563EB", va="center", ha="center", zorder=5)

        # Breakline + UP arrow
        if not is_first_floor:
            bk_y = min_y + 5.5 * step_h
            zx = min_x + half_w - mid_t
            ax.plot([min_x, min_x + (zx-min_x)*0.35, min_x + (zx-min_x)*0.50,
                     min_x + (zx-min_x)*0.65, zx],
                    [bk_y, bk_y, bk_y + 0.14, bk_y - 0.14, bk_y],
                    color="#0F172A", lw=1.5, zorder=6)
            ax2 = min_x + half_w * 0.45
            ax.plot([ax2, ax2], [min_y + 0.30, bk_y - 0.12], color="#000000", lw=1.5, zorder=5)
            ax.annotate("", xy=(ax2, bk_y - 0.02), xytext=(ax2, bk_y - 0.22),
                        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.5), zorder=5)
            ax.add_patch(patches.Circle((ax2, min_y + 0.24), 0.08, facecolor="#000000", zorder=6))
            ax.text(ax2, min_y + flight_h * 0.40, "UP (18 RISERS)", rotation=90,
                    color="#000000", fontsize=6.0, fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none"), zorder=7)

        # Intermediate landing
        land_y = min_y + flight_h
        ax.plot([min_x, min_x + rw], [land_y, land_y], color="#0F172A", lw=1.8, zorder=4)
        ax.plot([min_x, min_x + rw], [land_y + landing_d, land_y + landing_d],
                color="#0F172A", lw=1.8, zorder=4)
        ax.text(min_x + rw * 0.5, land_y + landing_d * 0.5,
                "MID-LANDING\n(+1500mm)\n4\'-0\" CLEAR",
                ha="center", va="center", color="#0F172A", fontsize=5.5, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.2", facecolor="#F8FAFC", edgecolor="#94A3B8", alpha=0.95),
                zorder=6)

        # Flight 2 stringers
        ax.plot([min_x + rw, min_x + rw], [min_y, min_y + flight_h], color="#0F172A", lw=2.2, zorder=4)
        ax.plot([min_x + half_w + mid_t, min_x + half_w + mid_t],
                [min_y, min_y + flight_h], color="#0F172A", lw=2.2, zorder=4)

        for i in range(n + 1):
            sy = min_y + i * step_h
            below = not is_first_floor and i < 4
            ax.plot([min_x + half_w + mid_t, min_x + rw], [sy, sy],
                    color="#94A3B8" if below else "#334155",
                    lw=0.8 if below else 1.0, ls="--" if below else "-", zorder=4)
            if i < n and is_first_floor:
                ax.text(min_x + rw - 0.22, sy + step_h * 0.5, str(n + i + 1),
                        fontsize=4.8, color="#2563EB", va="center", ha="center", zorder=5)

        if is_first_floor:
            ax2r = min_x + half_w + half_w * 0.55
            ax.plot([ax2r, ax2r], [min_y + flight_h - 0.25, min_y + 0.30],
                    color="#2563EB", lw=1.5, zorder=5)
            ax.annotate("", xy=(ax2r, min_y + 0.12), xytext=(ax2r, min_y + 0.32),
                        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.5), zorder=5)
            ax.add_patch(patches.Circle((ax2r, min_y + flight_h - 0.25), 0.08,
                facecolor="#2563EB", zorder=6))
            ax.text(ax2r, min_y + flight_h * 0.45, "DN (ARRIVAL)", rotation=270,
                    color="#2563EB", fontsize=6.0, fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none"), zorder=7)
            # Balustrade
            ax.plot([min_x + rw, min_x + rw], [min_y, min_y + flight_h],
                    color="#0F172A", lw=2.8, zorder=7)
            ax.plot([min_x + rw - 0.09, min_x + rw - 0.09], [min_y, min_y + flight_h],
                    color="#64748B", lw=1.0, zorder=7)
            ax.add_patch(patches.Circle((min_x + rw, min_y), 0.07, facecolor="#0F172A", zorder=8))
            ax.add_patch(patches.Circle((min_x + rw, min_y + flight_h), 0.07,
                facecolor="#0F172A", zorder=8))
            ax.text(min_x + rw - 0.20, min_y + flight_h * 0.50,
                    "BALUSTRADE\n1050mm HT.", rotation=270,
                    fontsize=4.8, fontweight="bold", color="#0F172A", ha="right", va="center",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF",
                              edgecolor="none", alpha=0.9), zorder=8)

    @classmethod
    def _draw_floating_stair_cad(cls, ax, min_x, min_y, rw, rh, is_first_floor):
        """Cantilevered floating staircase with glass balustrade."""
        steps = 16
        landing_h = max(1.00, rh * 0.20)
        flight_h = rh - landing_h
        step_h = flight_h / (steps - 1)
        tw = rw - 0.12

        ax.plot([min_x + 0.05, min_x + 0.05], [min_y, min_y + rh],
                color="#0F172A", lw=2.8, zorder=4)
        for i in range(steps):
            sy = min_y + i * step_h
            above = not is_first_floor and i > 8
            ax.add_patch(patches.Rectangle(
                (min_x + 0.08, sy - 0.035), tw - 0.08, 0.07,
                facecolor="#F8FAFC",
                edgecolor="#94A3B8" if above else "#0F172A",
                lw=0.8 if above else 1.2,
                ls="--" if above else "-", zorder=4))
            if not above:
                num = (steps - i) if is_first_floor else (i + 1)
                ax.text(min_x + 0.24, sy, str(num),
                        fontsize=5.0, color="#475569", va="center", ha="center", zorder=5)

        top_ly = min_y + flight_h
        ax.plot([min_x, min_x + rw], [top_ly, top_ly], color="#0F172A", lw=1.8, zorder=4)
        ax.text(min_x + rw * 0.5, top_ly + landing_h * 0.5, "TOP LANDING\n(4\'-0\" CLEAR)",
                ha="center", va="center", color="#0F172A", fontsize=5.5, fontweight="bold",
                bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF",
                          edgecolor="#CBD5E1", alpha=0.9), zorder=6)
        bal_x = min_x + tw
        ax.plot([bal_x, bal_x], [min_y, top_ly], color="#0284C7", lw=1.4, ls="--", zorder=6)
        ax.text(bal_x - 0.08, min_y + flight_h * 0.3, "12mm GLASS BALUSTRADE",
                rotation=90, fontsize=4.5, color="#0284C7", ha="right", va="center", zorder=6)
        cx = min_x + rw * 0.5
        if not is_first_floor:
            bb = min_y + 8.5 * step_h
            ax.plot([min_x, min_x + rw*0.38, min_x + rw*0.50, min_x + rw*0.62, min_x + rw],
                    [bb, bb, bb + 0.16, bb - 0.16, bb], color="#0F172A", lw=1.6, zorder=7)
            ax.plot([cx, cx], [min_y + 0.32, bb - 0.14], color="#000000", lw=1.5, zorder=5)
            ax.annotate("", xy=(cx, bb - 0.04), xytext=(cx, bb - 0.24),
                        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.5), zorder=5)
            ax.add_patch(patches.Circle((cx, min_y + 0.26), 0.08, facecolor="#000000", zorder=6))
            ax.text(cx, min_y + 4 * step_h, "UP (16 RISERS)", rotation=90,
                    color="#000000", fontsize=6.0, fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none"),
                    zorder=7)
        else:
            ax.plot([cx, cx], [top_ly - 0.22, min_y + 0.32], color="#2563EB", lw=1.5, zorder=5)
            ax.annotate("", xy=(cx, min_y + 0.12), xytext=(cx, min_y + 0.32),
                        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.5), zorder=5)
            ax.add_patch(patches.Circle((cx, top_ly - 0.22), 0.08, facecolor="#2563EB", zorder=6))
            ax.text(cx, min_y + flight_h * 0.5, "DN (ARRIVAL)", rotation=270,
                    color="#2563EB", fontsize=6.0, fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none"),
                    zorder=7)

    # =========================================================================
    # 3. LIVING ROOM / DRAWING ROOM / TV LOUNGE
    # =========================================================================

    @classmethod
    def draw_cad_living_suite(cls, ax, cx, cy, rw, rh, is_formal_drawing=False):
        """Drawing room (formal 3-seat suite) or TV Lounge (L-sectional)."""
        if is_formal_drawing:
            cls._draw_formal_drawing_room(ax, cx, cy, rw, rh)
        else:
            cls._draw_tv_lounge(ax, cx, cy, rw, rh)

    @classmethod
    def _draw_formal_drawing_room(cls, ax, cx, cy, rw, rh):
        """
        Formal Drawing Room matching reference top-view icons:
        3-seater sofa + 2 armchairs + glass coffee table + side credenza + area rug.
        """
        sm = 0.35
        sx1, sx2 = cx - rw/2 + sm, cx + rw/2 - sm
        sy1, sy2 = cy - rh/2 + sm, cy + rh/2 - sm
        aw, ah = sx2 - sx1, sy2 - sy1

        # Area rug
        rg_w, rg_h = min(aw * 0.90, 3.50), min(ah * 0.75, 2.80)
        ax.add_patch(patches.FancyBboxPatch(
            (cx - rg_w/2, cy - rg_h/2 - ah*0.05), rg_w, rg_h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor="#FEF9C3", edgecolor="#D97706", lw=0.8, ls="--", alpha=0.50, zorder=1))

        # 3-seat sofa (top of room, back against north wall)
        sf_w, sf_d = min(2.40, aw * 0.78), min(0.90, ah * 0.28)
        sf_x, sf_y = cx - sf_w/2, sy2 - sf_d
        ax.add_patch(patches.FancyBboxPatch(
            (sf_x, sf_y), sf_w, sf_d,
            boxstyle="round,pad=0.02,rounding_size=0.10",
            facecolor="#F1F5F9", edgecolor="#0F172A", lw=1.3, zorder=3))
        arm_w = 0.18
        ax.add_patch(patches.Rectangle((sf_x, sf_y + 0.02), arm_w, sf_d - 0.04,
            facecolor="#CBD5E1", edgecolor="#334155", lw=1.0, zorder=4))
        ax.add_patch(patches.Rectangle((sf_x + sf_w - arm_w, sf_y + 0.02), arm_w, sf_d - 0.04,
            facecolor="#CBD5E1", edgecolor="#334155", lw=1.0, zorder=4))
        ax.plot([sf_x + 0.02, sf_x + sf_w - 0.02],
                [sf_y + sf_d - 0.16, sf_y + sf_d - 0.16],
                color="#334155", lw=2.8, solid_capstyle="round", zorder=5)
        inner = sf_w - 2 * arm_w
        cw = inner / 3.0
        for i in range(3):
            cx_i = sf_x + arm_w + i * cw
            ax.add_patch(patches.Rectangle(
                (cx_i + 0.03, sf_y + 0.04), cw - 0.06, sf_d - 0.26,
                facecolor="#FFFFFF", edgecolor="#94A3B8", lw=0.8, zorder=4))
            ax.plot([cx_i + cw/2], [sf_y + (sf_d - 0.26)/2 + 0.04],
                    marker="o", color="#CBD5E1", markersize=3.5, zorder=5)

        # Glass coffee table
        tb_w, tb_d = min(1.30, aw * 0.42), min(0.70, ah * 0.22)
        tb_x, tb_y = cx - tb_w/2, sf_y - sf_d*0.5 - tb_d - 0.40
        ax.add_patch(patches.FancyBboxPatch(
            (tb_x, tb_y), tb_w, tb_d,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.2, zorder=3))
        ax.plot([tb_x + 0.06, tb_x + tb_w - 0.06], [tb_y + tb_d/2, tb_y + tb_d/2],
                color="#38BDF8", lw=0.7, ls=":", zorder=4)
        ax.text(cx, tb_y + tb_d/2, "COFFEE TABLE",
                ha="center", va="center", color="#0369A1", fontsize=5.0, fontweight="bold", zorder=5)

        # Two armchairs facing sofa
        ch_y = tb_y - 0.12 - 0.75
        sp = tb_w * 0.60
        for sign in [-1, 1]:
            ch_cx = cx + sign * sp
            ax.add_patch(patches.FancyBboxPatch(
                (ch_cx - 0.375, ch_y), 0.75, 0.75,
                boxstyle="round,pad=0.02,rounding_size=0.10",
                facecolor="#F1F5F9", edgecolor="#0F172A", lw=1.1, zorder=3))
            ax.plot([ch_cx - 0.375 + 0.02, ch_cx + 0.375 - 0.02], [ch_y, ch_y],
                    color="#334155", lw=2.5, solid_capstyle="round", zorder=4)
            ax.add_patch(patches.Rectangle((ch_cx - 0.25, ch_y + 0.12), 0.50, 0.45,
                facecolor="#FFFFFF", edgecolor="#94A3B8", lw=0.8, zorder=4))
            ax.add_patch(patches.Rectangle((ch_cx - 0.375, ch_y + 0.08), 0.10, 0.55,
                facecolor="#CBD5E1", edgecolor="#475569", lw=0.8, zorder=4))
            ax.add_patch(patches.Rectangle((ch_cx + 0.275, ch_y + 0.08), 0.10, 0.55,
                facecolor="#CBD5E1", edgecolor="#475569", lw=0.8, zorder=4))

        # Side credenza / showcase cabinet
        cr_w, cr_h = 0.45, min(1.60, ah * 0.55)
        cr_x, cr_y = sx2 - cr_w, cy - cr_h/2
        ax.add_patch(patches.Rectangle((cr_x, cr_y), cr_w, cr_h,
            facecolor="#E2E8F0", edgecolor="#475569", lw=1.0, zorder=3))
        for di in range(3):
            ax.plot([cr_x + 0.06, cr_x + cr_w - 0.06],
                    [cr_y + (di + 1) * cr_h/3, cr_y + (di + 1) * cr_h/3],
                    color="#94A3B8", lw=0.7, zorder=4)
        ax.text(cr_x + cr_w/2, cr_y + cr_h/2, "CREDENZA",
                rotation=90, ha="center", va="center",
                color="#334155", fontsize=5.0, fontweight="bold", zorder=5)
        ax.text(cx, sy1 + 0.22, "FORMAL DRAWING ROOM SUITE",
                ha="center", va="bottom", color="#0F172A", fontsize=5.5, fontweight="bold", zorder=7)

    @classmethod
    def _draw_tv_lounge(cls, ax, cx, cy, rw, rh):
        """
        TV Lounge: Modern L-shaped sectional sofa + designer coffee table + floating media console.
        Clean architectural layout without viewing distance clutter lines.
        """
        sm = 0.30
        sx1, sx2 = cx - rw/2 + sm, cx + rw/2 - sm
        sy1, sy2 = cy - rh/2 + sm, cy + rh/2 - sm
        aw, ah = sx2 - sx1, sy2 - sy1

        # Area rug under conversation zone
        rg_w, rg_h = min(aw * 0.88, 3.80), min(ah * 0.78, 3.20)
        ax.add_patch(patches.FancyBboxPatch(
            (cx - rg_w/2, cy - rg_h/2), rg_w, rg_h,
            boxstyle="round,pad=0.03,rounding_size=0.15",
            facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=0.8, ls="--", zorder=1))

        # TV console (left wall)
        tv_d, tv_h = 0.45, min(1.80, ah * 0.70)
        tv_x, tv_y = sx1, cy - tv_h/2
        ax.add_patch(patches.Rectangle((tv_x, tv_y), tv_d, tv_h,
            facecolor="#1E293B", edgecolor="#0F172A", lw=1.4, zorder=3))
        scr_h = tv_h * 0.70
        ax.add_patch(patches.Rectangle(
            (tv_x + tv_d, tv_y + (tv_h - scr_h)/2), 0.06, scr_h,
            facecolor="#0F172A", edgecolor="#000000", lw=1.1, zorder=4))
        ax.text(tv_x + tv_d/2, cy, "OLED TV\nCONSOLE",
                ha="center", va="center", color="#F8FAFC",
                fontsize=5.0, fontweight="bold", rotation=90, zorder=5)

        # L-shaped sectional sofa (vertically centered around cy, facing OLED TV)
        sf_w = min(2.80, aw * 0.75)
        sf_d = min(0.95, ah * 0.28)
        ch_w = min(0.95, aw * 0.28)
        ch_h = min(sf_w * 0.60, ah * 0.50)
        
        # Center the combined sofa + chaise unit vertically along cy
        total_sofa_h = sf_d + ch_h
        sf_y = cy - total_sofa_h * 0.50
        
        # Horizontally place sofa with proper throw distance from TV wall
        sf_x = min(sx2 - sf_w, max(tv_x + tv_d + 1.80, cx + (rw * 0.15)))
        
        ax.add_patch(patches.FancyBboxPatch(
            (sf_x, sf_y), sf_w, sf_d,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.4, zorder=3))
        ax.plot([sf_x + 0.03, sf_x + sf_w - 0.03], [sf_y, sf_y],
                color="#334155", lw=3.0, solid_capstyle="round", zorder=4)
        arm_w = 0.18
        ax.add_patch(patches.Rectangle((sf_x + sf_w - arm_w, sf_y + 0.04),
            arm_w, sf_d - 0.04, facecolor="#CBD5E1", edgecolor="#475569", lw=0.9, zorder=4))
        n_s = max(1, int((sf_w - arm_w) / 0.65))
        cw = (sf_w - arm_w) / n_s
        for i in range(n_s):
            bx2 = sf_x + i * cw
            ax.add_patch(patches.Rectangle(
                (bx2 + 0.04, sf_y + 0.05), cw - 0.08, sf_d - 0.18,
                facecolor="#FFFFFF", edgecolor="#94A3B8", lw=0.85, zorder=4))
            ax.plot([bx2 + 0.04, bx2 + cw - 0.04],
                    [sf_y + (sf_d - 0.18)/2 + 0.05, sf_y + (sf_d - 0.18)/2 + 0.05],
                    color="#CBD5E1", lw=0.7, ls="--", zorder=5)
        ax.add_patch(patches.FancyBboxPatch((sf_x + 0.08, sf_y + 0.18), 0.22, 0.22,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor="#E0E7FF", edgecolor="#4F46E5", lw=0.9, zorder=5))
        ax.add_patch(patches.FancyBboxPatch((sf_x + sf_w - arm_w - 0.30, sf_y + 0.18), 0.22, 0.22,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor="#E0E7FF", edgecolor="#4F46E5", lw=0.9, zorder=5))

        # Chaise (vertical arm of L)
        ch_x, ch_y = sf_x, sf_y + sf_d
        ax.add_patch(patches.FancyBboxPatch(
            (ch_x, ch_y), ch_w, ch_h,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.4, zorder=3))
        ax.plot([ch_x, ch_x], [ch_y + 0.03, ch_y + ch_h - 0.03],
                color="#334155", lw=3.0, solid_capstyle="round", zorder=4)
        ax.add_patch(patches.Rectangle((ch_x, ch_y + ch_h - arm_w), ch_w - 0.04, arm_w,
            facecolor="#CBD5E1", edgecolor="#475569", lw=0.9, zorder=4))
        ax.add_patch(patches.Rectangle((ch_x + 0.05, ch_y + 0.05),
            ch_w - 0.18, ch_h - arm_w - 0.08,
            facecolor="#FFFFFF", edgecolor="#94A3B8", lw=0.85, zorder=4))

        # Coffee table (centered between TV console and sofa, aligned along cy)
        tb_w = min(1.10, max(0.60, (sf_x - tv_x - tv_d - 0.50) * 0.70))
        tb_h = min(0.65, sf_d * 0.85)
        tb_x = sf_x - tb_w - 0.25
        tb_y = cy - tb_h / 2.0
        ax.add_patch(patches.FancyBboxPatch(
            (tb_x, tb_y), tb_w, tb_h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.2, zorder=3))
        ax.plot([tb_x + 0.05, tb_x + tb_w * 0.40, tb_x + tb_w - 0.05],
                [tb_y + tb_h - 0.06, tb_y + 0.06, tb_y + 0.06],
                color="#38BDF8", lw=0.7, ls=":", zorder=4)
        ax.text(tb_x + tb_w/2, tb_y + tb_h/2, "COFFEE\nTABLE",
                ha="center", va="center", color="#0369A1", fontsize=4.8, fontweight="bold", zorder=5)
        ax.text(cx, sy2 - 0.18, "TV LOUNGE – L-SECTIONAL SOFA SUITE",
                ha="center", va="top", color="#0F172A", fontsize=5.5, fontweight="bold", zorder=7)

    # =========================================================================
    # 4. DINING
    # =========================================================================

    @classmethod
    def draw_cad_dining_suite(cls, ax, cx, cy, rw=2.5, rh=2.5):
        """8-seater dining table with individual backrest-rail chairs matching reference images."""
        tbl_w, tbl_d = 2.44, 1.10
        bx, by = cx - tbl_w/2, cy - tbl_d/2

        ax.add_patch(patches.FancyBboxPatch(
            (bx, by), tbl_w, tbl_d,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor="#FEF3C7", edgecolor="#B45309", lw=1.6, zorder=3))
        ax.add_patch(patches.FancyBboxPatch(
            (bx + 0.08, by + 0.08), tbl_w - 0.16, tbl_d - 0.16,
            boxstyle="round,pad=0.01,rounding_size=0.08",
            facecolor="none", edgecolor="#D97706", lw=0.7, ls=":", zorder=4))
        for gi in range(4):
            gx = bx + 0.20 + gi * (tbl_w - 0.40) / 3
            ax.plot([gx, gx], [by + 0.12, by + tbl_d - 0.12],
                    color="#D97706", lw=0.5, alpha=0.5, zorder=4)
        ax.text(cx, cy, "8-SEATER DINING\n(8\'-0\" x 3\'-8\")",
                ha="center", va="center", color="#78350F", fontsize=6.0, fontweight="bold", zorder=5)

        ch_w, ch_d = 0.44, 0.42
        gap, sp = 0.06, tbl_w / 3.0
        for i in range(3):
            ch_cx = bx + i * sp + sp/2
            cls._draw_dining_chair(ax, ch_cx, by + tbl_d + ch_d/2 + gap, ch_w, ch_d, "top", zorder=4)
            cls._draw_dining_chair(ax, ch_cx, by - ch_d/2 - gap, ch_w, ch_d, "bottom", zorder=4)
        cls._draw_dining_chair(ax, bx - ch_d/2 - gap, cy, ch_d, ch_w, "left", zorder=4)
        cls._draw_dining_chair(ax, bx + tbl_w + ch_d/2 + gap, cy, ch_d, ch_w, "right", zorder=4)

    # =========================================================================
    # 5. KITCHEN
    # =========================================================================

    @classmethod
    def draw_cad_kitchen_details(cls, ax, min_x, min_y, rw, rh, is_show_kitchen=True):
        """
        U-shaped counters + hob + double sink + fridge + oven + waterfall island.
        Matches the reference kitchen floor plan top-view image.
        """
        if is_show_kitchen:
            cls._draw_show_kitchen(ax, min_x, min_y, rw, rh)
        else:
            cls._draw_wet_kitchen(ax, min_x, min_y, rw, rh)

    @classmethod
    def _draw_show_kitchen(cls, ax, min_x, min_y, rw, rh):
        depth, m = 0.61, 0.08

        # U-shaped counters
        ax.add_patch(patches.Rectangle((min_x+m, min_y+m), rw-2*m, depth,
            facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.2, zorder=3))
        ax.add_patch(patches.Rectangle((min_x+m, min_y+m+depth), depth, rh-2*m-depth,
            facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.2, zorder=3))
        ax.add_patch(patches.Rectangle((min_x+rw-m-depth, min_y+m+depth), depth, rh-2*m-depth,
            facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.2, zorder=3))
        # Edge lines
        for px1, py1, px2, py2 in [
            (min_x+m+0.05, min_y+m+depth, min_x+rw-m-0.05, min_y+m+depth),
            (min_x+m+depth, min_y+m+depth+0.05, min_x+m+depth, min_y+rh-m-0.05),
            (min_x+rw-m-depth, min_y+m+depth+0.05, min_x+rw-m-depth, min_y+rh-m-0.05),
        ]:
            ax.plot([px1, px2], [py1, py2], color="#64748B", lw=0.8, zorder=4)

        # Hob (center-bottom counter)
        hob_w, hob_d = 0.76, 0.48
        hob_x = min_x + m + (rw - 2*m - hob_w) / 2
        hob_y = min_y + m
        ax.add_patch(patches.Rectangle((hob_x, hob_y), hob_w, hob_d,
            facecolor="#1E293B", edgecolor="#0F172A", lw=1.2, zorder=4))
        for brow, bcol in [(0,0),(0,1),(1,0),(1,1)]:
            bx2 = hob_x + 0.16 + bcol * 0.44
            by2 = hob_y + 0.12 + brow * 0.24
            r = 0.065 if (brow == 0 and bcol == 0) else 0.052
            ax.add_patch(patches.Circle((bx2, by2), r,
                facecolor="#64748B", edgecolor="#94A3B8", lw=0.8, zorder=5))
            ax.add_patch(patches.Circle((bx2, by2), r*0.45,
                facecolor="#0F172A", zorder=6))
        ax.text(hob_x + hob_w/2, hob_y + hob_d + 0.06, "HOB",
                fontsize=4.5, ha="center", va="bottom", color="#334155", zorder=5)

        # Double sink (left counter)
        sk_x, sk_y = min_x + m, min_y + m + depth + 0.12
        sk_w, sk_h = depth - 0.06, 0.82
        ax.add_patch(patches.Rectangle((sk_x, sk_y), sk_w, sk_h,
            facecolor="#F8FAFC", edgecolor="#475569", lw=1.1, zorder=4))
        bsin_h = (sk_h - 0.14) / 2
        for bi in range(2):
            by_b = sk_y + 0.06 + bi * (bsin_h + 0.02)
            ax.add_patch(patches.FancyBboxPatch(
                (sk_x + 0.04, by_b), sk_w - 0.08, bsin_h,
                boxstyle="round,pad=0.01,rounding_size=0.04",
                facecolor="#E0F2FE", edgecolor="#0284C7", lw=0.9, zorder=5))
        ax.add_patch(patches.Circle((sk_x + sk_w/2, sk_y + sk_h/2), 0.038,
            facecolor="#334155", zorder=6))
        ax.plot([sk_x + sk_w/2, sk_x + sk_w/2],
                [sk_y + sk_h/2, sk_y + sk_h/2 + 0.12],
                color="#334155", lw=1.5, zorder=6)
        ax.text(sk_x + sk_w/2, sk_y - 0.06, "DOUBLE\nSINK",
                fontsize=4.5, ha="center", va="top", color="#0369A1", fontweight="bold", zorder=5)

        # Fridge (placed along solid exterior wall top-left, keeping door wall completely clear)
        fd = depth - 0.04
        fh = min(0.88, rh * 0.22)
        fx = min_x + m
        fy = min_y + rh - m - fh
        ax.add_patch(patches.Rectangle((fx, fy), fd, fh,
            facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.3, zorder=4))
        ax.plot([fx + fd/2, fx + fd/2], [fy, fy + fh], color="#0F172A", lw=0.9, zorder=5)
        ax.plot([fx + 0.06, fx + fd - 0.06], [fy + fh * 0.60, fy + fh * 0.60],
                color="#64748B", lw=0.7, zorder=5)
        ax.text(fx + fd/2, fy + fh/2, "FRIDGE",
                ha="center", va="center", color="#0F172A", fontsize=5.0, fontweight="bold", zorder=6)

        # Oven (bottom counter, right of hob)
        ov_x = hob_x + hob_w + 0.12
        ov_w = min(0.65, min_x + rw - m - ov_x - 0.10)
        if ov_w > 0.30:
            ax.add_patch(patches.Rectangle((ov_x, min_y+m), ov_w, depth,
                facecolor="#334155", edgecolor="#0F172A", lw=1.0, zorder=4))
            ax.add_patch(patches.Rectangle((ov_x+0.04, min_y+m+0.04), ov_w-0.08, depth*0.45,
                facecolor="#1E293B", edgecolor="#64748B", lw=0.7, zorder=5))
            ax.text(ov_x + ov_w/2, min_y + m + depth*0.72, "OVEN",
                    ha="center", va="center", color="#F8FAFC", fontsize=4.5, zorder=6)

        # Central waterfall island
        isl_w = min(2.44, max(1.60, rw * 0.58))
        isl_h = min(1.10, max(0.90, rh * 0.30))
        ix = min_x + (rw - isl_w) / 2
        iy = min_y + (rh - isl_h) / 2 + rh * 0.08
        ax.add_patch(patches.FancyBboxPatch(
            (ix, iy), isl_w, isl_h,
            boxstyle="round,pad=0.01,rounding_size=0.06",
            facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.8, zorder=3))
        ax.plot([ix+0.08, ix+0.08], [iy, iy+isl_h], color="#0F172A", lw=1.6, zorder=4)
        ax.plot([ix+isl_w-0.08, ix+isl_w-0.08], [iy, iy+isl_h], color="#0F172A", lw=1.6, zorder=4)
        # Prep sink on island
        ax.add_patch(patches.FancyBboxPatch(
            (ix + 0.30, iy + (isl_h - 0.36)/2), 0.46, 0.36,
            boxstyle="round,pad=0.01,rounding_size=0.05",
            facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0, zorder=5))
        ax.add_patch(patches.Circle((ix + 0.30 + 0.23, iy + isl_h/2), 0.03,
            facecolor="#334155", zorder=6))
        ax.text(ix + isl_w/2, iy + isl_h/2,
                "WATERFALL ISLAND\n(BREAKFAST BAR)",
                ha="center", va="center", color="#0F172A", fontsize=5.5, fontweight="bold", zorder=6)
        n_st = min(4, int(isl_w / 0.55))
        for ki in range(n_st):
            stx = ix + (isl_w / (n_st + 1)) * (ki + 1)
            sty = iy - 0.17 - 0.16
            ax.add_patch(patches.Circle((stx, sty), 0.17,
                facecolor="#F1F5F9", edgecolor="#0F172A", lw=1.1, zorder=4))
            ax.add_patch(patches.Circle((stx, sty), 0.12,
                facecolor="none", edgecolor="#94A3B8", lw=0.8, ls="--", zorder=5))

    @classmethod
    def _draw_wet_kitchen(cls, ax, min_x, min_y, rw, rh):
        """Draws dedicated dirty kitchen (wet kitchen/scullery) with commercial gas range, double utility sink, and pantry."""
        depth, m = 0.61, 0.08
        # Continuous granite prep counter along bottom and left walls
        ax.add_patch(patches.Rectangle((min_x+m, min_y+m), rw-2*m, depth,
            facecolor="#FED7AA", edgecolor="#C2410C", lw=1.2, zorder=3))
        ax.add_patch(patches.Rectangle((min_x+m, min_y+m+depth), depth, rh-2*m-depth,
            facecolor="#FED7AA", edgecolor="#C2410C", lw=1.2, zorder=3))

        # Deep double-bowl utility scullery sink (left counter)
        sc_cy = min_y + m + depth + (rh - 2*m - depth) * 0.40
        sx, sy = min_x + m, sc_cy - 0.45
        sk_h = min(0.90, rh * 0.45)
        ax.add_patch(patches.Rectangle((sx, sy), depth, sk_h,
            facecolor="#F8FAFC", edgecolor="#475569", lw=1.1, zorder=4))
        # Drainboard ribbed grooves
        for gi in range(4):
            gy = sy + 0.08 + gi * 0.07
            ax.plot([sx + 0.04, sx + 0.18], [gy, gy], color="#94A3B8", lw=0.8, zorder=5)
        # Deep wash basins
        bs_h = (sk_h - 0.38) / 2
        for bi in range(2):
            by_b = sy + 0.34 + bi * (bs_h + 0.03)
            ax.add_patch(patches.FancyBboxPatch(
                (sx + 0.04, by_b), depth - 0.08, bs_h,
                boxstyle="round,pad=0.01,rounding_size=0.04",
                facecolor="#E0F2FE", edgecolor="#0284C7", lw=0.9, zorder=5))
        ax.add_patch(patches.Circle((sx + depth/2, sy + 0.34 + bs_h), 0.035, facecolor="#334155", zorder=6))
        ax.text(sx + depth/2, sy - 0.06, "UTILITY SINK", fontsize=4.2, color="#0369A1", fontweight="bold", ha="center", va="top", zorder=6)

        # Heavy-Duty 4-Burner Commercial Gas Range & Extraction Hood (bottom counter)
        hob_x = min_x + rw - m - 0.85
        ax.add_patch(patches.Rectangle((hob_x, min_y+m), 0.80, depth,
            facecolor="#1E293B", edgecolor="#0F172A", lw=1.3, zorder=4))
        # Stainless extraction hood dashed outline
        ax.add_patch(patches.Rectangle((hob_x - 0.05, min_y+m - 0.02), 0.90, depth + 0.04,
            facecolor="none", edgecolor="#EA580C", lw=0.8, ls="--", zorder=5))
        for br, bc in [(0,0),(0,1),(1,0),(1,1)]:
            cx_b = hob_x + 0.16 + bc * 0.46
            cy_b = min_y + m + 0.14 + br * 0.28
            ax.add_patch(patches.Circle((cx_b, cy_b), 0.06, facecolor="#64748B", edgecolor="#94A3B8", lw=0.8, zorder=6))
            ax.add_patch(patches.Circle((cx_b, cy_b), 0.025, facecolor="#0F172A", zorder=7))
        ax.text(hob_x + 0.40, min_y + m + depth + 0.06, "COOKING RANGE & HOOD", fontsize=4.2, color="#C2410C", fontweight="bold", ha="center", va="bottom", zorder=6)

        # Full-height storage / spice pantry cabinet (top left)
        ax.add_patch(patches.Rectangle((min_x+m, min_y+rh-m-0.85), depth, 0.82,
            facecolor="#FED7AA", edgecolor="#7C2D12", lw=1.2, zorder=4))
        ax.plot([min_x+m+depth/2, min_x+m+depth/2], [min_y+rh-m-0.85, min_y+rh-m-0.03], color="#7C2D12", lw=0.9, zorder=5)
        for pi in range(3):
            ax.plot([min_x+m+0.05, min_x+m+depth-0.05], [min_y+rh-m-0.85 + (pi+1)*0.20, min_y+rh-m-0.85 + (pi+1)*0.20], color="#9A3412", lw=0.7, ls=":", zorder=5)
        ax.text(min_x+m+depth/2, min_y+rh-m-0.43, "PANTRY",
                ha="center", va="center", color="#7C2D12", fontsize=4.8, fontweight="bold",
                rotation=90, zorder=6)
        ax.text(min_x+rw*0.58, min_y+rh*0.62, "DIRTY KITCHEN\n(WET SCULLERY)",
                ha="center", va="center", color="#C2410C", fontsize=5.8, fontweight="bold", zorder=5)

    # =========================================================================
    # 6. BATHROOMS
    # =========================================================================

    @classmethod
    def draw_cad_bath_fixtures(cls, ax, min_x, min_y, rw, rh,
                                is_5_fixture=False, is_powder=False):
        """
        Anatomically correct CAD bathroom fixtures matching reference images:
        - WC: cistern + D-shaped bowl + inner seat ring
        - Basin vanity: counter + oval undermount basin + faucet
        - Bathtub: rounded rectangle + oval inner water area + filler spout
        - Shower: frameless glass enclosure + trench drain + rain head
        """
        if is_powder:
            cls._draw_powder_room(ax, min_x, min_y, rw, rh)
        elif is_5_fixture or (rw >= 2.0 and rh >= 2.4):
            cls._draw_ensuite_bathroom(ax, min_x, min_y, rw, rh)
        else:
            cls._draw_secondary_bathroom(ax, min_x, min_y, rw, rh)

    @classmethod
    def _draw_wc(cls, ax, cx, cy, w=0.40, d=0.64, facing="up", zorder=4):
        """Top-view WC: cistern block + D-shaped bowl + seat ring."""
        hw, hd = w/2, d/2
        cis_d = d * 0.28
        if facing in ("up", "down"):
            cis_y = (cy + hd - cis_d) if facing == "up" else (cy - hd)
            bowl_y = (cy - hd + 0.02) if facing == "up" else (cy - hd + cis_d + 0.02)
            bowl_h = d - cis_d - 0.04
            # Cistern
            ax.add_patch(patches.Rectangle((cx - hw, cis_y), w, cis_d,
                facecolor="#CBD5E1", edgecolor="#0F172A", lw=1.1, zorder=zorder))
            # Flush button
            ax.add_patch(patches.Circle((cx, cis_y + cis_d/2), 0.035,
                facecolor="#94A3B8", edgecolor="#475569", lw=0.7, zorder=zorder+1))
            # Bowl body
            ax.add_patch(patches.FancyBboxPatch(
                (cx - hw + 0.02, bowl_y), w - 0.04, bowl_h,
                boxstyle="round,pad=0.01,rounding_size=0.18",
                facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.1, zorder=zorder))
            # Seat ring
            ax.add_patch(patches.FancyBboxPatch(
                (cx - hw + 0.06, bowl_y + 0.04), w - 0.12, bowl_h - 0.08,
                boxstyle="round,pad=0.01,rounding_size=0.14",
                facecolor="#F0F9FF", edgecolor="#475569", lw=0.8, zorder=zorder+1))
            ax.add_patch(patches.Circle((cx, bowl_y + bowl_h * 0.42), 0.04,
                facecolor="#94A3B8", zorder=zorder+2))
        else:
            cis_w = cis_d
            cis_x = (cx + hd - cis_w) if facing == "right" else (cx - hd)
            bowl_x = (cx - hd + 0.02) if facing == "right" else (cx - hd + cis_w + 0.02)
            bowl_w = d - cis_w - 0.04
            ax.add_patch(patches.Rectangle((cis_x, cy - hw), cis_w, w,
                facecolor="#CBD5E1", edgecolor="#0F172A", lw=1.1, zorder=zorder))
            ax.add_patch(patches.Circle((cis_x + cis_w/2, cy), 0.035,
                facecolor="#94A3B8", edgecolor="#475569", lw=0.7, zorder=zorder+1))
            ax.add_patch(patches.FancyBboxPatch(
                (bowl_x, cy - hw + 0.02), bowl_w, w - 0.04,
                boxstyle="round,pad=0.01,rounding_size=0.18",
                facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.1, zorder=zorder))
            ax.add_patch(patches.FancyBboxPatch(
                (bowl_x + 0.04, cy - hw + 0.06), bowl_w - 0.08, w - 0.12,
                boxstyle="round,pad=0.01,rounding_size=0.14",
                facecolor="#F0F9FF", edgecolor="#475569", lw=0.8, zorder=zorder+1))
            ax.add_patch(patches.Circle((bowl_x + bowl_w * 0.42, cy), 0.04,
                facecolor="#94A3B8", zorder=zorder+2))

    @classmethod
    def _draw_basin(cls, ax, cx, cy, w=0.65, d=0.50, zorder=4):
        """Countertop vanity with oval undermount basin and faucet."""
        hw, hd = w/2, d/2
        ax.add_patch(patches.Rectangle((cx - hw, cy - hd), w, d,
            facecolor="#E0F2FE", edgecolor="#0369A1", lw=1.2, zorder=zorder))
        ax.plot([cx - hw + 0.04, cx + hw - 0.04], [cy - hd + 0.06, cy - hd + 0.06],
                color="#38BDF8", lw=0.7, ls=":", zorder=zorder+1)
        ax.add_patch(patches.Ellipse((cx, cy), w * 0.70, d * 0.72,
            facecolor="#FFFFFF", edgecolor="#0284C7", lw=1.0, zorder=zorder+1))
        ax.add_patch(patches.Circle((cx, cy - hd + 0.08), 0.03,
            facecolor="#0F172A", zorder=zorder+2))

    @classmethod
    def _draw_bathtub(cls, ax, cx, cy, w=1.65, d=0.76, zorder=3):
        """Rectangular bathtub with oval inner water area matching reference images."""
        hw, hd = w/2, d/2
        ax.add_patch(patches.FancyBboxPatch(
            (cx - hw, cy - hd), w, d,
            boxstyle="round,pad=0.03,rounding_size=0.36",
            facecolor="#FFFFFF", edgecolor="#0284C7", lw=1.5, zorder=zorder))
        ax.add_patch(patches.FancyBboxPatch(
            (cx - hw + 0.08, cy - hd + 0.08), w - 0.16, d - 0.16,
            boxstyle="round,pad=0.02,rounding_size=0.28",
            facecolor="#F0F9FF", edgecolor="#38BDF8", lw=0.8, ls="--", zorder=zorder+1))
        ax.add_patch(patches.Circle((cx - hw + 0.18, cy), 0.042,
            facecolor="#334155", zorder=zorder+2))
        ax.plot([cx - hw + 0.18, cx - hw + 0.08], [cy, cy],
                color="#334155", lw=1.4, zorder=zorder+2)
        ax.text(cx, cy, "BATH TUB",
                ha="center", va="center", color="#0284C7",
                fontsize=5.0, fontweight="bold", zorder=zorder+3)

    @classmethod
    def _draw_shower(cls, ax, sx, sy, w=1.10, d=1.10, zorder=3):
        """Frameless glass shower with trench drain and rain head."""
        ax.add_patch(patches.Rectangle((sx, sy), w, d,
            facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.3, ls="--", zorder=zorder))
        ax.plot([sx + 0.10, sx + w - 0.10], [sy + 0.12, sy + 0.12],
                color="#0284C7", lw=2.5, solid_capstyle="round", zorder=zorder+1)
        shcx, shcy = sx + w/2, sy + d/2
        ax.add_patch(patches.Circle((shcx, shcy), 0.14,
            facecolor="none", edgecolor="#0284C7", lw=1.0, ls=":", zorder=zorder+1))
        ax.add_patch(patches.Circle((shcx, shcy), 0.04,
            facecolor="#0284C7", zorder=zorder+2))
        ax.text(shcx, sy + d * 0.76, "SHOWER\n(FRAMELESS)",
                ha="center", va="center", color="#0284C7",
                fontsize=4.6, fontweight="bold", zorder=zorder+3)

    @classmethod
    def _draw_ensuite_bathroom(cls, ax, min_x, min_y, rw, rh):
        m = 0.12
        # WC bottom-left
        cls._draw_wc(ax, min_x + m + 0.20, min_y + m + 0.32, 0.40, 0.64, "up", zorder=5)
        ax.text(min_x + m + 0.20, min_y + m + 0.70, "WC",
                ha="center", va="bottom", color="#0284C7", fontsize=4.8, fontweight="bold", zorder=6)
        # Shower bottom-right
        sh_s = min(min(rw * 0.42, rh * 0.42), 1.15)
        sh_x, sh_y = min_x + rw - m - sh_s, min_y + m
        cls._draw_shower(ax, sh_x, sh_y, sh_s, sh_s, zorder=4)
        # Bathtub top
        tub_w = min(1.60, rw - 2*m - 0.20)
        tub_d, tub_cx = 0.76, min_x + rw/2
        tub_cy = min_y + rh - m - tub_d/2
        cls._draw_bathtub(ax, tub_cx, tub_cy, tub_w, tub_d, zorder=4)
        # Vanity (remaining space)
        van_h = tub_cy - tub_d/2 - min_y - m - 0.64 - m - 0.20
        if van_h > 0.35:
            van_cx = min_x + m + (rw - sh_s - 2*m - 0.10) / 2
            van_w = rw - sh_s - 2*m - 0.10
            van_cy = min_y + m + 0.64 + m + 0.20 + van_h/2
            cls._draw_basin(ax, van_cx, van_cy, van_w, min(0.55, van_h), zorder=5)
            ax.text(van_cx, van_cy - min(0.55, van_h)/2 - 0.06, "VANITY",
                    ha="center", va="top", color="#0369A1", fontsize=4.8, fontweight="bold", zorder=6)

    @classmethod
    def _draw_secondary_bathroom(cls, ax, min_x, min_y, rw, rh):
        m = 0.10
        # WC
        wc_w, wc_d = 0.40, 0.64
        cls._draw_wc(ax, min_x + m + wc_w/2, min_y + m + wc_d/2, wc_w, wc_d, "up", zorder=5)
        ax.text(min_x + m + wc_w/2, min_y + m + wc_d + 0.06, "WC",
                ha="center", va="bottom", color="#0284C7", fontsize=4.8, fontweight="bold", zorder=6)
        # Basin
        van_w = min(0.65, rw - wc_w - 3*m)
        van_d = min(0.50, wc_d)
        van_cx = min_x + m + wc_w + m + van_w/2
        van_cy = min_y + m + van_d/2
        cls._draw_basin(ax, van_cx, van_cy, van_w, van_d, zorder=5)
        ax.text(van_cx, van_cy + van_d/2 + 0.06, "BASIN",
                ha="center", va="bottom", color="#0369A1", fontsize=4.8, fontweight="bold", zorder=6)
        # Tub or shower
        upper_h = rh - m - wc_d - m - m
        av_w = rw - 2*m
        if upper_h > 0.80 and av_w > 0.80:
            if rh > 1.80 and upper_h > 1.00:
                tub_w = min(1.55, av_w * 0.90)
                tub_d = min(0.74, upper_h * 0.80)
                cls._draw_bathtub(ax, min_x + rw/2,
                                  min_y + m + wc_d + m + tub_d/2, tub_w, tub_d, zorder=4)
            else:
                sh_s = min(upper_h * 0.90, av_w * 0.80, 1.10)
                cls._draw_shower(ax, min_x + rw/2 - sh_s/2,
                                  min_y + m + wc_d + m, sh_s, sh_s, zorder=4)

    @classmethod
    def _draw_powder_room(cls, ax, min_x, min_y, rw, rh):
        m = 0.12
        cls._draw_wc(ax, min_x + rw/2, min_y + m + 0.32, 0.38, 0.60, "up", zorder=5)
        van_w = min(0.80, rw - 2*m)
        van_d = 0.48
        cls._draw_basin(ax, min_x + rw/2, min_y + rh - m - van_d/2, van_w, van_d, zorder=5)
        ax.text(min_x + rw/2, min_y + rh/2, "POWDER ROOM",
                ha="center", va="center", color="#0369A1",
                fontsize=5.0, fontweight="bold", zorder=7)

    # =========================================================================
    # 7. BEDROOMS
    # =========================================================================

    @classmethod
    def draw_cad_bed_suite(cls, ax, cx, cy, rw, rh, is_master=False):
        """
        CAD bed suite matching reference bedroom floor plan images:
        headboard + mattress + duvet fold + pillows + nightstands + bench (master).
        """
        bed_w = 2.00 if is_master else 1.65
        bed_l = 2.10
        bx = cx - bed_w / 2.0
        by = cy - bed_l / 2.0 + 0.15

        hb_h = 0.20
        ax.add_patch(patches.Rectangle(
            (bx - 0.06, by + bed_l - hb_h), bed_w + 0.12, hb_h,
            facecolor="#334155", edgecolor="#0F172A", lw=1.5, zorder=3))
        ax.add_patch(patches.FancyBboxPatch(
            (bx, by), bed_w, bed_l - hb_h,
            boxstyle="round,pad=0.02,rounding_size=0.10",
            facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.4, zorder=3))
        duvet_h = (bed_l - hb_h) * 0.60
        ax.add_patch(patches.Rectangle(
            (bx + 0.04, by + 0.05), bed_w - 0.08, duvet_h,
            facecolor="#E2E8F0", edgecolor="#64748B", lw=0.9, zorder=4))
        ax.plot([bx + 0.04, bx + bed_w - 0.04],
                [by + duvet_h + 0.05, by + duvet_h + 0.05],
                color="#475569", lw=1.1, ls="--", zorder=5)
        p_w, p_h = 0.62, 0.38
        ax.add_patch(patches.FancyBboxPatch(
            (bx + 0.10, by + bed_l - hb_h - p_h - 0.06), p_w, p_h,
            boxstyle="round,pad=0.01,rounding_size=0.06",
            facecolor="#FFFFFF", edgecolor="#94A3B8", lw=0.9, zorder=5))
        ax.add_patch(patches.FancyBboxPatch(
            (bx + bed_w - p_w - 0.10, by + bed_l - hb_h - p_h - 0.06), p_w, p_h,
            boxstyle="round,pad=0.01,rounding_size=0.06",
            facecolor="#FFFFFF", edgecolor="#94A3B8", lw=0.9, zorder=5))
        ns = 0.50 if is_master else 0.42
        for ns_x in [bx - ns - 0.10, bx + bed_w + 0.10]:
            ns_y = by + bed_l - ns - hb_h - 0.10
            ax.add_patch(patches.FancyBboxPatch(
                (ns_x, ns_y), ns, ns,
                boxstyle="round,pad=0.01,rounding_size=0.06",
                facecolor="#F1F5F9", edgecolor="#0F172A", lw=1.1, zorder=3))
            ax.add_patch(patches.Circle((ns_x + ns/2, ns_y + ns/2), 0.11,
                facecolor="#FEF08A", edgecolor="#CA8A04", lw=0.9, zorder=4))
        if is_master:
            bench_w, bench_d = bed_w * 0.82, 0.38
            ax.add_patch(patches.FancyBboxPatch(
                (cx - bench_w/2, by - bench_d - 0.10), bench_w, bench_d,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.1, zorder=3))
            ax.text(cx, by - bench_d/2 - 0.10, "BENCH",
                    ha="center", va="center", color="#334155", fontsize=4.8, fontweight="bold", zorder=4)
            ax.text(cx, by + 0.42, "MASTER SUITE (KING)",
                    ha="center", va="center", color="#0F172A", fontsize=5.5, fontweight="bold", zorder=6)
        else:
            ax.text(cx, by + 0.42, "BEDROOM SUITE",
                    ha="center", va="center", color="#0F172A", fontsize=5.2, fontweight="bold", zorder=6)
