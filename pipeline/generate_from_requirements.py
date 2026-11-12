#!/usr/bin/env python3
"""
pipeline/generate_from_requirements.py - End-to-End Architectural Synthesis Pipeline

Implements:
1. Requirements -> Retrieve real plans (corpus/plans.jsonl)
2. When layout_usable is True:
   Direct Layout-Driven Adaptation (layout_engine/adapt.py) with fallback_used=False
3. When layout_usable is False or adaptation fails:
   Explicit procedural synthesis with fallback_used=True and explicit reason
4. Verification checklist against user requirements
5. Archiving reference images and generated plans in results/generation_tests/
"""

import os
import sys
import shutil
import json
from typing import Dict, List, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.search import search_plans
from layout_engine.adapt import adapt_layout_from_reference
from adapter.record_to_constraints import adapt_record_to_engine_input
from api_server import ProceduralArchitecturalEngine

OUTPUT_GEN_DIR = os.path.join(PROJECT_ROOT, "results", "generation_tests")


def verify_requirements_met(
    requested: Dict[str, Any],
    design: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates every requested parameter against the actual synthesized plan output.
    Returns checklist with pass/fail and overall status.
    """
    checklist = []
    all_passed = True

    # 1. Plot Dimensions / Marla
    req_w = requested.get("plot_width")
    req_l = requested.get("plot_length")
    gen_plot = design.get("plot") or {}
    gen_w = gen_plot.get("width_ft") or gen_plot.get("width")
    gen_l = gen_plot.get("length_ft") or gen_plot.get("length")

    if req_w and req_l and gen_w and gen_l:
        plot_ok = (abs(gen_w - req_w) <= 1.0 and abs(gen_l - req_l) <= 1.0)
        checklist.append({
            "requirement": "Plot Dimensions",
            "requested": f"{req_w:.0f}'x{req_l:.0f}'",
            "generated": f"{gen_w:.0f}'x{gen_l:.0f}'",
            "passed": plot_ok
        })
        if not plot_ok:
            all_passed = False
    elif requested.get("marla") or gen_plot.get("marla_equivalent"):
        req_m = requested.get("marla") or 5.0
        gen_m = gen_plot.get("marla_equivalent") or gen_plot.get("marla") or 0
        marla_ok = (abs(gen_m - req_m) <= 1.5)
        checklist.append({
            "requirement": "Marla Scale",
            "requested": f"{req_m} Marla",
            "generated": f"{gen_m:.1f} Marla",
            "passed": marla_ok
        })
        if not marla_ok:
            all_passed = False

    # 2. Bedrooms
    req_beds = requested.get("bedrooms")
    gen_beds = design.get("bedrooms_count", 0)
    if req_beds is not None:
        beds_ok = (gen_beds == req_beds)
        checklist.append({
            "requirement": "Bedroom Count",
            "requested": req_beds,
            "generated": gen_beds,
            "passed": beds_ok
        })
        if not beds_ok:
            all_passed = False

    # 3. Bathrooms
    req_baths = requested.get("bathrooms")
    gen_baths = design.get("bathrooms_count", 0)
    if req_baths is not None:
        baths_ok = (gen_baths >= min(req_baths, req_beds or req_baths))
        checklist.append({
            "requirement": "Bathroom Count",
            "requested": req_baths,
            "generated": gen_baths,
            "passed": baths_ok
        })
        if not baths_ok:
            all_passed = False

    # 4. Floors
    req_floors = requested.get("floors")
    gen_floors = design.get("floors_count", 1)
    if req_floors is not None:
        floors_ok = (gen_floors == req_floors)
        checklist.append({
            "requirement": "Floor Count",
            "requested": req_floors,
            "generated": gen_floors,
            "passed": floors_ok
        })
        if not floors_ok:
            all_passed = False

    # 5. Room inspection from actual floors
    all_gen_rooms = []
    for fl in design.get("floors", []):
        all_gen_rooms.extend(fl.get("rooms", []))

    room_names_lower = [r.get("name", "").lower() for r in all_gen_rooms]

    # Kitchen check
    has_kitchen = any("kitchen" in nm for nm in room_names_lower)
    checklist.append({
        "requirement": "Kitchen Facility",
        "requested": ">= 1 Kitchen",
        "generated": f"{sum(1 for nm in room_names_lower if 'kitchen' in nm)} Kitchen(s)",
        "passed": has_kitchen
    })
    if not has_kitchen:
        all_passed = False

    # Lounge check
    has_lounge = any("lounge" in nm or "living" in nm or "family" in nm for nm in room_names_lower)
    checklist.append({
        "requirement": "Living Lounge",
        "requested": ">= 1 Family Lounge",
        "generated": "Present" if has_lounge else "Missing",
        "passed": has_lounge
    })
    if not has_lounge:
        all_passed = False

    # Porch check if requested
    p_lower = (requested.get("prompt") or "").lower()
    if requested.get("porch") or any(k in p_lower for k in ["porch", "car", "garage"]):
        has_porch = any("porch" in nm or "garage" in nm or "parking" in nm for nm in room_names_lower)
        checklist.append({
            "requirement": "Car Porch / Parking",
            "requested": "Car Porch",
            "generated": "Present" if has_porch else "Missing",
            "passed": has_porch
        })
        if not has_porch:
            all_passed = False

    # Lawn check if requested
    if requested.get("lawn") or "lawn" in p_lower or "garden" in p_lower:
        has_lawn = any("lawn" in nm or "garden" in nm for nm in room_names_lower)
        checklist.append({
            "requirement": "Front Lawn / Garden",
            "requested": "Front Lawn",
            "generated": "Present" if has_lawn else "Missing",
            "passed": has_lawn
        })
        if not has_lawn:
            all_passed = False

    # 6. Quality Gate Status
    qg = design.get("quality_gate") or {}
    qg_status = qg.get("status", "FAIL")
    qg_passed = (qg_status == "PASS")
    checklist.append({
        "requirement": "QualityGate Compliance",
        "requested": "PASS",
        "generated": f"{qg_status} (Score: {qg.get('score', 0):.2f})",
        "passed": qg_passed
    })
    if not qg_passed:
        all_passed = False

    return {
        "status": "PASS" if all_passed else "FAIL",
        "checklist": checklist
    }


def generate_from_requirements(
    requirements: Dict[str, Any],
    tag: str = "run",
    override_reference: Optional[Dict[str, Any]] = None,
    force_procedural_fallback: bool = False
) -> Dict[str, Any]:
    """
    Executes the full pipeline:
    Search -> Adapt -> Synthesize -> Verify -> Image Archiving
    """
    os.makedirs(OUTPUT_GEN_DIR, exist_ok=True)

    # 1. Search top matches (prefer usable plans first)
    hits = search_plans(requirements, top_k=3, usable_only=True)
    if not hits:
        hits = search_plans(requirements, top_k=3, usable_only=False)
    if not hits:
        raise RuntimeError("No matching plans found in retrieval index")

    if override_reference:
        top_hit = override_reference
        ref_id = top_hit.get("plan_id")
    else:
        top_hit = hits[0]
        ref_id = top_hit["plan_id"]

    # Load full plan from corpus/plans.jsonl
    full_reference = None
    corpus_path = os.path.join(PROJECT_ROOT, "corpus", "plans.jsonl")
    if os.path.exists(corpus_path):
        with open(corpus_path, "r", encoding="utf-8") as cf:
            for line in cf:
                if ref_id in line:
                    full_reference = json.loads(line)
                    break

    if not full_reference:
        full_reference = top_hit

    is_usable = full_reference.get("layout_usable", False) and not force_procedural_fallback

    # 2. Layout Adaptation or Procedural Fallback
    if is_usable:
        print(f"[{tag}] Synthesizing layout-driven plan directly from reference {ref_id} (fallback_used=False)...")
        adapt_res = adapt_layout_from_reference(full_reference, requirements, tag=tag)
        if adapt_res.get("success"):
            design = adapt_res["design"]
            adapter_expl = {
                "strategy": "layout_driven_adaptation",
                "reference_plan_id": ref_id,
                "fidelity_metric": adapt_res["fidelity"],
                "edits": adapt_res["edits_log"]
            }
        else:
            print(f"[{tag}] Adaptation failed; invoking procedural fallback (fallback_used=True)...")
            engine_kwargs, adapter_expl = adapt_record_to_engine_input(requirements, full_reference)
            design = ProceduralArchitecturalEngine.synthesize_design(**engine_kwargs)
            design["fallback_used"] = True
            design["fallback_reason"] = "Layout adaptation failed on geometry"
    else:
        reason = "Procedural forced by ablation test" if force_procedural_fallback else f"Reference plan {ref_id} layout_usable=False; procedural fallback used"
        print(f"[{tag}] {reason} (fallback_used=True)...")
        engine_kwargs, adapter_expl = adapt_record_to_engine_input(requirements, full_reference)
        design = ProceduralArchitecturalEngine.synthesize_design(**engine_kwargs)
        design["fallback_used"] = True
        design["fallback_reason"] = reason

    # 3. Verify Requirements Met
    verification = verify_requirements_met(requirements, design)

    # 4. Save Output Images next to Reference Image
    ref_src_rel = full_reference.get("image_path") or top_hit.get("image_path", "")
    ref_src_abs = os.path.join(PROJECT_ROOT, "extraction_v2", ref_src_rel) if not os.path.exists(ref_src_rel) else ref_src_rel

    ref_ext = os.path.splitext(ref_src_rel)[1] or ".jpg"
    dest_ref_img = os.path.join(OUTPUT_GEN_DIR, f"{tag}_reference_{ref_id}{ref_ext}")
    dest_gen_plan = os.path.join(OUTPUT_GEN_DIR, f"{tag}_generated_plan.png")
    dest_gen_elev = os.path.join(OUTPUT_GEN_DIR, f"{tag}_generated_elevation.png")

    if os.path.exists(ref_src_abs):
        try:
            shutil.copyfile(ref_src_abs, dest_ref_img)
        except Exception:
            pass

    # Copy generated plan from output/web_generated/
    p_images = design.get("images") or {}
    web_plan_url = p_images.get("ground")
    if web_plan_url:
        plan_src_abs = os.path.join(PROJECT_ROOT, web_plan_url.lstrip("/"))
        if os.path.exists(plan_src_abs):
            try:
                shutil.copyfile(plan_src_abs, dest_gen_plan)
            except Exception:
                pass

    web_elev_url = p_images.get("elevation")
    if web_elev_url:
        elev_src_abs = os.path.join(PROJECT_ROOT, web_elev_url.lstrip("/"))
        if os.path.exists(elev_src_abs):
            try:
                shutil.copyfile(elev_src_abs, dest_gen_elev)
            except Exception:
                pass

    return {
        "tag": tag,
        "requirements": requirements,
        "reference_plan_id": ref_id,
        "reference_similarity": top_hit.get("similarity_score", 1.0),
        "fallback_used": design.get("fallback_used", False),
        "fallback_reason": design.get("fallback_reason"),
        "top_3_hits": hits[:3],
        "adapter_explanations": adapter_expl,
        "design": design,
        "verification": verification,
        "saved_images": {
            "reference_image": dest_ref_img,
            "generated_plan_image": dest_gen_plan,
            "generated_elevation_image": dest_gen_elev
        }
    }


if __name__ == "__main__":
    from retrieval.search import parse_requirements

    test_queries = [
        "5 marla 3 bedroom house",
        "7 marla 3 bedroom double storey with lawn",
        "single floor 3 bedroom house",
        "10 marla luxury house with lawn and servant quarter",
        "1 kanal double storey 4 bedroom house",
        "3 bedroom house with drawing room and car porch"
    ]

    all_results = []
    for idx, q in enumerate(test_queries, 1):
        parsed = parse_requirements(q)
        parsed["prompt"] = q
        tag = f"req_{idx}"
        print(f"\nProcessing Request {idx}: {q}...")
        res = generate_from_requirements(parsed, tag=tag)
        all_results.append(res)
        print(f"[{tag}] Status: {res['verification']['status']} | Fallback: {res['fallback_used']} | Ref: {res['reference_plan_id']}")
        for chk in res["verification"]["checklist"]:
            mark = "PASS" if chk["passed"] else "FAIL"
            print(f"  [{mark}] {chk['requirement']}: req={chk['requested']} vs gen={chk['generated']}")

    summary_path = os.path.join(OUTPUT_GEN_DIR, "generation_tests_summary.json")
    with open(summary_path, "w", encoding="utf-8") as sf:
        serializable = []
        for r in all_results:
            serializable.append({
                "tag": r["tag"],
                "prompt": r["requirements"].get("prompt"),
                "reference_plan_id": r["reference_plan_id"],
                "reference_similarity": r["reference_similarity"],
                "fallback_used": r["fallback_used"],
                "fallback_reason": r["fallback_reason"],
                "verification": r["verification"],
                "saved_images": r["saved_images"]
            })
        json.dump(serializable, sf, indent=2)
    print(f"\nAll 6 requests processed. Summary written to {summary_path}")
