"""
Multi-Scale RAG Retrieval Audit and Anti-Cloning Verification Test Suite.
Author: Principal Residential CAD Architect & Lead Systems Engineer

Rigorous test suite across all 5 standard architectural scales:
- 3 Marla (Plans A, B, C)
- 5 Marla (Plans A, B, C)
- 7 Marla (Plans A, B, C)
- 10 Marla (Plans A, B, C)
- 1 Kanal (Plans A, B, C)
Total = 15 distinct architectural generation prompt scenarios.

Rigorously Asserts:
1. Retrieval Accuracy: Each prompt cleanly retrieves its distinct authentic blueprint from dataset/dataset_index.json.
2. 100% QualityGate Compliance: Every synthesized design achieves quality_score == 1.0 (Status PASS, 0 Critical, 0 High failures).
3. Topological Dissimilarity: Pairwise Jaccard Graph Distance >= 0.20 within each scale.
4. Geometric Dissimilarity: Pairwise Spatial IoU <= 0.65 within each scale.
5. Anti-Mirroring Verification: Pairwise Mirrored IoU (X and Y reflections) <= 0.65, ensuring no mirrored duplicates.
6. Visual Documentation: Generates high-fidelity 3-panel triptych comparison sheets in output/diversity_matrix_full/.
"""

import os
import pytest
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any
from shapely.geometry import Polygon

from generation.rag_solver import DatasetDrivenRAGSolver
from generation.quality_gate import FloorPlanQualityGate
from generation.diversity_evaluator import DiversityEvaluator
from generation.visualizer import FloorPlanVisualizer
from dataset.schema.canonical import CanonicalFloorPlan, RoomModel


OUTPUT_DIR = os.path.join("output", "diversity_matrix_full")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@pytest.fixture(scope="module")
def rag_solver() -> DatasetDrivenRAGSolver:
    """Fixture providing initialized DatasetDrivenRAGSolver."""
    return DatasetDrivenRAGSolver()


def mirror_plan(plan: CanonicalFloorPlan, axis: str = "x") -> CanonicalFloorPlan:
    """Reflects a canonical floor plan across X or Y axis for anti-mirroring audit."""
    min_x = min(pt[0] for pt in plan.boundary)
    max_x = max(pt[0] for pt in plan.boundary)
    min_y = min(pt[1] for pt in plan.boundary)
    max_y = max(pt[1] for pt in plan.boundary)

    mirrored_rooms = []
    for r in plan.rooms:
        if axis == "x":
            m_poly = [[round(max_x - (pt[0] - min_x), 2), pt[1]] for pt in r.polygon]
        else:
            m_poly = [[pt[0], round(max_y - (pt[1] - min_y), 2)] for pt in r.polygon]
        p_geom = Polygon(m_poly)
        mirrored_rooms.append(RoomModel(
            room_id=r.room_id,
            room_type=r.room_type,
            room_name=r.room_name,
            polygon=m_poly,
            area_m2=r.area_m2,
            centroid=[round(p_geom.centroid.x, 2), round(p_geom.centroid.y, 2)],
            level_index=r.level_index,
            is_habitable=r.is_habitable,
            metadata=dict(r.metadata or {})
        ))

    return CanonicalFloorPlan(
        metadata=plan.metadata,
        boundary=plan.boundary,
        total_area_m2=plan.total_area_m2,
        walls=plan.walls,
        openings=plan.openings,
        rooms=mirrored_rooms,
        graph_edges=plan.graph_edges
    )


def render_triptych_sheet(
    plans: List[CanonicalFloorPlan],
    titles: List[str],
    sheet_title: str,
    output_filename: str,
    metrics_summary: str
) -> str:
    """Renders a 3-panel side-by-side CAD comparison sheet with diversity metrics overlay."""
    fig, axes = plt.subplots(1, 3, figsize=(28, 12), dpi=140)
    fig.patch.set_facecolor("#FFFFFF")

    for idx, (ax, plan, title) in enumerate(zip(axes, plans, titles)):
        FloorPlanVisualizer._draw_level_on_axis(ax, plan, level_index=0)
        ax.set_title(f"{title}\n[Ground Floor Level 0]", fontsize=11, fontweight="bold", color="#1E293B", pad=12)

    fig.suptitle(
        f"{sheet_title}\n{metrics_summary}",
        fontsize=13,
        fontweight="bold",
        color="#0F172A",
        y=0.98
    )

    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.93])
    out_path = os.path.join(OUTPUT_DIR, output_filename)
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visualizer] Exported 3-panel triptych sheet to {out_path}")
    return out_path


def _extract_matched_blueprint_id(plan: CanonicalFloorPlan) -> str:
    """Extracts raw blueprint identifier from plan metadata."""
    if plan.metadata.provenance and "blueprint_id" in plan.metadata.provenance:
        return plan.metadata.provenance["blueprint_id"]
    pid = plan.metadata.plan_id
    for s in ["_1F", "_2F", "_3F", "gen_"]:
        pid = pid.replace(s, "")
    return pid


# ===========================================================================
# 1. 3 MARLA AUDIT (Prompts 1, 2, 3)
# ===========================================================================
def test_3_marla_multi_prompt_retrieval_and_diversity(rag_solver):
    """
    3 Marla Retrieval & Anti-Cloning Audit:
    - P1: Modern urban home, linear spine straight stair, open living (3_marla_plan_A)
    - P2: Compact residence, front L-shaped stairs, rear suite (3_marla_plan_B)
    - P3: Single-storey 1-bed garden suite cottage, front drawing, courtyard (3_marla_plan_C)
    """
    prompts = [
        ("3M-P1", "3 Marla modern urban home with linear spine straight staircase and open living concept, Plan A", "3_marla_plan_A"),
        ("3M-P2", "3 Marla compact residence with front L-shaped stairs, open kitchen, and rear master suite, Plan B", "3_marla_plan_B"),
        ("3M-P3", "3 Marla single-storey 1-bedroom garden suite cottage with front drawing salon and rear courtyard patio, Plan C", "3_marla_plan_C"),
    ]

    plans = []
    matched_ids = []
    for pid, prompt_text, expected_id in prompts:
        plan = rag_solver.synthesize(prompt_text)
        mid = _extract_matched_blueprint_id(plan)
        matched_ids.append(mid)

        # 1. Assert correct blueprint retrieval
        assert mid == expected_id, f"Prompt '{pid}' expected blueprint {expected_id} but matched {mid}"

        # 2. Assert 100% QualityGate Compliance
        gate_rep = FloorPlanQualityGate.evaluate(plan)
        assert gate_rep["final_status"] == "PASS", f"Plan {pid} failed QualityGate: {gate_rep['failures']}"
        assert gate_rep["quality_score"] == 1.0, f"Plan {pid} quality score {gate_rep['quality_score']} < 1.0"
        assert len(gate_rep["failures"]) == 0, f"Plan {pid} has unexpected failures: {gate_rep['failures']}"

        plans.append(plan)

    # 3. Assert all 3 retrieved blueprints are distinct
    assert len(set(matched_ids)) == 3, f"Duplicate blueprint retrieval detected for 3 Marla: {matched_ids}"

    # 4. Pairwise Diversity & Anti-Cloning Verification
    pairs = [(0, 1), (0, 2), (1, 2)]
    metric_logs = []
    for i, j in pairs:
        pa, pb = plans[i], plans[j]
        j_dist = DiversityEvaluator.compute_adjacency_jaccard_distance(pa, pb)
        s_iou = DiversityEvaluator.compute_spatial_layout_iou(pa, pb)
        mx_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "x"), pb)
        my_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "y"), pb)
        max_mirror = max(mx_iou, my_iou)

        pair_name = f"{prompts[i][0]} vs {prompts[j][0]}"
        metric_logs.append(f"{pair_name}: J={j_dist:.2f}, IoU={s_iou:.2f}, Mirr={max_mirror:.2f}")

        assert j_dist >= 0.20, f"Jaccard Graph Distance {j_dist:.3f} < 0.20 for {pair_name}"
        assert s_iou <= 0.65, f"Spatial IoU {s_iou:.3f} > 0.65 for {pair_name}"
        assert mx_iou <= 0.65, f"Horizontal Mirror IoU {mx_iou:.3f} > 0.65 for {pair_name}"
        assert my_iou <= 0.65, f"Vertical Mirror IoU {my_iou:.3f} > 0.65 for {pair_name}"

    # 5. Export 3-Panel Triptych Comparison Sheet
    render_triptych_sheet(
        plans=plans,
        titles=[
            f"3M Plan A (Linear Spine)\nRetrieved: {matched_ids[0]}",
            f"3M Plan B (L-Stair Suite)\nRetrieved: {matched_ids[1]}",
            f"3M Plan C (Garden Cottage)\nRetrieved: {matched_ids[2]}"
        ],
        sheet_title="3 MARLA MULTI-SCALE RAG RETRIEVAL & ANTI-CLONING AUDIT",
        output_filename="3_marla_triptych_A_B_C.png",
        metrics_summary=" | ".join(metric_logs) + " | 100% QUALITY GATE PASS"
    )


# ===========================================================================
# 2. 5 MARLA AUDIT (Prompts 4, 5, 6)
# ===========================================================================
def test_5_marla_multi_prompt_retrieval_and_diversity(rag_solver):
    """
    5 Marla Retrieval & Anti-Cloning Audit:
    - P1: Single storey 1-bed suite with spacious lawn (5_marla_plan_A)
    - P2: 4-bedroom double storey residence with linear straight stair (5_marla_plan_B)
    - P3: Traditional segregated family villa with dogleg stairs (5_marla_plan_C)
    """
    prompts = [
        ("5M-P1", "5 Marla single storey 1-bedroom suite with spacious front lawn, Plan A", "5_marla_plan_A"),
        ("5M-P2", "5 Marla 4-bedroom double storey residence with linear straight staircase, Plan B", "5_marla_plan_B"),
        ("5M-P3", "5 Marla traditional segregated family villa with dogleg stairs and dual rear suites, Plan C", "5_marla_plan_C"),
    ]

    plans = []
    matched_ids = []
    for pid, prompt_text, expected_id in prompts:
        plan = rag_solver.synthesize(prompt_text)
        mid = _extract_matched_blueprint_id(plan)
        matched_ids.append(mid)

        assert mid == expected_id, f"Prompt '{pid}' expected blueprint {expected_id} but matched {mid}"

        gate_rep = FloorPlanQualityGate.evaluate(plan)
        assert gate_rep["final_status"] == "PASS", f"Plan {pid} failed QualityGate: {gate_rep['failures']}"
        assert gate_rep["quality_score"] == 1.0, f"Plan {pid} quality score {gate_rep['quality_score']} < 1.0"
        assert len(gate_rep["failures"]) == 0, f"Plan {pid} has unexpected failures: {gate_rep['failures']}"

        plans.append(plan)

    assert len(set(matched_ids)) == 3, f"Duplicate blueprint retrieval detected for 5 Marla: {matched_ids}"

    pairs = [(0, 1), (0, 2), (1, 2)]
    metric_logs = []
    for i, j in pairs:
        pa, pb = plans[i], plans[j]
        j_dist = DiversityEvaluator.compute_adjacency_jaccard_distance(pa, pb)
        s_iou = DiversityEvaluator.compute_spatial_layout_iou(pa, pb)
        mx_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "x"), pb)
        my_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "y"), pb)
        max_mirror = max(mx_iou, my_iou)

        pair_name = f"{prompts[i][0]} vs {prompts[j][0]}"
        metric_logs.append(f"{pair_name}: J={j_dist:.2f}, IoU={s_iou:.2f}, Mirr={max_mirror:.2f}")

        assert j_dist >= 0.20, f"Jaccard Graph Distance {j_dist:.3f} < 0.20 for {pair_name}"
        assert s_iou <= 0.65, f"Spatial IoU {s_iou:.3f} > 0.65 for {pair_name}"
        assert mx_iou <= 0.65, f"Horizontal Mirror IoU {mx_iou:.3f} > 0.65 for {pair_name}"
        assert my_iou <= 0.65, f"Vertical Mirror IoU {my_iou:.3f} > 0.65 for {pair_name}"

    render_triptych_sheet(
        plans=plans,
        titles=[
            f"5M Plan A (Single Floor 1-Bed)\nRetrieved: {matched_ids[0]}",
            f"5M Plan B (Linear 4-Bed 2-Storey)\nRetrieved: {matched_ids[1]}",
            f"5M Plan C (Traditional Segregated)\nRetrieved: {matched_ids[2]}"
        ],
        sheet_title="5 MARLA MULTI-SCALE RAG RETRIEVAL & ANTI-CLONING AUDIT",
        output_filename="5_marla_triptych_A_B_C.png",
        metrics_summary=" | ".join(metric_logs) + " | 100% QUALITY GATE PASS"
    )


# ===========================================================================
# 3. 7 MARLA AUDIT (Prompts 7, 8, 9)
# ===========================================================================
def test_7_marla_multi_prompt_retrieval_and_diversity(rag_solver):
    """
    7 Marla Retrieval & Anti-Cloning Audit:
    - P1: Classic residence with dual rear suites and side show kitchen (7_marla_plan_A)
    - P2: Courtyard-centric villa with central glass patio and straight stair (7_marla_plan_B)
    - P3: Executive home with mid-ground suite, open lounge, and rear master suite (7_marla_plan_C)
    """
    prompts = [
        ("7M-P1", "7 Marla classic residence with dual rear suites and side show kitchen, Plan A", "7_marla_plan_A"),
        ("7M-P2", "7 Marla courtyard-centric villa with central glass patio and linear staircase, Plan B", "7_marla_plan_B"),
        ("7M-P3", "7 Marla executive home with ground floor office suite and separate entrance, Plan C", "7_marla_plan_C"),
    ]

    plans = []
    matched_ids = []
    for pid, prompt_text, expected_id in prompts:
        plan = rag_solver.synthesize(prompt_text)
        mid = _extract_matched_blueprint_id(plan)
        matched_ids.append(mid)

        assert mid == expected_id, f"Prompt '{pid}' expected blueprint {expected_id} but matched {mid}"

        gate_rep = FloorPlanQualityGate.evaluate(plan)
        assert gate_rep["final_status"] == "PASS", f"Plan {pid} failed QualityGate: {gate_rep['failures']}"
        assert gate_rep["quality_score"] == 1.0, f"Plan {pid} quality score {gate_rep['quality_score']} < 1.0"
        assert len(gate_rep["failures"]) == 0, f"Plan {pid} has unexpected failures: {gate_rep['failures']}"

        plans.append(plan)

    assert len(set(matched_ids)) == 3, f"Duplicate blueprint retrieval detected for 7 Marla: {matched_ids}"

    pairs = [(0, 1), (0, 2), (1, 2)]
    metric_logs = []
    for i, j in pairs:
        pa, pb = plans[i], plans[j]
        j_dist = DiversityEvaluator.compute_adjacency_jaccard_distance(pa, pb)
        s_iou = DiversityEvaluator.compute_spatial_layout_iou(pa, pb)
        mx_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "x"), pb)
        my_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "y"), pb)
        max_mirror = max(mx_iou, my_iou)

        pair_name = f"{prompts[i][0]} vs {prompts[j][0]}"
        metric_logs.append(f"{pair_name}: J={j_dist:.2f}, IoU={s_iou:.2f}, Mirr={max_mirror:.2f}")

        assert j_dist >= 0.20, f"Jaccard Graph Distance {j_dist:.3f} < 0.20 for {pair_name}"
        assert s_iou <= 0.65, f"Spatial IoU {s_iou:.3f} > 0.65 for {pair_name}"
        assert mx_iou <= 0.65, f"Horizontal Mirror IoU {mx_iou:.3f} > 0.65 for {pair_name}"
        assert my_iou <= 0.65, f"Vertical Mirror IoU {my_iou:.3f} > 0.65 for {pair_name}"

    render_triptych_sheet(
        plans=plans,
        titles=[
            f"7M Plan A (Dual Rear Suites)\nRetrieved: {matched_ids[0]}",
            f"7M Plan B (Glass Courtyard Patio)\nRetrieved: {matched_ids[1]}",
            f"7M Plan C (Executive Office Suite)\nRetrieved: {matched_ids[2]}"
        ],
        sheet_title="7 MARLA MULTI-SCALE RAG RETRIEVAL & ANTI-CLONING AUDIT",
        output_filename="7_marla_triptych_A_B_C.png",
        metrics_summary=" | ".join(metric_logs) + " | 100% QUALITY GATE PASS"
    )


# ===========================================================================
# 4. 10 MARLA AUDIT (Prompts 10, 11, 12)
# ===========================================================================
def test_10_marla_multi_prompt_retrieval_and_diversity(rag_solver):
    """
    10 Marla Retrieval & Anti-Cloning Audit:
    - P1: 5-bedroom traditional segregated family villa with dogleg stair (10_marla_plan_A)
    - P2: 3-bedroom modern open-concept residence with linear straight stair, gym, office (10_marla_plan_B)
    - P3: Executive villa with central courtyard patio, show kitchen, open lounge (10_marla_plan_C)
    """
    prompts = [
        ("10M-P1", "10 Marla 5-bedroom traditional segregated family villa with dogleg stair, Plan A", "10_marla_plan_A"),
        ("10M-P2", "10 Marla 3-bedroom modern open-concept residence with linear straight staircase, gym, and office, Plan B", "10_marla_plan_B"),
        ("10M-P3", "10 Marla executive villa with central courtyard patio, show kitchen, and open lounge, Plan C", "10_marla_plan_C"),
    ]

    plans = []
    matched_ids = []
    for pid, prompt_text, expected_id in prompts:
        plan = rag_solver.synthesize(prompt_text)
        mid = _extract_matched_blueprint_id(plan)
        matched_ids.append(mid)

        assert mid == expected_id, f"Prompt '{pid}' expected blueprint {expected_id} but matched {mid}"

        gate_rep = FloorPlanQualityGate.evaluate(plan)
        assert gate_rep["final_status"] == "PASS", f"Plan {pid} failed QualityGate: {gate_rep['failures']}"
        assert gate_rep["quality_score"] == 1.0, f"Plan {pid} quality score {gate_rep['quality_score']} < 1.0"
        assert len(gate_rep["failures"]) == 0, f"Plan {pid} has unexpected failures: {gate_rep['failures']}"

        plans.append(plan)

    assert len(set(matched_ids)) == 3, f"Duplicate blueprint retrieval detected for 10 Marla: {matched_ids}"

    pairs = [(0, 1), (0, 2), (1, 2)]
    metric_logs = []
    for i, j in pairs:
        pa, pb = plans[i], plans[j]
        j_dist = DiversityEvaluator.compute_adjacency_jaccard_distance(pa, pb)
        s_iou = DiversityEvaluator.compute_spatial_layout_iou(pa, pb)
        mx_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "x"), pb)
        my_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "y"), pb)
        max_mirror = max(mx_iou, my_iou)

        pair_name = f"{prompts[i][0]} vs {prompts[j][0]}"
        metric_logs.append(f"{pair_name}: J={j_dist:.2f}, IoU={s_iou:.2f}, Mirr={max_mirror:.2f}")

        assert j_dist >= 0.20, f"Jaccard Graph Distance {j_dist:.3f} < 0.20 for {pair_name}"
        assert s_iou <= 0.65, f"Spatial IoU {s_iou:.3f} > 0.65 for {pair_name}"
        assert mx_iou <= 0.65, f"Horizontal Mirror IoU {mx_iou:.3f} > 0.65 for {pair_name}"
        assert my_iou <= 0.65, f"Vertical Mirror IoU {my_iou:.3f} > 0.65 for {pair_name}"

    render_triptych_sheet(
        plans=plans,
        titles=[
            f"10M Plan A (Traditional 5-Bed)\nRetrieved: {matched_ids[0]}",
            f"10M Plan B (Modern Linear Gym/Office)\nRetrieved: {matched_ids[1]}",
            f"10M Plan C (Courtyard Villa)\nRetrieved: {matched_ids[2]}"
        ],
        sheet_title="10 MARLA MULTI-SCALE RAG RETRIEVAL & ANTI-CLONING AUDIT",
        output_filename="10_marla_triptych_A_B_C.png",
        metrics_summary=" | ".join(metric_logs) + " | 100% QUALITY GATE PASS"
    )


# ===========================================================================
# 5. 1 KANAL AUDIT (Prompts 13, 14, 15)
# ===========================================================================
def test_1_kanal_multi_prompt_retrieval_and_diversity(rag_solver):
    """
    1 Kanal Retrieval & Anti-Cloning Audit:
    - P1: Palatial classic mansion, 15ft lawn, bifurcated stair, triple SUV portico (1_kanal_plan_A)
    - P2: C-shaped courtyard estate, internal patio pool, chef kitchen, master wing (1_kanal_plan_B)
    - P3: Contemporary villa, curved rotunda staircase, double-height ceiling, law office (1_kanal_plan_C)
    """
    prompts = [
        ("1K-P1", "1 Kanal palatial classic mansion with 15ft lawn, bifurcated stair, and triple car porch, Plan A", "1_kanal_plan_A"),
        ("1K-P2", "1 Kanal C-shaped courtyard estate with internal patio pool, chef kitchen, and master wing, Plan B", "1_kanal_plan_B"),
        ("1K-P3", "1 Kanal contemporary villa with curved rotunda staircase, double-height ceiling, and home office, Plan C", "1_kanal_plan_C"),
    ]

    plans = []
    matched_ids = []
    for pid, prompt_text, expected_id in prompts:
        plan = rag_solver.synthesize(prompt_text)
        mid = _extract_matched_blueprint_id(plan)
        matched_ids.append(mid)

        assert mid == expected_id, f"Prompt '{pid}' expected blueprint {expected_id} but matched {mid}"

        gate_rep = FloorPlanQualityGate.evaluate(plan)
        assert gate_rep["final_status"] == "PASS", f"Plan {pid} failed QualityGate: {gate_rep['failures']}"
        assert gate_rep["quality_score"] == 1.0, f"Plan {pid} quality score {gate_rep['quality_score']} < 1.0"
        assert len(gate_rep["failures"]) == 0, f"Plan {pid} has unexpected failures: {gate_rep['failures']}"

        plans.append(plan)

    assert len(set(matched_ids)) == 3, f"Duplicate blueprint retrieval detected for 1 Kanal: {matched_ids}"

    pairs = [(0, 1), (0, 2), (1, 2)]
    metric_logs = []
    for i, j in pairs:
        pa, pb = plans[i], plans[j]
        j_dist = DiversityEvaluator.compute_adjacency_jaccard_distance(pa, pb)
        s_iou = DiversityEvaluator.compute_spatial_layout_iou(pa, pb)
        mx_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "x"), pb)
        my_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "y"), pb)
        max_mirror = max(mx_iou, my_iou)

        pair_name = f"{prompts[i][0]} vs {prompts[j][0]}"
        metric_logs.append(f"{pair_name}: J={j_dist:.2f}, IoU={s_iou:.2f}, Mirr={max_mirror:.2f}")

        assert j_dist >= 0.20, f"Jaccard Graph Distance {j_dist:.3f} < 0.20 for {pair_name}"
        assert s_iou <= 0.65, f"Spatial IoU {s_iou:.3f} > 0.65 for {pair_name}"
        assert mx_iou <= 0.65, f"Horizontal Mirror IoU {mx_iou:.3f} > 0.65 for {pair_name}"
        assert my_iou <= 0.65, f"Vertical Mirror IoU {my_iou:.3f} > 0.65 for {pair_name}"

    render_triptych_sheet(
        plans=plans,
        titles=[
            f"1K Plan A (Palatial Bifurcated)\nRetrieved: {matched_ids[0]}",
            f"1K Plan B (C-Shape Courtyard Pool)\nRetrieved: {matched_ids[1]}",
            f"1K Plan C (Rotunda Curved Stair)\nRetrieved: {matched_ids[2]}"
        ],
        sheet_title="1 KANAL MULTI-SCALE RAG RETRIEVAL & ANTI-CLONING AUDIT",
        output_filename="1_kanal_triptych_A_B_C.png",
        metrics_summary=" | ".join(metric_logs) + " | 100% QUALITY GATE PASS"
    )
