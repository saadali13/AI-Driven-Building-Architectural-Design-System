"""
ArchiScript — the design script Gemini writes, the engine runs, and the client can edit
=========================================================================================

Instead of a hidden JSON blob, Gemini writes a short, human-readable script that describes
the plan as nested bands (the same slicing-tree model the CAD engine uses). The engine:

  1. parses it (line-numbered errors),
  2. checks the sizes add up (scales them to fit and writes the real sizes back into the script),
  3. runs it through ``plan_geometry_engine`` (walls, doors, windows, furniture, setbacks,
     circulation, daylight, stair stacking) and the client's requirement checklist,
  4. sends every problem back to Gemini *by line number* until the script passes.

The client sees the same script in the UI, can edit it and run it again, or ask in plain words
for a change ("make bed space 2 bigger", "move the kitchen next to the gate") and Gemini edits it.

It is deliberately a small declarative language, not Python: the server never executes code
written by the model or typed by a user.

Example::

    PLOT 53 x 25
    SETBACKS front 7.5 rear 5
    LEVEL 1 "FIRST FLOOR PORTION"
    ROWS
      7.5 | OPEN CORRIDOR | gallery
      12.5 COLS
        4.5 | STAIR | stair | door: OPEN CORRIDOR | gate
        10 | KITCHEN | kitchen | door: OPEN CORRIDOR | furniture: counter, sink, hob, fridge
        ...
      5 | REAR OPEN | open
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from generation.plan_geometry_engine import _allocate, _TYPE_CATEGORY

ROOM_TYPES = [
    "car_porch", "driveway", "lawn", "garden", "entrance", "lobby", "corridor", "gallery", "drawing", "lounge",
    "dining", "kitchen", "dirty_kitchen", "bedroom", "master_bedroom", "servant", "study", "bath", "powder",
    "dressing", "store", "stair", "ots", "balcony", "terrace", "open", "wash_area", "pool", "deck", "prayer",
    "gym", "room",
]
_LEVEL_PREFIX = {0: "gf", 1: "ff", 2: "sf", 3: "tf"}
_SIZE_RE = r"(\d+(?:\.\d+)?)(?:\s*'\s*-?\s*(\d+(?:\.\d+)?)\s*\"?)?'?"

SCRIPT_SPEC = """
=== ARCHISCRIPT - the design language you write (one line per space, NO coordinates) ===
PLOT <width> x <depth>                 width = street frontage, depth = front to back (feet)
SETBACKS front <ft> rear <ft>
LEVEL <n> "<label>"                    0 = ground floor, 1 = first floor ...; write ROOF after the label for a roof level
ROWS                                   root of every level: bands from the STREET (front) to the BACK
  <depth> | <NAME> | <type> | door: <NAME it is entered from> | furniture: a, b
  <depth> COLS                         a band divided side by side, LEFT -> RIGHT
    <width> | <NAME> | <type> | door: <NAME>
    <width> ROWS                       a column divided FRONT -> BACK
      <depth> | <NAME> | <type> | door: <NAME>
FORMAT RULES
* Indent children by 2 spaces under their ROWS / COLS line. Sizes are feet (12.5 or 12'6").
* Inside ROWS the numbers are depths and must add up to the parent's depth (root ROWS = plot depth).
  Inside COLS they are widths and must add up to the parent's width (root width = plot width).
* Every level covers the WHOLE plot. `SETBACKS front <ft> rear <ft>` holds what the client states (0 if none); whatever
  you write there is enforced: no enclosed room may start inside it.
* NAMES are unique on a level, in capitals (BED ROOM 1, BATH 1, DRAWING ROOM ...); door: and arch: use NAMES.
  Only a shared space that runs through several bands (lounge, lobby, corridor, open gallery) may be written as
  several leaves with the SAME NAME in bands that touch: the engine joins the parts and treats them as one space.
* door: = the space you walk in from; it must share a wall at least 3 ft long. If there is no front porch/lawn at y=0, the front entrance space on the street edge can use `door: STREET` (or `gate`). arch: A, B = open arches.
  extra door: A, B = more doors from that room (e.g. a bedroom onto its balcony or terrace).
* Open spaces (gallery, terrace, balcony, lawn, open, ots) never take door: - write door: <open space> on the room
  (or stair) that opens onto them. A room whose only open-air wall also holds its door needs that wall >= 8 ft.
* gate = add this word to the line whose door is the entrance gate (e.g. the stair landing or gallery entry).
* furniture hints: king_bed, queen_bed, single_bed, sofa_bed, wardrobe, dressing_table, study_desk, sofa_3, sofa_2,
  armchair, coffee_table, tv_console, floor_seating (Arab majlis cushions + low table), dining_6, counter, sink, hob,
  fridge, car, prayer_mat.
* types: """ + ", ".join(ROOM_TYPES) + """
  (gallery = open corridor / verandah on open air; open = unbuilt open space; ots = open-to-sky shaft)
HOW TO SEE WHAT TOUCHES (the cutting in point 1, made practical - most door errors come from skipping this)
* Two leaves touch ONLY if they are neighbours inside the same COLS / ROWS group, or they sit in two bands that
  meet AND their x-ranges (for bands stacked front to back) overlap by 3 ft or more. A room NEVER touches a space
  two bands away, and in a column split into ROWS only the first / last leaf touches the band before / after it.
* So above every COLS band of the root ROWS write a comment line with its y-range and every column's x-range:
    # y 18-32 | DRAWING x 0-12 | TV LOUNGE x 12-35
  and write door: X only when X is beside the room in the same band, or in the band directly before / after it
  with overlapping x. Check every door: line against these comments before you answer.
* If the lounge does not reach a room, bring the circulation to the room instead of guessing: extend the lounge
  into that band (same NAME = one space), or run a CORRIDOR down the plot - give each band a column named
  CORRIDOR (about 4 ft wide) at the SAME x; the parts join into one corridor that every room beside it touches.
UPPER LEVELS
* They are entered from the STAIR: the upper lounge / lobby takes door: STAIR.
* Each level is planned for its OWN rooms - a floor is not a copy of the one below unless the client asks for that.
SYNTAX EXAMPLE (30 x 60, two levels - it passes every engine check; it shows the notation and the stacking
only - do NOT copy its rooms or sizes, design from the client's brief):
PLOT 30 x 60
SETBACKS front 7.5 rear 5
LEVEL 0 "GROUND FLOOR"
ROWS
  # y 0-18 | CAR PORCH x 0-11 | FRONT LAWN x 11-30 (y 0-7.5) then ENT LOBBY x 11-16.5, DRAWING ROOM x 16.5-30 (y 7.5-18)
  18 COLS
    11 | CAR PORCH | car_porch | furniture: car
    19 ROWS
      7.5 | FRONT LAWN | lawn
      10.5 COLS
        5.5 | ENT LOBBY | entrance | door: CAR PORCH
        13.5 | DRAWING ROOM | drawing | door: ENT LOBBY | furniture: sofa_3, sofa_2, coffee_table
  # y 18-32 | KITCHEN + OTS x 0-8 | TV LOUNGE x 8-25 (touches ENT LOBBY x 11-16.5 above) | STAIR x 25-30
  14 COLS
    8 ROWS
      9 | KITCHEN | kitchen | door: TV LOUNGE | furniture: counter, sink, hob, fridge
      5 | OTS | ots
    17 | TV LOUNGE | lounge | door: ENT LOBBY | furniture: sofa_3, tv_console
    5 | STAIR | stair | door: TV LOUNGE
  # y 32-50 | BED ROOM 1 x 0-13.5 (lounge above x 8-25: 5.5 ft shared) | BATHS x 13.5-19 | BED ROOM 2 x 19-30 (6 ft shared)
  18 COLS
    13.5 | BED ROOM 1 | bedroom | door: TV LOUNGE | furniture: queen_bed, wardrobe
    5.5 ROWS
      8 | BATH 1 | bath | door: BED ROOM 1
      10 | BATH 2 | bath | door: BED ROOM 2
    11 | BED ROOM 2 | bedroom | door: TV LOUNGE | furniture: queen_bed, wardrobe
  10 | REAR LAWN | lawn
LEVEL 1 "FIRST FLOOR"
ROWS
  18 ROWS
    7.5 | FRONT BALCONY | balcony
    10.5 COLS
      23 | BED ROOM 3 | bedroom | door: UPPER LOUNGE | extra door: FRONT BALCONY | furniture: queen_bed, wardrobe
      7 | BATH 3 | bath | door: BED ROOM 3
  14 COLS
    8 ROWS
      9 | LAUNDRY | wash_area | door: UPPER LOUNGE
      5 | OTS | ots
    17 | UPPER LOUNGE | lounge | door: STAIR | furniture: sofa_3, tv_console
    5 | STAIR | stair | door: UPPER LOUNGE
  18 COLS
    13.5 | BED ROOM 4 | bedroom | door: UPPER LOUNGE | furniture: queen_bed, wardrobe
    5.5 ROWS
      8 | BATH 4 | bath | door: BED ROOM 4
      10 | BATH 5 | bath | door: BED ROOM 5
    11 | BED ROOM 5 | bedroom | door: UPPER LOUNGE | furniture: queen_bed, wardrobe
  10 | REAR OPEN | open
"""


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:28] or "space"


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().upper())


def parse_size(tok: str) -> Optional[float]:
    m = re.fullmatch(r"\s*" + _SIZE_RE + r"\s*", tok or "")
    if not m:
        return None
    ft = float(m.group(1))
    inch = float(m.group(2)) if m.group(2) else 0.0
    return ft + inch / 12.0


def extract_script(text: str) -> Tuple[str, str]:
    """Pulls the script out of a model answer; returns (script, the rest of the text e.g. CHANGES:)."""
    text = (text or "").replace("\r\n", "\n")
    m = re.search(r"```[a-zA-Z]*\s*\n(.*?)```", text, re.S)
    if m:
        script = m.group(1)
        rest = (text[:m.start()] + text[m.end():]).strip()
    else:
        lines = text.split("\n")
        start = next((i for i, ln in enumerate(lines) if re.match(r"\s*(PLOT|LEVEL)\b", ln, re.I)), 0)
        cut = next((i for i, ln in enumerate(lines) if re.match(r"\s*CHANGES\s*:", ln, re.I)), len(lines))
        script = "\n".join(lines[start:cut])
        rest = "\n".join(lines[cut:])
    notes = ""
    mc = re.search(r"CHANGES\s*:\s*(.*)", rest, re.S | re.I)
    if mc:
        notes = mc.group(1).strip()
    elif rest:
        notes = rest.strip()
    return script.strip("\n"), notes[:1200]


def _issue(code: str, level: str, line: Optional[int], msg: str, floor=None, room=None) -> Dict[str, Any]:
    return {"code": code, "level": level, "line": line, "floor": floor, "room": room,
            "message": (f"line {line}: " if line else "") + msg}


def parse_script(text: str, plot_w: float, plot_l: float, front_sb: Optional[float] = None,
                 rear_sb: Optional[float] = None) -> Dict[str, Any]:
    """Parses ArchiScript into the engine's layout (floors of slicing trees).

    Returns {floors, plot_w, plot_l, front_sb, rear_sb, errors, warnings, rooms (level,id)->{line,name},
    normalised_script}. Parse problems are reported per line; they never raise."""
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    raw_lines = (text or "").replace("\r\n", "\n").split("\n")
    floors: List[Dict[str, Any]] = []
    script_plot = None
    script_sb = {}
    cur = None
    stack: List[Tuple[int, Dict[str, Any]]] = []

    for i, raw in enumerate(raw_lines, start=1):
        body = raw.split("#", 1)[0].rstrip()
        if not body.strip():
            continue
        exp = body.expandtabs(4)
        indent = len(exp) - len(exp.lstrip())
        s = exp.strip()
        up = s.upper()

        if re.match(r"PLOT\b", up):
            m = re.match(r"PLOT\s+" + _SIZE_RE + r"\s*[xX*]\s*" + _SIZE_RE, s, re.I)
            if m:
                w = float(m.group(1)) + (float(m.group(2)) / 12.0 if m.group(2) else 0.0)
                l_ = float(m.group(3)) + (float(m.group(4)) / 12.0 if m.group(4) else 0.0)
                script_plot = (w, l_)
            else:
                errors.append(_issue("SCRIPT_SYNTAX", "error", i, "write the plot as: PLOT <width> x <depth>"))
            continue
        if re.match(r"SETBACKS?\b", up):
            for key in ("front", "rear"):
                m = re.search(key + r"\s*[:=]?\s*" + _SIZE_RE, s, re.I)
                if m:
                    script_sb[key] = float(m.group(1)) + (float(m.group(2)) / 12.0 if m.group(2) else 0.0)
            continue
        if re.match(r"LEVEL\b", up):
            m = re.match(r'LEVEL\s+(-?\d+)\s*(?:"([^"]*)"|\'([^\']*)\'|([^|]*))?', s, re.I)
            if not m:
                errors.append(_issue("SCRIPT_SYNTAX", "error", i, 'write a level as: LEVEL <n> "<label>"'))
                continue
            lvl = int(m.group(1))
            label = (m.group(2) or m.group(3) or (m.group(4) or "").replace("ROOF", "").strip() or
                     {0: "GROUND FLOOR", 1: "FIRST FLOOR", 2: "SECOND FLOOR"}.get(lvl, f"LEVEL {lvl}")).strip()
            roof = bool(re.search(r"\bROOF\b", up))
            if any(f["level"] == lvl for f in floors):
                errors.append(_issue("SCRIPT_DUPLICATE_LEVEL", "error", i, f"LEVEL {lvl} is written twice"))
            cur = {"level": lvl, "label": label.upper(), "layout": None, "_line": i}
            if roof:
                cur["roof"] = True
            floors.append(cur)
            stack = []
            continue

        if cur is None:
            cur = {"level": 0, "label": "GROUND FLOOR", "layout": None, "_line": i}
            floors.append(cur)
            warnings.append(_issue("SCRIPT_NO_LEVEL", "warning", i, 'no LEVEL line before the first space - assumed LEVEL 0 "GROUND FLOOR"'))

        node = _parse_node(s, i, errors, warnings)
        if node is None:
            continue
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            if cur["layout"] is None and "parts" in node and node.get("size_ft") is None:
                if node.get("split") != "rows":
                    warnings.append(_issue("SCRIPT_ROOT", "warning", i, "the root of a level should be ROWS (front to back)"))
                cur["layout"] = node                      # the level's root ROWS block
            elif cur["layout"] is None:                   # spaces written without a root ROWS line
                cur["layout"] = {"split": "rows", "parts": [node], "_line": i}
            else:                                         # any other top-level line belongs to the root
                cur["layout"]["parts"].append(node)
        else:
            parent = stack[-1][1]
            if "parts" not in parent:
                errors.append(_issue("SCRIPT_INDENT", "error", i,
                                     f"indented under a room line (line {parent['_line']}); only ROWS / COLS lines can contain spaces"))
                continue
            parent["parts"].append(node)
        if "parts" in node:
            stack.append((indent, node))

    W, L = float(plot_w), float(plot_l)
    if script_plot and (abs(script_plot[0] - W) > 0.05 or abs(script_plot[1] - L) > 0.05):
        warnings.append(_issue("SCRIPT_PLOT", "warning", None,
                               f"the script says PLOT {script_plot[0]:g} x {script_plot[1]:g} but the plot is {W:g} x {L:g}; "
                               f"the real plot is used"))
    fsb = front_sb if front_sb is not None else script_sb.get("front", 0.0)
    rsb = rear_sb if rear_sb is not None else script_sb.get("rear", 0.0)

    rooms_map: Dict[Tuple[int, str], Dict[str, Any]] = {}
    actual_sizes: Dict[int, float] = {}
    for fl in floors:
        if fl["layout"] is None or not fl["layout"].get("parts"):
            errors.append(_issue("SCRIPT_EMPTY_LEVEL", "error", fl["_line"], f"LEVEL {fl['level']} has no spaces"))
            fl["layout"] = {"split": "rows", "parts": [{"size_ft": L, "room": {"name": "OPEN", "type": "open"}}]}
            continue
        _assign_ids(fl, rooms_map, errors, warnings)
        _size_check(fl["layout"], W, L, warnings, actual_sizes, root=True)

    return {"floors": [{k: v for k, v in f.items() if k != "_line"} for f in floors],
            "plot_w": W, "plot_l": L, "front_sb": float(fsb), "rear_sb": float(rsb),
            "script_setbacks": script_sb, "errors": errors, "warnings": warnings, "rooms": rooms_map,
            "normalised_script": _rewrite_sizes(raw_lines, actual_sizes)}


def _parse_node(s: str, i: int, errors, warnings) -> Optional[Dict[str, Any]]:
    m = re.fullmatch(r"(?:" + _SIZE_RE + r"\s*\|?\s*)?(ROWS|COLS|COLUMNS)\s*:?\s*", s, re.I)
    if m:
        size = None
        if m.group(1):
            size = float(m.group(1)) + (float(m.group(2)) / 12.0 if m.group(2) else 0.0)
        split = "rows" if m.group(3).upper() == "ROWS" else "cols"
        node = {"split": split, "parts": [], "_line": i}
        if size is not None:
            node["size_ft"] = round(size, 3)
        return node
    cells = [c.strip() for c in s.split("|")]
    if len(cells) < 3:
        errors.append(_issue("SCRIPT_SYNTAX", "error", i,
                             f"'{s[:50]}' - write a space as: <size> | <NAME> | <type> | door: <NAME>"))
        return None
    size = parse_size(cells[0])
    if size is None or size <= 0:
        errors.append(_issue("SCRIPT_SYNTAX", "error", i, f"'{cells[0]}' is not a size in feet"))
        return None
    name = _norm(cells[1]) or "SPACE"
    rtype = cells[2].strip().lower().replace(" ", "_").replace("-", "_")
    if rtype not in ROOM_TYPES and rtype not in _TYPE_CATEGORY:
        warnings.append(_issue("SCRIPT_TYPE", "warning", i, f"unknown type '{cells[2]}' for {name} - treated by its name"))
    room: Dict[str, Any] = {"name": name, "type": rtype, "door_from": None}
    for cell in cells[3:]:
        if not cell:
            continue
        mm = re.match(r"(door|from|entered from|arch|arches|furniture|id|extra door|extra_doors)\s*[:=]\s*(.*)", cell, re.I)
        if mm:
            key, val = mm.group(1).lower(), mm.group(2).strip()
            if key in ("door", "from", "entered from"):
                room["_door_ref"] = val
            elif key in ("arch", "arches"):
                room["_arch_refs"] = [v.strip() for v in val.split(",") if v.strip()]
            elif key in ("extra door", "extra_doors"):
                room["_extra_refs"] = [v.strip() for v in val.split(",") if v.strip()]
            elif key == "furniture":
                room["furniture"] = [v.strip().lower().replace(" ", "_") for v in val.split(",") if v.strip()]
            elif key == "id":
                room["id"] = _slug(val)
        elif cell.lower() in ("gate", "entrance gate", "main gate"):
            room["gate"] = True
        else:
            warnings.append(_issue("SCRIPT_ATTR", "warning", i, f"ignored '{cell}' (use door: / arch: / furniture: / gate)"))
    return {"size_ft": round(size, 3), "room": room, "_line": i}


def _leaves(node: Dict[str, Any]):
    if "room" in node:
        yield node
    for p in node.get("parts", []):
        yield from _leaves(p)


# rooms that are one room each: the same name twice is a second room, never a second part of the first
_SINGLE_ROOM_CATEGORIES = ("bedroom", "bath", "kitchen", "stair", "dressing", "study", "room", "porch", "pool")


def _assign_ids(fl: Dict[str, Any], rooms_map, errors, warnings) -> None:
    lvl = fl["level"]
    prefix = "rf" if fl.get("roof") else _LEVEL_PREFIX.get(lvl, f"l{lvl}")
    by_name: Dict[str, str] = {}
    used = set()
    leaves = list(_leaves(fl["layout"]))
    for lf in leaves:
        r = lf["room"]
        if _norm(r["name"]) in by_name:
            # the same NAME again = another part of the same space (an L-shaped lounge written in two bands):
            # the parts are joined by an open arch and a door: to that name lands on the part that is touched
            base, k = r["name"], 2
            if _TYPE_CATEGORY.get(str(r.get("type", "")).lower(), "") not in _SINGLE_ROOM_CATEGORIES:
                r["part_of"] = by_name[_norm(base)]
            while _norm(f"{base} {k}") in by_name:
                k += 1
            warnings.append(_issue("SCRIPT_DUPLICATE_NAME", "warning", lf["_line"],
                                   f"the name {base} is used twice on LEVEL {lvl} - this one is {base} {k}, "
                                   f"a part of the same space"))
            r["name"] = f"{base} {k}"
        rid = r.get("id") or f"{prefix}_{_slug(r['name'])}"
        base_id, k = rid, 2
        while rid in used:
            rid = f"{base_id}_{k}"
            k += 1
        r["id"] = rid
        used.add(rid)
        by_name[_norm(r["name"])] = rid
        rooms_map[(lvl, rid)] = {"line": lf["_line"], "name": r["name"]}

    ids = set(used)

    def resolve(ref: str, line: int, what: str) -> Optional[str]:
        if not ref or ref.lower() in ("none", "null", "-", "open"):
            return None
        key = _norm(ref)
        if key == "STREET":
            return "STREET"
        if key in by_name:
            return by_name[key]
        if _slug(ref) in ids or ref in ids:
            return _slug(ref) if _slug(ref) in ids else ref
        cands = [n for n in by_name if n.startswith(key) or key.startswith(n)]
        if len(cands) == 1:
            return by_name[cands[0]]
        errors.append(_issue("SCRIPT_BAD_REF", "error", line,
                             f"{what} '{ref}' is not a space on LEVEL {lvl} (names: {', '.join(list(by_name)[:12])})"))
        return None

    for lf in leaves:
        r = lf["room"]
        if "_door_ref" in r:
            r["door_from"] = resolve(r.pop("_door_ref"), lf["_line"], "door:")
        if "_arch_refs" in r:
            r["arch_to"] = [x for x in (resolve(a, lf["_line"], "arch:") for a in r.pop("_arch_refs")) if x]
        if "_extra_refs" in r:
            r["extra_doors_from"] = [x for x in (resolve(a, lf["_line"], "extra door:") for a in r.pop("_extra_refs")) if x]


def _size_check(node: Dict[str, Any], w: float, h: float, warnings, actual: Dict[int, float], root=False) -> None:
    parts = node.get("parts") or []
    if not parts:
        return
    rows = node.get("split", "rows") == "rows"
    extent = h if rows else w
    sizes = [p.get("size_ft") for p in parts]
    known = [s for s in sizes if s]
    if known and len(known) == len(sizes) and abs(sum(known) - extent) > 0.26:
        what = "depths" if rows else "widths"
        warnings.append(_issue("SIZE_SCALED", "warning", node.get("_line"),
                               f"the {what} under this {'ROWS' if rows else 'COLS'} add up to {sum(known):g} ft but the space is "
                               f"{extent:g} ft - scaled to fit (the script now shows the real sizes)"))
    lens = _allocate(sizes, extent)
    for p, ln in zip(parts, lens):
        if p.get("_line"):
            actual[p["_line"]] = ln
        if "parts" in p:
            _size_check(p, w if rows else ln, ln if rows else h, warnings, actual)


def _fmt(v: float) -> str:
    v = round(v * 4) / 4.0
    return f"{v:g}"


def _rewrite_sizes(raw_lines: List[str], actual: Dict[int, float]) -> str:
    out = []
    for i, raw in enumerate(raw_lines, start=1):
        if i in actual:
            m = re.match(r"^(\s*)" + _SIZE_RE, raw)
            if m:
                old = float(m.group(2)) + (float(m.group(3)) / 12.0 if m.group(3) else 0.0)
                if abs(old - actual[i]) > 0.01:
                    raw = m.group(1) + _fmt(actual[i]) + raw[m.end():]
        out.append(raw)
    return "\n".join(out).strip("\n")


def script_issue_lines(validation: Dict[str, Any], rooms_map: Dict[Tuple[int, str], Dict[str, Any]],
                       limit: int = 30) -> List[str]:
    """Engine findings re-worded with the script line of the room they concern, root causes first
    (a broken door makes every room behind it 'unreachable' - those are grouped into one line)."""
    def prio(code: str) -> int:
        for k, v in (("SCRIPT_", 0), ("DOOR", 1), ("STAIR", 2), ("TILING", 2), ("OVERLAP", 2), ("SETBACK", 3),
                     ("NO_MAIN", 3), ("LANDLOCKED", 4), ("WALK_THROUGH", 5)):
            if code.startswith(k):
                return v
        return 6
    lines: List[Tuple[int, str]] = []
    unreachable: List[str] = []
    for i in validation.get("errors", []):
        where = ""
        info = rooms_map.get((i.get("floor"), i.get("room"))) if i.get("room") is not None else None
        if info and not i.get("line"):
            where = f"line {info['line']} ({info['name']}): "
        if i["code"] == "UNREACHABLE":
            unreachable.append(f"{info['name']} (line {info['line']})" if info else str(i.get("room")))
            continue
        lines.append((prio(i["code"]), f"- [{i['code']}] {where}{i['message']}"))
    lines.sort(key=lambda x: x[0])
    out = [ln for _, ln in lines[:limit]]
    if unreachable:
        out.append(f"- [UNREACHABLE] {len(unreachable)} space(s) cannot be reached from the entrance / stair: "
                   f"{', '.join(unreachable[:14])}. Usually one door problem above causes this - give every space a "
                   f"door: to a space that is itself reachable (gallery, corridor, lobby, lounge).")
    return out


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

ENGINEERING_NOTIONS = """
=== HOW THIS SYSTEM WORKS (this is not a rule list - it is the machine you are driving; picture it as you write) ===
You do not draw. You write a short script that CUTS THE PLOT INTO RECTANGLES. A CAD engine turns those rectangles
into a building and then moves through it the way a person would. Everything it reports back comes from the seven
things below. If you can see them in your head, the design passes.

1. CUTTING. The plot is one rectangle. ROWS cuts a rectangle into bands from the street to the back; COLS cuts it
   into columns from left to right; you nest them. Each leaf is one space and gets exactly the rectangle the cuts
   leave it - no coordinates, no overlaps, nothing left over. The numbers are shares of the parent: if they do
   not add up, the engine stretches them until they do, and your rooms change size.
   What follows from this: a space only ever touches (a) its neighbours inside the same cut, and (b) whatever lies
   directly across the edge of its band, where the two rectangles overlap. It cannot touch anything further away.

2. WALLS AND DOORS. The engine thickens every edge into a wall (9 in outside, 4.5 in inside), so a room's clear
   size is a little less than its rectangle. `door: X` does not place a door - it says "cut an opening in the wall
   I share with X". The engine finds that wall and needs about 3 ft of it free between corners (2.5 ft for a bath,
   3.5 ft for a lounge, 4 ft for the main door, 5 ft for an arch). Where two rectangles share no wall, there is
   nothing to cut and the door cannot exist.

3. WALKING. Then it walks the house: on the ground floor from the street (through the porch, the lawn, or a
   `door: STREET` when a room stands on the front edge), upstairs from the STAIR - only through the openings. A room
   it cannot walk to is unreachable, and one missing door near the entrance cuts off everything behind it. If the
   only way to a room leads through somebody's bedroom or bath, it reports that too: a home needs a shared space
   (lounge, lobby, corridor, gallery) that the rooms open onto. The STAIR rectangle is filled with steps: a person
   steps onto it from the shared space and comes off it on the next floor - nobody walks across it to reach a
   room, so the way from the entrance to the lounge never leads through the stair.

4. LIGHT. Windows are placed by the engine too. For each room it looks for a wall that faces open air: the street
   edge of the plot, or a space that has no roof (lawn, car porch, open strip, gallery, terrace, balcony, OTS).
   The two side edges and the back edge of the plot are the neighbours' walls - nothing opens there. The stretch
   of wall a door already uses is not available for the window. A bedroom, lounge, drawing, dining, kitchen or
   study left with no such wall is a dark room. So on a deep, narrow plot the real design question is: where does
   each inner room get its air? A strip left open at the back, a shaft (type ots) cut between rooms, a gallery,
   a terrace - you choose, but every room must reach one.

5. FURNISHING. It then moves real furniture in. A queen bed is about 5 x 6.75 ft (king 6 ft wide, single 3.5 ft)
   and needs one wall free of doors and windows with space to walk beside it; a car is about 6 x 15 ft; a stair
   needs 3.5 x 9 ft at the very least to hold its steps. If the furniture you listed cannot be placed, it says so.

6. STACKING. Each level is cut separately, but they stand on each other. The stair is one hole through all the
   floors, so it is the same rectangle on every level. A shaft only brings light down if it stays open (type ots)
   on every level above. A room upstairs needs something built under it - over a lawn or a shaft it would hang in
   the air, so that area upstairs is a terrace, balcony or open.

7. BALANCE. Last, it compares the spaces with each other, because the plot is a fixed amount of floor: every
   foot one space takes, another loses. It tells you when a stair holds more floor than its steps use, when a
   bath or a passage is larger than its use, when the kitchen is bigger than the lounge the family sits in, when
   a room is so long and thin that it works like a corridor, or when a bedroom is so narrow that the bed leaves
   no way past. These come back as notes, not failures - a size the client states always wins.

WHO DECIDES WHAT. The client decides what is built: which rooms, how many, where, what sizes, setbacks or none.
Nothing above is a bylaw or a standard size. The engine only reports whether a person could walk in, get
daylight, climb the stair and fit a bed.

HOW TO WORK. First the skeleton: where the air comes from, and where the shared space runs so that rooms can open
onto it. Then hang the rooms on that skeleton. Then, for every door: line, name the wall it goes through - if you
cannot point to it, the two spaces do not touch.
"""


def build_script_prompt(brief: str, checklist: List[str], plot_w: float, plot_l: float, front_sb: float,
                        rear_sb: float, levels_note: str, size_notions: str = "", style: str = "") -> str:
    must = "\n".join(f"  {k + 1}. {c}" for k, c in enumerate(checklist))
    sb_note = (f"Client-requested setbacks: front {front_sb:g} ft, rear {rear_sb:g} ft."
               if (front_sb > 0 or rear_sb > 0)
               else "The brief states no setbacks - none are forced; leave open space (lawn / porch / OTS / open strip) where rooms need daylight.")
    return f"""You are a senior civil engineer and residential architect. Design EXACTLY what the client describes, and write it as an ARCHISCRIPT. Read "HOW THIS SYSTEM WORKS" first: a CAD engine builds your script and walks through it, and whatever does not work comes back to you by line number.

=== CLIENT BRIEF (the sole authority - follow it literally, fit every requested room) ===
"{brief.strip()}"

=== WHAT THE CLIENT ASKED FOR (every item must appear; name rooms so they are recognisable) ===
{must}

=== SITE & SIZING ===
- Plot {plot_w:g} ft wide (street frontage) x {plot_l:g} ft deep. {sb_note}
- {levels_note}
{size_notions}
- Style: {style or 'as the brief describes'} (affects the elevation only).
{ENGINEERING_NOTIONS}
{SCRIPT_SPEC}
Work in this order: (1) list every space the brief asks for and any size it gives; (2) decide the skeleton - where the air comes from and where the shared space runs on the {plot_w:g} x {plot_l:g} ft plot; (3) hang the rooms on it and make the band depths / column widths add up; (4) for every door: name the wall it goes through.
Then return ONLY the complete script inside ```archiscript ... ``` fences.
"""


def build_stage_prompt(brief: str, checklist: List[str], plot_w: float, plot_l: float, front_sb: float,
                       rear_sb: float, stage_note: str, fixed_script: str = "", size_notions: str = "",
                       style: str = "") -> str:
    """One level at a time: the levels below are fixed (already checked) and shown; only the next level is asked for."""
    must = "\n".join(f"  {k + 1}. {c}" for k, c in enumerate(checklist))
    fixed = (f"\n=== LEVELS ALREADY DESIGNED AND CHECKED (fixed - do NOT rewrite or change them) ===\n"
             f"```archiscript\n{fixed_script.strip()}\n```\n") if fixed_script.strip() else ""
    sb_note = (f"Client-requested setbacks: front {front_sb:g} ft, rear {rear_sb:g} ft."
               if (front_sb > 0 or rear_sb > 0)
               else "The brief states no setbacks - none are forced; leave open space (lawn / porch / OTS / open strip) where rooms need daylight.")
    return f"""You are a senior civil engineer and residential architect. Design EXACTLY what the client describes as an ARCHISCRIPT, ONE LEVEL AT A TIME. Read "HOW THIS SYSTEM WORKS" first: a CAD engine builds each level from your script and walks through it before the next level is designed on top of it.

=== CLIENT BRIEF (the sole authority - follow it literally) ===
"{brief.strip()}"

=== WHAT THE CLIENT ASKED FOR (every item must appear on some level; name rooms so they are recognisable) ===
{must}

=== SITE & SIZING ===
- Plot {plot_w:g} ft wide (street frontage) x {plot_l:g} ft deep. {sb_note}
- Coordinates: x is measured from the LEFT side of the plot, y from the STREET (front) towards the back.
{size_notions}
- Style: {style or 'as the brief describes'} (affects the elevation only).
{ENGINEERING_NOTIONS}
{SCRIPT_SPEC}{fixed}
=== THIS STEP ===
{stage_note}
Return the PLOT and SETBACKS lines and ONLY the level(s) asked for in THIS STEP, inside ```archiscript ... ``` fences.
"""


def build_script_repair_prompt(base_prompt: str, script: str, problems: List[str],
                               notes: Optional[List[str]] = None, picture: str = "") -> str:
    seen = (f"=== WHAT YOUR SCRIPT BUILT (look at which letters touch: a door needs two rooms side by side along at "
            f"least 3 ft; '.' = nothing) ===\n{picture}\n") if picture else ""
    probs = seen + (("=== PROBLEMS FOUND (fix ALL of them; keep everything that is already right and keep every client "
                     "item) ===\n" + "\n".join(problems) + "\n") if problems else
                    "=== NO RULE PROBLEMS - every check passed. Improve the layout notes below without breaking anything. ===\n")
    extra = ("=== LAYOUT NOTES (improve these where the brief allows - they are advice, not errors; never change a size "
             "the brief gives) ===\n" + "\n".join(notes) + "\n") if notes else ""
    return f"""{base_prompt}

=== REPAIR STEP: make the SMALLEST change that fixes each problem. Do not re-plan what already works - a repair that
moves many rooms usually breaks more doors than it fixes. Check each door: against the letter map before you answer. ===

=== YOUR PREVIOUS SCRIPT (the CAD engine ran it) ===
```archiscript
{script}
```
{probs}{extra}
Return the corrected script - everything the task above asks for - inside ```archiscript ... ``` fences.
"""


def build_converse_prompt(brief: str, checklist: List[str], script: str, message: str,
                          history: List[Dict[str, str]], plot_w: float, plot_l: float, front_sb: float,
                          rear_sb: float, problems: Optional[List[str]] = None) -> str:
    convo = "\n".join(f"{h.get('role', 'user').upper()}: {h.get('text', '')}" for h in (history or [])[-8:])
    must = "\n".join(f"  - {c}" for c in checklist)
    probs = ("\n=== PROBLEMS THE CAD ENGINE STILL REPORTS ON THE CURRENT SCRIPT ===\n" + "\n".join(problems)) if problems else ""
    return f"""You are the architect editing a client's ArchiScript in a conversation. Apply the client's message to the
script and keep everything else that still fits the brief: keep every CLIENT ITEM, keep the same LEVELs (never add a
level or a roof unless the message asks for it), keep the plot and setbacks. Make the smallest change that does what the
client asked. If the message is only a question, answer it and return the script unchanged.

ORIGINAL BRIEF: "{brief.strip()}"
CLIENT ITEMS:
{must}
SITE: plot {plot_w:g} x {plot_l:g} ft, front setback {front_sb:g} ft, rear setback {rear_sb:g} ft.
{ENGINEERING_NOTIONS}
{SCRIPT_SPEC}
=== CURRENT SCRIPT ===
```archiscript
{script}
```{probs}
=== CONVERSATION SO FAR ===
{convo or '(none)'}
=== CLIENT'S NEW MESSAGE ===
{message.strip()}

Return the COMPLETE updated script inside ```archiscript ... ``` fences, then one line:
CHANGES: <what you changed and why, in one or two plain sentences>
"""


# ---------------------------------------------------------------------------
# Layout -> script (any engine layout can be shown and edited as a script)
# ---------------------------------------------------------------------------

def to_script(layout: Dict[str, Any], plot_w: float, plot_l: float, front_sb: float, rear_sb: float) -> str:
    out = [f"PLOT {plot_w:g} x {plot_l:g}", f"SETBACKS front {front_sb:g} rear {rear_sb:g}"]
    for fl in layout.get("floors", []):
        tree = fl.get("layout")
        if not isinstance(tree, dict):
            continue
        names: Dict[str, str] = {}
        seen: Dict[str, int] = {}
        for lf in _leaves(tree):
            r = lf["room"]
            base = _norm(r.get("name", "SPACE"))
            seen[base] = seen.get(base, 0) + 1
            names[r.get("id", base)] = base if seen[base] == 1 else f"{base} {seen[base]}"
        out.append(f'LEVEL {fl.get("level", 0)} "{fl.get("label", "")}"' + (" ROOF" if fl.get("roof") else ""))

        def emit(node, depth):
            ind = "  " * depth
            size = node.get("size_ft")
            if "room" in node:
                r = node["room"]
                cells = [_fmt(float(size or 0) or 1.0), names.get(r.get("id"), _norm(r.get("name", "SPACE"))),
                         str(r.get("type", "room"))]
                if r.get("door_from"):
                    cells.append("door: " + names.get(r["door_from"], str(r["door_from"])))
                if r.get("extra_doors_from"):
                    cells.append("extra door: " + ", ".join(names.get(a, str(a)) for a in r["extra_doors_from"]))
                if r.get("arch_to"):
                    cells.append("arch: " + ", ".join(names.get(a, str(a)) for a in r["arch_to"]))
                if r.get("furniture"):
                    cells.append("furniture: " + ", ".join(str(f) for f in r["furniture"]))
                if r.get("gate"):
                    cells.append("gate")
                out.append(ind + " | ".join(cells))
            else:
                head = "ROWS" if node.get("split", "rows") == "rows" else "COLS"
                out.append(ind + (f"{_fmt(float(size))} {head}" if size and depth > 0 else head))
                for p in node.get("parts", []):
                    if isinstance(p, dict):
                        emit(p, depth + 1)
        emit(tree, 0)
    return "\n".join(out)
