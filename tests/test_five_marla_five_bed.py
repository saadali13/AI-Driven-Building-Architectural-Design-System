"""
Automated Test Suite for 5 Marla 5-Bedroom Feasibility & Two-Floor Coordinated Generation.

Validates:
1. Requirements Parsing & Feasibility Guard for 5 Marla 5-Bedroom program.
2. Conversion of Ground Floor Drawing Room into Bedroom 1 (Guest Suite) + attached bath.
3. Multi-Floor Coordinated Layout: 2 Bedrooms on Ground Floor, 3 Bedrooms on Level 1.
4. IBC Section 1207 compliance for each of the 5 bedrooms:
   - Minimum Floor Area >= 70 sq ft (6.50 m²).
   - Minimum Horizontal Dimension >= 7'-0" (2.13 m).
5. FloorPlanQualityGate Quality Score == 1.0 (PASS, 0 failures).
6. CoordinatedTwoFloorSolver verification:
   - Staircase geometry invariance (IoU >= 0.98).
   - Vertical wall stacking ratio >= 70%.
   - Continuous vertical shafts (OTS).
   - Clean setback coordination.
"""

import pytest
from requirements.parser import NaturalLanguageRequirementsParser, validate_architectural_feasibility
from generation.solver import CoordinatedTwoFloorSolver
from generation.quality_gate import FloorPlanQualityGate


class TestFiveMarlaFiveBed:

    @pytest.fixture
    def five_bed_program(self):
        prompt = "5 Marla residential house with 5 bedrooms, attached baths, and family lounge"
        prog = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=True)
        return prog

    def test_requirements_feasibility(self, five_bed_program):
        """Program parser must accept 5-bed 5-marla request as feasible with 2 GF beds."""
        assert five_bed_program.is_feasible is True
        assert len(five_bed_program.infeasibility_reasons) == 0
        assert five_bed_program.plot_category == "5_marla"
        assert five_bed_program.requested_room_counts.get("bedroom") == 5
        assert five_bed_program.ground_room_counts.get("bedroom") == 2
        # Drawing room is converted to Bedroom 1
        assert five_bed_program.ground_room_counts.get("drawing") == 0

    def test_plan_generation_and_room_distribution(self, five_bed_program):
        """Validates that CoordinatedTwoFloorSolver generates exactly 5 bedrooms (2 GF + 3 L1)."""
        plan = CoordinatedTwoFloorSolver.generate_rag_plan(five_bed_program)
        assert plan is not None
        assert plan.metadata.floor_count == 2
        assert plan.metadata.levels == [0, 1]

        all_beds = [r for r in plan.rooms if r.room_type == "bedroom"]
        gf_beds = [r for r in all_beds if r.level_index == 0]
        l1_beds = [r for r in all_beds if r.level_index == 1]

        assert len(all_beds) == 5, f"Expected exactly 5 bedrooms, got {len(all_beds)}"
        assert len(gf_beds) == 2, f"Expected 2 bedrooms on Ground Floor, got {len(gf_beds)}"
        assert len(l1_beds) == 3, f"Expected 3 bedrooms on Level 1, got {len(l1_beds)}"

        # Verify Ground Floor has Car Porch, TV Lounge, Kitchen, OTS
        l0_types = {r.room_type for r in plan.rooms if r.level_index == 0}
        assert "garage" in l0_types
        assert "lounge" in l0_types
        assert "kitchen" in l0_types
        assert "outdoor" in l0_types

        # Verify Level 1 has Upper Lounge, Balcony/Terrace, OTS
        l1_types = {r.room_type for r in plan.rooms if r.level_index == 1}
        assert "lounge" in l1_types
        assert "balcony" in l1_types or "outdoor" in l1_types

    def test_ibc_section_1207_minimum_dimensions(self, five_bed_program):
        """
        Verify each of the 5 bedrooms meets IBC Section 1207 minimum standards:
        - Floor Area >= 70 sq ft (6.50 m²).
        - Minimum Room Width/Dimension >= 7'-0" (2.13 m).
        """
        plan = CoordinatedTwoFloorSolver.generate_rag_plan(five_bed_program)
        bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]

        for bed in bedrooms:
            # 1. Minimum Floor Area
            assert bed.area_m2 >= 6.50, (
                f"Bedroom {bed.room_id} ({bed.room_name}) area {bed.area_m2}m² violates IBC Section 1207 minimum (6.50 m² / 70 sq ft)."
            )

            # 2. Minimum Width / Dimension
            poly = bed.polygon
            xs = [pt[0] for pt in poly]
            ys = [pt[1] for pt in poly]
            width = max(xs) - min(xs)
            depth = max(ys) - min(ys)
            min_dim = min(width, depth)

            assert min_dim >= 2.13, (
                f"Bedroom {bed.room_id} ({bed.room_name}) dimension {min_dim:.2f}m violates IBC Section 1207 minimum width (2.13m / 7'-0\")."
            )

    def test_quality_gate_and_two_floor_coordination(self, five_bed_program):
        """Validates 100% QualityGate compliance (score 1.0) and two-floor coordination."""
        plan = CoordinatedTwoFloorSolver.generate_rag_plan(five_bed_program)

        gate = FloorPlanQualityGate.evaluate(plan)
        assert gate["final_status"] == "PASS", f"QualityGate failures: {gate.get('failures')}"
        assert gate.get("quality_score") == 1.0, f"QualityGate score {gate.get('quality_score')} != 1.0"
        assert len(gate.get("failures", [])) == 0

        coord = CoordinatedTwoFloorSolver.verify_two_floor_coordination(plan)
        assert coord["is_valid"] is True, f"Two-floor coordination errors: {coord.get('errors')}"
        assert coord.get("stair_iou", 0) >= 0.98, f"Staircase invariance violated: {coord.get('stair_iou')}"
        assert coord.get("stacking_ratio", 0) >= 0.70, f"Vertical stacking violated: {coord.get('stacking_ratio')}"
