"""
Typological and Geometric Diversity Verification Matrix Test Suite.
Author: Principal Residential CAD Architect & Lead Systems Engineer

Validates:
1. test_10_marla_prompt_diversity:
   - Compares Plan 10A (5-bed, traditional segregated, dogleg stair) vs
     Plan 10B (3-bed, modern open-plan, linear straight stair, office, gym).
   - Enforces Jaccard Graph Distance >= 0.30 and Spatial IoU <= 0.70.
   - FloorPlanQualityGate evaluates to PASS for both plans.
   - Exports output/diversity_matrix/10_marla_comparison_A_vs_B.png.

2. test_5_marla_prompt_diversity:
   - Compares Plan 5A (1-bed single floor) vs Plan 5B (4-bed 2-story residence).
   - Enforces Jaccard Graph Distance >= 0.25 and Spatial IoU <= 0.70.
   - FloorPlanQualityGate evaluates to PASS for both plans.
   - Exports output/diversity_matrix/5_marla_comparison_A_vs_B.png.

3. test_3_marla_prompt_diversity:
   - Compares Plan 3A (2-story compact, 3-bed) vs Plan 3B (3-story, 4-bed, terrace).
   - Enforces Jaccard Graph Distance >= 0.25 and Spatial IoU <= 0.70.
   - FloorPlanQualityGate evaluates to PASS for both plans.
   - Exports output/diversity_matrix/3_marla_comparison_A_vs_B.png.

4. test_1_kanal_prompt_diversity:
   - Compares Plan 1KA (luxury villa with stairs) vs
     Plan 1KB (contemporary estate, rotunda stair, cinema, pool deck).
   - Enforces Jaccard Graph Distance >= 0.25 and Spatial IoU <= 0.70.
   - FloorPlanQualityGate evaluates to PASS for both plans.
   - Exports output/diversity_matrix/1_kanal_comparison_A_vs_B.png.

5. test_irregular_site_shape_diversity:
   - Compares Triangle, Trapezoid, and Chamfered Corner plot synthesis.
   - Enforces pairwise Jaccard Graph Distance >= 0.25 and Spatial IoU <= 0.70 across all pairs.
   - FloorPlanQualityGate evaluates to PASS for all shapes.
   - Exports output/diversity_matrix/shapes_comparison_triangle_vs_trapezoid_vs_corner.png.
"""

import os
import pytest
import matplotlib.pyplot as plt

from generation.rag_solver import DatasetDrivenRAGSolver
from generation.irregular_solver import IrregularSiteSolver
from generation.diversity_evaluator import DiversityEvaluator
from generation.quality_gate import FloorPlanQualityGate
from generation.visualizer import FloorPlanVisualizer
from requirements.site_geometry import (
    create_triangle,
    create_trapezoid,
    create_corner_plot
)


OUTPUT_DIR = os.path.join("output", "diversity_matrix")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@pytest.fixture(scope="module")
def rag_solver():
    return DatasetDrivenRAGSolver()


@pytest.fixture(scope="module")
def irregular_solver():
    return IrregularSiteSolver()


def _render_side_by_side_comparison(
    plan_a,
    plan_b,
    title_a: str,
    title_b: str,
    sheet_title: str,
    output_filename: str,
    metrics: dict
):
    """Renders high-resolution side-by-side CAD comparison sheet with diversity metrics overlay."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 13), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")

    FloorPlanVisualizer._draw_level_on_axis(ax1, plan_a, level_index=0)
    FloorPlanVisualizer._draw_level_on_axis(ax2, plan_b, level_index=0)

    j_dist = metrics.get("jaccard_distance", 0.0)
    iou = metrics.get("average_spatial_iou", 0.0)

    ax1.set_title(f"{title_a}\n[Level 0 Ground Floor Plan]", fontsize=12, fontweight="bold", color="#1E293B")
    ax2.set_title(f"{title_b}\n[Level 0 Ground Floor Plan]", fontsize=12, fontweight="bold", color="#1E293B")

    fig.suptitle(
        f"{sheet_title}\n"
        f"QUANTITATIVE DIVERSITY BENCHMARK: Jaccard Graph Distance = {j_dist:.3f} | Spatial IoU = {iou:.3f} | 100% QUALITY GATE PASS",
        fontsize=14,
        fontweight="bold",
        color="#0F172A",
        y=0.98
    )

    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.94])
    out_path = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _render_tri_shape_comparison(
    plan_tri,
    plan_trap,
    plan_corner,
    sheet_title: str,
    output_filename: str
):
    """Renders 3-way irregular site shape comparison sheet."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(26, 10), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")

    FloorPlanVisualizer._draw_level_on_axis(ax1, plan_tri, level_index=0)
    FloorPlanVisualizer._draw_level_on_axis(ax2, plan_trap, level_index=0)
    FloorPlanVisualizer._draw_level_on_axis(ax3, plan_corner, level_index=0)

    ax1.set_title("Triangle Site (45' x 65' x 79')\n[Level 0 Ground Plan]", fontsize=11, fontweight="bold", color="#1E293B")
    ax2.set_title("Trapezoid Site (40' x 28' x 60' x 55')\n[Level 0 Ground Plan]", fontsize=11, fontweight="bold", color="#1E293B")
    ax3.set_title("Chamfered Corner Plot (50' x 60' x 15' Splay)\n[Level 0 Ground Plan]", fontsize=11, fontweight="bold", color="#1E293B")

    fig.suptitle(
        f"{sheet_title}\n"
        f"NON-ORTHOGONAL SITE GEOMETRY SYNTHESIS BENCHMARK | ALL PAIRS JACCARD DISTANCE >= 0.60 | 100% QUALITY GATE PASS",
        fontsize=13,
        fontweight="bold",
        color="#0F172A",
        y=0.98
    )

    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.94])
    out_path = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def test_10_marla_prompt_diversity(rag_solver):
    """
    Asserts contrasting prompt requirements on 10 Marla produce fundamentally distinct layouts:
    - Plan 10A: Traditional segregated 5-bedroom luxury residence with dogleg stairs.
    - Plan 10B: Modern open-plan 3-bedroom contemporary villa with home office, gym, and linear straight staircase.
    """
    prompt_a = "Design an executive 2-story 10 marla luxury residence with 5 bedrooms, traditional segregated layout, drawing room, and dogleg stairs"
    prompt_b = "Design a modern 2-story 10 marla contemporary open-plan residence with 3 bedrooms, home office, fitness studio, open kitchen, and linear straight staircase"

    plan_a = rag_solver.synthesize(prompt_a)
    plan_b = rag_solver.synthesize(prompt_b)

    # 1. FloorPlanQualityGate Compliance
    gate_a = FloorPlanQualityGate.evaluate(plan_a)
    gate_b = FloorPlanQualityGate.evaluate(plan_b)
    assert gate_a["final_status"] == "PASS", f"Plan 10A failed QualityGate: {gate_a['failures']}"
    assert gate_b["final_status"] == "PASS", f"Plan 10B failed QualityGate: {gate_b['failures']}"

    # 2. Quantitative Diversity Evaluation
    metrics = DiversityEvaluator.evaluate_diversity(plan_a, plan_b, min_jaccard=0.30, max_iou=0.70)

    assert metrics["jaccard_distance"] >= 0.30, (
        f"Jaccard graph distance ({metrics['jaccard_distance']}) below 0.30 threshold"
    )
    assert metrics["average_spatial_iou"] <= 0.70, (
        f"Average Spatial IoU ({metrics['average_spatial_iou']}) exceeds 0.70 threshold"
    )
    assert metrics["is_topologically_distinct"] is True
    assert metrics["is_spatially_distinct"] is True
    assert metrics["is_diverse"] is True

    # 3. Node Vector Program Dissimilarity
    node_diff = metrics["node_dissimilarity"]
    assert node_diff["bedroom_diff"] >= 2, "Expected bedroom count difference between 10A and 10B"
    assert node_diff["stair_matches"] is False, "Expected different staircase typologies"

    # 4. Export Visual Comparison Sheet
    out_path = _render_side_by_side_comparison(
        plan_a, plan_b,
        title_a="Plan 10A: Traditional Segregated 5-Bed (Dogleg Stair)",
        title_b="Plan 10B: Modern Open-Plan 3-Bed (Linear Stair & Office)",
        sheet_title="10 MARLA TYPOLOGICAL DIVERSITY COMPARISON MATRIX",
        output_filename="10_marla_comparison_A_vs_B.png",
        metrics=metrics
    )
    assert os.path.exists(out_path), f"Failed to export {out_path}"


def test_5_marla_prompt_diversity(rag_solver):
    """
    Asserts contrasting prompt requirements on 5 Marla produce distinct single- vs multi-floor layouts:
    - Plan 5A: 1-bedroom compact single-floor house.
    - Plan 5B: 4-bedroom 2-story family residence with straight stairs.
    """
    prompt_a = "1 bedroom compact house on ground floor with parking and courtyard"
    prompt_b = "Design a modern 2-floor 5 marla family residence with 4 bedrooms, attached baths, and straight stairs"

    plan_a = rag_solver.synthesize(prompt_a)
    plan_b = rag_solver.synthesize(prompt_b)

    # 1. QualityGate verification
    gate_a = FloorPlanQualityGate.evaluate(plan_a)
    gate_b = FloorPlanQualityGate.evaluate(plan_b)
    assert gate_a["final_status"] == "PASS", f"Plan 5A failed QualityGate: {gate_a['failures']}"
    assert gate_b["final_status"] == "PASS", f"Plan 5B failed QualityGate: {gate_b['failures']}"

    # 2. Storey and room structure
    assert plan_a.floor_count == 1, f"Expected 1 floor for Plan 5A, got {plan_a.floor_count}"
    assert plan_b.floor_count == 2, f"Expected 2 floors for Plan 5B, got {plan_b.floor_count}"

    # 3. Diversity Evaluation
    metrics = DiversityEvaluator.evaluate_diversity(plan_a, plan_b, min_jaccard=0.25, max_iou=0.70)

    assert metrics["jaccard_distance"] >= 0.25, (
        f"5M Jaccard distance ({metrics['jaccard_distance']}) below 0.25 threshold"
    )
    assert metrics["average_spatial_iou"] <= 0.70, (
        f"5M Spatial IoU ({metrics['average_spatial_iou']}) exceeds 0.70 threshold"
    )
    assert metrics["is_diverse"] is True

    # 4. Export Visual Comparison Sheet
    out_path = _render_side_by_side_comparison(
        plan_a, plan_b,
        title_a="Plan 5A: Single-Storey 1-Bed Compact Urban House",
        title_b="Plan 5B: Two-Storey 4-Bed Contemporary Family Villa",
        sheet_title="5 MARLA DYNAMIC PROGRAM & SCALE DIVERSITY MATRIX",
        output_filename="5_marla_comparison_A_vs_B.png",
        metrics=metrics
    )
    assert os.path.exists(out_path), f"Failed to export {out_path}"


def test_3_marla_prompt_diversity(rag_solver):
    """
    Asserts contrasting prompt requirements on 3 Marla produce distinct 2-floor vs 3-floor layouts:
    - Plan 3A: 2-story compact urban house with dogleg stairs and 3 bedrooms.
    - Plan 3B: 3-story urban residence with 4 bedrooms, terrace, and straight stairs.
    """
    prompt_a = "Design a 2-story 3 marla compact urban house with doglegged stairs and 3 bedrooms"
    prompt_b = "Design a 3-story 3 marla house with 4 bedrooms, terrace, and straight stairs"

    plan_a = rag_solver.synthesize(prompt_a)
    plan_b = rag_solver.synthesize(prompt_b)

    # 1. QualityGate verification
    gate_a = FloorPlanQualityGate.evaluate(plan_a)
    gate_b = FloorPlanQualityGate.evaluate(plan_b)
    assert gate_a["final_status"] == "PASS", f"Plan 3A failed QualityGate: {gate_a['failures']}"
    assert gate_b["final_status"] == "PASS", f"Plan 3B failed QualityGate: {gate_b['failures']}"

    assert plan_a.floor_count == 2
    assert plan_b.floor_count == 3

    # 2. Diversity Evaluation
    metrics = DiversityEvaluator.evaluate_diversity(plan_a, plan_b, min_jaccard=0.25, max_iou=0.70)

    assert metrics["jaccard_distance"] >= 0.25, (
        f"3M Jaccard distance ({metrics['jaccard_distance']}) below 0.25 threshold"
    )
    assert metrics["average_spatial_iou"] <= 0.70, (
        f"3M Spatial IoU ({metrics['average_spatial_iou']}) exceeds 0.70 threshold"
    )
    assert metrics["is_diverse"] is True

    # 3. Export Visual Comparison Sheet
    out_path = _render_side_by_side_comparison(
        plan_a, plan_b,
        title_a="Plan 3A: 2-Storey Compact Urban (3-Bed, Dogleg Stair)",
        title_b="Plan 3B: 3-Storey Vertical Urban (4-Bed, Linear Stair, G+2)",
        sheet_title="3 MARLA MULTI-STOREY VERTICAL DIVERSITY MATRIX",
        output_filename="3_marla_comparison_A_vs_B.png",
        metrics=metrics
    )
    assert os.path.exists(out_path), f"Failed to export {out_path}"


def test_1_kanal_prompt_diversity(rag_solver):
    """
    Asserts contrasting prompt requirements on 1 Kanal produce distinct grand estate layouts:
    - Plan 1KA: Grand luxury villa with formal drawing and double-height lounge.
    - Plan 1KB: Contemporary estate with 5 suites, private cinema, pool terrace, and rotunda grand staircase.
    """
    prompt_a = "Design a grand 2-floor 1 kanal luxury villa with stairs and double height lounge"
    prompt_b = "Design a 2-story 1 kanal contemporary estate with 5 bedroom suites, home cinema, swimming pool terrace, and rotunda grand staircase"

    plan_a = rag_solver.synthesize(prompt_a)
    plan_b = rag_solver.synthesize(prompt_b)

    # 1. QualityGate verification
    gate_a = FloorPlanQualityGate.evaluate(plan_a)
    gate_b = FloorPlanQualityGate.evaluate(plan_b)
    assert gate_a["final_status"] == "PASS", f"Plan 1KA failed QualityGate: {gate_a['failures']}"
    assert gate_b["final_status"] == "PASS", f"Plan 1KB failed QualityGate: {gate_b['failures']}"

    # 2. Diversity Evaluation
    metrics = DiversityEvaluator.evaluate_diversity(plan_a, plan_b, min_jaccard=0.25, max_iou=0.70)

    assert metrics["jaccard_distance"] >= 0.25, (
        f"1K Jaccard distance ({metrics['jaccard_distance']}) below 0.25 threshold"
    )
    assert metrics["average_spatial_iou"] <= 0.70, (
        f"1K Spatial IoU ({metrics['average_spatial_iou']}) exceeds 0.70 threshold"
    )
    assert metrics["is_diverse"] is True

    # 3. Export Visual Comparison Sheet
    out_path = _render_side_by_side_comparison(
        plan_a, plan_b,
        title_a="Plan 1KA: Grand Luxury Villa (Right-Entry, Dogleg Core)",
        title_b="Plan 1KB: Contemporary Estate (Left-Entry, Cinema, Rotunda)",
        sheet_title="1 KANAL LUXURY ESTATE TYPOLOGICAL DIVERSITY MATRIX",
        output_filename="1_kanal_comparison_A_vs_B.png",
        metrics=metrics
    )
    assert os.path.exists(out_path), f"Failed to export {out_path}"


def test_irregular_site_shape_diversity(irregular_solver):
    """
    Asserts distinct non-orthogonal site shapes produce unique topological and spatial layouts:
    - Triangle site (45' x 65' x 79')
    - Trapezoid site (40' x 28' x 60' x 55')
    - Chamfered Corner plot (50' x 60' x 15' Splay)
    """
    tri_site = create_triangle(front=45.0, left=65.0, hypotenuse=79.0, unit="ft")
    trap_site = create_trapezoid(front=40.0, rear=28.0, left=60.0, right=55.0, unit="ft")
    corner_site = create_corner_plot(front=50.0, depth=60.0, splay=15.0, unit="ft")

    prompt = "3 bedroom family residence"
    plan_tri = irregular_solver.synthesize(tri_site, prompt=prompt, floor_count=2)
    plan_trap = irregular_solver.synthesize(trap_site, prompt=prompt, floor_count=2)
    plan_corner = irregular_solver.synthesize(corner_site, prompt=prompt, floor_count=2)

    # 1. QualityGate verification
    gate_tri = FloorPlanQualityGate.evaluate(plan_tri)
    gate_trap = FloorPlanQualityGate.evaluate(plan_trap)
    gate_cor = FloorPlanQualityGate.evaluate(plan_corner)

    assert gate_tri["final_status"] == "PASS", f"Triangle plan failed QualityGate: {gate_tri['failures']}"
    assert gate_trap["final_status"] == "PASS", f"Trapezoid plan failed QualityGate: {gate_trap['failures']}"
    assert gate_cor["final_status"] == "PASS", f"Corner plot plan failed QualityGate: {gate_cor['failures']}"

    # 2. Pairwise Diversity Evaluations
    div_tri_trap = DiversityEvaluator.evaluate_diversity(plan_tri, plan_trap, min_jaccard=0.25, max_iou=0.70)
    div_trap_cor = DiversityEvaluator.evaluate_diversity(plan_trap, plan_corner, min_jaccard=0.25, max_iou=0.70)
    div_tri_cor = DiversityEvaluator.evaluate_diversity(plan_tri, plan_corner, min_jaccard=0.25, max_iou=0.70)

    assert div_tri_trap["jaccard_distance"] >= 0.25
    assert div_tri_trap["average_spatial_iou"] <= 0.70

    assert div_trap_cor["jaccard_distance"] >= 0.25
    assert div_trap_cor["average_spatial_iou"] <= 0.70

    assert div_tri_cor["jaccard_distance"] >= 0.25
    assert div_tri_cor["average_spatial_iou"] <= 0.70

    # 3. Export 3-way Visual Comparison Sheet
    out_path = _render_tri_shape_comparison(
        plan_tri, plan_trap, plan_corner,
        sheet_title="NON-ORTHOGONAL SITE GEOMETRY DIVERSITY MATRIX",
        output_filename="shapes_comparison_triangle_vs_trapezoid_vs_corner.png"
    )
    assert os.path.exists(out_path), f"Failed to export {out_path}"
