"""
tests/test_phase1_wiring.py
Phase 1 Verification & Wiring Test Suite for ArchiCraft AI.

Verifies:
1. DesignDiversityEngine is the primary generator (canonical_plan is present, fallback_used is False).
2. Multi-variant generation produces 3 distinct strategies for 3, 5, 7, 10 Marla and 1 Kanal.
3. QualityGate evaluates to PASS across all standard plot sizes.
4. RequirementsComplianceEngine evaluates requested vs delivered features.
5. Explainability metadata contains source archetype and influenced plans.
6. Versioned persistence stores output/{plan_id}/v1/plan.json.
"""

import os
import sys
import json
import pytest

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api_server import ProceduralArchitecturalEngine


PLOT_CONFIGS = [
    {
        "scale": "3_marla",
        "name": "3 Marla Compact",
        "prompt": "3 Marla modern house 20x34 with 3 bedrooms, drawing room, open kitchen, and car porch",
        "width": 20.0,
        "length": 34.0,
        "floors": 2,
        "beds": 3,
        "baths": 3
    },
    {
        "scale": "5_marla",
        "name": "5 Marla Urban",
        "prompt": "5 Marla modern house 25x45 with 4 bedrooms, drawing room, TV lounge, and car porch",
        "width": 25.0,
        "length": 45.0,
        "floors": 2,
        "beds": 4,
        "baths": 4
    },
    {
        "scale": "7_marla",
        "name": "7 Marla Duplex",
        "prompt": "7 Marla contemporary house 30x55 with 4 bedrooms, drawing room, TV lounge, and double porch",
        "width": 30.0,
        "length": 55.0,
        "floors": 2,
        "beds": 4,
        "baths": 4
    },
    {
        "scale": "10_marla",
        "name": "10 Marla Luxury Executive",
        "prompt": "10 marla, double story, 4 bedrooms with attached baths, drawing room, TV lounge, open kitchen, car porch, modern style",
        "width": 35.0,
        "length": 65.0,
        "floors": 2,
        "beds": 4,
        "baths": 4
    },
    {
        "scale": "1_kanal",
        "name": "1 Kanal Grand Estate",
        "prompt": "1 Kanal classical estate 50x90 with 5 bedrooms, drawing and dining, 2-car porch, and front lawn",
        "width": 50.0,
        "length": 90.0,
        "floors": 2,
        "beds": 5,
        "baths": 5
    }
]


def test_phase1_all_plot_sizes():
    """Tests all 5 Pakistani residential plot sizes through the primary engine."""
    results_table = []

    for cfg in PLOT_CONFIGS:
        res = ProceduralArchitecturalEngine.synthesize_design(
            prompt=cfg["prompt"],
            plot_width=cfg["width"],
            plot_length=cfg["length"],
            floors=cfg["floors"],
            bedrooms=cfg["beds"],
            bathrooms=cfg["baths"],
            style="modern",
            seed=1
        )

        has_canonical = res.get("canonical_plan") is not None
        fallback_used = res.get("fallback_used", True)
        qg_status = res.get("quality_gate", {}).get("status", "FAIL")
        strategy_used = res.get("explainability", {}).get("strategy_id", "unknown")
        variants = res.get("variants", [])

        # Assertions
        assert has_canonical, f"CanonicalFloorPlan must be present for {cfg['scale']}"
        assert not fallback_used, f"Fallback solver should NOT be used for {cfg['scale']}"
        assert qg_status == "PASS", f"Quality gate must pass for {cfg['scale']}"
        assert len(variants) == 3, f"Must generate 3 distinct variants for {cfg['scale']}"

        # Assert distinct strategies among the 3 variants
        variant_strategies = [v["strategy_id"] for v in variants]
        assert len(set(variant_strategies)) == 3, f"Variants must use 3 different strategies: {variant_strategies}"

        # Check compliance checklist
        compliance = res.get("compliance_checklist")
        assert compliance is not None, "Compliance checklist must be present"
        assert len(compliance.get("items", [])) >= 5, "Checklist must contain evaluated items"

        # Check explainability
        exp = res.get("explainability")
        assert exp is not None, "Explainability panel must be present"
        assert exp.get("source_archetype_id"), "Source archetype ID must be present"
        assert len(exp.get("bylaw_rules_applied", [])) > 0, "Bylaw rules must be documented"

        # Check plan.json persistence
        plan_id = res.get("project_id")
        persisted_path = os.path.join(PROJECT_ROOT, "output", plan_id, "v1", "plan.json")
        assert os.path.exists(persisted_path), f"Persisted plan.json not found at {persisted_path}"

        with open(persisted_path, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
            assert persisted_data.get("version") == 1
            assert persisted_data.get("canonical_plan") is not None
            assert persisted_data.get("compliance_checklist") is not None

        results_table.append({
            "plot_size": cfg["name"],
            "scale": cfg["scale"],
            "strategy": strategy_used,
            "canonical_present": has_canonical,
            "quality_gate": qg_status,
            "fallback_used": fallback_used,
            "compliance_score": f"{compliance.get('score_pct', 0)}%"
        })

    # Print summary table for inspection
    print("\n" + "=" * 90)
    print(f"{'Plot Size':<25} | {'Strategy Used':<28} | {'Canonical':<10} | {'QG':<6} | {'Fallback':<8} | {'Score'}")
    print("-" * 90)
    for row in results_table:
        print(f"{row['plot_size']:<25} | {row['strategy']:<28} | {str(row['canonical_present']):<10} | {row['quality_gate']:<6} | {str(row['fallback_used']):<8} | {row['compliance_score']}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    test_phase1_all_plot_sizes()

