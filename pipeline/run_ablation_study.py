#!/usr/bin/env python3
"""
pipeline/run_ablation_study.py - Controlled Ablation Study

Compares 3 conditions across 2 distinct user requests:
  Condition A: Rank-1 Real Reference (Layout-Driven, fallback_used=False)
  Condition B: Rank-3 Real Reference (Layout-Driven, fallback_used=False)
  Condition C: Old master_* Procedural Catalog (Procedural Fallback, fallback_used=True)

Records zone layouts, room topologies, fidelity metrics, and saves outputs in:
  results/ablation_study.md
  results/generation_tests/ablation_*
"""

import os
import sys
import json
import shutil
from typing import Dict, List, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.search import search_plans, parse_requirements
from pipeline.generate_from_requirements import generate_from_requirements

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "results")
GEN_DIR = os.path.join(OUTPUT_DIR, "generation_tests")


def run_ablation():
    os.makedirs(GEN_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    test_cases = [
        {
            "name": "Case 1: 5 Marla 3-Bedroom Residence",
            "prompt": "5 marla 3 bedroom house",
            "tag_prefix": "ablation_c1"
        },
        {
            "name": "Case 2: 7 Marla 3-Bedroom Double Storey with Lawn",
            "prompt": "7 marla 3 bedroom double storey with lawn",
            "tag_prefix": "ablation_c2"
        }
    ]

    ablation_results = []

    for tc in test_cases:
        prompt = tc["prompt"]
        req = parse_requirements(prompt)
        req["prompt"] = prompt
        prefix = tc["tag_prefix"]

        print(f"\n=======================================================")
        print(f"Running Ablation on: {tc['name']} ({prompt})")
        print(f"=======================================================")

        hits = search_plans(req, top_k=3, usable_only=True)
        if len(hits) < 3:
            hits = search_plans(req, top_k=3, usable_only=False)

        rank_1_ref = hits[0]
        rank_3_ref = hits[2] if len(hits) >= 3 else hits[-1]

        # Condition A: Rank-1 Real Reference
        tag_a = f"{prefix}_condA_rank1"
        print(f"\n--- Condition A: Rank-1 Reference ({rank_1_ref['plan_id']}) ---")
        res_a = generate_from_requirements(req, tag=tag_a, override_reference=rank_1_ref, force_procedural_fallback=False)

        # Condition B: Rank-3 Real Reference
        tag_b = f"{prefix}_condB_rank3"
        print(f"\n--- Condition B: Rank-3 Reference ({rank_3_ref['plan_id']}) ---")
        res_b = generate_from_requirements(req, tag=tag_b, override_reference=rank_3_ref, force_procedural_fallback=False)

        # Condition C: Old master_* Procedural Catalog Fallback
        tag_c = f"{prefix}_condC_procedural"
        print(f"\n--- Condition C: Procedural Fallback (Old master_* catalogs) ---")
        res_c = generate_from_requirements(req, tag=tag_c, override_reference=rank_1_ref, force_procedural_fallback=True)

        ablation_results.append({
            "case": tc["name"],
            "prompt": prompt,
            "conditions": {
                "A_rank1": res_a,
                "B_rank3": res_b,
                "C_procedural": res_c
            }
        })

    # Compile Markdown Report
    report_lines = [
        "# Architectural Generation Ablation Study",
        "",
        "This study rigorously evaluates the three generation modalities:",
        "1. **Condition A (Rank-1 Reference)**: Layout-driven adaptation following the top retrieved real blueprint.",
        "2. **Condition B (Rank-3 Reference)**: Layout-driven adaptation following an alternative retrieved real blueprint.",
        "3. **Condition C (Old master_* Catalogs)**: Purely procedural synthesis using hardcoded master layout catalogs.",
        "",
        "---",
        ""
    ]

    for item in ablation_results:
        c_name = item["case"]
        prompt = item["prompt"]
        conds = item["conditions"]
        res_a = conds["A_rank1"]
        res_b = conds["B_rank3"]
        res_c = conds["C_procedural"]

        report_lines.append(f"## {c_name}")
        report_lines.append(f"**Prompt**: `{prompt}`\n")
        report_lines.append("| Metric / Feature | Condition A (Rank-1 Real) | Condition B (Rank-3 Real) | Condition C (Procedural Catalog) |")
        report_lines.append("| :--- | :--- | :--- | :--- |")

        # Ref ID
        report_lines.append(f"| **Reference Plan ID** | `{res_a['reference_plan_id']}` | `{res_b['reference_plan_id']}` | `{res_c['reference_plan_id']} (unused)` |")

        # Fallback used
        report_lines.append(f"| **Fallback Used** | `{res_a['fallback_used']}` | `{res_b['fallback_used']}` | `{res_c['fallback_used']}` |")
        report_lines.append(f"| **Fallback Reason** | `{res_a.get('fallback_reason') or 'None (Layout Adapted)'}` | `{res_b.get('fallback_reason') or 'None (Layout Adapted)'}` | `{res_c.get('fallback_reason')}` |")

        # Fidelity Metric
        fid_a = res_a["design"].get("fidelity_metric", 0.0)
        fid_b = res_b["design"].get("fidelity_metric", 0.0)
        fid_c = res_c["design"].get("fidelity_metric", 0.0)
        report_lines.append(f"| **Fidelity Metric** | **{fid_a:.3f}** | **{fid_b:.3f}** | **{fid_c:.3f}** (N/A) |")

        # Bedroom Count
        beds_a = res_a["design"].get("bedrooms_count", 0)
        beds_b = res_b["design"].get("bedrooms_count", 0)
        beds_c = res_c["design"].get("bedrooms_count", 0)
        report_lines.append(f"| **Bedrooms** | {beds_a} | {beds_b} | {beds_c} |")

        # Bathroom Count
        baths_a = res_a["design"].get("bathrooms_count", 0)
        baths_b = res_b["design"].get("bathrooms_count", 0)
        baths_c = res_c["design"].get("bathrooms_count", 0)
        report_lines.append(f"| **Bathrooms** | {baths_a} | {baths_b} | {baths_c} |")

        # Floor Count
        fl_a = res_a["design"].get("floors_count", 0)
        fl_b = res_b["design"].get("floors_count", 0)
        fl_c = res_c["design"].get("floors_count", 0)
        report_lines.append(f"| **Floor Count** | {fl_a} | {fl_b} | {fl_c} |")

        # Quality Gate
        qg_a = res_a["design"].get("quality_gate", {})
        qg_b = res_b["design"].get("quality_gate", {})
        qg_c = res_c["design"].get("quality_gate", {})
        report_lines.append(f"| **QualityGate Status** | {qg_a.get('status')} ({qg_a.get('score', 0):.2f}) | {qg_b.get('status')} ({qg_b.get('score', 0):.2f}) | {qg_c.get('status')} ({qg_c.get('score', 0):.2f}) |")

        # Layout Topology Description
        def get_topology_desc(d):
            fl0 = d.get("floors", [{}])[0]
            rms = fl0.get("rooms", [])
            rear = [r.get("name") for r in rms if r.get("y_zone") == "back"]
            mid = [r.get("name") for r in rms if r.get("y_zone") == "middle"]
            front = [r.get("name") for r in rms if r.get("y_zone") == "front"]
            return f"Rear: {', '.join(rear[:3])}<br>Mid: {', '.join(mid[:3])}<br>Front: {', '.join(front[:3])}"

        top_a = get_topology_desc(res_a["design"])
        top_b = get_topology_desc(res_b["design"])
        top_c = get_topology_desc(res_c["design"])
        report_lines.append(f"| **Spatial Zone Layout** | {top_a} | {top_b} | {top_c} |")

        # Image Links
        report_lines.append(f"| **Blueprint Image** | ![{res_a['tag']}]({res_a['saved_images']['generated_plan_image']}) | ![{res_b['tag']}]({res_b['saved_images']['generated_plan_image']}) | ![{res_c['tag']}]({res_c['saved_images']['generated_plan_image']}) |")
        report_lines.append(f"| **Reference Blueprint** | ![{res_a['tag']}_ref]({res_a['saved_images']['reference_image']}) | ![{res_b['tag']}_ref]({res_b['saved_images']['reference_image']}) | N/A (Procedural) |")
        report_lines.append("")

    report_path = os.path.join(OUTPUT_DIR, "ablation_study.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_lines))

    print(f"\nAblation study completed successfully. Written to {report_path}")


if __name__ == "__main__":
    run_ablation()

