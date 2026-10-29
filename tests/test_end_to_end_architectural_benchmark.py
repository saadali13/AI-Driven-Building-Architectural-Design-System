"""
End-to-End Architectural Benchmark Test Suite.
Validates the entire pipeline against TESTS 1-5 defined in the master specification:
- TEST 1: 5 Marla, 3 beds, 2 baths, master attached bath, single-storey.
- TEST 2: 5 Marla, 4 beds, 4 attached baths, powder room, garage, kitchen, dining, TV lounge.
- TEST 3: 10 Marla, 2 storey, 5 beds, attached baths, drawing, dining, kitchen, TV lounge, double garage.
- TEST 4: 1 Kanal, 5 beds, attached baths, drawing, dining, double kitchen, courtyard, double garage.
- TEST 5: Explicitly impossible single-storey program -> INFEASIBLE_PROGRAM (rejection without fake plan).
"""

import os
import sys
import json
import pytest

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from requirements.parser import NaturalLanguageRequirementsParser
from generation.real_plan_analyzer import RealFloorPlanAnalyzer
from generation.quality_gate import FloorPlanQualityGate
from generation.validation import LayoutValidator
from pipeline_runner import run_generation_pipeline


class TestArchitecturalBenchmark:

    def test_01_five_marla_single_storey_3bed_2bath(self, tmp_path):
        """
        TEST 1:
        5 marla, 3 bedrooms, 2 bathrooms, master attached bathroom, single-storey.
        """
        prompt = "5 marla house with 3 bedrooms and 2 bathrooms, master bedroom attached bathroom, single-storey"
        out_dir = str(tmp_path / "test_1_output")
        plan = run_generation_pipeline(prompt, out_dir, render_3d=False)

        assert plan is not None, "TEST 1 must generate a valid plan"
        assert len(plan.metadata.levels) == 1, "Must be single-storey"
        assert plan.metadata.levels == [0]

        program = NaturalLanguageRequirementsParser.parse(prompt)
        assert program.is_feasible is True
        assert program.floor_count == 1
        assert program.is_single_storey_explicit is True

        # Evaluate Quality Gate
        gate = FloorPlanQualityGate.evaluate(plan, program)
        assert gate["final_status"] == "PASS", f"Quality gate failures: {gate['failures']}"
        assert gate["is_valid"] is True

        # Check room counts
        bed_count = sum(1 for r in plan.rooms if r.room_type == "bedroom")
        bath_count = sum(1 for r in plan.rooms if r.room_type == "bathroom")
        assert bed_count == 3, f"Expected 3 bedrooms, got {bed_count}"
        assert bath_count == 2, f"Expected 2 bathrooms, got {bath_count}"

        # Verify master suite attached bathroom door connectivity
        master_bed = next((r for r in plan.rooms if "master" in r.room_name.lower()), None)
        assert master_bed is not None, "Master bedroom must be designated"
        master_bath = next((r for r in plan.rooms if "master" in r.room_name.lower() and r.room_type == "bathroom"), None)
        assert master_bath is not None, "Master attached bathroom must exist"

        # Check connecting door
        doors = [op for op in plan.openings if op.opening_type == "door"]
        connecting_doors = [
            d for d in doors 
            if master_bed.room_id in d.connects_rooms and master_bath.room_id in d.connects_rooms
        ]
        assert len(connecting_doors) >= 1, "Must have physical door connecting master bedroom and master bathroom"

    def test_02_five_marla_4bed_4bath_powder_garage_lounge(self, tmp_path):
        """
        TEST 2:
        5 marla, 4 bedrooms, 4 attached bathrooms, powder room, garage, kitchen, dining, TV lounge.
        """
        prompt = "5 marla house with 4 bedrooms, 4 attached bathrooms, powder room, garage, kitchen, dining, and TV lounge"
        out_dir = str(tmp_path / "test_2_output")
        plan = run_generation_pipeline(prompt, out_dir, render_3d=False)

        assert plan is not None, "TEST 2 must generate a valid plan"
        program = NaturalLanguageRequirementsParser.parse(prompt)

        gate = FloorPlanQualityGate.evaluate(plan, program)
        assert gate["final_status"] == "PASS", f"Quality gate failures: {gate['failures']}"

        # Verify room program
        bed_count = sum(1 for r in plan.rooms if r.room_type == "bedroom")
        bath_count = sum(1 for r in plan.rooms if r.room_type == "bathroom")
        garage_exists = any(r.room_type == "garage" for r in plan.rooms)
        powder_exists = any("powder" in r.room_name.lower() for r in plan.rooms)

        assert bed_count == 4, f"Expected 4 bedrooms, got {bed_count}"
        assert bath_count >= 4, f"Expected at least 4 bathrooms, got {bath_count}"
        assert garage_exists is True, "Garage must be present"
        assert powder_exists is True, "Powder room must be present"

    def test_03_ten_marla_2storey_5bed_ensuite_drawing_dining_double_garage(self, tmp_path):
        """
        TEST 3:
        10 marla, 2 storey, 5 bedrooms, attached bathrooms, drawing, dining, kitchen, TV lounge, double garage.
        """
        prompt = "10 marla 2 storey house with 5 bedrooms, attached bathrooms, drawing room, dining room, kitchen, TV lounge, double garage"
        out_dir = str(tmp_path / "test_3_output")
        plan = run_generation_pipeline(prompt, out_dir, render_3d=False)

        assert plan is not None, "TEST 3 must generate a valid plan"
        assert len(plan.metadata.levels) == 2, "Must be 2 storeys"

        program = NaturalLanguageRequirementsParser.parse(prompt)
        gate = FloorPlanQualityGate.evaluate(plan, program)
        assert gate["final_status"] == "PASS", f"Quality gate failures: {gate['failures']}"

        # Verify bedrooms across 2 floors
        gf_beds = [r for r in plan.rooms if r.room_type == "bedroom" and r.level_index == 0]
        ff_beds = [r for r in plan.rooms if r.room_type == "bedroom" and r.level_index == 1]
        assert len(gf_beds) == 2, f"Expected 2 ground floor bedrooms, got {len(gf_beds)}"
        assert len(ff_beds) == 3, f"Expected 3 first floor bedrooms, got {len(ff_beds)}"
        assert len(gf_beds) + len(ff_beds) == 5

        # Check drawing and dining
        assert any("drawing" in r.room_name.lower() for r in plan.rooms)
        assert any("dining" in r.room_name.lower() for r in plan.rooms)

    def test_04_one_kanal_luxury_5bed_double_kitchen_courtyard(self, tmp_path):
        """
        TEST 4:
        1 kanal, 5 bedrooms, attached bathrooms, drawing, dining, double kitchen, courtyard, double garage.
        """
        prompt = "1 kanal luxury estate with 5 bedrooms, attached bathrooms, drawing room, dining room, double kitchen, courtyard, double garage"
        out_dir = str(tmp_path / "test_4_output")
        plan = run_generation_pipeline(prompt, out_dir, render_3d=False)

        assert plan is not None, "TEST 4 must generate a valid plan"
        program = NaturalLanguageRequirementsParser.parse(prompt)

        gate = FloorPlanQualityGate.evaluate(plan, program)
        assert gate["final_status"] == "PASS", f"Quality gate failures: {gate['failures']}"

        # Verify double kitchen (main kitchen + spice/dirty kitchen)
        kitchens = [r for r in plan.rooms if r.room_type == "kitchen"]
        assert len(kitchens) >= 2, f"Expected double kitchen (>= 2), got {len(kitchens)}"

        # Verify courtyard / open patio
        courtyards = [r for r in plan.rooms if "courtyard" in r.room_name.lower() or "patio" in r.room_name.lower()]
        assert len(courtyards) >= 1, "Courtyard/patio must exist"

    def test_05_explicitly_infeasible_single_storey_program(self, tmp_path):
        """
        TEST 5:
        Explicitly impossible single-storey program:
        5 marla, single-storey, 6 bedrooms, 6 bathrooms, drawing, dining, kitchen, garage.
        Expected: INFEASIBLE_PROGRAM (rejection without fake plan).
        """
        prompt = "5 marla single-storey house with 6 bedrooms and 6 attached bathrooms and drawing room and dining room and kitchen and garage"
        out_dir = str(tmp_path / "test_5_output")
        plan = run_generation_pipeline(prompt, out_dir, render_3d=False)

        # Plan MUST BE None (no fake plan generated)
        assert plan is None, "Infeasible program MUST NOT generate a fake plan!"

        # Quality report must exist and indicate INFEASIBLE_PROGRAM
        report_path = os.path.join(out_dir, "quality_report.json")
        assert os.path.exists(report_path), "quality_report.json must be recorded"

        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        assert report["final_status"] == "INFEASIBLE_PROGRAM"
        assert report["is_valid"] is False
        assert len(report["infeasibility_reasons"]) > 0
        assert any("building footprint limit" in r.lower() or "exceeds" in r.lower() for r in report["infeasibility_reasons"])
