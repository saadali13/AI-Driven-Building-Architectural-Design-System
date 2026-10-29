"""
Test Suite for 40 Canonical Master Blueprints Catalog.
Verifies:
1. All 40 master files exist and validate against CanonicalFloorPlan schema.
2. FloorPlanQualityGate evaluates all 40 plans with quality_score == 1.0, 0 critical failures, 0 high failures.
3. Intra-scale pairwise typological diversity: Jaccard Distance >= 0.25 and Anti-Mirroring Spatial IoU <= 0.70.
4. Dataset index registration integrity in dataset/dataset_index.json.
"""

import os
import json
import pytest
from typing import List, Dict, Tuple
from copy import deepcopy
from shapely.geometry import Polygon

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel
from generation.quality_gate import FloorPlanQualityGate
from generation.diversity_evaluator import DiversityEvaluator


SCALES = ["3_marla", "7_marla", "10_marla", "1_kanal"]
ALL_PLAN_IDS = [
    f"master_{scale}_v{idx:02d}"
    for scale in SCALES
    for idx in range(1, 11)
]


def mirror_plan(plan: CanonicalFloorPlan, axis: str = "x") -> CanonicalFloorPlan:
    """Reflects room polygons across the midpoint of the envelope along the chosen axis."""
    min_x = min(pt[0] for pt in plan.boundary)
    max_x = max(pt[0] for pt in plan.boundary)
    min_y = min(pt[1] for pt in plan.boundary)
    max_y = max(pt[1] for pt in plan.boundary)

    mirrored_rooms = []
    for r in plan.rooms:
        if axis == "x":
            new_poly = [[round(min_x + max_x - pt[0], 2), pt[1]] for pt in r.polygon]
        else:
            new_poly = [[pt[0], round(min_y + max_y - pt[1], 2)] for pt in r.polygon]
        p_poly = Polygon(new_poly)
        mirrored_rooms.append(RoomModel(
            room_id=r.room_id,
            room_type=r.room_type,
            room_name=r.room_name,
            polygon=new_poly,
            area_m2=r.area_m2,
            centroid=[round(p_poly.centroid.x, 2), round(p_poly.centroid.y, 2)],
            level_index=r.level_index,
            is_habitable=r.is_habitable,
            metadata=deepcopy(r.metadata)
        ))

    mirrored = plan.model_copy(deep=True)
    mirrored.rooms = mirrored_rooms
    return mirrored


def load_plan(plan_id: str) -> CanonicalFloorPlan:
    path = os.path.join("dataset", "canonical_baselines", f"{plan_id}.json")
    assert os.path.exists(path), f"Master plan file does not exist: {path}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CanonicalFloorPlan.model_validate(data)


# -----------------------------------------------------------------------------
# 1. Existence and Schema Validation
# -----------------------------------------------------------------------------
def test_all_40_master_files_exist_and_validate():
    """Confirms all 40 files exist and validate against the CanonicalFloorPlan Pydantic model."""
    assert len(ALL_PLAN_IDS) == 40
    for plan_id in ALL_PLAN_IDS:
        plan = load_plan(plan_id)
        assert plan.metadata.plan_id == plan_id
        assert len(plan.boundary) >= 4, f"{plan_id} must have a valid boundary"
        assert len(plan.rooms) >= 5, f"{plan_id} must have rooms"
        assert len(plan.walls) > 0, f"{plan_id} must have walls"
        assert len(plan.openings) > 0, f"{plan_id} must have openings"
        assert len(plan.graph_edges) > 0, f"{plan_id} must have graph edges"
        assert plan.total_area_m2 > 0


# -----------------------------------------------------------------------------
# 2. Quality Gate 100% Score
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("plan_id", ALL_PLAN_IDS)
def test_quality_gate_all_40_masters(plan_id: str):
    """Runs FloorPlanQualityGate on every master plan; asserts quality_score == 1.0, 0 critical, 0 high."""
    plan = load_plan(plan_id)
    report = FloorPlanQualityGate.evaluate(plan)

    critical_failures = report.get("critical_failures", [])
    high_failures = report.get("high_failures", [])
    score = report.get("quality_score", 0.0)
    status = report.get("final_status", "FAIL")

    assert status == "PASS", f"{plan_id} status is {status}, failures: {report.get('failures')}"
    assert score == 1.0, f"{plan_id} quality score {score} != 1.0, failures: {report.get('failures')}"
    assert len(critical_failures) == 0, f"{plan_id} has critical failures: {critical_failures}"
    assert len(high_failures) == 0, f"{plan_id} has high failures: {high_failures}"


# -----------------------------------------------------------------------------
# 3. Pairwise Typological Diversity Within Scales
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("scale", SCALES)
def test_pairwise_typological_diversity_within_scales(scale: str):
    """Asserts pairwise Jaccard Distance >= 0.25 and Anti-Mirroring Spatial IoU <= 0.70 across all 45 archetype pairs."""
    scale_plan_ids = [f"master_{scale}_v{idx:02d}" for idx in range(1, 11)]
    plans = [load_plan(pid) for pid in scale_plan_ids]

    violations = []
    pairs_tested = 0

    for i in range(len(plans)):
        for j in range(i + 1, len(plans)):
            pairs_tested += 1
            pa = plans[i]
            pb = plans[j]
            pair_name = f"{scale_plan_ids[i]} vs {scale_plan_ids[j]}"

            # Jaccard Graph Distance
            j_dist = DiversityEvaluator.compute_adjacency_jaccard_distance(pa, pb)
            if j_dist < 0.25:
                violations.append(f"{pair_name}: Jaccard Distance {j_dist:.3f} < 0.25")

            # Direct Spatial IoU
            s_iou = DiversityEvaluator.compute_spatial_layout_iou(pa, pb)
            if s_iou > 0.70:
                violations.append(f"{pair_name}: Direct Spatial IoU {s_iou:.3f} > 0.70")

            # Anti-Mirroring IoU (X and Y reflections)
            mx_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "x"), pb)
            if mx_iou > 0.70:
                violations.append(f"{pair_name}: Mirrored-X Spatial IoU {mx_iou:.3f} > 0.70")

            my_iou = DiversityEvaluator.compute_spatial_layout_iou(mirror_plan(pa, "y"), pb)
            if my_iou > 0.70:
                violations.append(f"{pair_name}: Mirrored-Y Spatial IoU {my_iou:.3f} > 0.70")

    assert pairs_tested == 45, f"Expected 45 pairs for {scale}, tested {pairs_tested}"
    assert len(violations) == 0, f"Diversity violations for {scale} ({len(violations)}): " + "; ".join(violations)


# -----------------------------------------------------------------------------
# 4. Dataset Index Registration Integrity
# -----------------------------------------------------------------------------
def test_dataset_index_registration_all_40_masters():
    """Verifies that all 40 master plans are fully registered with required metadata in dataset/dataset_index.json."""
    index_path = os.path.join("dataset", "dataset_index.json")
    assert os.path.exists(index_path), "dataset/dataset_index.json must exist"

    with open(index_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    indexed_plans = {p["plan_id"]: p for p in catalog.get("plans", [])}

    for plan_id in ALL_PLAN_IDS:
        assert plan_id in indexed_plans, f"Plan {plan_id} missing from dataset_index.json"
        entry = indexed_plans[plan_id]

        assert "plot_category" in entry
        assert "typology_tag" in entry and len(entry["typology_tag"]) > 0
        assert "staircase_type" in entry and entry["staircase_type"] in [
            "straight", "dogleg", "curved", "bifurcated", "external", "l_shaped", "floating", "winder", "none"
        ]
        assert "room_counts" in entry and isinstance(entry["room_counts"], dict)
        assert entry.get("frontage_ft", 0) > 0
        assert entry.get("depth_ft", 0) > 0
        assert entry.get("total_area_sqft", 0) > 0
        assert "canonical_path" in entry
        assert os.path.exists(entry["canonical_path"]), f"File {entry['canonical_path']} does not exist on disk"

        gf_rooms = entry.get("ground_floor_rooms", [])
        assert len(gf_rooms) >= 4, f"{plan_id} must have at least 4 ground floor rooms in index for RAG retrieval"
        for r in gf_rooms:
            assert "room_id" in r
            assert "room_name" in r
            assert "room_type" in r
            assert "area_m2" in r
            assert "centroid" in r
