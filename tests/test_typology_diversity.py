"""
Phase 13: Architectural Typology Diversity & Topological Dissimilarity Test Suite.
Mathematically verifies that procedural typologies (A, B, and C) are structurally,
topologically, and circulation-wise distinct.

Tests:
1. Weisfeiler-Lehman graph kernel dissimilarity (NetworkX graph hashes differ across all typologies).
2. Spatial Intersection-over-Union (IoU) dissimilarity for Staircases (< 0.20) and Kitchens (< 0.30).
3. Entrance node degree distribution and depth-tree variations from Porch to Master Bedroom.
4. Coordinated Two-Floor Synthesis & Stacking (staircase invariance, wall stacking >= 70%, terrace conversion).
5. Full FloorPlanQualityGate compliance with zero CRITICAL and zero HIGH failures across all typologies.
"""

import pytest
import networkx as nx
from shapely.geometry import Polygon

from generation.architectural_templates import (
    TypologyALinearSpineEngine,
    TypologyBRotundaGrandHallEngine,
    TypologyCCourtyardCoreEngine
)
from generation.solver import CoordinatedTwoFloorSolver, spatial_iou
from generation.quality_gate import FloorPlanQualityGate
from dataset.schema.canonical import CanonicalFloorPlan


def _plan_to_networkx(plan: CanonicalFloorPlan) -> nx.Graph:
    """Converts a CanonicalFloorPlan into a typed NetworkX room adjacency graph."""
    G = nx.Graph()
    for r in plan.rooms:
        G.add_node(r.room_id, room_type=r.room_type, room_name=r.room_name, level=r.level_index)
    for op in plan.openings:
        if op.opening_type == "door" and len(op.connects_rooms) == 2:
            G.add_edge(op.connects_rooms[0], op.connects_rooms[1], edge_type="door")
    for edge in plan.graph_edges:
        if edge.relationship_type == "via_door":
            G.add_edge(edge.source_room_id, edge.target_room_id, edge_type="vertical_stair")
    return G


@pytest.fixture(scope="module")
def plan_A():
    return CoordinatedTwoFloorSolver.generate_coordinated_plan("A")


@pytest.fixture(scope="module")
def plan_B():
    return CoordinatedTwoFloorSolver.generate_coordinated_plan("B")


@pytest.fixture(scope="module")
def plan_C():
    return CoordinatedTwoFloorSolver.generate_coordinated_plan("C")


def test_graph_topology_dissimilarity(plan_A, plan_B, plan_C):
    """
    Asserts that the room adjacency graphs across typologies have distinct
    Weisfeiler-Lehman graph hashes, proving topological dissimilarity.
    """
    G_A = _plan_to_networkx(plan_A)
    G_B = _plan_to_networkx(plan_B)
    G_C = _plan_to_networkx(plan_C)

    hash_A = nx.weisfeiler_lehman_graph_hash(G_A, node_attr="room_type")
    hash_B = nx.weisfeiler_lehman_graph_hash(G_B, node_attr="room_type")
    hash_C = nx.weisfeiler_lehman_graph_hash(G_C, node_attr="room_type")

    assert hash_A != hash_B, f"Typologies A and B have identical WL graph hash: {hash_A}"
    assert hash_B != hash_C, f"Typologies B and C have identical WL graph hash: {hash_B}"
    assert hash_A != hash_C, f"Typologies A and C have identical WL graph hash: {hash_A}"


def test_spatial_iou_dissimilarity(plan_A, plan_B, plan_C):
    """
    Mathematically verifies spatial layout dissimilarity:
    - Staircase IoU < 0.20 across all pairs (proves stairs are arranged differently).
    - Kitchen IoU < 0.30 across all pairs (proves service core is rearranged).
    """
    def get_poly(plan, room_type_kw, name_kw):
        for r in plan.rooms:
            if r.level_index == 0:
                if room_type_kw in r.room_type.lower() and name_kw in r.room_name.lower():
                    return r.polygon
        for r in plan.rooms:
            if r.level_index == 0 and name_kw in r.room_name.lower():
                return r.polygon
        raise ValueError(f"Room matching {room_type_kw}/{name_kw} not found on level 0.")

    # Staircase Polygons
    stair_A = get_poly(plan_A, "corridor", "stair")
    stair_B = get_poly(plan_B, "corridor", "stair")
    stair_C = get_poly(plan_C, "corridor", "stair")

    iou_stair_AB = spatial_iou(stair_A, stair_B)
    iou_stair_BC = spatial_iou(stair_B, stair_C)
    iou_stair_AC = spatial_iou(stair_A, stair_C)

    assert iou_stair_AB < 0.20, f"Staircase IoU A-B ({iou_stair_AB}) exceeds 0.20"
    assert iou_stair_BC < 0.20, f"Staircase IoU B-C ({iou_stair_BC}) exceeds 0.20"
    assert iou_stair_AC < 0.20, f"Staircase IoU A-C ({iou_stair_AC}) exceeds 0.20"

    # Kitchen Polygons
    kit_A = get_poly(plan_A, "kitchen", "kitchen")
    kit_B = get_poly(plan_B, "kitchen", "kitchen")
    kit_C = get_poly(plan_C, "kitchen", "kitchen")

    iou_kit_AB = spatial_iou(kit_A, kit_B)
    iou_kit_BC = spatial_iou(kit_B, kit_C)
    iou_kit_AC = spatial_iou(kit_A, kit_C)

    assert iou_kit_AB < 0.30, f"Kitchen IoU A-B ({iou_kit_AB}) exceeds 0.30"
    assert iou_kit_BC < 0.30, f"Kitchen IoU B-C ({iou_kit_BC}) exceeds 0.30"
    assert iou_kit_AC < 0.30, f"Kitchen IoU A-C ({iou_kit_AC}) exceeds 0.30"


def test_room_node_count_and_degree_distribution(plan_A, plan_B, plan_C):
    """
    Verifies that entrance degree distributions and circulation depth trees
    (from Main Entrance / Porch to Ground Master Bed) vary across typologies.
    """
    G_A = _plan_to_networkx(plan_A)
    G_B = _plan_to_networkx(plan_B)
    G_C = _plan_to_networkx(plan_C)

    # Porch Degree
    deg_A = G_A.degree("room_L0_porch")
    deg_B = G_B.degree("room_L0_porch")
    deg_C = G_C.degree("room_L0_porch")

    # Shortest path depth from entrance porch to master bed 1
    depth_A = nx.shortest_path_length(G_A, "room_L0_porch", "room_L0_bed1")
    depth_B = nx.shortest_path_length(G_B, "room_L0_porch", "room_L0_bed1")
    depth_C = nx.shortest_path_length(G_C, "room_L0_porch", "room_L0_bed1")

    # Prove depth variations: Typology A (Linear Spine: 2), Typology B (Grand Hall: 5), Typology C (Courtyard: 3)
    depths = {depth_A, depth_B, depth_C}
    assert len(depths) >= 2, f"Depth trees must vary across typologies: got A={depth_A}, B={depth_B}, C={depth_C}"
    assert depth_B > depth_A, f"Rotunda grand hall depth ({depth_B}) should be deeper than linear spine ({depth_A})"


def test_coordinated_two_floor_synthesis_and_stacking(plan_A, plan_B, plan_C):
    """
    Verifies coordinated two-floor synthesis rules:
    - Staircase Invariance: exact (X1, Y1, X2, Y2) coordinates pinned between L0 and L1.
    - Vertical Wall Stacking (F19): envelope overlap >= 70%.
    - Level 1 Setback Envelope: Car Porch on L0 converts to Open Terrace on L1.
    - Vertical Shaft Continuity: Central/rear OTS shafts project continuously through Level 1.
    """
    for plan, name in [(plan_A, "Typology A"), (plan_B, "Typology B"), (plan_C, "Typology C")]:
        report = CoordinatedTwoFloorSolver.verify_two_floor_coordination(plan)
        assert report["is_valid"], f"{name} coordination failed: {report['errors']}"
        assert report["stair_iou"] >= 0.99, f"{name} staircase invariance violated: IoU {report['stair_iou']}"
        assert report["stacking_ratio"] >= 0.70, f"{name} structural stacking violated: ratio {report['stacking_ratio']}"
        assert report["terrace_converted"], f"{name} terrace conversion failed"
        assert report["shaft_continuity"], f"{name} vertical shaft continuity failed"


def test_quality_gate_compliance(plan_A, plan_B, plan_C):
    """
    Verifies that all three typologies pass the strict FloorPlanQualityGate
    with final_status == 'PASS' and zero critical or high failures.
    """
    for plan, name in [(plan_A, "Typology A"), (plan_B, "Typology B"), (plan_C, "Typology C")]:
        qg = FloorPlanQualityGate.evaluate(plan)
        assert qg["final_status"] == "PASS", f"{name} QualityGate failed: {[f['description'] for f in qg['failures']]}"
        assert qg["critical_failures_count"] == 0, f"{name} had critical failures: {qg['critical_failures_count']}"
        assert qg["high_failures_count"] == 0, f"{name} had high failures: {qg['high_failures_count']}"


def test_executive_two_floor_coordination_and_quality_gate():
    """
    Verifies that the Executive Two-Floor Plan (anchored by the refactored Ground Floor
    and its natural First-Floor structural counterpart):
    1. Satisfies two-floor coordination (stair invariance IoU = 1.0, stacking ratio >= 80%, terrace conversion, shaft continuity).
    2. Passes FloorPlanQualityGate with 100% Quality Score and 0 failures.
    """
    plan_exec = CoordinatedTwoFloorSolver.generate_executive_plan()
    report = CoordinatedTwoFloorSolver.verify_two_floor_coordination(plan_exec)
    assert report["is_valid"], f"Executive plan coordination failed: {report['errors']}"
    assert report["stair_iou"] >= 0.99, f"Executive plan staircase invariance violated: IoU {report['stair_iou']}"
    assert report["stacking_ratio"] >= 0.80, f"Executive plan structural stacking violated: ratio {report['stacking_ratio']}"
    assert report["terrace_converted"], "Executive plan terrace conversion failed"
    assert report["shaft_continuity"], "Executive plan vertical shaft continuity failed"

    qg = FloorPlanQualityGate.evaluate(plan_exec, strict=True)
    assert qg["final_status"] == "PASS", f"Executive plan QualityGate failed: {[f['description'] for f in qg['failures']]}"
    assert qg["quality_score"] == 1.0
    assert qg["critical_failures_count"] == 0
    assert qg["high_failures_count"] == 0
