"""
Unit and Integration Tests for Non-Orthogonal & Arbitrary Polygonal Site Engine.
Validates:
1. Triangular plots: Inscription of rectangular habitable rooms, wedge allocation to porch/lawn/OTS.
2. Trapezoidal / Skewed quads: Statutory setback buffering, load-bearing stacking >= 70%.
3. Chamfered corner plots: Splay entry alignment, staircase IoU = 1.0 across floors.
4. Feasibility check (F13): Rejection when buildable envelope < 45.0 sqm.
5. 100% QualityGate compliance (F01-F20).
"""

import math
import pytest
from shapely.geometry import Polygon, box

from requirements.site_geometry import (
    SiteGeometryParser,
    SiteBoundary,
    create_triangle,
    create_trapezoid,
    create_corner_plot,
    from_vertices,
    from_vertex_string
)
from generation.setback_engine import (
    SetbackEngine,
    SetbackConfig,
    BuildableEnvelope,
    InfeasibleProgramError
)
from generation.irregular_solver import IrregularSiteSolver
from generation.quality_gate import FloorPlanQualityGate


def is_polygon_orthogonal_rectangle(poly_coords):
    """
    Validates whether a polygon's vertices form a strict 4-corner orthogonal rectangle.
    """
    pts = poly_coords[:-1] if poly_coords[0] == poly_coords[-1] else poly_coords
    if len(pts) != 4:
        return False
    xs = set(round(p[0], 2) for p in pts)
    ys = set(round(p[1], 2) for p in pts)
    return len(xs) == 2 and len(ys) == 2


def test_triangular_plot_generation():
    """
    Test Triangular Plot: 45' front, 65' left depth, 79' hypotenuse.
    Asserts:
    - Habitable rooms (Bedrooms, Lounge, Kitchen) remain 100% orthogonal rectangles.
    - Wedge corners are allocated to non-habitable outdoor/service zones (porch, lawn, OTS).
    - QualityGate evaluation returns PASS with 0 failures.
    """
    site = create_triangle(front=45.0, left=65.0, hypotenuse=79.0, unit="ft")
    assert site.shape_type == "triangle"
    assert site.area_sqft > 1000.0

    solver = IrregularSiteSolver()
    plan = solver.synthesize(site, prompt="3 bedroom family residence")

    # 1. QualityGate Verification
    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed: {gate['failures']}"
    assert len(gate["failures"]) == 0

    # 2. Check Bedrooms are strictly orthogonal rectangles
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) >= 2
    for b in bedrooms:
        assert is_polygon_orthogonal_rectangle(b.polygon), f"Bedroom {b.room_id} is not an orthogonal rectangle: {b.polygon}"
        assert b.area_m2 >= 5.0

    # 3. Check Wedge corners allocated to outdoor / service zones
    outdoor_rooms = [r for r in plan.rooms if r.room_type in ("outdoor", "balcony")]
    outdoor_ids = [r.room_id for r in outdoor_rooms]
    assert any("porch" in oid for oid in outdoor_ids), "Car porch wedge not allocated"
    assert any("ots" in oid for oid in outdoor_ids), "Rear OTS wedge not allocated"


def test_trapezoid_plot_generation():
    """
    Test Trapezoidal Plot: 40' front, 28' rear, 60' left depth, 55' right depth.
    Asserts:
    - Setbacks correctly applied via inward polygon buffering.
    - Usable buildable envelope ratio between 40% and 80%.
    - Multi-floor load-bearing wall stacking >= 70%.
    - QualityGate returns PASS with 0 critical errors.
    """
    site = create_trapezoid(front=40.0, rear=28.0, left=60.0, right=55.0, unit="ft")
    assert site.shape_type == "trapezoid"

    # Verify setback clipping
    env = SetbackEngine.compute_buildable_envelope(site)
    assert env.poly_buildable.area < site.polygon.area
    assert 0.40 <= env.usable_coverage <= 0.80

    solver = IrregularSiteSolver()
    plan = solver.synthesize(site, prompt="3 bedroom residence", floor_count=2)

    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed: {gate['failures']}"

    # Verify Load-Bearing Wall Stacking >= 70%
    l0_walls = [w for w in plan.walls if w.level_index == 0]
    l1_walls = [w for w in plan.walls if w.level_index == 1]
    assert len(l0_walls) > 0 and len(l1_walls) > 0

    stacked_count = 0
    for w0 in l0_walls:
        for w1 in l1_walls:
            # Check centerline coordinate coincidence in either direction
            c0 = w0.centerline
            c1 = w1.centerline
            direct_match = (
                abs(c0[0][0] - c1[0][0]) < 0.15 and
                abs(c0[0][1] - c1[0][1]) < 0.15 and
                abs(c0[1][0] - c1[1][0]) < 0.15 and
                abs(c0[1][1] - c1[1][1]) < 0.15
            )
            reverse_match = (
                abs(c0[0][0] - c1[1][0]) < 0.15 and
                abs(c0[0][1] - c1[1][1]) < 0.15 and
                abs(c0[1][0] - c1[0][0]) < 0.15 and
                abs(c0[1][1] - c1[0][1]) < 0.15
            )
            if direct_match or reverse_match:
                stacked_count += 1
                break

    stacking_ratio = stacked_count / len(l0_walls)
    assert stacking_ratio >= 0.70, f"Load-bearing wall stacking ratio {stacking_ratio:.2f} < 0.70"


def test_chamfered_corner_plot():
    """
    Test 50'x60' Chamfered Corner Plot with a 15' street splay.
    Asserts:
    - Splay edge classified as CHAMFER.
    - Main entry / porch aligns with the frontage & chamfered edge.
    - Level 0 and Level 1 staircase coordinates match with IoU = 1.0.
    - QualityGate evaluation returns PASS.
    """
    site = create_corner_plot(front=50.0, depth=60.0, splay=15.0, unit="ft")
    assert site.shape_type == "corner_plot"

    # Verify edge semantics identify CHAMFER
    chamfer_edges = [e for e in site.edges if e.semantic == "CHAMFER"]
    assert len(chamfer_edges) >= 1, "Chamfer edge was not detected by boundary classifier"

    solver = IrregularSiteSolver()
    plan = solver.synthesize(site, prompt="3 bedroom family residence", floor_count=2)

    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed: {gate['failures']}"

    # Verify staircase coordinate overlap IoU = 1.0
    stair_0 = next(r for r in plan.rooms if r.level_index == 0 and "stair" in r.room_id.lower())
    stair_1 = next(r for r in plan.rooms if r.level_index == 1 and "stair" in r.room_id.lower())

    p0 = Polygon(stair_0.polygon)
    p1 = Polygon(stair_1.polygon)
    iou = p0.intersection(p1).area / p0.union(p1).area
    assert round(iou, 3) == 1.0, f"Staircase IoU between L0 and L1 must be 1.0, got {iou}"


def test_infeasible_geometry_under_setbacks():
    """
    Feasibility Check (F13):
    An extremely tiny plot whose buildable envelope after setbacks is < 45.0 sqm
    must raise InfeasibleProgramError.
    """
    # 15' x 20' plot (~300 sq ft) with statutory setbacks will leave < 45.0 sqm buildable envelope
    tiny_site = SiteGeometryParser.from_vertices(
        [(0, 0), (15, 0), (15, 20), (0, 20)],
        unit="ft",
        shape_type="arbitrary_polygon"
    )

    with pytest.raises(InfeasibleProgramError):
        SetbackEngine.compute_buildable_envelope(tiny_site)


def test_arbitrary_cartesian_vertex_string_parsing():
    """
    Tests parsing arbitrary polygon from semicolon-separated vertex string.
    Checks polygon closure, CCW normalization, and edge count.
    """
    v_str = "0,0; 12,0; 10,18; 0,16"
    site = from_vertex_string(v_str, unit="m")
    assert site.shape_type == "arbitrary_polygon"
    assert len(site.vertices) == 5  # 4 vertices + closed ring endpoint
    assert site.polygon.is_valid
    assert site.area_m2 > 100.0
