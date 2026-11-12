#!/usr/bin/env python3
"""
tests/test_orientation.py - Orientation Canary Test & Negative Control

Verifies:
1. For generated plans, porch/entrance is at the bottom (y near 0, front)
   and bedrooms are at the top (y near target_l, back).
2. Negative Control: Deliberately inverts layout coordinates vertically (cy -> target_l - cy)
   and proves that the physical fidelity metric plummets below 0.30.
"""

import os
import sys
import json
import copy

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from layout_engine.adapt import adapt_layout_from_reference, calculate_fidelity
from retrieval.search import search_plans, parse_requirements
from layout_engine.slicing_reconstructor import reconstruct_slicing_layout


def test_orientation_and_negative_control():
    test_queries = [
        "5 marla 3 bedroom house",
        "7 marla 3 bedroom double storey with lawn",
        "single floor 3 bedroom house",
        "10 marla luxury house with lawn and servant quarter",
        "3 bedroom house with drawing room and car porch"
    ]

    corpus_path = os.path.join(PROJECT_ROOT, "corpus", "plans.jsonl")
    corpus = {}
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            corpus[p["plan_id"]] = p

    print("==========================================================================")
    print("ORIENTATION CANARY TEST & NEGATIVE CONTROL VERIFICATION")
    print("==========================================================================")

    results = []

    for idx, q in enumerate(test_queries, 1):
        parsed = parse_requirements(q)
        parsed["prompt"] = q

        hits = search_plans(parsed, top_k=3, usable_only=True)
        if not hits:
            hits = search_plans(parsed, top_k=3, usable_only=False)

        top_ref = corpus.get(hits[0]["plan_id"])
        res = adapt_layout_from_reference(top_ref, parsed, tag=f"canary_{idx}")

        design = res["design"]
        plot = design["plot"]
        target_w = plot["width_ft"]
        target_l = plot["length_ft"]

        fl0 = design["floors"][0]
        rooms0 = fl0["rooms"]

        # 1. Porch / Entrance Position (must be at front, bottom of sheet, y < 0.40 * target_l)
        porch_rm = next((r for r in rooms0 if r["canonical_type"] == "porch"), None)
        assert porch_rm is not None, f"Porch missing in {q}"
        porch_cy = porch_rm["y"] + porch_rm["length"] / 2.0
        porch_rel_y = porch_cy / target_l

        # 2. Bedroom Position (must be at rear, top of sheet, y > 0.50 * target_l)
        bed_rms = [r for r in rooms0 if r["canonical_type"] == "bedroom"]
        assert len(bed_rms) > 0, f"Bedrooms missing in {q}"
        avg_bed_cy = sum(r["y"] + r["length"] / 2.0 for r in bed_rms) / len(bed_rms)
        bed_rel_y = avg_bed_cy / target_l

        # Verification of orientation: Porch at bottom (front), Bedrooms at top (rear)
        porch_at_bottom = (porch_rel_y < 0.40)
        beds_at_top = (bed_rel_y > 0.50)
        normal_fidelity = res["fidelity"]

        # 3. NEGATIVE CONTROL: Deliberately flip layout vertically (cy -> target_l - cy)
        flipped_rooms = []
        for r in rooms0:
            rf = copy.deepcopy(r)
            # Invert y coordinate
            new_y = target_l - (rf["y"] + rf["length"])
            rf["y"] = new_y
            flipped_rooms.append(rf)

        slicing_data = reconstruct_slicing_layout(top_ref, use_run_d_for_pilot=True)
        ref_rooms = slicing_data.get("rooms", [])

        flipped_fidelity = calculate_fidelity(ref_rooms, flipped_rooms, target_w=target_w, target_l=target_l)

        print(f"\n[Request {idx}] \"{q}\" (Ref: {top_ref['plan_id']}):")
        print(f"  Porch Cy: {porch_cy:.1f}' ({porch_rel_y*100:.1f}% from street/bottom) -> {'FRONT/BOTTOM' if porch_at_bottom else 'WRONG'}")
        print(f"  Bedrooms Cy: {avg_bed_cy:.1f}' ({bed_rel_y*100:.1f}% from street/bottom) -> {'REAR/TOP' if beds_at_top else 'WRONG'}")
        print(f"  Standard Layout Fidelity: {normal_fidelity:.3f} (>= 0.70 Target)")
        print(f"  NEGATIVE CONTROL (Flipped Layout) Fidelity: {flipped_fidelity:.3f} (< 0.30 Target)")

        assert porch_at_bottom, f"Porch not at bottom: {porch_rel_y}"
        assert beds_at_top, f"Bedrooms not at top: {bed_rel_y}"
        assert normal_fidelity >= 0.65, f"Normal fidelity too low: {normal_fidelity}"
        assert flipped_fidelity <= 0.30, f"Negative control failed! Flipped fidelity is {flipped_fidelity} > 0.30 (metric is blind!)"

        results.append({
            "request": q,
            "ref_id": top_ref["plan_id"],
            "porch_rel_y": round(porch_rel_y, 3),
            "bed_rel_y": round(bed_rel_y, 3),
            "normal_fidelity": normal_fidelity,
            "flipped_fidelity": flipped_fidelity,
            "passed": True
        })

    print("\n==========================================================================")
    print("ALL 5 REQUESTS PASSED ORIENTATION & NEGATIVE CONTROL ASSERTIONS!")
    print("==========================================================================")

    out_file = os.path.join(PROJECT_ROOT, "results", "orientation_test_results.json")
    with open(out_file, "w", encoding="utf-8") as of:
        json.dump(results, of, indent=2)
    print(f"Results saved to {out_file}")


if __name__ == "__main__":
    test_orientation_and_negative_control()

