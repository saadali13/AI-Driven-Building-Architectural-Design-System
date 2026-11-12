#!/usr/bin/env python3
"""
layout_engine/plan_edits.py - Requirement Planner

Diffs a reference layout's program against user requirements and produces
an ordered, logged list of edit operations from edit_ops.py.

Entry points:
  plan_edits(reference_layout, requirements, prompt_text="") -> (layout, ops_log, feasibility)

Where:
  reference_layout - dict as loaded from corpus/layouts/<id>.json
  requirements     - dict with keys: bedrooms, bathrooms, floors, marla,
                     servant, porch_side, lawn, courtyard, prompt (raw text)
  prompt_text      - optional raw text for positional parsing

Returns:
  (new_layout, ops_log, feasibility)
  feasibility = {"feasible": bool, "reason": str or None}
"""

import re
import copy
from typing import Dict, Any, List, Tuple, Optional

from layout_engine.edit_ops import (
    add_room, remove_room, convert_room, swap_rooms, move_room,
    mirror_layout, resize_room, _room_area, _total_area, run_post_checks
)

# ---------------------------------------------------------------------------
# Hard limits (used for impossible-request detection)
# ---------------------------------------------------------------------------

MIN_SQFT_PER_BEDROOM = 100.0
MIN_SQFT_OTHER = 200.0  # kitchen + lounge + bathrooms + stair minimum


def check_feasibility(marla: Optional[float], bedrooms: int) -> Tuple[bool, Optional[str]]:
    """Return (feasible, reason). Reason is None if feasible."""
    if marla is None:
        return True, None
    area_sqft = marla * 225.0
    min_needed = bedrooms * MIN_SQFT_PER_BEDROOM + MIN_SQFT_OTHER
    if min_needed > area_sqft:
        return False, (
            f"IMPOSSIBLE: {bedrooms} bedrooms need at least {min_needed:.0f} sqft "
            f"({bedrooms}×{MIN_SQFT_PER_BEDROOM:.0f} bed + {MIN_SQFT_OTHER:.0f} other), "
            f"but {marla:.1f} marla = {area_sqft:.0f} sqft. "
            f"Maximum feasible bedrooms on {marla:.1f} marla: "
            f"{int((area_sqft - MIN_SQFT_OTHER) / MIN_SQFT_PER_BEDROOM)}."
        )
    return True, None


# ---------------------------------------------------------------------------
# Positional request parser
# ---------------------------------------------------------------------------

POSITIONAL_PATTERNS = [
    (re.compile(r'\bkitchen\s+at\s+(the\s+)?(back|rear)\b', re.I), "kitchen_rear"),
    (re.compile(r'\bkitchen\s+at\s+(the\s+)?(front)\b', re.I),    "kitchen_front"),
    (re.compile(r'\bporch\s+(on\s+)?(left|right)\b', re.I),       "porch_side"),
    (re.compile(r'\bcar\s*porch\s+(on\s+)?(left|right)\b', re.I), "porch_side"),
    (re.compile(r'\bmaster\s+bedroom\s+(on\s+)?(ground\s+floor)\b', re.I), "master_ground"),
    (re.compile(r'\b(back|rear)\s+lawn\b', re.I),                  "rear_lawn"),
    (re.compile(r'\bfront\s+lawn\b', re.I),                        "front_lawn"),
    (re.compile(r'\bcourtyard\b', re.I),                           "courtyard"),
]


def parse_position_requests(prompt_text: str) -> Dict[str, Any]:
    """Extract positional requirements from raw prompt text."""
    result = {}
    for pat, key in POSITIONAL_PATTERNS:
        m = pat.search(prompt_text)
        if m:
            if key == "porch_side":
                side = m.group(2).lower() if m.group(2) else "left"
                result["porch_side"] = side
            elif key in ("kitchen_rear", "kitchen_front"):
                result["kitchen_zone"] = "back" if "rear" in key else "front"
            elif key == "master_ground":
                result["master_ground_floor"] = True
            else:
                result[key] = True
    return result


# ---------------------------------------------------------------------------
# Diff and plan
# ---------------------------------------------------------------------------

def diff_programs(reference_layout: dict, requirements: dict) -> List[dict]:
    """
    Compare reference room counts to requested counts.
    Returns a list of requirement diffs:
        [{requirement, source, op_sequence: [str]}]
    """
    rooms = reference_layout.get("rooms", [])
    from collections import Counter
    ref_counts = Counter(r.get("canonical_type") for r in rooms)

    req_beds = requirements.get("bedrooms")
    req_servant = requirements.get("servant", 0)
    req_lawn = requirements.get("lawn", 0)
    req_porch_side = requirements.get("porch_side")
    req_kitchen_zone = requirements.get("kitchen_zone")

    diffs = []

    # Bedrooms
    if req_beds is not None:
        cur_beds = ref_counts.get("bedroom", 0)
        delta = req_beds - cur_beds
        if delta > 0:
            diffs.append({
                "requirement": f"bedrooms {cur_beds} -> {req_beds} (+{delta})",
                "source": "user",
                "op_sequence": [f"add_room(bedroom) x{delta} [upper floor first, else split rear]"],
                "delta": delta,
                "op": "add_bedrooms",
                "count": delta,
            })
        elif delta < 0:
            diffs.append({
                "requirement": f"bedrooms {cur_beds} -> {req_beds} ({delta})",
                "source": "user",
                "op_sequence": [f"convert_room(bedroom->study) or remove_room x{abs(delta)}"],
                "delta": delta,
                "op": "remove_bedrooms",
                "count": abs(delta),
            })

    # Servant quarter
    cur_servant = ref_counts.get("servant_quarter", 0)
    if req_servant and cur_servant == 0:
        diffs.append({
            "requirement": "add servant quarter",
            "source": "user",
            "op_sequence": ["add_room(servant_quarter, back_corner)"],
            "op": "add_servant",
        })

    # Lawn
    if req_lawn and ref_counts.get("lawn", 0) == 0:
        diffs.append({
            "requirement": "add lawn",
            "source": "default",
            "op_sequence": ["add_room(lawn, front)"],
            "op": "add_lawn",
        })

    # Porch side
    cur_porch_side = reference_layout.get("porch_side", "centre")
    if req_porch_side and req_porch_side != cur_porch_side:
        diffs.append({
            "requirement": f"porch_side {cur_porch_side} -> {req_porch_side}",
            "source": "user",
            "op_sequence": ["mirror_layout(x) if opposite side, else move_room(porch)"],
            "op": "move_porch",
            "target_side": req_porch_side,
        })

    # Kitchen zone
    if req_kitchen_zone:
        kitchen_rooms = [r for r in rooms if r.get("canonical_type") == "kitchen"]
        if kitchen_rooms:
            cur_kz = kitchen_rooms[0].get("y_zone", "back")
            if cur_kz != req_kitchen_zone:
                kit_id = kitchen_rooms[0].get("room_index", 0)
                diffs.append({
                    "requirement": f"kitchen zone {cur_kz} -> {req_kitchen_zone}",
                    "source": "user",
                    "op_sequence": [f"move_room(kitchen_id={kit_id}, to_y_zone={req_kitchen_zone})"],
                    "op": "move_kitchen",
                    "room_id": kit_id,
                    "target_zone": req_kitchen_zone,
                })

    return diffs


def plan_edits(
    reference_layout: dict,
    requirements: dict,
    prompt_text: str = "",
) -> Tuple[dict, List[dict], Dict[str, Any]]:
    """
    Main entry point.
    Returns (adapted_layout, ops_log, feasibility_dict).

    feasibility_dict = {"feasible": bool, "reason": str|None}
    ops_log = list of log entries from edit_ops.py
    """
    # 1. Feasibility gate
    marla = requirements.get("marla") or requirements.get("marla_225")
    req_beds = requirements.get("bedrooms", 3)
    feasible, reason = check_feasibility(marla, req_beds)
    if not feasible:
        return reference_layout, [], {"feasible": False, "reason": reason}

    # 2. Merge positional requests from prompt text
    pos_reqs = parse_position_requests(prompt_text)
    merged = {**requirements, **pos_reqs}

    # 3. Build diff list
    diffs = diff_programs(reference_layout, merged)

    layout = copy.deepcopy(reference_layout)
    ops_log = []

    for diff in diffs:
        op = diff.get("op", "")
        reason_str = diff.get("requirement", "")

        if op == "add_bedrooms":
            count = diff.get("count", 1)
            for i in range(count):
                layout, log = add_room(
                    layout, "bedroom", "back",
                    target_size_sqft=130.0,
                    reason=f"User requested +{count} bedrooms (bedroom {i+1}/{count})",
                    new_name=f"Bedroom {i+1}",
                )
                ops_log.append(log)
                if log["result"] == "failed":
                    # Try upper floor zone
                    layout, log2 = add_room(
                        layout, "bedroom", "front",
                        target_size_sqft=120.0,
                        reason=f"Retry: add bedroom to front zone",
                        new_name=f"Bedroom {i+1}",
                    )
                    ops_log.append(log2)

        elif op == "remove_bedrooms":
            count = diff.get("count", 1)
            bedroom_rooms = [r for r in layout.get("rooms", [])
                             if r.get("canonical_type") == "bedroom"]
            for i, br in enumerate(bedroom_rooms[:count]):
                bid = br.get("room_index", i)
                # Convert to study rather than hard-delete
                layout, log = convert_room(
                    layout, bid, "study",
                    reason=f"User requested -{count} bedrooms: convert bedroom to study",
                )
                ops_log.append(log)

        elif op == "add_servant":
            layout, log = add_room(
                layout, "servant_quarter", "back",
                target_size_sqft=80.0,
                reason="User requested servant quarter: add in rear corner",
                new_name="Servant Quarter",
            )
            ops_log.append(log)

        elif op == "add_lawn":
            layout, log = add_room(
                layout, "lawn", "front",
                target_size_sqft=100.0,
                reason="Add front lawn (default for plot size)",
                new_name="Front Lawn",
            )
            ops_log.append(log)

        elif op == "move_porch":
            target_side = diff.get("target_side", "left")
            cur_side = layout.get("porch_side", "centre")
            # Mirror if porch needs to move to opposite side
            if (cur_side == "left" and target_side == "right") or \
               (cur_side == "right" and target_side == "left") or \
               (cur_side == "centre" and target_side in ("left", "right")):
                layout, log = mirror_layout(
                    layout, axis="x",
                    reason=f"User requested porch on {target_side}: mirroring layout",
                )
            else:
                porch_rooms = [r for r in layout.get("rooms", [])
                               if r.get("canonical_type") == "porch"]
                if porch_rooms:
                    pid = porch_rooms[0].get("room_index", 0)
                    layout, log = move_room(
                        layout, pid, "front", target_side,
                        reason=f"Move porch to {target_side}",
                    )
                else:
                    log = {"op": "move_porch", "result": "failed",
                           "failure_reason": ["No porch room found"]}
            ops_log.append(log)

        elif op == "move_kitchen":
            kid = diff.get("room_id", 0)
            tz = diff.get("target_zone", "back")
            layout, log = move_room(
                layout, kid, tz, "centre",
                reason=f"User requested kitchen at {tz}",
            )
            ops_log.append(log)

    return layout, ops_log, {"feasible": True, "reason": None}

