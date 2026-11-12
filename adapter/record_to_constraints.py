#!/usr/bin/env python3
"""
adapter/record_to_constraints.py - Bridge between Retrieved CAD Records and Synthesis Engine

Takes (user_requirements, retrieved_record) and prepares the exact input parameters
for ProceduralArchitecturalEngine.synthesize_design.

Applies:
- Guidance from reference: plot dimensions (if not user-specified), strategy archetype,
  typical room dimensions from verified CAD data.
- User precedence: User's explicit requirements (bedrooms, bathrooms, floors, plot size)
  always override reference values.
- Explainability: Returns lists of "kept from reference", "changed to meet requirements",
  and "dropped guidance".
"""

import os
import sys
import json
from typing import Dict, List, Any, Tuple, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def infer_strategy_from_record(record: Dict[str, Any]) -> str:
    """Infers the most appropriate architectural planning strategy from the retrieved record."""
    rooms = record.get("rooms", [])
    room_names = [r.get("printed_name", "").lower() for r in rooms]
    canonical_types = [r.get("canonical_type", "") for r in rooms]

    # Check for courtyard / OTS / garden centric
    if any(k in " ".join(room_names) for k in ["courtyard", "patio", "open to sky", "ots"]) or "OTS" in canonical_types:
        return "courtyard_inward_focus"
    # Check for rear garden / lawn
    if any(k in " ".join(room_names) for k in ["rear lawn", "back yard", "garden", "backyard"]):
        return "rear_garden_promenade"
    # Check for prominent corridor / passage
    if any(k in " ".join(room_names) for k in ["passage", "corridor", "gallery"]):
        return "side_corridor_gallery"
    # Default to standard Pakistani central lounge / family hub
    return "central_family_lounge"


def adapt_record_to_engine_input(
    user_requirements: Dict[str, Any],
    retrieved_record: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    """
    Transforms user requirements and retrieved reference into engine synthesis arguments.
    """
    kept_from_ref = []
    changed_to_req = []
    dropped_guidance = []

    # 1. Plot Dimensions
    ref_plot = retrieved_record.get("plot") or {}
    ref_w = ref_plot.get("width_ft") or retrieved_record.get("plot_width")
    ref_l = ref_plot.get("depth_ft") or retrieved_record.get("plot_depth")

    user_w = user_requirements.get("plot_width")
    user_l = user_requirements.get("plot_length")

    if user_w and user_l:
        final_w = float(user_w)
        final_l = float(user_l)
        if ref_w and ref_l:
            changed_to_req.append(f"Plot dimensions: User specified {final_w:.0f}'x{final_l:.0f}' (reference had {ref_w:.0f}'x{ref_l:.0f}')")
        else:
            changed_to_req.append(f"Plot dimensions: User specified {final_w:.0f}'x{final_l:.0f}'")
    elif ref_w and ref_l:
        final_w = float(ref_w)
        final_l = float(ref_l)
        kept_from_ref.append(f"Plot dimensions: Kept reference dimensions {final_w:.0f}'x{final_l:.0f}'")
    else:
        # Default fallback based on marla
        marla = user_requirements.get("marla", 5.0)
        if marla <= 4.0:
            final_w, final_l = 20.0, 40.0
        elif marla <= 6.0:
            final_w, final_l = 25.0, 45.0
        elif marla <= 8.5:
            final_w, final_l = 30.0, 60.0
        elif marla <= 12.0:
            final_w, final_l = 35.0, 65.0
        else:
            final_w, final_l = 50.0, 90.0
        changed_to_req.append(f"Plot dimensions: Synthesized standard dimensions {final_w:.0f}'x{final_l:.0f}' from {marla} Marla")

    # 2. Bedrooms & Bathrooms (User always wins)
    ref_counts = retrieved_record.get("counts") or {}
    ref_beds = ref_counts.get("bedroom", 0)
    ref_baths = ref_counts.get("bathroom", 0)

    user_beds = user_requirements.get("bedrooms")
    if user_beds is not None:
        final_beds = int(user_beds)
        if ref_beds and ref_beds != final_beds:
            changed_to_req.append(f"Bedrooms: User requested {final_beds} (reference had {ref_beds})")
        else:
            kept_from_ref.append(f"Bedrooms: Kept matching count of {final_beds}")
    else:
        final_beds = max(1, ref_beds or 3)
        kept_from_ref.append(f"Bedrooms: Adopted reference count of {final_beds}")

    user_baths = user_requirements.get("bathrooms")
    if user_baths is not None:
        final_baths = int(user_baths)
        if ref_baths and ref_baths != final_baths:
            changed_to_req.append(f"Bathrooms: User requested {final_baths} (reference had {ref_baths})")
        else:
            kept_from_ref.append(f"Bathrooms: Kept matching count of {final_baths}")
    else:
        final_baths = max(1, ref_baths or final_beds)
        kept_from_ref.append(f"Bathrooms: Adopted reference count of {final_baths}")

    # 3. Floors
    user_floors = user_requirements.get("floors")
    ref_floors = retrieved_record.get("floors", 1)
    if user_floors is not None:
        final_floors = int(user_floors)
        if ref_floors and ref_floors != final_floors:
            changed_to_req.append(f"Floors: User requested {final_floors} (reference had {ref_floors})")
        else:
            kept_from_ref.append(f"Floors: Kept matching floor count of {final_floors}")
    else:
        final_floors = max(1, ref_floors or 2)
        kept_from_ref.append(f"Floors: Adopted reference floor count of {final_floors}")

    # 4. Strategy & Layout Archetype
    strategy = infer_strategy_from_record(retrieved_record)
    kept_from_ref.append(f"Layout Planning Strategy: Inferred '{strategy}' from reference floor plan topology")

    # 5. Room Schedule & Dimensions Guidance
    custom_room_dims = []
    ref_rooms = retrieved_record.get("rooms", [])
    for r in ref_rooms:
        dims = r.get("dimensions")
        if dims and isinstance(dims, (list, tuple)) and len(dims) == 2 and dims[0] and dims[1]:
            ctype = r.get("canonical_type")
            pname = r.get("printed_name")
            if ctype in ["master_bedroom", "bedroom", "kitchen", "lounge", "drawing"]:
                try:
                    w_ft = round(float(dims[0]), 1)
                    l_ft = round(float(dims[1]), 1)
                    if 6.0 <= w_ft <= 35.0 and 6.0 <= l_ft <= 35.0:
                        custom_room_dims.append({
                            "name": pname or ctype,
                            "canonical_type": ctype,
                            "width": w_ft,
                            "length": l_ft
                        })
                except Exception:
                    pass

    if custom_room_dims:
        kept_from_ref.append(f"Room Dimensions: Adopted {len(custom_room_dims)} verified room sizes from reference CAD drawing")
    else:
        changed_to_req.append("Room Dimensions: Using standard statutory procedural sizing (reference sizes not provided)")

    # 6. Dropped Guidance (as required by specification)
    dropped_guidance.append("Dropped normalized (x, y) coordinate positions: Engine procedural layout solver enforces statutory setbacks and wall alignments")
    dropped_guidance.append("Dropped raw wall pixel contours: Engine generates true parametric walls with 9\" exterior / 4.5\" interior standards")
    dropped_guidance.append("Dropped raster title block & margin annotations: Clean CAD vector output generated")

    # Style
    style = user_requirements.get("style", "spanish")
    shape = user_requirements.get("shape", "rectangular")

    # Formulate effective prompt for the procedural engine
    prompt = user_requirements.get("prompt")
    if not prompt:
        prompt = (
            f"{int(final_w * final_l / 225.0)} Marla {style.capitalize()} house ({int(final_w)}x{int(final_l)}) "
            f"with {final_beds} bedrooms, {final_baths} bathrooms, {final_floors} floors, car porch and drawing room"
        )

    engine_input = {
        "prompt": prompt,
        "plot_width": final_w,
        "plot_length": final_l,
        "floors": final_floors,
        "bedrooms": final_beds,
        "bathrooms": final_baths,
        "style": style,
        "shape": shape,
        "strategy": strategy,
        "custom_room_dimensions": custom_room_dims
    }

    explanations = {
        "kept_from_reference": kept_from_ref,
        "changed_to_meet_requirements": changed_to_req,
        "dropped_guidance": dropped_guidance
    }

    return engine_input, explanations


if __name__ == "__main__":
    from retrieval.search import search
    test_req = {
        "prompt": "10 Marla Spanish villa (35x65) with 4 bedrooms, 4 bathrooms, 2 floors",
        "marla": 10.0,
        "plot_width": 35.0,
        "plot_length": 65.0,
        "bedrooms": 4,
        "bathrooms": 4,
        "floors": 2
    }
    hits = search(test_req, k=1)
    if hits:
        top_hit = hits[0]
        # Load full record
        rec_path = os.path.join(PROJECT_ROOT, "extraction_v2", "records", f"{top_hit['record_id']}.json")
        with open(rec_path, 'r', encoding='utf-8') as f:
            full_rec = json.load(f)

        engine_args, expl = adapt_record_to_engine_input(test_req, full_rec)
        print("Engine Arguments:")
        for k, v in engine_args.items():
            print(f"  {k}: {v}")
        print("\nExplanations:")
        print("  Kept:", expl["kept_from_reference"])
        print("  Changed:", expl["changed_to_meet_requirements"])
        print("  Dropped:", expl["dropped_guidance"])
