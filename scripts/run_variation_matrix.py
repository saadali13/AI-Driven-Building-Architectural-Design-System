#!/usr/bin/env python3
"""
scripts/run_variation_matrix.py

Executes Phase 2 Controlled Experiment Matrix across 5 plot scales
(3 Marla, 5 Marla, 7 Marla, 10 Marla, 1 Kanal) and variants V1 to V10.
Logs all telemetry, parsed requirements, quality gate results, archetype/strategy,
paths to drawings, and computes pairwise diversity matrices via tools/measure_diversity.py.
"""

import os
import sys
import time
import json
import glob
import traceback
from typing import Dict, List, Any, Tuple
from collections import Counter

# Ensure project root in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipeline_runner import run_generation_pipeline
from requirements.parser import NaturalLanguageRequirementsParser, InfeasibleProgramError
from tools.measure_diversity import compare_plans, generate_heatmap_and_matrix

VARIATION_EXPERIMENTS_DIR = os.path.join(PROJECT_ROOT, "variation_experiments")
os.makedirs(VARIATION_EXPERIMENTS_DIR, exist_ok=True)

# Define experiment specifications per plot size
EXPERIMENT_SPECS = {
    "3_marla": {
        "label": "3 Marla (20'x35')",
        "variants": [
            {"id": "V1", "name": "Baseline", "prompt": "3 Marla 2 bedroom family house"},
            {"id": "V2", "name": "Bedroom_Count", "prompt": "3 Marla 3 bedroom house"},
            {"id": "V3", "name": "Style", "prompt": "3 Marla 2 bedroom Spanish style house"},
            {"id": "V4", "name": "Room_Program", "prompt": "3 Marla 2 bedroom house with study and dirty kitchen"},
            {"id": "V5", "name": "Special_Feature", "prompt": "3 Marla 2 bedroom house with central courtyard and patio"},
            {"id": "V6", "name": "Storeys", "prompt": "3 Marla 1 bedroom single storey house"},
            {"id": "V7", "name": "Parking", "prompt": "3 Marla 2 bedroom house with no porch"},
            {"id": "V8", "name": "Layout_Intent", "prompt": "3 Marla 2 bedroom house with linear spine corridor and straight stair"},
            {"id": "V9", "name": "Paraphrase_Control", "prompt": "Compact 2-bed double storey home on 3 Marla plot"},
            {"id": "V10_1", "name": "Repeat_1", "prompt": "3 Marla 2 bedroom family house"},
            {"id": "V10_2", "name": "Repeat_2", "prompt": "3 Marla 2 bedroom family house"},
            {"id": "V10_3", "name": "Repeat_3", "prompt": "3 Marla 2 bedroom family house"},
            {"id": "V10_4", "name": "Repeat_4", "prompt": "3 Marla 2 bedroom family house"},
            {"id": "V10_5", "name": "Repeat_5", "prompt": "3 Marla 2 bedroom family house"},
            # Infeasibility stress test
            {"id": "V_INFEASIBLE", "name": "Infeasible_Stress_Test", "prompt": "3 Marla 2-storey house with 6 bedrooms and 100% covered zero setback"}
        ]
    },
    "5_marla": {
        "label": "5 Marla (25'x45')",
        "variants": [
            {"id": "V1", "name": "Baseline", "prompt": "5 Marla 3 bedroom modern house"},
            {"id": "V2", "name": "Bedroom_Count", "prompt": "5 Marla 4 bedroom house"},
            {"id": "V3", "name": "Style", "prompt": "5 Marla 3 bedroom Spanish villa"},
            {"id": "V4", "name": "Room_Program", "prompt": "5 Marla 3 bedroom house with dirty kitchen and drawing room"},
            {"id": "V5", "name": "Special_Feature", "prompt": "5 Marla 3 bedroom house with central courtyard and lightwell"},
            {"id": "V6", "name": "Storeys", "prompt": "5 Marla 2 bedroom single storey house"},
            {"id": "V7", "name": "Parking", "prompt": "5 Marla 3 bedroom house with double car porch"},
            {"id": "V8", "name": "Layout_Intent", "prompt": "5 Marla 3 bedroom house with open-concept living and floating stair"},
            {"id": "V9", "name": "Paraphrase_Control", "prompt": "Contemporary double-storey 3 bed residence on 5 Marla plot"},
            {"id": "V10_1", "name": "Repeat_1", "prompt": "5 Marla 3 bedroom modern house"},
            {"id": "V10_2", "name": "Repeat_2", "prompt": "5 Marla 3 bedroom modern house"},
            {"id": "V10_3", "name": "Repeat_3", "prompt": "5 Marla 3 bedroom modern house"},
            {"id": "V10_4", "name": "Repeat_4", "prompt": "5 Marla 3 bedroom modern house"},
            {"id": "V10_5", "name": "Repeat_5", "prompt": "5 Marla 3 bedroom modern house"},
            {"id": "V_INFEASIBLE", "name": "Infeasible_Stress_Test", "prompt": "5 Marla 2-storey house with 8 bedrooms and 2 full kitchens on Ground Floor"}
        ]
    },
    "7_marla": {
        "label": "7 Marla (30'x55')",
        "variants": [
            {"id": "V1", "name": "Baseline", "prompt": "7 Marla 4 bedroom modern house"},
            {"id": "V2", "name": "Bedroom_Count", "prompt": "7 Marla 5 bedroom house"},
            {"id": "V3", "name": "Style", "prompt": "7 Marla 4 bedroom Spanish style house"},
            {"id": "V4", "name": "Room_Program", "prompt": "7 Marla 4 bedroom house with dirty kitchen and executive study"},
            {"id": "V5", "name": "Special_Feature", "prompt": "7 Marla 4 bedroom house with grand atrium and lightwell"},
            {"id": "V6", "name": "Storeys", "prompt": "7 Marla 3 bedroom single storey house"},
            {"id": "V7", "name": "Parking", "prompt": "7 Marla 4 bedroom house with double car garage"},
            {"id": "V8", "name": "Layout_Intent", "prompt": "7 Marla 4 bedroom house with curved rotunda foyer and formal salon"},
            {"id": "V9", "name": "Paraphrase_Control", "prompt": "4-bedroom family home on 7 Marla plot with two floors"},
            {"id": "V10_1", "name": "Repeat_1", "prompt": "7 Marla 4 bedroom modern house"},
            {"id": "V10_2", "name": "Repeat_2", "prompt": "7 Marla 4 bedroom modern house"},
            {"id": "V10_3", "name": "Repeat_3", "prompt": "7 Marla 4 bedroom modern house"},
            {"id": "V10_4", "name": "Repeat_4", "prompt": "7 Marla 4 bedroom modern house"},
            {"id": "V10_5", "name": "Repeat_5", "prompt": "7 Marla 4 bedroom modern house"},
            {"id": "V_INFEASIBLE", "name": "Infeasible_Stress_Test", "prompt": "7 Marla 2-storey house with 6 bedrooms"}
        ]
    },
    "10_marla": {
        "label": "10 Marla (35'x65')",
        "variants": [
            {"id": "V1", "name": "Baseline", "prompt": "10 Marla 4 bedroom family house"},
            {"id": "V2", "name": "Bedroom_Count", "prompt": "10 Marla 5 bedroom luxury residence"},
            {"id": "V3", "name": "Style", "prompt": "10 Marla 4 bedroom Contemporary house"},
            {"id": "V4", "name": "Room_Program", "prompt": "10 Marla 4 bedroom house with dirty kitchen, drawing room, and servant quarter"},
            {"id": "V5", "name": "Special_Feature", "prompt": "10 Marla 4 bedroom house with central courtyard and water patio"},
            {"id": "V6", "name": "Storeys", "prompt": "10 Marla 3 bedroom single storey residence"},
            {"id": "V7", "name": "Parking", "prompt": "10 Marla 4 bedroom house with double car garage"},
            {"id": "V8", "name": "Layout_Intent", "prompt": "10 Marla 4 bedroom house with separate guest wing and side corridor"},
            {"id": "V9", "name": "Paraphrase_Control", "prompt": "Spacious two-floor 4 bed residence on 10 Marla plot"},
            {"id": "V10_1", "name": "Repeat_1", "prompt": "10 Marla 4 bedroom family house"},
            {"id": "V10_2", "name": "Repeat_2", "prompt": "10 Marla 4 bedroom family house"},
            {"id": "V10_3", "name": "Repeat_3", "prompt": "10 Marla 4 bedroom family house"},
            {"id": "V10_4", "name": "Repeat_4", "prompt": "10 Marla 4 bedroom family house"},
            {"id": "V10_5", "name": "Repeat_5", "prompt": "10 Marla 4 bedroom family house"},
            {"id": "V_INFEASIBLE", "name": "Infeasible_Stress_Test", "prompt": "10 Marla 2-storey house with 8 bedrooms"}
        ]
    },
    "1_kanal": {
        "label": "1 Kanal (50'x90')",
        "variants": [
            {"id": "V1", "name": "Baseline", "prompt": "1 Kanal 5 bedroom executive mansion"},
            {"id": "V2", "name": "Bedroom_Count", "prompt": "1 Kanal 6 bedroom palace"},
            {"id": "V3", "name": "Style", "prompt": "1 Kanal 5 bedroom Spanish colonial mansion"},
            {"id": "V4", "name": "Room_Program", "prompt": "1 Kanal 5 bedroom house with dirty kitchen, formal banquet dining, and servant quarter"},
            {"id": "V5", "name": "Special_Feature", "prompt": "1 Kanal 5 bedroom house with grand double-height atrium and swimming pool patio"},
            {"id": "V6", "name": "Storeys", "prompt": "1 Kanal 3 bedroom single storey luxury villa"},
            {"id": "V7", "name": "Parking", "prompt": "1 Kanal 5 bedroom house with triple car porch"},
            {"id": "V8", "name": "Layout_Intent", "prompt": "1 Kanal 5 bedroom mansion with monumental curved rotunda entrance and private rear master pavilion"},
            {"id": "V9", "name": "Paraphrase_Control", "prompt": "Luxury two-storey 5-bed villa on 1 Kanal residential plot"},
            {"id": "V10_1", "name": "Repeat_1", "prompt": "1 Kanal 5 bedroom executive mansion"},
            {"id": "V10_2", "name": "Repeat_2", "prompt": "1 Kanal 5 bedroom executive mansion"},
            {"id": "V10_3", "name": "Repeat_3", "prompt": "1 Kanal 5 bedroom executive mansion"},
            {"id": "V10_4", "name": "Repeat_4", "prompt": "1 Kanal 5 bedroom executive mansion"},
            {"id": "V10_5", "name": "Repeat_5", "prompt": "1 Kanal 5 bedroom executive mansion"},
            {"id": "V_INFEASIBLE", "name": "Infeasible_Stress_Test", "prompt": "1 Kanal 2-storey house with 10 bedrooms and 100% covered zero lawn"}
        ]
    }
}


def run_experiment_matrix():
    master_log = []
    print("===========================================================================")
    print("STARTING CONTROLLED ARCHITECTURAL DIVERSITY EXPERIMENT MATRIX (PHASE 2)")
    print("===========================================================================")

    for scale_key, spec in EXPERIMENT_SPECS.items():
        scale_label = spec["label"]
        scale_dir = os.path.join(VARIATION_EXPERIMENTS_DIR, scale_key)
        os.makedirs(scale_dir, exist_ok=True)
        print(f"\n" + "=" * 75)
        print(f"EVALUATING PLOT SCALE: {scale_label}")
        print("=" * 75)

        successful_canonical_plans: List[Tuple[str, str]] = []

        for var in spec["variants"]:
            v_id = var["id"]
            v_name = var["name"]
            prompt = var["prompt"]
            out_var_dir = os.path.join(scale_dir, v_id)
            os.makedirs(out_var_dir, exist_ok=True)

            print(f"\n--- [Run {scale_key} | {v_id}: {v_name}] ---")
            print(f"Prompt: \"{prompt}\"")

            t0 = time.time()
            log_entry = {
                "plot_scale": scale_key,
                "variant_id": v_id,
                "variant_name": v_name,
                "prompt": prompt,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "UNKNOWN",
                "runtime_seconds": 0.0,
                "parsed_requirements": None,
                "strategy_selected": None,
                "canonical_plan_id": None,
                "canonical_json_path": None,
                "quality_score": None,
                "failures": [],
                "room_counts": {},
                "stair_position": None,
                "drawings": {}
            }

            try:
                # 1. Parse prompt
                prog = NaturalLanguageRequirementsParser.parse(prompt, validate=False)
                log_entry["parsed_requirements"] = {
                    "plot_category": prog.plot_category,
                    "floor_count": prog.floor_count,
                    "requested_room_counts": prog.requested_room_counts,
                    "ground_room_counts": prog.ground_room_counts,
                    "dirty_kitchen_count": prog.dirty_kitchen_count,
                    "car_porch_capacity": prog.car_porch_capacity,
                    "stair_type": prog.stair_type,
                    "spatial_typology": prog.spatial_typology,
                    "is_feasible": prog.is_feasible,
                    "infeasibility_reasons": prog.infeasibility_reasons,
                    "hard_constraints": prog.hard_constraints
                }

                # 2. Check if canonical plan already generated
                existing_can = glob.glob(os.path.join(out_var_dir, "*_canonical.json"))
                if existing_can:
                    from dataset.schema.canonical import CanonicalFloorPlan
                    with open(existing_can[0], "r", encoding="utf-8") as cf:
                        plan = CanonicalFloorPlan.model_validate_json(cf.read())
                    print(f"      [RESUME] Found existing generated plan: {existing_can[0]}")
                else:
                    plan = run_generation_pipeline(
                        prompt=prompt,
                        output_dir=out_var_dir,
                        export_format="png",
                        render_3d=False
                    )

                elapsed = round(time.time() - t0, 2)
                log_entry["runtime_seconds"] = elapsed

                if plan:
                    log_entry["status"] = "SUCCESS"
                    log_entry["canonical_plan_id"] = plan.metadata.plan_id
                    log_entry["strategy_selected"] = plan.metadata.provenance.get("planning_strategy", "N/A")
                    c_path = os.path.join(out_var_dir, f"{plan.metadata.plan_id}_canonical.json")
                    log_entry["canonical_json_path"] = c_path

                    # Room summary
                    r_counts = Counter(r.room_type for r in plan.rooms)
                    log_entry["room_counts"] = dict(r_counts)
                    log_entry["storeys"] = plan.metadata.floor_count

                    # Stair info
                    for r in plan.rooms:
                        if "stair" in (r.room_name + r.room_id).lower():
                            log_entry["stair_position"] = {
                                "centroid": r.centroid,
                                "type": r.metadata.get("stair_type", plan.metadata.provenance.get("stair_type", "dogleg"))
                            }
                            break

                    # Quality report
                    q_rep_path = os.path.join(out_var_dir, "quality_report.json")
                    if os.path.exists(q_rep_path):
                        with open(q_rep_path, "r", encoding="utf-8") as qf:
                            q_data = json.load(qf)
                        log_entry["quality_score"] = q_data.get("quality_score", 1.0)
                        log_entry["failures"] = q_data.get("failures", [])

                    # Drawings
                    for f in os.listdir(out_var_dir):
                        if f.endswith(".png"):
                            log_entry["drawings"][f] = os.path.join(out_var_dir, f)

                    successful_canonical_plans.append((f"{v_id}_{v_name}", c_path))
                    print(f"-> SUCCESS in {elapsed}s | Strategy: {log_entry['strategy_selected']} | Rooms: {len(plan.rooms)}")

                else:
                    # Infeasible or rejected
                    log_entry["status"] = "REJECTED_INFEASIBLE"
                    q_rep_path = os.path.join(out_var_dir, "quality_report.json")
                    if os.path.exists(q_rep_path):
                        with open(q_rep_path, "r", encoding="utf-8") as qf:
                            q_data = json.load(qf)
                        log_entry["infeasibility_reasons"] = q_data.get("infeasibility_reasons", [])
                        log_entry["failures"] = q_data.get("failures", [])
                    print(f"-> REJECTED_INFEASIBLE in {elapsed}s | Reasons: {log_entry.get('infeasibility_reasons')}")

            except InfeasibleProgramError as ipe:
                elapsed = round(time.time() - t0, 2)
                log_entry["status"] = "REJECTED_INFEASIBLE"
                log_entry["runtime_seconds"] = elapsed
                log_entry["infeasibility_reasons"] = [str(ipe)]
                print(f"-> INFEASIBLE_PROGRAM detected: {ipe}")

            except Exception as e:
                elapsed = round(time.time() - t0, 2)
                log_entry["status"] = "ERROR"
                log_entry["runtime_seconds"] = elapsed
                log_entry["error"] = str(e)
                log_entry["traceback"] = traceback.format_exc()
                print(f"-> ERROR in {elapsed}s: {e}")

            # Save individual run log
            with open(os.path.join(out_var_dir, "run_log.json"), "w", encoding="utf-8") as rf:
                json.dump(log_entry, rf, indent=2)

            master_log.append(log_entry)

        # After all variants for this scale, compute pairwise diversity matrix
        if len(successful_canonical_plans) >= 2:
            print(f"\nComputing Pairwise Diversity Matrix for {scale_label} ({len(successful_canonical_plans)} plans)...")
            csv_path = os.path.join(scale_dir, "pairwise_diversity_matrix.csv")
            png_path = os.path.join(scale_dir, "pairwise_diversity_heatmap.png")
            res_mat = generate_heatmap_and_matrix(
                plan_paths=successful_canonical_plans,
                out_csv_path=csv_path,
                out_png_path=png_path,
                plot_label=scale_label
            )
            print(f"-> Matrix saved to {csv_path} and Heatmap saved to {png_path}")
            print(f"-> Distinct Plan Clusters identified: {res_mat['distinct_clusters']} / {len(successful_canonical_plans)}")

    # Write Master Log
    master_log_path = os.path.join(VARIATION_EXPERIMENTS_DIR, "master_experiment_log.json")
    with open(master_log_path, "w", encoding="utf-8") as mf:
        json.dump(master_log, mf, indent=2)
    print(f"\n===========================================================================")
    print(f"EXPERIMENT MATRIX COMPLETE: Saved master log to {master_log_path}")
    print(f"===========================================================================")


if __name__ == "__main__":
    run_experiment_matrix()
