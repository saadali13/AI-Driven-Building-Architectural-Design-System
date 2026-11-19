"""
Gemini CAD Engine - prompt-driven residential design
=====================================================

  1. Brief    - the client's words are read (plot, storeys, rooms, must-haves); the guided interview asks about gaps.
  2. Concepts - Gemini proposes several different layout ideas for the brief.
  3. Script   - Gemini writes an ArchiScript (generation.design_script): the plot cut into rectangles, one level
                at a time. The prompt explains how the engine works; it carries no bylaw list and no RAG.
  4. Engine   - generation.plan_geometry_engine (Shapely + NetworkX) builds walls, doors, windows and furniture
                and checks only physical things: doors on shared walls, walking routes, daylight, the stair,
                furniture that fits, terraces that stand on something.
  5. Repair   - problems go back to Gemini by line number: line edits when few are left, a fresh start on another
                concept when repairs stall.
  6. Review   - Gemini reviews its own finished design as an architect in Pakistan and may improve it.
  7. Drawings - plans, elevation and 3D views (generation.massing_render) all come from the one checked model.

Software CAD validation only - not a structural certificate or a municipal approval.
"""

import os
import sys
import concurrent.futures
import gc
import json
import random
import hashlib
import math
import uuid
import datetime
import re
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, PathPatch, Rectangle, Circle, Polygon as MplPolygon
from matplotlib.path import Path as MplPath
from shapely.geometry import Point, box
from shapely.ops import unary_union

from google import genai
from google.genai import types

from config.gemini_config import GeminiConfig
from generation import massing_render
from generation.pakistan_rag import build_planner_context
from generation.plan_geometry_engine import (
    EXT_WALL, _pt, analyse_layout, build_wall_geometry, classify_room,
    format_issues_for_llm, is_enclosed, room_clear_rect,
)
from generation.brief_parser import (
    LLM_EXTRACTION_PROMPT, apply_message_to_requirements, build_checklist, check_requirements,
    compliance_checklist, merge_llm_requirements, merge_llm_site, parse_brief, read_site,
)
from generation.design_script import (
    build_converse_prompt, build_script_prompt, build_script_repair_prompt, build_stage_prompt, extract_script,
    parse_script, script_issue_lines,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER_DPI = 220             # sheet resolution; lowered for one retry if the machine runs out of memory
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "web_generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Strongest spatial reasoner first; the lite model is only a last resort (verified 2026-11-12 on v1beta)
ACTIVE_MODELS = ["gemini-3-flash-preview", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.0-flash"]

# ---------------------------------------------------------------------------
# STANDARD ARCHITECTURAL CAD PALETTE (Monochrome Technical Ink on Paper)
# ---------------------------------------------------------------------------
INK           = "#0F172A"   # Primary structural CAD ink
INK_BLACK     = "#000000"   # Heavy section cut ink
INK_MID       = "#334155"   # Secondary CAD linework (furniture, inner lines)
INK_LIGHT     = "#64748B"   # Gridlines, hatching, dimension extensions
WALL_POCHE    = "#CBD5E1"   # Masonry wall section poché fill
ROOM_WHITE    = "#FFFFFF"   # Pure white room interior
PAPER         = "#FFFFFF"   # Pure white CAD sheet background
GRID_BUBBLE   = "#F8FAFC"   # Structural grid bubble fill

# Wall thicknesses (EXT_WALL 9", INT_WALL 4.5") are imported from plan_geometry_engine


def _ft_in_str(val_ft: float) -> str:
    """Formats decimal feet into standard architectural Feet'-Inches\" notation (e.g. 14'-6\")."""
    total_in = int(round(float(val_ft) * 12.0))
    ft = total_in // 12
    inch = total_in % 12
    return f"{ft}'-{inch}\""


# ---------------------------------------------------------------------------
# GEMINI API CALL — returns the raw topology JSON (slicing trees + door links).
# Exact geometry is computed afterwards by generation.plan_geometry_engine; nothing
# here moves, snaps or invents rooms.
# ---------------------------------------------------------------------------

def call_gemini_json(prompt_text: str, api_key: Optional[str] = None, temperature: float = 0.3) -> Dict[str, Any]:
    """Invokes Google Gemini with JSON response enforcement across the active models."""
    key = (api_key or GeminiConfig.get_api_key() or "").strip()
    if not key or len(key) < 12:
        raise ValueError("Valid Google Gemini API Key required. Set GEMINI_API_KEY in .env.")

    # JSON mode is only enabled on the v1beta endpoint; on v1 the stronger models reject the
    # request and the loop silently fell back to the weakest model.
    client = genai.Client(api_key=key, http_options=types.HttpOptions(api_version="v1beta"))

    def _config_for(model_name: str) -> types.GenerateContentConfig:
        # Long hidden "thinking" consumed the output budget and truncated the JSON; keep it short.
        thinking = None
        if model_name.startswith("gemini-3") and "lite" not in model_name:
            thinking = types.ThinkingConfig(thinking_level="LOW")
        elif model_name.startswith("gemini-2.5-flash") and "lite" not in model_name:
            thinking = types.ThinkingConfig(thinking_budget=2048)
        return types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=temperature,
            max_output_tokens=32768,
            thinking_config=thinking,
        )

    last_error: Optional[Exception] = None
    for model_name in ACTIVE_MODELS:
        try:
            resp = client.models.generate_content(model=model_name, contents=prompt_text, config=_config_for(model_name))
            raw = (resp.text or "").strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            data = json.loads(raw)
            if isinstance(data, list):
                data = {"floors": data}
            if isinstance(data, dict) and data.get("floors"):
                data["_model_used"] = model_name
                return data
            last_error = ValueError(f"{model_name} returned JSON without 'floors'")
        except Exception as e:  # try the next model, but say so (silent fallbacks hid a config bug)
            print(f"[Gemini CAD] {model_name} failed: {str(e)[:200]}")
            last_error = e
            continue

    raise RuntimeError(f"Gemini LLM CAD generation failed on all models. Last error: {last_error}")


REQUIREMENT_MODELS = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-3-flash-preview"]


def extract_requirements_llm(brief: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Gemini's own reading of the brief (English / Urdu / Roman Urdu) as a small JSON checklist.
    Merged on top of the rule-based parser; any failure returns {} and the rules alone are used."""
    key = (api_key or GeminiConfig.get_api_key() or "").strip()
    if not key or len(key) < 12 or not (brief or "").strip():
        return {}
    client = genai.Client(api_key=key, http_options=types.HttpOptions(api_version="v1beta"))
    prompt = LLM_EXTRACTION_PROMPT.format(brief=brief.strip()[:4000])
    for model_name in REQUIREMENT_MODELS:
        try:
            thinking = None
            if model_name.startswith("gemini-3") and "lite" not in model_name:
                thinking = types.ThinkingConfig(thinking_level="LOW")
            elif model_name.startswith("gemini-2.5-flash") and "lite" not in model_name:
                thinking = types.ThinkingConfig(thinking_budget=0)
            cfg = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0,
                                              max_output_tokens=8192, thinking_config=thinking)
            resp = client.models.generate_content(model=model_name, contents=prompt, config=cfg)
            raw = (resp.text or "").strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            data = json.loads(raw)
            if isinstance(data, dict):
                data["_model"] = model_name
                return data
        except Exception as e:
            print(f"[Gemini brief reading] {model_name} failed: {str(e)[:160]}")
    return {}


def call_gemini_cad_llm(prompt_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Backward-compatible alias (returns raw topology JSON; run analyse_layout() for geometry)."""
    return call_gemini_json(prompt_text, api_key=api_key)


def _classify_room(room: Dict[str, Any]) -> str:
    """Room category (shared vocabulary with plan_geometry_engine)."""
    return room.get("category") or classify_room(room)


# ---------------------------------------------------------------------------
# DRAWING PRIMITIVES — reference-style monochrome CAD (solid black walls)
# ---------------------------------------------------------------------------

def _add_shapely(ax, geom, **kw):
    """Draws a Shapely (Multi)Polygon, holes included, as a Matplotlib PathPatch."""
    if geom is None or geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        polys = [geom]
    else:
        polys = [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]
    for poly in polys:
        verts, codes = [], []
        for ring in [poly.exterior] + list(poly.interiors):
            coords = list(ring.coords)
            if len(coords) < 3:
                continue
            verts.extend(coords)
            codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(coords) - 2) + [MplPath.CLOSEPOLY])
        if verts:
            ax.add_patch(PathPatch(MplPath(verts, codes), **kw))


def draw_room_base(ax, room: Dict[str, Any], building, lw: float):
    """Room floor fill and open-space conventions (lawn, porch, balcony, OTS, open)."""
    x1, y1 = float(room["x_ft"]), float(room["y_ft"])
    w, l = float(room["w_ft"]), float(room["l_ft"])
    cat = _classify_room(room)
    name = str(room.get("name", "")).upper()
    ax.add_patch(Rectangle((x1, y1), w, l, facecolor=ROOM_WHITE, edgecolor="none", zorder=2))

    if cat == "outdoor":
        if any(k in name for k in ("LAWN", "GARDEN")):
            ax.add_patch(Rectangle((x1, y1), w, l, facecolor=ROOM_WHITE, edgecolor=INK_LIGHT,
                                   hatch="..", linewidth=0.0, zorder=2.5))
        elif any(k in name for k in ("BALCONY", "TERRACE", "VERANDAH")):
            inset = 0.35
            ax.add_patch(Rectangle((x1 + inset, y1 + inset), max(0.1, w - 2 * inset), max(0.1, l - 2 * inset),
                                   facecolor="none", edgecolor=INK_MID, linewidth=lw * 0.7, zorder=3))
        elif "DRIVE" in name:
            for gy in np.arange(y1 + 2.0, y1 + l, 2.0):
                ax.plot([x1, x1 + w], [gy, gy], color="#E2E8F0", linewidth=lw * 0.4, zorder=3)
        ax.add_patch(Rectangle((x1, y1), w, l, facecolor="none", edgecolor=INK_LIGHT,
                               linewidth=lw * 0.6, linestyle=(0, (4, 3)), zorder=3))
    elif cat == "porch":
        # Porch roof outline (dash-dot) + free-standing RCC columns at the open corners
        ax.add_patch(Rectangle((x1, y1), w, l, facecolor="none", edgecolor=INK_MID,
                               linewidth=lw * 0.7, linestyle=(0, (8, 3, 2, 3)), zorder=3))
        col = EXT_WALL
        for cx, cy in ((x1, y1), (x1 + w - col, y1), (x1, y1 + l - col), (x1 + w - col, y1 + l - col)):
            centre = Point(cx + col / 2.0, cy + col / 2.0)
            if not building.is_empty and building.buffer(0.05).contains(centre):
                continue
            if cy > y1 + 0.1 and not building.is_empty and centre.distance(building) < 1.0:
                continue
            ax.add_patch(Rectangle((cx, cy), col, col, facecolor=INK_BLACK, edgecolor=INK_BLACK, zorder=7))
    elif cat == "pool":
        # Swimming pool: 1 ft coping, water surface lines, entry steps at one end
        c = min(1.0, w * 0.1, l * 0.1)
        ax.add_patch(Rectangle((x1, y1), w, l, facecolor="#F1F5F9", edgecolor=INK_BLACK, linewidth=lw * 1.1, zorder=3))
        ax.add_patch(Rectangle((x1 + c, y1 + c), w - 2 * c, l - 2 * c, facecolor="#E0F2FE", edgecolor=INK_BLACK,
                               linewidth=lw * 0.8, zorder=3.1))
        for k in range(1, 4):
            yy = y1 + c + (l - 2 * c) * k / 4.0
            xs = np.linspace(x1 + c + 0.6, x1 + w - c - 0.6, 40)
            ax.plot(xs, yy + 0.18 * np.sin((xs - x1) * 2.2), color=INK_LIGHT, linewidth=lw * 0.5, zorder=3.2)
        for k in range(3):
            sx = x1 + c + k * 0.9
            ax.plot([sx, sx], [y1 + c, y1 + l - c], color=INK_MID, linewidth=lw * 0.6, zorder=3.3)
    elif cat == "ots":
        ax.add_patch(Rectangle((x1, y1), w, l, facecolor="none", edgecolor=INK_MID, linewidth=lw * 0.6, zorder=3))
        ax.plot([x1, x1 + w], [y1, y1 + l], color=INK_LIGHT, linewidth=lw * 0.6, linestyle="--", zorder=3)
        ax.plot([x1, x1 + w], [y1 + l, y1], color=INK_LIGHT, linewidth=lw * 0.6, linestyle="--", zorder=3)


def draw_gate(ax, room: Dict[str, Any], lw: float, fs: float):
    """Sliding gate (S/G GATE) on the front boundary in front of the car porch / drive way."""
    x1, y1 = float(room["x_ft"]), float(room["y_ft"])
    w = float(room["w_ft"])
    if y1 > 0.05:
        return
    ax.plot([x1 + 0.6, x1 + w - 0.6], [0.0, 0.0], color=ROOM_WHITE, linewidth=lw * 3.0, zorder=4)
    ax.plot([x1 + 0.6, x1 + w - 0.6], [0.0, 0.0], color=INK_BLACK, linewidth=lw * 1.1,
            linestyle=(0, (5, 2)), zorder=5)
    ax.text(x1 + w / 2.0, 0.55, "S/G GATE", ha="center", va="bottom", fontsize=fs * 0.75,
            fontweight="bold", color=INK_BLACK, zorder=12)


def draw_door(ax, d: Dict[str, Any], lw: float):
    """Door leaf at 90° + thin swing arc; arches drawn as an open passage with dashed head lines."""
    o, s, e = d["orient"], float(d["s"]), float(d["e"])
    lo, hi = float(d["band"][0]), float(d["band"][1])
    into = int(d["into"])
    face = hi if into > 0 else lo

    def P(along, across):
        return _pt(o, along, across)

    for a in (s, e):
        p1, p2 = P(a, lo), P(a, hi)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=INK_BLACK, linewidth=lw * 0.9, zorder=9)
    if d.get("kind") == "arch":
        for c in (lo, hi):
            p1, p2 = P(s, c), P(e, c)
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=INK_MID, linewidth=lw * 0.7,
                    linestyle=(0, (3, 2)), zorder=9)
        return
    w = e - s
    if d.get("kind") == "main_double":
        leaves = [(s, 1.0, w / 2.0), (e, -1.0, w / 2.0)]
    else:
        h = s if d.get("hinge", "s") == "s" else e
        leaves = [(h, 1.0 if h == s else -1.0, w)]
    for h, dirn, r in leaves:
        p_h, p_tip = P(h, face), P(h, face + into * r)
        ax.plot([p_h[0], p_tip[0]], [p_h[1], p_tip[1]], color=INK_BLACK, linewidth=lw * 1.5, zorder=10)
        ts = np.linspace(0.0, math.pi / 2.0, 28)
        pts = [P(h + dirn * r * math.cos(t), face + into * r * math.sin(t)) for t in ts]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=INK_MID, linewidth=lw * 0.75, zorder=10)


def draw_window(ax, w: Dict[str, Any], lw: float):
    """Window cut through the wall: two frame lines + two glazing lines; ventilator = single glazing line."""
    o, s, e = w["orient"], float(w["s"]), float(w["e"])
    lo, hi = float(w["band"][0]), float(w["band"][1])

    def seg(c, width, color=INK_BLACK):
        p1, p2 = _pt(o, s, c), _pt(o, e, c)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=width, zorder=9)

    seg(lo, lw * 0.8)
    seg(hi, lw * 0.8)
    if w.get("kind") == "ventilator":
        seg((lo + hi) / 2.0, lw * 0.7, INK_MID)
    else:
        seg(lo + (hi - lo) * 0.38, lw * 0.6, INK_MID)
        seg(lo + (hi - lo) * 0.62, lw * 0.6, INK_MID)
    for a in (s, e):
        p1, p2 = _pt(o, a, lo), _pt(o, a, hi)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=INK_BLACK, linewidth=lw * 0.8, zorder=9)


def draw_stair(ax, room: Dict[str, Any], clear: Tuple[float, float, float, float], floor_idx: int,
               n_floors: int, doors: List[Dict[str, Any]], lw: float, fs: float):
    """Dog-leg (≥ 6 ft wide) or straight flight drawn along the long side, starting at the door end."""
    x1, y1, x2, y2 = clear
    w, l = x2 - x1, y2 - y1
    if w < 2.0 or l < 2.0:
        return
    long_is_y = l >= w
    L, S = (l, w) if long_is_y else (w, l)

    # Start the flight at the end nearest the stair door
    flip = False
    my_doors = [d for d in doors if d["room_id"] == room.get("id") or d["from_id"] == room.get("id")]
    if my_doors:
        d = my_doors[0]
        cx = (d["s"] + d["e"]) / 2.0 if d["orient"] == ("v" if long_is_y else "h") else d["coord"]
        lo_axis = y1 if long_is_y else x1
        flip = (cx - lo_axis) > L / 2.0

    def P(a, c):
        a = (L - a) if flip else a
        return (x1 + c, y1 + a) if long_is_y else (x1 + a, y1 + c)

    def line(a1, c1, a2, c2, width=lw * 0.8, ls="-", color=INK_BLACK):
        p1, p2 = P(a1, c1), P(a2, c2)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=width, linestyle=ls, zorder=6)

    tread = 0.83
    up_lbl = "UP" if floor_idx < n_floors else "DN"
    if S >= 6.0:
        well = 0.33
        fw = (S - well) / 2.0
        landing = min(fw, max(3.0, L * 0.3))
        run = L - landing
        n = max(4, int(run / tread))
        step = run / n
        line(run, 0, run, S, lw * 1.0)
        line(0, fw, run, fw, lw * 0.9)
        line(0, fw + well, run, fw + well, lw * 0.9)
        for k in range(1, n):
            a = k * step
            ls1 = "--" if (floor_idx == 0 and a > run * 0.55) else "-"
            line(a, 0, a, fw, lw * 0.7, ls1)
            line(a, fw + well, a, S, lw * 0.7)
        if floor_idx == 0:
            line(run * 0.5, 0, run * 0.6, fw, lw * 1.1)   # breakline on the ground floor
        a1, a2 = P(0.4, fw / 2.0), P(run - 0.3, fw / 2.0)
        ax.annotate("", xy=a2, xytext=a1, arrowprops=dict(arrowstyle="->", color=INK_BLACK, lw=lw), zorder=8)
        b1, b2 = P(run - 0.3, fw + well + fw / 2.0), P(0.6, fw + well + fw / 2.0)
        ax.annotate("", xy=b2, xytext=b1, arrowprops=dict(arrowstyle="->", color=INK_BLACK, lw=lw), zorder=8)
        tp = P(0.15, fw / 2.0)
        ax.text(tp[0], tp[1], "UP" if floor_idx == 0 or n_floors > floor_idx + 1 else up_lbl, ha="center",
                va="center", fontsize=fs * 0.7, fontweight="bold", color=INK_BLACK, zorder=9,
                bbox=dict(boxstyle="square,pad=0.05", facecolor=ROOM_WHITE, edgecolor="none"))
        if floor_idx > 0:
            dp = P(0.15, fw + well + fw / 2.0)
            ax.text(dp[0], dp[1], "DN", ha="center", va="center", fontsize=fs * 0.7, fontweight="bold",
                    color=INK_BLACK, zorder=9, bbox=dict(boxstyle="square,pad=0.05", facecolor=ROOM_WHITE, edgecolor="none"))
    else:
        n = max(4, int(L / tread))
        step = L / n
        for k in range(1, n):
            a = k * step
            ls1 = "--" if (floor_idx == 0 and a > L * 0.55) else "-"
            line(a, 0, a, S, lw * 0.7, ls1)
        if floor_idx == 0:
            line(L * 0.5, 0, L * 0.6, S, lw * 1.1)
        a1, a2 = P(0.4, S / 2.0), P(L - 0.3, S / 2.0)
        ax.annotate("", xy=a2, xytext=a1, arrowprops=dict(arrowstyle="->", color=INK_BLACK, lw=lw), zorder=8)
        tp = P(0.15, S / 2.0)
        ax.text(tp[0], tp[1], "UP" if floor_idx == 0 else "DN", ha="center", va="center", fontsize=fs * 0.7,
                fontweight="bold", color=INK_BLACK, zorder=9,
                bbox=dict(boxstyle="square,pad=0.05", facecolor=ROOM_WHITE, edgecolor="none"))


# ---------------------------------------------------------------------------
# FURNITURE & FIXTURE SYMBOLS (drawn in each item's local frame; positions come
# from plan_geometry_engine.furnish_room, which already avoided door swings)
# ---------------------------------------------------------------------------

class _Local:
    """Maps item-local coords (lx across, ly from the back/wall towards the front) to plan coords."""

    def __init__(self, it: Dict[str, Any]):
        self.x, self.y = float(it["x"]), float(it["y"])
        self.W, self.D = float(it["W"]), float(it["D"])
        self.f = it.get("facing", "N")

    def pt(self, lx: float, ly: float) -> Tuple[float, float]:
        if self.f == "N":
            return (self.x + lx, self.y + ly)
        if self.f == "S":
            return (self.x + self.W - lx, self.y + self.D - ly)
        if self.f == "E":
            return (self.x + ly, self.y + self.W - lx)
        return (self.x + self.D - ly, self.y + lx)


def draw_furniture_item(ax, it: Dict[str, Any], lw: float, fs: float):
    t = it["type"]
    F = _Local(it)
    W, D = F.W, F.D

    def poly(lx, ly, w, d, fc=ROOM_WHITE, ec=INK_MID, m=0.8, ls="-", z=6):
        pts = [F.pt(lx, ly), F.pt(lx + w, ly), F.pt(lx + w, ly + d), F.pt(lx, ly + d)]
        ax.add_patch(MplPolygon(pts, closed=True, facecolor=fc, edgecolor=ec, linewidth=lw * m, linestyle=ls, zorder=z))

    def line(a, b, m=0.6, color=INK_MID, ls="-", z=7):
        p1, p2 = F.pt(*a), F.pt(*b)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=lw * m, linestyle=ls, zorder=z)

    def ell(cx, cy, rx, ry, fc=ROOM_WHITE, ec=INK_MID, m=0.7, z=7):
        pts = [F.pt(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 28)]
        ax.add_patch(MplPolygon(pts, closed=True, facecolor=fc, edgecolor=ec, linewidth=lw * m, zorder=z))

    if t.startswith("bed_"):
        poly(0, 0, W, D, ec=INK_BLACK, m=0.9)
        poly(0, 0, W, 0.35, fc="#E5E7EB", ec=INK_BLACK, m=0.8)
        if t == "bed_single":
            poly(W * 0.18, 0.55, W * 0.64, 0.75, m=0.6)
        else:
            pw = (W - 0.9) / 2.0
            poly(0.3, 0.55, pw, 0.75, m=0.6)
            poly(W - 0.3 - pw, 0.55, pw, 0.75, m=0.6)
        line((0, D * 0.42), (W, D * 0.42))
        line((0, D * 0.42), (W * 0.22, D * 0.56))
    elif t == "nightstand":
        poly(0, 0, W, D)
        ell(W / 2, D / 2, 0.28, 0.28, fc="#F3F4F6", m=0.5)
    elif t in ("wardrobe", "bookshelf"):
        poly(0, 0, W, D, fc="#F9FAFB", ec=INK_BLACK, m=0.8)
        line((0, D * 0.5), (W, D * 0.5), m=0.5)
        for k in range(1, max(3, int(W / 0.6))):
            lx = k * W / max(3, int(W / 0.6))
            line((lx - 0.15, D * 0.25), (lx + 0.15, D * 0.75), m=0.4, color=INK_LIGHT)
        c = F.pt(W / 2, D * 0.5)
        ax.text(c[0], c[1], "W/R" if t == "wardrobe" else "SHELF", ha="center", va="center", fontsize=fs * 0.55, color=INK_MID, zorder=8,
                bbox=dict(boxstyle="square,pad=0.03", facecolor="#F9FAFB", edgecolor="none"))
    elif t in ("dressing_table", "study_desk"):
        poly(0, 0, W, D, ec=INK_BLACK, m=0.8)
        line((0.2, 0.25), (W - 0.2, 0.25), m=0.5)
    elif t in ("sofa_3", "sofa_2", "armchair"):
        poly(0, 0, W, D, ec=INK_BLACK, m=0.9)
        poly(0, 0, W, 0.65, fc="#E5E7EB", m=0.7)
        poly(0, 0, 0.55, D, fc="#E5E7EB", m=0.7)
        poly(W - 0.55, 0, 0.55, D, fc="#E5E7EB", m=0.7)
        seats = 3 if t == "sofa_3" else (2 if t == "sofa_2" else 1)
        for k in range(1, seats):
            lx = 0.55 + k * (W - 1.1) / seats
            line((lx, 0.65), (lx, D - 0.1), m=0.5)
    elif t == "coffee_table":
        poly(0, 0, W, D, ec=INK_BLACK, m=0.8)
        poly(0.2, 0.2, W - 0.4, D - 0.4, m=0.5)
    elif t == "tv_console":
        poly(0, 0, W, D, fc="#F9FAFB", ec=INK_BLACK, m=0.8)
        poly(W * 0.12, 0.2, W * 0.76, 0.18, fc=INK_BLACK, ec=INK_BLACK, m=0.5)
    elif t in ("dining_6", "dining_4"):
        tl = 3.5 if t == "dining_6" else 3.0
        ty = (D - tl) / 2.0
        poly(0, ty, W, tl, ec=INK_BLACK, m=0.9)
        n = 3 if t == "dining_6" else 2
        for k in range(n):
            cx = (k + 0.5) * W / n
            poly(cx - 0.65, 0.1, 1.3, 1.1, m=0.6)
            poly(cx - 0.65, D - 1.2, 1.3, 1.1, m=0.6)
    elif t == "counter":
        poly(0, 0, W, D, fc="#F3F4F6", ec=INK_BLACK, m=0.8)
        line((0, D - 0.15), (W, D - 0.15), m=0.4, color=INK_LIGHT)
    elif t == "sink":
        poly(0, 0, W, D, ec=INK_BLACK, m=0.7, z=8)
        poly(0.15, 0.15, W / 2 - 0.25, D - 0.3, m=0.5, z=8)
        poly(W / 2 + 0.1, 0.15, W / 2 - 0.25, D - 0.3, m=0.5, z=8)
    elif t == "hob":
        poly(0, 0, W, D, ec=INK_BLACK, m=0.7, z=8)
        for bx in (0.28, 0.72):
            for by in (0.3, 0.7):
                ell(W * bx, D * by, min(W, D) * 0.15, min(W, D) * 0.15, m=0.5, z=9)
    elif t == "fridge":
        poly(0, 0, W, D, fc="#F3F4F6", ec=INK_BLACK, m=0.8)
        line((0, D), (W, 0), m=0.4, color=INK_LIGHT)
        c = F.pt(W / 2, D / 2)
        ax.text(c[0], c[1], "REF", ha="center", va="center", fontsize=fs * 0.5, color=INK_MID, zorder=8)
    elif t == "wc":
        poly(W * 0.08, 0, W * 0.84, 0.6, fc="#F3F4F6", ec=INK_BLACK, m=0.7)
        ell(W / 2, 0.6 + (D - 0.6) / 2, W * 0.4, (D - 0.6) / 2 - 0.05, ec=INK_BLACK)
    elif t == "basin":
        poly(0, 0, W, D, fc="#F9FAFB", ec=INK_BLACK, m=0.7)
        ell(W / 2, D / 2, W * 0.32, D * 0.3, ec=INK_BLACK, m=0.6)
    elif t == "shower":
        poly(0, 0, W, D, fc="none", ec=INK_BLACK, m=0.7, ls="--")
        line((0, 0), (W, D), m=0.4, color=INK_LIGHT)
        line((0, D), (W, 0), m=0.4, color=INK_LIGHT)
        ell(W / 2, D / 2, 0.2, 0.2, ec=INK_BLACK, m=0.5)
    elif t in ("car", "car_compact"):
        ax.add_patch(FancyBboxPatch((it["x"] + 0.1, it["y"] + 0.1), it["w"] - 0.2, it["h"] - 0.2,
                                    boxstyle="round,pad=0.05,rounding_size=0.9", facecolor="#F9FAFB",
                                    edgecolor=INK_BLACK, linewidth=lw * 0.9, zorder=6))
        poly(0.6, D * 0.3, W - 1.2, D * 0.42, m=0.6)
        line((0.35, D * 0.22), (0.6, D * 0.3))
        line((W - 0.35, D * 0.22), (W - 0.6, D * 0.3))
        line((0.4, D * 0.8), (0.6, D * 0.72))
        line((W - 0.4, D * 0.8), (W - 0.6, D * 0.72))
    elif t == "sofa_bed":
        poly(0, 0, W, D, ec=INK_BLACK, m=0.9)
        poly(0, 0, W, 0.7, fc="#E5E7EB", m=0.7)
        for k in range(1, 3):
            line((k * W / 3.0, 0.7), (k * W / 3.0, D - 0.1), m=0.5)
        c = F.pt(W / 2, D * 0.62)
        ax.text(c[0], c[1], "SOFA BED", ha="center", va="center", fontsize=fs * 0.45, color=INK_MID, zorder=8)
    elif t == "floor_cushion":
        poly(0, 0, W, D, fc="#F9FAFB", ec=INK_BLACK, m=0.8)
        poly(0, 0, W, 0.8, fc="#E5E7EB", m=0.6)                  # back bolster against the wall
        n = max(1, int(W / 2.5))
        for k in range(1, n):
            line((k * W / n, 0.8), (k * W / n, D), m=0.45)
    elif t == "low_table":
        poly(0, 0, W, D, ec=INK_BLACK, m=0.8)
        ell(W / 2, D / 2, W * 0.3, D * 0.3, m=0.5)
    elif t == "prayer_mat":
        # Janamaz: border, pointed mihrab arch at the Qibla end (front of the item)
        poly(0, 0, W, D, fc="#F9FAFB", ec=INK_BLACK, m=0.7)
        poly(0.15, 0.15, W - 0.3, D - 0.3, m=0.4)
        line((0.45, 0.6), (0.45, D - 1.25), m=0.5)
        line((W - 0.45, 0.6), (W - 0.45, D - 1.25), m=0.5)
        line((0.45, D - 1.25), (W / 2, D - 0.45), m=0.5)
        line((W - 0.45, D - 1.25), (W / 2, D - 0.45), m=0.5)
    elif t == "tree":
        cx, cy, r = it["x"] + it["w"] / 2, it["y"] + it["h"] / 2, it["w"] / 2
        ax.add_patch(Circle((cx, cy), r, facecolor=ROOM_WHITE, edgecolor=INK_MID, linewidth=lw * 0.6, zorder=6))
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            ax.plot([cx, cx + r * 0.75 * math.cos(a)], [cy, cy + r * 0.75 * math.sin(a)],
                    color=INK_LIGHT, linewidth=lw * 0.5, zorder=6)


# ---------------------------------------------------------------------------
# ROOM LABELS (placed on the clearest spot so they do not hide furniture)
# ---------------------------------------------------------------------------

def draw_room_label(ax, room: Dict[str, Any], floor_idx: int, scale: float, is_furnishing: bool,
                    furniture: Optional[List[Dict[str, Any]]] = None):
    rx, ry = float(room["x_ft"]), float(room["y_ft"])
    rw, rl = float(room["w_ft"]), float(room["l_ft"])
    cat = _classify_room(room)
    if rw < 3.0 or rl < 3.0:
        return
    raw_name = str(room.get("name") or room.get("type") or "ROOM").upper().strip()
    words = raw_name.split()
    if len(words) >= 3 and rw < 11.5:
        mid = len(words) // 2
        display_name = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
    else:
        display_name = raw_name

    fs_name = max(5.0, min(8.2, min(rw, rl) * scale * 0.5))
    is_open = cat == "outdoor" and raw_name.startswith("OPEN")
    if is_open:
        label_text = display_name
        fs_name *= 0.85
    else:
        label_text = f"{display_name}\n{_ft_in_str(rw)} X {_ft_in_str(rl)}"
        if not is_furnishing and is_enclosed(cat) and cat not in ("stair",) and rw >= 7.0 and rl >= 7.0:
            label_text += f"\n({int(round(rw * rl))} SQ.FT)"

    # Choose the candidate spot that overlaps the least furniture
    lines = label_text.split("\n")
    est_w = max(len(s) for s in lines) * 0.2 * fs_name / 7.0 * 1.9
    est_h = len(lines) * 0.42 * fs_name / 7.0 * 1.9
    cands = [(rx + rw * fx, ry + rl * fy) for fx, fy in
             ((0.5, 0.5), (0.5, 0.3), (0.5, 0.7), (0.3, 0.5), (0.7, 0.5), (0.3, 0.3), (0.7, 0.7), (0.3, 0.7), (0.7, 0.3))]
    items = [f for f in (furniture or []) if f.get("room_id") == room.get("id")]
    if cat == "stair":
        cands = [(rx + rw * 0.5, ry + rl * 0.5)]
        items = []

    def overlap(c):
        lb = box(c[0] - est_w / 2, c[1] - est_h / 2, c[0] + est_w / 2, c[1] + est_h / 2)
        return sum(lb.intersection(box(f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])).area for f in items)

    cx, cy = min(cands, key=lambda c: (round(overlap(c), 1), abs(c[0] - rx - rw / 2) + abs(c[1] - ry - rl / 2)))
    ax.text(
        cx, cy, label_text, ha="center", va="center", fontsize=fs_name, fontweight="bold",
        color=INK_BLACK if not is_open else INK_LIGHT, fontfamily="DejaVu Sans", multialignment="center",
        bbox=dict(boxstyle="round,pad=0.15", facecolor=ROOM_WHITE, edgecolor="none", alpha=0.9) if not is_open else None,
        zorder=12,
    )

# ---------------------------------------------------------------------------
# TWO-TIER EXTERIOR CAD DIMENSION CHAINS & STRUCTURAL GRID BUBBLES
# ---------------------------------------------------------------------------

def draw_cad_dimensions_and_grids(ax, layout: Dict[str, Any], floor_idx: int, scale: float):
    """
    Draws standard architectural construction drawing dimension chains and structural grids:
    - Tier 1 (Inner Chain): Room-by-room bay dimensions along South, North, West, East
    - Tier 2 (Outer Chain): Overall plot frontage and depth dimensions
    - Structural Grid Bubbles: Circular grid axes (A, B, C... on Top; 1, 2, 3... on Left)
    """
    plot_w = float(layout.get("plot_width_ft", 35.0))
    plot_l = float(layout.get("plot_length_ft", 65.0))
    rooms = layout["floors"][floor_idx].get("rooms", [])

    lw = max(0.65, 0.9 * scale)
    tick = 0.45
    fs_dim = max(5.5, 7.2 * scale)

    def draw_dim_segment(x1, y1, x2, y2, text, vertical=False, offset_text=0.85):
        # Dimension line
        ax.plot([x1, x2], [y1, y2], color=INK_BLACK, linewidth=lw, zorder=13)
        # 45-degree architectural slash ticks at both ends
        for px, py in [(x1, y1), (x2, y2)]:
            ax.plot(
                [px - tick, px + tick], [py - tick, py + tick],
                color=INK_BLACK, linewidth=lw * 1.35, zorder=14
            )
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        if vertical:
            ax.text(
                mx + offset_text, my, text,
                ha="center", va="center", rotation=90,
                fontsize=fs_dim, fontweight="bold", color=INK_BLACK,
                fontfamily="DejaVu Sans",
                bbox=dict(boxstyle="square,pad=0.08", facecolor=PAPER, edgecolor="none"),
                zorder=15
            )
        else:
            ax.text(
                mx, my + offset_text, text,
                ha="center", va="center",
                fontsize=fs_dim, fontweight="bold", color=INK_BLACK,
                fontfamily="DejaVu Sans",
                bbox=dict(boxstyle="square,pad=0.08", facecolor=PAPER, edgecolor="none"),
                zorder=15
            )

    # Collect unique X and Y structural bay coordinates from rooms
    xs = sorted(set(
        [0.0, round(plot_w, 2)] +
        [round(float(r["x_ft"]), 2) for r in rooms] +
        [round(float(r["x_ft"]) + float(r["w_ft"]), 2) for r in rooms]
    ))
    ys = sorted(set(
        [0.0, round(plot_l, 2)] +
        [round(float(r["y_ft"]), 2) for r in rooms] +
        [round(float(r["y_ft"]) + float(r["l_ft"]), 2) for r in rooms]
    ))

    # Filter out tiny slivers (< 2.5 ft) so dimension chains stay crisp
    clean_xs = [xs[0]]
    for x in xs[1:]:
        if x - clean_xs[-1] >= 2.5 or x == xs[-1]:
            clean_xs.append(x)
    clean_ys = [ys[0]]
    for y in ys[1:]:
        if y - clean_ys[-1] >= 2.5 or y == ys[-1]:
            clean_ys.append(y)

    # ── 1. SOUTH (BOTTOM) TWO-TIER DIMENSION CHAINS ──────────────────────────
    y_tier1 = -2.4
    y_tier2 = -4.8
    for x in clean_xs:
        ax.plot([x, x], [-0.4, y_tier1 - 0.4], color=INK_LIGHT, linewidth=lw * 0.7, zorder=12)
    for i in range(len(clean_xs) - 1):
        seg_w = clean_xs[i + 1] - clean_xs[i]
        if seg_w >= 2.0:
            draw_dim_segment(clean_xs[i], y_tier1, clean_xs[i + 1], y_tier1, _ft_in_str(seg_w), vertical=False, offset_text=-0.75)

    # Overall Width Dimension
    ax.plot([0, 0], [-0.4, y_tier2 - 0.4], color=INK_LIGHT, linewidth=lw * 0.8, zorder=12)
    ax.plot([plot_w, plot_w], [-0.4, y_tier2 - 0.4], color=INK_LIGHT, linewidth=lw * 0.8, zorder=12)
    draw_dim_segment(0, y_tier2, plot_w, y_tier2, f"OVERALL WIDTH: {_ft_in_str(plot_w)}", vertical=False, offset_text=-0.85)

    # ── 2. EAST (RIGHT) TWO-TIER DIMENSION CHAINS ────────────────────────────
    x_tier1 = plot_w + 2.4
    x_tier2 = plot_w + 5.0
    for y in clean_ys:
        ax.plot([plot_w + 0.4, x_tier1 + 0.4], [y, y], color=INK_LIGHT, linewidth=lw * 0.7, zorder=12)
    for i in range(len(clean_ys) - 1):
        seg_l = clean_ys[i + 1] - clean_ys[i]
        if seg_l >= 2.0:
            draw_dim_segment(x_tier1, clean_ys[i], x_tier1, clean_ys[i + 1], _ft_in_str(seg_l), vertical=True, offset_text=0.8)

    # Overall Depth Dimension
    ax.plot([plot_w + 0.4, x_tier2 + 0.4], [0, 0], color=INK_LIGHT, linewidth=lw * 0.8, zorder=12)
    ax.plot([plot_w + 0.4, x_tier2 + 0.4], [plot_l, plot_l], color=INK_LIGHT, linewidth=lw * 0.8, zorder=12)
    draw_dim_segment(x_tier2, 0, x_tier2, plot_l, f"OVERALL DEPTH: {_ft_in_str(plot_l)}", vertical=True, offset_text=0.9)

    # ── 3. STRUCTURAL GRID BUBBLES (TOP: A, B, C... | LEFT: 1, 2, 3...) ──────
    grid_y = plot_l + 2.6
    for idx_x, gx in enumerate(clean_xs[:8]):
        lbl = chr(ord("A") + idx_x)
        ax.plot([gx, gx], [plot_l + 0.3, grid_y - 0.85], color=INK_LIGHT, linewidth=lw * 0.65, linestyle="-.", zorder=12)
        ax.add_patch(Circle((gx, grid_y), 0.85, facecolor=GRID_BUBBLE, edgecolor=INK_BLACK, linewidth=lw * 1.1, zorder=14))
        ax.text(gx, grid_y, lbl, ha="center", va="center", fontsize=fs_dim, fontweight="bold", color=INK_BLACK, zorder=15)

    grid_x = -2.6
    for idx_y, gy in enumerate(clean_ys[:10]):
        lbl = str(idx_y + 1)
        ax.plot([grid_x + 0.85, -0.3], [gy, gy], color=INK_LIGHT, linewidth=lw * 0.65, linestyle="-.", zorder=12)
        ax.add_patch(Circle((grid_x, gy), 0.85, facecolor=GRID_BUBBLE, edgecolor=INK_BLACK, linewidth=lw * 1.1, zorder=14))
        ax.text(grid_x, gy, lbl, ha="center", va="center", fontsize=fs_dim, fontweight="bold", color=INK_BLACK, zorder=15)


def draw_north_and_scale_cad(ax, plot_w: float, plot_l: float, scale: float):
    """Draws compact CAD North symbol and graphic scale bar below the bottom dimension line."""
    # North arrow at top-right above gridline
    nx, ny = plot_w + 3.2, plot_l + 1.4
    ax.add_patch(Circle((nx, ny + 1.0), 1.0, facecolor=ROOM_WHITE, edgecolor=INK_BLACK, linewidth=1.1 * scale, zorder=14))
    ax.annotate(
        "", xy=(nx, ny + 2.2), xytext=(nx, ny + 0.1),
        arrowprops=dict(arrowstyle="-|>", color=INK_BLACK, lw=1.5 * scale, mutation_scale=11 * scale),
        zorder=15
    )
    ax.text(nx, ny + 2.4, "N", ha="center", va="bottom", fontsize=max(6.5, 8.5 * scale), fontweight="bold", color=INK_BLACK, zorder=15)

    # Graphic scale bar at bottom-left
    sy = -7.6
    segs = [0, 5, 10, 15]
    for i in range(len(segs) - 1):
        x0, x1 = segs[i], segs[i + 1]
        if x1 > plot_w:
            break
        fc = INK_BLACK if i % 2 == 0 else ROOM_WHITE
        ax.add_patch(Rectangle((x0, sy), x1 - x0, 0.55, facecolor=fc, edgecolor=INK_BLACK, linewidth=1.0 * scale, zorder=14))
        ax.text(x0, sy - 0.75, f"{x0}'", ha="center", va="top", fontsize=max(4.5, 5.8 * scale), color=INK_BLACK)
    ax.text(min(plot_w, 15), sy - 0.75, f"{min(int(plot_w), 15)}'", ha="center", va="top", fontsize=max(4.5, 5.8 * scale), color=INK_BLACK)


# ---------------------------------------------------------------------------
# MAIN FLOOR PLAN CAD SHEET RENDERER
# ---------------------------------------------------------------------------

def _draw_floor_on_axis(ax, layout: Dict[str, Any], floor_idx: int, is_furnishing: bool = False):
    """Draws one floor from the engine geometry (rooms, doors, windows, furniture)."""
    floor = layout["floors"][floor_idx]
    rooms = floor.get("rooms", [])
    for r in rooms:
        r.setdefault("category", classify_room(r))
    doors = floor.get("doors") or []
    windows = floor.get("windows") or []
    furniture = floor.get("furniture") or []
    plot_w = float(layout.get("plot_width_ft", 35.0))
    plot_l = float(layout.get("plot_length_ft", 65.0))
    n_floors = len(layout.get("floors", [])) or 1
    level_label = floor.get("label", f"LEVEL {floor_idx}").upper()

    scale = max(0.65, min(1.35, 38.0 / max(plot_w, plot_l)))
    lw_int = max(0.9, 1.35 * scale)
    lw_gen = max(0.75, 1.05 * scale)
    fs = max(5.5, 7.2 * scale)

    # 1. Property line
    ax.add_patch(Rectangle((0, 0), plot_w, plot_l, facecolor=PAPER, edgecolor=INK_BLACK,
                           linewidth=lw_int, zorder=1))

    geo = build_wall_geometry(rooms, doors, windows)
    building = geo["building"]

    # 2. Room bases & open-space conventions
    for room in rooms:
        if float(room.get("w_ft", 0)) < 1.0 or float(room.get("l_ft", 0)) < 1.0:
            continue
        draw_room_base(ax, room, building, lw_gen)

    # 3. Setback lines (dashed) so compliance is visible on the sheet
    for y_line, txt in ((layout.get("front_setback_ft"), "FRONT SETBACK LINE"),
                        (plot_l - float(layout.get("rear_setback_ft") or 0.0) if layout.get("rear_setback_ft") else None,
                         "REAR SETBACK LINE")):
        if y_line and 0.5 < float(y_line) < plot_l - 0.5:
            ax.plot([0, plot_w], [y_line, y_line], color=INK_LIGHT, linewidth=lw_gen * 0.5,
                    linestyle=(0, (10, 3, 2, 3)), zorder=3.2)
            ax.text(plot_w - 0.4, float(y_line) + 0.25, txt, ha="right", va="bottom", fontsize=fs * 0.55,
                    color=INK_LIGHT, zorder=3.3)

    # 3b. Roof level: 9" parapet along the edge of the roof slab of the floor below (mumty rooms
    #     keep their solid walls; terraces / garden / plunge pool are open to sky inside the parapet)
    if floor.get("roof") and floor_idx > 0:
        below = layout["floors"][floor_idx - 1].get("rooms", [])
        slab = unary_union([box(float(r["x_ft"]), float(r["y_ft"]), float(r["x_ft"]) + float(r["w_ft"]),
                                float(r["y_ft"]) + float(r["l_ft"]))
                            for r in below if r.get("category", classify_room(r)) not in ("outdoor", "ots", "pool")])
        if not slab.is_empty:
            parapet = slab.difference(slab.buffer(-0.75, join_style="mitre")).difference(building)
            _add_shapely(ax, parapet, facecolor="#CBD5E1", edgecolor=INK_BLACK, linewidth=lw_gen * 0.6,
                         hatch="////", zorder=5.5)
            bx1, by1, bx2, by2 = slab.bounds
            ax.text(bx2 - 0.4, by1 + 1.1, "9\" PARAPET", ha="right", va="bottom", fontsize=fs * 0.5,
                    color=INK_MID, zorder=9)

    # 4. Solid walls with true door / window cut-outs (single shared walls)
    _add_shapely(ax, geo["walls"], facecolor=INK_BLACK, edgecolor=INK_BLACK, linewidth=0.2, zorder=6)

    # 5. Stairs, gate, wet-area floor traps
    for room in rooms:
        cat = room["category"]
        if cat == "stair":
            draw_stair(ax, room, room_clear_rect(room, building), floor_idx, n_floors, doors, lw_gen, fs)
        elif cat == "porch" or (cat == "outdoor" and "DRIVE" in str(room.get("name", "")).upper()):
            if floor_idx == 0:
                draw_gate(ax, room, lw_gen, fs)
        elif cat == "bath" and not is_furnishing:
            cr = room_clear_rect(room, building)
            fx, fy = (cr[0] + cr[2]) / 2.0, cr[1] + (cr[3] - cr[1]) * 0.25
            ax.add_patch(Circle((fx, fy), 0.22, facecolor=ROOM_WHITE, edgecolor=INK_MID, linewidth=lw_gen * 0.7, zorder=7))
            ax.text(fx + 0.35, fy, "FT", ha="left", va="center", fontsize=fs * 0.5, color=INK_MID, zorder=7)

    # 6. Furniture (already collision-checked against door swings by the engine)
    if is_furnishing:
        for it in furniture:
            try:
                draw_furniture_item(ax, it, lw_gen, fs)
            except Exception as e_f:
                print(f"[CAD Furniture Warning] {it.get('type')}: {e_f}")

    # 7. Doors & windows
    gate_ids = {r["id"] for r in rooms if r.get("gate")}
    for d in doors:
        draw_door(ax, d, lw_gen)
        if d.get("room_id") in gate_ids or d.get("from_id") in gate_ids:
            gx, gy = _pt(d["orient"], (d["s"] + d["e"]) / 2.0, d["coord"])
            ax.text(gx, gy, "GATE", ha="center", va="center", fontsize=fs * 0.6, fontweight="bold",
                    color=INK_BLACK, zorder=12, bbox=dict(boxstyle="square,pad=0.1", facecolor=ROOM_WHITE,
                                                          edgecolor=INK_BLACK, linewidth=0.5))
    for w in windows:
        draw_window(ax, w, lw_gen)

    # 8. Labels (a space written in several parts is one space: one label, on its largest part, under its own name)
    by_room_id = {r.get("id"): r for r in rooms}
    part_groups: Dict[Any, List[Dict[str, Any]]] = {}
    for r in rooms:
        if r.get("part_of") in by_room_id:
            part_groups.setdefault(r["part_of"], [by_room_id[r["part_of"]]]).append(r)
    label_part = {root: max(ms, key=lambda m: float(m["w_ft"]) * float(m["l_ft"])) for root, ms in part_groups.items()}
    for room in rooms:
        root_id = room.get("part_of") if room.get("part_of") in part_groups else (room.get("id") if room.get("id") in part_groups else None)
        if root_id is not None:
            if label_part[root_id] is not room:
                continue
            room = dict(room, name=by_room_id[root_id].get("name"))
        try:
            draw_room_label(ax, room, floor_idx, scale, is_furnishing, furniture if is_furnishing else None)
        except Exception as e_lbl:
            print(f"[CAD Label Warning] {room.get('name')}: {e_lbl}")

    # 9. Dimensions, grids, north, title
    draw_cad_dimensions_and_grids(ax, layout, floor_idx, scale)
    draw_north_and_scale_cad(ax, plot_w, plot_l, scale)
    mode_tag = "FURNISHED ARCHITECTURAL LAYOUT" if is_furnishing else "2D WORKING PLAN"
    ax.text(
        plot_w / 2.0, -9.8,
        f"{level_label}  —  {mode_tag}   |   PLOT: {_ft_in_str(plot_w)} × {_ft_in_str(plot_l)}   |   SCALE: 1/8\" = 1'-0\"",
        ha="center", va="top", fontsize=max(7.5, 10.0 * scale), fontweight="bold",
        color=INK_BLACK, fontfamily="DejaVu Sans", zorder=15,
    )
    ax.set_xlim(-5.2, plot_w + 7.8)
    ax.set_ylim(-11.5, plot_l + 4.8)
    ax.set_aspect("equal")
    ax.axis("off")

def render_floor_plan_cad_sheet(
    layout: Dict[str, Any],
    floor_idx: int,
    project_id: str,
    style: str,
    out_dir: str,
    is_furnishing: bool = False
) -> str:
    """Renders a clean, full-bleed standard CAD sheet for a single floor (structural or furnished)."""
    plot_w = float(layout.get("plot_width_ft", 35.0))
    plot_l = float(layout.get("plot_length_ft", 65.0))
    floor = layout["floors"][floor_idx]
    level_label = floor.get("label", f"LEVEL {floor_idx}")

    fig_w = max(10.5, min(16.0, (plot_w + 13.0) * 0.26))
    fig_h = max(12.5, min(19.0, (plot_l + 16.5) * 0.26))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=RENDER_DPI)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    _draw_floor_on_axis(ax, layout, floor_idx, is_furnishing=is_furnishing)

    plt.tight_layout(pad=0.35)
    slug = re.sub(r"[^a-z0-9]+", "_", level_label.lower()).strip("_")
    type_tag = "furnishing" if is_furnishing else "plan"
    fname = f"{project_id}_{slug}_{type_tag}_2d.png"
    fpath = os.path.join(out_dir, fname)
    plt.savefig(fpath, dpi=RENDER_DPI, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    return fpath


def render_rooftop_slab_cad_sheet(layout: Dict[str, Any], project_id: str, out_dir: str) -> str:
    """
    Renders a dedicated Standard CAD Rooftop Slab & Mumty Plan showing:
    - Perimeter parapet wall (9\" double-line with hatch)
    - Aligned Stair Mumty Tower with arrival flight (DN) & weatherproof door
    - Overhead RCC Water Tank (OHT)
    - OTS Skylight Curb voids aligned with lower OTS shafts
    - Rainwater drainage slope arrows & RWP downspouts
    """
    plot_w = float(layout.get("plot_width_ft", 35.0))
    plot_l = float(layout.get("plot_length_ft", 65.0))

    # Locate staircase and OTS positions from lower floors so rooftop aligns 1:1
    stair_room = None
    ots_rooms = []
    for fl in layout.get("floors", []):
        for r in fl.get("rooms", []):
            cat = _classify_room(r)
            if cat == "stair" and stair_room is None:
                stair_room = dict(r)
            elif cat == "ots":
                ots_rooms.append(dict(r))

    if not stair_room:
        stair_room = {
            "id": "rf_mumty",
            "name": "MUMTY STAIR TOWER",
            "type": "stair",
            "x_ft": round(plot_w * 0.35, 1),
            "y_ft": round(plot_l * 0.42, 1),
            "w_ft": min(11.0, round(plot_w * 0.38, 1)),
            "l_ft": min(13.0, round(plot_l * 0.25, 1)),
            "door": {"wall": "south", "offset_ft": 1.5, "width_ft": 3.0, "swing": "out"}
        }
    else:
        stair_room["name"] = "MUMTY STAIR TOWER"

    roof_rooms = [
        stair_room,
        {
            "id": "rf_oht",
            "name": "RCC OVERHEAD WATER TANK",
            "type": "dressing",
            "x_ft": max(1.0, min(plot_w - 9.0, float(stair_room["x_ft"]))),
            "y_ft": min(plot_l - 8.5, float(stair_room["y_ft"]) + float(stair_room["l_ft"]) + 1.0),
            "w_ft": min(8.0, float(stair_room["w_ft"])),
            "l_ft": 6.5,
            "door": None,
            "windows": []
        }
    ]
    for idx_o, ots in enumerate(ots_rooms[:2]):
        ots_copy = dict(ots)
        ots_copy["id"] = f"rf_ots_{idx_o}"
        ots_copy["name"] = "OTS VOID CURB"
        ots_copy["door"] = None
        ots_copy["windows"] = []
        roof_rooms.append(ots_copy)

    roof_layout = {
        "plot_width_ft": plot_w,
        "plot_length_ft": plot_l,
        "floors": [{"level": len(layout.get("floors", [])), "label": "ROOFTOP SLAB", "rooms": roof_rooms}]
    }

    fig_w = max(10.5, min(16.0, (plot_w + 13.0) * 0.26))
    fig_h = max(12.5, min(19.0, (plot_l + 16.5) * 0.26))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=RENDER_DPI)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    _draw_floor_on_axis(ax, roof_layout, 0, is_furnishing=False)

    # Perimeter Parapet Wall (double-line around entire roof slab)
    ax.add_patch(Rectangle(
        (0, 0), plot_w, plot_l,
        facecolor="none", edgecolor=INK_BLACK, linewidth=2.5, zorder=6
    ))
    ax.add_patch(Rectangle(
        (EXT_WALL, EXT_WALL), plot_w - 2 * EXT_WALL, plot_l - 2 * EXT_WALL,
        facecolor="none", edgecolor=INK_BLACK, linewidth=1.2, zorder=6
    ))

    # Open Roof Terrace Label + Rainwater Slope Arrows & RWP Downspouts in clear front terrace bay
    terrace_cy = min(plot_l * 0.20, max(4.0, float(stair_room["y_ft"]) * 0.45))
    ax.text(
        plot_w / 2.0, terrace_cy,
        f"OPEN ROOF TERRACE SLAB\n{_ft_in_str(plot_w)} × {_ft_in_str(plot_l)}\n(SLOPE 1:100 TO RWP)",
        ha="center", va="center", fontsize=7.5, fontweight="bold",
        color=INK_BLACK, fontfamily="DejaVu Sans",
        bbox=dict(boxstyle="square,pad=0.2", facecolor=ROOM_WHITE, edgecolor=INK_LIGHT, lw=0.6),
        zorder=10
    )
    # 4" RWP Corner Rainwater Downspouts + Drainage Slope Arrows
    for rwp_x in [1.4, plot_w - 1.4]:
        ax.add_patch(Circle((rwp_x, 1.4), 0.4, facecolor=ROOM_WHITE, edgecolor=INK_BLACK, linewidth=1.0, zorder=8))
        ax.text(rwp_x, 2.2, "RWP", ha="center", va="bottom", fontsize=5.2, fontweight="bold", color=INK_MID, zorder=9)
    ax.annotate("", xy=(2.0, 2.0), xytext=(plot_w * 0.28, terrace_cy - 1.5), arrowprops=dict(arrowstyle="->", color=INK_MID, lw=0.9, ls="--"), zorder=7)
    ax.annotate("", xy=(plot_w - 2.0, 2.0), xytext=(plot_w * 0.72, terrace_cy - 1.5), arrowprops=dict(arrowstyle="->", color=INK_MID, lw=0.9, ls="--"), zorder=7)

    plt.tight_layout(pad=0.35)
    fname = f"{project_id}_rooftop_slab_plan_2d.png"
    fpath = os.path.join(out_dir, fname)
    plt.savefig(fpath, dpi=RENDER_DPI, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    return fpath


def render_composite_multi_floor_cad_sheet(
    layout: Dict[str, Any],
    project_id: str,
    out_dir: str,
    is_furnishing: bool = True
) -> str:
    """Renders all floors side-by-side on a single coordinated CAD sheet."""
    floors = layout.get("floors", [])
    n_floors = len(floors)
    plot_w = float(layout.get("plot_width_ft", 35.0))
    plot_l = float(layout.get("plot_length_ft", 65.0))

    fig_w = max(16.0, min(26.0, n_floors * (plot_w + 12.0) * 0.23))
    fig_h = max(12.0, min(18.0, (plot_l + 16.0) * 0.25))
    fig, axes = plt.subplots(1, n_floors, figsize=(fig_w, fig_h), dpi=min(200, RENDER_DPI))
    fig.patch.set_facecolor(PAPER)

    if n_floors == 1:
        axes = [axes]

    for fi in range(n_floors):
        axes[fi].set_facecolor(PAPER)
        _draw_floor_on_axis(axes[fi], layout, fi, is_furnishing=is_furnishing)

    plt.tight_layout(pad=0.4)
    fname = f"{project_id}_composite_two_floors.png"
    fpath = os.path.join(out_dir, fname)
    plt.savefig(fpath, dpi=min(200, RENDER_DPI), bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    return fpath


# ---------------------------------------------------------------------------
# STANDARD ARCHITECTURAL CAD FRONT ELEVATION RENDERER
# ---------------------------------------------------------------------------

def render_front_elevation_cad(
    layout: Dict[str, Any],
    project_id: str,
    style: str,
    out_dir: str
) -> str:
    """
    Renders a clean, standard architectural CAD Front Elevation sheet with:
    - Vertical height datum lines & elevation markers (Road ±0'-0\", Plinth +2'-6\", GF, FF, Parapet, Mumty)
    - 1:1 horizontally aligned front bays from Ground & First Floor rooms
    - Multi-pane casement windows with frames, mullions, and sill projections
    - Architectural balcony railing, porch canopy & columns, and entrance door detail
    - Vertical height dimension chain on the right side
    """
    plot_w = float(layout.get("plot_width_ft", 35.0))
    plot_l = float(layout.get("plot_length_ft", 65.0))
    total_floors = int(layout.get("total_floors", len(layout.get("floors", [1]))))
    elev = layout.get("elevation_features", {})

    plinth_h  = float(elev.get("plinth_height_ft", 2.5))
    gf_h      = float(elev.get("ground_floor_height_ft", 11.0))
    ff_h      = float(elev.get("first_floor_height_ft", 10.5)) if total_floors >= 2 else 0.0
    parapet_h = float(elev.get("parapet_height_ft", 3.5))
    mumty_w   = float(elev.get("mumty_width_ft", min(10.0, plot_w * 0.35)))
    mumty_h   = 9.0

    total_h = plinth_h + gf_h + ff_h + parapet_h + mumty_h

    fig_w = max(12.0, min(17.0, (plot_w + 14.0) * 0.28))
    fig_h = max(10.5, min(15.0, (total_h + 10.0) * 0.28))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=RENDER_DPI)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    scale = max(0.7, min(1.3, 35.0 / max(plot_w, total_h)))
    lw_heavy = 2.2 * scale
    lw_med   = 1.3 * scale
    lw_light = 0.75 * scale

    # Helper for datum callouts on the left
    def draw_datum(y_val: float, label: str):
        ax.plot([-4.2, plot_w + 1.2], [y_val, y_val], color=INK_LIGHT, linewidth=lw_light * 0.75, linestyle=(0, (6, 4)), zorder=2)
        # Datum triangle marker
        tri = MplPolygon([[-1.4, y_val], [-2.1, y_val + 0.55], [-2.1, y_val - 0.55]], closed=True, facecolor=INK_BLACK, edgecolor=INK_BLACK, zorder=11)
        ax.add_patch(tri)
        ax.text(
            -2.4, y_val, f"{label}  (+{_ft_in_str(y_val)})" if y_val > 0 else f"{label}  (±0'-0\")",
            ha="right", va="center", fontsize=max(5.5, 6.8 * scale),
            fontweight="bold", color=INK_BLACK, fontfamily="DejaVu Sans", zorder=12
        )

    # 1. Ground Road Line (starts at -1.35 so it never crosses the ROAD LVL text at -2.4)
    ax.plot([-1.35, plot_w + 4.0], [0, 0], color=INK_BLACK, linewidth=lw_heavy * 1.4, zorder=10)
    # Earth hatch below ground line
    ax.add_patch(Rectangle((-1.35, -1.0), plot_w + 3.35, 1.0, facecolor="#F1F5F9", edgecolor="none", hatch="///", zorder=1))
    draw_datum(0.0, "ROAD LVL")

    # 2. Plinth Base + Entrance Steps
    ax.add_patch(Rectangle((0, 0), plot_w, plinth_h, facecolor="#E2E8F0", edgecolor=INK_BLACK, linewidth=lw_med, zorder=3))
    pc = elev.get("porch_canopy", {})
    pc_x = max(0.0, min(plot_w - 8.0, float(pc.get("x_ft", 0.0))))
    pc_w = max(8.0, min(plot_w - pc_x, float(pc.get("w_ft", plot_w * 0.42))))
    # Entrance steps in plinth
    for si in range(3):
        sh = (si + 1) * (plinth_h / 3.0)
        ax.plot([pc_x + 1.0, pc_x + pc_w - 1.0], [sh, sh], color=INK_BLACK, linewidth=lw_light, zorder=5)
    draw_datum(plinth_h, "PLINTH FFL")

    # 3. Ground Floor Facade Mass
    gf_y = plinth_h
    ax.add_patch(Rectangle((0, gf_y), plot_w, gf_h, facecolor=ROOM_WHITE, edgecolor=INK_BLACK, linewidth=lw_heavy, zorder=3))
    # Subtle horizontal architectural groove lines on non-porch wall
    wx_start = pc_x + pc_w if pc_x < 1.0 else 0.0
    wx_end = plot_w if pc_x < 1.0 else pc_x
    for gy in np.arange(gf_y + 1.5, gf_y + gf_h - 0.5, 1.5):
        ax.plot([wx_start, wx_end], [gy, gy], color="#E2E8F0", linewidth=lw_light * 0.65, zorder=4)

    # Porch Canopy & Columns (only when the plan has a car porch)
    pc_h = min(gf_h - 0.8, float(pc.get("h_ft", 9.5)))
    if pc or "front_windows" not in elev:
        ax.add_patch(Rectangle((pc_x, gf_y + pc_h), pc_w, 0.85, facecolor=INK_BLACK, edgecolor=INK_BLACK, linewidth=lw_med, zorder=6))
        # Porch columns stand in front of the facade, so they are drawn over windows behind them
        for col_x in [pc_x + 0.35, pc_x + pc_w - 1.15]:
            ax.add_patch(Rectangle((col_x, gf_y), 0.8, pc_h, facecolor="#CBD5E1", edgecolor=INK_BLACK, linewidth=lw_med, zorder=8))

    # Main entrance door — at the plan position when it faces the street; omitted when the
    # plan's main door is on a side wall (not visible in a front elevation)
    ent = elev.get("entrance_door")
    if ent is None:   # legacy layouts without plan-derived features
        ent = {"x_ft": pc_x + (pc_w - min(4.5, pc_w * 0.42)) / 2.0, "w_ft": min(4.5, pc_w * 0.42)}
    if ent:
        door_w = float(ent["w_ft"])
        door_x = float(ent["x_ft"])
        door_h = min(8.0, pc_h - 0.5)
        ax.add_patch(Rectangle((door_x, gf_y), door_w, door_h, facecolor="#F8FAFC", edgecolor=INK_BLACK, linewidth=lw_med, zorder=5))
        ax.plot([door_x + door_w / 2, door_x + door_w / 2], [gf_y, gf_y + door_h], color=INK_BLACK, linewidth=lw_med, zorder=6)
        for p_off in [0.25, door_w / 2 + 0.2]:
            ax.add_patch(Rectangle((door_x + p_off, gf_y + 0.4), door_w / 2 - 0.45, door_h - 0.8, facecolor=ROOM_WHITE, edgecolor=INK_MID, linewidth=lw_light, zorder=6))

    # Helper to draw detailed multi-pane CAD window in elevation
    def draw_elev_window(wx: float, wy: float, ww: float, wh: float):
        wx = max(0.8, min(wx, plot_w - ww - 0.8))
        # Outer frame
        ax.add_patch(Rectangle((wx, wy), ww, wh, facecolor="#F8FAFC", edgecolor=INK_BLACK, linewidth=lw_med, zorder=5))
        # Inner sash frame
        ax.add_patch(Rectangle((wx + 0.25, wy + 0.25), ww - 0.5, wh - 0.5, facecolor=ROOM_WHITE, edgecolor=INK_MID, linewidth=lw_light, zorder=6))
        # Vertical & horizontal mullions
        n_panes = 3 if ww >= 5.5 else 2
        for pi in range(1, n_panes):
            mx = wx + pi * (ww / n_panes)
            ax.plot([mx, mx], [wy + 0.25, wy + wh - 0.25], color=INK_BLACK, linewidth=lw_light, zorder=6)
        ax.plot([wx + 0.25, wx + ww - 0.25], [wy + wh * 0.72, wy + wh * 0.72], color=INK_MID, linewidth=lw_light, zorder=6)
        # Glass reflection diagonal ticks
        ax.plot([wx + 0.6, wx + 1.3], [wy + 0.8, wy + 2.0], color=INK_LIGHT, linewidth=lw_light * 0.7, zorder=6)
        ax.plot([wx + 0.9, wx + 1.4], [wy + 0.8, wy + 1.6], color=INK_LIGHT, linewidth=lw_light * 0.7, zorder=6)
        # Projected sill & lintel sunshade
        ax.add_patch(Rectangle((wx - 0.3, wy - 0.35), ww + 0.6, 0.35, facecolor="#CBD5E1", edgecolor=INK_BLACK, linewidth=lw_light, zorder=6))
        ax.add_patch(Rectangle((wx - 0.4, wy + wh), ww + 0.8, 0.4, facecolor=INK_BLACK, edgecolor=INK_BLACK, linewidth=lw_light, zorder=6))

    # Ground floor windows
    gf_wins = [w for w in elev.get("front_windows", []) if int(w.get("floor", 0)) == 0]
    if not gf_wins and "front_windows" not in elev:
        win_x = pc_x + pc_w + (plot_w - (pc_x + pc_w) - 5.5) / 2.0 if (plot_w - (pc_x + pc_w)) >= 6.5 else 2.5
        gf_wins = [{"x_ft": win_x, "w_ft": min(6.0, max(3.5, plot_w - pc_w - 3.0)), "h_ft": 5.5}]
    for w in gf_wins:
        draw_elev_window(float(w.get("x_ft", 14.0)), gf_y + 2.5, float(w.get("w_ft", 5.0)), float(w.get("h_ft", 5.5)))

    cur_y = gf_y + gf_h
    draw_datum(cur_y, "FIRST FLOOR FFL" if total_floors >= 2 else "ROOF SLAB LVL")

    # 4. First Floor Facade (if multi-storey)
    if total_floors >= 2:
        ff_y = cur_y
        # Floor slab band
        ax.add_patch(Rectangle((-0.3, ff_y - 0.4), plot_w + 0.6, 0.6, facecolor="#CBD5E1", edgecolor=INK_BLACK, linewidth=lw_med, zorder=5))
        ax.add_patch(Rectangle((0, ff_y), plot_w, ff_h, facecolor=ROOM_WHITE, edgecolor=INK_BLACK, linewidth=lw_heavy, zorder=3))

        # Architectural Balcony Projection & Railing
        # Balcony / terrace railings — only where the first-floor plan actually has them
        bal = elev.get("balcony", {})
        bx = max(0.0, min(plot_w - 6.0, float(bal.get("x_ft", pc_x))))
        bw = max(6.0, min(plot_w - bx, float(bal.get("w_ft", pc_w))))
        rails = elev.get("balconies") if "balconies" in elev else ([bal] if bal else [])
        for rb in rails:
            bx = max(0.0, min(plot_w - 2.0, float(rb.get("x_ft", 0.0))))
            bw = max(2.0, min(plot_w - bx, float(rb.get("w_ft", 6.0))))
            rail_h = 3.2
            ax.add_patch(Rectangle((bx - 0.2, ff_y), bw + 0.4, 0.55, facecolor=INK_BLACK, edgecolor=INK_BLACK, linewidth=lw_med, zorder=6))
            ax.add_patch(Rectangle((bx, ff_y + 0.55), bw, rail_h, facecolor="#F8FAFC", edgecolor=INK_BLACK, linewidth=lw_med, zorder=6))
            for rx_post in np.arange(bx + 0.8, bx + bw, 1.1):
                ax.plot([rx_post, rx_post], [ff_y + 0.55, ff_y + 0.55 + rail_h], color=INK_MID, linewidth=lw_light, zorder=7)
            ax.plot([bx, bx + bw], [ff_y + 0.55 + rail_h, ff_y + 0.55 + rail_h], color=INK_BLACK, linewidth=lw_med * 1.2, zorder=7)

        # First floor windows (taken from the plan; invented only for legacy layouts without plan windows)
        ff_wins = [w for w in elev.get("front_windows", []) if int(w.get("floor", 0)) == 1]
        if not ff_wins and "front_windows" not in elev:
            ff_wins = [
                {"x_ft": bx + (bw - 4.5) / 2.0, "w_ft": 4.5, "h_ft": 6.5},
                {"x_ft": min(plot_w - 6.5, bx + bw + 2.5), "w_ft": 5.5, "h_ft": 5.5}
            ]
        for w in ff_wins:
            draw_elev_window(float(w.get("x_ft", 3.0)), ff_y + 2.5, float(w.get("w_ft", 5.0)), float(w.get("h_ft", 5.5)))

        cur_y = ff_y + ff_h
        draw_datum(cur_y, "ROOF SLAB LVL")

    # 5. Parapet Wall & Coping
    ax.add_patch(Rectangle((0, cur_y), plot_w, parapet_h, facecolor="#F1F5F9", edgecolor=INK_BLACK, linewidth=lw_heavy, zorder=4))
    ax.add_patch(Rectangle((-0.4, cur_y + parapet_h - 0.4), plot_w + 0.8, 0.45, facecolor=INK_BLACK, edgecolor=INK_BLACK, zorder=5))
    cur_y += parapet_h
    draw_datum(cur_y, "PARAPET TOP")

    # 6. Stair Mumty Tower (+ every other enclosed room of a designed roof level)
    blocks = elev.get("roof_blocks") or [{"x_ft": float(elev.get("mumty_x_ft", (plot_w - mumty_w) / 2.0)),
                                          "w_ft": mumty_w}]
    for blk in blocks:
        b_w = max(3.0, min(plot_w, float(blk["w_ft"])))
        mumty_x = max(0.0, min(plot_w - b_w, float(blk["x_ft"])))
        ax.add_patch(Rectangle((mumty_x, cur_y), b_w, mumty_h, facecolor=ROOM_WHITE, edgecolor=INK_BLACK, linewidth=lw_heavy, zorder=4))
        ax.add_patch(Rectangle((mumty_x - 0.5, cur_y + mumty_h - 0.5), b_w + 1.0, 0.6, facecolor=INK_BLACK, edgecolor=INK_BLACK, zorder=5))
        # clerestory window louvers
        lw_w = min(b_w * 0.5, 6.0)
        lw_x = mumty_x + (b_w - lw_w) / 2.0
        ax.add_patch(Rectangle((lw_x, cur_y + 2.0), lw_w, 4.5, facecolor="#F8FAFC", edgecolor=INK_BLACK, linewidth=lw_med, zorder=5))
        for ly in np.arange(cur_y + 2.5, cur_y + 6.2, 0.6):
            ax.plot([lw_x + 0.2, lw_x + lw_w - 0.2], [ly, ly], color=INK_MID, linewidth=lw_light, zorder=6)
    # Roof garden planting seen over the parapet
    for g in elev.get("roof_garden", []):
        gx, gw = float(g["x_ft"]), float(g["w_ft"])
        for k, tx in enumerate(np.arange(gx + 1.5, gx + gw - 1.0, 3.0)):
            r_ = 1.1 if k % 2 == 0 else 0.8
            ax.add_patch(Circle((tx, cur_y + r_ * 0.9), r_, facecolor=ROOM_WHITE, edgecolor=INK_MID, linewidth=lw_light, zorder=3.5))
    draw_datum(cur_y + mumty_h, "MUMTY TOP")

    # 7. Overall Width & Total Height Dimension Lines
    dim_x = plot_w + 3.0
    ax.plot([dim_x, dim_x], [0, cur_y + mumty_h], color=INK_BLACK, linewidth=lw_light, zorder=12)
    for py in [0, cur_y + mumty_h]:
        ax.plot([dim_x - 0.4, dim_x + 0.4], [py - 0.4, py + 0.4], color=INK_BLACK, linewidth=lw_med, zorder=13)
    ax.text(
        dim_x + 0.9, (cur_y + mumty_h) / 2.0,
        f"TOTAL HEIGHT: {_ft_in_str(cur_y + mumty_h)}",
        ha="center", va="center", rotation=90,
        fontsize=max(6.0, 7.5 * scale), fontweight="bold", color=INK_BLACK
    )

    ax.text(
        plot_w / 2.0, -3.2,
        f"FRONT ELEVATION (SOUTH FACING)   |   PLOT: {_ft_in_str(plot_w)} × {_ft_in_str(plot_l)}   |   STYLE: {style.upper()}   |   SCALE: 1/8\" = 1'-0\"",
        ha="center", va="top",
        fontsize=max(7.5, 9.5 * scale), fontweight="bold", color=INK_BLACK
    )

    ax.set_xlim(-12.5, plot_w + 6.5)
    ax.set_ylim(-5.2, cur_y + mumty_h + 3.0)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout(pad=0.4)
    fname = f"{project_id}_front_elevation_2d.png"
    fpath = os.path.join(out_dir, fname)
    plt.savefig(fpath, dpi=RENDER_DPI, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    return fpath


# ---------------------------------------------------------------------------
# 3D SPATIAL NODES FOR THREE.JS WEBGL
# ---------------------------------------------------------------------------

def generate_three_d_nodes(layout: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generates 3D extrusion nodes for the Three.js WebGL viewport."""
    nodes = []
    gf_h = float(layout.get("elevation_features", {}).get("ground_floor_height_ft", 11.0))
    ff_h = float(layout.get("elevation_features", {}).get("first_floor_height_ft", 10.5))
    floor_heights = [gf_h, ff_h, 10.0]

    for fi, floor in enumerate(layout.get("floors", [])):
        base_y = sum(floor_heights[:fi]) + fi * 0.5
        is_roof = bool(floor.get("roof"))
        for r in floor.get("rooms", []):
            if is_roof and r.get("category") == "ots":
                continue
            nodes.append({
                "id": r.get("id", uuid.uuid4().hex[:6]),
                "name": r.get("name", "Room"),
                "category": r.get("type", "bedroom"),
                "level": fi,
                "x": float(r.get("x_ft", 0)),
                "y": base_y,
                "z": float(r.get("y_ft", 0)),
                "width": float(r.get("w_ft", 12)),
                "height": ((9.0 if is_enclosed(r.get("category", "room")) else 0.4) if is_roof else
                           (floor_heights[fi] if fi < len(floor_heights) else 10.5)),
                "depth": float(r.get("l_ft", 14))
            })
    return nodes


# ---------------------------------------------------------------------------
# PLAN → ELEVATION COHERENCE (front elevation features derived from the plan geometry)
# ---------------------------------------------------------------------------

def _derive_elevation_features(layout: Dict[str, Any]) -> Dict[str, Any]:
    """Front windows, porch canopy, balcony and mumty position taken from the actual plan."""
    elev = dict(layout.get("elevation_features") or {})
    plot_l = float(layout.get("plot_length_ft", 65.0))
    floors = layout.get("floors", [])
    front_wins = []
    for fl in floors:
        if fl.get("roof"):
            continue
        for w in fl.get("windows", []):
            # A street-facing window sits on a horizontal wall with its room behind it (+y side)
            if w["orient"] != "h" or int(w["into"]) < 0 or w["coord"] > plot_l * 0.5:
                continue
            if w.get("faces_category") not in ("porch", "outdoor", "street"):
                continue
            front_wins.append({"floor": int(fl.get("level", 0)), "x_ft": float(w["s"]), "w_ft": float(w["width"]),
                               "h_ft": 2.0 if w.get("kind") == "ventilator" else 5.0})
    elev["front_windows"] = front_wins
    gf = floors[0]["rooms"] if floors else []
    porch = next((r for r in gf if r.get("category") == "porch"), None)
    if porch:
        elev["porch_canopy"] = {"x_ft": float(porch["x_ft"]), "w_ft": float(porch["w_ft"]),
                                "h_ft": min(10.0, float(elev.get("ground_floor_height_ft", 11.0)) - 1.0)}
    # Railings on the street side of the first floor (balconies and porch-roof terraces)
    rails = []
    if len(floors) > 1 and not floors[1].get("roof"):
        for r in floors[1]["rooms"]:
            nm = str(r.get("name", "")).upper()
            if ("BALCONY" in nm or "TERRACE" in nm) and float(r["y_ft"]) < plot_l * 0.5:
                rails.append({"floor": 1, "x_ft": float(r["x_ft"]), "w_ft": float(r["w_ft"]),
                              "depth_ft": float(r["l_ft"])})
    rails.sort(key=lambda b: 0 if b["depth_ft"] <= 5.0 else 1)
    elev["balconies"] = rails
    elev["balcony"] = rails[0] if rails else {}
    # Main entrance: visible in the front elevation only if it sits on a street-facing wall
    main = next((d for d in (floors[0].get("doors", []) if floors else [])
                 if d.get("kind") in ("main", "main_double")), None)
    if main and main["orient"] == "h" and int(main["into"]) > 0:
        elev["entrance_door"] = {"x_ft": float(main["s"]), "w_ft": float(main["width"])}
    else:
        elev["entrance_door"] = {}
    stair = next((r for r in gf if r.get("category") == "stair"), None)
    if stair:
        elev["mumty_x_ft"] = float(stair["x_ft"])
        elev["mumty_width_ft"] = float(stair["w_ft"])
    # Designed roof level: every enclosed roof room (mumty, servant quarter, prayer room...) rises above
    # the parapet at its plan x-position; a roof garden shows planting over the parapet
    roof = next((fl for fl in floors if fl.get("roof")), None)
    elev["roof_blocks"] = []
    elev["roof_garden"] = []
    if roof:
        spans = sorted((float(r["x_ft"]), float(r["x_ft"]) + float(r["w_ft"])) for r in roof["rooms"]
                       if is_enclosed(r.get("category", classify_room(r))))
        merged: List[List[float]] = []
        for a, b in spans:
            if merged and a <= merged[-1][1] + 0.05:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        elev["roof_blocks"] = [{"x_ft": a, "w_ft": b - a} for a, b in merged]
        elev["roof_garden"] = [{"x_ft": float(r["x_ft"]), "w_ft": float(r["w_ft"])} for r in roof["rooms"]
                               if "GARDEN" in str(r.get("name", "")).upper()]
        if merged:
            elev["mumty_x_ft"] = merged[0][0]
            elev["mumty_width_ft"] = merged[0][1] - merged[0][0]
    return elev


# ---------------------------------------------------------------------------
# RENDER PACKAGE (all sheets from one validated geometry model)
# ---------------------------------------------------------------------------

def render_design_package(layout_data: Dict[str, Any], style: str, project_id: Optional[str] = None,
                          out_root: Optional[str] = None) -> Dict[str, Any]:
    """Renders every CAD sheet for an analysed layout. Returns {project_id, proj_dir, images}."""
    global RENDER_DPI
    plot_w = float(layout_data.get("plot_width_ft", 35.0))
    plot_l = float(layout_data.get("plot_length_ft", 65.0))
    style_slug = re.sub(r"[^a-z0-9]+", "_", style.lower()).strip("_")[:10]
    project_id = project_id or f"archi_{int(plot_w)}x{int(plot_l)}_{style_slug}_{uuid.uuid4().hex[:6]}"
    try:
        return _render_design_package(layout_data, style, project_id, out_root)
    except MemoryError:
        # the computer ran out of free memory while drawing: free what we hold and draw again at a lower
        # resolution rather than lose a finished design
        print(f"[Render] out of memory at {RENDER_DPI} dpi - drawing the sheets again at 110 dpi")
        plt.close("all")
        gc.collect()
        old, RENDER_DPI = RENDER_DPI, 110
        try:
            return _render_design_package(layout_data, style, project_id, out_root)
        finally:
            RENDER_DPI = old
            plt.close("all")


def _render_design_package(layout_data: Dict[str, Any], style: str, project_id: Optional[str] = None,
                           out_root: Optional[str] = None) -> Dict[str, Any]:
    plot_w = float(layout_data.get("plot_width_ft", 35.0))
    plot_l = float(layout_data.get("plot_length_ft", 65.0))
    style_slug = re.sub(r"[^a-z0-9]+", "_", style.lower()).strip("_")[:10]
    pid = project_id or f"archi_{int(plot_w)}x{int(plot_l)}_{style_slug}_{uuid.uuid4().hex[:6]}"
    proj_dir = os.path.join(out_root or OUTPUT_DIR, pid)
    os.makedirs(proj_dir, exist_ok=True)
    web_prefix = f"/output/web_generated/{pid}"

    images: Dict[str, str] = {}
    roof_idx = None
    for fi, _floor in enumerate(layout_data["floors"]):
        if _floor.get("roof"):
            roof_idx = fi
            continue
        lvl_key = "ground" if fi == 0 else "first" if fi == 1 else f"floor_{fi}"
        plan_path = render_floor_plan_cad_sheet(layout_data, fi, pid, style, proj_dir, is_furnishing=False)
        images[lvl_key] = f"{web_prefix}/{os.path.basename(plan_path)}"
        images[f"{lvl_key}_structural"] = images[lvl_key]
        furn_path = render_floor_plan_cad_sheet(layout_data, fi, pid, style, proj_dir, is_furnishing=True)
        images[f"{lvl_key}_furnishing"] = f"{web_prefix}/{os.path.basename(furn_path)}"

    if roof_idx is not None:   # designed roof level (mumty, roof rooms, terrace, garden, plunge pool)
        roof_plan = render_floor_plan_cad_sheet(layout_data, roof_idx, pid, style, proj_dir, is_furnishing=False)
        roof_furn = render_floor_plan_cad_sheet(layout_data, roof_idx, pid, style, proj_dir, is_furnishing=True)
        images["rooftop"] = f"{web_prefix}/{os.path.basename(roof_furn)}"
        images["rooftop_plan"] = f"{web_prefix}/{os.path.basename(roof_plan)}"
    else:
        roof_path = render_rooftop_slab_cad_sheet(layout_data, pid, proj_dir)
        images["rooftop"] = f"{web_prefix}/{os.path.basename(roof_path)}"
    images["rooftop_slab_plan"] = images["rooftop"]
    comp_path = render_composite_multi_floor_cad_sheet(layout_data, pid, proj_dir, is_furnishing=True)
    images["all"] = images["multiFloor"] = images["presentation"] = f"{web_prefix}/{os.path.basename(comp_path)}"
    # elevation and 3D views are projections of ONE massing model built from the plan geometry
    # Render 4 genuinely distinct architectural facade models strictly aligned to the 2D plan solids:
    # 1. modern_cantilever  2. spanish_neoclassical  3. brick_timber_sloped  4. jaali_courtyard
    elev_styles = massing_render.render_all_elevation_styles(layout_data, pid, style, proj_dir, dpi=RENDER_DPI)
    elev_path = elev_styles.get("primary") or elev_styles.get("modern_cantilever")
    images["elevation"] = f"{web_prefix}/{os.path.basename(elev_path)}"
    images["elevation_modern"] = f"{web_prefix}/{os.path.basename(elev_styles['modern_cantilever'])}"
    images["elevation_classical"] = f"{web_prefix}/{os.path.basename(elev_styles['spanish_neoclassical'])}"
    images["elevation_timber"] = f"{web_prefix}/{os.path.basename(elev_styles['brick_timber_sloped'])}"
    images["elevation_jaali"] = f"{web_prefix}/{os.path.basename(elev_styles['jaali_courtyard'])}"
    images["elevation_styles"] = {
        "modern_cantilever": images["elevation_modern"],
        "spanish_neoclassical": images["elevation_classical"],
        "brick_timber_sloped": images["elevation_timber"],
        "jaali_courtyard": images["elevation_jaali"],
        # backward-compatible aliases
        "modern_contemporary": images["elevation_modern"],
        "classical_traditional": images["elevation_classical"],
        "minimalist_timber": images["elevation_timber"],
    }
    for key, path in massing_render.render_3d_views(layout_data, pid, style, proj_dir, dpi=min(170, RENDER_DPI)).items():
        images[f"view3d_{key}"] = f"{web_prefix}/{os.path.basename(path)}"
    images["render3d"] = images.get("view3d_front_right", "")
    return {"project_id": pid, "proj_dir": proj_dir, "images": images}

# ---------------------------------------------------------------------------
# MASTER SYNTHESIS PIPELINE
#   brief -> requirements (rules + Gemini reading, prompt beats form defaults)
#         -> Gemini writes an ArchiScript (design_script.py)
#         -> the CAD engine parses, runs and tests it
#         -> problems go back to Gemini by line number until it passes (MAX_SCRIPT_ROUNDS)
#   No template is substituted: the response is always the AI's own (best) script, with any
#   remaining problems listed so the client can edit the script or ask for a change.
# ---------------------------------------------------------------------------

SCRIPT_MODELS = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-3.1-flash-lite"]
MAX_SCRIPT_ROUNDS = 4        # 1 design call + up to 3 repair calls driven by the CAD engine
SCRIPT_CANDIDATES_FIRST = 3  # designs asked for in parallel in round 1 (the engine keeps the best)
SCRIPT_CANDIDATES_REPAIR = 2 # repairs asked for in parallel in each later round
MAX_CONVERSE_ROUNDS = 4      # the requested change + up to 3 automatic repair/rebalance rounds
MAX_DESIGN_ROUNDS = MAX_SCRIPT_ROUNDS      # backward-compatible name
SCRIPT_THINKING_LEVEL = "MEDIUM"           # Gemini 3 thinking level for script calls
COPY_LIMIT = 0.7             # an upper floor that repeats more than this share of the floor below is sent back
CONCEPT_HISTORY_FILE = os.path.join(PROJECT_ROOT, "output", "design_concepts_history.json")


def call_gemini_text(prompt_text: str, api_key: Optional[str] = None, temperature: float = 0.3) -> Tuple[str, str]:
    """Asks Gemini for an ArchiScript (plain text). Returns (answer text, model used)."""
    key = (api_key or GeminiConfig.get_api_key() or "").strip()
    if not key or len(key) < 12:
        raise ValueError("Valid Google Gemini API Key required. Set GEMINI_API_KEY in .env.")
    client = genai.Client(api_key=key, http_options=types.HttpOptions(api_version="v1beta"))
    last_error: Optional[Exception] = None
    for model_name in SCRIPT_MODELS:
        try:
            # planning a house that passes the geometry checks needs real reasoning: MEDIUM, not LOW
            thinking = None
            if model_name.startswith("gemini-3") and "lite" not in model_name:
                thinking = types.ThinkingConfig(thinking_level=SCRIPT_THINKING_LEVEL)
            elif model_name.startswith("gemini-2.5-flash") and "lite" not in model_name:
                thinking = types.ThinkingConfig(thinking_budget=4096)
            cfg = types.GenerateContentConfig(temperature=temperature, max_output_tokens=24576, thinking_config=thinking)
            try:
                resp = client.models.generate_content(model=model_name, contents=prompt_text, config=cfg)
            except Exception as e_think:
                if thinking is None or "thinking" not in str(e_think).lower():
                    raise
                print(f"[Gemini script] {model_name} refused thinking {SCRIPT_THINKING_LEVEL}; retrying LOW")
                cfg = types.GenerateContentConfig(temperature=temperature, max_output_tokens=16384,
                                                  thinking_config=types.ThinkingConfig(thinking_level="LOW"))
                resp = client.models.generate_content(model=model_name, contents=prompt_text, config=cfg)
            text = resp.text or ""
            if re.search(r"\bLEVEL\b", text, re.I) and "|" in text:
                return text, model_name
            # a repair asked for as line edits is answered with edits, not with a whole script
            if re.search(r"^\s*[-*]?\s*(REPLACE|INSERT AFTER|DELETE)\s+(LINE\s+)?\d+", text, re.I | re.M):
                return text, model_name
            last_error = ValueError(f"{model_name} answered without an ArchiScript")
            print(f"[Gemini script] {last_error}")
        except Exception as e:
            print(f"[Gemini script] {model_name} failed: {str(e)[:200]}")
            last_error = e
    raise RuntimeError(f"Gemini script generation failed on all models. Last error: {last_error}")


def _size_notions(custom_room_dimensions: Optional[List[Any]]) -> str:
    """No standard / typical room sizes are given to the AI - only sizes the client typed in the room
    schedule (the AI-prompt flow sends none: sizes come from the prompt itself)."""
    sched = [f"{it.get('name')} {it.get('widthFt', '?')}' x {it.get('lengthFt', '?')}' ({it.get('floor', 'any floor')})"
             for it in (custom_room_dimensions or []) if isinstance(it, dict) and it.get("name")]
    return ("- Room sizes the client entered: " + "; ".join(sched[:12])) if sched else ""


def prepare_design_context(prompt: str, plot_width: float, plot_length: float, floors: int, bedrooms: int,
                           bathrooms: int, style: str, api_key: Optional[str] = None,
                           custom_room_dimensions: Optional[List[Any]] = None,
                           requirements: Optional[Dict[str, Any]] = None,
                           setbacks: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Requirements (the prompt wins over any form defaults), optional setbacks from the prompt (0 by default so the AI
    can use the full plot when fitting dense layouts like 5 rooms in 5 Marla), and the level plan."""
    W, L = float(plot_width), float(plot_length)
    floors = int(floors or 0)
    marla_label = f"{round(W * L / 225.0, 1):g} Marla"
    brief = (prompt or "").strip() or (
        f"Design a {marla_label} ({W:.0f}'x{L:.0f}') {style} residence with {floors} storeys, "
        f"{bedrooms} bedrooms and {bathrooms} bathrooms.")
    future = None
    if requirements is None:
        _pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = _pool.submit(extract_requirements_llm, brief, api_key)
        _pool.shutdown(wait=False)
    front_sb, rear_sb = 0.0, 0.0
    for side in ("front", "rear"):
        v = (setbacks or {}).get(side)
        if v is not None:
            if side == "front":
                front_sb = float(v)
            else:
                rear_sb = float(v)

    if requirements is not None:
        req = {k: v for k, v in dict(requirements).items() if k not in ("checklist", "understood_as")}
        req.setdefault("raw_brief", brief)
        for k in ("notes", "other_requests", "extra_rooms"):
            req.setdefault(k, [])
        llm_reading = {}
    else:
        req = parse_brief(brief, W, L, floors, bedrooms, bathrooms)
        for item in custom_room_dimensions or []:
            nm = str(item.get("name", "")).lower() if isinstance(item, dict) else ""
            if "pool" in nm and not req.get("pool"):
                req["pool"] = {"location": "rear"}
        try:
            llm_reading = future.result(timeout=30) if future else {}
        except Exception as e_read:
            print(f"[Gemini brief reading] skipped: {e_read}")
            llm_reading = {}
        req = merge_llm_requirements(req, llm_reading, bedrooms, bathrooms, floors)
    req["checklist"] = build_checklist(req, bedrooms, bathrooms, floors)
    print("[Brief] understood:", req.get("understood_as"))

    portion = req.get("portion") or {}
    if portion.get("kind") == "upper":
        lvl = int(portion.get("level", 1))
        label = {1: "FIRST FLOOR PORTION", 2: "SECOND FLOOR PORTION", 3: "THIRD FLOOR PORTION"}.get(lvl, "UPPER PORTION")
        levels_note = (f"Levels: this is an UPPER-FLOOR PORTION only. Write ONLY LEVEL {lvl} \"{label}\" - no ground floor, "
                       f"no car porch. It is reached by the STAIR coming up from the ground: include that stair "
                       f"and mark the entrance gate.")
    elif floors:
        n = floors
        ctx_same_layout = bool(req.get("same_layout"))
        levels_note = (f"Levels: whole house of {n} storey(s): write LEVEL 0" + (f" to LEVEL {n - 1}" if n > 1 else "") +
                       (". The stair keeps its rectangle on every level; each level is planned for its own rooms"
                        + (" (the client wants the SAME layout on every floor)" if ctx_same_layout else "") + ". "
                        if n > 1 else ". One storey: there is no upper floor, so no STAIR unless the brief asks for one. ")
                       +
                       "Add a ROOF level only if the client asks for roof items (roof terrace / garden / pool, rooms on the roof).")
    else:
        levels_note = ("Levels: the brief does not say how many storeys - use the fewest levels that hold everything the "
                       "client asked for with rooms that work (LEVEL 0 alone, or LEVEL 0 and LEVEL 1 with a stair). The "
                       "stair keeps its rectangle on every level. Add a ROOF level only if the client asks for roof items.")
    rag_info = {"context_text": "", "references": [], "mode": "disabled"}
    try:
        rag_info = build_planner_context(brief, W, L, floors, top_k=5, api_key=api_key)
    except Exception as e_rag:
        print(f"[Pakistan RAG] notice: {e_rag}")
    return {"brief": brief, "W": W, "L": L, "floors": floors, "style": style, "marla_label": marla_label,
            "setbacks_from_prompt": {k: v for k, v in (setbacks or {}).items() if v is not None},
            "front_sb": front_sb, "rear_sb": rear_sb, "req": req, "llm_reading": llm_reading,
            "bedrooms": req["bedrooms"], "bathrooms": req["bathrooms"], "levels_note": levels_note,
            "size_notions": _size_notions(custom_room_dimensions), "api_key": api_key,
            "rag_context": rag_info.get("context_text", ""),
            "rag_references": rag_info.get("references", []),
            "rag_mode": rag_info.get("mode", "lexical")}


def _ascii_map(geo: Dict[str, Any], levels: Optional[set] = None) -> str:
    """A small picture of what the script built, so the AI can SEE which rooms touch: one character per cell,
    top row = street side, one letter per room."""
    W, L = float(geo.get("plot_width_ft") or 0), float(geo.get("plot_length_ft") or 0)
    if not W or not L:
        return ""
    cell = max(1.5, round(max(W, L) / 32.0 * 2) / 2.0)
    cols, rows = int(math.ceil(W / cell - 1e-6)), int(math.ceil(L / cell - 1e-6))
    symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"
    out = []
    for fl in geo.get("floors", []):
        if levels is not None and fl.get("level") not in levels:
            continue
        grid = [["." for _ in range(cols)] for _ in range(rows)]
        legend = []
        for i, r in enumerate(fl.get("rooms", [])[:len(symbols)]):
            ch = symbols[i]
            legend.append(f"{ch}={r['name']}")
            x0, y0 = float(r["x_ft"]), float(r["y_ft"])
            x1, y1 = x0 + float(r["w_ft"]), y0 + float(r["l_ft"])
            for row in range(rows):
                cy = (row + 0.5) * cell
                if y0 <= cy < y1:
                    for col in range(cols):
                        if x0 <= (col + 0.5) * cell < x1:
                            grid[row][col] = ch
        out.append(f"LEVEL {fl.get('level')}{' (roof)' if fl.get('roof') else ''} - top row = street side, "
                   f"1 character = {cell:g} ft")
        out += ["  " + "".join(row) for row in grid]
        out.append("  " + ", ".join(legend))
    return "\n".join(out)


def _add_fix_hints(geo: Dict[str, Any], v: Dict[str, Any]) -> None:
    """Turns 'what is wrong' into 'how to fix it in the script': a door problem lists the spaces the room really
    touches (so the AI picks a real neighbour instead of guessing), a windowless room gets the moves that give it
    open air, and a bed that does not fit says what it needs."""
    from generation.plan_geometry_engine import shared_edge
    by_level = {fl.get("level"): fl for fl in geo.get("floors", [])}

    def neighbours(level, rid):
        fl = by_level.get(level) or {}
        rooms = fl.get("rooms", [])
        r = next((x for x in rooms if x.get("id") == rid), None)
        if not r:
            return None, []
        out = []
        for o in rooms:
            e = shared_edge(r, o) if o is not r else None
            if e and e[3] - e[2] >= 3.9:
                out.append((e[3] - e[2], o["name"]))
        return r, [f"{n} ({ln:.0f} ft)" for ln, n in sorted(out, reverse=True)[:8]]
    for i in v.get("errors", []):
        if i["code"] == "UNREACHABLE":
            # a terrace / balcony nobody can step onto: open spaces never take door: themselves, so the general
            # "give it a door" advice cannot be followed - say which room should open onto it
            r, nb = neighbours(i.get("floor"), i.get("room"))
            if r and not is_enclosed(r.get("category")):
                i["code"] = "OPEN_SPACE_NO_DOOR"
                i["message"] = (f"{r['name']} is a terrace / balcony that no room opens onto, so nobody can step on it. "
                                f"It touches: {', '.join(nb) or 'no room along 4 ft'}. Fix: on ONE of those rooms' lines "
                                f"add `extra door: {r['name']}` (do not write door: on {r['name']} itself); or, if nobody "
                                f"needs to walk there, change its type to open")
        elif i["code"] == "DOOR_NO_SHARED_WALL":
            r, nb = neighbours(i.get("floor"), i.get("room"))
            if r:
                i["message"] += (f". {r['name']} really touches: {', '.join(nb) or 'no space with a 4 ft wall'} - write "
                                 f"door: one of these (lobby / lounge / corridor / gallery / its own room), or move "
                                 f"{r['name']} beside the space you want it entered from")
        elif i["code"] == "CAR_PORCH_TOO_SMALL":
            i["message"] += (" - fix: the CAR PORCH must be ONE space at least 10 ft wide and 16 ft deep, so do not split it "
                             "into a driveway band plus a porch band: give the front a band at least 16-18 ft deep whose "
                             "first column is the CAR PORCH (full depth) and whose other column is a ROWS with the lawn in "
                             "front (setback depth) and rooms behind it")
        elif i["code"] == "SETBACK_REAR":
            i["message"] += (" - fix: make the LAST band of that level's root ROWS the rear setback on its own (e.g. "
                             "'<rear setback> | REAR OPEN | open') so no column runs into it")
        elif i["code"] == "SETBACK_FRONT":
            i["message"] += (" - fix: the front-setback depth holds only porch / driveway / lawn (ground) or balcony / "
                             "terrace / open (upper levels); start enclosed rooms behind it")
        elif i["code"] == "STAIR_TOO_SMALL":
            i["message"] += (" - fix: give the STAIR a rectangle at least 3.5 ft by 9 ft (a dog-leg stair is about "
                             "7 x 10 ft, a straight flight about 3.5 x 14 ft) and take the area from the lounge / passage")
        elif i["code"].startswith("WALK_THROUGH") and i["code"] != "WALK_THROUGH_STAIR":
            i["message"] += (" - fix: give that room its own door: to the lounge / lobby / corridor / gallery (move it "
                             "so it shares a 3 ft wall with one), or put a corridor beside the bedroom")
        elif i["code"] == "LANDLOCKED" and "no window fits" in i["message"]:
            i["message"] += (" - fix: lengthen the wall it shares with that open space to 8 ft or more, or enter the "
                             "room from another side so the open-air wall is free for the window")
        elif i["code"] == "LANDLOCKED" and "no wall on open air" in i["message"]:
            i["message"] += (" - fix: move it into the front or rear band, or put an OTS (type ots) or the gallery "
                             "next to it in the same ROWS / COLS group so one of its walls faces open air")
    for w in v.get("warnings", []):
        if w["code"] == "FURNITURE_UNPLACED" and re.search(r"\bbed_|sofa_bed", w["message"]):
            fl = by_level.get(w.get("floor")) or {}
            r = next((x for x in fl.get("rooms", []) if x.get("id") == w.get("room")), None)
            nd = sum(1 for d in fl.get("doors", []) if w.get("room") in (d.get("room_id"), d.get("from_id")))
            if r:
                w["message"] += (f" ({r['name']} is {_ft_in_str(float(r['w_ft']))} x {_ft_in_str(float(r['l_ft']))} with "
                                 f"{nd} door(s): a bed needs one clear wall about 6'-6\" long away from the door swings "
                                 f"and windows, with walking space beside it - lengthen that wall, put the attached bath "
                                 f"BESIDE the room instead of across its free wall, or move a door")


_OUTSIDE_STAIR_RE = re.compile(r"separate (entrance|entry|access|portion|stair)|independent (entrance|entry|access|portion)"
                               r"|(external|outside|outdoor|outer) stair|stairs? (from|in|at) (the )?(porch|outside|street|lawn|front)"
                               r"|rent|tenant", re.I)


def _evaluate_script(script: str, ctx: Dict[str, Any], rnd: int, source: str, model: Optional[str],
                     enforce_setbacks: bool = False, scope: Optional[set] = None,
                     with_requirements: bool = True, req_level: Optional[int] = None,
                     req_whole: bool = True) -> Dict[str, Any]:
    """Parse + run + test one script. Returns the candidate with geometry, problems and requirement report.
    scope = the levels being designed in this step (problems of the fixed levels below are not counted or sent);
    with_requirements = False while the house is still being designed level by level."""
    parsed = parse_script(script, ctx["W"], ctx["L"])
    ssb = parsed["script_setbacks"]
    prompt_sb = ctx.get("setbacks_from_prompt") or {}
    fsb = float(prompt_sb["front"]) if (enforce_setbacks and "front" in prompt_sb) else float(ssb.get("front", ctx["front_sb"]))
    rsb = float(prompt_sb["rear"]) if (enforce_setbacks and "rear" in prompt_sb) else float(ssb.get("rear", ctx["rear_sb"]))
    layout = {"project_title": f"{ctx['W']:g}' x {ctx['L']:g}' - designed from the brief",
              "design_rationale": ctx["req"].get("understood_as", ""), "floors": parsed["floors"]}
    geo = analyse_layout(layout, ctx["W"], ctx["L"], fsb, rsb, ctx["bedrooms"], ctx["bathrooms"])
    v = geo["validation"]
    _add_fix_hints(geo, v)
    if not _OUTSIDE_STAIR_RE.search(str(ctx.get("brief") or "")):
        # a stair reached only from outside is a failure unless the brief asks for a separate entrance upstairs
        moved = [w for w in v.get("warnings", []) if w["code"] == "STAIR_OUTSIDE_ONLY"]
        for w in moved:
            w["severity"] = "error"
        v["warnings"] = [w for w in v.get("warnings", []) if w["code"] != "STAIR_OUTSIDE_ONLY"]
        v["errors"] = v["errors"] + moved
    v["errors"] = parsed["errors"] + v["errors"]
    v["warnings"] = parsed["warnings"] + v["warnings"]
    v["status"] = "PASS" if not v["errors"] else "FAIL"
    v["score"] = max(0.0, round(1.0 - 0.12 * len(v["errors"]) - 0.015 * len(v["warnings"]), 3))
    def in_scope(i):
        return scope is None or i.get("floor") is None or i.get("floor") in scope
    errs = [i for i in v["errors"] if in_scope(i)]
    warns = [i for i in v["warnings"] if in_scope(i)]
    report = check_requirements(geo, ctx["req"], ctx["bedrooms"], ctx["bathrooms"]) if with_requirements else []
    if req_level is not None:      # level-by-level design: the checks of this level (+ whole-house ones at the end)
        report = [r for r in report if r.get("level") == req_level or (req_whole and r.get("level") is None)]
    unmet = [r for r in report if not r["met"]]
    # a bedroom without a bed or a kitchen without a counter is a design failure, not a cosmetic warning
    key_missing, key_items = [], []
    for w in warns:
        m = re.search(r"\b(bed_\w+|sofa_bed|kitchen_counter|wc|prayer_mat|floor_seating)\b", w["message"])
        if w["code"] == "FURNITURE_UNPLACED":
            info = parsed["rooms"].get((w.get("floor"), w.get("room")))
            where = f"line {info['line']} ({info['name']}): " if info else ""
            key_missing.append(f"- [FURNITURE_DOES_NOT_FIT] {where}{w['message']} - give the room a longer clear wall "
                               f"(widen it or move its doors off that wall); do not drop the furniture")
            if m:
                key_items.append({"floor": w.get("floor"), "room": w.get("room"), "item": m.group(1),
                              "name": info["name"] if info else w.get("room"), "problem": key_missing[-1]})
    for w in warns:
        if w["code"] == "DOOR_SWING_CLASH":
            info = parsed["rooms"].get((w.get("floor"), w.get("room")))
            where = f"line {info['line']} ({info['name']}): " if info else ""
            key_missing.append(f"- [DOOR_SWING_CLASH] {where}{w['message']} - two doors cannot swing through the same "
                               f"floor space: move one of them along its wall or onto another wall")
    problems = script_issue_lines({"errors": errs}, parsed["rooms"]) + \
        [f"- [REQUIREMENT_MISSING] {r['item']}: {r['detail']}" for r in unmet] + key_missing
    # layout notes: relative quality checks (proportion, wasted area, door clashes, unventilated baths) - advice
    notes, major = [], 0
    for w in warns:
        if w["code"] in LAYOUT_NOTE_CODES:
            info = parsed["rooms"].get((w.get("floor"), w.get("room")))
            where = f"line {info['line']} ({info['name']}): " if info else ""
            notes.append(f"- [{w['code']}] {where}{w['message']}")
            major += w["code"] in ("PROPORTION", "WASTED_SPACE", "BALANCE", "TIGHT_ROOM")
    return {"round": rnd, "source": source, "model": model, "script": parsed["normalised_script"], "geo": geo,
            "parsed": parsed, "errors": len(errs), "warnings": len(warns), "requirements": report,
            "unmet": len(unmet), "quality": len(key_missing), "key_missing_items": key_items, "problems": problems,
            "notes": notes, "major_notes": major, "front_sb": fsb, "rear_sb": rsb}


LAYOUT_NOTE_CODES = ("PROPORTION", "WASTED_SPACE", "BALANCE", "TIGHT_ROOM", "BATH_NO_VENT", "OTS_COVERED")


def _furniture_family(item: str) -> str:
    item = (item or "").lower()
    if item.startswith("bed_"):
        return "bed"
    return {"floor_seating": "floor_cushion", "kitchen_counter": "counter"}.get(item, item)


def _lost_furniture(cand: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Key furniture (bed, sofa bed, counter, WC, prayer mat, floor seating) that fitted in the current design
    but no longer fits after the change - a change must not take away what the client already had."""
    had = {(fl.get("level"), f.get("room_id"), _furniture_family(f.get("type")))
           for fl in current["geo"].get("floors", []) for f in fl.get("furniture", [])}
    return [m for m in cand.get("key_missing_items", [])
            if (m["floor"], m["room"], _furniture_family(m["item"])) in had]


def synthesize_design(
    prompt: str,
    plot_width: float = 35.0,
    plot_length: float = 65.0,
    floors: int = 2,
    bedrooms: int = 4,
    bathrooms: int = 4,
    style: str = "Modern Contemporary",
    api_key: Optional[str] = None,
    budget_tier: str = "balanced",
    custom_room_dimensions: Optional[List[Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Designs from the prompt: Gemini writes an ArchiScript, the CAD engine runs and tests it, and every
    problem goes back to Gemini by line number until the script passes (MAX_SCRIPT_ROUNDS). The AI's own best
    script is returned - no template is swapped in. If Gemini is unreachable the error propagates."""
    ctx = prepare_design_context(prompt, plot_width, plot_length, floors, bedrooms, bathrooms, style, api_key,
                                 custom_room_dimensions, kwargs.get("requirements"), kwargs.get("setbacks"))
    base = build_script_prompt(ctx["brief"], ctx["req"]["checklist"], ctx["W"], ctx["L"], ctx["front_sb"],
                               ctx["rear_sb"], ctx["levels_note"], ctx["size_notions"], kwargs.get("style_label", style))
    if ctx.get("rag_context"):
        base = base + "\n\n" + ctx["rag_context"]
    portion = (ctx["req"].get("portion") or {}).get("kind") == "upper"
    if int(ctx["floors"] or 0) >= 2 and not portion:
        # a house of 2+ storeys is designed level by level: the ground floor is designed and checked first and stays
        # fixed while each upper level is designed on top of it
        best, attempts = _staged_synthesis(ctx, api_key, kwargs.get("style_label", style))
        _remember_concept(ctx, best.get("concept"))
        improved = _improve_from_review(ctx, best, base, api_key)
        if improved is not best:
            attempts.append(improved)
        return _design_response(improved, attempts, ctx, style, mode="generate")
    attempts: List[Dict[str, Any]] = []
    concepts = propose_concepts(ctx, api_key, max(1, SCRIPT_CANDIDATES_FIRST))
    text: Any = [base + _concept_text(c) for c in concepts] or base
    used: List[Optional[Dict[str, Any]]] = list(concepts)
    polished = False
    patch_src: Optional[str] = None
    for rnd in range(1, MAX_SCRIPT_ROUNDS + 1 + 2 * FRESH_STARTS):
        temps = [0.5, 0.65, 0.8][:max(1, SCRIPT_CANDIDATES_FIRST)] if rnd == 1 else \
            [0.2, 0.5, 0.75][:max(1, SCRIPT_CANDIDATES_REPAIR)]
        if rnd > MAX_SCRIPT_ROUNDS and (rnd - MAX_SCRIPT_ROUNDS) % 2 == 1:
            # FRESH START: the repairs did not converge - the skeleton is wrong. Design again on another layout idea,
            # knowing what failed; the round after it repairs that new design.
            top = min(attempts, key=_attempt_rank)
            if not top["errors"] + top["unmet"]:
                break
            lesson = ("\n=== AN EARLIER DESIGN COULD NOT BE REPAIRED ===\n" + top["script"] +
                      "\nWhat the engine found in it:\n" + "\n".join(top["problems"][:8]) +
                      "\nDo NOT repair that script. Its skeleton caused these problems - start again from a "
                      "different, simpler skeleton in which they cannot happen: every room sits beside the shared "
                      "space it opens onto, and every bedroom / lounge / kitchen has one wall on open air.\n")
            if rnd > MAX_SCRIPT_ROUNDS + 1:
                try:
                    concepts = concepts + propose_concepts(ctx, api_key, 2)
                except Exception as e_c:
                    print(f"[Concepts] second proposal failed: {e_c}")
            tried = {id(a.get("concept")) for a in attempts}
            fresh = ([c for c in concepts if id(c) not in tried] or
                     [c for c in concepts if c is not top.get("concept")])[:2] or [top.get("concept")]
            text = [base + _concept_text(c) + lesson for c in fresh]
            used = list(fresh)
            temps = [0.4, 0.7][:len(text)]
            patch_src = None
            print(f"[Gemini script] repairs did not converge ({top['errors']} errors) - fresh start")
        answers = _parallel_scripts(text, api_key, temps)
        good = [(a, used[i] if i < len(used) else None) for i, a in enumerate(answers) if not isinstance(a, Exception)]
        if not good:
            if attempts:
                print(f"[Gemini script] round {rnd} failed: {answers[0]}")
                break
            raise answers[0]
        # the engine tests every candidate of the round and keeps the best one
        round_cands = []
        for (ans, model), concept in good:
            c = _evaluate_script(_answer_script(ans, patch_src), ctx, rnd, "gemini", model)
            c["concept"] = concept
            round_cands.append(c)
        cand = min(round_cands, key=_attempt_rank)
        cand["candidates"] = len(round_cands)
        attempts.append(cand)
        print(f"[Gemini script] round {rnd}: best of {len(round_cands)} -> {cand['errors']} errors, "
              f"{cand['warnings']} warnings, {cand['unmet']} unmet requirements, {len(cand['notes'])} layout notes "
              f"(others: {[c['errors'] for c in round_cands if c is not cand]})")
        clean = not cand["errors"] and not cand["unmet"] and not cand["quality"]
        # a clean script with long-thin rooms or wasted area gets ONE polish round (kept only if it scores better)
        if clean and (not cand["major_notes"] or polished):
            break
        polished = polished or clean
        # always repair the BEST script so far - a round that made things worse is not built upon
        top = min(attempts, key=_attempt_rank)
        used = [top.get("concept")] * SCRIPT_CANDIDATES_REPAIR      # a repair keeps the concept of the script it repairs
        text, patch_src = _repair_text(base + _concept_text(top.get("concept")), top, ctx, rnd, top["script"],
                                       _ascii_map(top["geo"]), top["notes"][:12 if clean else 6])
        if patch_src:
            print(f"[Gemini script] {top['errors'] + top['unmet'] + top['quality']} problem(s) left - asking for line edits")
    best = min(attempts, key=_attempt_rank)
    _remember_concept(ctx, best.get("concept"))
    improved = _improve_from_review(ctx, best, base, api_key)
    if improved is not best:
        attempts.append(improved)
    return _design_response(improved, attempts, ctx, style, mode="generate")



# ---------------------------------------------------------------------------
# Unique designs: every parallel candidate follows a DIFFERENT layout concept
# ---------------------------------------------------------------------------

_CONCEPT_FALLBACK = [
    {"name": "Central lounge hub", "stair": "at one side of the middle band, entered from the lounge",
     "lounge": "middle of the plot, rooms open off it", "circulation": "lounge is the hub - no corridor",
     "bedrooms": "back band facing the rear open space", "open_space": "front lawn / porch and a rear strip, OTS beside the lounge"},
    {"name": "Side corridor spine", "stair": "near the entrance at the front, off the lobby",
     "lounge": "front half behind the drawing / porch", "circulation": "a corridor along one side wall from front to back",
     "bedrooms": "in a row off the corridor, each beside a small OTS or the rear strip", "open_space": "rear strip plus OTS shafts on the party-wall side"},
    {"name": "Courtyard house", "stair": "beside the courtyard", "lounge": "wrapped around the courtyard",
     "circulation": "rooms ring a central OTS courtyard that lights them", "bedrooms": "split - some at the front, some at the back",
     "open_space": "one generous central OTS / courtyard, small front and rear open strips"},
    {"name": "Front living, rear sleeping", "stair": "at the back, off a lobby between living and bedrooms",
     "lounge": "front, looking onto the lawn / street", "circulation": "short lobby between the two zones",
     "bedrooms": "all in the quiet rear half", "open_space": "front lawn and a wide rear open space"},
    {"name": "Rear living, front sleeping", "stair": "in the middle beside the entrance lobby",
     "lounge": "at the back opening onto a rear lawn / terrace", "circulation": "entrance lobby leading straight to the rear lounge",
     "bedrooms": "at the front beside the porch, windows to the street side", "open_space": "large rear lawn / terrace, compact front"},
    {"name": "Split by a gallery", "stair": "at the end of an open gallery", "lounge": "one side of the gallery",
     "circulation": "an open gallery / verandah across the plot gives every room air", "bedrooms": "across the gallery from the living rooms",
     "open_space": "the gallery itself plus the rear strip"},
]


def _concept_key(ctx: Dict[str, Any]) -> str:
    brief = re.sub(r"\s+", " ", (ctx.get("brief") or "").strip().lower())
    return hashlib.sha1(f"{brief}|{ctx['W']:g}x{ctx['L']:g}".encode("utf-8")).hexdigest()[:16]


def _concept_history(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        with open(CONCEPT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return list((json.load(f) or {}).get(_concept_key(ctx), []))
    except Exception:
        return []


def _remember_concept(ctx: Dict[str, Any], concept: Optional[Dict[str, Any]]) -> None:
    """The concept of the design the client was shown - the next design for the same brief avoids it."""
    if not concept:
        return
    try:
        data: Dict[str, Any] = {}
        if os.path.exists(CONCEPT_HISTORY_FILE):
            with open(CONCEPT_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        used = data.setdefault(_concept_key(ctx), [])
        used.append({k: concept.get(k) for k in ("name", "stair", "lounge", "circulation", "bedrooms", "open_space")})
        data[_concept_key(ctx)] = used[-8:]
        if len(data) > 300:
            for k in list(data)[:len(data) - 300]:
                data.pop(k, None)
        os.makedirs(os.path.dirname(CONCEPT_HISTORY_FILE), exist_ok=True)
        with open(CONCEPT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    except Exception as e:
        print(f"[Concepts] history not saved: {e}")


def _concept_text(c: Optional[Dict[str, Any]]) -> str:
    if not c:
        return ""
    rows = [f"- {label}: {c[k]}" for k, label in (("stair", "Stair"), ("lounge", "Lounge / living"),
                                                  ("circulation", "Circulation"), ("bedrooms", "Bedrooms"),
                                                  ("open_space", "Open space / daylight")) if c.get(k)]
    return (f"\n=== LAYOUT CONCEPT FOR THIS DESIGN: \"{c.get('name', 'concept')}\" ===\n"
            "Several architects are designing this house in parallel, each with a different concept. This is YOURS - "
            "follow it so your design is different from theirs. Where it conflicts with the client's brief, the brief wins.\n"
            + "\n".join(rows) + "\n")


def propose_concepts(ctx: Dict[str, Any], api_key: Optional[str], n: int = 3) -> List[Dict[str, Any]]:
    """n layout concepts that differ in stair position, lounge position, circulation and bedroom zone, written
    for THIS brief and plot, avoiding the concepts already used for the same brief. One small Gemini call; if it
    fails, concepts are drawn from a built-in list so the designs still differ."""
    used = _concept_history(ctx)
    used_names = {str(u.get("name", "")).lower() for u in used}
    concepts: List[Dict[str, Any]] = []
    req = ctx["req"]
    fixed = [c for c in req.get("checklist", []) if re.search(r"STAIR|SAME layout|CORRIDOR|MASTER", c)]
    prompt = f"""You are a residential architect. Propose {n} clearly DIFFERENT layout concepts for this house.
BRIEF: "{ctx['brief']}"
PLOT: {ctx['W']:g} ft wide (street side) x {ctx['L']:g} ft deep, {ctx['floors'] or 'as few as needed'} storey(s). The two side boundaries are party walls (no windows); daylight comes from the street front, the rear, and any lawn / open strip / OTS / gallery you leave open.
{("THE BRIEF FIXES (keep these the same in every concept): " + "; ".join(fixed)) if fixed else ""}
{("ALREADY USED for this brief - propose concepts that differ from ALL of these: " + json.dumps(used[-6:])) if used else ""}
Any two concepts must differ in at least THREE of: stair position, where the lounge sits, circulation type (lounge hub / corridor spine / central courtyard / open gallery), where the bedrooms are, where the open space goes.
Each concept must let every bedroom, lounge and kitchen have a window, and must fit this plot.
Return JSON only: {{"concepts": [{{"name": "3-5 words", "stair": "...", "lounge": "...", "circulation": "...", "bedrooms": "...", "open_space": "..."}}]}}"""
    try:
        raw = _call_interview_llm_json(prompt, api_key) or ""
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        data = json.loads(raw)
        for c in (data.get("concepts") if isinstance(data, dict) else data) or []:
            if isinstance(c, dict) and c.get("name") and str(c["name"]).lower() not in used_names:
                concepts.append({k: str(c.get(k, ""))[:220] for k in ("name", "stair", "lounge", "circulation",
                                                                      "bedrooms", "open_space")})
                concepts[-1]["source"] = "gemini"
    except Exception as e:
        print(f"[Concepts] Gemini concepts skipped: {str(e)[:160]}")
    if len(concepts) < n:
        pool = [dict(c, source="built-in") for c in _CONCEPT_FALLBACK
                if c["name"].lower() not in used_names and c["name"] not in {x["name"] for x in concepts}]
        random.shuffle(pool)
        concepts += pool[:n - len(concepts)]
    print("[Concepts]", [c["name"] for c in concepts[:n]], "| already used:", sorted(used_names))
    return concepts[:n]


# ---------------------------------------------------------------------------
# Right designs: a room budget for every level, and no copied floors
# ---------------------------------------------------------------------------

def _level_program(geo: Dict[str, Any], level: int) -> Dict[str, int]:
    """Bedrooms, bedrooms with their own bath, and baths the engine built on one level."""
    fl = next((f for f in geo.get("floors", []) if f.get("level") == level and not f.get("roof")), None)
    if not fl:
        return {"beds": 0, "attached": 0, "baths": 0}
    cat = {r["id"]: r.get("category") for r in fl.get("rooms", [])}
    beds = [r["id"] for r in fl.get("rooms", []) if r.get("category") == "bedroom" and "SERVANT" not in r["name"].upper()]
    with_bath = set()
    for d in fl.get("doors", []):
        a, b = d.get("room_id"), d.get("from_id")
        if cat.get(a) == "bath" and b in beds:
            with_bath.add(b)
        if cat.get(b) == "bath" and a in beds:
            with_bath.add(a)
    return {"beds": len(beds), "attached": len(with_bath), "baths": sum(1 for c in cat.values() if c == "bath")}


def _level_budget(req: Dict[str, Any], k: int, n_levels: int, done: Dict[str, int]) -> Dict[str, int]:
    """What level k must hold so the whole house adds up: the client's own per-floor numbers when the brief gives
    them, else what is still missing shared over the levels that are left (upper levels take the remainder - the
    ground floor also carries the porch, drawing room and kitchen). `done` = what the fixed levels already hold."""
    left = n_levels - k

    def share(total: int, have: int) -> int:
        remaining = max(0, int(total or 0) - have)
        return remaining if left <= 1 else remaining // left
    given = {int(a): int(b) for a, b in (req.get("beds_per_level") or {}).items()}
    beds = given[k] if k in given else share(req.get("bedrooms"), done["beds"])
    attached = min(beds, share(req.get("attached_baths"), done["attached"])) if req.get("attached_baths") else 0
    if left <= 1 and req.get("attached_baths"):
        attached = max(0, int(req["attached_baths"]) - done["attached"])
    baths = max(attached, share(req.get("bathrooms"), done["baths"]))
    return {"beds": beds, "attached": attached, "baths": baths}


def _budget_note(k: int, b: Dict[str, int], auto: bool, total_beds: int = 0) -> str:
    if not (b["beds"] or b["baths"]):
        return ""
    parts = []
    if b["beds"]:
        parts.append(f"{b['beds']} bedroom(s) (the client asked for {total_beds} in the whole house - not more)" if total_beds else f"{b['beds']} bedroom(s)")
        parts[-1] += ((f", {b['attached']} of them with their OWN attached bath "
                       f"(bath door: that bedroom)") if b["attached"] else "")
    if b["baths"]:
        parts.append(f"at least {b['baths']} bath(s) in total")
    return (f"- ROOM BUDGET FOR LEVEL {k} (the engine counts it): " + "; ".join(parts) +
            (". The house total only adds up if this level holds them" if auto else "") + ".")


def _budget_problems(k: int, got: Dict[str, int], want: Dict[str, int]) -> List[str]:
    out = []
    if got["beds"] < want["beds"]:
        out.append(f"- [LEVEL_BUDGET] LEVEL {k} has {got['beds']} bedroom(s) but must hold {want['beds']}: add "
                   f"{want['beds'] - got['beds']} more (type bedroom, named BED ROOM n) - shrink the lounge / passages "
                   f"or re-slice the bands to make room")
    if got["attached"] < want["attached"]:
        out.append(f"- [LEVEL_BUDGET] LEVEL {k} has {got['attached']} bedroom(s) with their own bath but needs "
                   f"{want['attached']}: give {want['attached'] - got['attached']} more bedroom(s) a bath that touches "
                   f"it and is entered from it (door: that bedroom)")
    if got["baths"] < want["baths"]:
        out.append(f"- [LEVEL_BUDGET] LEVEL {k} has {got['baths']} bath(s) but must hold {want['baths']}")
    return out


_UPPER_VARIATIONS = [
    "the lounge / sitting area at the FRONT opening onto a front terrace or balcony; bedrooms in the middle and at the rear",
    "bedrooms at the FRONT with windows to a front balcony; the lounge in the MIDDLE beside the stair; a bedroom or terrace at the rear",
    "the lounge at the REAR opening onto a rear terrace; bedrooms at the front and in the middle",
]


def _upper_variation(level: int, i: int) -> str:
    v = _UPPER_VARIATIONS[(i + level) % len(_UPPER_VARIATIONS)]
    return (f"\n=== YOUR ARRANGEMENT FOR LEVEL {level} ===\nPlan this level with {v}. Other architects are trying the other "
            f"arrangements; the engine measures how much of this level repeats the level below and sends back a copy. "
            f"The stair, the OTS shafts and the rule that rooms stand over built rooms still hold - adapt the "
            f"arrangement to them.\n")


def _floor_similarity(geo: Dict[str, Any], level: int) -> float:
    """Share (0..1) of this level's room area that is the same kind of room in the same rectangle as on the level
    below (the stair and OTS, which must stack, are left out)."""
    by = {f.get("level"): f for f in geo.get("floors", []) if not f.get("roof")}
    up, down = by.get(level), by.get(level - 1)
    if not up or not down:
        return 0.0
    skip = ("stair", "ots")
    below = [(r.get("category"), float(r["x_ft"]), float(r["y_ft"]), float(r["w_ft"]), float(r["l_ft"]))
             for r in down.get("rooms", []) if r.get("category") not in skip]
    total = same = 0.0
    for r in up.get("rooms", []):
        if r.get("category") in skip or not is_enclosed(r.get("category")):
            continue
        box_ = (float(r["x_ft"]), float(r["y_ft"]), float(r["w_ft"]), float(r["l_ft"]))
        area = box_[2] * box_[3]
        total += area
        if any(c == r.get("category") and all(abs(a - b) <= 0.75 for a, b in zip(box_, o)) for c, *o in below):
            same += area
    return same / total if total else 0.0


GROUND_CANDIDATES = 4        # ground-floor designs asked for in parallel, each on its own layout concept
FRESH_STARTS = 2             # times a level is redesigned from scratch when its repairs do not converge
STAGE_ROUNDS = 3             # rounds per level when a house is designed level by level


def _split_levels(script: str) -> Tuple[List[str], List[Tuple[int, bool, str]], List[str]]:
    """Script -> (header lines, [(level number, is roof, block text)], '#' comment lines)."""
    header: List[str] = []
    comments: List[str] = []
    blocks: List[List[Any]] = []
    for line in (script or "").splitlines():
        s = line.strip()
        if s.startswith("#"):
            comments.append(s)
            continue
        m = re.match(r"LEVEL\s+(-?\d+)", s, re.I)
        if m:
            blocks.append([int(m.group(1)), bool(re.search(r"\bROOF\b", s, re.I)), [line]])
        elif blocks:
            blocks[-1][2].append(line)
        elif s:
            header.append(line)
    return header, [(n, roof, "\n".join(lines).rstrip()) for n, roof, lines in blocks], comments


def _stage_facts(geo: Dict[str, Any], level: int) -> List[str]:
    """What the level above must respect, measured on the level below (x from the left side, y from the street)."""
    fl = next((f for f in geo.get("floors", []) if f.get("level") == level), None)
    if not fl:
        return []
    out = []
    for s in [r for r in fl.get("rooms", []) if r.get("category") == "stair"][:1]:
        x0, y0 = float(s["x_ft"]), float(s["y_ft"])
        x1, y1 = x0 + float(s["w_ft"]), y0 + float(s["l_ft"])
        out.append(f"- The STAIR must occupy exactly x {x0:g} to {x1:g} ft and y {y0:g} to {y1:g} ft "
                   f"({float(s['w_ft']):g} x {float(s['l_ft']):g} ft), the same rectangle as on LEVEL {level}: keep a band "
                   f"from y {y0:g} to {y1:g} with columns that put the stair there.")
    opens = [r for r in fl.get("rooms", []) if r.get("category") in ("outdoor", "ots", "pool")]
    if opens:
        out.append("- Open below (no enclosed room may stand over it; a balcony / terrace / open space may): " + "; ".join(
            f"{r['name']} x {float(r['x_ft']):g}-{float(r['x_ft']) + float(r['w_ft']):g}, "
            f"y {float(r['y_ft']):g}-{float(r['y_ft']) + float(r['l_ft']):g}" for r in opens[:10]))
    return out


def _staged_synthesis(ctx: Dict[str, Any], api_key: Optional[str], style_label: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Designs a house of 2+ storeys one level at a time. Each level gets its own repair rounds (several designs in
    parallel, the engine keeps the best); the best level is then FIXED and the next level is designed on top of it.
    Ground-floor client items are checked while the ground floor is designed; the whole-house items at the end."""
    req = ctx["req"]
    n_levels = int(ctx["floors"])
    roof = bool(req.get("roof_terrace") or req.get("roof_garden") or (req.get("pool") or {}).get("location") == "roof")
    header = f"PLOT {ctx['W']:g} x {ctx['L']:g}\nSETBACKS front {ctx['front_sb']:g} rear {ctx['rear_sb']:g}"
    fixed: List[str] = []
    program: List[str] = []
    attempts: List[Dict[str, Any]] = []
    prev_geo: Dict[str, Any] = {}
    concepts = propose_concepts(ctx, api_key, max(1, GROUND_CANDIDATES))
    concept: Optional[Dict[str, Any]] = None      # the concept of the ground floor that won - upper levels follow it
    done = {"beds": 0, "attached": 0, "baths": 0}
    auto_budget = not req.get("beds_per_level")
    for k in range(n_levels):
        last = k == n_levels - 1
        budget = _level_budget(req, k, n_levels, done)
        budget_note = _budget_note(k, budget, auto_budget, int(req.get('bedrooms') or 0))
        if k == 0:
            note = (f"The house has {n_levels} storeys (LEVEL 0 to LEVEL {n_levels - 1})" + (" plus a ROOF level" if roof else "") +
                    ". NOW write ONLY LEVEL 0 (the ground floor).\nFirst write comment lines that give every client space a "
                    "level:\n" + "\n".join(f"# LEVEL {i}: <spaces on this level>" for i in range(n_levels)) +
                    ("\n# ROOF: <roof spaces>" if roof else "") +
                    "\nThe ground floor holds the STAIR going up, placed and entered as the brief says - it keeps this rectangle "
                    "on every level, so choose a place that also works upstairs." + ("\n" + budget_note if budget_note else ""))
        else:
            facts = _stage_facts(prev_geo, k - 1)
            note = (f"LEVEL 0 to LEVEL {k - 1} are fixed (shown above). NOW write ONLY LEVEL {k}" +
                    (" and then the ROOF level (write ROOF after its label; it holds the stair mumty in the same "
                     "rectangle plus the roof spaces)" if last and roof else "") + ".\n" +
                    ("Level plan you made: " + " | ".join(program) + "\n" if program else "") +
                    "\n".join(facts) + "\n" +
                    ("- The client wants the SAME layout on every floor: repeat the bands and columns of the level below and "
                     "change only what this level's rooms need." if req.get("same_layout") else
                     "- Plan this level for its OWN rooms - do NOT copy the floor below; only the stair position is fixed. "
                     "Put baths over baths or over the kitchen below where you can (plumbing).") +
                    "\n- This level is entered from the STAIR: give the upper lounge / lobby / corridor door: STAIR, and every "
                    "room a door to a space that is itself reachable." + ("\n" + budget_note if budget_note else ""))
        base = build_stage_prompt(ctx["brief"], req["checklist"], ctx["W"], ctx["L"], ctx["front_sb"], ctx["rear_sb"],
                                  note, header + "\n" + "\n".join(fixed) if fixed else "", ctx["size_notions"], style_label)
        # ground floor: one concept per parallel design; upper levels: the concept of the ground floor that won
        text: Any = ([base + _concept_text(c) for c in concepts] or base) if k == 0 else base + _concept_text(concept)
        used: List[Optional[Dict[str, Any]]] = list(concepts) if k == 0 else [concept] * SCRIPT_CANDIDATES_FIRST
        if k > 0 and not req.get("same_layout"):
            # upper levels: each parallel design gets its own arrangement, so the engine can keep one that both
            # passes and differs from the floor below
            text = [base + _concept_text(concept) + _upper_variation(k, i) for i in range(max(1, SCRIPT_CANDIDATES_FIRST))]
        stage: List[Dict[str, Any]] = []
        patch_src: Optional[str] = None         # set while a repair is asked for as line edits of this script
        for rnd in range(1, STAGE_ROUNDS + 2 + 2 * FRESH_STARTS):
            temps = [0.5, 0.65, 0.8][:max(1, SCRIPT_CANDIDATES_FIRST)] if rnd == 1 else \
                [0.2, 0.5, 0.75][:max(1, SCRIPT_CANDIDATES_REPAIR)]
            if rnd == 1 and k == 0:             # the ground floor decides the whole house: more ideas in parallel
                temps = [0.45, 0.6, 0.75, 0.9][:max(1, min(GROUND_CANDIDATES, len(concepts) or 1))]
            if rnd == STAGE_ROUNDS + 1:
                # one extra, careful round only for a level that is nearly right (1-3 things left): a small
                # fix is likely to land, while a level with many problems would not be saved by one more try
                top = min(stage, key=_attempt_rank)
                if not 0 < top["errors"] + top["unmet"] + top["quality"] <= 3:
                    continue                    # too far off for a small fix: go to the fresh start
                temps = [0.1, 0.3]
            elif rnd > STAGE_ROUNDS + 1 and (rnd - STAGE_ROUNDS) % 2 == 0:
                # FRESH START: the repairs did not converge, which means the skeleton itself is wrong (a small
                # change cannot move a courtyard). Design the level again on a different skeleton, knowing what
                # failed, then give that design one repair round.
                top = min(stage, key=_attempt_rank)
                if not top["errors"] + top["unmet"]:
                    break
                lesson = ("\n=== AN EARLIER DESIGN OF THIS LEVEL COULD NOT BE REPAIRED ===\n" + top["level_block"] +
                          "\nWhat the engine found in it:\n" + "\n".join(top["problems"][:8]) +
                          "\nDo NOT repair that script. Its skeleton caused these problems - start again from a "
                          "different, simpler skeleton in which they cannot happen: every room sits beside the shared "
                          "space it opens onto, and every bedroom / lounge / kitchen has one wall on open air.\n")
                if k == 0:
                    if rnd > STAGE_ROUNDS + 2:      # second fresh start: ask for new layout ideas altogether
                        try:
                            concepts = concepts + propose_concepts(ctx, api_key, 2)
                        except Exception as e_c:
                            print(f"[Concepts] second proposal failed: {e_c}")
                    tried = {id(a.get("concept")) for a in stage}
                    fresh = ([c for c in concepts if id(c) not in tried] or
                             [c for c in concepts if c is not top.get("concept")])[:2] or [top.get("concept")]
                    text = [base + _concept_text(c) + lesson for c in fresh]
                    used = list(fresh)
                else:
                    text = [base + _concept_text(concept) + (_upper_variation(k, i + 1) if not req.get("same_layout") else "")
                            + lesson for i in range(2)]
                    used = [concept, concept]
                temps = [0.4, 0.7][:len(text)]
                patch_src = None
                print(f"[Gemini levels] level {k}: repairs did not converge ({top['errors']} errors) - fresh start")
            answers = _parallel_scripts(text, api_key, temps)
            good = [(a, used[i] if i < len(used) else None) for i, a in enumerate(answers) if not isinstance(a, Exception)]
            if not good:
                if stage or attempts:
                    print(f"[Gemini levels] level {k} round {rnd} failed: {answers[0]}")
                    break
                raise answers[0]
            cands = []
            for (ans, model), cand_concept in good:
                script = _answer_script(ans, patch_src)
                _, blocks, comments = _split_levels(script)
                mine = [b for b in blocks if b[0] == k and not b[1]]
                roofs = [b for b in blocks if b[1]] if last and roof else []
                block = "\n".join(([mine[0][2]] if mine else []) + ([roofs[-1][2]] if roofs else []))
                scope = {k} | {b[0] for b in roofs[-1:]}
                c = _evaluate_script(header + "\n" + "\n".join(fixed + [block]), ctx, rnd, "gemini", model,
                                     scope=scope, req_level=k, req_whole=last)
                if not mine:
                    c["errors"] += 1
                    c["problems"].insert(0, f"- [LEVEL_MISSING] write LEVEL {k} - it is the level asked for in this step")
                if k == 0 and not any(r.get("category") == "stair" for f in c["geo"].get("floors", [])
                                      if f.get("level") == 0 for r in f.get("rooms", [])):
                    c["errors"] += 1
                    c["problems"].insert(0, "- [STAIR_MISSING] LEVEL 0 needs the STAIR that goes up to the next level")
                _, nblocks, _ = _split_levels(c["script"])      # keep the engine's normalised sizes
                c["level_block"] = "\n".join(b[2] for b in nblocks if b[0] in scope) or block
                c["program"] = [x.lstrip("# ").strip() for x in comments if re.match(r"#\s*(LEVEL|ROOF)", x, re.I)]
                c["stage"] = k
                c["concept"] = cand_concept
                # the room budget of this level (so the house total adds up while the level can still be changed)
                c["program_built"] = _level_program(c["geo"], k)
                short = _budget_problems(k, c["program_built"], budget) if mine else []
                if short:
                    c["problems"] += short
                    if not last:                # on the last level the whole-house counts already report it
                        c["unmet"] += len(short)
                # a floor that repeats the floor below (the client did not ask for identical floors)
                c["similarity"] = _floor_similarity(c["geo"], k) if k > 0 else 0.0
                if c["similarity"] > COPY_LIMIT and not req.get("same_layout"):
                    c["quality"] += 1
                    c["problems"].append(
                        f"- [COPIED_FLOOR] LEVEL {k} repeats LEVEL {k - 1}: {c['similarity'] * 100:.0f}% of its rooms are the "
                        f"same room in the same place. The client did not ask for identical floors - re-plan this level "
                        f"(only the STAIR and any OTS stay put): move the lounge, turn or regroup the bedrooms, change the "
                        f"band depths, use a terrace / balcony where the level below has a room it does not need")
                cands.append(c)
            cand = min(cands, key=_attempt_rank)
            cand["candidates"] = len(cands)
            stage.append(cand)
            print(f"[Gemini levels] level {k} round {rnd}: best of {len(cands)} -> {cand['errors']} errors, "
                  f"{cand['unmet']} unmet, {cand['quality']} furniture (others: {[c['errors'] for c in cands if c is not cand]})")
            if not cand["errors"] and not cand["unmet"] and not cand["quality"]:
                break
            top = min(stage, key=_attempt_rank)
            shown = {k - 1, k} | {f.get("level") for f in top["geo"].get("floors", []) if f.get("roof")}
            used = [top.get("concept")] * SCRIPT_CANDIDATES_REPAIR
            text, patch_src = _repair_text(
                base + _concept_text(top.get("concept")), top, ctx, rnd, header + "\n" + top["level_block"],
                _ascii_map(top["geo"], shown), top["notes"][:6],
                eval_kwargs={"scope": {k} | {f.get("level") for f in top["geo"].get("floors", []) if f.get("roof")},
                             "req_level": k, "req_whole": last}, only_level=k)
            if patch_src:
                print(f"[Gemini levels] level {k}: {top['errors'] + top['unmet'] + top['quality']} problem(s) left - "
                      f"asking for line edits")
        best = min(stage, key=_attempt_rank)
        if k == 0:
            concept = best.get("concept")
        built = best.get("program_built") or _level_program(best["geo"], k)
        done = {key: done[key] + built[key] for key in done}
        print(f"[Gemini levels] level {k} fixed: {built} (budget {budget}), copy {best.get('similarity', 0) * 100:.0f}%"
              + (f", concept '{concept['name']}'" if concept and k == 0 else ""))
        for a in stage:
            a["round"] = len(attempts) + 1
            attempts.append(a)
        fixed.append(best["level_block"])
        program = program or best["program"]
        prev_geo = best["geo"]
    final = _evaluate_script(header + "\n" + "\n".join(fixed), ctx, len(attempts) + 1, "gemini",
                             attempts[-1]["model"] if attempts else None)
    final["levels_designed"] = n_levels
    final["level_plan"] = program
    final["concept"] = concept
    final["concepts_tried"] = [c["name"] for c in concepts]
    final["floor_similarity"] = {str(lv): round(_floor_similarity(final["geo"], lv), 2) for lv in range(1, n_levels)}
    return final, attempts


def _parallel_scripts(text: Any, api_key: Optional[str], temps: List[float]) -> List[Any]:
    """Asks Gemini for len(temps) scripts at once. `text` is one prompt for all, or a list with one prompt per
    candidate (each with its own layout concept). Returns (answer, model) tuples, or the exception of a failed call."""
    texts = list(text) if isinstance(text, (list, tuple)) else [text] * len(temps)
    temps = temps[:len(texts)]
    if len(temps) == 1:
        try:
            return [call_gemini_text(texts[0], api_key, temperature=temps[0])]
        except Exception as e:
            return [e]
    out: List[Any] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(temps)) as pool:
        futs = [pool.submit(call_gemini_text, tx, api_key, t) for tx, t in zip(texts, temps)]
        for f in futs:
            try:
                out.append(f.result())
            except Exception as e:
                out.append(e)
    return out


PATCH_MAX_PROBLEMS = 3        # with this many problems or fewer left, the repair is asked for as LINE EDITS


def _numbered(script: str) -> str:
    return "\n".join(f"{i:>3}| {ln}" for i, ln in enumerate(script.split("\n"), 1))


def apply_line_edits(script: str, answer: str) -> Optional[str]:
    """Applies REPLACE n: / INSERT AFTER n: / DELETE n edits (line numbers of `script`) and returns the new script,
    or None when the answer holds no edit. Indentation carries the nesting of a script, so an edit written
    without indentation takes the indentation of the line it replaces / follows."""
    lines = script.split("\n")
    ops: List[Tuple[str, int, str]] = []
    for raw in (answer or "").replace("\r\n", "\n").split("\n"):
        m = re.match(r"\s*[-*]?\s*(REPLACE|INSERT AFTER|DELETE)\s+(?:LINE\s+)?(\d+)\s*:?[ ]?(.*)$", raw, re.I)
        if not m:
            continue
        n = int(m.group(2))
        if not 1 <= n <= len(lines):
            continue
        txt = re.sub(r"^\s*\d+\|\s?", lambda mm: " " * 0, m.group(3).rstrip()) if re.match(r"^\s*\d+\|", m.group(3)) else m.group(3).rstrip()
        txt = txt.strip("`")
        op = m.group(1).upper()
        if op != "DELETE":
            if not txt.strip():
                continue
            if txt == txt.lstrip():             # no indentation given: keep the nesting of the line it belongs to
                ref = lines[n - 1]
                txt = ref[:len(ref) - len(ref.lstrip())] + txt
        ops.append((op, n, txt))
    if not ops:
        return None
    replaced: Dict[int, str] = {}
    deleted = set()
    inserts: Dict[int, List[str]] = {}
    for op, n, txt in ops:
        if op == "REPLACE":
            replaced[n] = txt
        elif op == "DELETE":
            deleted.add(n)
        else:
            inserts.setdefault(n, []).append(txt)
    out: List[str] = []
    for i, ln in enumerate(lines, 1):
        if i not in deleted:
            out.append(replaced.get(i, ln))
        out.extend(inserts.get(i, []))
    return "\n".join(out)


def _patch_prompt(base_prompt: str, script: str, problems: List[str], picture: str = "",
                  only_level: Optional[int] = None) -> str:
    scope = (f"Only the lines of LEVEL {only_level} may change - the levels below are built and fixed.\n"
             if only_level is not None and only_level > 0 else "")
    seen = (f"=== WHAT THE SCRIPT BUILT (letters = rooms; a door needs two rooms side by side along at least 3 ft) ===\n"
            f"{picture}\n") if picture else ""
    return f"""{base_prompt}

=== SMALL REPAIR BY LINE EDITS ===
Your script below is nearly right: only the problems listed remain. Do NOT write the script again - every rewrite so
far broke rooms that were working. Give ONLY the line edits that fix these problems; every other line stays exactly
as it is.
{scope}
=== YOUR SCRIPT, WITH LINE NUMBERS ===
{_numbered(script)}

{seen}=== PROBLEMS LEFT (fix all of them) ===
{chr(10).join(problems)}

Before you answer, find for each problem the wall it is about (use the x-ranges of the two bands) and the smallest
edit that fixes it: a different door: target that really touches, an `extra door:` on a neighbour, a size number
changed in ONE ROWS / COLS group (then its neighbours in that group change too, so the group still adds up), a room
swapped with its neighbour, or one leaf added / removed.

Answer with edits only, one per line, in exactly this form (the text after the colon is the complete new line,
with the same indentation as the line it replaces):
REPLACE <line number>: <new line>
INSERT AFTER <line number>: <new line>
DELETE <line number>
"""


def _answer_script(answer: str, patch_src: Optional[str]) -> str:
    """The script an answer stands for: the edited script when line edits were asked for, else the fenced script."""
    if patch_src:
        edited = apply_line_edits(patch_src, answer)
        if edited:
            return edited
    return extract_script(answer)[0]


def _repair_text(base_prompt: str, top: Dict[str, Any], ctx: Dict[str, Any], rnd: int, shown_script: str,
                 picture: str, notes: List[str], eval_kwargs: Optional[Dict[str, Any]] = None,
                 only_level: Optional[int] = None) -> Tuple[str, Optional[str]]:
    """The next repair prompt for the best script so far: line edits when only a few problems are left (returns the
    script the line numbers refer to), a full repair otherwise (returns None)."""
    left = top["errors"] + top["unmet"] + top["quality"]
    if 0 < left <= PATCH_MAX_PROBLEMS:
        src = top["script"]
        try:    # line numbers must be those of the listing shown, so the script is measured once more as shown
            pv = _evaluate_script(src, ctx, rnd, "gemini", top.get("model"), **(eval_kwargs or {}))
            probs = pv["problems"] + [q for q in top["problems"]
                                      if not re.search(r"\bline \d+", q) and q not in pv["problems"]]
        except Exception:
            probs = top["problems"]
        if probs:
            return _patch_prompt(base_prompt, src, probs, picture, only_level), src
    return build_script_repair_prompt(base_prompt, shown_script, top["problems"], notes, picture=picture), None


def _improve_from_review(ctx: Dict[str, Any], best: Dict[str, Any], base_prompt: str,
                         api_key: Optional[str]) -> Dict[str, Any]:
    """The LLM reviews its finished design as the family's architect; when it has concerns of its own, it gets one
    round to answer them. The improved design is kept only if the engine still finds no problem in it, no
    furniture was lost, no floor became a copy, and the LLM's own second review does not score it lower."""
    if not ARCHITECT_REVIEW:
        return best
    review = architect_review(ctx, best)
    best["review"] = review
    if best["errors"] or best["unmet"] or not review:
        return best
    if int(review.get("score") or 0) >= 8 or not (review.get("concerns") or review.get("suggestions")):
        return best
    try:
        prompt = base_prompt + _concept_text(best.get("concept")) + f"""
=== YOUR OWN REVIEW OF YOUR DESIGN ===
The script below passed every physical check of the engine. Then you looked at it as the family's architect and said:
{review.get('verdict', '')}
Your concerns:
{chr(10).join('- ' + c for c in review.get('concerns', []))}
Your ideas:
{chr(10).join('- ' + c for c in review.get('suggestions', []))}

=== THE SCRIPT, WITH LINE NUMBERS ===
{_numbered(best['script'])}

=== WHAT THE SCRIPT BUILT (letters = rooms) ===
{_ascii_map(best['geo'])}

Improve the design so that it answers the most important of your own concerns, as far as the client's brief and
this plot allow. Do NOT write the script again - a rewrite breaks rooms that work. Give LINE EDITS only (at most
12): move a cut by changing size numbers inside ONE ROWS / COLS group (the group must still add up), swap two
neighbours, re-target a door, rename or re-type a space. Keep every client item and every count the brief gives
(do not remove a bedroom or bath the client asked for); keep the STAIR in the same rectangle on every level.
The engine will run the result: a version that breaks a door, a walking route, daylight or loses furniture is
thrown away, so prefer two safe edits to six risky ones.

Answer with edits only, one per line, in exactly this form (the text after the colon is the complete new line,
with the same indentation as the line it replaces):
REPLACE <line number>: <new line>
INSERT AFTER <line number>: <new line>
DELETE <line number>
"""
        answers = _parallel_scripts(prompt, api_key, [0.3, 0.6])
        ok = []
        for a in answers:
            if isinstance(a, Exception):
                continue
            edited = apply_line_edits(best["script"], a[0])
            if not edited or edited == best["script"]:
                continue
            c = _evaluate_script(edited, ctx, int(best.get("round") or 0) + 1, "gemini", a[1])
            n_lv = len([f for f in c["geo"].get("floors", []) if not f.get("roof")])
            sims = {str(lv): round(_floor_similarity(c["geo"], lv), 2) for lv in range(1, n_lv)}
            copied = (not ctx["req"].get("same_layout")) and any(v > COPY_LIMIT for v in sims.values())
            if c["errors"] or c["unmet"] or c["quality"] > best["quality"] or copied:
                continue
            c["floor_similarity"] = sims
            ok.append(c)
        print(f"[Architect review] score {review.get('score')} - {len(ok)} improved design(s) passed the engine")
        if not ok:
            return best
        cand = min(ok, key=_attempt_rank)
        second = architect_review(ctx, cand)
        if not second or int(second.get("score") or 0) < int(review.get("score") or 0):
            return best
        for key in ("concept", "levels_designed", "level_plan", "concepts_tried"):
            if key in best:
                cand[key] = best[key]
        cand["review"] = second
        cand["review_before"] = review
        cand["improved_after_review"] = True
        print(f"[Architect review] improved design kept: own score {review.get('score')} -> {second.get('score')}")
        return cand
    except Exception as e:
        print(f"[Architect review] improvement skipped: {str(e)[:160]}")
        return best


def _attempt_rank(a: Dict[str, Any]) -> Tuple:
    return (a["errors"], a["unmet"], a["quality"], a["major_notes"], len(a["notes"]), -a["round"])


def _call_interview_llm_json(interview_prompt: str, api_key: Optional[str] = None) -> Optional[str]:
    """Calls Gemini to get the AI Civil Architect's next conversational interview turn in JSON."""
    key = (api_key or GeminiConfig.get_api_key() or "").strip()
    if not key or len(key) < 12:
        return None
    client = genai.Client(api_key=key, http_options=types.HttpOptions(api_version="v1beta"))
    for model_name in REQUIREMENT_MODELS:
        try:
            thinking = None
            if model_name.startswith("gemini-3") and "lite" not in model_name:
                thinking = types.ThinkingConfig(thinking_level="LOW")
            elif model_name.startswith("gemini-2.5-flash") and "lite" not in model_name:
                thinking = types.ThinkingConfig(thinking_budget=0)
            cfg = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.35,
                                              max_output_tokens=4096, thinking_config=thinking)
            resp = client.models.generate_content(model=model_name, contents=interview_prompt, config=cfg)
            raw = (resp.text or "").strip()
            if raw:
                return raw
        except Exception as e:
            print(f"[Gemini interview] {model_name} failed: {str(e)[:160]}")
    return None


def interview_brief(prompt: str, answers: Optional[Dict[str, str]] = None, skipped: Optional[List[str]] = None,
                    history: Optional[List[Dict[str, str]]] = None, message: Optional[str] = None,
                    api_key: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Text-based AI Civil Architect interview turn: conducts a conversational interview using Gemini LLM."""
    from generation.brief_interview import conduct_architect_interview
    res = conduct_architect_interview(
        prompt=prompt,
        history=history,
        answers=answers if isinstance(answers, dict) else None,
        skipped=skipped if isinstance(skipped, list) else None,
        message=message,
        llm_call_fn=lambda p: _call_interview_llm_json(p, api_key=api_key),
    )
    res["success"] = True
    return res


def read_brief(prompt: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Everything the design is built from, read from the prompt alone: plot, storeys, setbacks, style and the
    client's items (rules + Gemini's evidence-checked reading). Nothing is taken from form defaults."""
    brief = (prompt or "").strip()
    site = read_site(brief)
    llm = extract_requirements_llm(brief, api_key) if brief else {}
    site = merge_llm_site(site, llm, brief)
    W, L = site.get("width_ft"), site.get("length_ft")
    floors = int(site.get("storeys") or 0)
    req = parse_brief(brief, W or 0, L or 0, floors, 0, 0)
    req = merge_llm_requirements(req, llm, 0, 0, floors)
    portion = req.get("portion") or {}
    if portion.get("kind") == "upper":
        floors = 1                      # one level is designed: the portion
    req["checklist"] = build_checklist(req, 0, 0, floors)
    setbacks = {"front": site.get("front_setback_ft"), "rear": site.get("rear_setback_ft")}
    eff = {k: (float(setbacks[k]) if setbacks[k] is not None else 0.0) for k in ("front", "rear")}
    not_stated = []
    if not floors:
        not_stated.append("Number of storeys - the architect will use as few levels as fit your brief")
    if not site.get("style"):
        not_stated.append("Style - a modern contemporary elevation is drawn unless you name a style")
    if not (req.get("bedrooms") or req.get("bathrooms")):
        not_stated.append("Bedroom / bathroom counts - the architect decides from the rest of your brief")
    return {
        "success": True, "prompt": brief, "ok": bool(W and L),
        "plot": {"width_ft": W, "length_ft": L, "source": site.get("plot_source"), "quote": site.get("plot_quote"),
                 "marla": site.get("marla") or (round(W * L / 225.0, 1) if W and L else None)},
        "storeys": floors or None, "storeys_quote": site.get("storeys_quote"),
        "portion": portion or None,
        "setbacks": {"front_ft": eff["front"], "rear_ft": eff["rear"],
                     "front_source": "prompt" if setbacks["front"] is not None else "architect_decides",
                     "rear_source": "prompt" if setbacks["rear"] is not None else "architect_decides",
                     "stated": {k: v for k, v in setbacks.items() if v is not None}},
        "style": site.get("style"), "bedrooms": req.get("bedrooms") or None, "bathrooms": req.get("bathrooms") or None,
        "understood_as": req.get("understood_as"), "checklist": req.get("checklist", []),
        "notes": req.get("notes", []), "assumptions": site.get("assumptions", []), "missing": site.get("missing", []),
        "not_stated": not_stated, "read_by": ("rules + " + str(llm.get("_model"))) if llm else "rules",
        "requirements": {k: v for k, v in req.items() if k not in ("llm_reading",)},
    }


def synthesize_from_prompt(prompt: str, api_key: Optional[str] = None, reading: Optional[Dict[str, Any]] = None,
                           budget_tier: str = "balanced", **kwargs) -> Dict[str, Any]:
    """The prompt is the only input: plot, storeys, setbacks, style and every room come from it. Raises ValueError
    with a plain message when the prompt does not give the plot size."""
    if not reading or not reading.get("ok") or (reading.get("prompt") or "").strip() != (prompt or "").strip():
        reading = read_brief(prompt, api_key)
    if not reading.get("ok"):
        raise ValueError("Your prompt does not say the plot size. " + " ".join(reading.get("missing", [])))
    req = reading.get("requirements")
    res = synthesize_design(prompt, plot_width=float(reading["plot"]["width_ft"]),
                            plot_length=float(reading["plot"]["length_ft"]), floors=int(reading.get("storeys") or 0),
                            bedrooms=int(reading.get("bedrooms") or 0), bathrooms=int(reading.get("bathrooms") or 0),
                            style=reading.get("style") or "Modern Contemporary", api_key=api_key,
                            budget_tier=budget_tier, custom_room_dimensions=[], requirements=req,
                            setbacks=reading.get("setbacks", {}).get("stated"),
                            style_label=reading.get("style") or "as the brief describes")
    res["reading"] = {k: v for k, v in reading.items() if k != "requirements"}
    res["input_mode"] = "prompt_only"
    if isinstance(res.get("requirements"), dict):
        res["requirements"]["read_by"] = reading.get("read_by", res["requirements"].get("read_by"))
    return res


def run_design_script(script: str, prompt: str = "", plot_width: float = 35.0, plot_length: float = 65.0,
                      floors: int = 1, bedrooms: int = 3, bathrooms: int = 3, style: str = "Modern Contemporary",
                      requirements: Optional[Dict[str, Any]] = None, api_key: Optional[str] = None,
                      **kwargs) -> Dict[str, Any]:
    """Runs a script the client edited (no AI call unless the brief has not been read yet)."""
    ctx = prepare_design_context(prompt, plot_width, plot_length, floors, bedrooms, bathrooms, style, api_key,
                                 kwargs.get("custom_room_dimensions"), requirements)
    cand = _evaluate_script(script, ctx, 0, "client_edit", None, enforce_setbacks=False)
    return _design_response(cand, [cand], ctx, style, mode="run")


def converse_design_script(script: str, message: str, prompt: str = "", history: Optional[List[Dict[str, str]]] = None,
                           plot_width: float = 35.0, plot_length: float = 65.0, floors: int = 1, bedrooms: int = 3,
                           bathrooms: int = 3, style: str = "Modern Contemporary",
                           requirements: Optional[Dict[str, Any]] = None, api_key: Optional[str] = None,
                           **kwargs) -> Dict[str, Any]:
    """The client asks for a change in plain words; Gemini edits the script, the engine tests it and one
    automatic repair round fixes anything the change broke."""
    ctx = prepare_design_context(prompt, plot_width, plot_length, floors, bedrooms, bathrooms, style, api_key,
                                 kwargs.get("custom_room_dimensions"), requirements)
    ctx["req"] = apply_message_to_requirements(ctx["req"], message, bedrooms, bathrooms, floors)
    ctx["bedrooms"], ctx["bathrooms"] = ctx["req"]["bedrooms"], ctx["req"]["bathrooms"]
    current = _evaluate_script(script, ctx, 0, "current", None, enforce_setbacks=False)
    base = build_converse_prompt(ctx["brief"], ctx["req"]["checklist"], current["script"], message, history or [],
                                 ctx["W"], ctx["L"], current["front_sb"], current["rear_sb"],
                                 problems=current["problems"][:15] if current["errors"] else None,
                                 rag_context=ctx.get("rag_context", ""))
    attempts: List[Dict[str, Any]] = []
    reply = ""
    text = base
    patch_src: Optional[str] = None
    for rnd in range(1, MAX_CONVERSE_ROUNDS + 1):
        answer, model = call_gemini_text(text, api_key, temperature=0.25)
        if patch_src:                           # a repair asked for as line edits of the changed script
            new_script, notes = _answer_script(answer, patch_src), ""
        else:
            new_script, notes = extract_script(answer)
        if rnd == 1:
            reply = notes
        cand = _evaluate_script(new_script, ctx, rnd, "conversation", model, enforce_setbacks=False)
        attempts.append(cand)
        cand["lost"] = _lost_furniture(cand, current)
        print(f"[Gemini converse] round {rnd}: {cand['errors']} errors, {cand['unmet']} unmet, "
              f"{len(cand['lost'])} furniture lost")
        if not cand["errors"] and cand["unmet"] <= current["unmet"] and cand["quality"] <= current["quality"]:
            break
        problems = cand["problems"] + [f"- [FURNITURE_LOST_BY_CHANGE] the {m['item']} in {m['name']} fitted in the "
                                       f"client's current design - keep that room big enough for it" for m in cand["lost"]]
        # what the change broke is repaired on the best changed script so far - by line edits when little is left
        top = min(attempts, key=lambda a: (a["errors"], a["unmet"], len(a["lost"]), a["quality"], -a["round"]))
        if top is cand and 0 < len(problems) <= PATCH_MAX_PROBLEMS:
            patch_src = cand["script"]
            text = _patch_prompt(base, patch_src, problems, _ascii_map(cand["geo"]))
        else:
            patch_src = None
            text = build_script_repair_prompt(base, top["script"], top["problems"] if top is not cand else problems)
    best = min(attempts, key=lambda a: (a["errors"], a["unmet"], len(a["lost"]), a["quality"], -a["round"]))
    # Keep all physical CAD checks and balances intact: reject ONLY if the edit broke physical CAD rules
    # (more errors than before) or dropped essential furniture in a room that still exists.
    # Never block intentional room deletions/cuts or rebalances requested by the client.
    if best["errors"] > current["errors"] or best["lost"]:
        current["round"], current["source"], current["model"] = 0, "kept_previous", None
        current["lost"] = []
        res = _design_response(current, attempts + [current], ctx, style, mode="converse")
        if best["errors"] > current["errors"]:
            why = "it would break physical CAD checks (" + "; ".join(p.lstrip("- ")[:140] for p in best["problems"][:3]) + ")"
        else:
            why = "it would no longer fit " + ", ".join(f"the {m['item']} in {m['name']}" for m in best["lost"])
        res["assistant_message"] = ((reply + " ") if reply else "") + \
            f"I could not make that change cleanly because {why}, so I kept your current plan. " \
            f"Try specifying which adjacent room to trim or remove to make space."
        res["proposed_script"] = best["script"]
        res["change_applied"] = False
        res["design_source"] = "previous_design_kept"
        return res
    changes = _script_changes(current["script"], best["script"])
    if not changes:
        # the model answered but changed nothing: say so instead of presenting the old plan as a new version
        current["round"], current["source"], current["model"] = 0, "kept_previous", None
        current["lost"] = []
        res = _design_response(current, attempts + [current], ctx, style, mode="converse")
        res["assistant_message"] = ((reply + " ") if reply else "") + \
            "Nothing in the plan was changed by that request. Say what should change and where " \
            "(for example: 'make BED ROOM 2 3 ft wider and take the width from the lounge')."
        res["change_applied"] = False
        res["changes"] = []
        res["design_source"] = "previous_design_kept"
        return res
    res = _design_response(best, attempts, ctx, style, mode="converse")
    msg = reply or "I updated the script."
    if best["errors"]:
        msg += f" The engine still reports {best['errors']} problem(s) - they are listed under the script."
    res["assistant_message"] = msg
    res["change_applied"] = True
    res["changes"] = changes
    return res


def _script_changes(old: str, new: str) -> List[str]:
    """What a change request really changed, as short '- old line' / '+ new line' entries (empty = nothing)."""
    import difflib
    a = [ln.rstrip() for ln in (old or "").split("\n") if ln.strip()]
    b = [ln.rstrip() for ln in (new or "").split("\n") if ln.strip()]
    out: List[str] = []
    for ln in difflib.unified_diff(a, b, lineterm="", n=0):
        if ln.startswith(("---", "+++", "@@")):
            continue
        out.append(("- " if ln.startswith("-") else "+ ") + ln[1:].strip())
    return out[:60]


ARCHITECT_REVIEW = True       # after a design is made, the LLM reviews it itself (its own opinion, no rule list)


def architect_review(ctx: Dict[str, Any], best: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The LLM looks at the finished design - the script, the map the engine drew and what the engine measured -
    and gives its OWN review as an architect who builds homes in Pakistan. No bylaws or rule lists are supplied."""
    try:
        v = best["geo"].get("validation", {})
        found = [f"- [{e['code']}] {e['message']}" for e in v.get("errors", [])][:12]
        missing = [f"- {w['message']}" for w in v.get("warnings", []) if w["code"] == "FURNITURE_UNPLACED"][:8]
        rooms = []
        for fl in best["geo"].get("floors", []):
            for r in fl.get("rooms", []):
                rooms.append(f"L{fl.get('level')} {r['name']}: {float(r['w_ft']):g} x {float(r['l_ft']):g} ft")
        prompt = f"""You are a senior residential architect who designs and builds family homes in Pakistan.
Below is a house design made for a client. Review it yourself, from your own knowledge of how homes are built and
lived in in Pakistan. No bylaws are given to you and none should be cited - this is your professional opinion.

CLIENT BRIEF: "{ctx['brief'].strip()}"
PLOT: {ctx['W']:g} x {ctx['L']:g} ft ({ctx.get('marla_label', '')}), {ctx['floors']} storey(s). The street is at the bottom of the map (y = 0).

DESIGN SCRIPT (ROWS = bands from the street to the back, COLS = left to right, numbers in feet):
{best['script']}

MAP THE CAD ENGINE DREW (letters = rooms):
{_ascii_map(best['geo'])}

ROOM SIZES:
{chr(10).join(rooms[:90])}

WHAT THE CAD ENGINE MEASURED (physical checks only: walking routes, daylight, doors, stair, furniture):
{chr(10).join(found) if found else '- no physical problem found'}
{('Furniture that did not fit:' + chr(10) + chr(10).join(missing)) if missing else ''}

Think about: where guests are received and whether the family keeps its privacy; the drawing room, lounge, kitchen,
baths and stair - where they sit and how they connect; room sizes for this plot and this family; daylight and
cross-ventilation in a hot climate; the car porch and entrance; terraces and wash area; how the house faces the street.

Return ONLY JSON:
{{"verdict": "<one or two plain sentences>", "score": <1-10>,
  "strengths": ["<up to 5, each names the room or feature>"],
  "concerns": ["<up to 6, each names the room and says why it matters to the family>"],
  "suggestions": ["<up to 5 concrete changes the client could ask for>"]}}"""
        raw = _call_interview_llm_json(prompt)
        if not raw:
            return None
        data = json.loads(re.sub(r"^```[a-z]*|```$", "", raw.strip(), flags=re.M).strip())
        if not isinstance(data, dict):
            return None
        out = {"verdict": str(data.get("verdict", ""))[:600],
               "score": max(1, min(10, int(float(data.get("score", 0) or 0)))) if data.get("score") is not None else None,
               "source": "the designing LLM's own opinion - not a bylaw check and not a professional certificate"}
        for k, n in (("strengths", 5), ("concerns", 6), ("suggestions", 5)):
            out[k] = [str(x)[:400] for x in (data.get(k) or []) if str(x).strip()][:n]
        return out
    except Exception as e:
        print(f"[Architect review] skipped: {str(e)[:160]}")
        return None


def _design_response(best: Dict[str, Any], attempts: List[Dict[str, Any]], ctx: Dict[str, Any], style: str,
                     mode: str) -> Dict[str, Any]:
    req = ctx["req"]
    plot_width, plot_length = ctx["W"], ctx["L"]
    marla_label = ctx["marla_label"]
    front_sb, rear_sb = best["front_sb"], best["rear_sb"]
    design_source = {"generate": "ai_script", "run": "client_edited_script", "converse": "ai_script_conversation"}[mode]
    layout_data = best["geo"]
    model_used = best["model"] or next((a["model"] for a in attempts if a.get("model")), None) or "none (client script)"
    layout_data["design_source"] = design_source
    layout_data["_model_used"] = model_used
    layout_data["total_floors"] = sum(1 for f in layout_data["floors"] if not f.get("roof")) or 1
    has_roof_level = any(f.get("roof") for f in layout_data["floors"])
    layout_data["marla_size"] = marla_label
    layout_data["design_script"] = best["script"]
    layout_data["elevation_features"] = _derive_elevation_features(layout_data)
    validation = layout_data["validation"]

    pkg = render_design_package(layout_data, style)
    pid, proj_dir, images = pkg["project_id"], pkg["proj_dir"], pkg["images"]
    with open(os.path.join(proj_dir, "design.archi"), "w", encoding="utf-8") as f_s:
        f_s.write(best["script"] + "\n")
    with open(os.path.join(proj_dir, "layout_ai.json"), "w", encoding="utf-8") as f_json:
        json.dump([{k: a[k] for k in ("round", "source", "model", "errors", "warnings", "unmet", "problems",
                                       "requirements", "script")} for a in attempts], f_json, indent=2)
    with open(os.path.join(proj_dir, "layout_geometry.json"), "w", encoding="utf-8") as f_geo:
        json.dump(layout_data, f_geo, indent=2)

    three_d_nodes = massing_render.three_d_nodes(layout_data)

    total_covered_sqft = 0
    room_schedule = []
    floors_summary = []
    for fi, floor in enumerate(layout_data["floors"]):
        fl_sqft = 0
        fl_rooms = []
        for r in floor.get("rooms", []):
            cat = _classify_room(r)
            rw = float(r.get("w_ft", 12))
            rl = float(r.get("l_ft", 14))
            sqft = round(rw * rl)
            if cat not in ("outdoor", "ots", "pool"):
                total_covered_sqft += sqft
                fl_sqft += sqft
            rm_entry = {
                "id": r.get("id", uuid.uuid4().hex[:6]), "name": r.get("name", "Room"), "type": r.get("type", cat),
                "category": cat, "floor": floor.get("label", f"Floor {fi}"), "level": fi,
                "x_ft": float(r.get("x_ft", 0)), "y_ft": float(r.get("y_ft", 0)), "widthFt": rw, "lengthFt": rl,
                "dimensions_ft": f"{_ft_in_str(rw)} × {_ft_in_str(rl)}", "area_sqft": sqft,
                "door": r.get("door"), "windows": r.get("windows", []), "furniture": r.get("furniture", []),
                "furniture_layout": r.get("furniture_layout", []),
                # the same rectangle under the names the DXF / SVG / PDF exporters read
                "x": float(r.get("x_ft", 0)), "y": float(r.get("y_ft", 0)), "width": rw, "length": rl,
            }
            room_schedule.append(rm_entry)
            fl_rooms.append(rm_entry)
        floors_summary.append({
            "level": fi, "name": floor.get("label", f"Floor {fi}"), "covered_sqft": fl_sqft, "rooms": fl_rooms,
            "is_roof_level": bool(floor.get("roof")),
            "doors": len(floor.get("doors", [])), "windows": len(floor.get("windows", [])),
        })

    grey_rate, finish_rate = 3400, 3100
    grey_cost = int(total_covered_sqft * grey_rate)
    finish_cost = int(total_covered_sqft * finish_rate)
    total_cost = grey_cost + finish_cost
    cost_estimate = {
        "covered_area_sqft": total_covered_sqft, "total_cost_pkr": total_cost, "grand_total": total_cost,
        "grey_structure_pkr": grey_cost, "grey_cost": grey_cost, "finishing_pkr": finish_cost,
        "finishing_cost": finish_cost, "cement_bags": int(total_covered_sqft * 0.45),
        "steel_ton": round(total_covered_sqft * 0.004, 2), "burnt_clay_bricks": int(total_covered_sqft * 28),
        "sand_cft": int(total_covered_sqft * 1.8), "crush_cft": int(total_covered_sqft * 1.4), "currency": "PKR",
        "benchmark": "Verified 2026 Pakistan Construction Rates",
    }

    n_err = len(validation["errors"])
    rounds = [{"round": a["round"], "source": a["source"], "model": a["model"], "errors": a["errors"],
               "warnings": a["warnings"], "unmet": a["unmet"], "problems": a["problems"][:25],
               "level": a.get("stage"), "candidates": a.get("candidates", 1)} for a in attempts]
    requirement_notes = list(req.get("notes", []))
    quality_gate = {
        "status": validation["status"], "score": validation["score"], "source": validation["engine"],
        "errors": validation["errors"], "warnings": validation["warnings"], "auto_fixes": validation["auto_fixes"],
        "design_source": design_source, "requirements": best["requirements"], "design_rounds": rounds,
        "disclaimer": validation["disclaimer"],
    }
    who = {"generate": f"Gemini ({model_used}) wrote the design script from your brief",
           "run": "your edited design script", "converse": f"Gemini ({model_used}) edited the script as you asked"}[mode]
    return {
        "success": True,
        "project_id": pid,
        "project_title": layout_data.get("project_title", f"{marla_label} {style} Residence"),
        "design_rationale": req.get("understood_as", ""),
        "source": "gemini_cad_engine",
        "design_source": design_source,
        "model_used": model_used,
        "design_script": best["script"],
        "design_concept": best.get("concept"),
        "concepts_tried": best.get("concepts_tried") or sorted({a["concept"]["name"] for a in attempts if a.get("concept")}),
        "floor_similarity": best.get("floor_similarity") or {},
        "script_format": "archiscript-1",
        "style": style,
        "script_problems": best["problems"],
        "script_rounds": rounds,
        "explainability": {
            "strategy_id": "prompt_to_archiscript_to_cad_engine",
            "strategy_name": who + " - the CAD engine ran and tested it",
            "strategy_description": req.get("understood_as", ""),
            "source_archetype_id": f"archiscript + {model_used}",
            "influenced_by_plans": [],
            "bylaw_rules_applied": [
                "Every habitable room has a window on open air (street front, lawn, terrace, gallery or OTS)",
                "No room reached through a bedroom or bath; stair at least 3'-6\" x 9'-0\"",
                "Doors only on walls shared by two spaces (or street frontage when front setback is 0)",
                "Reachability checked with a NetworkX circulation graph",
                "Stair kept in the same place on every level; listed furniture placed in every room",
                "Single 9\" external / 4.5\" internal walls with true door and window cut-outs",
            ],
            "quality_gate_fixes": [f"[UNDERSTOOD] {req.get('understood_as', '')}"] + (
                [f"[CONCEPT] {best['concept']['name']}: stair {best['concept'].get('stair', '')}; "
                 f"{best['concept'].get('circulation', '')}"] if best.get("concept") else []) + [
                f"{'[OK]' if r['met'] else ('[PARTIAL]' if r.get('status') == 'PARTIAL' else '[MISSING]')} "
                f"{r['item']}: {r['detail']}" for r in best["requirements"]
            ] + [f"[NOTE] {n}" for n in requirement_notes] + [
                f"Script round {a['round']} ({a['source']}): {a['errors']} errors, {a['unmet']} unmet" for a in rounds
            ],
        },
        "layout_json": layout_data,
        "floors_detail": floors_summary,
        "images": images,
        "room_schedule": room_schedule,
        "total_rooms": len(room_schedule),
        "covered_area_sqft": total_covered_sqft,
        "floors": layout_data["total_floors"],
        "has_roof_level": has_roof_level,
        "compliance_checklist": compliance_checklist(
            best["requirements"], req, front_sb, rear_sb,
            has_ots=any(r.get("category") == "ots" for f in layout_data["floors"] for r in f.get("rooms", [])),
            has_roof=has_roof_level),
        "cost_estimate": cost_estimate,
        "boq": cost_estimate,
        "total_cost_pkr": total_cost,
        "bylaw_status": ("CAD geometry checks passed" if not n_err
                         else f"{n_err} problem(s) remain - edit the script or ask for a change"),
        "quality_gate": quality_gate,
        "validation": validation,
        "architect_review": best["review"] if "review" in best else (
            architect_review(ctx, best) if (ARCHITECT_REVIEW and mode == "generate") else None),
        "improved_after_review": bool(best.get("improved_after_review")),
        "architect_review_before": best.get("review_before"),
        "requirements": {"checklist": req["checklist"], "report": best["requirements"], "notes": requirement_notes,
                         "understood_as": req.get("understood_as", ""),
                         "read_by": ("rules + " + str(ctx["llm_reading"].get("_model"))) if ctx.get("llm_reading") else "rules",
                         "parsed": {k: v for k, v in req.items() if k not in ("raw_brief", "checklist", "llm_reading")}},
        "brief": ctx["brief"],
        "plot": {"width_ft": plot_width, "length_ft": plot_length, "front_setback_ft": front_sb, "rear_setback_ft": rear_sb},
        "front_elevation": {
            "image_url": images["elevation"],
            "styles": images.get("elevation_styles", {})
        },
        "three_d_model": {"nodes": three_d_nodes, "source": "massing_render",
                          "views": {k: v for k, v in images.items() if k.startswith("view3d_")}},
        "rag_references": ctx.get("rag_references", []),
        "llm_rag": {
            "source": "gemini_live",
            "model": model_used,
            "rag_mode": ctx.get("rag_mode", "vector"),
            "rules_retrieved": len(ctx.get("rag_references", [])),
        },
        "timestamp": datetime.datetime.now().isoformat(),
    }
