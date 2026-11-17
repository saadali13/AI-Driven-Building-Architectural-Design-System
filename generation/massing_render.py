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
from matplotlib.patches import Polygon as MplPolygon, Rectangle
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
# 3 DISTINCT ELEVATION STYLE THEMES (all strictly bound to the 2D layout solids)
# ---------------------------------------------------------------------------
ELEVATION_THEMES = {
    "modern_contemporary": {
        "id": "modern_contemporary",
        "name": "Modern Contemporary",
        "description": "Clean minimalist lines, charcoal architectural frames, large glass apertures, and subtle groove reveals.",
        "bg_paper": "#FFFFFF",
        "wall_fill": "#F8FAFC",
        "feature_fill": "#E2E8F0",
        "frame_color": "#1E293B",
        "accent_color": "#334155",
        "slab_fill": "#0F172A",
        "rail_style": "glass",         # full-panel glass balustrade with top rail
        "window_style": "picture",     # slim mullions, corner/frame focus
        "grooves": True,
        "texture": "groove",
    },
    "classical_traditional": {
        "id": "classical_traditional",
        "name": "Classical & Traditional",
        "description": "Timeless symmetrical mouldings, dentil cornice bands, fluted pilasters, arched lintel details, and wrought balusters.",
        "bg_paper": "#FAF9F6",
        "wall_fill": "#FFFDF7",
        "feature_fill": "#EFE8DA",
        "frame_color": "#3E2723",
        "accent_color": "#5D4037",
        "slab_fill": "#D7CCC8",
        "rail_style": "wrought",       # ornate vertical balusters with intermediate spindles
        "window_style": "arched",      # classic divided lites with moulded sill brackets
        "grooves": False,
        "texture": "cornice",
    },
    "minimalist_timber": {
        "id": "minimalist_timber",
        "name": "Minimalist Timber & Stone",
        "description": "Warm organic cedar louvers, slate accent cladding, floating monolithic parapet coping, and dark bronze mullions.",
        "bg_paper": "#FCFCFA",
        "wall_fill": "#F5F3EF",
        "feature_fill": "#E8DFC8",
        "frame_color": "#27272A",
        "accent_color": "#8C6D46",
        "slab_fill": "#3F3F46",
        "rail_style": "louver",        # warm architectural horizontal/vertical timber screen
        "window_style": "deep_recess", # deep shadow reveal casings
        "grooves": True,
        "texture": "timber_louvers",
    }
}


def _ft_in(v: float) -> str:
    total = int(round(abs(v) * 12))
    return f"{total // 12}'-{total % 12}\""


def _elev_window(ax, x, z, w, h, lw, vent=False, zo=5.0, theme=None):
    t = theme or ELEVATION_THEMES["modern_contemporary"]
    frame_col = t.get("frame_color", INK)
    w_style = t.get("window_style", "picture")

    # Main window opening
    ax.add_patch(Rectangle((x, z), w, h, facecolor="#F8FAFC", edgecolor=frame_col, linewidth=lw, zorder=zo))
    if w > 1.0 and h > 1.0:
        ax.add_patch(Rectangle((x + 0.2, z + 0.2), w - 0.4, h - 0.4, facecolor="#FFFFFF", edgecolor=t.get("accent_color", INK_MID),
                               linewidth=lw * 0.55, zorder=zo))

    if vent:
        for k in range(1, 4):
            ax.plot([x + 0.2, x + w - 0.2], [z + h * k / 4.0] * 2, color=t.get("accent_color", INK_MID), linewidth=lw * 0.5, zorder=zo)
    else:
        if w_style == "arched" and w >= 2.5:
            # Classical style: upper arch/divided lite decorative transom
            arch_h = min(1.4, h * 0.28)
            ax.plot([x + 0.2, x + w - 0.2], [z + h - arch_h, z + h - arch_h], color=frame_col, linewidth=lw * 0.65, zorder=zo)
            # 3 vertical panes in top transom
            for k in range(1, 4):
                ax.plot([x + w * k / 4.0, x + w * k / 4.0], [z + h - arch_h, z + h - 0.2], color=frame_col, linewidth=lw * 0.5, zorder=zo)
            # central mullion below
            ax.plot([x + w / 2.0, x + w / 2.0], [z + 0.2, z + h - arch_h], color=frame_col, linewidth=lw * 0.6, zorder=zo)
        elif w_style == "deep_recess":
            # Timber/Stone style: deep horizontal shadow louvers on upper glass
            n = 3 if w >= 5.5 else 2
            for k in range(1, n):
                ax.plot([x + w * k / n] * 2, [z + 0.2, z + h - 0.2], color=frame_col, linewidth=lw * 0.65, zorder=zo)
            for ly in [z + h * 0.55, z + h * 0.75, z + h * 0.9]:
                ax.plot([x + 0.25, x + w - 0.25], [ly, ly], color=t.get("accent_color", "#8C6D46"), linewidth=lw * 0.5, zorder=zo)
        else:
            # Modern picture window
            n = 3 if w >= 5.5 else 2
            for k in range(1, n):
                ax.plot([x + w * k / n] * 2, [z + 0.2, z + h - 0.2], color=frame_col, linewidth=lw * 0.6, zorder=zo)
            ax.plot([x + 0.2, x + w - 0.2], [z + h * 0.72] * 2, color=t.get("accent_color", INK_MID), linewidth=lw * 0.5, zorder=zo)

    # Sill & Lintel
    sill_color = t.get("slab_fill", "#CBD5E1")
    lintel_color = t.get("frame_color", INK)
    if w_style == "arched":
        # Classical moulded projecting bracket
        ax.add_patch(Rectangle((x - 0.45, z - 0.45), w + 0.9, 0.45, facecolor="#EFE8DA", edgecolor=frame_col, linewidth=lw * 0.65, zorder=zo))
        ax.add_patch(Rectangle((x - 0.3, z + h), w + 0.6, 0.4, facecolor="#D7CCC8", edgecolor=frame_col, linewidth=lw * 0.65, zorder=zo))
    elif w_style == "deep_recess":
        # Heavy timber projecting casing
        ax.add_patch(Rectangle((x - 0.4, z - 0.35), w + 0.8, 0.35, facecolor="#8C6D46", edgecolor=frame_col, linewidth=lw * 0.65, zorder=zo))
        ax.add_patch(Rectangle((x - 0.45, z + h), w + 0.9, 0.45, facecolor="#3F3F46", edgecolor=frame_col, linewidth=lw * 0.65, zorder=zo))
    else:
        # Modern slim projecting cantilever
        ax.add_patch(Rectangle((x - 0.3, z - 0.3), w + 0.6, 0.3, facecolor=sill_color, edgecolor=frame_col, linewidth=lw * 0.6, zorder=zo))
        ax.add_patch(Rectangle((x - 0.35, z + h), w + 0.7, 0.35, facecolor=lintel_color, edgecolor=lintel_color, linewidth=lw * 0.6, zorder=zo))


def _elev_door(ax, x, z, w, h, lw, main=False, zo=5.0, theme=None):
    t = theme or ELEVATION_THEMES["modern_contemporary"]
    frame_col = t.get("frame_color", INK)
    door_bg = t.get("wall_fill", "#F8FAFC")
    ax.add_patch(Rectangle((x, z), w, h, facecolor=door_bg, edgecolor=frame_col, linewidth=lw, zorder=zo))
    leaves = 2 if (main and w >= 3.6) else 1
    for k in range(leaves):
        lx = x + k * w / leaves
        ax.add_patch(Rectangle((lx + 0.2, z + 0.35), w / leaves - 0.4, h - 0.7, facecolor="#FFFFFF", edgecolor=t.get("accent_color", INK_MID),
                               linewidth=lw * 0.55, zorder=zo))
        # Handle / lockset indicator
        hx = lx + (w / leaves - 0.6) if k == 0 else lx + 0.5
        ax.plot([hx, hx], [z + 3.2, z + 3.7], color=frame_col, linewidth=lw * 1.1, zorder=zo + 0.05)
    if leaves == 2:
        ax.plot([x + w / 2.0] * 2, [z, z + h], color=frame_col, linewidth=lw * 0.7, zorder=zo)


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
    """Selects one of the 3 distinct elevation themes based on variant key or style hint."""
    if variant_key and variant_key in ELEVATION_THEMES:
        return ELEVATION_THEMES[variant_key]
    s = (style or "").lower()
    if any(k in s for k in ("classic", "spanish", "traditional", "victorian", "colonial")):
        return ELEVATION_THEMES["classical_traditional"]
    if any(k in s for k in ("timber", "wood", "stone", "minimal", "zen", "japandi", "warm")):
        return ELEVATION_THEMES["minimalist_timber"]
    return ELEVATION_THEMES["modern_contemporary"]


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
    W, total = m["W"], m["total_height"]
    fig_w = max(12.0, min(17.0, (W + 16.0) * 0.28))
    fig_h = max(9.0, min(17.0, (total + 10.0) * 0.28))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    bg_paper = theme.get("bg_paper", PAPER)
    fig.patch.set_facecolor(bg_paper)
    ax.set_facecolor(bg_paper)
    scale = max(0.7, min(1.3, 35.0 / max(W, total)))
    lw_h, lw_m, lw_l = 2.0 * scale, 1.2 * scale, 0.7 * scale

    frame_col = theme.get("frame_color", INK)
    accent_col = theme.get("accent_color", INK_MID)
    wall_fill = theme.get("wall_fill", "#FFFFFF")
    feature_fill = theme.get("feature_fill", "#E2E8F0")
    slab_fill = theme.get("slab_fill", "#CBD5E1")

    # Road line
    ax.plot([-1.35, W + 4.0], [0, 0], color=frame_col, linewidth=lw_h * 1.4, zorder=30)
    ax.add_patch(Rectangle((-1.35, -1.0), W + 3.35, 1.0, facecolor="#F1F5F9", edgecolor="none", zorder=1))

    # far solids first: what stands nearer the street is drawn over what stands behind it.
    solids = sorted(_merge_front([s for s in m["solids"] if s["z1"] > 0.4]), key=lambda s: (-s["y0"], s["z0"]))
    for k_, s in enumerate(solids):
        x, z, w, h = s["x0"], s["z0"], s["x1"] - s["x0"], s["z1"] - s["z0"]
        role = s["role"]
        heavy = role in ("wall", "mumty")
        zo = 4.0 + k_ * 0.02

        # Role-based color adaptation per theme
        if role == "wall":
            fc = wall_fill
        elif role == "plinth":
            fc = feature_fill
        elif role in ("slab", "column"):
            fc = slab_fill
        elif role == "parapet":
            fc = feature_fill
        elif role == "mumty":
            fc = wall_fill
        elif role == "cap":
            fc = frame_col
        else:
            fc = _ELEV_FILL.get(role, PAPER)

        ax.add_patch(Rectangle((x, z), w, h, facecolor=fc, edgecolor=frame_col,
                               linewidth=lw_h if heavy else lw_m, zorder=zo))

        # Architectural Facade Texture / Surface Details
        if role == "wall" and w >= 2.0 and h >= 3.0:
            if theme.get("texture") == "groove":
                # Modern horizontal reveals
                for gy in np.arange(z + 1.6, z + h - 0.5, 1.6):
                    ax.plot([x + 0.1, x + w - 0.1], [gy, gy], color="#E2E8F0", linewidth=lw_l * 0.65, zorder=zo + 0.005)
            elif theme.get("texture") == "timber_louvers":
                # Cedar vertical screening panel on wall piers (width between 2.0 and 8.0 ft)
                if 2.0 <= w <= 8.5:
                    for vx in np.arange(x + 0.35, x + w - 0.2, 0.45):
                        ax.plot([vx, vx], [z + 0.2, z + h - 0.2], color="#8C6D46", linewidth=lw_l * 0.9, zorder=zo + 0.006)
            elif theme.get("texture") == "cornice":
                # Classical decorative string course & quoins
                ax.plot([x, x + w], [z + h - 0.3, z + h - 0.3], color=accent_col, linewidth=lw_m * 0.9, zorder=zo + 0.005)
                ax.plot([x, x + w], [z + h - 0.5, z + h - 0.5], color=accent_col, linewidth=lw_l * 0.6, zorder=zo + 0.005)
                # Corner quoin stones
                if w >= 4.0:
                    for qy in np.arange(z + 0.5, z + h - 0.8, 1.4):
                        qw = min(1.2, w * 0.18)
                        ax.add_patch(Rectangle((x + 0.05, qy), qw, 0.6, facecolor="#EFE8DA", edgecolor=frame_col, linewidth=lw_l * 0.55, zorder=zo + 0.006))
                        ax.add_patch(Rectangle((x + w - qw - 0.05, qy), qw, 0.6, facecolor="#EFE8DA", edgecolor=frame_col, linewidth=lw_l * 0.55, zorder=zo + 0.006))

        # Classical parapet dentil moulding band
        if role == "parapet" and theme.get("texture") == "cornice" and w >= 3.0:
            for dx in np.arange(x + 0.3, x + w - 0.3, 0.8):
                ax.add_patch(Rectangle((dx, z + h - 0.55), 0.35, 0.3, facecolor="#D7CCC8", edgecolor=frame_col, linewidth=lw_l * 0.5, zorder=zo + 0.006))

        # Balustrade Railing Styling
        if role == "rail":
            r_style = theme.get("rail_style", "glass")
            if r_style == "glass":
                # Modern seamless glass balustrade with stainless top handrail
                ax.add_patch(Rectangle((x + 0.1, z + 0.1), w - 0.2, h - 0.2, facecolor="#86BEDD", alpha=0.35,
                                       edgecolor=accent_col, linewidth=lw_l, zorder=zo + 0.005))
                # Spigots / posts every 4.0 ft
                for bx in np.arange(x + 1.5, x + w - 0.5, 4.0):
                    ax.plot([bx, bx], [z, z + 0.5], color=frame_col, linewidth=lw_m * 1.5, zorder=zo + 0.008)
                ax.plot([x, x + w], [z + h, z + h], color=frame_col, linewidth=lw_m * 1.5, zorder=zo + 0.01)
            elif r_style == "wrought":
                # Classical wrought iron spindles with intermediate circles/spears
                for bx in np.arange(x + 0.4, x + w, 0.55):
                    ax.plot([bx, bx], [z, z + h], color=frame_col, linewidth=lw_l * 0.9, zorder=zo + 0.005)
                ax.plot([x, x + w], [z + h, z + h], color=frame_col, linewidth=lw_m * 1.4, zorder=zo + 0.008)
                ax.plot([x, x + w], [z + h - 0.4, z + h - 0.4], color=accent_col, linewidth=lw_l * 0.7, zorder=zo + 0.006)
            elif r_style == "louver":
                # Warm architectural horizontal timber slats
                for ly in np.arange(z + 0.4, z + h, 0.45):
                    ax.plot([x + 0.1, x + w - 0.1], [ly, ly], color="#8C6D46", linewidth=lw_m * 1.2, zorder=zo + 0.005)
                # Vertical stanchions
                for sx in np.arange(x + 0.8, x + w, 2.2):
                    ax.plot([sx, sx], [z, z + h], color=frame_col, linewidth=lw_m * 1.3, zorder=zo + 0.006)
                ax.plot([x, x + w], [z + h, z + h], color=frame_col, linewidth=lw_m * 1.5, zorder=zo + 0.008)
            else:
                for bx in [x + k * 0.9 for k in range(1, int(w / 0.9) + 1) if x + k * 0.9 < x + w - 0.1]:
                    ax.plot([bx, bx], [z, z + h], color=INK_MID, linewidth=lw_l * 0.8, zorder=zo)
                ax.plot([x, x + w], [z + h, z + h], color=INK, linewidth=lw_m * 1.3, zorder=zo)

        # Openings on front face (windows, vents, doors)
        for o in s["open"]:
            if o["face"] != "front":
                continue
            ow, oh = o["a1"] - o["a0"], o["z1"] - o["z0"]
            if o["kind"] in ("door", "main"):
                _elev_door(ax, o["a0"], o["z0"], ow, oh, lw_m, main=o["kind"] == "main", zo=zo + 0.01, theme=theme)
            else:
                _elev_window(ax, o["a0"], o["z0"], ow, oh, lw_m, vent=o["kind"] == "vent", zo=zo + 0.01, theme=theme)

    # datum levels on the left
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

    # overall height (right) and width (bottom)
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
            f"   |   STYLE: {theme_label}   |   SCALE: 1/8\" = 1'-0\"",
            ha="center", va="top", fontsize=max(7.0, 9.0 * scale), fontweight="bold", color=frame_col)

    ax.set_xlim(-13.5, W + 6.5)
    ax.set_ylim(-6.6, total + 3.0)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout(pad=0.4)

    # Filename suffix distinguishes the variant
    suffix = f"_{variant_key}" if variant_key else ""
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
    Renders 3 distinct architectural front elevation styles for the exact same layout solids:
    1. Modern Contemporary
    2. Classical & Traditional
    3. Minimalist Timber & Stone
    Returns a dict mapping style key to output file path.
    """
    res: Dict[str, str] = {}
    for v_key in ELEVATION_THEMES.keys():
        path = render_front_elevation(layout, project_id, style, out_dir, dpi=dpi, variant_key=v_key)
        res[v_key] = path
    # Also ensure the primary elevation is always available
    primary_theme = _resolve_theme(style)
    res["primary"] = res.get(primary_theme["id"]) or render_front_elevation(layout, project_id, style, out_dir, dpi=dpi)
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
