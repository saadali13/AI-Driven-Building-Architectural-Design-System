"""
Multi-Plot + Multi-Requirement + Design Diversity Benchmark Test Suite.
Validates the complete 35-design matrix across all Pakistani residential plot sizes:
- 3 Marla: 5 designs (3M-01 through 3M-05)
- 5 Marla: 5 designs (5M-01 through 5M-05)
- 7 Marla: 5 designs (7M-01 through 7M-05)
- 10 Marla: 10 designs (10M-01 through 10M-10) [Primary Diversity Benchmark]
- 1 Kanal: 10 designs (1K-01 through 1K-10)

For each plot size, verifies:
1. Programmatic validation (FloorPlanQualityGate 1.00)
2. Structural design signature extraction (centroids, graph, anchors)
3. Automatic duplicate rejection (similarity < 0.72 threshold)
4. Gemini architectural requirement compliance audit (PASS)
5. Dirty kitchen / service zone logic
6. Statutory society bylaws & open-space preservation
7. Renders side-by-side visual comparison matrix sheets
8. Emits comprehensive machine-readable multi_plot_diversity_report.json
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath("."))

from generation.rag_solver import DatasetDrivenRAGSolver
from generation.structural_signature import extract_structural_signature, compute_structural_similarity
from generation.duplicate_detector import DuplicateDetector
from generation.gemini_architectural_auditor import GeminiArchitecturalAuditor
from generation.visualizer import FloorPlanVisualizer
from generation.quality_gate import FloorPlanQualityGate

OUTPUT_DIR = os.path.abspath(r"C:\Users\m\OneDrive\Desktop\New folder\output\diversity_matrix")
os.makedirs(OUTPUT_DIR, exist_ok=True)


PROMPTS_3M = [
    ("3M-01", "3M-01: Design a compact Pakistani 3 Marla ground-floor house for a small family with 2 bedrooms, 2 bathrooms, family living/lounge, kitchen, staircase, small car parking and a usable front open area."),
    ("3M-02", "3M-02: Design a 3 Marla Pakistani house prioritizing privacy between guest and family spaces, with 2 bedrooms, 2 bathrooms, a guest sitting area, family lounge, kitchen and staircase."),
    ("3M-03", "3M-03: Design a modern 3 Marla Pakistani house with an open family living and dining concept, 2 bedrooms, 2 bathrooms, kitchen, staircase and compact parking."),
    ("3M-04", "3M-04: Design a traditional Pakistani 3 Marla house with a separate guest area, family lounge, bedrooms, kitchen, bathrooms, staircase and practical service circulation."),
    ("3M-05", "3M-05: Design a 3 Marla Pakistani house for a family that needs 2 bedrooms, 2 bathrooms, family lounge, kitchen, staircase, parking and a small dedicated study/work area.")
]

PROMPTS_5M = [
    ("5M-01", "5M-01: Design a Pakistani 5 Marla family house with 3 bedrooms, attached bathrooms where practical, family lounge, kitchen, dirty kitchen/service area, staircase, parking and front open space."),
    ("5M-02", "5M-02: Design a 5 Marla Pakistani house where the guest sitting area is visually and functionally separated from the private family zone, with 3 bedrooms, bathrooms, kitchen, staircase and parking."),
    ("5M-03", "5M-03: Design a contemporary 5 Marla house with an open living/dining/family concept, 3 bedrooms, bathrooms, kitchen, dirty kitchen, staircase and practical parking."),
    ("5M-04", "5M-04: Design a 5 Marla Pakistani house using a small courtyard or lightwell strategy to improve daylight and ventilation while maintaining 3 bedrooms, bathrooms, kitchen, staircase and parking."),
    ("5M-05", "5M-05: Design a 5 Marla house for a multigenerational family requiring 3 bedrooms, family lounge, guest room/sitting, kitchen, dirty kitchen, bathrooms, staircase and strong privacy between zones.")
]

PROMPTS_7M = [
    ("7M-01", "7M-01: Design a Pakistani 7 Marla house for a larger family with 4 bedrooms, bathrooms, family lounge, guest sitting, kitchen, dirty kitchen, staircase, parking and lawn/open space."),
    ("7M-02", "7M-02: Design a 7 Marla house with clearly separated guest, family, private bedroom and service zones, with 4 bedrooms, bathrooms, kitchen, dirty kitchen and staircase."),
    ("7M-03", "7M-03: Design a 7 Marla Pakistani house organized around a central family lounge, with 4 bedrooms, bathrooms, guest area, kitchen, dirty kitchen, staircase and parking."),
    ("7M-04", "7M-04: Design a 7 Marla house using a courtyard/lightwell as an important planning element for daylight, ventilation and family interaction, while providing 4 bedrooms, bathrooms, kitchen and service spaces."),
    ("7M-05", "7M-05: Design a contemporary Pakistani 7 Marla villa with 4 bedrooms, spacious family living, guest sitting, kitchen, dirty kitchen, staircase, parking and landscaped open space.")
]

PROMPTS_10M = [
    ("10M-01", "10M-01: 10 Marla compact efficient family residence with 4 bedrooms, family lounge, kitchen, dirty kitchen, bathrooms, staircase, parking and lawn"),
    ("10M-02", "10M-02: 10 Marla guest privacy focused residence with separate guest zone from family/private areas, 4 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("10M-03", "10M-03: 10 Marla residence organized around a central family lounge, with 4 bedrooms, kitchen, dirty kitchen, staircase, parking and lawn"),
    ("10M-04", "10M-04: 10 Marla residence using a courtyard/lightwell as part of spatial organization, with 4 bedrooms, family lounge, kitchen, dirty kitchen, parking and lawn"),
    ("10M-05", "10M-05: 10 Marla open contemporary residence with open living/dining/family arrangement, 4 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("10M-06", "10M-06: 10 Marla traditional Pakistani residence with compartmentalized rooms, guest sitting, family zone, service zone, 4 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("10M-07", "10M-07: 10 Marla residence including dedicated study/home office, 4 bedrooms, family lounge, kitchen, dirty kitchen, parking and lawn"),
    ("10M-08", "10M-08: 10 Marla multigenerational residence for parents + children with strong privacy and functional zoning, 4 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("10M-09", "10M-09: 10 Marla residence prioritizing lawn, landscaping, natural light and outdoor living, 4 bedrooms, kitchen, dirty kitchen, parking and generous lawn"),
    ("10M-10", "10M-10: 10 Marla service-oriented residence with strong kitchen to dirty kitchen to service/rear utility relationship, 4 bedrooms, parking and lawn")
]

PROMPTS_1K = [
    ("1K-01", "1K-01: 1 Kanal large family residence with multiple bedrooms, spacious family circulation, kitchen, dirty kitchen, parking and lawn"),
    ("1K-02", "1K-02: 1 Kanal luxury residence with strong separation between formal guest spaces and private family spaces, 5 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("1K-03", "1K-03: 1 Kanal courtyard residence using one or more courtyards/lightwells as meaningful architectural elements, 5 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("1K-04", "1K-04: 1 Kanal residence organized around a central family lounge with bedrooms organized around it, kitchen, dirty kitchen, parking and lawn"),
    ("1K-05", "1K-05: 1 Kanal villa-style zoning with landscaped open spaces, strong indoor/outdoor relationships, 5 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("1K-06", "1K-06: 1 Kanal multigenerational residence with independent zones for different generations, 5 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("1K-07", "1K-07: 1 Kanal contemporary open plan residence with large living/dining/family spaces, modern circulation, 5 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("1K-08", "1K-08: 1 Kanal traditional Pakistani residence with formal guest area, family zone, private bedrooms, service zone, kitchen, dirty kitchen, parking and lawn"),
    ("1K-09", "1K-09: 1 Kanal residence with multiple study/work spaces integrated into the residential plan, 5 bedrooms, kitchen, dirty kitchen, parking and lawn"),
    ("1K-10", "1K-10: 1 Kanal luxury service-oriented residence with large kitchen, dirty kitchen, pantry/store, laundry/service zone, parking and lawn")
]


def _execute_scale_diversity_benchmark(scale_name: str, prompts: list, sheet_filename: str):
    solver = DatasetDrivenRAGSolver()
    detector = DuplicateDetector()
    plans = []
    signatures = []

    print(f"\n{'=' * 75}\nBENCHMARKING SCALE: {scale_name.upper()} ({len(prompts)} DISTINCT PROMPTS)\n{'=' * 75}")

    for code, prompt in prompts:
        print(f"---> Synthesizing [{code}]: {prompt[:65]}...")
        plan = solver.synthesize(prompt)
        assert plan is not None, f"Failed synthesis for {code}"

        # 1. QualityGate verification
        qg = FloorPlanQualityGate.evaluate(plan)
        assert qg["is_valid"], f"QualityGate failed for {code}: {qg['failures']}"

        # 2. Extract Structural Signature
        sig = extract_structural_signature(plan)
        signatures.append(sig)

        # 3. Gemini User Requirements Audit
        req_res = GeminiArchitecturalAuditor.audit_user_requirements(prompt, plan)
        assert req_res["verdict"] == "PASS", f"Requirements failed for {code}: {req_res['missing_requirements']}"

        # 4. Duplicate Detection
        is_dup, sim, repeated, conflict = detector.evaluate_design(plan)
        assert not is_dup, f"Duplicate detected for {code} against {conflict} (similarity {sim:.2f})"

        detector.register_design(plan)
        plans.append(plan)
        print(f"      -> [{code}] ACCEPTED. Strategy: {sig.planning_strategy}, Rooms: {sig.room_count}")

    # Pairwise diversity evaluation
    n = len(signatures)
    comparisons = 0
    sum_sim = 0.0
    max_sim = 0.0

    for i in range(n):
        for j in range(i + 1, n):
            sim, repeated = compute_structural_similarity(signatures[i], signatures[j])
            comparisons += 1
            sum_sim += sim
            if sim > max_sim:
                max_sim = sim
            assert sim < 0.72, f"Excessive similarity ({sim:.2f}) between {prompts[i][0]} and {prompts[j][0]}: repeated {repeated}"

    avg_sim = sum_sim / max(1, comparisons)
    print(f"\n[{scale_name.upper()} DIVERSITY VERIFIED] Comparisons: {comparisons}, Avg Similarity: {avg_sim:.3f}, Max: {max_sim:.3f}")

    # Render Visual Comparison Matrix Sheet
    sheet_path = os.path.join(OUTPUT_DIR, sheet_filename)
    FloorPlanVisualizer.render_diversity_comparison_sheet(
        plans,
        sheet_path,
        title=f"{scale_name.upper()} RESIDENTIAL DESIGN MATRIX ({len(plans)} DISTINCT PROMPTS)"
    )
    assert os.path.exists(sheet_path), f"Comparison matrix not found: {sheet_path}"
    print(f"Saved {scale_name} Comparison Matrix: {sheet_path} ({os.path.getsize(sheet_path)} bytes)\n")

    return {
        "scale": scale_name,
        "designs_count": len(plans),
        "comparisons_count": comparisons,
        "average_similarity": round(avg_sim, 3),
        "maximum_similarity": round(max_sim, 3),
        "comparison_sheet": sheet_path
    }


def test_3_marla_5_requirements_diversity():
    res = _execute_scale_diversity_benchmark("3 Marla", PROMPTS_3M, "3_marla_comparison_sheet.png")
    assert res["designs_count"] == 5
    assert res["maximum_similarity"] < 0.72


def test_5_marla_5_requirements_diversity():
    res = _execute_scale_diversity_benchmark("5 Marla", PROMPTS_5M, "5_marla_comparison_sheet.png")
    assert res["designs_count"] == 5
    assert res["maximum_similarity"] < 0.72


def test_7_marla_5_requirements_diversity():
    res = _execute_scale_diversity_benchmark("7 Marla", PROMPTS_7M, "7_marla_comparison_sheet.png")
    assert res["designs_count"] == 5
    assert res["maximum_similarity"] < 0.72


def test_10_marla_10_requirements_primary_diversity():
    res = _execute_scale_diversity_benchmark("10 Marla", PROMPTS_10M, "10_marla_comparison_sheet.png")
    assert res["designs_count"] == 10
    assert res["maximum_similarity"] < 0.72


def test_1_kanal_10_requirements_diversity():
    res = _execute_scale_diversity_benchmark("1 Kanal", PROMPTS_1K, "1_kanal_comparison_sheet.png")
    assert res["designs_count"] == 10
    assert res["maximum_similarity"] < 0.72


if __name__ == "__main__":
    r3 = _execute_scale_diversity_benchmark("3 Marla", PROMPTS_3M, "3_marla_comparison_sheet.png")
    r5 = _execute_scale_diversity_benchmark("5 Marla", PROMPTS_5M, "5_marla_comparison_sheet.png")
    r7 = _execute_scale_diversity_benchmark("7 Marla", PROMPTS_7M, "7_marla_comparison_sheet.png")
    r10 = _execute_scale_diversity_benchmark("10 Marla", PROMPTS_10M, "10_marla_comparison_sheet.png")
    r1k = _execute_scale_diversity_benchmark("1 Kanal", PROMPTS_1K, "1_kanal_comparison_sheet.png")

    summary_report = {
        "status": "PASS",
        "benchmark": "MULTI-PLOT + MULTI-REQUIREMENT DESIGN DIVERSITY BENCHMARK",
        "total_prompts": 35,
        "total_generated": 35,
        "total_accepted": 35,
        "total_rejected": 0,
        "threshold_max_similarity": 0.72,
        "scales": [r3, r5, r7, r10, r1k]
    }
    report_path = os.path.join(OUTPUT_DIR, "multi_plot_diversity_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
    print(f"Exported Master Diversity Benchmark Report to: {report_path}")
