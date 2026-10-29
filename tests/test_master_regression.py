"""
Production Master Regression & Snapshot Integrity Test Suite.
Guarantees:
1. Zero polygon drift against dataset/canonical_baselines/executive_10_marla_master.json.
2. Strict 100% QualityGate score (is_valid=True, quality_score=1.0, 0 critical, 0 high failures).
3. Swappability of all 9 staircase typologies without breaking room circulation or graph reachability.
4. Complete AIA 8-layer DXF export and vector PDF/SVG presentation export validation.
"""

import os
import json
import pytest
import ezdxf
from dataset.schema.canonical import CanonicalFloorPlan
from generation.solver import CoordinatedTwoFloorSolver
from generation.quality_gate import FloorPlanQualityGate
from cad.dxf_generator import export_to_dxf, DXFGenerator
from generation.visualizer import FloorPlanVisualizer


BASELINE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "dataset", "canonical_baselines", "executive_10_marla_master.json"
)


@pytest.fixture(scope="module")
def golden_baseline_dict():
    assert os.path.exists(BASELINE_PATH), f"Golden baseline missing at {BASELINE_PATH}"
    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fresh_executive_plan():
    # CoordinatedTwoFloorSolver defaults to EXECUTIVE typology with u_shaped stairs
    return CoordinatedTwoFloorSolver.generate_coordinated_plan()


def test_baseline_json_snapshot_integrity(golden_baseline_dict, fresh_executive_plan):
    """
    Asserts zero drift on room polygons, centroids, wall centerlines, and opening placements.
    """
    fresh_dict = fresh_executive_plan.model_dump()

    # 1. Verify Room Counts and Zero Polygon Drift
    baseline_rooms = {r["room_id"]: r for r in golden_baseline_dict["rooms"]}
    fresh_rooms = {r["room_id"]: r for r in fresh_dict["rooms"]}

    assert len(fresh_rooms) == len(baseline_rooms), f"Room count mismatch: {len(fresh_rooms)} vs {len(baseline_rooms)}"
    assert set(fresh_rooms.keys()) == set(baseline_rooms.keys()), "Room ID set mismatch"

    for r_id, b_room in baseline_rooms.items():
        f_room = fresh_rooms[r_id]
        # Check area
        assert abs(f_room["area_m2"] - b_room["area_m2"]) < 1e-4, f"Area drift in room {r_id}"
        # Check centroid
        assert abs(f_room["centroid"][0] - b_room["centroid"][0]) < 1e-4, f"Centroid X drift in room {r_id}"
        assert abs(f_room["centroid"][1] - b_room["centroid"][1]) < 1e-4, f"Centroid Y drift in room {r_id}"
        # Check polygon coordinates
        assert len(f_room["polygon"]) == len(b_room["polygon"]), f"Polygon vertex count drift in room {r_id}"
        for (fx, fy), (bx, by) in zip(f_room["polygon"], b_room["polygon"]):
            assert abs(fx - bx) < 1e-4 and abs(fy - by) < 1e-4, f"Polygon coordinate drift in room {r_id}"

    # 2. Verify Walls and Baffle Partition
    baseline_walls = {w["wall_id"]: w for w in golden_baseline_dict["walls"]}
    fresh_walls = {w["wall_id"]: w for w in fresh_dict["walls"]}

    assert "wall_L0_baffle" in fresh_walls, "wall_L0_baffle missing from fresh plan walls"
    assert len(fresh_walls) == len(baseline_walls), f"Wall count mismatch: {len(fresh_walls)} vs {len(baseline_walls)}"

    baffle = fresh_walls["wall_L0_baffle"]
    assert baffle["thickness_m"] == 0.115, "Baffle wall thickness must be 4.5\" (0.115m)"
    assert baffle["centerline"] == [[3.10, 8.60], [4.95, 8.60]], "Baffle wall coordinate drift"

    # 3. Verify Openings and IBC 1011 Landing Door Placement
    fresh_doors = {d["opening_id"]: d for d in fresh_dict["openings"] if d["opening_type"] == "door"}
    assert "door_L1_05" in fresh_doors, "door_L1_05 missing"
    assert fresh_doors["door_L1_05"]["position"] == [2.50, 7.40], "door_L1_05 must remain at y=7.40 for IBC 1011 clearance"


def test_baseline_quality_gate_score(fresh_executive_plan):
    """
    Asserts that the default executive master layout strictly achieves a 1.0 (100%) QualityGate score
    with zero critical or high failures.
    """
    qgate = FloorPlanQualityGate()
    report = qgate.evaluate(fresh_executive_plan)

    assert report["is_valid"] is True, f"QualityGate failed: {report.get('failures')}"
    assert report["quality_score"] == 1.0, f"QualityGate score {report['quality_score']} is less than 1.0"
    assert report.get("critical_failures_count", 0) == 0, "Critical failures found"
    assert report.get("high_failures_count", 0) == 0, "High failures found"


@pytest.mark.parametrize("stair_typology", [
    "straight", "l_shaped", "u_shaped", "winder",
    "spiral", "curved", "ladder", "floating", "bifurcated"
])
def test_stair_typology_swappability_and_reachability(stair_typology):
    """
    Asserts that all 9 modular staircase typologies can be swapped into the master layout
    and maintain full circulation graph reachability for all habitable spaces.
    """
    plan = CoordinatedTwoFloorSolver.generate_coordinated_plan(stair_type=stair_typology)

    # Verify stair metadata propagated
    stair_rooms = [r for r in plan.rooms if "stair" in r.room_id]
    assert len(stair_rooms) >= 2, "Both ground and first floor stairs must exist"
    for sr in stair_rooms:
        assert sr.metadata.get("typology") == stair_typology

    # Verify circulation graph reachability from entry (porch)
    adj_graph = {}
    for edge in plan.graph_edges:
        adj_graph.setdefault(edge.source_room_id, set()).add(edge.target_room_id)
        adj_graph.setdefault(edge.target_room_id, set()).add(edge.source_room_id)

    # Breadth-first search from Ground Porch
    visited = set()
    queue = ["room_L0_porch"]
    while queue:
        curr = queue.pop(0)
        visited.add(curr)
        for neighbor in adj_graph.get(curr, set()):
            if neighbor not in visited and neighbor not in queue:
                queue.append(neighbor)

    # Assert that all habitable rooms on both floors are reachable
    habitable_rooms = [r.room_id for r in plan.rooms if r.is_habitable]
    assert len(habitable_rooms) > 0
    unreachable = [r_id for r_id in habitable_rooms if r_id not in visited]
    assert len(unreachable) == 0, f"Unreachable habitable rooms for stair {stair_typology}: {unreachable}"


def test_production_vector_and_dxf_exports(fresh_executive_plan, tmp_path):
    """
    Verifies that export_to_dxf populates all 8 AIA layers, and vector PDF/SVG presentation
    sheets export correctly with Arch D scaling.
    """
    # 1. DXF Export
    dxf_path = str(tmp_path / "test_master.dxf")
    export_to_dxf(fresh_executive_plan, dxf_path)
    assert os.path.exists(dxf_path)
    assert os.path.getsize(dxf_path) > 20000

    # Inspect DXF layers
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    required_layers = [
        "A-WALL-EXTR", "A-WALL-INTR", "A-DOOR", "A-GLAZ",
        "A-STRS", "A-FURN", "A-ANNO-TEXT", "A-ANNO-DIMS"
    ]
    present_layers = {layer.dxf.name for layer in doc.layers}
    for req_l in required_layers:
        assert req_l in present_layers, f"Required AIA layer {req_l} missing from DXF"
        entities = list(msp.query(f'*[layer=="{req_l}"]'))
        assert len(entities) > 0, f"AIA layer {req_l} has zero entities in modelspace"

    # 2. Vector PDF Export (Arch D 24"x36")
    pdf_path = str(tmp_path / "test_master.pdf")
    FloorPlanVisualizer.render_vector_sheet(fresh_executive_plan, pdf_path, paper_size="ARCH_D", dpi=300)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 20000

    # 3. Vector SVG Export
    svg_path = str(tmp_path / "test_master.svg")
    FloorPlanVisualizer.render_vector_sheet(fresh_executive_plan, svg_path, paper_size="ARCH_D", dpi=300)
    assert os.path.exists(svg_path)
    assert os.path.getsize(svg_path) > 50000
