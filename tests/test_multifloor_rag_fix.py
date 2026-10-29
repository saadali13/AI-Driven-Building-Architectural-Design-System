"""
Test Suite: Multi-Floor Synthesis & Architectural First-Floor Derivation Verification
Tests 3 Marla, 5 Marla, 7 Marla, and 1 Kanal multi-storey synthesis.
Asserts:
- 100% QualityGate pass (Score == 1.0)
- Zero Critical failures
- Zero High failures
- Zero F01 errors (exact bedroom count match across floors)
- Zero F13 errors (statutory coverage & feasibility compliance)
"""

import pytest
from generation.rag_solver import DatasetDrivenRAGSolver
from generation.quality_gate import FloorPlanQualityGate
from requirements.parser import NaturalLanguageRequirementsParser


@pytest.fixture(scope="module")
def solver():
    return DatasetDrivenRAGSolver()


def test_3_marla_2_storey_3_beds(solver):
    prompt = "3 Marla 2-storey house with 3 bedrooms, 3 baths, lounge, kitchen, and drawing room"
    plan = solver.synthesize(prompt)
    prog = NaturalLanguageRequirementsParser.parse(prompt)
    gate = FloorPlanQualityGate.evaluate(plan, prog)

    # Architectural assertions
    assert plan.metadata.floor_count == 2, f"Expected 2 floors, got {plan.metadata.floor_count}"
    
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) == 3, f"Expected exactly 3 bedrooms, got {len(bedrooms)}"

    # Ground floor statutory coverage <= 75% (48.0 m²)
    gf_rooms = [r for r in plan.rooms if r.level_index == 0]
    gf_habitable_area = sum(r.area_m2 for r in gf_rooms if r.room_type != "garage")
    assert gf_habitable_area <= 48.0, f"Ground floor covered area {gf_habitable_area} m² exceeds 48.0 m² (75% limit)"

    # Quality Gate compliance
    assert gate["final_status"] == "PASS", f"Quality gate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0, f"Quality score {gate['quality_score']} is not 1.0"
    assert "F01" not in gate["failure_codes"], "F01 error found in quality report"
    assert "F13" not in gate["failure_codes"], "F13 error found in quality report"


def test_5_marla_2_storey_3_beds(solver):
    prompt = "5 Marla 2-storey house with 3 bedrooms, 3 baths, lounge, kitchen, and drawing room"
    plan = solver.synthesize(prompt)
    prog = NaturalLanguageRequirementsParser.parse(prompt)
    gate = FloorPlanQualityGate.evaluate(plan, prog)

    assert plan.metadata.floor_count == 2, f"Expected 2 floors, got {plan.metadata.floor_count}"
    
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) == 3, f"Expected exactly 3 bedrooms, got {len(bedrooms)}"

    # Quality Gate compliance
    assert gate["final_status"] == "PASS", f"Quality gate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0, f"Quality score {gate['quality_score']} is not 1.0"
    assert "F01" not in gate["failure_codes"], "F01 error found in quality report"
    assert "F13" not in gate["failure_codes"], "F13 error found in quality report"


def test_7_marla_2_storey_4_beds(solver):
    prompt = "7 Marla 2-storey house with 4 bedrooms, 4 baths, lounge, kitchen, and drawing room"
    plan = solver.synthesize(prompt)
    prog = NaturalLanguageRequirementsParser.parse(prompt)
    gate = FloorPlanQualityGate.evaluate(plan, prog)

    assert plan.metadata.floor_count == 2, f"Expected 2 floors, got {plan.metadata.floor_count}"
    
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) == 4, f"Expected exactly 4 bedrooms, got {len(bedrooms)}"

    # Quality Gate compliance
    assert gate["final_status"] == "PASS", f"Quality gate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0, f"Quality score {gate['quality_score']} is not 1.0"
    assert "F01" not in gate["failure_codes"], "F01 error found in quality report"
    assert "F13" not in gate["failure_codes"], "F13 error found in quality report"


def test_1_kanal_2_storey_4_beds(solver):
    prompt = "1 Kanal 2-storey luxury villa with 4 bedrooms, 4 baths, double kitchen, servant quarter, and lawn"
    plan = solver.synthesize(prompt)
    prog = NaturalLanguageRequirementsParser.parse(prompt)
    gate = FloorPlanQualityGate.evaluate(plan, prog)

    assert plan.metadata.floor_count == 2, f"Expected 2 floors, got {plan.metadata.floor_count}"
    
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) == 4, f"Expected exactly 4 bedrooms, got {len(bedrooms)}"

    # Quality Gate compliance
    assert gate["final_status"] == "PASS", f"Quality gate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0, f"Quality score {gate['quality_score']} is not 1.0"
    assert "F01" not in gate["failure_codes"], "F01 error found in quality report"
    assert "F13" not in gate["failure_codes"], "F13 error found in quality report"
