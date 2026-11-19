"""
One 3D massing model, built from the analysed plan geometry, drawn two ways:

* ``render_front_elevation`` - the orthographic front elevation (every storey, every street-side window and door
  at its plan position, terraces with railings, porch canopy, parapet, stair mumty);
* ``render_3d_views``        - shaded axonometric 3D views of the same solids.

Because both drawings come from the same solids as the floor plans, they cannot disagree with the plans.
This is a CAD massing visualisation - not a structural or municipal approval drawing.
"""
from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon as MplPolygon, Rectangle, Wedge
import numpy as np
from shapely.geometry import box as sbox
from shapely.ops import unary_union

OPEN_AIR = {"porch", "outdoor", "ots", "pool"}
EPS = 1e-6

PLINTH_H = 2.5
PARAPET_H = 3.0
MUMTY_H = 8.5
RAIL_H = 3.0


def _enclosed(r: Dict[str, Any]) -> bool:
    return r.get("category") not in OPEN_AIR


def _rect(r: Dict[str, Any]) -> Tuple[float, float, float, float]:
    x, y = float(r["x_ft"]), float(r["y_ft"])
    return x, y, x + float(r["w_ft"]), y + float(r["l_ft"])


def _solid(role: str, x0, y0, x1, y1, z0, z1, **kw) -> Dict[str, Any]:
    s = {"role": role, "x0": float(x0), "y0": float(y0), "x1": float(x1), "y1": float(y1),
         "z0": float(z0), "z1": float(z1), "open": []}
    s.update(kw)
    return s


def level_heights(layout: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[float], List[float], Optional[Dict[str, Any]]]:
    """(storeys, floor level of each storey, height of each storey, designed roof level or None)."""
    elev = layout.get("elevation_features") or {}
    gf_h = float(elev.get("ground_floor_height_ft", 11.0))
    up_h = float(elev.get("first_floor_height_ft", 10.5))
    storeys = [f for f in layout.get("floors", []) if not f.get("roof")]
    roof = next((f for f in layout.get("floors", []) if f.get("roof")), None)
    heights = [gf_h if i == 0 else up_h for i in range(len(storeys))]
    base, z = [], float(elev.get("plinth_height_ft", PLINTH_H))
    for h in heights:
        base.append(z)
        z += h
    return storeys, base, heights, roof


def _edge_exposed(r: Dict[str, Any], others: List[Dict[str, Any]], side: str) -> bool:
    """True when most of this edge of an open terrace has no room or terrace of the same level against it."""
    x0, y0, x1, y1 = _rect(r)
    covered = 0.0
    for o in others:
        if o is r or o.get("category") == "ots":
            continue
        a0, b0, a1, b1 = _rect(o)
        if side == "front" and abs(b1 - y0) < 0.05:
            covered += max(0.0, min(x1, a1) - max(x0, a0))
        elif side == "back" and abs(b0 - y1) < 0.05:
            covered += max(0.0, min(x1, a1) - max(x0, a0))
        elif side == "left" and abs(a1 - x0) < 0.05:
            covered += max(0.0, min(y1, b1) - max(y0, b0))
        elif side == "right" and abs(a0 - x1) < 0.05:
            covered += max(0.0, min(y1, b1) - max(y0, b0))
    length = (x1 - x0) if side in ("front", "back") else (y1 - y0)
    return covered < 0.5 * length


def build_massing(layout: Dict[str, Any]) -> Dict[str, Any]:
    """The building as axis-aligned solids (feet; x across the plot, y from the street to the back, z up)."""
    W = float(layout.get("plot_width_ft", 35.0))
    L = float(layout.get("plot_length_ft", 65.0))
    storeys, base, heights, roof = level_heights(layout)
    plinth = base[0] if base else PLINTH_H
    solids: List[Dict[str, Any]] = []
    box_of: Dict[Tuple[int, str], Dict[str, Any]] = {}

    for i, fl in enumerate(storeys):
        z0, z1 = base[i], base[i] + heights[i]
        rooms = fl.get("rooms", [])
        for r in rooms:
            x0, y0, x1, y1 = _rect(r)
            cat, nm = r.get("category"), str(r.get("name", "")).upper()
            if _enclosed(r):
                if i == 0:
                    solids.append(_solid("plinth", x0, y0, x1, y1, 0.0, plinth))
                s = _solid("wall", x0, y0, x1, y1, z0, z1, level=i, name=nm, top_is_roof=(i == len(storeys) - 1))
                solids.append(s)
                box_of[(i, r.get("id"))] = s
            elif cat == "ots":
                continue
            elif i == 0:
                if cat == "porch":
                    solids.append(_solid("paving", x0, y0, x1, y1, 0.0, 0.3))
                    cw = 0.9
                    for cx in (x0 + 0.1, x1 - cw - 0.1):
                        solids.append(_solid("column", cx, y0 + 0.1, cx + cw, y0 + 0.1 + cw, 0.3, z1 - 0.6))
                    solids.append(_solid("slab", x0, y0, x1, y1, z1 - 0.6, z1))
                elif cat == "pool":
                    solids.append(_solid("water", x0, y0, x1, y1, 0.0, 0.2))
                elif any(k in nm for k in ("LAWN", "GARDEN", "GREEN")):
                    solids.append(_solid("lawn", x0, y0, x1, y1, 0.0, 0.15))
                else:
                    solids.append(_solid("paving", x0, y0, x1, y1, 0.0, 0.2))
            else:
                # an open terrace / balcony upstairs: a railing along every edge that is not against a room.
                # Nothing is drawn where no built space stands under it (a terrace cannot hang over a lawn).
                below = [sbox(*_rect(o)) for o in storeys[i - 1].get("rooms", [])
                         if _enclosed(o) or o.get("category") == "porch"]
                me = sbox(x0, y0, x1, y1)
                if not below or unary_union(below).intersection(me).area < 0.5 * me.area:
                    if min(x1 - x0, y1 - y0) > 8.0:
                        continue
                    # a shallow balcony may project on its own slab
                    solids.append(_solid("slab", x0, y0, x1, y1, z0 - 0.4, z0))
                t = 0.3
                if _edge_exposed(r, rooms, "front"):
                    solids.append(_solid("rail", x0, y0, x1, y0 + t, z0, z0 + RAIL_H))
                if _edge_exposed(r, rooms, "back"):
                    solids.append(_solid("rail", x0, y1 - t, x1, y1, z0, z0 + RAIL_H))
                if _edge_exposed(r, rooms, "left") and (y1 - y0) > 2 * t + 0.2:
                    solids.append(_solid("rail", x0, y0 + t, x0 + t, y1 - t, z0, z0 + RAIL_H))
                if _edge_exposed(r, rooms, "right") and (y1 - y0) > 2 * t + 0.2:
                    solids.append(_solid("rail", x1 - t, y0 + t, x1, y1 - t, z0, z0 + RAIL_H))

        # openings of this storey, attached to the wall box they are cut into
        by_id = {r.get("id"): r for r in rooms}
        sill = z0 + 3.0
        for w in fl.get("windows", []):
            s = box_of.get((i, w.get("room_id")))
            if s is None:
                continue
            vent = w.get("kind") == "ventilator"
            zz = (z0 + 6.3, z0 + 8.0) if vent else (sill, sill + 4.5)
            if w.get("orient") == "h":
                face = "front" if int(w.get("into", 1)) > 0 else "back"
            else:
                face = "left" if int(w.get("into", 1)) > 0 else "right"
            s["open"].append({"kind": "vent" if vent else "window", "face": face, "a0": float(w["s"]),
                              "a1": float(w["e"]), "z0": zz[0], "z1": zz[1]})
        for d in fl.get("doors", []):
            if d.get("kind") in ("arch", "gate"):
                continue
            a, b = by_id.get(d.get("room_id")), by_id.get(d.get("from_id"))
            a_in = a is not None and _enclosed(a)
            b_in = b is not None and _enclosed(b)
            if a_in == b_in:
                continue                        # an inside door, or a door between two open spaces
            into = int(d.get("into", 1))        # direction from the wall into room_id
            host, outward = (a, -into) if a_in else (b, into)
            s = box_of.get((i, host.get("id")))
            if s is None:
                continue
            if d.get("orient") == "h":
                face = "front" if outward < 0 else "back"
            else:
                face = "left" if outward < 0 else "right"
            s["open"].append({"kind": "main" if str(d.get("kind", "")).startswith("main") else "door", "face": face,
                              "a0": float(d["s"]), "a1": float(d["e"]), "z0": z0, "z1": z0 + 7.0})

    top = base[-1] + heights[-1] if base else plinth
    mumty_rects: List[Tuple[float, float, float, float]] = []
    if storeys:
        if roof:
            for r in roof.get("rooms", []):
                if _enclosed(r):
                    mumty_rects.append(_rect(r))
        else:
            st = next((r for r in storeys[-1].get("rooms", []) if r.get("category") == "stair"), None)
            if st is not None and len(storeys) > 0:
                mumty_rects.append(_rect(st))
        for (x0, y0, x1, y1) in mumty_rects:
            solids.append(_solid("mumty", x0, y0, x1, y1, top, top + MUMTY_H))
            solids.append(_solid("cap", x0 - 0.4, y0 - 0.4, x1 + 0.4, y1 + 0.4, top + MUMTY_H, top + MUMTY_H + 0.5))

        # parapet along the edge of the top roof
        tops = [sbox(*_rect(r)) for r in storeys[-1].get("rooms", []) if _enclosed(r)]
        if tops:
            u = unary_union(tops).buffer(0)
            polys = [u] if u.geom_type == "Polygon" else list(getattr(u, "geoms", []))
            t = 0.35
            for poly in polys:
                for ring in [poly.exterior] + list(poly.interiors):
                    pts = list(ring.coords)
                    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
                        if math.hypot(bx - ax, by - ay) < 0.6:
                            continue
                        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
                        if any(x0 - 0.05 <= mx <= x1 + 0.05 and y0 - 0.05 <= my <= y1 + 0.05
                               for (x0, y0, x1, y1) in mumty_rects):
                            continue
                        if abs(ay - by) < EPS:                       # runs along x
                            inside_up = poly.contains(sbox(mx - 0.1, my + 0.05, mx + 0.1, my + 0.2))
                            ya, yb = (my, my + t) if inside_up else (my - t, my)
                            solids.append(_solid("parapet", min(ax, bx), ya, max(ax, bx), yb, top, top + PARAPET_H))
                        elif abs(ax - bx) < EPS:                     # runs along y
                            inside_right = poly.contains(sbox(mx + 0.05, my - 0.1, mx + 0.2, my + 0.1))
                            xa, xb = (mx, mx + t) if inside_right else (mx - t, mx)
                            solids.append(_solid("parapet", xa, min(ay, by) + t, xb, max(ay, by) - t, top, top + PARAPET_H))

    solids = [s for s in solids if s["x1"] - s["x0"] > 0.02 and s["y1"] - s["y0"] > 0.02 and s["z1"] - s["z0"] > 0.02]
    total = max([s["z1"] for s in solids] + [top])
    return {"W": W, "L": L, "solids": solids, "base": base, "heights": heights, "plinth": plinth, "top": top,
            "storeys": len(storeys), "has_mumty": bool(mumty_rects), "total_height": total,
            "labels": [str(f.get("label") or f"LEVEL {i}").upper() for i, f in enumerate(storeys)]}


# ---------------------------------------------------------------------------
# FRONT ELEVATION (orthographic, seen from the street)
# ---------------------------------------------------------------------------

INK = "#000000"
INK_MID = "#334155"
INK_LIGHT = "#94A3B8"
PAPER = "#FFFFFF"

_ELEV_FILL = {
    "wall": "#FFFFFF", "plinth": "#E2E8F0", "slab": "#CBD5E1", "column": "#CBD5E1", "rail": "#F8FAFC",
    "parapet": "#F1F5F9", "mumty": "#FFFFFF", "cap": "#000000"
}

# ---------------------------------------------------------------------------
# 4 DISTINCT ARCHITECTURAL FACADE MODELS (all 100% aligned to 2D plan solids)
# ---------------------------------------------------------------------------
ELEVATION_MODELS = {
    "modern_cantilever": {
        "id": "modern_cantilever",
        "name": "Modern Cantilever & Frame Grid",
        "badge": "Box Frame & Glass",
        "description": "Bold cantilevered dark-charcoal portal frames, recessed shadow-gap soffits, pergola porch canopy, and frameless glass balustrades.",
        "bg_paper": "#FFFFFF",
        "sky_tint": "#F1F7FB",
        "wall_fill": "#F8FAFC",
        "upper_wall_fill": "#FFFFFF",
        "feature_fill": "#CBD5E1",
        "frame_color": "#1E293B",
        "accent_color": "#0F172A",
        "slab_fill": "#1E293B",
        "glass_fill": "#CFE6F5",
        "door_fill": "#5C4033",
        "rail_style": "glass",
        "window_style": "cantilever_box",
        "roof_style": "cantilever_portal",
    },
    "spanish_neoclassical": {
        "id": "spanish_neoclassical",
        "name": "Spanish / Neoclassical Villa",
        "badge": "Arches & Terracotta",
        "description": "Sculpted arched window crowns, fluted pilasters with capitals, dentil cornice bands, pitched terracotta roof hoods, and wrought-iron balustrades.",
        "bg_paper": "#FCFBF7",
        "sky_tint": "#F5F8FC",
        "wall_fill": "#FFFDF6",
        "upper_wall_fill": "#FDF8EC",
        "feature_fill": "#EAE0CE",
        "frame_color": "#4A3222",
        "accent_color": "#A34828",
        "slab_fill": "#D9CCB8",
        "glass_fill": "#D8EAF4",
        "door_fill": "#6B3E26",
        "rail_style": "wrought",
        "window_style": "arched_pediment",
        "roof_style": "terracotta_pitched",
    },
    "brick_timber_sloped": {
        "id": "brick_timber_sloped",
        "name": "Contemporary Brick, Timber & Sloped Roof",
        "badge": "Brick & Sloped Canopy",
        "description": "Exposed terracotta-brick masonry piers, vertical cedar timber louvers, sloped standing-seam porch & mumty canopies, and horizontal timber railings.",
        "bg_paper": "#FCFCFA",
        "sky_tint": "#F2F6F9",
        "wall_fill": "#F4F1EA",
        "upper_wall_fill": "#EFEBE2",
        "feature_fill": "#D9CBB8",
        "frame_color": "#27272A",
        "accent_color": "#9A4B31",
        "timber_color": "#9B6B3B",
        "slab_fill": "#3F3F46",
        "glass_fill": "#C9DFEE",
        "door_fill": "#6E4726",
        "rail_style": "timber_louver",
        "window_style": "deep_bronze",
        "roof_style": "sloped_canopy",
    },
    "jaali_courtyard": {
        "id": "jaali_courtyard",
        "name": "Pakistani Jaali & Travertine Stone",
        "badge": "Jaali & Planters",
        "description": "Geometric perforated jaali privacy screens, travertine ashlar stone bands, cantilevered upper planter boxes, and recessed entrance portal.",
        "bg_paper": "#FAF9F5",
        "sky_tint": "#F3F7F4",
        "wall_fill": "#F6F3EB",
        "upper_wall_fill": "#FAF8F2",
        "feature_fill": "#E2D9C5",
        "frame_color": "#26322B",
        "accent_color": "#23483D",
        "slab_fill": "#CBBFA8",
        "glass_fill": "#CFE2DD",
        "door_fill": "#4E3829",
        "rail_style": "jaali_screen",
        "window_style": "travertine_recess",
        "roof_style": "stepped_crown",
    },
}

# Backward-compatible aliases so existing callers/tests keep working seamlessly
_STYLE_ALIASES = {
    "modern_contemporary": "modern_cantilever",
    "classical_traditional": "spanish_neoclassical",
    "minimalist_timber": "brick_timber_sloped",
}
ELEVATION_THEMES = ELEVATION_MODELS


def _ft_in(v: float) -> str:
    total = int(round(abs(v) * 12))
    return f"{total // 12}'-{total % 12}\""


def _draw_shadow(ax, x, z, w, h, zo, alpha=0.14):
    ax.add_patch(Rectangle((x, z), w, h, facecolor="#0F172A", edgecolor="none", alpha=alpha, zorder=zo))


def _draw_jaali_pattern(ax, x, z, w, h, frame_col, accent_col, lw, zo):
    """Draws a crisp geometric Islamic/Pakistani perforated jaali lattice inside (x, z, w, h)."""
    ax.add_patch(Rectangle((x, z), w, h, facecolor="#EFE9DC", edgecolor=frame_col, linewidth=lw * 0.85, zorder=zo))
    step = max(0.55, min(0.85, min(w, h) / 4.0))
    nx = max(1, int(w / step))
    nz = max(1, int(h / step))
    dx, dz = w / nx, h / nz
    for ix in range(nx):
        for iz in range(nz):
            cx = x + (ix + 0.5) * dx
            cz = z + (iz + 0.5) * dz
            diamond = MplPolygon(
                [(cx, cz + dz * 0.36), (cx + dx * 0.36, cz), (cx, cz - dz * 0.36), (cx - dx * 0.36, cz)],
                closed=True, facecolor="#3A4740", edgecolor=accent_col, alpha=0.45, linewidth=lw * 0.35, zorder=zo + 0.004
            )
            ax.add_patch(diamond)


def _draw_brick_panel(ax, x, z, w, h, lw, zo):
    """Draws exposed terracotta-brick courses over a solid masonry pier."""
    ax.add_patch(Rectangle((x, z), w, h, facecolor="#B85D43", edgecolor="#5A2A1C", linewidth=lw * 0.7, zorder=zo))
    course_h = 0.42
    brick_w = 1.05
    row = 0
    y = z + course_h
    while y < z + h - 0.05:
        ax.plot([x, x + w], [y, y], color="#EADCD2", linewidth=lw * 0.38, alpha=0.75, zorder=zo + 0.003)
        offset = (brick_w * 0.5) if (row % 2 == 1) else 0.0
        bx = x + offset + brick_w
        while bx < x + w - 0.1:
            ax.plot([bx, bx], [y - course_h, y], color="#EADCD2", linewidth=lw * 0.32, alpha=0.65, zorder=zo + 0.003)
            bx += brick_w
        y += course_h
        row += 1


def _draw_terracotta_roof_band(ax, x, z, w, pitch_h, frame_col, lw, zo):
    """Draws a pitched Spanish terracotta roof hood with clay-tile ribs."""
    poly = MplPolygon(
        [(x - 0.5, z), (x + w + 0.5, z), (x + w - 0.8, z + pitch_h), (x + 0.8, z + pitch_h)],
        closed=True, facecolor="#B64B2C", edgecolor=frame_col, linewidth=lw * 0.9, zorder=zo
    )
    ax.add_patch(poly)
    # Clay tile ribs
    n_ribs = max(4, int(w / 0.85))
    for i in range(1, n_ribs):
        t = i / n_ribs
        bx = (x - 0.3) + t * (w + 0.6)
        tx = (x + 0.8) + t * (w - 1.6)
        ax.plot([bx, tx], [z, z + pitch_h], color="#7A2D18", linewidth=lw * 0.45, alpha=0.75, zorder=zo + 0.005)
    # Ridge cap
    ax.plot([x + 0.75, x + w - 0.75], [z + pitch_h, z + pitch_h], color="#5A2010", linewidth=lw * 1.1, zorder=zo + 0.006)
    _draw_shadow(ax, x - 0.35, z - 0.4, w + 0.7, 0.4, zo - 0.001, alpha=0.18)


def _draw_sloped_metal_canopy(ax, x, z, w, rise_h, frame_col, lw, zo, slope_right=True):
    """Draws a contemporary sloped standing-seam architectural canopy."""
    if slope_right:
        pts = [(x - 0.4, z), (x + w + 0.4, z), (x + w + 0.4, z + rise_h * 0.32), (x - 0.4, z + rise_h)]
    else:
        pts = [(x - 0.4, z), (x + w + 0.4, z), (x + w + 0.4, z + rise_h), (x - 0.4, z + rise_h * 0.32)]
    ax.add_patch(MplPolygon(pts, closed=True, facecolor="#3F444A", edgecolor=frame_col, linewidth=lw * 0.95, zorder=zo))
    # Standing seam lines
    for sx in np.arange(x + 0.5, x + w, 1.3):
        frac = (sx - (x - 0.4)) / (w + 0.8)
        top_y = (z + rise_h * (1.0 - 0.68 * frac)) if slope_right else (z + rise_h * (0.32 + 0.68 * frac))
        ax.plot([sx, sx], [z + 0.05, top_y - 0.05], color="#9CA3AF", linewidth=lw * 0.45, alpha=0.7, zorder=zo + 0.004)
    _draw_shadow(ax, x - 0.35, z - 0.45, w + 0.7, 0.45, zo - 0.001, alpha=0.2)


def _elev_window(ax, x, z, w, h, lw, vent=False, zo=5.0, theme=None):
    t = theme or ELEVATION_MODELS["modern_cantilever"]
    frame_col = t.get("frame_color", INK)
    accent_col = t.get("accent_color", INK_MID)
    glass_col = t.get("glass_fill", "#D6E8F5")
    w_style = t.get("window_style", "cantilever_box")

    # Drop shadow beneath opening
    _draw_shadow(ax, x + 0.15, z - 0.45, w, 0.45, zo - 0.002, alpha=0.14)

    # Outer casing + glass
    ax.add_patch(Rectangle((x, z), w, h, facecolor=frame_col, edgecolor=frame_col, linewidth=lw * 0.9, zorder=zo))
    if w > 0.8 and h > 0.8:
        ax.add_patch(Rectangle((x + 0.22, z + 0.22), w - 0.44, h - 0.44, facecolor=glass_col,
                               edgecolor=frame_col, linewidth=lw * 0.5, zorder=zo + 0.002))
        # Subtle glass reflection sheen
        ax.plot([x + 0.45, x + min(w - 0.45, 1.45)], [z + 0.55, z + min(h - 0.45, 1.95)],
                color="#FFFFFF", linewidth=lw * 0.9, alpha=0.75, zorder=zo + 0.004)
        ax.plot([x + 0.85, x + min(w - 0.45, 1.65)], [z + 0.55, z + min(h - 0.45, 1.55)],
                color="#FFFFFF", linewidth=lw * 0.55, alpha=0.65, zorder=zo + 0.004)

    if vent:
        for k in range(1, 4):
            ax.plot([x + 0.22, x + w - 0.22], [z + h * k / 4.0] * 2, color=frame_col, linewidth=lw * 0.55, zorder=zo + 0.005)
    else:
        if w_style == "arched_pediment" and w >= 2.2:
            # Spanish/Neoclassical: semicircular moulded arch hood + keystone + French divided panes
            arch_r = min(w * 0.46, 1.6)
            cx = x + w / 2.0
            ax.add_patch(Wedge((cx, z + h), arch_r, 0, 180, width=0.42, facecolor="#EAE0CE",
                               edgecolor=frame_col, linewidth=lw * 0.7, zorder=zo + 0.006))
            ax.add_patch(Wedge((cx, z + h), max(0.1, arch_r - 0.42), 0, 180, facecolor=glass_col,
                               edgecolor=frame_col, linewidth=lw * 0.45, zorder=zo + 0.005))
            # Keystone at arch apex
            ax.add_patch(Rectangle((cx - 0.22, z + h + arch_r - 0.45), 0.44, 0.55, facecolor="#D9CCB8",
                                   edgecolor=frame_col, linewidth=lw * 0.55, zorder=zo + 0.007))
            # French muntins
            n_v = 3 if w >= 5.0 else 2
            for k in range(1, n_v):
                ax.plot([x + w * k / n_v] * 2, [z + 0.22, z + h - 0.22], color=frame_col, linewidth=lw * 0.55, zorder=zo + 0.005)
            for frac in (0.36, 0.68):
                ax.plot([x + 0.22, x + w - 0.22], [z + h * frac] * 2, color=frame_col, linewidth=lw * 0.45, zorder=zo + 0.005)
            # Moulded sill with corbel brackets
            ax.add_patch(Rectangle((x - 0.45, z - 0.42), w + 0.9, 0.42, facecolor="#EAE0CE", edgecolor=frame_col, linewidth=lw * 0.65, zorder=zo + 0.006))
            for bx in (x - 0.25, x + w - 0.15):
                ax.add_patch(Rectangle((bx, z - 0.82), 0.4, 0.4, facecolor="#D9CCB8", edgecolor=frame_col, linewidth=lw * 0.5, zorder=zo + 0.005))
        elif w_style == "deep_bronze":
            # Deep cantilevered bronze window box + upper timber sun-breaker fins
            ax.add_patch(Rectangle((x - 0.38, z - 0.35), w + 0.76, h + 0.72, facecolor="none",
                                   edgecolor=frame_col, linewidth=lw * 1.45, zorder=zo + 0.006))
            ax.add_patch(Rectangle((x - 0.42, z + h), w + 0.84, 0.42, facecolor=t.get("timber_color", "#9B6B3B"),
                                   edgecolor=frame_col, linewidth=lw * 0.65, zorder=zo + 0.007))
            n_v = 3 if w >= 5.5 else 2
            for k in range(1, n_v):
                ax.plot([x + w * k / n_v] * 2, [z + 0.22, z + h - 0.22], color=frame_col, linewidth=lw * 0.65, zorder=zo + 0.005)
            ax.plot([x + 0.22, x + w - 0.22], [z + h * 0.75] * 2, color=frame_col, linewidth=lw * 0.55, zorder=zo + 0.005)
        elif w_style == "travertine_recess":
            # Deep travertine stone surround + slender vertical sun-louvers on one edge
            ax.add_patch(Rectangle((x - 0.35, z - 0.35), w + 0.7, h + 0.7, facecolor="none",
                                   edgecolor="#B8A98E", linewidth=lw * 1.5, zorder=zo + 0.005))
            n_v = 3 if w >= 5.2 else 2
            for k in range(1, n_v):
                ax.plot([x + w * k / n_v] * 2, [z + 0.22, z + h - 0.22], color=frame_col, linewidth=lw * 0.6, zorder=zo + 0.005)
            ax.add_patch(Rectangle((x - 0.42, z + h), w + 0.84, 0.42, facecolor=accent_col, edgecolor=frame_col, linewidth=lw * 0.6, zorder=zo + 0.007))
            ax.add_patch(Rectangle((x - 0.38, z - 0.35), w + 0.76, 0.35, facecolor="#D6CCB8", edgecolor=frame_col, linewidth=lw * 0.55, zorder=zo + 0.006))
        else:
            # Modern Cantilever Box: projecting charcoal sunshade canopy + crisp picture mullions
            n_v = 3 if w >= 5.5 else 2
            for k in range(1, n_v):
                ax.plot([x + w * k / n_v] * 2, [z + 0.22, z + h - 0.22], color=frame_col, linewidth=lw * 0.65, zorder=zo + 0.005)
            ax.plot([x + 0.22, x + w - 0.22], [z + h * 0.76] * 2, color=frame_col, linewidth=lw * 0.5, zorder=zo + 0.005)
            ax.add_patch(Rectangle((x - 0.35, z - 0.28), w + 0.7, 0.28, facecolor="#CBD5E1", edgecolor=frame_col, linewidth=lw * 0.6, zorder=zo + 0.006))
            ax.add_patch(Rectangle((x - 0.48, z + h), w + 0.96, 0.48, facecolor=accent_col, edgecolor=frame_col, linewidth=lw * 0.7, zorder=zo + 0.007))
            _draw_shadow(ax, x - 0.35, z + h - 0.35, w + 0.7, 0.35, zo + 0.004, alpha=0.18)


def _elev_door(ax, x, z, w, h, lw, main=False, zo=5.0, theme=None):
    t = theme or ELEVATION_MODELS["modern_cantilever"]
    frame_col = t.get("frame_color", INK)
    door_fill = t.get("door_fill", "#6B4423")
    r_style = t.get("roof_style", "cantilever_portal")

    # Portal surround for main entrance door
    if main:
        ax.add_patch(Rectangle((x - 0.45, z), w + 0.9, h + 0.55, facecolor=t.get("feature_fill", "#CBD5E1"),
                               edgecolor=frame_col, linewidth=lw * 0.9, zorder=zo - 0.002))
        if r_style == "terracotta_pitched":
            arch_r = min(w * 0.48, 1.8)
            ax.add_patch(Wedge((x + w / 2.0, z + h), arch_r, 0, 180, width=0.45, facecolor="#EAE0CE",
                               edgecolor=frame_col, linewidth=lw * 0.75, zorder=zo + 0.004))

    ax.add_patch(Rectangle((x, z), w, h, facecolor=door_fill, edgecolor=frame_col, linewidth=lw, zorder=zo))
    leaves = 2 if (main and w >= 3.6) else 1
    for k in range(leaves):
        lx = x + k * w / leaves
        lw_leaf = w / leaves
        ax.add_patch(Rectangle((lx + 0.22, z + 0.35), lw_leaf - 0.44, h - 0.7, facecolor=door_fill,
                               edgecolor="#D9C3A3", linewidth=lw * 0.5, zorder=zo + 0.003))
        # Horizontal modern grooves on door leaf
        for gy in np.arange(z + 1.4, z + h - 0.8, 1.3):
            ax.plot([lx + 0.3, lx + lw_leaf - 0.3], [gy, gy], color="#3A2314", linewidth=lw * 0.4, alpha=0.6, zorder=zo + 0.004)
        # Tall architectural pull handle
        hx = lx + (lw_leaf - 0.55) if k == 0 else lx + 0.55
        ax.plot([hx, hx], [z + 2.6, z + 4.2], color="#E2E8F0", linewidth=lw * 1.4, zorder=zo + 0.006)
    if leaves == 2:
        ax.plot([x + w / 2.0] * 2, [z, z + h], color=frame_col, linewidth=lw * 0.8, zorder=zo + 0.005)


def _merge_front(solids: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Joins solids that share a front plane, a height band and a role, and touch side by side."""
    groups: Dict[Tuple, List[Dict[str, Any]]] = {}
    for s in solids:
        key = (s["role"], round(s["y0"], 2), round(s["z0"], 2), round(s["z1"], 2))
        groups.setdefault(key, []).append(s)
    out: List[Dict[str, Any]] = []
    for key, items in groups.items():
        if key[0] not in ("wall", "plinth", "parapet", "rail"):
            out.extend(items)
            continue
        items = sorted(items, key=lambda s: s["x0"])
        cur = dict(items[0], open=list(items[0]["open"]))
        for s in items[1:]:
            if s["x0"] <= cur["x1"] + 0.05:
                cur["x1"] = max(cur["x1"], s["x1"])
                cur["y1"] = max(cur["y1"], s["y1"])
                cur["open"] = cur["open"] + list(s["open"])
            else:
                out.append(cur)
                cur = dict(s, open=list(s["open"]))
        out.append(cur)
    return out


def _resolve_theme(style: str, variant_key: Optional[str] = None) -> Dict[str, Any]:
    """Selects one of the 4 distinct architectural facade models (with backward-compatible aliases)."""
    if variant_key:
        vk = _STYLE_ALIASES.get(variant_key, variant_key)
        if vk in ELEVATION_MODELS:
            return ELEVATION_MODELS[vk]
    s = (style or "").lower()
    if any(k in s for k in ("classic", "spanish", "traditional", "victorian", "colonial", "neoclassic")):
        return ELEVATION_MODELS["spanish_neoclassical"]
    if any(k in s for k in ("brick", "timber", "wood", "sloped", "pitched", "chalet", "hill")):
        return ELEVATION_MODELS["brick_timber_sloped"]
    if any(k in s for k in ("jaali", "islamic", "courtyard", "travertine", "stone", "pakistani")):
        return ELEVATION_MODELS["jaali_courtyard"]
    return ELEVATION_MODELS["modern_cantilever"]


def render_front_elevation(
    layout: Dict[str, Any],
    project_id: str,
    style: str,
    out_dir: str,
    dpi: int = 220,
    variant_key: Optional[str] = None
) -> str:
    m = build_massing(layout)
    theme = _resolve_theme(style, variant_key)
    model_id = theme["id"]
    W, total = m["W"], m["total_height"]
    extra_top = 3.2 if model_id in ("spanish_neoclassical", "brick_timber_sloped") else 1.5
    fig_w = max(12.5, min(17.5, (W + 16.0) * 0.29))
    fig_h = max(9.5, min(17.5, (total + extra_top + 10.0) * 0.29))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    bg_paper = theme.get("bg_paper", PAPER)
    fig.patch.set_facecolor(bg_paper)
    ax.set_facecolor(bg_paper)
    scale = max(0.7, min(1.3, 35.0 / max(W, total)))
    lw_h, lw_m, lw_l = 2.0 * scale, 1.2 * scale, 0.7 * scale

    frame_col = theme.get("frame_color", INK)
    accent_col = theme.get("accent_color", INK_MID)
    wall_fill = theme.get("wall_fill", "#FFFFFF")
    upper_wall_fill = theme.get("upper_wall_fill", wall_fill)
    feature_fill = theme.get("feature_fill", "#E2E8F0")
    slab_fill = theme.get("slab_fill", "#CBD5E1")

    # Subtle architectural sky wash behind the building envelope
    ax.add_patch(Rectangle((-2.5, 0.0), W + 5.5, total + extra_top + 1.5,
                           facecolor=theme.get("sky_tint", "#F4F8FB"), edgecolor="none", zorder=0.5))

    # Ground road plane & subtle pavement texture
    ax.plot([-1.35, W + 4.0], [0, 0], color=frame_col, linewidth=lw_h * 1.45, zorder=30)
    ax.add_patch(Rectangle((-1.35, -1.1), W + 3.55, 1.1, facecolor="#E2E8F0", edgecolor="none", zorder=1))

    # Far solids first: nearer solids cover farther ones (exact 2D plan depth order)
    solids = sorted(_merge_front([s for s in m["solids"] if s["z1"] > 0.4]), key=lambda s: (-s["y0"], s["z0"]))

    for k_, s in enumerate(solids):
        x, z, w, h = s["x0"], s["z0"], s["x1"] - s["x0"], s["z1"] - s["z0"]
        role = s["role"]
        lvl = int(s.get("level") or 0)
        heavy = role in ("wall", "mumty")
        zo = 4.0 + k_ * 0.02

        if role == "wall":
            fc = upper_wall_fill if lvl >= 1 else wall_fill
        elif role == "plinth":
            fc = feature_fill
        elif role in ("slab", "column"):
            fc = slab_fill
        elif role == "parapet":
            fc = feature_fill
        elif role == "mumty":
            fc = upper_wall_fill
        elif role == "cap":
            fc = frame_col
        else:
            fc = _ELEV_FILL.get(role, PAPER)

        ax.add_patch(Rectangle((x, z), w, h, facecolor=fc, edgecolor=frame_col,
                               linewidth=lw_h if heavy else lw_m, zorder=zo))

        # --- MODEL-SPECIFIC ARCHITECTURAL FACADE MASSING & DETAILING ---
        front_opens = [o for o in s["open"] if o["face"] == "front"]

        # 1. Plinth detailing
        if role == "plinth" and w >= 3.0:
            if model_id == "spanish_neoclassical":
                for px in np.arange(x + 1.5, x + w - 0.5, 2.0):
                    ax.plot([px, px], [z, z + h], color=frame_col, linewidth=lw_l * 0.5, alpha=0.45, zorder=zo + 0.004)
            elif model_id == "jaali_courtyard":
                ax.plot([x, x + w], [z + h * 0.5, z + h * 0.5], color=frame_col, linewidth=lw_l * 0.5, alpha=0.4, zorder=zo + 0.004)

        # 2. Porch Canopy Slab & Columns
        if role == "slab":
            _draw_shadow(ax, x, z - 0.65, w, 0.65, zo - 0.002, alpha=0.20)
            if model_id == "modern_cantilever" and w >= 5.0:
                # Sleek pergola louver slats above porch canopy
                for lx in np.arange(x + 0.7, x + w - 0.5, 1.1):
                    ax.add_patch(Rectangle((lx, z + h), 0.35, 0.45, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_l * 0.5, zorder=zo + 0.006))
            elif model_id == "brick_timber_sloped" and w >= 6.0 and z < (m["base"][0] + (m["heights"][0] if m["heights"] else 11.0) + 1.0):
                # Sloped standing-seam architectural porch canopy
                _draw_sloped_metal_canopy(ax, x, z + h, w, min(2.0, max(1.2, w * 0.12)), frame_col, lw_m, zo + 0.007, slope_right=True)
            elif model_id == "spanish_neoclassical" and w >= 5.0:
                # Stepped moulded porch entablature
                ax.add_patch(Rectangle((x - 0.35, z + h), w + 0.7, 0.45, facecolor="#EAE0CE", edgecolor=frame_col, linewidth=lw_m * 0.8, zorder=zo + 0.006))

        if role == "column":
            if model_id == "spanish_neoclassical":
                # Classical column base & capital + fluting
                ax.add_patch(Rectangle((x - 0.2, z), w + 0.4, 0.65, facecolor="#EAE0CE", edgecolor=frame_col, linewidth=lw_l * 0.8, zorder=zo + 0.005))
                ax.add_patch(Rectangle((x - 0.25, z + h - 0.65), w + 0.5, 0.65, facecolor="#EAE0CE", edgecolor=frame_col, linewidth=lw_l * 0.8, zorder=zo + 0.005))
                ax.plot([x + w * 0.5, x + w * 0.5], [z + 0.7, z + h - 0.7], color=frame_col, linewidth=lw_l * 0.5, alpha=0.5, zorder=zo + 0.004)
            elif model_id == "brick_timber_sloped":
                # Brick-clad porch pier
                _draw_brick_panel(ax, x, z, w, h, lw_l, zo + 0.003)

        # 3. Wall Facade Articulation (Model-Specific)
        if role == "wall" and w >= 2.0 and h >= 3.0:
            if model_id == "modern_cantilever":
                # Subtle horizontal reveals + bold cantilevered dark portal frame on upper storeys
                for gy in np.arange(z + 2.0, z + h - 0.5, 2.0):
                    ax.plot([x + 0.1, x + w - 0.1], [gy, gy], color="#CBD5E1", linewidth=lw_l * 0.55, zorder=zo + 0.003)
                if lvl >= 1 and w >= 6.0:
                    # Cantilevered charcoal architectural box frame wrapping the upper volume
                    t_f = 0.55
                    ax.add_patch(Rectangle((x - 0.35, z + h - t_f), w + 0.7, t_f + 0.15, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_m, zorder=zo + 0.006))
                    ax.add_patch(Rectangle((x - 0.35, z - 0.15), w + 0.7, t_f, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_m, zorder=zo + 0.006))
                    ax.add_patch(Rectangle((x - 0.35, z), t_f, h, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_m, zorder=zo + 0.006))
                    ax.add_patch(Rectangle((x + w - t_f + 0.35, z), t_f, h, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_m, zorder=zo + 0.006))
                    _draw_shadow(ax, x - 0.2, z - 0.85, w + 0.4, 0.7, zo + 0.001, alpha=0.18)

            elif model_id == "spanish_neoclassical":
                # Classical string-course cornice + fluted corner pilasters + quoining
                ax.add_patch(Rectangle((x - 0.25, z + h - 0.55), w + 0.5, 0.55, facecolor="#EAE0CE", edgecolor=frame_col, linewidth=lw_m * 0.85, zorder=zo + 0.005))
                if w >= 5.0:
                    pw = min(1.3, w * 0.11)
                    for px in (x + 0.05, x + w - pw - 0.05):
                        ax.add_patch(Rectangle((px, z), pw, h - 0.55, facecolor="#F5EFE2", edgecolor=frame_col, linewidth=lw_l * 0.75, zorder=zo + 0.004))
                        ax.plot([px + pw * 0.35] * 2, [z + 0.6, z + h - 1.0], color=frame_col, linewidth=lw_l * 0.4, alpha=0.45, zorder=zo + 0.005)
                        ax.plot([px + pw * 0.65] * 2, [z + 0.6, z + h - 1.0], color=frame_col, linewidth=lw_l * 0.4, alpha=0.45, zorder=zo + 0.005)
                        # Pilaster capital
                        ax.add_patch(Rectangle((px - 0.15, z + h - 1.05), pw + 0.3, 0.5, facecolor="#D9CCB8", edgecolor=frame_col, linewidth=lw_l * 0.7, zorder=zo + 0.006))

            elif model_id == "brick_timber_sloped":
                # Exposed brick feature zone on clear solid wall intervals + vertical cedar louvers
                intervals = sorted([(o["a0"], o["a1"]) for o in front_opens])
                solid_spans: List[Tuple[float, float]] = []
                cur_x = x
                for a0, a1 in intervals:
                    if a0 - cur_x >= 2.2:
                        solid_spans.append((cur_x + 0.2, a0 - 0.2))
                    cur_x = max(cur_x, a1)
                if x + w - cur_x >= 2.2:
                    solid_spans.append((cur_x + 0.2, x + w - 0.2))
                for idx_sp, (sx0, sx1) in enumerate(solid_spans):
                    sw = sx1 - sx0
                    if sw >= 3.2 and idx_sp % 2 == 0:
                        _draw_brick_panel(ax, sx0, z + 0.15, min(sw, 7.5), h - 0.3, lw_l, zo + 0.003)
                    elif sw >= 2.0:
                        # Vertical cedar timber louver screen
                        ax.add_patch(Rectangle((sx0, z + 0.2), min(sw, 5.5), h - 0.4, facecolor="#EDE6D6", edgecolor="none", zorder=zo + 0.002))
                        for vx in np.arange(sx0 + 0.25, sx0 + min(sw, 5.5) - 0.15, 0.42):
                            ax.plot([vx, vx], [z + 0.25, z + h - 0.25], color="#9B6B3B", linewidth=lw_m * 0.9, zorder=zo + 0.004)
                # Concrete slab shadow band
                ax.add_patch(Rectangle((x - 0.2, z + h - 0.45), w + 0.4, 0.45, facecolor=slab_fill, edgecolor=frame_col, linewidth=lw_m * 0.85, zorder=zo + 0.005))

            elif model_id == "jaali_courtyard":
                # Travertine ashlar horizontal stone bands + geometric jaali accent pier
                for gy in np.arange(z + 1.4, z + h - 0.3, 1.4):
                    ax.plot([x + 0.1, x + w - 0.1], [gy, gy], color="#CBBFA8", linewidth=lw_l * 0.65, zorder=zo + 0.003)
                intervals = sorted([(o["a0"], o["a1"]) for o in front_opens])
                cur_x = x
                for a0, a1 in intervals:
                    if a0 - cur_x >= 2.6:
                        jw = min(4.2, a0 - cur_x - 0.6)
                        _draw_jaali_pattern(ax, cur_x + 0.3, z + 0.5, jw, h - 1.0, frame_col, accent_col, lw_l, zo + 0.004)
                        break
                    cur_x = max(cur_x, a1)
                else:
                    if x + w - cur_x >= 2.6:
                        jw = min(4.2, x + w - cur_x - 0.6)
                        _draw_jaali_pattern(ax, cur_x + 0.3, z + 0.5, jw, h - 1.0, frame_col, accent_col, lw_l, zo + 0.004)

        # 4. Parapet Crown & Roofline Treatment
        if role == "parapet" and w >= 2.5:
            if model_id == "spanish_neoclassical":
                # Dentil moulding + pitched terracotta roof hood above parapet
                for dx_d in np.arange(x + 0.35, x + w - 0.35, 0.75):
                    ax.add_patch(Rectangle((dx_d, z + h - 0.6), 0.35, 0.32, facecolor="#D9CCB8", edgecolor=frame_col, linewidth=lw_l * 0.5, zorder=zo + 0.005))
                _draw_terracotta_roof_band(ax, x, z + h, w, min(2.4, max(1.4, w * 0.075)), frame_col, lw_m, zo + 0.006)
            elif model_id == "modern_cantilever":
                # Floating dark monolithic parapet coping with shadow reveal
                ax.add_patch(Rectangle((x - 0.55, z + h - 0.55), w + 1.1, 0.65, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_m, zorder=zo + 0.006))
                _draw_shadow(ax, x - 0.4, z + h - 0.95, w + 0.8, 0.4, zo + 0.004, alpha=0.18)
            elif model_id == "jaali_courtyard":
                # Stepped double-coping crown + perforated parapet breeze strip
                ax.add_patch(Rectangle((x - 0.35, z + h - 0.45), w + 0.7, 0.5, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_m * 0.9, zorder=zo + 0.006))
                if w >= 5.0:
                    _draw_jaali_pattern(ax, x + 0.8, z + 0.45, w - 1.6, max(1.2, h - 1.1), frame_col, accent_col, lw_l * 0.85, zo + 0.004)
            elif model_id == "brick_timber_sloped":
                # Timber fascia band along parapet top
                ax.add_patch(Rectangle((x - 0.4, z + h - 0.5), w + 0.8, 0.55, facecolor="#9B6B3B", edgecolor=frame_col, linewidth=lw_m * 0.9, zorder=zo + 0.006))

        # 5. Stair Mumty Tower Roof Treatment
        if role == "mumty" and w >= 2.5:
            # Clerestory daylight ribbon window on mumty
            cw = min(w * 0.55, 5.5)
            cx = x + (w - cw) / 2.0
            ax.add_patch(Rectangle((cx, z + h * 0.48), cw, min(2.6, h * 0.32), facecolor=theme.get("glass_fill", "#D6E8F5"),
                                   edgecolor=frame_col, linewidth=lw_m * 0.8, zorder=zo + 0.005))
            if model_id == "spanish_neoclassical":
                _draw_terracotta_roof_band(ax, x, z + h, w, min(2.8, max(1.6, w * 0.22)), frame_col, lw_m, zo + 0.008)
            elif model_id == "brick_timber_sloped":
                _draw_sloped_metal_canopy(ax, x, z + h, w, min(2.6, max(1.6, w * 0.22)), frame_col, lw_m, zo + 0.008, slope_right=False)
            elif model_id == "jaali_courtyard":
                _draw_jaali_pattern(ax, cx, z + h * 0.48, cw, min(2.6, h * 0.32), frame_col, accent_col, lw_l, zo + 0.006)
            elif model_id == "modern_cantilever":
                ax.add_patch(Rectangle((x - 0.6, z + h), w + 1.2, 0.65, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_m, zorder=zo + 0.007))

        # 6. Balcony / Terrace Railing Styling
        if role == "rail":
            r_style = theme.get("rail_style", "glass")
            if r_style == "glass":
                ax.add_patch(Rectangle((x + 0.08, z + 0.08), w - 0.16, h - 0.16, facecolor="#7CC4E8", alpha=0.38,
                                       edgecolor=accent_col, linewidth=lw_l, zorder=zo + 0.005))
                for bx in np.arange(x + 1.2, x + w - 0.4, 3.2):
                    ax.plot([bx, bx], [z, z + 0.55], color=frame_col, linewidth=lw_m * 1.6, zorder=zo + 0.007)
                ax.plot([x, x + w], [z + h, z + h], color=frame_col, linewidth=lw_m * 1.6, zorder=zo + 0.008)
            elif r_style == "wrought":
                for bx in np.arange(x + 0.4, x + w, 0.55):
                    ax.plot([bx, bx], [z, z + h], color=frame_col, linewidth=lw_l * 0.9, zorder=zo + 0.005)
                # Ornamental rings near top rail
                for rx_c in np.arange(x + 0.7, x + w - 0.4, 1.1):
                    ax.add_patch(Circle((rx_c, z + h - 0.45), 0.22, facecolor="none", edgecolor=frame_col, linewidth=lw_l * 0.75, zorder=zo + 0.006))
                ax.plot([x, x + w], [z + h, z + h], color=frame_col, linewidth=lw_m * 1.5, zorder=zo + 0.008)
                ax.plot([x, x + w], [z + h - 0.7, z + h - 0.7], color=frame_col, linewidth=lw_l * 0.7, zorder=zo + 0.006)
            elif r_style == "timber_louver":
                for ly in np.arange(z + 0.4, z + h, 0.45):
                    ax.plot([x + 0.1, x + w - 0.1], [ly, ly], color="#9B6B3B", linewidth=lw_m * 1.25, zorder=zo + 0.005)
                for sx in np.arange(x + 0.8, x + w, 2.2):
                    ax.plot([sx, sx], [z, z + h], color=frame_col, linewidth=lw_m * 1.3, zorder=zo + 0.006)
                ax.plot([x, x + w], [z + h, z + h], color=frame_col, linewidth=lw_m * 1.5, zorder=zo + 0.008)
            elif r_style == "jaali_screen":
                _draw_jaali_pattern(ax, x, z, w, h, frame_col, accent_col, lw_l, zo + 0.005)
                # Cantilevered planter box with greenery along balcony front edge
                ax.add_patch(Rectangle((x - 0.15, z - 0.55), w + 0.3, 0.6, facecolor=accent_col, edgecolor=frame_col, linewidth=lw_l, zorder=zo + 0.007))
                for gx in np.arange(x + 0.9, x + w - 0.6, 1.8):
                    ax.add_patch(Circle((gx, z + 0.35), 0.42, facecolor="#5C8D67", edgecolor="#23483D", alpha=0.85, linewidth=lw_l * 0.5, zorder=zo + 0.008))

        # 7. Exact Plan-Aligned Front Openings (Windows, Vents, Doors)
        for o in front_opens:
            ow, oh = o["a1"] - o["a0"], o["z1"] - o["z0"]
            if o["kind"] in ("door", "main"):
                _elev_door(ax, o["a0"], o["z0"], ow, oh, lw_m, main=o["kind"] == "main", zo=zo + 0.01, theme=theme)
            else:
                _elev_window(ax, o["a0"], o["z0"], ow, oh, lw_m, vent=o["kind"] == "vent", zo=zo + 0.01, theme=theme)

    # Datum levels on the left
    def datum(z, label):
        ax.plot([-4.2, W + 1.2], [z, z], color=INK_LIGHT, linewidth=lw_l * 0.75, linestyle=(0, (6, 4)), zorder=2)
        ax.add_patch(MplPolygon([[-1.4, z], [-2.1, z + 0.55], [-2.1, z - 0.55]], closed=True, facecolor=frame_col,
                                edgecolor=frame_col, zorder=31))
        txt = f"{label}  (+{_ft_in(z)})" if z > 0 else f"{label}  (±0'-0\")"
        ax.text(-2.4, z, txt, ha="right", va="center", fontsize=max(5.5, 6.8 * scale), fontweight="bold", color=frame_col,
                zorder=32)

    ordinal = ["GROUND", "FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
    datum(0.0, "ROAD LVL")
    for i, z in enumerate(m["base"]):
        datum(z, "PLINTH / GROUND FFL" if i == 0 else f"{ordinal[i] if i < len(ordinal) else f'LEVEL {i}'} FLOOR FFL")
    datum(m["top"], "ROOF SLAB LVL")
    datum(m["top"] + PARAPET_H, "PARAPET TOP")
    if m["has_mumty"]:
        datum(m["top"] + MUMTY_H + 0.5, "MUMTY TOP")

    # Overall height (right) and width (bottom)
    dx = W + 3.0
    ax.plot([dx, dx], [0, total], color=frame_col, linewidth=lw_l, zorder=12)
    for py in (0, total):
        ax.plot([dx - 0.4, dx + 0.4], [py - 0.4, py + 0.4], color=frame_col, linewidth=lw_m, zorder=13)
    ax.text(dx + 0.9, total / 2.0, f"TOTAL HEIGHT: {_ft_in(total)}", ha="center", va="center", rotation=90,
            fontsize=max(6.0, 7.5 * scale), fontweight="bold", color=frame_col)
    dy = -2.2
    ax.plot([0, W], [dy, dy], color=frame_col, linewidth=lw_l, zorder=12)
    for px in (0, W):
        ax.plot([px - 0.4, px + 0.4], [dy - 0.4, dy + 0.4], color=frame_col, linewidth=lw_m, zorder=13)
    ax.text(W / 2.0, dy - 0.5, f"OVERALL WIDTH: {_ft_in(W)}", ha="center", va="top", fontsize=max(6.0, 7.5 * scale),
            fontweight="bold", color=frame_col)

    theme_label = theme.get("name", style).upper()
    ax.text(W / 2.0, -4.6,
            f"FRONT ELEVATION (STREET SIDE)   |   {m['storeys']} STOREY(S)   |   PLOT: {_ft_in(W)} × {_ft_in(m['L'])}"
            f"   |   MODEL: {theme_label}   |   SCALE: 1/8\" = 1'-0\"",
            ha="center", va="top", fontsize=max(7.0, 9.0 * scale), fontweight="bold", color=frame_col)

    ax.set_xlim(-13.5, W + 6.5)
    ax.set_ylim(-6.6, total + extra_top + 2.5)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout(pad=0.4)

    suffix = f"_{model_id}" if variant_key else ""
    fpath = os.path.join(out_dir, f"{project_id}_front_elevation_2d{suffix}.png")
    plt.savefig(fpath, dpi=dpi, bbox_inches="tight", facecolor=bg_paper)
    plt.close(fig)
    return fpath


def render_all_elevation_styles(
    layout: Dict[str, Any],
    project_id: str,
    style: str,
    out_dir: str,
    dpi: int = 220
) -> Dict[str, str]:
    """
    Renders 4 genuinely distinct architectural front elevation models for the exact same 2D plan solids:
      1. modern_cantilever    — Modern Cantilever & Frame Grid
      2. spanish_neoclassical — Spanish / Neoclassical Villa
      3. brick_timber_sloped  — Contemporary Brick, Timber & Sloped Roof
      4. jaali_courtyard      — Pakistani Jaali & Travertine Stone
    Also populates backward-compatible alias keys (`modern_contemporary`, `classical_traditional`, `minimalist_timber`).
    """
    res: Dict[str, str] = {}
    for v_key in ELEVATION_MODELS.keys():
        path = render_front_elevation(layout, project_id, style, out_dir, dpi=dpi, variant_key=v_key)
        res[v_key] = path
    for old_k, new_k in _STYLE_ALIASES.items():
        res[old_k] = res[new_k]
    primary_theme = _resolve_theme(style)
    res["primary"] = res.get(primary_theme["id"]) or res["modern_cantilever"]
    return res


# ---------------------------------------------------------------------------
# 3D VIEWS (shaded axonometric projection of the same solids)
# ---------------------------------------------------------------------------

# role -> (top, front, side) colours
_C3 = {
    "wall": ("#CFC8B8", "#F4EFE4", "#D9D2C2"),
    "roof": ("#B9B2A3", "#F4EFE4", "#D9D2C2"),
    "plinth": ("#9AA0A8", "#B4B9C0", "#8E949C"),
    "slab": ("#D8D2C4", "#E9E4D8", "#C6BFB0"),
    "column": ("#D8D2C4", "#E9E4D8", "#C6BFB0"),
    "parapet": ("#D8D2C4", "#EFEADF", "#CFC8B8"),
    "mumty": ("#B9B2A3", "#F4EFE4", "#D9D2C2"),
    "cap": ("#8A8478", "#A39C8E", "#7C766B"),
    "rail": ("#5B6470", "#6B7480", "#4A525D"),
    "lawn": ("#8DBB6E", "#7BA85E", "#6E9954"),
    "paving": ("#C7CBD1", "#B5B9BF", "#A6AAB0"),
    "water": ("#7CC4E8", "#6BB2D6", "#5FA3C6"),
}
_GLASS, _FRAME, _DOOR = "#86BEDD", "#2F3B4B", "#8A5A36"


def _order(solids: List[Dict[str, Any]], side: int) -> List[Dict[str, Any]]:
    """Back-to-front drawing order for a camera in front of the plot, to its right (side=+1) or left (side=-1),
    looking down. Two boxes that a plane separates have a fixed order; a topological sort joins the pairs."""
    n = len(solids)
    after: List[List[int]] = [[] for _ in range(n)]      # after[i] = boxes that must be drawn after i
    indeg = [0] * n
    e = 1e-3

    def first(a, b) -> int:
        """-1: a is drawn before b, 1: b before a, 0: no constraint."""
        if a["y0"] >= b["y1"] - e:
            return -1
        if b["y0"] >= a["y1"] - e:
            return 1
        if side > 0:
            if a["x1"] <= b["x0"] + e:
                return -1
            if b["x1"] <= a["x0"] + e:
                return 1
        else:
            if a["x0"] >= b["x1"] - e:
                return -1
            if b["x0"] >= a["x1"] - e:
                return 1
        if a["z1"] <= b["z0"] + e:
            return -1
        if b["z1"] <= a["z0"] + e:
            return 1
        return 0

    for i in range(n):
        for j in range(i + 1, n):
            c = first(solids[i], solids[j])
            if c < 0:
                after[i].append(j)
                indeg[j] += 1
            elif c > 0:
                after[j].append(i)
                indeg[i] += 1

    def depth(s):       # larger = farther from the camera
        return s["y0"] - side * s["x0"] * 0.6 - s["z0"] * 0.3

    out, done = [], [False] * n
    ready = [i for i in range(n) if indeg[i] == 0]
    while len(out) < n:
        if not ready:   # a cycle (rare): release the farthest box that is still waiting
            ready = [max((i for i in range(n) if not done[i]), key=lambda i: depth(solids[i]))]
        ready.sort(key=lambda i: -depth(solids[i]))
        i = ready.pop(0)
        if done[i]:
            continue
        done[i] = True
        out.append(solids[i])
        for j in after[i]:
            indeg[j] -= 1
            if indeg[j] == 0 and not done[j]:
                ready.append(j)
    return out


def _render_view(m: Dict[str, Any], side: int, title: str, fpath: str, dpi: int) -> str:
    az, tilt = math.radians(38.0), math.radians(27.0)
    ca, sa, ct, st = math.cos(az), math.sin(az), math.cos(tilt), math.sin(tilt)

    def P(x, y, z):
        sx = x * ca + side * y * sa
        d = -side * x * sa + y * ca
        return (sx, z * ct + d * st)

    W, L = m["W"], m["L"]
    fig, ax = plt.subplots(figsize=(13.0, 10.0), dpi=dpi)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    pts: List[Tuple[float, float]] = []

    def poly(points3, color, lw=0.5, edge="#3A3F47", z=3):
        p2 = [P(*p) for p in points3]
        pts.extend(p2)
        ax.add_patch(MplPolygon(p2, closed=True, facecolor=color, edgecolor=edge, linewidth=lw, zorder=z, joinstyle="round"))

    # ground: the street in front, then the plot
    poly([(-8, -14, 0), (W + 8, -14, 0), (W + 8, -2, 0), (-8, -2, 0)], "#B9BDC4", lw=0.0, edge="none", z=1)
    poly([(-8, -2, 0), (W + 8, -2, 0), (W + 8, L + 6, 0), (-8, L + 6, 0)], "#E7E9EC", lw=0.0, edge="none", z=1)
    poly([(0, 0, 0), (W, 0, 0), (W, L, 0), (0, L, 0)], "#D7DADF", lw=0.6, z=1)

    for s in _order(m["solids"], side):
        x0, x1, y0, y1, z0, z1 = s["x0"], s["x1"], s["y0"], s["y1"], s["z0"], s["z1"]
        role = "roof" if (s["role"] == "wall" and s.get("top_is_roof")) else s["role"]
        c_top, c_front, c_side = _C3.get(role, _C3["wall"])
        xs = x1 if side > 0 else x0                       # the side face the camera sees
        thin = (z1 - z0) < 0.5
        lw = 0.25 if thin else 0.55
        poly([(xs, y0, z0), (xs, y1, z0), (xs, y1, z1), (xs, y0, z1)], c_side, lw)
        poly([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], c_front, lw)
        poly([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], c_top, lw)
        seen = "right" if side > 0 else "left"
        for o in s["open"]:
            if o["face"] == "front":
                q = [(o["a0"], y0, o["z0"]), (o["a1"], y0, o["z0"]), (o["a1"], y0, o["z1"]), (o["a0"], y0, o["z1"])]
            elif o["face"] == seen:
                q = [(xs, o["a0"], o["z0"]), (xs, o["a1"], o["z0"]), (xs, o["a1"], o["z1"]), (xs, o["a0"], o["z1"])]
            else:
                continue
            is_door = o["kind"] in ("door", "main")
            poly(q, _DOOR if is_door else _GLASS, lw=0.9, edge=_FRAME)
            if not is_door and o["kind"] == "window":   # a mullion down the middle
                am = (o["a0"] + o["a1"]) / 2.0
                a, b = ((am, y0, o["z0"]), (am, y0, o["z1"])) if o["face"] == "front" else \
                    ((xs, am, o["z0"]), (xs, am, o["z1"]))
                (ax1, ay1), (ax2, ay2) = P(*a), P(*b)
                ax.plot([ax1, ax2], [ay1, ay2], color=_FRAME, linewidth=0.7, zorder=3)

    xs_, ys_ = [p[0] for p in pts], [p[1] for p in pts]
    pad = 3.0
    ax.set_xlim(min(xs_) - pad, max(xs_) + pad)
    ax.set_ylim(min(ys_) - pad - 3.0, max(ys_) + pad)
    ax.text((min(xs_) + max(xs_)) / 2.0, min(ys_) - pad - 1.0, title, ha="center", va="center", fontsize=10,
            fontweight="bold", color="#111827")
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout(pad=0.3)
    plt.savefig(fpath, dpi=dpi, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(fig)
    return fpath


def render_3d_views(layout: Dict[str, Any], project_id: str, style: str, out_dir: str, dpi: int = 160) -> Dict[str, str]:
    """Two shaded 3D views (front-right and front-left). Returns {"front_right": path, "front_left": path}."""
    m = build_massing(layout)
    info = f"{m['storeys']} STOREY(S)   |   PLOT: {_ft_in(m['W'])} × {_ft_in(m['L'])}   |   HEIGHT: {_ft_in(m['total_height'])}"
    out = {}
    for key, side, name in (("front_right", 1, "FRONT-RIGHT"), ("front_left", -1, "FRONT-LEFT")):
        out[key] = _render_view(m, side, f"3D VIEW ({name})   |   {info}   |   STYLE: {style.upper()}",
                                os.path.join(out_dir, f"{project_id}_3d_view_{key}.png"), dpi)
    return out


def three_d_nodes(layout: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The same solids as a flat list (feet), for the OBJ / Blender exporters and any 3D viewer."""
    # x / y / z are the CENTRE of each box (y is up), which is what the OBJ and Blender exporters expect
    return [{"role": s["role"], "name": s.get("name") or s["role"], "category": s["role"], "level": s.get("level"),
             "x": (s["x0"] + s["x1"]) / 2.0, "y": (s["z0"] + s["z1"]) / 2.0, "z": (s["y0"] + s["y1"]) / 2.0,
             "width": s["x1"] - s["x0"], "height": s["z1"] - s["z0"], "depth": s["y1"] - s["y0"],
             "openings": s["open"]} for s in build_massing(layout)["solids"]]
