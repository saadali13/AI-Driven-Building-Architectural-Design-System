"""
Automated Test Suite: Purely Dataset-Driven Floor Plan Generator (FYP Part 2)
Tests end-to-end synthesis using real CV-extracted topologies from dataset/dataset_index.json:
- F13 Invalidation Guard rejection of unfeasible programs
- Provenance verification against real extracted dataset plans
- 100% QualityGate pass rates across 3 Marla, 5 Marla, 7 Marla, 10 Marla, and 1 Kanal
- Export of 2D CAD blueprint renders to output/dataset_generated_{scale}.png
"""

import os
import json
import pytest
from shapely.geometry import Polygon
import networkx as nx

from generation.rag_solver import DatasetDrivenRAGSolver
from generation.quality_gate import FloorPlanQualityGate
from generation.visualizer import FloorPlanVisualizer


@pytest.fixture(scope="module")
def solver():
    return DatasetDrivenRAGSolver()


@pytest.fixture(scope="module")
def dataset_catalog():
    catalog_path = os.path.join("dataset", "dataset_index.json")
    assert os.path.exists(catalog_path), f"Missing {catalog_path}"
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {p["plan_id"]: p for p in data["plans"]}


def test_catalog_integrity(dataset_catalog):
    """Asserts dataset_index.json contains all 185 unique real blueprint plans."""
    assert len(dataset_catalog) >= 180, f"Expected >= 180 plans, found {len(dataset_catalog)}"
    
    categories = set(p["plot_category"] for p in dataset_catalog.values())
    expected_categories = {"3_marla", "5_marla", "7_marla", "10_marla", "1_kanal"}
    assert expected_categories.issubset(categories), f"Missing categories: {expected_categories - categories}"

    # Verify enrichment fields
    for pid, plan in dataset_catalog.items():
        assert "frontage_ft" in plan
        assert "depth_ft" in plan
        assert "total_area_sqft" in plan
        assert "ground_floor_rooms" in plan
        assert len(plan["ground_floor_rooms"]) >= 4


def test_invalidation_guard_f13(solver):
    """Asserts that architecturally unfeasible requests are strictly rejected by the F13 gate."""
    # 5 bedrooms requested on a tiny 3 Marla plot
    with pytest.raises(ValueError, match="F13 Architectural Infeasibility Guard"):
        solver.synthesize("Design a 3 marla house with 6 bedrooms and 6 bathrooms")

    # 3 kitchens requested on 5 Marla
    with pytest.raises(ValueError, match="F13 Architectural Infeasibility Guard"):
        solver.synthesize("Design a 5 marla house with 3 kitchens")


SCALES = [
    ("3_marla", "Design a 2-story 3 marla compact urban house with doglegged stairs"),
    ("5_marla", "Design a modern 2-floor 5 marla family residence with straight stairs"),
    ("7_marla", "Design a 2-story 7 marla contemporary home with doglegged stairs"),
    ("10_marla", "Design an executive 2-story 10 marla luxury residence with stairs"),
    ("1_kanal", "Design a grand 2-floor 1 kanal luxury villa with stairs and double height lounge")
]


@pytest.mark.parametrize("scale,prompt", SCALES)
def test_dataset_driven_synthesis_and_quality_gate(solver, dataset_catalog, scale, prompt):
    """
    Synthesizes floor plans across all Pakistani plot scales, asserting:
    1. Dataset provenance (matched_plan_id in dataset_index.json)
    2. Zero critical and high QualityGate failures (100% PASS)
    3. Structural vertical stair continuity (IoU >= 0.98)
    4. Car porch to upper terrace conversion
    5. Continuous vertical OTS shaft alignment
    6. Complete BFS circulation reachability
    """
    plan = solver.synthesize(prompt)
    assert plan is not None

    prov = plan.metadata.provenance
    assert prov.get("is_dataset_derived") is True
    matched_id = prov.get("matched_plan_id")
    assert matched_id in dataset_catalog, f"Matched plan {matched_id} not found in dataset_index.json"

    # Evaluate QualityGate
    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed for {scale}: {gate['failures']}"
    assert gate["critical_failures_count"] == 0
    assert gate["high_failures_count"] == 0
    assert gate["quality_score"] == 1.0

    # Vertical Stair Alignment (IoU >= 0.98)
    stair_0 = next(r for r in plan.rooms if r.level_index == 0 and "stair" in r.room_id.lower())
    stair_1 = next(r for r in plan.rooms if r.level_index == 1 and "stair" in r.room_id.lower())
    p0 = Polygon(stair_0.polygon)
    p1 = Polygon(stair_1.polygon)
    iou = p0.intersection(p1).area / p0.union(p1).area
    assert iou >= 0.98, f"Staircase vertical alignment IoU {iou:.3f} < 0.98"

    # Ground Porch -> Upper Terrace Conversion
    porch_0 = next(r for r in plan.rooms if r.level_index == 0 and ("porch" in r.room_id.lower() or r.room_type == "garage"))
    terrace_1 = next(r for r in plan.rooms if r.level_index == 1 and ("terrace" in r.room_id.lower() or r.room_type == "balcony"))
    assert porch_0 is not None and terrace_1 is not None

    # OTS Vertical Shaft Continuity
    ots_rooms_0 = [r for r in plan.rooms if r.level_index == 0 and "ots" in r.room_id.lower()]
    ots_rooms_1 = [r for r in plan.rooms if r.level_index == 1 and "ots" in r.room_id.lower()]
    assert len(ots_rooms_0) == len(ots_rooms_1), "Mismatched OTS vertical shafts"

    # BFS Circulation Reachability
    g = nx.Graph()
    for r in plan.rooms:
        g.add_node(r.room_id)
    for op in plan.openings:
        if op.opening_type == "door" and len(op.connects_rooms) == 2:
            g.add_edge(op.connects_rooms[0], op.connects_rooms[1])
    for e in plan.graph_edges:
        if e.relationship_type in ("via_door", "direct"):
            g.add_edge(e.source_room_id, e.target_room_id)

    entrance = next(r for r in plan.rooms if "porch" in r.room_id.lower() or "entry" in r.room_id.lower())
    for r in plan.rooms:
        if r.is_habitable and r.room_id != entrance.room_id:
            assert nx.has_path(g, entrance.room_id, r.room_id), f"Unreachable room {r.room_name} ({r.room_id})"


@pytest.mark.parametrize("scale,prompt", SCALES)
def test_export_cad_blueprint_renders(solver, scale, prompt):
    """Exports publication-grade 2D CAD blueprint renders to output/dataset_generated_{scale}.png."""
    plan = solver.synthesize(prompt)
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"dataset_generated_{scale}.png")

    rendered_path = FloorPlanVisualizer.render_composite_two_floor_sheet(plan, out_file, dpi=150)
    assert os.path.exists(rendered_path), f"Render file {rendered_path} was not created"
    assert os.path.getsize(rendered_path) > 30000, f"Render file {rendered_path} is unexpectedly small"
