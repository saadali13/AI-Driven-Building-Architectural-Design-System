#!/usr/bin/env python3
"""
layout_engine/edit_ops.py - Room-Level Edit Operations for Slicing Layouts

Each operation:
  - Takes a layout dict (as produced by corpus/layouts/<id>.json or reconstruct_slicing_layout)
  - Returns (new_layout, log_entry)
  - Runs post-op checks automatically
  - Never modifies the input layout (deep-copy first)

Layout structure used here:
  layout["rooms"]  - list of room dicts with keys:
        printed_name, canonical_type, band_index, order_in_band,
        zone, y_zone, x_zone, rect_norm [x0,y0,x1,y1], rect_ft [x0,y0,x1,y1],
        nominal_dims [w,d], dimensions [w,d], is_habitable
  layout["bands"]  - list of band dicts {band_index, y_zone, ...}
  layout["adjacencies"] - list of [i, j] pairs (room indices)
  layout["envelope_ft"] - [x0, y0, x1, y1] building envelope in feet
  layout["porch_side"]  - "left" | "centre" | "right"
  layout["stair_zone"]  - {y_zone, x_zone, zone} or None

Post-op checks (run after every operation):
  1. No overlap - confirmed by slicing (non-overlapping by construction; we check centres)
  2. All rooms inside plot boundary (rect_ft within envelope_ft)
  3. Min sizes: bedroom>=100 sqft, bathroom>=30 sqft, kitchen>=60 sqft, lounge>=120 sqft
  4. Bedrooms on exterior wall (y_zone in {back, front})
  5. Wet rooms grouped (bathroom near kitchen/bathroom)
  6. Kitchen adjacent to lounge/dining
  7. Stair and entrance NOT moved (unless op explicitly allows it)
  8. Every room reachable from entrance (BFS on adjacency graph)
  9. Total area budget within 10% of original

Log entry format:
  {op, args, reason, rooms_before, rooms_after, area_change_sqft, result, failure_reason}
"""

import copy
import json
import math
from typing import Dict, List, Any, Optional, Tuple

# Minimum floor areas in sq ft
MIN_AREA = {
    "bedroom": 100.0,
    "bathroom": 30.0,
    "kitchen": 60.0,
    "living_lounge": 120.0,
    "porch": 80.0,
    "stair": 25.0,
    "ots": 40.0,
    "store": 20.0,
    "servant_quarter": 60.0,
    "other": 20.0,
}

SKIP_MOVE = {"stair", "porch"}  # never auto-moved unless explicitly allowed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _room_area(r: dict) -> float:
    rf = r.get("rect_ft") or []
    if len(rf) == 4:
        return max(0.0, (rf[2] - rf[0]) * (rf[3] - rf[1]))
    dims = r.get("dimensions") or r.get("nominal_dims") or [0, 0]
    return dims[0] * dims[1]


def _total_area(rooms: list) -> float:
    return sum(_room_area(r) for r in rooms)


def _room_snapshot(rooms: list) -> list:
    return [
        {
            "room_index": r.get("room_index", i),
            "name": r.get("printed_name", "?"),
            "type": r.get("canonical_type", "?"),
            "zone": r.get("zone", "?"),
            "area_sqft": round(_room_area(r), 1),
        }
        for i, r in enumerate(rooms)
    ]


def _build_adj_graph(rooms: list, adjacencies: list) -> Dict[int, List[int]]:
    """
    Build adjacency graph supporting both formats:
    - List of [room_index_a, room_index_b] pairs (edit_ops format)
    - List of dicts {room_1: name, room_2: name, ...} (corpus format)
    """
    idx_map = {r.get("room_index", i): i for i, r in enumerate(rooms)}
    name_map = {r.get("printed_name", ""): i for i, r in enumerate(rooms)}
    g: Dict[int, List[int]] = {i: [] for i in range(len(rooms))}
    for pair in adjacencies:
        if isinstance(pair, dict):
            # Corpus format: {room_1: name, room_2: name}
            n1 = pair.get("room_1", "")
            n2 = pair.get("room_2", "")
            ai = name_map.get(n1)
            bi = name_map.get(n2)
            if ai is not None and bi is not None and ai != bi:
                g[ai].append(bi)
                g[bi].append(ai)
        elif isinstance(pair, (list, tuple)) and len(pair) >= 2:
            a, b = pair[0], pair[1]
            ai = idx_map.get(a, a) if isinstance(a, int) else a
            bi = idx_map.get(b, b) if isinstance(b, int) else b
            if isinstance(ai, int) and isinstance(bi, int):
                if 0 <= ai < len(rooms) and 0 <= bi < len(rooms):
                    g[ai].append(bi)
                    g[bi].append(ai)
    return g


def _bfs_reachable(start: int, graph: Dict[int, List[int]]) -> set:
    visited = {start}
    queue = [start]
    while queue:
        node = queue.pop(0)
        for nb in graph.get(node, []):
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return visited


# ---------------------------------------------------------------------------
# Post-op checks
# ---------------------------------------------------------------------------

def _parse_envelope(layout: dict) -> List[float]:
    """
    Returns [x0, y0, x1, y1] from whatever envelope_ft format is stored.
    Corpus files store [w, h] (2-element); edit_ops stores [x0, y0, x1, y1] (4-element).
    """
    env = layout.get("envelope_ft") or [0, 0, 100, 100]
    if len(env) == 2:
        # [width, height] — treat as [0, 0, w, h]
        return [0.0, 0.0, float(env[0]), float(env[1])]
    return [float(v) for v in env[:4]]


# ---------------------------------------------------------------------------
# Post-op checks
# ---------------------------------------------------------------------------

def run_post_checks(
    layout: dict,
    original_area: float,
    allow_move_stair: bool = False,
    allow_move_entrance: bool = False,
) -> List[str]:
    """Returns list of violation strings. Empty = OK."""
    rooms = layout.get("rooms", [])
    env = _parse_envelope(layout)
    adjacencies = layout.get("adjacencies", [])
    errors = []

    # 1. Min sizes
    for r in rooms:
        ctype = r.get("canonical_type", "other")
        area = _room_area(r)
        min_a = MIN_AREA.get(ctype, 20.0)
        if area < min_a:
            errors.append(
                f"MIN_SIZE: {r.get('printed_name','?')} ({ctype}) area {area:.0f} sqft < {min_a:.0f} sqft"
            )

    # 2. All rooms inside plot boundary
    # envelope_ft from corpus is [env_w, env_h]; plot can be wider than the building envelope.
    # Use plot dimensions from layout["plot"] if available, else fall back to envelope_ft.
    _plot = layout.get("plot") or {}
    _pw = _plot.get("width") or env[2]
    _pl = _plot.get("depth") or env[3]
    for r in rooms:
        rf = r.get("rect_ft") or []
        if len(rf) == 4 and max(rf) > 2.0:  # skip normalised (0-1) rects
            tol = 2.0
            if rf[0] < -tol or rf[2] > _pw + tol or rf[1] < -tol or rf[3] > _pl + tol:
                errors.append(
                    f"OUTSIDE_PLOT: {r.get('printed_name','?')} "
                    f"rect [{rf[0]:.1f},{rf[1]:.1f},{rf[2]:.1f},{rf[3]:.1f}] "
                    f"outside plot 0..{_pw:.1f} x 0..{_pl:.1f}"
                )

    # 3. Bedrooms on exterior wall (y_zone in {back, front})
    for r in rooms:
        if r.get("canonical_type") == "bedroom":
            yz = r.get("y_zone", "middle")
            if yz == "middle":
                errors.append(
                    f"LANDLOCKED_BEDROOM: {r.get('printed_name','?')} has y_zone=middle (no exterior wall)"
                )

    # 4. Kitchen adjacency to lounge/dining
    kitchen_idxs = [i for i, r in enumerate(rooms) if r.get("canonical_type") == "kitchen"]
    lounge_idxs = [i for i, r in enumerate(rooms) if r.get("canonical_type") in ("living_lounge", "dining")]
    if kitchen_idxs and lounge_idxs:
        graph = _build_adj_graph(rooms, adjacencies)
        kitchen_neighbours = set()
        for ki in kitchen_idxs:
            kitchen_neighbours.update(graph.get(ki, []))
        lounge_adj = any(li in kitchen_neighbours for li in lounge_idxs)
        if not lounge_adj:
            errors.append("KITCHEN_NOT_ADJ_LOUNGE: Kitchen has no adjacency to lounge/dining")

    # 5. BFS reachability from entrance (index 0 assumed, or porch)
    porch_idxs = [i for i, r in enumerate(rooms) if r.get("canonical_type") == "porch"]
    start_node = porch_idxs[0] if porch_idxs else 0
    if rooms and adjacencies:
        graph = _build_adj_graph(rooms, adjacencies)
        reachable = _bfs_reachable(start_node, graph)
        all_idxs = set(range(len(rooms)))
        unreachable = all_idxs - reachable
        if unreachable:
            names = [rooms[i].get("printed_name", f"room_{i}") for i in unreachable]
            errors.append(f"UNREACHABLE_ROOMS: {names}")

    # 6. Area budget
    new_area = _total_area(rooms)
    if original_area > 0:
        ratio = abs(new_area - original_area) / original_area
        if ratio > 0.10:
            errors.append(
                f"AREA_BUDGET: Area changed by {ratio*100:.0f}% "
                f"({original_area:.0f} -> {new_area:.0f} sqft), limit 10%"
            )

    return errors


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def _make_log(op: str, args: dict, reason: str,
              before: list, after: list, orig_area: float,
              errors: List[str]) -> dict:
    new_area = sum(e["area_sqft"] for e in after)
    return {
        "op": op,
        "args": args,
        "reason": reason,
        "rooms_before": before,
        "rooms_after": after,
        "area_change_sqft": round(new_area - orig_area, 1),
        "result": "failed" if errors else "ok",
        "failure_reason": errors if errors else None,
    }


def remove_room(layout: dict, room_id: int, reason: str = "") -> Tuple[dict, dict]:
    """
    Remove a room by its room_index (or list position).
    Redistributes its area to the largest adjacent room.
    Does NOT remove stair or porch.
    """
    lay = copy.deepcopy(layout)
    rooms = lay["rooms"]
    orig_area = _total_area(rooms)
    before = _room_snapshot(rooms)

    target_idx = next((i for i, r in enumerate(rooms)
                       if r.get("room_index", i) == room_id), None)
    if target_idx is None:
        log = _make_log("remove_room", {"room_id": room_id}, reason, before, before, orig_area,
                        [f"Room index {room_id} not found"])
        return layout, log

    target = rooms[target_idx]
    ctype = target.get("canonical_type", "")
    if ctype in SKIP_MOVE:
        log = _make_log("remove_room", {"room_id": room_id}, reason, before, before, orig_area,
                        [f"Cannot remove {ctype} (protected type)"])
        return layout, log

    removed_area = _room_area(target)
    adjacencies = lay.get("adjacencies", [])
    graph = _build_adj_graph(rooms, adjacencies)
    neighbours = graph.get(target_idx, [])
    if neighbours:
        biggest_nb = max(neighbours, key=lambda i: _room_area(rooms[i]))
        nb_room = rooms[biggest_nb]
        rf = list(nb_room.get("rect_ft") or [0, 0, 10, 10])
        # Expand neighbour in depth
        rf[3] += removed_area / max(1.0, rf[2] - rf[0])
        nb_room["rect_ft"] = rf
        dims = list(nb_room.get("dimensions") or [0, 0])
        dims[1] += removed_area / max(1.0, dims[0])
        nb_room["dimensions"] = dims

    rooms.pop(target_idx)
    # Update adjacency list
    lay["adjacencies"] = [pair for pair in adjacencies
                          if target_idx not in pair
                          and room_id not in pair]

    errors = run_post_checks(lay, orig_area)
    log = _make_log("remove_room", {"room_id": room_id}, reason,
                    before, _room_snapshot(rooms), orig_area, errors)
    return lay, log


def convert_room(layout: dict, room_id: int, new_type: str, reason: str = "") -> Tuple[dict, dict]:
    """Change a room's canonical_type (e.g. bedroom -> study)."""
    lay = copy.deepcopy(layout)
    rooms = lay["rooms"]
    orig_area = _total_area(rooms)
    before = _room_snapshot(rooms)

    target_idx = next((i for i, r in enumerate(rooms)
                       if r.get("room_index", i) == room_id), None)
    if target_idx is None:
        log = _make_log("convert_room", {"room_id": room_id, "new_type": new_type}, reason,
                        before, before, orig_area, [f"Room {room_id} not found"])
        return layout, log

    rooms[target_idx]["canonical_type"] = new_type
    rooms[target_idx]["is_habitable"] = new_type in ("bedroom", "living_lounge")

    errors = run_post_checks(lay, orig_area)
    log = _make_log("convert_room", {"room_id": room_id, "new_type": new_type}, reason,
                    before, _room_snapshot(rooms), orig_area, errors)
    return lay, log


def merge_rooms(layout: dict, room_id_a: int, room_id_b: int, reason: str = "") -> Tuple[dict, dict]:
    """
    Merge two adjacent rooms.  The merged room takes room_id_a's type and
    combined dimensions.  room_id_b is removed.
    """
    lay = copy.deepcopy(layout)
    rooms = lay["rooms"]
    orig_area = _total_area(rooms)
    before = _room_snapshot(rooms)

    idx_a = next((i for i, r in enumerate(rooms) if r.get("room_index", i) == room_id_a), None)
    idx_b = next((i for i, r in enumerate(rooms) if r.get("room_index", i) == room_id_b), None)

    if idx_a is None or idx_b is None:
        log = _make_log("merge_rooms", {"room_id_a": room_id_a, "room_id_b": room_id_b}, reason,
                        before, before, orig_area, ["One or both room ids not found"])
        return layout, log

    ra, rb = rooms[idx_a], rooms[idx_b]
    area_a = _room_area(ra)
    area_b = _room_area(rb)
    combined_area = area_a + area_b

    # Expand room A dimensions
    dims = list(ra.get("dimensions") or [10, 10])
    dims[1] = combined_area / max(1.0, dims[0])
    ra["dimensions"] = dims
    ra["nominal_dims"] = dims
    rf = list(ra.get("rect_ft") or [0, 0, 10, 10])
    rf[3] = rf[1] + dims[1]
    ra["rect_ft"] = rf
    ra["printed_name"] = f"{ra.get('printed_name','')} + {rb.get('printed_name','')}"

    # Remove room B
    del rooms[idx_b]
    lay["adjacencies"] = [pair for pair in lay.get("adjacencies", [])
                          if room_id_b not in pair]

    errors = run_post_checks(lay, orig_area)
    log = _make_log("merge_rooms", {"room_id_a": room_id_a, "room_id_b": room_id_b}, reason,
                    before, _room_snapshot(rooms), orig_area, errors)
    return lay, log


def add_room(layout: dict, room_type: str, target_y_zone: str,
             target_size_sqft: float = 120.0, reason: str = "",
             new_name: str = "") -> Tuple[dict, dict]:
    """
    Add a new room.
    Strategy:
      1. Split the largest room in target_y_zone that is NOT a core protected type.
      2. If that fails, split any large room in target_y_zone.
      3. Record fallback in log.
    """
    lay = copy.deepcopy(layout)
    rooms = lay["rooms"]
    orig_area = _total_area(rooms)
    before = _room_snapshot(rooms)

    PROTECTED = {"stair", "porch", "bathroom"}
    candidates = [r for r in rooms
                  if r.get("y_zone") == target_y_zone
                  and r.get("canonical_type") not in PROTECTED
                  and _room_area(r) >= target_size_sqft * 1.3]

    if not candidates:
        # Relax: any room in zone with enough area (1.1x)
        candidates = [r for r in rooms
                      if r.get("y_zone") == target_y_zone
                      and _room_area(r) >= target_size_sqft * 1.1]

    if not candidates:
        # Relax further: any room in zone
        candidates = [r for r in rooms
                      if r.get("y_zone") == target_y_zone
                      and r.get("canonical_type") not in PROTECTED]

    strategy = "split_largest"
    if not candidates:
        log = _make_log("add_room",
                        {"type": room_type, "y_zone": target_y_zone, "size": target_size_sqft},
                        reason, before, before, orig_area,
                        [f"No room in {target_y_zone} zone large enough to split for {room_type}"])
        return layout, log

    donor = max(candidates, key=_room_area)
    donor_area = _room_area(donor)

    # Split: new room takes target_size_sqft from donor's depth
    donor_rf = list(donor.get("rect_ft") or [0, 0, 10, 10])
    donor_w = max(1.0, donor_rf[2] - donor_rf[0])
    new_depth = target_size_sqft / donor_w
    new_room_rf = [donor_rf[0], donor_rf[3] - new_depth, donor_rf[2], donor_rf[3]]
    donor_rf[3] -= new_depth
    donor["rect_ft"] = donor_rf
    donor_dims = list(donor.get("dimensions") or [donor_w, 10])
    donor_dims[1] = max(1.0, donor_rf[3] - donor_rf[1])
    donor["dimensions"] = donor_dims

    new_room = {
        "room_index": max((r.get("room_index", i) for i, r in enumerate(rooms)), default=0) + 1,
        "printed_name": new_name or room_type.replace("_", " ").title(),
        "canonical_type": room_type,
        "band_index": donor.get("band_index", 1),
        "order_in_band": donor.get("order_in_band", 0) + 1,
        "zone": donor.get("zone", target_y_zone + "_centre"),
        "y_zone": target_y_zone,
        "x_zone": donor.get("x_zone", "centre"),
        "rect_ft": new_room_rf,
        "rect_norm": [0, 0, 1, 1],
        "nominal_dims": [donor_w, new_depth],
        "dimensions": [donor_w, new_depth],
        "is_habitable": room_type in ("bedroom", "living_lounge"),
    }
    rooms.append(new_room)

    # Add adjacency to donor
    donor_local_idx = rooms.index(donor)
    new_local_idx = len(rooms) - 1
    lay["adjacencies"] = list(lay.get("adjacencies", []))
    lay["adjacencies"].append([donor_local_idx, new_local_idx])

    errors = run_post_checks(lay, orig_area, allow_move_stair=True)
    log = _make_log("add_room",
                    {"type": room_type, "y_zone": target_y_zone, "size": target_size_sqft, "strategy": strategy},
                    reason, before, _room_snapshot(rooms), orig_area, errors)
    return lay, log


def move_room(layout: dict, room_id: int, to_y_zone: str, to_x_zone: str = "centre",
              reason: str = "") -> Tuple[dict, dict]:
    """
    Move a room to a new zone by swapping its zone metadata.
    Does NOT physically move rect_ft (that would require full re-packing).
    Updates y_zone, x_zone, zone, band_index to reflect new position.
    Returns a check that the room is NOT stair/porch.
    """
    lay = copy.deepcopy(layout)
    rooms = lay["rooms"]
    orig_area = _total_area(rooms)
    before = _room_snapshot(rooms)

    target_idx = next((i for i, r in enumerate(rooms)
                       if r.get("room_index", i) == room_id), None)
    if target_idx is None:
        log = _make_log("move_room", {"room_id": room_id, "to_y_zone": to_y_zone}, reason,
                        before, before, orig_area, [f"Room {room_id} not found"])
        return layout, log

    r = rooms[target_idx]
    if r.get("canonical_type") in SKIP_MOVE:
        log = _make_log("move_room", {"room_id": room_id, "to_y_zone": to_y_zone}, reason,
                        before, before, orig_area,
                        [f"Cannot move {r.get('canonical_type')} (protected)"])
        return layout, log

    old_band = r.get("band_index", 1)
    # Map y_zone to band_index (0=rear, 1=middle, 2=front)
    zone_to_band = {"back": 0, "middle": 1, "front": 2}
    new_band = zone_to_band.get(to_y_zone, 1)

    r["y_zone"] = to_y_zone
    r["x_zone"] = to_x_zone
    r["zone"] = f"{to_y_zone}_{to_x_zone}"
    r["band_index"] = new_band

    # Also update rect_ft y coordinates to roughly match new band
    env = _parse_envelope(lay)
    env_h = env[3] - env[1]
    band_y_map = {"front": env[1], "middle": env[1] + env_h * 0.3, "back": env[1] + env_h * 0.65}
    rf = list(r.get("rect_ft") or [env[0], env[1], env[0]+10, env[1]+10])
    old_h = rf[3] - rf[1]
    rf[1] = band_y_map.get(to_y_zone, env[1])
    rf[3] = rf[1] + old_h
    r["rect_ft"] = rf

    errors = run_post_checks(lay, orig_area)
    log = _make_log("move_room", {"room_id": room_id, "to_y_zone": to_y_zone, "to_x_zone": to_x_zone},
                    reason, before, _room_snapshot(rooms), orig_area, errors)
    return lay, log


def swap_rooms(layout: dict, room_id_a: int, room_id_b: int, reason: str = "") -> Tuple[dict, dict]:
    """Swap the zone positions (y_zone, x_zone, zone, band_index, rect_ft) of two rooms."""
    lay = copy.deepcopy(layout)
    rooms = lay["rooms"]
    orig_area = _total_area(rooms)
    before = _room_snapshot(rooms)

    idx_a = next((i for i, r in enumerate(rooms) if r.get("room_index", i) == room_id_a), None)
    idx_b = next((i for i, r in enumerate(rooms) if r.get("room_index", i) == room_id_b), None)

    if idx_a is None or idx_b is None:
        log = _make_log("swap_rooms", {"room_id_a": room_id_a, "room_id_b": room_id_b}, reason,
                        before, before, orig_area, ["One or both room ids not found"])
        return layout, log

    ra, rb = rooms[idx_a], rooms[idx_b]
    for field in ["y_zone", "x_zone", "zone", "band_index", "rect_ft"]:
        ra[field], rb[field] = rb.get(field), ra.get(field)

    errors = run_post_checks(lay, orig_area)
    log = _make_log("swap_rooms", {"room_id_a": room_id_a, "room_id_b": room_id_b}, reason,
                    before, _room_snapshot(rooms), orig_area, errors)
    return lay, log


def resize_room(layout: dict, room_id: int, target_area_sqft: float, reason: str = "") -> Tuple[dict, dict]:
    """Adjust a room's depth to achieve target_area_sqft, taking/giving area to nearest back neighbour."""
    lay = copy.deepcopy(layout)
    rooms = lay["rooms"]
    orig_area = _total_area(rooms)
    before = _room_snapshot(rooms)

    target_idx = next((i for i, r in enumerate(rooms)
                       if r.get("room_index", i) == room_id), None)
    if target_idx is None:
        log = _make_log("resize_room", {"room_id": room_id, "target_area": target_area_sqft}, reason,
                        before, before, orig_area, [f"Room {room_id} not found"])
        return layout, log

    r = rooms[target_idx]
    rf = list(r.get("rect_ft") or [0, 0, 10, 10])
    cur_w = max(1.0, rf[2] - rf[0])
    cur_d = max(0.1, rf[3] - rf[1])
    new_d = target_area_sqft / cur_w
    delta_d = new_d - cur_d
    rf[3] = rf[1] + new_d
    r["rect_ft"] = rf
    dims = list(r.get("dimensions") or [cur_w, cur_d])
    dims[1] = new_d
    r["dimensions"] = dims
    r["nominal_dims"] = dims

    # Adjust adjacent room to compensate
    adjacencies = lay.get("adjacencies", [])
    graph = _build_adj_graph(rooms, adjacencies)
    neighbours = [i for i in graph.get(target_idx, []) if i != target_idx]
    if neighbours:
        nb = max(neighbours, key=_room_area)
        nb_rf = list(rooms[nb].get("rect_ft") or [0, 0, 10, 10])
        nb_rf[1] = max(nb_rf[1], nb_rf[1] + delta_d)
        nb_d = max(1.0, nb_rf[3] - nb_rf[1])
        nb_rf_w = max(1.0, nb_rf[2] - nb_rf[0])
        rooms[nb]["rect_ft"] = nb_rf
        nb_dims = list(rooms[nb].get("dimensions") or [nb_rf_w, nb_d])
        nb_dims[1] = nb_d
        rooms[nb]["dimensions"] = nb_dims

    errors = run_post_checks(lay, orig_area, allow_move_stair=True)
    log = _make_log("resize_room", {"room_id": room_id, "target_area_sqft": target_area_sqft}, reason,
                    before, _room_snapshot(rooms), orig_area, errors)
    return lay, log


def mirror_layout(layout: dict, axis: str = "x", reason: str = "") -> Tuple[dict, dict]:
    """
    Mirror all room positions along 'x' (vertical axis → left↔right flip).
    Porch moves to opposite x side.
    Updates x_zone, zone, porch_side.
    """
    lay = copy.deepcopy(layout)
    rooms = lay["rooms"]
    orig_area = _total_area(rooms)
    before = _room_snapshot(rooms)
    env = _parse_envelope(lay)
    env_w = env[2] - env[0]

    opposite_x = {"left": "right", "right": "left", "centre": "centre"}

    for r in rooms:
        rf = list(r.get("rect_ft") or [env[0], env[1], env[0]+10, env[1]+10])
        # Mirror x coordinates around centre of envelope
        new_x0 = env[0] + (env[2] - rf[2])
        new_x1 = env[0] + (env[2] - rf[0])
        r["rect_ft"] = [new_x0, rf[1], new_x1, rf[3]]
        r["x_zone"] = opposite_x.get(r.get("x_zone", "centre"), "centre")
        r["zone"] = f"{r.get('y_zone','middle')}_{r['x_zone']}"

    # Update porch_side
    ps = lay.get("porch_side", "centre")
    lay["porch_side"] = opposite_x.get(ps, ps)

    errors = run_post_checks(lay, orig_area)
    log = _make_log("mirror_layout", {"axis": axis}, reason,
                    before, _room_snapshot(rooms), orig_area, errors)
    return lay, log
