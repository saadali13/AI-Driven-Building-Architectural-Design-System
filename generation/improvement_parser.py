"""
generation/improvement_parser.py
Rule-Based Improvement Parser with Structured Operation Synthesis.

Parses natural language edit requests into structured architectural operations:
- RESIZE_ROOM: Adjusts room boundaries by expanding into adjacent space or along exterior wall.
- MOVE_ROOM: Repositions room to a designated spatial zone (front, mid, rear).
- SWAP_ROOMS: Exchanges locations and boundaries of two topologically compatible spaces.
- ADD_ROOM: Synthesizes a new functional room (bathroom, powder room, servant quarter, store).
- REMOVE_ROOM: Deletes an optional room and merges its footprint into an adjoining space.
- CHANGE_ADJACENCY: Re-routes connectivity or shifts rooms to become directly adjacent.
- MOVE_STAIRS: Relocates vertical circulation core (staircase) to front/rear/porch.
- CHANGE_FLOOR: Moves a room from ground floor to upper floor or vice versa.
"""

import re
from typing import Dict, Any, List, Optional


class ImprovementParser:
    """
    Deterministic rule-based parser that converts user modification text
    into a validated list of structured architectural operations.
    """

    ROOM_SYNONYMS = {
        "dirty kitchen": ["dirty kitchen", "diry kichen", "dirty mess kitchen", "mess kitchen", "scullery", "wet kitchen", "grease kitchen", "wok kitchen", "pantry", "service scullery", "dirty cooking"],
        "master bedroom": ["master bedroom", "master bed", "m.bed", "mbed", "main bedroom", "primary bedroom", "master suite"],
        "guest bedroom": ["guest bedroom", "guest bed", "drawing bed"],
        "bedroom": ["bedroom", "bed", "bed 1", "bed 2", "bed 3", "bed 4", "bed 5", "bed 6"],
        "kitchen": ["kitchen", "main kitchen", "show kitchen", "chef's kitchen", "clean kitchen"],
        "dining": ["dining", "dining room", "dining area", "dining hall"],
        "drawing room": ["drawing room", "drawing", "formal drawing", "guest salon", "formal sitting", "guest drawing", "drawing salon"],
        "lounge": ["lounge", "tv lounge", "family lounge", "living room", "living", "family hall", "tv room", "entertainment lounge"],
        "powder room": ["powder room", "powder", "guest toilet", "powder bath", "guest w/c"],
        "bathroom": ["bathroom", "bath", "washroom", "en-suite", "ensuite", "attached bath"],
        "staircase": ["staircase", "stairs", "stair", "stair lobby", "mumty"],
        "car porch": ["car porch", "porch", "garage", "carport", "driveway"],
        "servant quarter": ["servant quarter", "servant room", "servant", "maid room", "maid's room"],
        "ots": ["ots", "lightwell", "courtyard", "airwell"],
        "lawn": ["lawn", "garden", "front lawn"],
        "foyer": ["foyer", "grand entrance", "grand entry", "entry lobby", "entrance lobby", "entrance foyer", "vestibule", "entrance", "entry", "main entrance", "front entry", "front entrance"]
    }

    @classmethod
    def _normalize_room_name(cls, text: str) -> Optional[str]:
        t_low = text.lower()
        # Flatten all synonyms into (length, canonical_name, synonym) tuples
        # Sorted strictly by synonym length descending so multi-word phrases match first
        # (e.g. "dirty kitchen" matches before "kitchen", "master bedroom" before "bedroom")
        all_pairs = []
        for canonical_name, syns in cls.ROOM_SYNONYMS.items():
            for s in syns:
                all_pairs.append((len(s), canonical_name, s))
        all_pairs.sort(key=lambda x: x[0], reverse=True)

        for _, canonical_name, s in all_pairs:
            if re.search(r'\b' + re.escape(s) + r'\b', t_low):
                return canonical_name
        return None

    @classmethod
    def parse_improvements(cls, improvement_text: str) -> List[Dict[str, Any]]:
        """
        Parses user improvement text into a list of structured edit operations.
        """
        text = improvement_text.strip()
        operations: List[Dict[str, Any]] = []
        if not text:
            return operations

        # 0. Typo normalization & phonetic correction
        text = re.sub(r'\bdiry\b', 'dirty', text, flags=re.IGNORECASE)
        text = re.sub(r'\bkichen\b', 'kitchen', text, flags=re.IGNORECASE)
        text = re.sub(r'\bconect\b', 'connect', text, flags=re.IGNORECASE)
        text = re.sub(r'\bocup\b', 'occupy', text, flags=re.IGNORECASE)
        text = re.sub(r'\bteh\b', 'the', text, flags=re.IGNORECASE)
        text = re.sub(r'\bseperate\b', 'separate', text, flags=re.IGNORECASE)

        handled_rooms = set()

        # 0.1 Check for Dirty Kitchen isolation / connectivity rules
        # e.g. "dirty kitchen is connect to the formal drawing room and diry kichen is only door connect to the main kitchen"
        if re.search(r'\bdirty kitchen\b', text, re.IGNORECASE) and (
            re.search(r'\b(?:drawing room|drawing|formal drawing)\b', text, re.IGNORECASE) or
            re.search(r'\b(?:only door|only connect|connect to main kitchen)\b', text, re.IGNORECASE)
        ):
            operations.append({
                "op": "ISOLATE_DIRTY_KITCHEN",
                "target_room": "dirty kitchen",
                "connect_to": "kitchen",
                "disconnect_from": "drawing room",
                "description": "Isolate Dirty Kitchen: remove drawing room door, connect strictly to Main Kitchen and service OTS"
            })
            handled_rooms.add("dirty kitchen")

        # 0.2 Check for Grand Entrance / Foyer removal or integration into lounge
        # e.g. "remove the grand entrance this ocup the area", "grand entry is why separate to the tv lounge"
        if re.search(r'\b(?:grand entrance|grand entry|entrance foyer|foyer|entry lobby|entrance)\b', text, re.IGNORECASE) and (
            re.search(r'\b(?:remove|delete|eliminate|without|separate|occup|merge|open|not look good)\b', text, re.IGNORECASE)
        ):
            operations.append({
                "op": "REMOVE_ROOM",
                "room_name": "foyer",
                "merge_into": "lounge",
                "description": "Remove grand entrance / foyer and merge spatial area directly into family TV lounge"
            })
            handled_rooms.add("foyer")

        # 1. First check for SWAP operations across the full text or clauses
        swap_matches = re.finditer(r'(?:swap|exchange)\s+([a-zA-Z\s]+?)\s+(?:and|with)\s+([a-zA-Z\s]+?)(?:$|[,;]|\b(?:then|also)\b)', text, re.IGNORECASE)
        for swap_m in swap_matches:
            r1 = cls._normalize_room_name(swap_m.group(1))
            r2 = cls._normalize_room_name(swap_m.group(2))
            if r1 and r2 and r1 != r2:
                operations.append({
                    "op": "SWAP_ROOMS",
                    "room_1": r1,
                    "room_2": r2,
                    "description": f"Swap locations of {r1.title()} and {r2.title()}"
                })
                # Mask out this swap phrase so other checks don't get confused
                text = text[:swap_m.start()] + " " + text[swap_m.end():]

        # Split remaining clauses if separated by comma, semicolon, or "also" / "then" / "and"
        clauses = re.split(r'[,;]|\b(?:also|then|and)\b', text, flags=re.IGNORECASE)

        for clause in clauses:
            c = clause.strip()
            if not c:
                continue
            cl = c.lower()

            # 2. RESIZE_ROOM: Enlarge / Bigger / Expand
            if any(k in cl for k in ["bigger", "larger", "enlarge", "expand", "increase", "widen"]):
                r = cls._normalize_room_name(cl)
                if r:
                    pct_m = re.search(r'(\d+)\s*%', cl)
                    if pct_m:
                        pct = float(pct_m.group(1)) / 100.0
                    elif "slightly" in cl or "little" in cl:
                        pct = 0.10
                    elif "much" in cl or "significantly" in cl or "very" in cl:
                        pct = 0.35
                    else:
                        pct = 0.20
                    operations.append({
                        "op": "RESIZE_ROOM",
                        "room_name": r,
                        "action": "enlarge",
                        "delta_pct": pct,
                        "description": f"Increase size of {r.title()} by {int(pct * 100)}%"
                    })
                    continue

            # 3. RESIZE_ROOM: Shrink / Smaller / Reduce
            if any(k in cl for k in ["smaller", "shrink", "reduce", "decrease"]):
                r = cls._normalize_room_name(cl)
                if r:
                    pct_m = re.search(r'(\d+)\s*%', cl)
                    if pct_m:
                        pct = -float(pct_m.group(1)) / 100.0
                    else:
                        pct = -0.50 if "below" in cl or "much" in cl else -0.20
                    operations.append({
                        "op": "RESIZE_ROOM",
                        "room_name": r,
                        "action": "shrink",
                        "delta_pct": pct,
                        "description": f"Reduce size of {r.title()} by {int(abs(pct) * 100)}%"
                    })
                    continue

            # 4. MOVE_STAIRS
            if "stair" in cl or "staircase" in cl:
                if any(k in cl for k in ["shift", "move", "relocate"]):
                    target_loc = "rear" if "rear" in cl else ("front" if "front" in cl or "porch" in cl else "lobby")
                    operations.append({
                        "op": "MOVE_STAIRS",
                        "target_location": target_loc,
                        "description": f"Relocate staircase to {target_loc} circulation zone"
                    })
                    continue

            # 5. REMOVE_ROOM: e.g. "remove dirty kitchen", "delete powder room", "servant room hata do"
            remove_keywords = ["remove", "delete", "drop", "eliminate", "without", "discard", "exclude", "hatado", "hata do", "khatam", "no need"]
            if any(re.search(r'\b' + re.escape(k) + r'\b', cl) for k in remove_keywords):
                r = cls._normalize_room_name(cl)
                if r and r not in handled_rooms:
                    operations.append({
                        "op": "REMOVE_ROOM",
                        "room_name": r,
                        "description": f"Remove {r.title()} from layout and merge footprint into adjacent space"
                    })
                    handled_rooms.add(r)
                    continue

            # 6. MOVE_ROOM / CHANGE_ADJACENCY: e.g. "move kitchen next to dining"
            move_next_m = re.search(r'\b(?:move|shift|place)\s+([a-zA-Z\s]+?)\s+next\s+to\s+([a-zA-Z\s]+)', cl)
            if move_next_m:
                r1 = cls._normalize_room_name(move_next_m.group(1))
                r2 = cls._normalize_room_name(move_next_m.group(2))
                if r1 and r2:
                    operations.append({
                        "op": "CHANGE_ADJACENCY",
                        "room_name": r1,
                        "target_adjacent_room": r2,
                        "description": f"Move {r1.title()} adjacent to {r2.title()}"
                    })
                    continue

            # Move room to zone (rear, front, side)
            move_keywords = ["move", "shift", "relocate", "transfer"]
            if any(re.search(r'\b' + re.escape(k) + r'\b', cl) for k in move_keywords):
                r = cls._normalize_room_name(cl)
                if r and r not in handled_rooms:
                    zone = "rear" if "rear" in cl else ("front" if "front" in cl else "central")
                    operations.append({
                        "op": "MOVE_ROOM",
                        "room_name": r,
                        "target_zone": zone,
                        "description": f"Shift {r.title()} toward {zone} zone"
                    })
                    continue

            # 7. ADD_ROOM: e.g. "add one more bathroom", "add a servant quarter", "add powder room"
            add_keywords = ["add", "include", "provide", "create", "banao", "daalo"]
            if any(re.search(r'\b' + re.escape(k) + r'\b', cl) for k in add_keywords):
                r = cls._normalize_room_name(cl)
                if r:
                    floor_target = 1 if any(k in cl for k in ["first floor", "upper floor", "upstairs"]) else (
                        2 if any(k in cl for k in ["rooftop", "roof"]) else 0
                    )
                    operations.append({
                        "op": "ADD_ROOM",
                        "room_type": r,
                        "target_floor": floor_target,
                        "description": f"Add new {r.title()} on {'Rooftop' if floor_target == 2 else ('First Floor' if floor_target == 1 else 'Ground Floor')}"
                    })
                    continue

        # Strict deduplication while preserving ordering
        deduped_ops = []
        seen_keys = set()
        for op in operations:
            op_key = (op.get("op"), op.get("room_name") or op.get("target_room") or op.get("room_1") or op.get("target_location"))
            if op_key not in seen_keys:
                seen_keys.add(op_key)
                deduped_ops.append(op)

        return deduped_ops
