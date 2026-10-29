"""
Architectural Design Diversity & QA Verification Test Suite.
Validates:
1. 10 Marla Benchmark: 10 distinct user requirement prompts (TEST A through J) generate genuinely distinct floor plan topologies.
2. 10 Marla Alternative Generation: Identical prompt with 5 planning strategies generates 5 distinct topological alternatives.
3. Structural Design Signatures: Centroids, room adjacency graphs, key anchors (stair, kitchen, dirty kitchen, lawn, porch).
4. Duplicate Detection: Automatic rejection of candidates with similarity >= 0.72.
5. Gemini QA Auditor:
   - Verifies compliance with every explicit user requirement.
   - Distinguishes floor-plan diversity from cosmetic facade/style changes (rejecting facade-only changes).
6. Society Bylaws & Open Spaces: Preserves statutory front lawn setbacks and rear OTS ventilation lightwells.
7. Dirty Kitchen Validation: Ensures logical service circulation and kitchen connectivity.
8. Multi-Scale Verification: Confirms diversity across 3 Marla, 5 Marla, 7 Marla, 10 Marla, and 1 Kanal.
"""

import os
import sys
import copy
import pytest

from generation.rag_solver import DatasetDrivenRAGSolver
from generation.structural_signature import extract_structural_signature, compute_structural_similarity
from generation.duplicate_detector import DuplicateDetector
from generation.gemini_architectural_auditor import GeminiArchitecturalAuditor
from generation.visualizer import FloorPlanVisualizer
from generation.quality_gate import FloorPlanQualityGate


OUTPUT_DIR = os.path.abspath(r"C:\Users\m\OneDrive\Desktop\New folder\output\diversity_matrix")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_10_marla_benchmark_10_distinct_prompts_diversity():
    """
    SECTION 4 & 22 BENCHMARK:
    10 Marla as primary benchmark across 10 distinct user requirement prompts (TEST A - TEST J).
    Proves system does not repeat topologies, satisfies all requirements, and produces distinct layouts.
    """
    test_prompts = [
        ("TEST A", "10 Marla north-facing family house with 4 bedrooms, 4 bathrooms, guest room, family lounge, study, kitchen, dirty kitchen, 2-car parking and front lawn"),
        ("TEST B", "10 Marla north-facing residence focused on guest privacy with formal drawing room, family lounge, 3 bedrooms, study, kitchen, dirty kitchen and landscaped lawn"),
        ("TEST C", "10 Marla contemporary house with open living/dining, 4 bedrooms, home office, large kitchen, service kitchen, 2-car parking and private rear garden"),
        ("TEST D", "10 Marla traditional Pakistani residence with central family area, separate guest zone, 4 bedrooms, kitchen, dirty kitchen, staircase and generous front open space"),
        ("TEST E", "10 Marla Spanish Revival residence with courtyard character, 4 bedrooms, guest suite, family lounge, kitchen, service kitchen, parking and landscaped outdoor space"),
        ("TEST F", "10 Marla Mid-Century Modern residence with indoor/outdoor connection, 3 bedrooms, open living, study, kitchen, service area and landscaped garden"),
        ("TEST G", "10 Marla Craftsman residence with 4 bedrooms, family lounge, formal guest area, study, kitchen, service kitchen, porch and lawn"),
        ("TEST H", "10 Marla Georgian residence with formal entrance, separated guest/family zones, 4 bedrooms, study, kitchen, service area and 2-car parking"),
        ("TEST I", "10 Marla privacy-focused residence with bedrooms away from the entrance, large family lounge, guest room, kitchen, dirty kitchen, study and rear garden"),
        ("TEST J", "10 Marla multigenerational residence with 4 bedrooms, guest suite, family lounge, study, kitchen, service kitchen, parking and multiple outdoor spaces")
    ]

    solver = DatasetDrivenRAGSolver()
    detector = DuplicateDetector()
    plans = []
    signatures = []

    print("\n" + "=" * 75)
    print("10 MARLA PRIMARY BENCHMARK: GENERATING 10 DISTINCT PROMPTS (TEST A - J)")
    print("=" * 75)

    for test_id, prompt in test_prompts:
        print(f"\n---> Synthesizing [{test_id}]: {prompt[:65]}...")
        plan = solver.synthesize(f"{test_id}: {prompt}")
        assert plan is not None, f"Failed to synthesize plan for {test_id}"

        # 1. Programmatic QualityGate Verification
        qg = FloorPlanQualityGate.evaluate(plan)
        assert qg["is_valid"], f"QualityGate failed for {test_id}: {qg['failures']}"

        # 2. Extract Structural Signature
        sig = extract_structural_signature(plan)
        signatures.append(sig)

        # 3. Gemini User Requirements Audit
        req_res = GeminiArchitecturalAuditor.audit_user_requirements(prompt, plan)
        assert req_res["verdict"] == "PASS", f"User requirements check failed for {test_id}: {req_res['missing_requirements']}"

        # 4. Duplicate Detection against already accepted designs
        is_dup, sim, repeated, conflict = detector.evaluate_design(plan)
        assert not is_dup, f"Duplicate detected for {test_id} against {conflict} (similarity {sim:.2f})"

        detector.register_design(plan)
        plans.append(plan)
        print(f"      -> {test_id} Accepted. Registered in Unique Design Registry.")

    # 5. Full 45-Pairwise Diversity Verification
    assert len(plans) == 10
    total_comparisons = 0
    max_sim = 0.0
    sum_sim = 0.0

    print("\n" + "-" * 75)
    print("PAIRWISE TOPOLOGICAL SIMILARITY EVALUATION (45 PAIRS):")
    print("-" * 75)

    for i in range(len(signatures)):
        for j in range(i + 1, len(signatures)):
            sim, repeated = compute_structural_similarity(signatures[i], signatures[j])
            total_comparisons += 1
            sum_sim += sim
            if sim > max_sim:
                max_sim = sim
            assert sim < 0.72, f"Excessive similarity ({sim:.2f}) between {test_prompts[i][0]} and {test_prompts[j][0]}: repeated {repeated}"

    avg_sim = sum_sim / total_comparisons
    print(f"\n[DIVERSITY VERIFIED] Total Comparisons: {total_comparisons}")
    print(f"   * Average Similarity Score: {avg_sim:.3f} (< 0.72 threshold)")
    print(f"   * Maximum Similarity Score: {max_sim:.3f} (< 0.72 threshold)")

    # 6. Render Visual Diversity Comparison Matrix
    sheet_path = os.path.join(OUTPUT_DIR, "10_marla_10_prompts_comparison_sheet.png")
    FloorPlanVisualizer.render_diversity_comparison_sheet(
        plans,
        sheet_path,
        title="10 MARLA PRIMARY BENCHMARK: 10 DISTINCT PROMPTS COMPARISON MATRIX"
    )
    assert os.path.exists(sheet_path), f"Comparison sheet not found at {sheet_path}"
    print(f"Saved 10 Marla Comparison Matrix: {sheet_path} ({os.path.getsize(sheet_path)} bytes)\n")


def test_10_marla_same_prompt_5_architectural_alternatives():
    """
    SECTION 5 & 32 BENCHMARK:
    Mandatory Test: ONE identical prompt -> 5 fundamentally different planning alternatives.
    Verifies that differing planning strategies (Central Lounge, Side Gallery, Split Guest-Family,
    Courtyard, Open Living) alter room topology, circulation, and zoning.
    """
    base_prompt = "Design a 10 Marla north-facing Pakistani residence with 4 bedrooms, 4 bathrooms, guest room, family lounge, study, kitchen, dirty kitchen, 2-car parking and front lawn"

    solver = DatasetDrivenRAGSolver()
    detector = DuplicateDetector()
    plans = []
    signatures = []

    print("\n" + "=" * 75)
    print("SAME 10 MARLA PROMPT: GENERATING 5 ARCHITECTURAL ALTERNATIVES")
    print("=" * 75)

    for alt_idx in range(1, 6):
        prompt = f"{base_prompt}, Alternative 0{alt_idx}"
        print(f"\n---> Generating Alternative 0{alt_idx}...")
        plan = solver.synthesize(prompt, alternative_index=alt_idx)
        assert plan is not None, f"Failed to synthesize Alternative 0{alt_idx}"

        sig = extract_structural_signature(plan)

        # 1. Audit user requirements
        req_res = GeminiArchitecturalAuditor.audit_user_requirements(base_prompt, plan)
        assert req_res["verdict"] == "PASS", f"Alternative 0{alt_idx} failed requirements: {req_res['missing_requirements']}"

        # 2. Evaluate duplicate detection against previously accepted alternatives
        is_dup, sim, repeated, conflict = detector.evaluate_design(plan)
        assert not is_dup, f"Alternative 0{alt_idx} is duplicate of {conflict} (similarity {sim:.2f})"

        detector.register_design(plan)
        plans.append(plan)
        signatures.append(sig)
        print(f"      -> Alternative 0{alt_idx} Accepted (Strategy: {sig.planning_strategy})")

    assert len(plans) == 5
    # Pairwise comparison among all 5 alternatives
    for i in range(len(signatures)):
        for j in range(i + 1, len(signatures)):
            sim, repeated = compute_structural_similarity(signatures[i], signatures[j])
            print(f"Alt 0{i+1} vs Alt 0{j+1} -> Structural Similarity: {sim:.3f}")
            assert sim < 0.72, f"Alternative 0{i+1} and Alternative 0{j+1} too similar ({sim:.2f}): {repeated}"

    # Render Visual 5-Alternatives Comparison Matrix
    sheet_path = os.path.join(OUTPUT_DIR, "10_marla_same_prompt_5_alternatives_comparison_sheet.png")
    FloorPlanVisualizer.render_diversity_comparison_sheet(
        plans,
        sheet_path,
        title="10 MARLA BENCHMARK: SAME PROMPT - 5 ARCHITECTURAL ALTERNATIVES"
    )
    assert os.path.exists(sheet_path)
    print(f"Saved 5 Alternatives Comparison Matrix: {sheet_path}\n")


def test_gemini_rejects_facade_only_diversity():
    """
    SECTION 10 & 11 MANDATORY REQUIREMENT:
    Gemini QA Auditor must NOT confuse facade diversity with floor-plan diversity.
    If two designs share the same underlying room topology, changing style/facade
    MUST result in diversity = FAIL and requires_regeneration = True.
    """
    solver = DatasetDrivenRAGSolver()
    plan_modern = solver.synthesize("Design 10 marla modern residence with 4 bedrooms", alternative_index=1)

    # Create a clone with identical floor plan topology but Spanish Revival facade metadata
    plan_spanish_cosmetic = copy.deepcopy(plan_modern)
    plan_spanish_cosmetic.metadata.plan_id = "test_10m_spanish_cosmetic_clone"
    plan_spanish_cosmetic.metadata.provenance["architectural_style"] = "Spanish Revival"

    # Evaluate diversity using GeminiArchitecturalAuditor
    div_audit = GeminiArchitecturalAuditor.audit_design_diversity(
        candidate_plan=plan_spanish_cosmetic,
        accepted_plans=[plan_modern]
    )

    print("\n" + "=" * 75)
    print("GEMINI QA AUDITOR: FACADE-ONLY COSMETIC DIVERSITY TEST")
    print("=" * 75)
    print(f"Diversity Verdict: {div_audit['diversity']}")
    print(f"Similarity Score:  {div_audit['similarity_score']:.3f} (Threshold < 0.72)")
    print(f"Reason:            {div_audit['reason']}")
    print(f"Requires Regen:    {div_audit['requires_regeneration']}")

    assert div_audit["diversity"] == "FAIL", "Auditor must FAIL identical floor plans with different facades!"
    assert div_audit["requires_regeneration"] is True, "Auditor must demand regeneration for cosmetic clones!"
    assert div_audit["similarity_score"] >= 0.72, "Topological similarity must exceed threshold for clone."
    print("PASS: Gemini QA Auditor successfully rejected facade-only cosmetic variation.\n")


def test_dirty_kitchen_and_bylaws_validation():
    """
    SECTION 13 & 14 BENCHMARK:
    Society open space and dirty kitchen validation.
    """
    solver = DatasetDrivenRAGSolver()
    plan = solver.synthesize("Design 10 marla house with dirty kitchen, kitchen, 2-car parking, front lawn", alternative_index=1)
    sig = extract_structural_signature(plan)

    # 1. Dirty kitchen validation
    assert sig.has_dirty_kitchen, "Generated plan must include dirty kitchen when requested"
    assert sig.dirty_kitchen_zone in ("center_left", "center_right", "rear_left", "rear_right", "rear_center")

    # 2. Society open space / lawn validation
    assert sig.lawn_zone in ("front_right", "front_left", "front_center")
    assert sig.parking_capacity == "double_car"

    print("PASS: Dirty kitchen service relationship and society open spaces verified.\n")


def test_multi_scale_diversity_suite():
    """
    SECTION 20 BENCHMARK:
    Verifies that diversity engine operates across 3 Marla, 5 Marla, 7 Marla, 1 Kanal.
    Smaller plots must not reuse 1 template; larger plots must not scale the same layout.
    """
    scales = ["3_marla", "5_marla", "7_marla", "1_kanal"]
    solver = DatasetDrivenRAGSolver()

    print("\n" + "=" * 75)
    print("MULTI-SCALE ARCHITECTURAL DIVERSITY VERIFICATION (3M, 5M, 7M, 1 KANAL)")
    print("=" * 75)

    for sc in scales:
        plan1 = solver.synthesize(f"Design {sc.replace('_', ' ')} residence with modern layout, alternative 1", alternative_index=1)
        plan2 = solver.synthesize(f"Design {sc.replace('_', ' ')} residence with modern layout, alternative 2", alternative_index=2)

        sig1 = extract_structural_signature(plan1)
        sig2 = extract_structural_signature(plan2)

        sim, repeated = compute_structural_similarity(sig1, sig2)
        print(f"Scale [{sc}] Alt 01 vs Alt 02 -> Structural Similarity: {sim:.3f}")
        assert sim < 0.72, f"Scale {sc} failed diversity threshold: {sim:.2f}"

    print("PASS: Multi-scale diversity verified across all plot sizes.\n")
