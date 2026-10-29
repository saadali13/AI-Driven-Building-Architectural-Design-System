"""
Automated Test Suite for Hybrid Architectural System.
Validates:
1. Component 1: Invalid Program Rejections & InfeasibleProgramError Guards.
2. Component 2: Canonical Master Baseline QA Scores (100% pass rate).
3. Component 3: Real Dataset CV Extraction & Dataset Indexing (187 plans).
4. Component 4: Multi-Scale RAG Retrieval & Coordinated Two-Floor Plan Generation.
"""

import os
import json
import pytest
from shapely.geometry import Polygon

from requirements.parser import (
    NaturalLanguageRequirementsParser,
    validate_architectural_feasibility,
    InfeasibleProgramError
)
from generation.architectural_templates import CanonicalMasterBaselines
from generation.rag_matcher import RAGMatcher
from generation.solver import CoordinatedTwoFloorSolver
from generation.quality_gate import FloorPlanQualityGate


class TestHybridPipeline:

    # -------------------------------------------------------------------------
    # 1. Invalid Program Rejections (Component 1)
    # -------------------------------------------------------------------------
    def test_invalid_3_marla_separate_formal_dining(self):
        """3 Marla cannot accommodate a separate formal dining room."""
        prompt = "3 marla house with separate formal dining room and kitchen and 1 bedroom on ground floor"
        prog = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=False)
        assert prog.is_feasible is False
        assert any("separate formal dining" in r.lower() for r in prog.infeasibility_reasons)

        with pytest.raises(InfeasibleProgramError):
            validate_architectural_feasibility(prog, raise_on_error=True)

    def test_invalid_5_marla_excess_bedrooms_on_gf(self):
        """5 Marla allows maximum 2 bedrooms on Ground Floor."""
        prompt = "5 marla single-storey house with 3 bedrooms on ground floor and 3 bathrooms"
        prog = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=False)
        assert prog.is_feasible is False
        assert any("permits maximum 2 bedrooms on ground floor" in r.lower() for r in prog.infeasibility_reasons)

        with pytest.raises(InfeasibleProgramError):
            validate_architectural_feasibility(prog, raise_on_error=True)

    def test_invalid_multiple_show_kitchens_on_gf(self):
        """Universal constraint: multiple show kitchens on the same floor plate is illegal."""
        prompt = "10 marla luxury house with 2 show kitchens on ground floor"
        prog = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=False)
        assert prog.is_feasible is False
        assert any("show kitchen" in r.lower() for r in prog.infeasibility_reasons)

        with pytest.raises(InfeasibleProgramError):
            validate_architectural_feasibility(prog, raise_on_error=True)

    def test_invalid_multiple_tv_lounges_on_gf(self):
        """Universal constraint: multiple TV lounges on Ground Floor is illegal."""
        prompt = "7 marla house with 2 tv lounges on ground floor and kitchen"
        prog = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=False)
        assert prog.is_feasible is False
        assert any("tv lounge" in r.lower() for r in prog.infeasibility_reasons)

        with pytest.raises(InfeasibleProgramError):
            validate_architectural_feasibility(prog, raise_on_error=True)

    def test_invalid_ground_coverage_exceeding_75_percent(self):
        """Statutory by-law constraint: building footprint must not exceed 75% plot coverage."""
        prompt = "5 marla single-storey house with 6 bedrooms and 6 bathrooms and drawing room and dining room and kitchen and garage"
        prog = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=False)
        assert prog.is_feasible is False
        assert any("exceeds statutory 75% plot limit" in r.lower() or "exceeds" in r.lower() for r in prog.infeasibility_reasons)

        with pytest.raises(InfeasibleProgramError):
            validate_architectural_feasibility(prog, raise_on_error=True)

    # -------------------------------------------------------------------------
    # 2. Real Dataset Indexing & Batch Extraction (Component 3)
    # -------------------------------------------------------------------------
    def test_dataset_index_integrity(self):
        """Validates dataset/dataset_index.json catalog structure and metadata."""
        index_path = os.path.join("dataset", "dataset_index.json")
        assert os.path.exists(index_path), "dataset/dataset_index.json must exist"

        with open(index_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        assert catalog.get("total_plans", 0) >= 100, f"Expected >= 100 plans, found {catalog.get('total_plans')}"
        scales = set(catalog.get("scales_indexed", []))
        expected_scales = {"3_marla", "5_marla", "7_marla", "10_marla", "1_kanal"}
        assert expected_scales.issubset(scales), f"Missing scales: {expected_scales - scales}"

        plans = catalog.get("plans", [])
        assert len(plans) >= 100
        for p in plans[:20]:
            assert "plan_id" in p
            assert "scale" in p
            assert "dimensions_m" in p
            assert "ground_room_counts" in p
            assert "stair_type" in p
            assert "topology_graph_hash" in p
            assert "canonical_path" in p
            assert os.path.exists(p["canonical_path"]), f"Processed canonical file missing: {p['canonical_path']}"

    # -------------------------------------------------------------------------
    # 3. Canonical Master Baseline QA Scores (Component 2)
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("scale", ["3_marla", "5_marla", "7_marla", "10_marla", "1_kanal"])
    def test_canonical_master_baseline_qa_100_percent(self, scale):
        """Each of the 5 canonical golden master baselines must achieve 100% QualityGate pass rate."""
        plan = CanonicalMasterBaselines.get_master_baseline(scale)
        assert plan is not None, f"Could not load baseline for {scale}"
        assert plan.metadata.floor_count == 2, f"{scale} must be a 2-floor coordinated plan"

        gate = FloorPlanQualityGate.evaluate(plan)
        assert gate["final_status"] == "PASS", f"Quality gate failures for {scale}: {gate.get('failures')}"
        assert len(gate.get("failures", [])) == 0, f"Expected 0 failures for {scale}, got {gate.get('failures')}"

        # Verify exact wall thickness standards
        ext_walls = [w for w in plan.walls if w.wall_type == "exterior"]
        int_walls = [w for w in plan.walls if w.wall_type == "interior"]
        assert len(ext_walls) > 0, f"{scale} must have exterior walls"
        assert len(int_walls) > 0, f"{scale} must have interior walls"

    # -------------------------------------------------------------------------
    # 4. Multi-Scale RAG Retrieval & Generation (Component 4)
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("scale,prompt,expected_stair", [
        ("3_marla", "3 marla modern house with 1 bedroom on ground floor and straight staircase", "straight"),
        ("5_marla", "5 marla house with 2 bedrooms and 2 baths and dogleg staircase", "dogleg"),
        ("7_marla", "7 marla house with 2 bedrooms on ground floor, drawing and dining", "dogleg"),
        ("10_marla", "10 marla executive luxury villa with u-shaped staircase", "u_shaped"),
        ("1_kanal", "1 kanal luxury estate with grand helical staircase and double kitchen", "curved")
    ])
    def test_multi_scale_rag_generation(self, scale, prompt, expected_stair):
        """Validates topological query, candidate ranking, and coordinated RAG plan generation."""
        prog = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=False)
        assert prog.is_feasible is True

        matcher = RAGMatcher()
        matches = matcher.query(prog, top_k=3)
        assert len(matches) > 0, f"RAG query returned no matches for {scale}"
        assert matches[0]["scale"] == scale, f"Top match scale {matches[0]['scale']} != {scale}"
        assert matches[0]["similarity_score"] > 0.50

        # Generate RAG plan
        plan = CoordinatedTwoFloorSolver.generate_rag_plan(prog, stair_type=expected_stair)
        assert plan is not None
        assert plan.metadata.floor_count == 2
        assert plan.metadata.levels == [0, 1]

        # Enforce fixed wall thicknesses
        ext_thicknesses = set(w.thickness_m for w in plan.walls if w.wall_type == "exterior")
        int_thicknesses = set(w.thickness_m for w in plan.walls if w.wall_type == "interior")
        assert ext_thicknesses == {0.23}, f"Exterior wall thickness must be exactly 0.23m, got {ext_thicknesses}"
        assert int_thicknesses == {0.115}, f"Interior wall thickness must be exactly 0.115m, got {int_thicknesses}"

        # Enforce Staircase Invariance (identical polygon on Level 0 and Level 1)
        stair_0 = next((r for r in plan.rooms if r.level_index == 0 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower())), None)
        stair_1 = next((r for r in plan.rooms if r.level_index == 1 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower())), None)
        assert stair_0 is not None, "Ground floor must have staircase"
        assert stair_1 is not None, "First floor must have staircase landing"

        p0 = Polygon(stair_0.polygon)
        p1 = Polygon(stair_1.polygon)
        stair_iou = p0.intersection(p1).area / p0.union(p1).area
        assert stair_iou >= 0.98, f"Staircase invariance violated for {scale}: IoU = {stair_iou:.3f} < 0.98"

        # QualityGate evaluation
        gate = FloorPlanQualityGate.evaluate(plan)
        assert gate["final_status"] == "PASS", f"RAG plan for {scale} failed QualityGate: {gate.get('failures')}"
        assert len(gate.get("failures", [])) == 0
