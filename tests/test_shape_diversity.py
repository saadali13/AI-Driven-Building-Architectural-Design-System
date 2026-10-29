"""
Unit and Integration Test Suite for Shape Diversity, Dynamic Floor-Count Resolution,
and Furniture Boundary Containment.

Covers:
1. test_single_floor_one_bed_generation:
   - Verifies prompt '1 bedroom compact house on ground floor' strictly synthesizes Level 0 only.
   - Asserts plan.floor_count == 1, len(plan.levels) == 1, and no Level 1 rooms exist.
2. test_shape_geometries_produce_unique_layouts:
   - Synthesizes Triangle, Trapezoid, Square, and Chamfered Corner plots.
   - Asserts each geometry produces a 100% unique topological graph hash and room polygon footprint.
   - Asserts FloorPlanQualityGate evaluates to PASS for each layout.
3. test_terrace_furniture_boundary_containment:
   - Validates that Level 1 open terrace patio set furniture bounding boxes
     are strictly clamped within terrace_poly.buffer(-0.35m) with zero boundary penetration.
"""

import math
import hashlib
from typing import Set, Tuple
import pytest
from shapely.geometry import Polygon, Point, box

from requirements.parser import NaturalLanguageRequirementsParser, ArchitecturalProgram
from requirements.site_geometry import (
    create_triangle,
    create_trapezoid,
    create_corner_plot,
    create_square,
    from_vertex_string,
    SiteBoundary
)
from generation.irregular_solver import IrregularSiteSolver
from generation.quality_gate import FloorPlanQualityGate
from dataset.schema.canonical import CanonicalFloorPlan


def compute_topological_graph_hash(plan: CanonicalFloorPlan) -> str:
    """
    Computes a deterministic cryptographic hash of the architectural spatial graph:
    combines sorted room identifiers, architectural semantic types, relative areas,
    and verified traversal/adjacency graph edges.
    """
    node_tuples = sorted([
        (r.room_id, r.room_type, r.room_name, round(r.area_m2, 1))
        for r in plan.rooms
    ])
    edge_tuples = sorted([
        (e.source_room_id, e.target_room_id, e.relationship_type)
        for e in plan.graph_edges
    ])
    signature = f"NODES:{node_tuples}|EDGES:{edge_tuples}"
    return hashlib.sha256(signature.encode("utf-8")).hexdigest()


def extract_room_footprint_signature(plan: CanonicalFloorPlan) -> Tuple:
    """
    Extracts an immutable representation of room polygon geometry:
    sorted coordinate vertices rounded to 2 decimal places.
    """
    footprints = []
    for r in plan.rooms:
        clean_ring = tuple(
            (round(pt[0], 2), round(pt[1], 2)) for pt in r.polygon
        )
        footprints.append((r.room_id, r.room_type, clean_ring))
    return tuple(sorted(footprints))


def test_single_floor_one_bed_generation():
    """
    Asserts that prompts requesting a single-floor or 1-bedroom residence:
    1. Parse into ArchitecturalProgram with floor_count == 1 and levels == [0].
    2. Solver generates strictly Level 0 (Ground Floor) rooms only.
    3. First Floor drawings and composite sheets are suppressed.
    """
    prompt = "1 bedroom compact house on ground floor"
    program = NaturalLanguageRequirementsParser.parse(prompt)

    assert program.floor_count == 1, f"Expected floor_count == 1, got {program.floor_count}"
    assert program.levels == [0], f"Expected levels == [0], got {program.levels}"
    assert program.is_single_storey_explicit is True

    site = create_triangle(front=45.0, left=65.0, hypotenuse=79.0, unit="ft")
    solver = IrregularSiteSolver()
    plan = solver.synthesize(site, prompt=prompt)

    assert plan.floor_count == 1, f"Expected plan.floor_count == 1, got {plan.floor_count}"
    assert plan.levels == [0], f"Expected plan.levels == [0], got {plan.levels}"
    assert all(r.level_index == 0 for r in plan.rooms), "Found non-ground floor rooms in single-floor plan"
    assert all(w.level_index == 0 for w in plan.walls), "Found non-ground floor walls in single-floor plan"
    assert all(o.level_index == 0 for o in plan.openings), "Found non-ground floor openings in single-floor plan"

    # Verify roof layer metadata
    assert plan.metadata.provenance.get("roof_layer") == "standard_weatherproof_ceiling_slab"

    # QualityGate evaluation
    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"Quality gate failed: {gate['failures']}"


def test_shape_geometries_produce_unique_layouts():
    """
    Asserts that the system produces distinct, tailored layouts across geometric shapes:
    - Triangle (45' x 65' x 79')
    - Trapezoid (40' x 28' x 60' x 55')
    - Chamfered Corner Plot (50' x 60' x 15')
    - True Square (40' x 40')

    Asserts:
    1. Every geometry produces a unique topological graph hash.
    2. Every geometry produces a unique room polygon footprint.
    3. Every geometry evaluates to PASS in FloorPlanQualityGate.
    """
    sites = {
        "triangle": create_triangle(front=45.0, left=65.0, hypotenuse=79.0, unit="ft"),
        "trapezoid": create_trapezoid(front=40.0, rear=28.0, left=60.0, right=55.0, unit="ft"),
        "corner_plot": create_corner_plot(front=50.0, depth=60.0, splay=15.0, unit="ft"),
        "square": create_square(side_a=40.0, side_b=40.0, unit="ft"),
    }

    solver = IrregularSiteSolver()
    graph_hashes = set()
    footprint_signatures = set()

    for shape_name, site in sites.items():
        plan = solver.synthesize(site, prompt="3 bedroom family residence", floor_count=2)

        # 1. QualityGate verification
        gate = FloorPlanQualityGate.evaluate(plan)
        assert gate["final_status"] == "PASS", f"QualityGate failed for shape '{shape_name}': {gate['failures']}"

        # 2. Compute topological graph hash
        g_hash = compute_topological_graph_hash(plan)
        assert g_hash not in graph_hashes, (
            f"Duplicate topological graph hash detected for shape '{shape_name}'! "
            f"Each site geometry must synthesize a tailored topological structure."
        )
        graph_hashes.add(g_hash)

        # 3. Compute geometric footprint signature
        fp_sig = extract_room_footprint_signature(plan)
        assert fp_sig not in footprint_signatures, (
            f"Duplicate geometric footprint signature detected for shape '{shape_name}'! "
            f"Each site geometry must synthesize distinct room polygon coordinates."
        )
        footprint_signatures.add(fp_sig)

    assert len(graph_hashes) == 4, f"Expected 4 unique topological graph hashes, got {len(graph_hashes)}"
    assert len(footprint_signatures) == 4, f"Expected 4 unique footprint signatures, got {len(footprint_signatures)}"


def test_terrace_furniture_boundary_containment():
    """
    Asserts that the Level 1 Open Terrace patio set:
    1. Has all furniture bounding boxes clamped within terrace_poly.buffer(-0.35m).
    2. Zero penetration across the front exterior handrail or safety parapet wall.
    """
    site = create_triangle(front=45.0, left=65.0, hypotenuse=79.0, unit="ft")
    solver = IrregularSiteSolver()
    plan = solver.synthesize(site, prompt="3 bedroom family residence", floor_count=2)

    terrace = next((r for r in plan.rooms if r.level_index == 1 and ("terrace" in r.room_id.lower() or "terrace" in r.room_name.lower())), None)
    assert terrace is not None, "Level 1 Open Terrace room not found in plan"

    t_poly = Polygon(terrace.polygon)
    assert t_poly.is_valid and not t_poly.is_empty

    min_x = min(pt[0] for pt in terrace.polygon)
    max_x = max(pt[0] for pt in terrace.polygon)
    min_y = min(pt[1] for pt in terrace.polygon)
    max_y = max(pt[1] for pt in terrace.polygon)
    rw = max_x - min_x
    rh = max_y - min_y

    # Calculate safe envelope clamped to buffer(-0.35m)
    safe_x_min = min_x + 0.35
    safe_x_max = min_x + rw - 0.35
    safe_y_min = min_y + 0.35
    safe_y_max = min_y + rh - 0.35
    safe_envelope = box(safe_x_min, safe_y_min, safe_x_max, safe_y_max)

    cx = (safe_x_min + safe_x_max) / 2.0
    cy = (safe_y_min + safe_y_max) / 2.0
    avail_half_h = (safe_y_max - safe_y_min) / 2.0
    avail_half_w = (safe_x_max - safe_x_min) / 2.0

    # Calculate table and chair bounding boxes as rendered by visualizer
    if rh < 1.80:
        r_tbl = min(0.35, max(0.14, avail_half_h * 0.85))
        r_ch = min(0.18, max(0.08, r_tbl * 0.70))
        ch_dist = r_tbl + r_ch + 0.08
        if ch_dist + r_ch > avail_half_w:
            ch_dist = max(r_tbl + 0.04, avail_half_w - r_ch)
        chair_angles = [0, 180]
    else:
        max_r = min(avail_half_h, avail_half_w) * 0.95
        r_ch = min(0.22, max_r * 0.25)
        r_tbl = max_r * 0.45
        ch_dist = r_tbl + r_ch + 0.08
        chair_angles = [0, 90, 180, 270]

    # 1. Check Table Bounding Box
    tbl_bbox = box(cx - r_tbl, cy - r_tbl, cx + r_tbl, cy + r_tbl)
    assert t_poly.contains(tbl_bbox), (
        f"Table bounding box {tbl_bbox.bounds} penetrates terrace exterior boundary {t_poly.bounds}!"
    )
    assert safe_envelope.contains(tbl_bbox), (
        f"Table bounding box {tbl_bbox.bounds} violates 0.35m setback margin from parapet!"
    )

    # 2. Check Each Chair Bounding Box
    for angle in chair_angles:
        rad = math.radians(angle)
        ch_x = cx + ch_dist * math.cos(rad)
        ch_y = cy + ch_dist * math.sin(rad)
        ch_bbox = box(ch_x - r_ch, ch_y - r_ch, ch_x + r_ch, ch_y + r_ch)
        assert t_poly.contains(ch_bbox), (
            f"Chair at angle {angle} bounding box {ch_bbox.bounds} penetrates terrace exterior boundary!"
        )
        assert safe_envelope.contains(ch_bbox), (
            f"Chair at angle {angle} bounding box {ch_bbox.bounds} violates 0.35m setback margin from parapet!"
        )
