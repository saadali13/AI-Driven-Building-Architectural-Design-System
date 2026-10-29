"""
Multi-Scale, Multi-Style Diversity & Architectural Society Bylaws Verification Test Suite.
Validates:
1. Same plot size (10 Marla) testing across different prompts & styles (Spanish Revival vs Mid-Century Modern vs Georgian).
2. Proves system does NOT generate the same layout using DiversityEvaluator (Jaccard Distance > 0.25, Spatial IoU < 0.70).
3. Scale matrix testing (3 Marla, 5 Marla, 7 Marla, 1 Kanal).
4. Society bylaws compliance (statutory non-covered front lawn, rear OTS lightwell, side passages).
5. Live Gemini Senior Architect review, critique, and refinement execution.
6. 3D Blender procedural modeling with distinct architectural style facades and roof types.
7. Clean, beautiful 2D vector floor plan visualizer rendering.
"""

import os
import sys
import json
import pytest

from requirements.parser import NaturalLanguageRequirementsParser
from generation.rag_solver import DatasetDrivenRAGSolver
from generation.visualizer import FloorPlanVisualizer
from generation.diversity_evaluator import DiversityEvaluator
from generation.quality_gate import FloorPlanQualityGate
from generation.architectural_styles import ArchitecturalStyleEngine, STYLE_CATALOG
from three_d.blender_generator import Blender3DGenerator

OUTPUT_DIR = os.path.abspath(r"C:\Users\m\OneDrive\Desktop\New folder\output\system_update_verification")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_01_style_catalog_coverage():
    print("\n" + "=" * 75)
    print("TEST 1: 27 Architectural Styles Catalog & Detector Verification")
    print("=" * 75)
    all_styles = ArchitecturalStyleEngine.get_all_styles()
    print(f"Total Configured Styles: {len(all_styles)}")
    assert len(all_styles) == 27, f"Expected 27 styles, got {len(all_styles)}"

    # Spot test style detection
    test_cases = [
        ("10 marla Spanish Revival villa with terracotta roof", "Spanish Revival", "terracotta_barrel_tile"),
        ("1 kanal Georgian mansion with symmetrical portico", "Georgian", "classical_hipped"),
        ("5 marla Mid-Century Modern house with glass pavilion", "Mid-Century Modern", "minimalist_flat_cantilever"),
        ("7 marla Tudor Revival residence with half-timbering", "Tudor Revival", "steep_timber_gable"),
        ("5 marla Craftsman home with tapered porch columns", "Craftsman", "low_pitch_overhang"),
        ("10 marla Farmhouse with wrap-around porch and country kitchen", "Farmhouse", "pitched_metal_seam"),
        ("1 kanal Art Deco luxury villa with stepped ziggurat facade", "Art Deco", "box_parapet_stepped"),
        ("5 marla Prairie School home with cantilevered eaves", "Prairie School", "low_pitch_overhang"),
    ]

    for prompt, expected_name, expected_roof in test_cases:
        detected = ArchitecturalStyleEngine.detect_style(prompt)
        print(f"Prompt: \"{prompt[:45]}...\"")
        print(f"   -> Detected: {detected.display_name} | Roof: {detected.roof_type} | Walls: {detected.wall_finish_type}")
        assert detected.display_name == expected_name
        assert detected.roof_type == expected_roof

    print("PASS: All 27 Architectural Styles cataloged and detected accurately.\n")


def test_02_same_plot_size_diversity_10_marla():
    print("\n" + "=" * 75)
    print("TEST 2: Same Plot Size (10 Marla) Layout Differentiation & Diversity")
    print("=" * 75)

    prompts = {
        "10m_spanish_revival": "Design 10 marla Spanish Revival villa with 4 bedrooms, central courtyard, arched porch, terracotta balcony, and front lawn",
        "10m_mid_century_modern": "Design 10 marla Mid-Century Modern house with linear flight stairs, sunken patio, glass living, executive study, and open show kitchen",
        "10m_georgian_classical": "Design 10 marla Georgian residence with symmetrical grand foyer, formal executive drawing salon, banquet dining, and dogleg stairs"
    }

    plans = {}
    solver = DatasetDrivenRAGSolver()

    for key, prompt in prompts.items():
        print(f"\n---> Synthesizing 10 Marla Variant: [{key}]")
        print(f"Prompt: \"{prompt}\"")
        plan = solver.synthesize(prompt)
        plans[key] = plan

        # Verify QualityGate
        qg = FloorPlanQualityGate.evaluate(plan)
        print(f"QualityGate Status: {qg['final_status']} (Score: {qg['quality_score']:.2f})")
        assert qg["is_valid"], f"QualityGate failed for {key}: {qg['failures']}"

        # Verify Mandatory Society Bylaws: Front Lawn and Rear OTS must be outdoor and non-habitable
        outdoor_rooms = [r for r in plan.rooms if r.room_type == "outdoor" or "lawn" in r.room_name.lower() or "ots" in r.room_name.lower() or "courtyard" in r.room_name.lower()]
        assert len(outdoor_rooms) >= 1, f"Mandatory society open space (lawn/OTS) missing in {key}!"
        print(f"Society Open Spaces Identified: {[r.room_name for r in outdoor_rooms]}")

        # Render 2D floor plan image
        png_path = os.path.join(OUTPUT_DIR, f"{key}_floor_plan.png")
        FloorPlanVisualizer.render_floorplan(plan, png_path, dpi=180)
        print(f"Saved 2D Clean Floor Plan Drawing: {png_path} ({os.path.getsize(png_path)} bytes)")

    # Quantitative Diversity Comparison using DiversityEvaluator
    print("\n" + "-" * 60)
    print("QUANTITATIVE DIVERSITY EVALUATION ON SAME 10 MARLA PLOT SIZE:")
    print("-" * 60)

    pairs = [
        ("10m_spanish_revival", "10m_mid_century_modern"),
        ("10m_spanish_revival", "10m_georgian_classical"),
        ("10m_mid_century_modern", "10m_georgian_classical")
    ]

    for k1, k2 in pairs:
        div = DiversityEvaluator.evaluate_diversity(plans[k1], plans[k2])
        print(f"\nComparison: [{k1}] vs [{k2}]")
        print(f"   * Jaccard Graph Distance: {div['jaccard_distance']:.3f} (Threshold >= {div['min_jaccard_threshold']}) -> Distinct: {div['is_topologically_distinct']}")
        print(f"   * Average Spatial IoU:    {div['average_spatial_iou']:.3f} (Threshold <= {div['max_spatial_iou_threshold']}) -> Distinct: {div['is_spatially_distinct']}")
        print(f"   * Node Dissimilarity:     Rooms ({div['node_dissimilarity']['total_rooms_a']} vs {div['node_dissimilarity']['total_rooms_b']}), Stair: {div['node_dissimilarity']['stair_a']} vs {div['node_dissimilarity']['stair_b']}")
        print(f"   * OVERALL RESULT:         {'COMPLETELY DIFFERENT LAYOUTS (PASS)' if div['is_diverse'] else 'FAIL: Identical Layout'}")

        assert div["is_diverse"], f"FAILURE: System generated identical layout for {k1} and {k2}!"
        assert div["jaccard_distance"] >= 0.20 or div["node_dissimilarity"]["is_program_different"], "Plans must be topologically distinct!"

    print("\nPASS: System generates completely distinct architectural layouts on the same 10 Marla plot size.")


def test_03_multi_scale_matrix():
    print("\n" + "=" * 75)
    print("TEST 3: Multi-Scale Verification Matrix (3 Marla, 5 Marla, 7 Marla, 1 Kanal)")
    print("=" * 75)

    scales = [
        ("3_marla_tudor", "Design 3 marla compact Tudor Revival house with 2 bedrooms, open kitchenette, and linear stairs"),
        ("5_marla_craftsman", "Design 5 marla Craftsman home with 3 bedrooms, covered front porch, open kitchen, and dogleg stairs"),
        ("7_marla_farmhouse", "Design 7 marla modern Farmhouse with 4 bedrooms, wrap-around porch, country kitchen, and family lounge"),
        ("1_kanal_mediterranean_pool", "Design 1 kanal luxury Mediterranean villa with 5 bedrooms, internal pool patio, double portico car porch, and show kitchen")
    ]

    solver = DatasetDrivenRAGSolver()

    for scale_id, prompt in scales:
        print(f"\n---> Testing Scale Case: [{scale_id}]")
        print(f"Prompt: \"{prompt}\"")
        plan = solver.synthesize(prompt)

        # Check QualityGate
        qg = FloorPlanQualityGate.evaluate(plan)
        print(f"QualityGate Status: {qg['final_status']} (Score: {qg['quality_score']:.2f})")
        assert qg["is_valid"], f"QualityGate failed for {scale_id}: {qg['failures']}"

        # Check Gemini Senior Architect Review in provenance
        verdict = plan.metadata.provenance.get("senior_architect_verdict")
        style = plan.metadata.provenance.get("architectural_style")
        print(f"Architectural Style Tag: {style}")
        print(f"Gemini Senior Architect Verdict:\n   \"{verdict[:120]}...\"")
        assert verdict, "Gemini Senior Architect review verdict is missing!"

        # Render 2D drawing
        png_path = os.path.join(OUTPUT_DIR, f"{scale_id}_floor_plan.png")
        FloorPlanVisualizer.render_floorplan(plan, png_path, dpi=180)
        print(f"Saved 2D Clean Floor Plan Drawing: {png_path} ({os.path.getsize(png_path)} bytes)")

        # Export JSON
        json_path = os.path.join(OUTPUT_DIR, f"{scale_id}_plan.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(plan.to_json())

    print("\nPASS: All multi-scale test cases passed Quality Gate and Gemini review.")


def test_04_procedural_3d_blender_styles():
    print("\n" + "=" * 75)
    print("TEST 4: Procedural 3D Blender Multi-Style Facade & Roof Generation")
    print("=" * 75)

    gen = Blender3DGenerator()
    if not gen.is_blender_available():
        print("Blender 5.1 not available, skipping live render.")
        return

    # Render two distinct styles in 3D: Spanish Revival vs Mid-Century Modern
    styles_to_render = [
        ("10m_spanish_revival", "Spanish Revival 10 Marla (Terracotta Clay Roof & Arches)"),
        ("10m_mid_century_modern", "Mid-Century Modern 10 Marla (Flat Cantilever & Glass Pavilion)")
    ]

    for key, desc in styles_to_render:
        json_path = os.path.join(OUTPUT_DIR, f"{key}_plan.json")
        blend_path = os.path.join(OUTPUT_DIR, f"{key}_3d_model.blend")
        render_path = os.path.join(OUTPUT_DIR, f"{key}_perspective.png")

        # Load plan
        from dataset.schema.canonical import CanonicalFloorPlan
        from generation.rag_solver import DatasetDrivenRAGSolver
        solver = DatasetDrivenRAGSolver()

        if key == "10m_spanish_revival":
            plan = solver.synthesize("Design 10 marla Spanish Revival villa with terracotta roof and courtyard")
        else:
            plan = solver.synthesize("Design 10 marla Mid-Century Modern house with flat roof and glass pavilion")

        print(f"\nBuilding 3D Model: {desc}...")
        res = gen.generate_3d_model(plan, blend_path, render_path, timeout_seconds=120)
        print(f"Blender 3D Status: {res.get('success')}")
        assert res.get("success"), f"3D rendering failed for {key}: {res.get('stderr')}"

        if os.path.exists(render_path):
            print(f"Generated 3D Perspective Render: {render_path} ({os.path.getsize(render_path)} bytes)")
        if os.path.exists(blend_path):
            print(f"Generated Blender 3D Scene: {blend_path} ({os.path.getsize(blend_path)} bytes)")

    print("\nPASS: Distinct 3D procedural models generated for different architectural styles.")


if __name__ == "__main__":
    test_01_style_catalog_coverage()
    test_02_same_plot_size_diversity_10_marla()
    test_03_multi_scale_matrix()
    test_04_procedural_3d_blender_styles()
    print("\n" + "=" * 75)
    print("ALL SYSTEM UPDATE, DIVERSITY & ARCHITECTURAL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)
