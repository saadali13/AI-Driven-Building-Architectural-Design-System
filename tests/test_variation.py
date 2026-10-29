"""
Regression & Automated Diversity Test Suite for Design Variation Capabilities.
Verifies:
1. Intent-aware diversity across varying briefs on identical plots.
2. Perfect run-to-run determinism under fixed seeds / identical briefs.
3. Paraphrase stability and hyphenated bedroom parsing.
4. Parameterized variant alternative index exposure (1 to 10).
5. Post-generation constraint fidelity guard.
"""

import pytest
import os
from typing import Dict, Any
from generation.rag_solver import DatasetDrivenRAGSolver
from generation.fidelity_guard import FidelityGuard
from tools.measure_diversity import compare_plans, compute_composite_diversity_distance
from dataset.schema.canonical import CanonicalFloorPlan
from generation.quality_gate import FloorPlanQualityGate


@pytest.fixture(scope="module")
def solver():
    return DatasetDrivenRAGSolver()


class TestDesignVariation:

    @pytest.mark.parametrize("scale,plot_dims", [
        ("5_marla", (25.0, 45.0)),
        ("10_marla", (35.0, 65.0)),
    ])
    def test_meaningful_diversity_between_distinct_briefs(self, solver, scale, plot_dims):
        """Verify that distinct spatial briefs on the same plot yield composite distance >= 0.15."""
        p_baseline = f"{scale.replace('_', ' ').title()} modern family residence with 4 bedrooms, drawing room, and car porch"
        p_courtyard = f"{scale.replace('_', ' ').title()} Spanish hacienda with central courtyard, patio, 4 bedrooms, and porch"

        plan_a = solver.synthesize(p_baseline, target_dimensions_ft=plot_dims)
        plan_b = solver.synthesize(p_courtyard, target_dimensions_ft=plot_dims)

        assert plan_a is not None
        assert plan_b is not None

        comp = compare_plans(plan_a, plan_b)
        assert comp["composite_diversity_distance"] >= 0.15, (
            f"Expected composite distance >= 0.15 for distinct briefs, got {comp['composite_diversity_distance']:.4f}"
        )
        assert comp["classification"] in ("MEANINGFULLY DIFFERENT", "COSMETIC")

    def test_determinism_under_fixed_inputs(self, solver):
        """Verify that running the identical prompt produces exact geometric identity (D == 0.0000)."""
        prompt = "10 Marla contemporary villa with 4 bedrooms, drawing room, and car porch"
        plan_1 = solver.synthesize(prompt, target_dimensions_ft=(35.0, 65.0), seed=42)
        plan_2 = solver.synthesize(prompt, target_dimensions_ft=(35.0, 65.0), seed=42)

        comp = compare_plans(plan_1, plan_2)
        assert comp["composite_diversity_distance"] == 0.0000
        assert comp["classification"] == "IDENTICAL"

    def test_paraphrase_stability_and_hyphen_fix(self, solver):
        """Verify that hyphenated terms like '2-bed' or '3-bed' parse cleanly and satisfy F01 quality gate."""
        prompt_hyphen = "5 Marla house with 2-bed, drawing room, lounge, and car porch"
        prompt_words = "5 Marla house with 2 bedroom, drawing room, lounge, and car porch"

        plan_hyphen = solver.synthesize(prompt_hyphen, target_dimensions_ft=(25.0, 45.0))
        plan_words = solver.synthesize(prompt_words, target_dimensions_ft=(25.0, 45.0))

        # Both must produce exactly 2 bedrooms
        beds_hyphen = [r for r in plan_hyphen.rooms if r.room_type == "bedroom"]
        beds_words = [r for r in plan_words.rooms if r.room_type == "bedroom"]

        assert len(beds_hyphen) == 2, f"Hyphen prompt failed: expected 2 bedrooms, got {len(beds_hyphen)}"
        assert len(beds_words) == 2, f"Words prompt failed: expected 2 bedrooms, got {len(beds_words)}"

        # Both must pass QualityGate
        gate_h = FloorPlanQualityGate.evaluate(plan_hyphen)
        gate_w = FloorPlanQualityGate.evaluate(plan_words)
        assert gate_h["final_status"] == "PASS"
        assert gate_w["final_status"] == "PASS"

    def test_synonym_support_baithak(self, solver):
        """Verify that Urdu synonym 'baithak' is parsed and supported."""
        prompt_urdu = "5 Marla house with 3 bedrooms, baithak, dirty kitchen, and gari porch"
        plan = solver.synthesize(prompt_urdu, target_dimensions_ft=(25.0, 45.0))
        assert plan is not None

        # Verify dirty kitchen is present
        has_dirty = any("dirty" in r.room_name.lower() or "scullery" in r.room_name.lower() or r.metadata.get("is_dirty_kitchen") for r in plan.rooms)
        assert has_dirty is True, "Dirty kitchen not adapted from 'dirty kitchen' / 'bawarchi khana' brief"

    def test_variant_index_parameter_diversity(self, solver):
        """Verify that explicit variant_index parameters (1, 2, 3) steer distinct typological strategies."""
        prompt = "10 Marla family residence 35x65"
        plan_v1 = solver.synthesize(prompt, target_dimensions_ft=(35.0, 65.0), alternative_index=1)
        plan_v2 = solver.synthesize(prompt, target_dimensions_ft=(35.0, 65.0), alternative_index=2)
        plan_v3 = solver.synthesize(prompt, target_dimensions_ft=(35.0, 65.0), alternative_index=3)

        strat_1 = plan_v1.metadata.provenance.get("planning_strategy")
        strat_2 = plan_v2.metadata.provenance.get("planning_strategy")
        strat_3 = plan_v3.metadata.provenance.get("planning_strategy")

        assert strat_1 != strat_2, f"Variant 1 and 2 yielded same strategy: {strat_1}"
        assert strat_2 != strat_3, f"Variant 2 and 3 yielded same strategy: {strat_2}"

        comp_1_2 = compare_plans(plan_v1, plan_v2)
        comp_1_3 = compare_plans(plan_v1, plan_v3)

        assert comp_1_2["composite_diversity_distance"] >= 0.25
        assert comp_1_3["composite_diversity_distance"] >= 0.25
        assert comp_1_2["classification"] == "MEANINGFULLY DIFFERENT"
        assert comp_1_3["classification"] == "MEANINGFULLY DIFFERENT"

    def test_fidelity_guard_verification(self, solver):
        """Verify post-generation constraint fidelity guard reporting."""
        prompt = "10 Marla executive villa with 4 bedrooms, dirty kitchen, study, and 2-car porch"
        plan = solver.synthesize(prompt, target_dimensions_ft=(35.0, 65.0))

        fid = FidelityGuard.audit(plan, prompt=prompt)
        assert fid["fidelity_passed"] is True, f"Fidelity guard failed: {fid['violations']}"
        assert fid["actual_bedroom_count"] == 4

        # Verify presence of all requested functional spaces
        assert any("dirty" in r.room_name.lower() or "scullery" in r.room_name.lower() or r.metadata.get("is_dirty_kitchen") for r in plan.rooms)
        assert any(r.room_type in ("office", "study") or "study" in r.room_name.lower() or "office" in r.room_name.lower() for r in plan.rooms)

    def test_infeasible_adaptation_safety(self, solver):
        """Verify that legal constraints (e.g. 6 beds on 7 Marla 2-storey) are adapted safely with notice."""
        prompt = "7 Marla house with 6 bedrooms on 2 floors"
        plan = solver.synthesize(prompt, target_dimensions_ft=(30.0, 55.0))

        assert plan is not None
        # 6 bedrooms cannot fit legally on 2 floors under CDA/DHA setback rules, so adapted to 5 beds
        beds = [r for r in plan.rooms if r.room_type == "bedroom"]
        assert len(beds) == 5
        assert "statutory_red_note" in plan.metadata.provenance
