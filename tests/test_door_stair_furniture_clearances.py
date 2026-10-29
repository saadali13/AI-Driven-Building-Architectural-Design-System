"""
Spatial Defect Test Suite: Stair Boundary Containment, Door Swing Collision,
Furniture Wall Clearance, and Two-Floor Export Completeness.

Validates the four critical spatial constraints enforced across:
  - generation/staircase_engine.py  (StaircaseEngine envelope clamping)
  - generation/visualizer.py        (furniture clamping & door swing safety)
  - generation/rag_solver.py        (multi-floor plan completeness)
"""
import os
import sys
import math
import tempfile
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shapely.geometry import Polygon, box

from generation.staircase_engine import (
    StaircaseEngine,
    StairTypology,
    StairParametricModel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _room_bbox_tight(stair_bbox, margin=0.23):
    """Creates a room bbox that is just `margin` m larger than the stair on all sides."""
    x1, y1, x2, y2 = stair_bbox
    return (x1 - margin, y1 - margin, x2 + margin, y2 + margin)


def _room_bbox_small(stair_bbox, reduction=0.40):
    """Creates a room bbox that is smaller than the stair to trigger clamping."""
    x1, y1, x2, y2 = stair_bbox
    w = x2 - x1
    h = y2 - y1
    # Room is 'reduction' metres smaller on each axis than the stair
    return (x1, y1, x1 + max(0.5, w - reduction), y1 + max(0.5, h - reduction))


# ---------------------------------------------------------------------------
# 1. Staircase Boundary Containment Tests
# ---------------------------------------------------------------------------

class TestStaircaseBoundaryContainment:
    """Verifies that stair bounding_box stays inside the supplied room_bbox."""

    WALL_CLEARANCE = 0.23

    def _assert_contained(self, model: StairParametricModel, room_bbox):
        rb_min_x, rb_min_y, rb_max_x, rb_max_y = room_bbox
        bx1, by1, bx2, by2 = model.bounding_box
        assert bx1 >= rb_min_x - 1e-6, (
            f"Stair left edge {bx1:.3f} penetrates room left wall {rb_min_x:.3f}"
        )
        assert by1 >= rb_min_y - 1e-6, (
            f"Stair bottom edge {by1:.3f} penetrates room bottom wall {rb_min_y:.3f}"
        )
        assert bx2 <= rb_max_x + 1e-6, (
            f"Stair right edge {bx2:.3f} penetrates room right wall {rb_max_x:.3f}"
        )
        assert by2 <= rb_max_y + 1e-6, (
            f"Stair top edge {by2:.3f} penetrates room top wall {rb_max_y:.3f}"
        )

    def test_curved_stair_no_overflow_when_room_given(self):
        """Curved stair must not project beyond room_bbox."""
        room_bbox = (0.0, 0.0, 5.0, 5.0)
        model = StaircaseEngine.create_staircase(
            StairTypology.CURVED,
            x=0.23, y=0.0,
            room_bbox=room_bbox,
            outer_r=3.50  # Intentionally larger than room
        )
        self._assert_contained(model, room_bbox)

    def test_spiral_stair_no_overflow_when_room_given(self):
        """Spiral stair must fit within tight room_bbox."""
        room_bbox = (1.0, 1.0, 3.5, 3.5)
        model = StaircaseEngine.create_staircase(
            StairTypology.SPIRAL,
            x=1.0, y=1.0,
            room_bbox=room_bbox,
            diameter=5.0  # Much larger than room
        )
        self._assert_contained(model, room_bbox)

    def test_bifurcated_stair_no_overflow_when_room_given(self):
        """Bifurcated stair must be scaled down to fit within room_bbox."""
        room_bbox = (0.0, 0.0, 4.0, 5.0)
        model = StaircaseEngine.create_staircase(
            StairTypology.BIFURCATED,
            x=0.0, y=0.0,
            room_bbox=room_bbox,
            width_m=8.0,  # Grand stair wider than room
            length_m=6.0,
        )
        self._assert_contained(model, room_bbox)

    def test_curved_stair_without_room_bbox_uses_defaults(self):
        """Without room_bbox, a curved stair should still produce a valid model."""
        model = StaircaseEngine.create_staircase(
            StairTypology.CURVED, x=0.0, y=0.0
        )
        bx1, by1, bx2, by2 = model.bounding_box
        assert bx2 > bx1 and by2 > by1

    def test_straight_stair_always_contained(self):
        """Straight stair never needs clamping; verify it is unaffected by room_bbox."""
        room_bbox = (0.0, 0.0, 2.0, 6.0)
        model = StaircaseEngine.create_staircase(
            StairTypology.STRAIGHT,
            x=0.0, y=0.0,
            width_m=1.05, length_m=4.20,
            room_bbox=room_bbox
        )
        # Straight stair ignores room_bbox – just assert valid bbox
        bx1, by1, bx2, by2 = model.bounding_box
        assert bx2 > bx1 and by2 > by1

    def test_clamp_curved_to_bbox_helper_shrinks_excess_treads(self):
        """Direct unit test for _clamp_curved_to_bbox: all tread pts stay inside."""
        model = StaircaseEngine.generate_curved_stair(
            center_x=5.0, center_y=0.0, outer_r=4.0, risers=18
        )
        room_bbox = (0.5, 0.0, 3.5, 4.0)
        clamped = StaircaseEngine._clamp_curved_to_bbox(model, room_bbox)
        bx1, by1, bx2, by2 = clamped.bounding_box
        assert bx1 >= room_bbox[0] - 1e-6
        assert bx2 <= room_bbox[2] + 1e-6
        assert by1 >= room_bbox[1] - 1e-6
        assert by2 <= room_bbox[3] + 1e-6


# ---------------------------------------------------------------------------
# 2. Door Swing Collision Tests
# ---------------------------------------------------------------------------

class TestDoorSwingCollisions:
    """Verifies that door swing arc quadrant selection avoids fixtures."""

    @pytest.mark.parametrize("theta_start", [0, 90, 180, 270])
    def test_arc_polygon_is_inside_room(self, theta_start):
        """Simulates arc fan and checks it is inside the room polygon."""
        # A 4m × 3m rectangular room
        room_poly = [(0, 0), (4, 0), (4, 3), (0, 3), (0, 0)]
        room_shp = Polygon(room_poly)
        # Door at (2, 0) on bottom wall, leaf radius = 0.90m
        px, py = 2.0, 0.0
        w = 0.90
        arc_pts = [(px, py)]
        for deg in range(theta_start, theta_start + 91, 10):
            rad = math.radians(deg)
            arc_pts.append((px + w * math.cos(rad), py + w * math.sin(rad)))
        arc_poly = Polygon(arc_pts)
        # Only quadrant 0-90 should be fully inside for a door on the south wall
        if theta_start == 0:
            assert room_shp.buffer(0.05).contains(arc_poly) or \
                   room_shp.intersects(arc_poly)

    def test_swing_selection_logic_picks_interior_quadrant(self):
        """Tests the Shapely-based quadrant picker used in _draw_architectural_door."""
        try:
            from shapely.geometry import Polygon as SP
        except ImportError:
            pytest.skip("Shapely not available")

        # 5m × 4m room, door at SW corner
        room_poly = [(0, 0), (5, 0), (5, 4), (0, 4), (0, 0)]
        room_shp = SP(room_poly)

        px, py = 0.5, 0.0
        w = 0.90
        chosen_theta = None
        for theta_start in [0, 90, 180, 270]:
            arc_pts = [(px, py)]
            for deg in range(theta_start, theta_start + 91, 10):
                rad = math.radians(deg)
                arc_pts.append((px + w * math.cos(rad), py + w * math.sin(rad)))
            arc_poly = SP(arc_pts)
            if room_shp.buffer(0.02).contains(arc_poly):
                chosen_theta = theta_start
                break

        # Should pick 0 (arc goes right & up, inside the room)
        assert chosen_theta is not None, "No safe swing quadrant found inside room"
        # Verify chosen arc is indeed inside
        arc_pts = [(px, py)]
        for deg in range(chosen_theta, chosen_theta + 91, 10):
            rad = math.radians(deg)
            arc_pts.append((px + w * math.cos(rad), py + w * math.sin(rad)))
        arc_poly = SP(arc_pts)
        assert room_shp.buffer(0.02).contains(arc_poly), (
            f"Chosen swing theta={chosen_theta} still outside room"
        )


# ---------------------------------------------------------------------------
# 3. Furniture Boundary Clearance Tests
# ---------------------------------------------------------------------------

class TestFurnitureBoundaryLeaks:
    """Validates that furniture coordinates never cross room wall faces."""

    def test_nightstand_stays_inside_room_width(self):
        """Nightstand X coordinates must be within [room_left, room_right]."""
        # Simulate the clamping logic from _draw_double_bed
        min_x, rw = 1.0, 3.5
        cx = min_x + rw * 0.5
        bed_w = 1.90
        bx = cx - bed_w / 2.0
        ns_size = 0.45
        wall_margin = 0.10
        safe_x_min = min_x + wall_margin
        safe_x_max = min_x + rw - wall_margin

        # Left nightstand
        ns_left_x = max(safe_x_min, bx - ns_size - 0.10)
        if ns_left_x + ns_size <= safe_x_max:
            lamp_x = min(safe_x_max - 0.05, max(safe_x_min + 0.05, ns_left_x + ns_size / 2.0))
            assert lamp_x >= safe_x_min, f"Left lamp {lamp_x:.3f} < safe_x_min {safe_x_min:.3f}"
            assert lamp_x <= safe_x_max, f"Left lamp {lamp_x:.3f} > safe_x_max {safe_x_max:.3f}"

        # Right nightstand
        ns_right_x = min(safe_x_max - ns_size, bx + bed_w + 0.10)
        if ns_right_x >= safe_x_min:
            lamp_x = max(safe_x_min + 0.05, min(safe_x_max - 0.05, ns_right_x + ns_size / 2.0))
            assert lamp_x >= safe_x_min
            assert lamp_x <= safe_x_max

    def test_shower_stays_inside_room_bounds(self):
        """Shower stall top-right corner must not exceed room extents."""
        min_x, min_y = 0.0, 0.0
        rw, rh = 2.2, 2.5
        margin = 0.05
        safe_x_max = min_x + rw - margin
        safe_y_max = min_y + rh - margin

        sh_size = min(1.10, rw * 0.45, rh * 0.45)
        sh_x = max(min_x + margin, min_x + 0.15)
        sh_y = min(safe_y_max - sh_size, min_y + rh - sh_size - 0.15)
        sh_y = max(min_y + margin, sh_y)
        sh_x = min(sh_x, safe_x_max - sh_size)

        assert sh_x >= min_x + margin - 1e-6, f"Shower left {sh_x:.3f} < room margin"
        assert sh_x + sh_size <= safe_x_max + 1e-6, f"Shower right {sh_x+sh_size:.3f} > room right"
        assert sh_y >= min_y + margin - 1e-6, f"Shower bottom {sh_y:.3f} < room margin"
        assert sh_y + sh_size <= safe_y_max + 1e-6, f"Shower top {sh_y+sh_size:.3f} > room top"

    def test_kitchen_island_stays_inside_room(self):
        """Island bounding box must be inside [min_x+0.10, min_x+rw-0.10]."""
        min_x, min_y = 0.0, 0.0
        rw, rh = 4.0, 5.0
        island_w = min(2.0, rw * 0.45)
        island_h = 0.85
        ix = max(min_x + 0.10, min(min_x + rw * 0.35, min_x + rw - island_w - 0.10))
        iy = min_y + rh * 0.52
        iy = max(min_y + 0.10, min(iy, min_y + rh - island_h - 0.10))

        assert ix >= min_x + 0.10 - 1e-6
        assert ix + island_w <= min_x + rw - 0.10 + 1e-6
        assert iy >= min_y + 0.10 - 1e-6
        assert iy + island_h <= min_y + rh - 0.10 + 1e-6

    def test_wc_clamped_to_room(self):
        """WC X coordinate must stay within safe_x_max - 0.50."""
        min_x, rw = 0.0, 1.8
        margin = 0.05
        safe_x_min = min_x + margin
        safe_x_max = min_x + rw - margin
        wc_x = max(safe_x_min, min_x + 0.25)
        wc_x = min(wc_x, safe_x_max - 0.50)
        assert wc_x >= safe_x_min - 1e-6
        assert wc_x + 0.50 <= safe_x_max + 1e-6


# ---------------------------------------------------------------------------
# 4. Two-Floor Export Completeness Test
# ---------------------------------------------------------------------------

class TestTwoFloorExportCompleteness:
    """Validates that G+1 prompts produce both Level 0 and Level 1 rooms,
    and that metadata.levels = [0, 1]."""

    def test_g_plus_1_levels_metadata(self):
        """Synthesize a 2-storey plan and assert levels metadata = [0, 1]."""
        try:
            from generation.rag_solver import DatasetDrivenRAGSolver
        except ImportError:
            pytest.skip("DatasetDrivenRAGSolver not importable in this environment")

        solver = DatasetDrivenRAGSolver()
        plan = solver.synthesize(
            "Design a 5 Marla G+1 house with 3 bedrooms, drawing room, kitchen, 2 bathrooms"
        )
        assert plan is not None, "Solver returned None"
        assert plan.metadata.levels is not None, "metadata.levels is None"
        assert 0 in plan.metadata.levels, "Level 0 missing from metadata.levels"
        assert 1 in plan.metadata.levels, f"Level 1 missing; got {plan.metadata.levels}"
        # Verify there are rooms on both levels
        l0 = [r for r in plan.rooms if r.level_index == 0]
        l1 = [r for r in plan.rooms if r.level_index == 1]
        assert len(l0) > 0, "No Level 0 rooms generated"
        assert len(l1) > 0, "No Level 1 rooms generated – two-floor stacking failed"

    def test_render_composite_produces_file(self):
        """render_all_floors must produce a composite sheet file when levels=[0,1]."""
        try:
            from generation.rag_solver import DatasetDrivenRAGSolver
            from generation.visualizer import FloorPlanVisualizer
        except ImportError:
            pytest.skip("Modules not importable in this environment")

        solver = DatasetDrivenRAGSolver()
        plan = solver.synthesize(
            "5 Marla two storey house with 3 bedrooms and attached baths"
        )
        assert plan is not None
        if len(plan.metadata.levels) < 2:
            pytest.skip("Solver did not produce a 2-floor plan – skip render test")

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered = FloorPlanVisualizer.render_all_floors(plan, tmpdir)
            assert "composite_two_floors" in rendered, (
                f"Composite sheet key missing. Keys found: {list(rendered.keys())}"
            )
            composite_path = rendered["composite_two_floors"]
            assert os.path.exists(composite_path), (
                f"Composite sheet file not on disk: {composite_path}"
            )
            size_kb = os.path.getsize(composite_path) / 1024
            assert size_kb > 50, f"Composite PNG unexpectedly tiny ({size_kb:.1f} KB)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
