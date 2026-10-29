"""
Unit tests for Phase 11:
Natural Language Requirements Parsing, Staged CP-SAT Layout Generation, and Validation.
"""

import pytest
from requirements.parser import NaturalLanguageRequirementsParser
from generation.solver import LayoutGenerator
from generation.validation import LayoutValidator


def test_requirements_parser_3bhk():
    prompt = "I want a 3BHK modern family home with 2 bathrooms, an open kitchen, and a master bedroom with attached bathroom. Total area around 120 sqm."
    program = NaturalLanguageRequirementsParser.parse(prompt)

    assert program.total_target_area_m2 == 120.0
    
    # Verify room types
    r_types = [r.room_type for r in program.rooms]
    assert r_types.count("bedroom") == 3
    assert r_types.count("bathroom") == 2
    assert "living_room" in r_types
    assert "kitchen" in r_types

    # Verify adjacencies
    master_bath_adj = any(
        a.source_room_name == "Master Bedroom" and a.target_room_name == "Master Bathroom"
        for a in program.adjacencies
    )
    assert master_bath_adj is True


def test_staged_cpsat_solver_and_validator():
    prompt = "2BHK house with 1 bathroom, living room and kitchen, 80 sqm"
    program = NaturalLanguageRequirementsParser.parse(prompt)

    generator = LayoutGenerator(grid_scale=0.5)
    plan = generator.generate_layout(program, max_time_seconds=10.0)

    assert plan is not None, "CP-SAT solver should find a feasible layout"
    assert len(plan.rooms) == len(program.rooms)

    # Validate with LayoutValidator
    val_result = LayoutValidator.validate_plan(plan)
    assert val_result["is_valid"] is True, f"Validation failed with issues: {val_result['issues']}"
    assert val_result["issue_count"] == 0

    # Verify walls and openings exist
    assert len(plan.walls) >= 4, "Should have exterior and interior walls"
    assert len(plan.openings) >= 1, "Should have doors connecting rooms"

    # Verify room boundaries don't overlap geometrically
    for i in range(len(plan.rooms)):
        from shapely.geometry import Polygon
        p1 = Polygon(plan.rooms[i].polygon)
        for j in range(i + 1, len(plan.rooms)):
            p2 = Polygon(plan.rooms[j].polygon)
            overlap = p1.intersection(p2).area
            assert overlap < 0.05, f"Rooms {plan.rooms[i].room_name} and {plan.rooms[j].room_name} overlap by {overlap} m2"


def test_spanish_3_marla_residence():
    from generation.architectural_templates import Spanish3MarlaArchitecturalEngine
    plan = Spanish3MarlaArchitecturalEngine.generate_3_marla_house()

    assert plan is not None
    assert plan.metadata.floor_count == 2
    assert len(plan.rooms) >= 15
    assert len(plan.walls) >= 15
    assert len(plan.openings) >= 10

    # Validate layout
    val = LayoutValidator.validate_plan(plan)
    assert val["is_valid"] is True, f"Validation failed: {val['issues']}"

    # Verify 3 bedrooms each with attached bath
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    bathrooms = [r for r in plan.rooms if r.room_type == "bathroom"]
    assert len(bedrooms) == 3
    assert len(bathrooms) >= 4  # 3 attached + 1 powder

    # Verify staircase exact alignment between Level 0 and Level 1
    stairs_l0 = next(r for r in plan.rooms if r.room_id == "room_L0_stairs")
    stairs_l1 = next(r for r in plan.rooms if r.room_id == "room_L1_stairs")
    assert stairs_l0.polygon == stairs_l1.polygon
    assert stairs_l0.centroid == stairs_l1.centroid
