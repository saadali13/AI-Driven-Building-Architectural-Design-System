"""
Plan Geometry Engine - deterministic CAD geometry for Gemini-designed floor plans
=================================================================================

Why this module exists
----------------------
LLMs are good at architectural *zoning* (what goes next to what) but poor at
coordinate arithmetic. Asking Gemini for raw x/y rectangles produced overlapping
rooms, empty voids, doors on the plot boundary (opening onto the neighbour or the
street), missing staircases and furniture standing inside door swings.

Responsibilities are therefore split:

* Gemini returns, per floor, a SLICING TREE (bands front→rear, columns left→right)
  plus, for every room, the neighbouring room it is entered from (``door_from``).
* This module turns that into exact geometry with real engineering libraries and
  checks it:

  1. tree → exact rectangular tiling of the plot (no gaps / overlaps by construction)
  2. doors hosted on a wall that is genuinely shared by two spaces of the house -
     never on the plot boundary (party walls / street line)
  3. windows only on walls that face open air (setback, lawn, porch, OTS, balcony)
  4. single-thickness shared walls with true door / window cut-outs (Shapely union)
  5. furniture placed against walls, clear of door swings and door approach zones
  6. validation: setbacks, reachability and no-walk-through-bedroom (NetworkX graph),
     landlocked rooms, stair presence / vertical alignment, structure under upper rooms

Units: feet. Origin (0, 0) = front-left corner of the plot; +x runs left→right along
the street frontage, +y runs from the street (front) to the rear boundary.

This is software CAD validation only - it is not structural engineering
certification or municipal approval.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

# ---------------------------------------------------------------------------
# CONSTANTS (feet)
# ---------------------------------------------------------------------------
EXT_WALL = 0.75          # 9" external / party wall
INT_WALL = 0.375         # 4.5" internal partition
GRID = 0.25              # 3" planning module
EPS = 0.02
DOOR_RETURN = 0.33       # 4" wall return beside a door frame
APPROACH_DEPTH = 3.0     # clear standing zone in front of every door
MIN_PART_FT = 3.0        # smallest slice the tree builder will create

# Room category vocabulary -------------------------------------------------
OPEN_AIR = {"porch", "outdoor", "ots", "pool"}
HABITABLE = {"bedroom", "drawing", "lounge", "dining", "kitchen", "study"}

# The engine checks what is physical: can a person walk in, does the room get daylight, do the doors have a wall,
# does the stair hold its steps, does the listed furniture fit. Opinions about sizes and proportions (what a
# standard or a bylaw would say) are NOT reported - the designing LLM judges those itself. Set to True to get the
# size advice back as warnings.
SIZE_ADVICE = False
_SIZE_ADVICE_CODES = {"WASTED_SPACE", "BALANCE", "TIGHT_ROOM", "PROPORTION", "UNDERSIZED", "CAR_PORCH_TOO_SMALL"}

_TYPE_CATEGORY = {
    "car_porch": "porch", "porch": "porch", "garage": "porch", "carport": "porch",
    "driveway": "outdoor", "lawn": "outdoor", "garden": "outdoor", "balcony": "outdoor",
    "terrace": "outdoor", "open": "outdoor", "rear_open": "outdoor", "setback": "outdoor",
    "wash": "outdoor", "wash_area": "outdoor", "laundry": "outdoor", "verandah": "outdoor",
    "void": "outdoor", "open_to_below": "outdoor", "deck": "outdoor", "pool_deck": "outdoor",
    "pool": "pool", "swimming_pool": "pool", "plunge_pool": "pool",
    "ots": "ots", "courtyard": "ots", "lightwell": "ots", "shaft": "ots",
    "entrance": "circulation", "foyer": "circulation", "lobby": "circulation",
    "passage": "circulation", "corridor": "circulation", "hall": "circulation",
    "stair": "stair", "staircase": "stair", "mumty": "stair",
    "drawing": "drawing", "drawing_room": "drawing",
    "lounge": "lounge", "living": "lounge", "family": "lounge", "tv_lounge": "lounge",
    "dining": "dining",
    "kitchen": "kitchen", "dirty_kitchen": "kitchen", "pantry": "kitchen",
    "bedroom": "bedroom", "master_bedroom": "bedroom", "guest_bedroom": "bedroom",
    "servant": "bedroom", "servant_quarter": "bedroom", "study": "study", "office": "study",
    "bath": "bath", "bathroom": "bath", "powder": "bath", "toilet": "bath", "washroom": "bath",
    "dressing": "dressing", "store": "dressing", "prayer": "room", "gym": "room", "wardrobe": "dressing",
    "room": "room", "nook": "room",
    "gallery": "outdoor", "open_corridor": "outdoor", "majlis": "drawing", "guest_bedroom_suite": "bedroom",
}


def classify_room(room: Dict[str, Any]) -> str:
    """Normalises a room to one category. The explicit ``type`` wins; the name is a fallback."""
    t = str(room.get("type", "")).strip().lower().replace(" ", "_").replace("-", "_")
    if t in _TYPE_CATEGORY:
        return _TYPE_CATEGORY[t]
    raw = f"{room.get('type', '')} {room.get('name', '')}".lower()
    ordered = [
        ("outdoor", ["balcony", "terrace", "lawn", "garden", "driveway", "drive way", "verandah",
                     "setback", "open to below", "void", "wash area", "laundry", "rear open", "deck"]),
        ("pool", ["pool"]),
        ("porch", ["porch", "garage", "carport", "parking"]),
        ("ots", ["ots", "open to sky", "courtyard", "lightwell", "light well", "shaft"]),
        ("stair", ["stair", "mumty"]),
        ("bath", ["bath", "toilet", "powder", "washroom", "wc", "restroom", "ensuite"]),
        ("kitchen", ["kitchen", "scullery", "pantry"]),
        ("dining", ["dining", "breakfast"]),
        ("drawing", ["drawing", "drg", "baithak", "formal"]),
        ("lounge", ["lounge", "living", "tv", "family"]),
        ("circulation", ["lobby", "foyer", "passage", "corridor", "entrance", "ent "]),
        ("dressing", ["dress", "closet", "wardrobe", "store"]),
        ("study", ["study", "office", "library"]),
        ("bedroom", ["bed", "master", "suite", "servant", "guest"]),
    ]
    for cat, keys in ordered:
        if any(k in raw for k in keys):
            return cat
    if raw.strip() in ("open",) or raw.strip().endswith(" open"):
        return "outdoor"
    return "room"


def is_enclosed(cat: str) -> bool:
    return cat not in OPEN_AIR


def _rect(room: Dict[str, Any]) -> Tuple[float, float, float, float]:
    x, y = float(room["x_ft"]), float(room["y_ft"])
    return x, y, x + float(room["w_ft"]), y + float(room["l_ft"])


def _box(room: Dict[str, Any]) -> Polygon:
    return box(*_rect(room))


def _pt(orient: str, along: float, across: float) -> Tuple[float, float]:
    """Maps (along-wall, across-wall) coordinates to global (x, y)."""
    return (along, across) if orient == "h" else (across, along)


def ft_in(val_ft: float) -> str:
    total_in = int(round(float(val_ft) * 12.0))
    return f"{total_in // 12}'-{total_in % 12}\""


# ---------------------------------------------------------------------------
# 1. SLICING TREE → EXACT RECTANGULAR TILING
# ---------------------------------------------------------------------------

def _allocate(sizes: List[Any], extent: float) -> List[float]:
    """Scales requested part sizes so they fill ``extent`` exactly, snapped to a 3" grid."""
    n = len(sizes)
    vals: List[Optional[float]] = []
    for s in sizes:
        try:
            v = float(s)
            vals.append(v if v > 0 else None)
        except (TypeError, ValueError):
            vals.append(None)
    known = [v for v in vals if v]
    fill = (sum(known) / len(known)) if known else extent / max(1, n)
    vals_f = [v if v else fill for v in vals]
    if extent < n * MIN_PART_FT:
        return [extent / n] * n

    factor = extent / sum(vals_f)
    bounds = [0.0]
    cum = 0.0
    for v in vals_f[:-1]:
        cum += v * factor
        bounds.append(round(cum / GRID) * GRID)
    bounds.append(extent)
    parts = [max(0.0, bounds[i + 1] - bounds[i]) for i in range(n)]

    # Enforce a minimum slice by borrowing from the largest part
    for _ in range(n * 2):
        small = [i for i, p in enumerate(parts) if p < MIN_PART_FT - 1e-6]
        if not small:
            break
        i = small[0]
        j = max(range(n), key=lambda k: parts[k])
        need = MIN_PART_FT - parts[i]
        if parts[j] - need < MIN_PART_FT:
            break
        parts[i] += need
        parts[j] -= need
    return parts


def _is_rows(node: Dict[str, Any]) -> bool:
    split = str(node.get("split", "rows")).strip().lower()
    return split in ("rows", "row", "y", "stack", "front_to_rear", "depth", "vertical")


def build_rooms_from_tree(tree: Dict[str, Any], plot_w: float, plot_l: float, level: int) -> List[Dict[str, Any]]:
    """Converts a slicing tree into rooms that tile the plot exactly."""
    rooms: List[Dict[str, Any]] = []
    counter = [0]

    def walk(node: Any, x: float, y: float, w: float, h: float):
        if not isinstance(node, dict):
            return
        room_spec = node.get("room")
        parts = node.get("parts") or node.get("children") or []
        if isinstance(room_spec, dict) or not parts:
            counter[0] += 1
            r = copy.deepcopy(room_spec) if isinstance(room_spec, dict) else {"name": "OPEN", "type": "open"}
            r.update({
                "x_ft": round(x, 3), "y_ft": round(y, 3),
                "w_ft": round(w, 3), "l_ft": round(h, 3), "level": level,
            })
            if not r.get("id"):
                r["id"] = f"L{level}_R{counter[0]:02d}"
            rooms.append(r)
            return
        along_y = _is_rows(node)
        extent = h if along_y else w
        lens = _allocate([p.get("size_ft") if isinstance(p, dict) else None for p in parts], extent)
        off = 0.0
        for p, ln in zip(parts, lens):
            if along_y:
                walk(p, x, y + off, w, ln)
            else:
                walk(p, x + off, y, ln, h)
            off += ln

    walk(tree, 0.0, 0.0, float(plot_w), float(plot_l))
    return rooms


def _normalise_ids(rooms: List[Dict[str, Any]], level: int) -> None:
    seen = set()
    for i, r in enumerate(rooms):
        rid = str(r.get("id") or f"L{level}_R{i + 1:02d}").strip()
        base, k = rid, 2
        while rid in seen:
            rid = f"{base}_{k}"
            k += 1
        r["id"] = rid
        seen.add(rid)
        r["name"] = str(r.get("name") or r.get("type") or "ROOM").upper().strip()
        r["category"] = classify_room(r)


def _resolve_ref(ref: Any, rooms: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if ref is None:
        return None
    key = str(ref).strip()
    if not key or key.lower() in ("null", "none", "street", "outside", ""):
        return None
    for r in rooms:
        if r["id"] == key:
            return r
    for r in rooms:
        if r["id"].lower() == key.lower() or r["name"].lower() == key.lower():
            return r
    return None


# ---------------------------------------------------------------------------
# 2. SHARED WALL ANALYSIS
# ---------------------------------------------------------------------------

def shared_edge(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[Tuple[str, float, float, float]]:
    """Returns (orient, coord, lo, hi) of the wall segment shared by rooms a and b, if any."""
    ax1, ay1, ax2, ay2 = _rect(a)
    bx1, by1, bx2, by2 = _rect(b)
    for xa, xb in ((ax2, bx1), (ax1, bx2)):
        if abs(xa - xb) < EPS:
            lo, hi = max(ay1, by1), min(ay2, by2)
            if hi - lo > EPS:
                return ("v", round(xa, 3), lo, hi)
    for ya, yb in ((ay2, by1), (ay1, by2)):
        if abs(ya - yb) < EPS:
            lo, hi = max(ax1, bx1), min(ax2, bx2)
            if hi - lo > EPS:
                return ("h", round(ya, 3), lo, hi)
    return None


def _junctions(orient: str, coord: float, lo: float, hi: float, rooms: List[Dict[str, Any]]) -> List[float]:
    """Points along a wall segment where perpendicular walls meet it (T-junctions)."""
    pts = {lo, hi}
    for r in rooms:
        x1, y1, x2, y2 = _rect(r)
        if orient == "v" and (abs(x1 - coord) < EPS or abs(x2 - coord) < EPS):
            for v in (y1, y2):
                if lo + EPS < v < hi - EPS:
                    pts.add(v)
        if orient == "h" and (abs(y1 - coord) < EPS or abs(y2 - coord) < EPS):
            for v in (x1, x2):
                if lo + EPS < v < hi - EPS:
                    pts.add(v)
    return sorted(pts)


def _wall_band(orient: str, coord: float, a_room: Dict[str, Any], a_cat: str, b_cat: Optional[str]) -> Tuple[float, float, int]:
    """
    Across-wall extent (lo, hi) of the wall on a shared edge plus the direction (+1/-1)
    pointing into room A. Interior partitions straddle the line; external walls sit
    entirely inside the enclosed room.
    """
    x1, y1, x2, y2 = _rect(a_room)
    into = 1 if (abs((x1 if orient == "v" else y1) - coord) < EPS) else -1
    both_enclosed = is_enclosed(a_cat) and (b_cat is not None and is_enclosed(b_cat))
    if both_enclosed:
        return coord - INT_WALL / 2.0, coord + INT_WALL / 2.0, into
    if is_enclosed(a_cat):
        return (coord, coord + EXT_WALL, into) if into > 0 else (coord - EXT_WALL, coord, into)
    # A is open air, B enclosed: wall lies on B's side (opposite to A)
    return (coord - EXT_WALL, coord, into) if into > 0 else (coord, coord + EXT_WALL, into)


def _building_poly(rooms: List[Dict[str, Any]]):
    boxes = [_box(r) for r in rooms if is_enclosed(r["category"])]
    return unary_union(boxes) if boxes else Polygon()


def _end_clearance(orient: str, coord: float, along: float, building) -> float:
    """Clearance needed between a door jamb and the perpendicular wall at a segment end."""
    # The wall that meets the jamb is external only if the building outline itself turns there
    # (a corner, or an internal wall ending on the facade). A partition meeting an external wall
    # in a T-junction only needs half a partition of clearance.
    if not building.is_empty:
        px, py = _pt(orient, along, coord)
        bnd = building.boundary
        if Point(px, py).distance(bnd) < 0.05:
            dx, dy = (0.0, 0.3) if orient == "h" else (0.3, 0.0)
            if any(Point(px + s * dx, py + s * dy).distance(bnd) < 0.02 for s in (1, -1)):
                return EXT_WALL + DOOR_RETURN
    return INT_WALL / 2.0 + DOOR_RETURN


# ---------------------------------------------------------------------------
# 3. DOORS
# ---------------------------------------------------------------------------

def door_swing_polygon(d: Dict[str, Any]) -> Polygon:
    """90° swept sector of a hinged leaf (empty for arches / gates)."""
    if d.get("kind") in ("arch", "gate"):
        return Polygon()
    o, w, into = d["orient"], d["width"], d["into"]
    face = d["band"][1] if into > 0 else d["band"][0]
    if d.get("kind") == "main_double":
        leaves = [(d["s"], 1.0, w / 2.0), (d["e"], -1.0, w / 2.0)]
    else:
        hinge_along = d["s"] if d["hinge"] == "s" else d["e"]
        leaves = [(hinge_along, 1.0 if d["hinge"] == "s" else -1.0, w)]
    polys = []
    for h_along, dirn, radius in leaves:
        pts = [_pt(o, h_along, face)]
        for i in range(0, 13):
            t = (math.pi / 2.0) * i / 12.0
            pts.append(_pt(o, h_along + dirn * radius * math.cos(t), face + into * radius * math.sin(t)))
        polys.append(Polygon(pts))
    return unary_union(polys)


def door_approach_zones(d: Dict[str, Any], depth: float = APPROACH_DEPTH) -> List[Polygon]:
    """Clear standing zones (opening width x depth, 3 ft by default) on both sides of a door."""
    o = d["orient"]
    lo, hi = d["band"]
    zones = []
    for side in (1, -1):
        start = hi if side > 0 else lo
        end = start + side * depth
        a, b = sorted((start, end))
        p1 = _pt(o, d["s"], a)
        p2 = _pt(o, d["e"], b)
        zones.append(box(min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1])))
    return zones


def opening_polygon(op: Dict[str, Any]) -> Polygon:
    """Rectangle that cuts the wall solid for a door / window opening."""
    lo, hi = op["band"]
    p1 = _pt(op["orient"], op["s"], lo - 0.03)
    p2 = _pt(op["orient"], op["e"], hi + 0.03)
    return box(min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1]))


def _door_width(a_cat: str, kind: str) -> float:
    if kind.startswith("main"):
        return 4.0
    if kind == "arch":
        return 5.0
    if a_cat in ("bath", "dressing"):
        return 2.5
    if a_cat in ("drawing", "lounge"):
        return 3.5
    return 3.0


def _plan_door(a: Dict[str, Any], b: Dict[str, Any], rooms: List[Dict[str, Any]], building,
               kind: str, existing: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Hosts a door on the wall shared by rooms ``a`` (the room entered - the leaf swings into it)
    and ``b``. Returns (door, problem_message).
    """
    edge = shared_edge(a, b)
    if edge is None:
        return None, f"{a['id']} ({a['name']}) and {b['id']} ({b['name']}) do not share a wall"
    orient, coord, lo, hi = edge
    want = _door_width(a["category"], kind)
    if kind == "arch":
        want = min(5.0, max(3.5, (hi - lo) - 2.0))
        if (a.get("part_of") or a["id"]) == (b.get("part_of") or b["id"]):
            want = hi - lo                      # two parts of one space: no wall between them
    min_w = 2.33 if a["category"] in ("bath", "dressing") else 2.75

    pts = _junctions(orient, coord, lo, hi, rooms)
    ax1, ay1, ax2, ay2 = _rect(a)
    a_lo, a_hi = (ax1, ax2) if orient == "h" else (ay1, ay2)
    band = _wall_band(orient, coord, a, a["category"], b["category"])

    candidates = []
    for u, v in zip(pts[:-1], pts[1:]):
        cu = _end_clearance(orient, coord, u, building)
        cv = _end_clearance(orient, coord, v, building)
        usable = (v - cv) - (u + cu)
        eff_min_w = min_w
        if usable < eff_min_w - 1e-6 and (v - u) >= 2.6:
            cu = min(cu, INT_WALL / 2.0 + 0.08)
            cv = min(cv, INT_WALL / 2.0 + 0.08)
            usable = (v - cv) - (u + cu)
            eff_min_w = min(min_w, 2.2)
        if usable < eff_min_w - 1e-6:
            continue
        w = min(want, usable)
        cost_u = 0.0 if abs(u - a_lo) < EPS or abs(u - a_hi) < EPS else 1.0
        cost_v = 0.0 if abs(v - a_lo) < EPS or abs(v - a_hi) < EPS else 1.0
        if kind == "arch" or kind.startswith("main"):
            mid = (u + cu + v - cv) / 2.0
            candidates.append((0.0 + (want - w), mid - w / 2.0, mid + w / 2.0, "s"))
        else:
            candidates.append((cost_u + (want - w), u + cu, u + cu + w, "s"))
            candidates.append((cost_v + (want - w), v - cv - w, v - cv, "e"))
    if not candidates:
        return None, (f"wall shared by {a['id']} ({a['name']}) and {b['id']} ({b['name']}) is only "
                      f"{hi - lo:.1f} ft long between corners - too short for a {want:.1f} ft door")
    candidates.sort(key=lambda c: c[0])

    others = [od for od in existing if od.get("level") == a.get("level")]
    other_swings = unary_union([door_swing_polygon(od) for od in others]) if others else Polygon()
    other_open = unary_union([opening_polygon(od) for od in others]) if others else Polygon()
    chosen = None
    for cost, s, e, hinge in candidates:
        d = {
            "kind": "main_double" if kind.startswith("main") and (e - s) >= 3.9 else
                    ("main" if kind.startswith("main") else kind),
            "room_id": a["id"], "from_id": b["id"], "level": a.get("level", 0),
            "orient": orient, "coord": coord, "s": round(s, 3), "e": round(e, 3),
            "width": round(e - s, 3), "hinge": hinge, "into": band[2],
            "band": (round(band[0], 3), round(band[1], 3)),
        }
        sw = door_swing_polygon(d)
        clash = (sw.intersection(other_swings).area > 0.05) or (sw.intersection(other_open).area > 0.01) \
            or (opening_polygon(d).intersection(other_swings).area > 0.01)
        if not clash:
            chosen = d
            break
        if chosen is None:
            chosen = d
            chosen["_clash"] = True
    problem = None
    if chosen.pop("_clash", False):
        problem = f"door into {a['id']} ({a['name']}) collides with another door swing"
    return chosen, problem


_FALLBACK_PRIORITY = {
    "bath": ["bedroom", "circulation", "lounge", "dining"],
    "dressing": ["bedroom", "circulation"],
    "bedroom": ["circulation", "lounge", "dining"],
    "kitchen": ["dining", "lounge", "circulation"],
    "stair": ["circulation", "lounge", "dining", "porch"],
    "study": ["circulation", "lounge", "dining"],
    "drawing": ["circulation", "porch", "outdoor", "lounge"],
    "lounge": ["circulation", "dining", "lounge", "drawing"],
    "dining": ["lounge", "circulation", "kitchen"],
    "circulation": ["lounge", "circulation", "porch", "outdoor", "dining"],
    "room": ["circulation", "lounge", "dining"],
}


def compute_doors(rooms: List[Dict[str, Any]], plot_w: float, plot_l: float, level: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Plans every door of a floor from the declared ``door_from`` topology."""
    building = _building_poly(rooms)
    doors: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []
    fixes: List[str] = []

    def add_issue(code, level_s, room, msg):
        issues.append({"code": code, "level": level_s, "floor": level, "room": room, "message": msg})

    # A door written on an open space ("OPEN CORRIDOR door: STAIR") belongs to the room that opens onto it
    by_id = {r["id"]: r for r in rooms}
    for a in rooms:
        ref = a.get("door_from")
        b = by_id.get(ref) if ref not in (None, "", "null") else None
        if b is not None and not is_enclosed(a["category"]) and is_enclosed(b["category"]) \
                and b.get("door_from") in (None, "", "null") and not b.get("arch_to"):
            b["door_from"] = a["id"]
            a["door_from"] = None
            fixes.append(f"{b['id']} ({b['name']}) now opens onto {a['id']} ({a['name']}) - the door was written on the open space")

    def neighbour_candidates(a):
        out = []
        for b in rooms:
            if b is a:
                continue
            e = shared_edge(a, b)
            if e and (e[3] - e[2]) >= 2.8:
                out.append(b)
        return out

    # One space written as several parts (an L-shaped lounge in two bands: the parts carry part_of = first part).
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in rooms:
        root = r.get("part_of")
        if root and root in by_id:
            groups.setdefault(root, [by_id[root]]).append(r)

    def best_part(a, b):
        """A reference to a space with several parts lands on the part that shares the longest wall with a."""
        members = [m for m in groups.get(b.get("part_of") or b["id"], [b]) if m is not a]
        scored = [(e[3] - e[2], m) for m in members for e in [shared_edge(a, m)] if e]
        if scored:
            return max(scored, key=lambda t: t[0])[1]
        return b if b is not a else None

    for root, members in groups.items():        # the parts of one space are joined by an open arch
        for m in members[1:]:
            others = [o for o in members if o is not m]
            linked = set(m.get("arch_to") or []) | {m.get("door_from")}
            if not linked & {o["id"] for o in others}:
                tgt = best_part(m, by_id[root])
                if tgt is not None and shared_edge(m, tgt):
                    m["arch_to"] = list(m.get("arch_to") or []) + [tgt["id"]]

    def _plan_street_door(a: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Places a main entrance door on the street-facing wall (y=0) of room a when front setback is 0."""
        x1, y1, x2, y2 = _rect(a)
        if abs(y1) > EPS or (x2 - x1) < 3.0:
            return None
        w = min(3.5, max(2.8, (x2 - x1) - 1.5))
        mid = (x1 + x2) / 2.0
        band = _wall_band("h", 0.0, a, a["category"], None)
        return {
            "kind": "main",
            "room_id": a["id"], "from_id": "STREET", "level": a.get("level", 0),
            "orient": "h", "coord": 0.0, "s": round(mid - w / 2.0, 3), "e": round(mid + w / 2.0, 3),
            "width": round(w, 3), "hinge": "s", "into": band[2],
            "band": (round(band[0], 3), round(band[1], 3)),
        }

    def try_fallback(a, reason):
        prio = _FALLBACK_PRIORITY.get(a["category"], ["circulation", "lounge"])
        cands = neighbour_candidates(a)
        for cat in prio:
            for b in cands:
                if b["category"] != cat:
                    continue
                if any({d0["room_id"], d0["from_id"]} == {a["id"], b["id"]} for d0 in doors):
                    return True                 # these two spaces already have a door between them
                d, prob = _plan_door(a, b, rooms, building, "door", doors)
                if d and not prob:
                    doors.append(d)
                    fixes.append(f"{a['id']} ({a['name']}): {reason} -> door re-hosted on the wall shared with {b['id']} ({b['name']})")
                    return True
        if level == 0 and abs(float(a.get("y_ft", 99.0))) < EPS and a["category"] in ("circulation", "lounge", "drawing", "stair"):
            sd = _plan_street_door(a)
            if sd:
                doors.append(sd)
                fixes.append(f"{a['id']} ({a['name']}): {reason} -> main entrance door placed on street frontage")
                return True
        return False

    pairs_done = set()
    for a in rooms:
        cat = a["category"]
        refs = []
        if a.get("door_from") not in (None, "", "null"):
            refs.append(("door", a.get("door_from")))
        elif level == 0 and a.get("gate") and abs(float(a.get("y_ft", 99.0))) < EPS and is_enclosed(cat):
            refs.append(("door", "STREET"))
        for ref in a.get("extra_doors_from") or []:
            refs.append(("door", ref))
        for ref in a.get("arch_to") or []:
            refs.append(("arch", ref))

        if not refs:
            if is_enclosed(cat) and not try_fallback(a, "no door declared"):
                add_issue("NO_DOOR", "error", a["id"], f"{a['id']} ({a['name']}) has no door and no neighbouring circulation space to host one")
            continue

        for kind, ref in refs:
            if str(ref).strip().upper() == "STREET" and level == 0 and is_enclosed(cat):
                sd = _plan_street_door(a)
                if sd:
                    doors.append(sd)
                    continue
            b = _resolve_ref(ref, rooms)
            if b is not None and (b is a or b.get("part_of") or b["id"] in groups):
                b = best_part(a, b)
                if b is None:
                    continue                    # a space pointing at itself
            if b is None:
                if kind == "door" and is_enclosed(cat):
                    if not try_fallback(a, f"door_from '{ref}' does not exist on this floor"):
                        add_issue("DOOR_BAD_REF", "error", a["id"], f"{a['id']} ({a['name']}) door_from '{ref}' is not a room on this floor")
                continue
            key = tuple(sorted((a["id"], b["id"]))) + (kind,)
            if key in pairs_done:
                continue
            pairs_done.add(key)

            a_enc, b_enc = is_enclosed(cat), is_enclosed(b["category"])
            if not a_enc and not b_enc:
                continue  # open-air to open-air: no door, open connection
            # The leaf always swings into the enclosed room
            enter, other = (a, b) if a_enc else (b, a)
            d_kind = kind
            if kind == "door" and enter.get("level", 0) == 0 and other["category"] in ("porch", "outdoor") \
                    and other["y_ft"] < 1.0 and enter["category"] in ("circulation", "lounge"):
                d_kind = "main"
            if kind == "door" and enter["category"] in ("bedroom", "kitchen", "lounge", "drawing", "dining", "stair") \
                    and other["category"] in ("bedroom", "bath"):
                if try_fallback(enter, f"entered through {other['category']} {other['id']}"):
                    continue
            d, prob = _plan_door(enter, other, rooms, building, d_kind, doors)
            if d is None:
                if kind == "door" and is_enclosed(enter["category"]) and try_fallback(enter, prob):
                    continue
                add_issue("DOOR_NO_SHARED_WALL", "error", enter["id"], prob)
                continue
            doors.append(d)
            if prob:
                add_issue("DOOR_SWING_CLASH", "warning", enter["id"], prob)

    # If level 0 has no open front space at y=0 and no street door yet, auto-place a street door on the front circulation/lounge room
    if level == 0 and not any(r["category"] in ("porch", "outdoor") and float(r["y_ft"]) < EPS for r in rooms) \
            and not any(d.get("from_id") == "STREET" for d in doors):
        front_rooms = [r for r in rooms if is_enclosed(r["category"]) and abs(float(r["y_ft"])) < EPS]
        front_rooms.sort(key=lambda r: (0 if r.get("gate") else 1,
                                        0 if r["category"] in ("circulation", "lounge", "drawing", "stair") else 1))
        for fr in front_rooms:
            sd = _plan_street_door(fr)
            if sd:
                doors.append(sd)
                fixes.append(f"{fr['id']} ({fr['name']}): main entrance door placed on street frontage (no front setback)")
                break

    for i, d in enumerate(doors):
        d["id"] = f"D{level}_{i + 1:02d}"
    return doors, issues, fixes


def _on_plot_boundary(op: Dict[str, Any], plot_w: float, plot_l: float) -> bool:
    c = op["coord"]
    return (op["orient"] == "v" and (abs(c) < EPS or abs(c - plot_w) < EPS)) or \
           (op["orient"] == "h" and (abs(c) < EPS or abs(c - plot_l) < EPS))


# ---------------------------------------------------------------------------
# 4. WINDOWS (only where the wall faces open air)
# ---------------------------------------------------------------------------

_WINDOW_TARGET = {"bedroom": 5.0, "study": 4.0, "drawing": 6.0, "lounge": 6.0, "dining": 5.0, "kitchen": 4.0,
                  "bath": 2.0, "stair": 3.0, "circulation": 3.0, "dressing": 2.0, "room": 3.0}


def compute_windows(rooms: List[Dict[str, Any]], doors: List[Dict[str, Any]], plot_w: float, plot_l: float,
                    level: int) -> List[Dict[str, Any]]:
    windows: List[Dict[str, Any]] = []
    for a in rooms:
        cat = a["category"]
        if not is_enclosed(cat):
            continue
        cands = []
        for b in rooms:
            if b is a or is_enclosed(b["category"]):
                continue
            e = shared_edge(a, b)
            if e:
                cands.append((e, b["name"], b["category"]))
        x1, y1, x2, y2 = _rect(a)
        if abs(y1) < EPS:  # street facade (only possible if the room sits on the front line)
            cands.append((("h", 0.0, x1, x2), "STREET", "street"))
        segs = []
        for (orient, coord, lo, hi), faces, fcat in cands:
            cuts = _junctions(orient, coord, lo, hi, rooms)
            blocked = [(d["s"] - 0.5, d["e"] + 0.5) for d in doors
                       if d["orient"] == orient and abs(d["coord"] - coord) < EPS]
            for u, v in zip(cuts[:-1], cuts[1:]):
                free = [(u + 0.75, v - 0.75)]
                for bs, be in blocked:
                    nxt = []
                    for fs, fe in free:
                        if be <= fs or bs >= fe:
                            nxt.append((fs, fe))
                        else:
                            if bs > fs:
                                nxt.append((fs, bs))
                            if be < fe:
                                nxt.append((be, fe))
                    free = nxt
                for fs, fe in free:
                    if fe - fs > 1.4:
                        segs.append((fe - fs, orient, coord, fs, fe, faces, fcat))
        segs.sort(key=lambda s: -s[0])
        max_n = 2 if cat in ("bedroom", "drawing", "lounge", "dining") else 1
        used_lines = set()
        for length, orient, coord, fs, fe, faces, fcat in segs:
            if len([w for w in windows if w["room_id"] == a["id"]]) >= max_n:
                break
            if (orient, coord) in used_lines:
                continue
            target = _WINDOW_TARGET.get(cat, 3.0)
            w = min(target, length)
            if w < (1.5 if cat == "bath" else 2.5):
                continue
            mid = (fs + fe) / 2.0
            band = _wall_band(orient, coord, a, cat, None)
            windows.append({
                "id": f"W{level}_{len(windows) + 1:02d}", "room_id": a["id"], "level": level,
                "orient": orient, "coord": coord, "s": round(mid - w / 2, 3), "e": round(mid + w / 2, 3),
                "width": round(w, 3), "into": band[2], "band": (round(band[0], 3), round(band[1], 3)),
                "faces": faces, "faces_category": fcat,
                "kind": "ventilator" if cat == "bath" else "window",
            })
            used_lines.add((orient, coord))
    return windows


# ---------------------------------------------------------------------------
# 5. WALL SOLIDS (single shared walls + true cut-outs)
# ---------------------------------------------------------------------------

def build_wall_geometry(rooms: List[Dict[str, Any]], doors: List[Dict[str, Any]],
                        windows: List[Dict[str, Any]]) -> Dict[str, Any]:
    for r in rooms:
        r.setdefault("category", classify_room(r))
    enclosed = [_box(r) for r in rooms if is_enclosed(r["category"]) and float(r["w_ft"]) > 0.5 and float(r["l_ft"]) > 0.5]
    if not enclosed:
        return {"building": Polygon(), "solid": Polygon(), "walls": Polygon()}
    building = unary_union(enclosed)
    inner = building.buffer(-EXT_WALL, join_style="mitre")
    ext_ring = building.difference(inner)
    lines = unary_union([b.boundary for b in enclosed])
    int_walls = lines.buffer(INT_WALL / 2.0, cap_style="flat", join_style="mitre").intersection(building)
    solid = unary_union([ext_ring, int_walls])
    cuts = [opening_polygon(o) for o in list(doors) + list(windows)]
    walls = solid.difference(unary_union(cuts)) if cuts else solid
    return {"building": building, "solid": solid, "walls": walls}


def room_clear_rect(room: Dict[str, Any], building) -> Tuple[float, float, float, float]:
    """Room rectangle reduced by the actual wall thickness on each side."""
    x1, y1, x2, y2 = _rect(room)
    if not is_enclosed(room["category"]):
        return x1 + 0.2, y1 + 0.2, x2 - 0.2, y2 - 0.2
    env = building.boundary if not building.is_empty else None

    def inset(seg):
        ls = LineString(seg)
        if env is not None and ls.intersection(env).length > 0.3:
            return EXT_WALL
        return INT_WALL / 2.0

    return (x1 + inset([(x1, y1), (x1, y2)]), y1 + inset([(x1, y1), (x2, y1)]),
            x2 - inset([(x2, y1), (x2, y2)]), y2 - inset([(x1, y2), (x2, y2)]))


# ---------------------------------------------------------------------------
# 6. FURNITURE PLACEMENT (wall-hugging, collision-checked with Shapely)
# ---------------------------------------------------------------------------

_SIDE_FACING = {"S": "N", "N": "S", "W": "E", "E": "W"}
_OPPOSITE = {"S": "N", "N": "S", "W": "E", "E": "W"}


def _item_bbox(clear, side, W, D, t):
    x1, y1, x2, y2 = clear
    if side == "S":
        return (x1 + t, y1, x1 + t + W, y1 + D)
    if side == "N":
        return (x1 + t, y2 - D, x1 + t + W, y2)
    if side == "W":
        return (x1, y1 + t, x1 + D, y1 + t + W)
    return (x2 - D, y1 + t, x2, y1 + t + W)


def _wall_len(clear, side):
    x1, y1, x2, y2 = clear
    return (x2 - x1) if side in ("S", "N") else (y2 - y1)


def _depth_avail(clear, side):
    x1, y1, x2, y2 = clear
    return (y2 - y1) if side in ("S", "N") else (x2 - x1)


def _collides(poly: Polygon, obstacles: List[Polygon], tol: float = 0.02) -> bool:
    return any(poly.intersection(o).area > tol for o in obstacles if not o.is_empty)


class _Placer:
    def __init__(self, room, clear, hard, tall_only, door_sides, window_sides):
        self.room = room
        self.clear = clear
        self.clear_poly = box(*clear)
        self.hard = list(hard)          # door swings + approach zones + placed items
        self.tall_only = list(tall_only)  # window zones (block tall items only)
        self.door_sides = door_sides
        self.window_sides = window_sides
        self.items: List[Dict[str, Any]] = []
        self.unplaced: List[str] = []

    def _ok(self, bb, tall=False, extra=None):
        poly = box(*bb)
        if not self.clear_poly.buffer(0.01).contains(poly):
            return False
        obs = self.hard + (self.tall_only if tall else []) + (extra or [])
        return not _collides(poly, obs)

    def add(self, itype, bb, facing, W, D, keepout=None):
        it = {"type": itype, "x": round(bb[0], 3), "y": round(bb[1], 3),
              "w": round(bb[2] - bb[0], 3), "h": round(bb[3] - bb[1], 3),
              "facing": facing, "W": W, "D": D, "room_id": self.room["id"]}
        self.items.append(it)
        self.hard.append(box(*bb))
        for k in keepout or []:
            self.hard.append(k)
        return it

    def against_wall(self, itype, W, D, side_order, tall=False, align="center", check=None, keepout_fn=None):
        for side in side_order:
            L = _wall_len(self.clear, side)
            if W > L + 1e-6 or D > _depth_avail(self.clear, side) + 1e-6:
                continue
            span = L - W
            steps = int(span / GRID) + 1
            offs = [i * GRID for i in range(steps)] + [span]
            if align == "center":
                offs.sort(key=lambda t: abs(t - span / 2.0))
            elif align == "start":
                offs.sort()
            elif align == "end":
                offs.sort(reverse=True)
            for t in offs:
                bb = _item_bbox(self.clear, side, W, D, t)
                if not self._ok(bb, tall):
                    continue
                if check and not check(bb, side):
                    continue
                keep = keepout_fn(bb, side) if keepout_fn else None
                return self.add(itype, bb, _SIDE_FACING[side], W, D, keep), side
        self.unplaced.append(itype)
        return None, None

    def free(self, itype, W, D, facing, center, tall=False, radius=6.0):
        """Free-standing item: nearest collision-free position to ``center`` (3" search grid)."""
        cx, cy = center
        gw, gh = (W, D) if facing in ("N", "S") else (D, W)
        n = int(radius / GRID)
        offsets = sorted(((i, j) for i in range(-n, n + 1) for j in range(-n, n + 1)),
                         key=lambda ij: ij[0] * ij[0] + ij[1] * ij[1])
        for i, j in offsets:
            x = cx - gw / 2 + i * GRID
            y = cy - gh / 2 + j * GRID
            bb = (x, y, x + gw, y + gh)
            if self._ok(bb, tall):
                return self.add(itype, bb, facing, W, D)
        self.unplaced.append(itype)
        return None


def _side_rank(placer: _Placer, prefer_opposite_door=True, avoid_window=True, prefer_long=True):
    sides = ["S", "N", "W", "E"]
    door_side = placer.door_sides[0] if placer.door_sides else None

    def score(s):
        sc = 0.0
        if s in placer.door_sides:
            sc += 100.0
        if avoid_window and s in placer.window_sides:
            sc += 6.0
        if prefer_opposite_door and door_side and s == _OPPOSITE[door_side]:
            sc -= 3.0
        if prefer_long:
            sc -= _wall_len(placer.clear, s) * 0.1
        return sc
    return sorted(sides, key=score)


def _sides_of(room, ops) -> List[str]:
    x1, y1, x2, y2 = _rect(room)
    out = []
    for o in ops:
        c = o["coord"]
        if o["orient"] == "h":
            if abs(c - y1) < EPS:
                out.append("S")
            elif abs(c - y2) < EPS:
                out.append("N")
        else:
            if abs(c - x1) < EPS:
                out.append("W")
            elif abs(c - x2) < EPS:
                out.append("E")
    return out


def _window_zone(w: Dict[str, Any], depth=1.5) -> Polygon:
    lo, hi = w["band"]
    start = hi if w["into"] > 0 else lo
    end = start + w["into"] * depth
    a, b = sorted((start, end))
    p1 = _pt(w["orient"], w["s"], a)
    p2 = _pt(w["orient"], w["e"], b)
    return box(min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1]))


def _strip(clear, side, depth, lo=None, hi=None):
    x1, y1, x2, y2 = clear
    if side == "S":
        return (x1 if lo is None else lo, y1, x2 if hi is None else hi, y1 + depth)
    if side == "N":
        return (x1 if lo is None else lo, y2 - depth, x2 if hi is None else hi, y2)
    if side == "W":
        return (x1, y1 if lo is None else lo, x1 + depth, y2 if hi is None else hi)
    return (x2 - depth, y1 if lo is None else lo, x2, y2 if hi is None else hi)


def _requested(room, *keys) -> bool:
    items = " ".join(str(f).lower() for f in (room.get("furniture") or []))
    return any(k in items for k in keys)


def furnish_room(room: Dict[str, Any], building, doors: List[Dict[str, Any]],
                 windows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    cat = room["category"]
    clear = room_clear_rect(room, building)
    cw, cl = clear[2] - clear[0], clear[3] - clear[1]
    if cw < 2.0 or cl < 2.0:
        return [], []
    rid = room["id"]
    my_doors = [d for d in doors if d["room_id"] == rid or d["from_id"] == rid]
    hard = []
    rbox = _box(room)
    for d in my_doors:
        if d["room_id"] == rid:
            hard.append(door_swing_polygon(d).intersection(rbox))
        # parked cars may stand 1'-6" from a porch door; indoor furniture keeps the full 3 ft
        for z in door_approach_zones(d, 1.5 if cat == "porch" else APPROACH_DEPTH):
            zi = z.intersection(rbox)
            if zi.area > 0.05:
                hard.append(zi)
    my_wins = [w for w in windows if w["room_id"] == rid]
    tall = [_window_zone(w) for w in my_wins]
    p = _Placer(room, clear, hard, tall, _sides_of(room, [d for d in my_doors]), _sides_of(room, my_wins))
    small_side = min(cw, cl)
    area = cw * cl

    if cat == "bedroom" and _requested(room, "sofa_bed", "sofa bed", "sofa-bed"):
        # family "bed space": a sofa-cum-bed against the longest free wall + wardrobe
        sb, _ = p.against_wall("sofa_bed", 6.5, 3.0, _side_rank(p))
        if sb is None:
            p.unplaced.pop()
            sb, _ = p.against_wall("sofa_bed", 5.5, 3.0, _side_rank(p))
        for L in (5.0, 4.0, 3.0):
            wr, _ = p.against_wall("wardrobe", L, 2.0, _side_rank(p, prefer_opposite_door=False), tall=True, align="start")
            if wr is not None:
                break
            p.unplaced.pop()

    elif cat == "bedroom":
        if _requested(room, "single", "twin") or small_side < 9.0:
            bed_t, BW, BD = "bed_single", 3.5, 6.5
        elif _requested(room, "queen") or small_side < 11.0 or area < 125:
            bed_t, BW, BD = "bed_queen", 5.0, 6.75
        else:
            bed_t, BW, BD = "bed_king", 6.0, 6.75

        def bed_ok(bb, side):
            # walking space: 2 ft at the foot and 1.75 ft on at least one long side
            x1, y1, x2, y2 = bb
            c = p.clear
            if side == "S":
                foot = y2 + 2.0 <= c[3]
                long_side = (x1 - c[0] >= 1.75) or (c[2] - x2 >= 1.75)
            elif side == "N":
                foot = y1 - 2.0 >= c[1]
                long_side = (x1 - c[0] >= 1.75) or (c[2] - x2 >= 1.75)
            elif side == "W":
                foot = x2 + 2.0 <= c[2]
                long_side = (y1 - c[1] >= 1.75) or (c[3] - y2 >= 1.75)
            else:
                foot = x1 - 2.0 >= c[0]
                long_side = (y1 - c[1] >= 1.75) or (c[3] - y2 >= 1.75)
            return foot and long_side

        def bed_and_wardrobe(sides, align):
            """Places the bed (with its nightstands and walking zones) and then the wardrobe.
            Returns (bed, wall side of the bed, bed type, wardrobe placed?)."""
            bt, bw_, bd_ = bed_t, BW, BD
            bed, bside = p.against_wall(bt, bw_, bd_, sides, align=align, check=bed_ok)
            if bed is None and bt != "bed_single":
                p.unplaced.pop()
                bt, bw_, bd_ = ("bed_queen", 5.0, 6.75) if bt == "bed_king" else ("bed_single", 3.5, 6.5)
                bed, bside = p.against_wall(bt, bw_, bd_, sides, align=align, check=bed_ok)
            if bed is None:
                # Compact room fallback: place a compact bed against any clear wall without full walking-zone margin
                p.unplaced.pop()
                for ct, cw_b, cd_b in (("bed_queen", 4.5, 6.0), ("bed_single", 3.0, 5.8)):
                    bed, bside = p.against_wall(ct, cw_b, cd_b, sides, align=align, check=None)
                    if bed is not None:
                        bt = ct
                        break
                    p.unplaced.pop()
                if bed is None:
                    p.unplaced.append("bed_single")
            if bed is not None:
                bb = (bed["x"], bed["y"], bed["x"] + bed["w"], bed["y"] + bed["h"])
                for off in (-1.6, 1.6):
                    ns = 1.5
                    if bside in ("S", "N"):
                        nx0 = bb[0] - ns - 0.1 if off < 0 else bb[2] + 0.1
                        ny0 = bb[1] if bside == "S" else bb[3] - ns
                        nb = (nx0, ny0, nx0 + ns, ny0 + ns)
                    else:
                        ny0 = bb[1] - ns - 0.1 if off < 0 else bb[3] + 0.1
                        nx0 = bb[0] if bside == "W" else bb[2] - ns
                        nb = (nx0, ny0, nx0 + ns, ny0 + ns)
                    if p._ok(nb):
                        p.add("nightstand", nb, _SIDE_FACING[bside], ns, ns)
                # keep the bed's walking zones free for the wardrobe etc.
                x1, y1, x2, y2 = bb
                c = p.clear
                if bside in ("S", "N"):
                    p.hard.append(box(max(c[0], x1 - 1.75), y1, x1, y2))
                    p.hard.append(box(x2, y1, min(c[2], x2 + 1.75), y2))
                    p.hard.append(box(x1, y2, x2, min(c[3], y2 + 2.0)) if bside == "S" else box(x1, max(c[1], y1 - 2.0), x2, y1))
                else:
                    p.hard.append(box(x1, max(c[1], y1 - 1.75), x2, y1))
                    p.hard.append(box(x1, y2, x2, min(c[3], y2 + 1.75)))
                    p.hard.append(box(x2, y1, min(c[2], x2 + 2.0), y2) if bside == "W" else box(max(c[0], x1 - 2.0), y1, x1, y2))
            placed = False
            for L in (6.0, 5.0, 4.0, 3.0, 2.5, 2.0):
                order = [sd for sd in _side_rank(p, prefer_opposite_door=False) if sd != bside] + ([bside] if bside else [])
                wr, _ = p.against_wall("wardrobe", L, 2.0, order, tall=True, align="start")
                if wr is not None:
                    placed = True
                    break
                p.unplaced.pop()
            return bed, bside, bt, placed

        # The first bed position that works is not always one that leaves a wall for the wardrobe: when the
        # wardrobe finds no place, the bed is tried on the other walls / ends before the wardrobe is given up.
        snap = (list(p.items), list(p.hard), list(p.unplaced))
        ranked = _side_rank(p)
        bed, bside, bed_t, placed_wr = bed_and_wardrobe(ranked, "center")
        if bed is not None and not placed_wr:
            for alt_side, alt_align in [(sd, al) for al in ("center", "start", "end") for sd in ranked]:
                p.items[:], p.hard[:], p.unplaced[:] = list(snap[0]), list(snap[1]), list(snap[2])
                bed2, bside2, bt2, ok2 = bed_and_wardrobe([alt_side], alt_align)
                if bed2 is not None and ok2 and bt2 == bed_t:
                    bed, bside, placed_wr = bed2, bside2, True
                    break
            else:
                p.items[:], p.hard[:], p.unplaced[:] = list(snap[0]), list(snap[1]), list(snap[2])
                bed, bside, bed_t, placed_wr = bed_and_wardrobe(ranked, "center")
        if not placed_wr:
            p.unplaced.append("wardrobe")
        if (_requested(room, "desk", "study") or "STUDY" in room["name"]) and area > 90:
            it, _ = p.against_wall("study_desk", 3.5, 2.0, _side_rank(p, prefer_opposite_door=False), align="center")
            if it is None:
                p.unplaced.pop()
        elif area >= 150 or _requested(room, "dressing_table", "dresser"):
            it, _ = p.against_wall("dressing_table", 3.0, 1.5, _side_rank(p, prefer_opposite_door=False), align="center")
            if it is None:
                p.unplaced.pop()

    elif cat in ("lounge", "drawing") and _requested(room, "floor_seating", "majlis", "arab"):
        # Arab-style majlis: low floor cushions along the walls, a rug and a low table in the middle
        placed = 0
        for side in _side_rank(p, prefer_opposite_door=False):
            wl = _wall_len(p.clear, side)
            for L in sorted({min(wl, 14.0), min(wl, 10.0), 8.0, 6.0, 4.0}, reverse=True):
                if L > wl + 1e-6 or L < 3.9:
                    continue
                it, _ = p.against_wall("floor_cushion", L, 2.5, [side], align="center")
                if it is not None:
                    placed += 1
                    break
                p.unplaced.pop()
            if placed >= 3:
                break
        if not placed:
            p.unplaced.append("floor_seating")
        cx, cy = (p.clear[0] + p.clear[2]) / 2.0, (p.clear[1] + p.clear[3]) / 2.0
        if p.free("low_table", 3.0, 2.0, "N", (cx, cy), radius=2.0) is None:
            p.unplaced.pop()

    elif cat in ("lounge", "drawing"):
        sofa_W = 7.0 if max(cw, cl) >= 10.5 else 5.0
        sofa, sside = p.against_wall("sofa_3" if sofa_W == 7.0 else "sofa_2", sofa_W, 3.0, _side_rank(p))
        if sofa is None:
            p.unplaced.pop()
            sofa, sside = p.against_wall("sofa_2", 5.0, 3.0, _side_rank(p))
        if sofa is not None:
            bb = (sofa["x"], sofa["y"], sofa["x"] + sofa["w"], sofa["y"] + sofa["h"])
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            fwd = {"S": (0, 1), "N": (0, -1), "W": (1, 0), "E": (-1, 0)}[sside]
            depth_room = _depth_avail(p.clear, sside)
            gap = 1.5
            ct_c = (cx + fwd[0] * (1.5 + gap + 1.0), cy + fwd[1] * (1.5 + gap + 1.0))
            if depth_room >= 3.0 + gap + 2.0 + 2.5:
                p.free("coffee_table", 4.0 if sofa_W == 7.0 else 3.0, 2.0, _SIDE_FACING[sside], ct_c, radius=1.0)
            opp = _OPPOSITE[sside]
            if cat == "lounge":
                tv, _ = p.against_wall("tv_console", 5.0, 1.5, [opp] + [s for s in ("S", "N", "W", "E") if s not in (opp, sside)],
                                       align="center")
                if tv is None:
                    p.unplaced.pop()
            else:
                if depth_room >= 3.0 + gap + 2.0 + gap + 3.0:
                    opp_sofa, _ = p.against_wall("sofa_2", 5.0, 3.0, [opp], align="center")
                    if opp_sofa is None:
                        p.unplaced.pop()
                for perp in ([s for s in ("S", "N", "W", "E") if s not in (sside, opp)]):
                    ch, _ = p.against_wall("armchair", 2.75, 2.75, [perp], align="center")
                    if ch is None:
                        p.unplaced.pop()
            if "DINING" in room["name"] or _requested(room, "dining"):
                _place_dining(p)

    elif cat == "study":
        it, _ = p.against_wall("study_desk", 4.0, 2.0, _side_rank(p), align="center")
        if it is None:
            p.unplaced.pop()
        for L in (5.0, 4.0, 3.0):
            sh, _ = p.against_wall("bookshelf", L, 1.25, _side_rank(p, prefer_opposite_door=False), tall=True, align="start")
            if sh is not None:
                break
            p.unplaced.pop()

    elif cat == "dining":
        _place_dining(p)

    elif cat == "kitchen":
        _place_kitchen(p, my_wins)

    elif cat == "bath":
        _place_bath(p, area)

    elif cat == "porch":
        _place_cars(p, room)

    elif cat == "dressing" and "STORE" not in room["name"] and "PRAYER" not in room["name"]:
        for L in (5.0, 4.0, 3.0):
            wr, _ = p.against_wall("wardrobe", L, 2.0, _side_rank(p, prefer_opposite_door=False), tall=True, align="start")
            if wr is not None:
                break
            p.unplaced.pop()

    elif cat == "room" and "PRAYER" in room["name"]:
        # Prayer mats laid towards the Qibla (west in Pakistan; plan north is up, so west is -x)
        cx, cy = (clear[0] + clear[2]) / 2.0, (clear[1] + clear[3]) / 2.0
        n_mats = 2 if cl >= 6.0 and cw >= 5.5 else 1
        for k in range(n_mats):
            off = 0.0 if n_mats == 1 else (-1.4 if k == 0 else 1.4)
            if p.free("prayer_mat", 2.0, 3.6, "W", (cx, cy + off), radius=4.0) is None and k > 0:
                p.unplaced.pop()          # the second mat is optional; a missing first mat is reported

    elif cat == "outdoor":
        nm = room["name"]
        if any(k in nm for k in ("LAWN", "GARDEN")):
            r = min(1.25, min(cw, cl) * 0.22)
            if r >= 0.6:
                for (tx, ty) in ((clear[0] + r + 0.3, clear[1] + r + 0.3), (clear[2] - r - 0.3, clear[3] - r - 0.3)):
                    bb = (tx - r, ty - r, tx + r, ty + r)
                    if p._ok(bb):
                        p.add("tree", bb, "N", 2 * r, 2 * r)

    # A prayer mat asked for in any other room (e.g. a prayer corner in the drawing room), towards the Qibla
    if _requested(room, "prayer_mat") and not (cat == "room" and "PRAYER" in room["name"]) and is_enclosed(cat):
        cx, cy = (clear[0] + clear[2]) / 2.0, (clear[1] + clear[3]) / 2.0
        p.free("prayer_mat", 2.0, 3.6, "W", (cx, cy), radius=max(cw, cl))

    return p.items, p.unplaced


def _place_dining(p: _Placer):
    cw, cl = p.clear[2] - p.clear[0], p.clear[3] - p.clear[1]
    cx, cy = (p.clear[0] + p.clear[2]) / 2, (p.clear[1] + p.clear[3]) / 2
    # Prefer the half of the room away from existing items
    if p.items:
        ix = sum(i["x"] + i["w"] / 2 for i in p.items) / len(p.items)
        iy = sum(i["y"] + i["h"] / 2 for i in p.items) / len(p.items)
        cx = cx + (cx - ix) * 0.5
        cy = cy + (cy - iy) * 0.5
    facing = "N" if cw >= cl else "E"
    for W, D, t in ((6.0, 6.5, "dining_6"), (4.0, 6.0, "dining_4")):
        it = p.free(t, W, D, facing, (cx, cy), radius=4.0)
        if it is not None:
            return it
        p.unplaced.pop()
    p.unplaced.append("dining_table")
    return None


def _place_kitchen(p: _Placer, my_wins):
    depth = 2.0
    c = p.clear
    sides = ["S", "N", "W", "E"]

    def free_runs(side):
        """Fully clear rectangular counter runs along one wall (obstacles projected onto the wall axis)."""
        sb = _strip(c, side, depth)
        strip = box(*sb)
        horiz = side in ("S", "N")
        lo_a, hi_a = (sb[0], sb[2]) if horiz else (sb[1], sb[3])
        blocked = []
        for o in p.hard:
            if o.is_empty:
                continue
            inter = strip.intersection(o)
            if inter.area <= 0.01:
                continue
            bx1, by1, bx2, by2 = inter.bounds
            blocked.append((bx1, bx2) if horiz else (by1, by2))
        blocked.sort()
        runs, cur = [], lo_a
        for bs, be in blocked:
            if bs > cur:
                runs.append((cur, bs))
            cur = max(cur, be)
        if hi_a > cur:
            runs.append((cur, hi_a))
        out = []
        for a_, b_ in runs:
            if b_ - a_ >= 2.0:
                bb = (a_, sb[1], b_, sb[3]) if horiz else (sb[0], a_, sb[2], b_)
                out.append((b_ - a_, bb))
        return sorted(out, key=lambda r: -r[0])

    win_sides = p.window_sides
    ranked = sorted(sides, key=lambda s: (0 if s in win_sides else 1, -(free_runs(s)[0][0] if free_runs(s) else 0)))
    placed_runs = []
    for s in ranked:
        runs = free_runs(s)
        if not runs:
            continue
        length, bb = runs[0]
        if placed_runs:
            # second run must be perpendicular (L-shape) and not overlap the first
            if s in (placed_runs[0][0], _OPPOSITE[placed_runs[0][0]]):
                continue
        poly = box(*bb)
        if _collides(poly, [box(*r[1]) for r in placed_runs]):
            poly = poly.difference(unary_union([box(*r[1]) for r in placed_runs]))
            if poly.is_empty or poly.geom_type != "Polygon":
                continue
            bb = poly.bounds
        p.add("counter", bb, _SIDE_FACING[s], (bb[2] - bb[0]) if s in ("S", "N") else (bb[3] - bb[1]), depth)
        placed_runs.append((s, bb))
        if len(placed_runs) == 2:
            break
    if not placed_runs:
        p.unplaced.append("kitchen_counter")
        return
    # Fixtures sit ON the counters (drawn over them, not collision items)
    s0, bb0 = placed_runs[0]
    run_len0 = (bb0[2] - bb0[0]) if s0 in ("S", "N") else (bb0[3] - bb0[1])
    sink_w, hob_w = 3.0, 2.5
    sink_center = None
    for w in my_wins:
        if _sides_of(p.room, [w]) == [s0]:
            sink_center = (w["s"] + w["e"]) / 2.0
    run_lo = bb0[0] if s0 in ("S", "N") else bb0[1]
    run_hi = bb0[2] if s0 in ("S", "N") else bb0[3]
    if sink_center is None:
        sink_center = run_hi - sink_w / 2 - 0.3
    sink_center = max(run_lo + sink_w / 2 + 0.1, min(run_hi - sink_w / 2 - 0.1, sink_center))

    def on_run(side, bb, center, w, itype):
        if side in ("S", "N"):
            fb = (center - w / 2, bb[1] + 0.2, center + w / 2, bb[3] - 0.2)
        else:
            fb = (bb[0] + 0.2, center - w / 2, bb[2] - 0.2, center + w / 2)
        p.items.append({"type": itype, "x": round(fb[0], 3), "y": round(fb[1], 3), "w": round(fb[2] - fb[0], 3),
                        "h": round(fb[3] - fb[1], 3), "facing": _SIDE_FACING[side], "W": w, "D": depth - 0.4,
                        "room_id": p.room["id"], "on_counter": True})

    if run_len0 >= sink_w + 0.4:
        on_run(s0, bb0, sink_center, sink_w, "sink")
    if len(placed_runs) > 1:
        s1, bb1 = placed_runs[1]
        lo1 = bb1[0] if s1 in ("S", "N") else bb1[1]
        hi1 = bb1[2] if s1 in ("S", "N") else bb1[3]
        if hi1 - lo1 >= hob_w + 0.6:
            on_run(s1, bb1, (lo1 + hi1) / 2.0, hob_w, "hob")
    else:
        if run_lo + hob_w + 0.4 < sink_center - sink_w / 2 - 1.5:
            on_run(s0, bb0, run_lo + hob_w / 2 + 0.4, hob_w, "hob")
        elif sink_center + sink_w / 2 + 1.5 + hob_w < run_hi:
            on_run(s0, bb0, run_hi - hob_w / 2 - 0.4, hob_w, "hob")
    fr, _ = p.against_wall("fridge", 2.5, 2.5, _side_rank(p, prefer_opposite_door=False), tall=True, align="start")
    if fr is None:
        p.unplaced.pop()


def _place_bath(p: _Placer, area: float):
    c = p.clear
    cw, cl = c[2] - c[0], c[3] - c[1]
    door_side = p.door_sides[0] if p.door_sides else "S"
    far = _OPPOSITE[door_side]
    perp = [s for s in ("S", "N", "W", "E") if s not in (door_side, far)]
    if area >= 30 and min(cw, cl) >= 4.2:
        sh = min(3.0, min(cw, cl) - 1.0)
        it, _ = p.against_wall("shower", sh, sh, [far] + perp, align="end")
        if it is None:
            p.unplaced.pop()
            it, _ = p.against_wall("shower", sh, sh, [far] + perp, align="start")
            if it is None:
                p.unplaced.pop()
    wc, _ = p.against_wall("wc", 1.6, 2.4, perp + [far], align="center")
    if wc is None:
        p.unplaced.pop()
        wc, _ = p.against_wall("wc", 1.5, 2.2, perp + [far, door_side], align="center")
        if wc is None:
            p.unplaced.pop()
            p.unplaced.append("wc")
    bs, _ = p.against_wall("basin", 1.75, 1.4, perp + [far, door_side], align="center")
    if bs is None:
        p.unplaced.pop()
        bs, _ = p.against_wall("basin", 1.4, 1.2, perp + [far, door_side], align="center")
        if bs is None:
            p.unplaced.pop()
            p.unplaced.append("basin")


def _place_cars(p: _Placer, room):
    c = p.clear
    cw, cl = c[2] - c[0], c[3] - c[1]
    # Cars park nose-in, length along the plot depth (gate on the front boundary)
    if cl >= 14.5:
        CW, CL, t = 6.0, 15.0, "car"
    elif cl >= 12.5:
        CW, CL, t = 5.5, 12.5, "car_compact"
    else:
        return
    n = 2 if cw >= 2 * CW + 3.5 and room.get("w_ft", 0) >= 16 else 1
    cy = (c[1] + c[3]) / 2.0
    if n == 1:
        it = p.free(t, CW, CL, "S", ((c[0] + c[2]) / 2.0, cy), radius=4.0)
        if it is None and t == "car":   # a full-size car would block a door approach: try a compact car
            p.unplaced.pop()
            p.free("car_compact", 5.5, 12.5, "S", ((c[0] + c[2]) / 2.0, cy), radius=4.0)
    else:
        gap = (cw - 2 * CW) / 3.0
        for k in range(2):
            cx = c[0] + gap * (k + 1) + CW * k + CW / 2.0
            if p.free(t, CW, CL, "S", (cx, cy), radius=3.0) is None and t == "car":
                p.unplaced.pop()
                p.free("car_compact", 5.5, 12.5, "S", (cx, cy), radius=3.0)


def furnish_floor(rooms, doors, windows) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    building = _building_poly(rooms)
    items, unplaced = [], []
    for r in rooms:
        its, miss = furnish_room(r, building, doors, windows)
        items.extend(its)
        for m in miss:
            unplaced.append({"room": r["id"], "item": m})
    return items, unplaced


# ---------------------------------------------------------------------------
# 7. LEGACY FIELDS (frontend FloorPlanViewer reads room.door / room.windows)
# ---------------------------------------------------------------------------

def _legacy_opening(room, op):
    sides = _sides_of(room, [op])
    if not sides:
        return None
    side = sides[0]
    wall = {"S": "south", "N": "north", "W": "west", "E": "east"}[side]
    origin = float(room["x_ft"]) if side in ("S", "N") else float(room["y_ft"])
    return {"wall": wall, "offset_ft": round(op["s"] - origin, 2), "width_ft": round(op["width"], 2)}


def attach_legacy_fields(rooms, doors, windows, furniture):
    for r in rooms:
        primary = next((d for d in doors if d["room_id"] == r["id"]), None) or \
            next((d for d in doors if d["from_id"] == r["id"]), None)
        if primary:
            lg = _legacy_opening(r, primary)
            if lg:
                lg["swing"] = "double" if primary["kind"] == "main_double" else (
                    "none" if primary["kind"] == "arch" else ("in" if primary["room_id"] == r["id"] else "out"))
                r["door"] = lg
        else:
            r["door"] = None
        r["windows"] = [lg for lg in (_legacy_opening(r, w) for w in windows if w["room_id"] == r["id"]) if lg]
        r["furniture_layout"] = [f for f in furniture if f["room_id"] == r["id"]]


# ---------------------------------------------------------------------------
# 8. VALIDATION (Shapely + NetworkX)
# ---------------------------------------------------------------------------

def _issue(code, level_s, floor, room, msg):
    return {"code": code, "level": level_s, "floor": floor, "room": room, "message": msg}


def build_circulation_graph(rooms, doors, level, plot_l) -> nx.Graph:
    G = nx.Graph()
    for r in rooms:
        G.add_node(r["id"], category=r["category"])
    for d in doors:
        G.add_edge(d["room_id"], d["from_id"], kind=d["kind"])
    walkable_open = {"porch", "outdoor"}
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            if a["category"] in walkable_open and b["category"] in walkable_open and shared_edge(a, b):
                G.add_edge(a["id"], b["id"], kind="open")
    if level == 0:
        G.add_node("STREET")
        for r in rooms:
            if r["category"] in walkable_open and float(r["y_ft"]) < EPS:
                G.add_edge("STREET", r["id"], kind="gate")
    else:
        G.add_node("STAIR_LINK")
        for r in rooms:
            if r["category"] == "stair":
                G.add_edge("STAIR_LINK", r["id"], kind="stair")
    return G


def validate_floor(rooms, doors, windows, furniture, plot_w, plot_l, front_sb, rear_sb, level) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    boxes = [_box(r) for r in rooms]
    plot = box(0, 0, plot_w, plot_l)

    # Tiling
    union = unary_union(boxes) if boxes else Polygon()
    gap = plot.difference(union).area
    if gap > 1.0:
        out.append(_issue("TILING_GAP", "error", level, None, f"{gap:.0f} sq ft of the plot is not assigned to any space"))
    for i in range(len(rooms)):
        for j in range(i + 1, len(rooms)):
            ov = boxes[i].intersection(boxes[j]).area
            if ov > 0.5:
                out.append(_issue("OVERLAP", "error", level, rooms[i]["id"],
                                  f"{rooms[i]['id']} overlaps {rooms[j]['id']} by {ov:.0f} sq ft"))
    outside = union.difference(plot).area
    if outside > 0.5:
        out.append(_issue("OUTSIDE_PLOT", "error", level, None, f"{outside:.0f} sq ft of rooms lie outside the plot"))

    # Setbacks (only checked if the client requested a setback > 0)
    for r in rooms:
        if not is_enclosed(r["category"]):
            continue
        x1, y1, x2, y2 = _rect(r)
        if front_sb > 0.1 and y1 < front_sb - 0.1 and r["category"] == "stair":
            out.append(_issue("STAIR_IN_SETBACK", "warning", level, r["id"],
                              f"{r['id']} (STAIR) stands in the front setback (porch / drive way stair)"))
        elif front_sb > 0.1 and y1 < front_sb - 0.1:
            out.append(_issue("SETBACK_FRONT", "error", level, r["id"],
                              f"{r['id']} ({r['name']}) starts {y1:.1f} ft from the front boundary - inside the "
                              f"{front_sb:.1f} ft front setback"))
        if rear_sb > 0.1 and y2 > plot_l - rear_sb + 0.1:
            out.append(_issue("SETBACK_REAR", "error", level, r["id"],
                              f"{r['id']} ({r['name']}) extends into the {rear_sb:.1f} ft rear setback (ends at {y2:.1f} of {plot_l:.1f} ft)"))

    # Doors never on side/rear party boundaries (front boundary y=0 is allowed for street entrance doors)
    for d in doors:
        if d.get("from_id") == "STREET" and d["orient"] == "h" and abs(d["coord"]) < EPS:
            continue
        if _on_plot_boundary(d, plot_w, plot_l):
            out.append(_issue("DOOR_ON_BOUNDARY", "error", level, d["room_id"], f"door {d['id']} sits on the plot boundary"))
    for w in windows:
        c = w["coord"]
        if w["orient"] == "v" and (abs(c) < EPS or abs(c - plot_w) < EPS):
            out.append(_issue("WINDOW_ON_PARTY_WALL", "error", level, w["room_id"], f"window {w['id']} is on a party wall"))

    # Main entrance
    if level == 0 and not any(d["kind"] in ("main", "main_double") or d.get("from_id") == "STREET" for d in doors):
        has_front_door = any(
            d for d in doors
            if any(r["id"] == d["from_id"] and r["category"] in ("porch", "outdoor") for r in rooms)
        )
        if not has_front_door:
            out.append(_issue("NO_MAIN_ENTRANCE", "error", level, None,
                              "no door leads from the street / car porch / lawn into the house (main entrance missing)"))

    # Reachability & walk-through checks
    G = build_circulation_graph(rooms, doors, level, plot_l)
    root = "STREET" if level == 0 else "STAIR_LINK"
    stairs = [r for r in rooms if r["category"] == "stair"]
    if level > 0 and not stairs:
        out.append(_issue("STAIR_MISSING", "error", level, None, "upper floor has no staircase - it cannot be reached"))
    else:
        reach = nx.node_connected_component(G, root) if root in G else set()
        need = [r for r in rooms if is_enclosed(r["category"])] + \
               [r for r in rooms if any(k in r["name"] for k in ("BALCONY", "TERRACE"))]
        for r in need:
            if r["id"] not in reach:
                out.append(_issue("UNREACHABLE", "error", level, r["id"],
                                  f"{r['id']} ({r['name']}) cannot be reached from the {'street entrance' if level == 0 else 'staircase'}"))
        cat_of = {r["id"]: r["category"] for r in rooms}
        for r in rooms:
            if r["category"] not in ("bedroom", "bath") or r["id"] not in reach:
                continue
            H = G.copy()
            H.remove_node(r["id"])
            reach2 = nx.node_connected_component(H, root) if root in H else set()
            for q in reach:
                if q in (r["id"], root) or q in reach2 or q not in cat_of:
                    continue
                if not is_enclosed(cat_of[q]):
                    continue
                if r["category"] == "bedroom" and cat_of[q] in ("bath", "dressing"):
                    continue
                out.append(_issue("WALK_THROUGH_" + r["category"].upper(), "error", level, q,
                                  f"{q} is reached by walking through {r['category']} {r['id']} ({r['name']})"))
        # The stair rectangle is filled with steps: it is entered at its foot and left at the top. On the ground
        # floor nothing may lie behind it (a store under the flight is the one exception).
        if level == 0:
            name_of = {r["id"]: r["name"] for r in rooms}
            for st in stairs:
                if st["id"] not in reach:
                    continue
                H = G.copy()
                H.remove_node(st["id"])
                reach2 = nx.node_connected_component(H, root) if root in H else set()
                cut = [q for q in reach if q not in (st["id"], root) and q not in reach2 and q in cat_of
                       and is_enclosed(cat_of[q]) and "STORE" not in name_of[q]]
                if cut:
                    names = ", ".join(sorted(name_of[q] for q in cut)[:5])
                    out.append(_issue("WALK_THROUGH_STAIR", "error", level, st["id"],
                                      f"{names} can only be reached by walking across {st['name']} - the stair "
                                      f"rectangle is filled with steps, nobody can cross it. Fix: connect the entrance "
                                      f"side to the lounge / lobby directly (a door or arch on a wall they share), and "
                                      f"let the stair open onto that shared space from one side only"))

    # Daylight: a habitable room without a window is a physical failure, whatever the brief asks for
    win_rooms = {w["room_id"] for w in windows}
    _root = {r["id"]: (r.get("part_of") or r["id"]) for r in rooms}
    lit_spaces = {_root.get(rid) for rid in win_rooms}
    for r in rooms:
        if r["id"] in win_rooms or _root[r["id"]] in lit_spaces:    # a part of a space lit through its other part
            continue
        if r["category"] in HABITABLE:
            open_walls = [(o, shared_edge(r, o)) for o in rooms if not is_enclosed(o["category"]) and shared_edge(r, o)]
            if open_walls:
                o, e = max(open_walls, key=lambda t: t[1][3] - t[1][2])
                out.append(_issue("LANDLOCKED", "error", level, r["id"],
                                  f"{r['id']} ({r['name']}) touches {o['name']} for {e[3] - e[2]:.1f} ft and its door "
                                  f"takes that wall - no window fits"))
            else:
                out.append(_issue("LANDLOCKED", "error", level, r["id"],
                                  f"{r['id']} ({r['name']}) has no wall on open air - it gets no window"))
        elif r["category"] == "bath":
            out.append(_issue("BATH_NO_VENT", "warning", level, r["id"],
                              f"{r['id']} ({r['name']}) has no outside wall - needs an exhaust fan / ventilation duct"))

    # The stair of a family house is climbed from inside it (reported as a warning; the designer turns it into a
    # failure unless the brief asks for a separate outside entrance to the upper floors)
    if level == 0:
        by_id_ = {r["id"]: r for r in rooms}
        for st in stairs:
            sides = [by_id_.get(d["from_id"] if d["room_id"] == st["id"] else d["room_id"])
                     for d in doors if st["id"] in (d.get("room_id"), d.get("from_id"))]
            sides = [o for o in sides if o is not None]
            if sides and not any(is_enclosed(o["category"]) or "GALLERY" in o["name"] or "VERANDAH" in o["name"]
                                 for o in sides):
                out.append(_issue("STAIR_OUTSIDE_ONLY", "warning", level, st["id"],
                                  f"{st['name']} opens only onto {', '.join(o['name'] for o in sides)} - the family "
                                  f"would leave the house to go upstairs. Fix: place the stair beside the lounge / "
                                  f"lobby / corridor and write its door: to that space"))

    # Floor left open (ground floor): strips, shafts and open passages take width away from the rooms
    if level == 0:
        soft = ("LAWN", "GARDEN", "TERRACE", "BALCONY", "WASH", "DRIVE", "PORCH", "LAUNDRY", "DECK", "POOL")
        left_open = [r for r in rooms if r["category"] == "ots" or
                     (r["category"] == "outdoor" and not any(k in r["name"] for k in soft))]
        open_area = sum(float(r["w_ft"]) * float(r["l_ft"]) for r in left_open)
        if left_open and open_area > 0.15 * plot_w * plot_l:
            big = max(left_open, key=lambda r: float(r["w_ft"]) * float(r["l_ft"]))
            out.append(_issue("BALANCE", "warning", level, big["id"],
                              f"{open_area:.0f} sq ft of this floor ({open_area / (plot_w * plot_l) * 100:.0f}% of the plot) "
                              f"is left open as strips / shafts / open passages "
                              f"({', '.join(sorted({r['name'] for r in left_open})[:5])}). A window only needs a shaft about "
                              f"4 x 5 ft beside the room; give the rest of that width to the rooms"))

    # Stair size
    for s in stairs:
        a, b = sorted((float(s["w_ft"]), float(s["l_ft"])))
        if a < 3.5 or b < 9.0:
            out.append(_issue("STAIR_TOO_SMALL", "error", level, s["id"],
                              f"staircase {s['id']} is {ft_in(s['w_ft'])} x {ft_in(s['l_ft'])}; a stair a person can climb needs at least 3'-6\" x 9'-0\""))

    # Car porch size note
    if level == 0:
        for r in rooms:
            if r["category"] == "porch" and (float(r["w_ft"]) < 10.0 or float(r["l_ft"]) < 16.0):
                out.append(_issue("CAR_PORCH_TOO_SMALL", "warning", level, r["id"],
                                  f"{r['id']} ({r['name']}) is {ft_in(r['w_ft'])} x {ft_in(r['l_ft'])} - compact porch"))

    # Wasted space: service rooms far larger than they need to be
    caps = {"STORE": 60.0, "DRESS": 70.0}
    for r in rooms:
        area = float(r["w_ft"]) * float(r["l_ft"])
        cat, nm = r["category"], r["name"]
        limit = None
        if cat == "dressing":
            limit = next((v for k, v in caps.items() if k in nm), 70.0)
        elif cat == "bath":
            limit = 75.0
        elif cat == "circulation" and any(k in nm for k in ("ENT", "FOYER", "ENTRANCE")):
            limit = 90.0
        # advice, not an error: the client's brief may ask for a big room
        if limit and area > limit:
            out.append(_issue("WASTED_SPACE", "warning", level, r["id"],
                              f"{r['id']} ({nm}) is {area:.0f} sq ft - more than {limit:.0f} sq ft for this use; unless "
                              f"the brief asks for it, shrink it and give the area to a habitable room"))
        if cat == "circulation" and min(float(r["w_ft"]), float(r["l_ft"])) > 7.5 and "ENT" not in nm:
            out.append(_issue("WASTED_SPACE", "warning", level, r["id"],
                              f"{r['id']} ({nm}) passage is {ft_in(min(float(r['w_ft']), float(r['l_ft'])))} wide - "
                              f"wider than walking needs; give the extra width to the rooms beside it"))

    # Balance (relative): the floor is a fixed amount of area - what one space takes, another loses
    def _area(r):
        return float(r["w_ft"]) * float(r["l_ft"])
    by_rid = {r["id"]: r for r in rooms}
    lounge_area: Dict[str, float] = {}
    for r in rooms:
        if r["category"] == "lounge":
            k = r.get("part_of") or r["id"]
            lounge_area[k] = lounge_area.get(k, 0.0) + _area(r)
    for r in rooms:
        cat, nm = r["category"], r["name"]
        if cat == "stair" and _area(r) > 120.0:
            out.append(_issue("WASTED_SPACE", "warning", level, r["id"],
                              f"{r['id']} ({nm}) is {ft_in(r['w_ft'])} x {ft_in(r['l_ft'])} = {_area(r):.0f} sq ft - its "
                              f"steps use about 7 x 10 ft; the rest is floor nobody can stand on. Shrink the stair "
                              f"rectangle and give the area to the lounge or a room beside it"))
        elif cat == "kitchen" and "DIRTY" not in nm and lounge_area and _area(r) > max(lounge_area.values()):
            out.append(_issue("BALANCE", "warning", level, r["id"],
                              f"{r['id']} ({nm}) is {_area(r):.0f} sq ft - larger than the lounge the family sits in "
                              f"({max(lounge_area.values()):.0f} sq ft); unless the brief asks for a big kitchen, move "
                              f"the cut between them"))
        elif cat == "bath":
            host = by_rid.get(r.get("door_from"))
            if host is not None and host["category"] == "bedroom" and _area(r) > 0.45 * _area(host):
                out.append(_issue("BALANCE", "warning", level, r["id"],
                                  f"{r['id']} ({nm}) is {_area(r):.0f} sq ft - nearly half of its bedroom {host['name']} "
                                  f"({_area(host):.0f} sq ft); narrow the bath and give the strip to the bedroom or put "
                                  f"a dressing / store beside the bath"))
        elif cat == "bedroom" and min(float(r["w_ft"]), float(r["l_ft"])) < 9.0:
            a_ = min(float(r["w_ft"]), float(r["l_ft"]))
            out.append(_issue("TIGHT_ROOM", "warning", level, r["id"],
                              f"{r['id']} ({nm}) is only {ft_in(a_)} across before its walls are taken off - a bed is "
                              f"6'-9\" long, so almost nothing is left to walk past its foot; widen the room unless "
                              f"the brief gives this size"))

    # Proportion (relative - no fixed size): a long thin habitable room works like a corridor
    _part_ids = {r["id"] for r in rooms if r.get("part_of")} | {r.get("part_of") for r in rooms if r.get("part_of")}
    for r in rooms:
        if r["category"] in HABITABLE and r["id"] not in _part_ids:     # a part is not the whole space
            a, b = sorted((float(r["w_ft"]), float(r["l_ft"])))
            lim = 3.0 if r["category"] == "kitchen" else 2.5
            if a > 0 and b / a > lim:
                out.append(_issue("PROPORTION", "warning", level, r["id"],
                                  f"{r['id']} ({r['name']}) is {ft_in(a)} x {ft_in(b)} - {b / a:.1f} times longer than "
                                  f"wide; reshape it nearer to square (or split off a bath / store / dressing)"))

    # Minimum sizes (warnings)
    mins = {"bedroom": (9.0, 100.0), "bath": (4.0, 20.0), "kitchen": (6.5, 56.0), "lounge": (10.0, 110.0),
            "drawing": (10.0, 110.0), "circulation": (3.5, 0.0)}
    for r in rooms:
        if r["category"] in mins:
            mn, ma = mins[r["category"]]
            if "DIRTY" in r["name"] or "POWDER" in r["name"]:
                mn, ma = 4.0, 20.0
            w_, l_ = float(r["w_ft"]), float(r["l_ft"])
            if min(w_, l_) < mn or w_ * l_ < ma:
                out.append(_issue("UNDERSIZED", "warning", level, r["id"],
                                  f"{r['id']} ({r['name']}) is {ft_in(w_)} x {ft_in(l_)} - below the usual minimum ({mn:.1f} ft wide, {ma:.0f} sq ft)"))

    # Furniture must never sit in a door swing (sanity check of the placer)
    swings = [door_swing_polygon(d) for d in doors]
    for f in furniture:
        if f.get("on_counter") or f["type"] == "tree":
            continue
        fb = box(f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])
        if _collides(fb, swings, tol=0.1):
            out.append(_issue("FURNITURE_IN_SWING", "error", level, f["room_id"], f"{f['type']} intrudes into a door swing"))
    if not SIZE_ADVICE:
        out = [i for i in out if i["code"] not in _SIZE_ADVICE_CODES]
    return out


def validate_vertical(floors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    if len(floors) < 2:
        return out
    gf = floors[0]["rooms"]
    gf_stairs = [r for r in gf if r["category"] == "stair"]
    if not gf_stairs:
        out.append(_issue("STAIR_MISSING", "error", 0, None, "multi-storey house but the ground floor has no staircase"))
        return out
    s0 = _box(gf_stairs[0])
    gf_open = unary_union([_box(r) for r in gf if r["category"] in ("outdoor", "ots", "pool")]) if gf else Polygon()
    gf_ots = [r for r in gf if r["category"] == "ots"]
    for idx, fl in enumerate(floors[1:], start=1):
        lvl = fl["level"]
        # rooms must stand on built space of the floor directly below (roof rooms on the top floor)
        below = floors[idx - 1]["rooms"]
        below_open = unary_union([_box(r) for r in below if r["category"] in ("outdoor", "ots", "pool")]) \
            if below else Polygon()
        gf_open_l = unary_union([gf_open, below_open])
        st = [r for r in fl["rooms"] if r["category"] == "stair"]
        if st:
            best = max(st, key=lambda r: _box(r).intersection(s0).area)
            inter = _box(best).intersection(s0).area
            iou = inter / max(1e-6, _box(best).union(s0).area)
            if iou < 0.8:
                g = gf_stairs[0]
                out.append(_issue("STAIR_MISALIGNED", "error", lvl, best["id"],
                                  f"staircase on level {lvl} is not stacked over the ground-floor stair "
                                  f"(GF stair at x={g['x_ft']:.1f}, y={g['y_ft']:.1f}, {g['w_ft']:.1f} x {g['l_ft']:.1f} ft; overlap {iou:.0%}). "
                                  f"Repeat the same band/column sizes so the stair occupies the identical rectangle"))
        for r in fl["rooms"]:
            if not is_enclosed(r["category"]):
                continue
            unsupported = _box(r).intersection(gf_open_l).area
            if unsupported > 2.0:
                out.append(_issue("NO_STRUCTURE_BELOW", "error", lvl, r["id"],
                                  f"{r['id']} ({r['name']}) is built over {unsupported:.0f} sq ft of open ground-floor space "
                                  f"(lawn/OTS/setback) with no wall or column below"))
        for o in gf_ots:
            covered = sum(_box(o).intersection(_box(r)).area for r in fl["rooms"] if is_enclosed(r["category"]))
            if covered > 2.0:
                out.append(_issue("OTS_COVERED", "warning", lvl, o["id"],
                                  f"ground-floor OTS {o['id']} is roofed over by level-{lvl} rooms ({covered:.0f} sq ft) - it no longer ventilates"))
    return out


def _program_check(floors, bedrooms: int, bathrooms: int) -> List[Dict[str, Any]]:
    out = []
    beds = sum(1 for f in floors for r in f["rooms"] if r["category"] == "bedroom" and "SERVANT" not in r["name"]
               and "STUDY" not in r["name"])
    baths = sum(1 for f in floors for r in f["rooms"] if r["category"] == "bath")
    if bedrooms and beds != bedrooms:
        out.append(_issue("PROGRAM_BEDROOMS", "warning", None, None, f"{beds} bedrooms designed, {bedrooms} requested"))
    if bathrooms and baths < bathrooms:
        out.append(_issue("PROGRAM_BATHS", "warning", None, None, f"{baths} bathrooms designed, {bathrooms} requested"))
    return out


# ---------------------------------------------------------------------------
# 9. MASTER ENTRY POINT
# ---------------------------------------------------------------------------

def analyse_layout(layout: Dict[str, Any], plot_w: float, plot_l: float, front_sb: float, rear_sb: float,
                   bedrooms: int = 0, bathrooms: int = 0) -> Dict[str, Any]:
    """
    Converts a Gemini layout (slicing trees, or legacy room lists with coordinates) into
    exact CAD geometry and validates it. Returns a deep-copied layout with, per floor:
    ``rooms`` (exact rectangles + legacy door/windows fields), ``doors``, ``windows``,
    ``furniture`` and a top-level ``validation`` report.
    """
    out = copy.deepcopy(layout)
    out["plot_width_ft"] = float(plot_w)
    out["plot_length_ft"] = float(plot_l)
    out["front_setback_ft"] = float(front_sb)
    out["rear_setback_ft"] = float(rear_sb)
    issues: List[Dict[str, Any]] = []
    fixes: List[str] = []

    floors = out.get("floors") or []
    for fi, fl in enumerate(floors):
        level = int(fl.get("level", fi)) if str(fl.get("level", fi)).lstrip("-").isdigit() else fi
        fl["level"] = level
        fl.setdefault("label", "GROUND FLOOR" if level == 0 else ("FIRST FLOOR" if level == 1 else f"FLOOR {level}"))
        tree = fl.get("layout")
        if isinstance(tree, dict):
            rooms = build_rooms_from_tree(tree, plot_w, plot_l, level)
            fl["geometry_source"] = "slicing_tree"
        else:
            rooms = copy.deepcopy(fl.get("rooms") or [])
            for r in rooms:
                for k, dflt in (("x_ft", 0.0), ("y_ft", 0.0), ("w_ft", 10.0), ("l_ft", 10.0)):
                    r[k] = float(r.get(k, dflt))
                r["level"] = level
            fl["geometry_source"] = "llm_coordinates"
        _normalise_ids(rooms, level)
        doors, door_issues, door_fixes = compute_doors(rooms, plot_w, plot_l, level)
        windows = compute_windows(rooms, doors, plot_w, plot_l, level)
        furniture, unplaced = furnish_floor(rooms, doors, windows)
        attach_legacy_fields(rooms, doors, windows, furniture)
        fl["rooms"] = rooms
        fl["doors"] = doors
        fl["windows"] = windows
        fl["furniture"] = furniture
        issues.extend(door_issues)
        fixes.extend(door_fixes)
        issues.extend(validate_floor(rooms, doors, windows, furniture, plot_w, plot_l, front_sb, rear_sb, level))
        # a space written in several parts is furnished as one space: only its largest part must hold the furniture
        _grp: Dict[str, List[Dict[str, Any]]] = {}
        for r_ in rooms:
            _grp.setdefault(r_.get("part_of") or r_["id"], []).append(r_)
        _minor = {m["id"] for ms in _grp.values() if len(ms) > 1
                  for m in ms if m is not max(ms, key=lambda q: float(q["w_ft"]) * float(q["l_ft"]))}
        for u in unplaced:
            if u["room"] in _minor:
                continue
            issues.append(_issue("FURNITURE_UNPLACED", "warning", level, u["room"],
                                 f"{u['item']} omitted in {u['room']} - no position clear of doors/windows"))

    issues.extend(validate_vertical(floors))
    issues.extend(_program_check(floors, bedrooms, bathrooms))
    errors = [i for i in issues if i["level"] == "error"]
    warnings = [i for i in issues if i["level"] == "warning"]
    score = max(0.0, round(1.0 - 0.12 * len(errors) - 0.015 * len(warnings), 3))
    out["validation"] = {
        "status": "PASS" if not errors else "FAIL",
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "auto_fixes": fixes,
        "engine": "plan_geometry_engine (shapely + networkx)",
        "disclaimer": "Software CAD validation only - not structural certification or municipal approval.",
    }
    return out


def format_issues_for_llm(validation: Dict[str, Any], limit: int = 25) -> str:
    lines = []
    for i in validation.get("errors", [])[:limit]:
        where = f"level {i['floor']}" if i.get("floor") is not None else "whole design"
        lines.append(f"- [{i['code']}] ({where}) {i['message']}")
    return "\n".join(lines)
