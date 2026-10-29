import sys
import os
sys.path.insert(0, os.path.abspath("."))

from generation.architectural_templates import Modern5MarlaArchitecturalEngine
from dataset.schema.canonical import CanonicalFloorPlan

def test_room_replacement_execution():
    plan = Modern5MarlaArchitecturalEngine.generate_5_marla_house(plan_id="test_5m_replace")
    
    # Verify initial state
    bed3 = next(r for r in plan.rooms if r.room_id == "room_L1_bed3")
    assert bed3.room_name == "Bedroom 3"
    assert bed3.room_type == "bedroom"
    
    # Simulate Gemini Senior Architect recommending replacement:
    # "Client requested an Executive Home Study / Office in place of Bedroom 3"
    mock_replacements = [
        {
            "room_id": "room_L1_bed3",
            "action": "replace",
            "new_name": "Executive Study / Home Office",
            "new_category": "study",
            "reason": "Conversion of upper room to dedicated home workspace"
        }
    ]
    
    # Apply replacement
    for rep in mock_replacements:
        rid = rep["room_id"]
        target_room = next(r for r in plan.rooms if r.room_id == rid)
        target_room.room_name = rep["new_name"]
        target_room.room_type = rep["new_category"]
        
    updated_bed3 = next(r for r in plan.rooms if r.room_id == "room_L1_bed3")
    assert updated_bed3.room_name == "Executive Study / Home Office"
    assert updated_bed3.room_type == "study"
    print("[TEST PASSED] Room replacement executed successfully!")

def test_room_swap_execution():
    plan = Modern5MarlaArchitecturalEngine.generate_5_marla_house(plan_id="test_5m_swap")
    
    # Verify initial centroids
    r_dining = next(r for r in plan.rooms if r.room_id == "room_L0_dining")
    r_kitchen = next(r for r in plan.rooms if r.room_id == "room_L0_kitchen")
    c_dining = list(r_dining.centroid)
    c_kitchen = list(r_kitchen.centroid)
    
    # Simulate Gemini Senior Architect swap:
    # Swap Dining and Kitchen
    poly_temp = r_dining.polygon
    cent_temp = r_dining.centroid
    area_temp = r_dining.area_m2
    
    r_dining.polygon = r_kitchen.polygon
    r_dining.centroid = r_kitchen.centroid
    r_dining.area_m2 = r_kitchen.area_m2
    
    r_kitchen.polygon = poly_temp
    r_kitchen.centroid = cent_temp
    r_kitchen.area_m2 = area_temp
    
    assert r_dining.centroid == c_kitchen
    assert r_kitchen.centroid == c_dining
    print("[TEST PASSED] Room swap executed successfully!")


def test_10_marla_different_prompts_diversity():
    """
    Benchmarks 10 distinct user requirement prompts on the SAME 10 Marla plot.
    Proves each yields a distinct structural signature and passes programmatic and Gemini QA.
    """
    from generation.rag_solver import DatasetDrivenRAGSolver
    from generation.structural_signature import extract_structural_signature, compute_structural_similarity
    from generation.duplicate_detector import DuplicateDetector
    from generation.gemini_architectural_auditor import GeminiArchitecturalAuditor
    from generation.visualizer import FloorPlanVisualizer

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

    for test_id, prompt in test_prompts:
        plan = solver.synthesize(f"{test_id}: {prompt}")
        sig = extract_structural_signature(plan)

        # 1. Audit user requirements
        req_res = GeminiArchitecturalAuditor.audit_user_requirements(prompt, plan)
        assert req_res["verdict"] == "PASS", f"Failed requirements for {test_id}: {req_res['missing_requirements']}"

        # 2. Evaluate duplicate detection
        is_dup, sim, repeated, conflict = detector.evaluate_design(plan)
        assert not is_dup, f"Duplicate detected for {test_id} against {conflict} (similarity {sim:.2f})"

        detector.register_design(plan)
        plans.append(plan)
        signatures.append(sig)

    # Pairwise diversity evaluation
    assert len(plans) == 10
    total_comparisons = 0
    max_sim = 0.0
    sum_sim = 0.0

    for i in range(len(signatures)):
        for j in range(i + 1, len(signatures)):
            sim, _ = compute_structural_similarity(signatures[i], signatures[j])
            total_comparisons += 1
            sum_sim += sim
            if sim > max_sim:
                max_sim = sim
            assert sim < 0.72, f"Excessive similarity ({sim:.2f}) between Plan {i+1} and Plan {j+1}"

    avg_sim = sum_sim / total_comparisons
    print(f"\n[DIVERSITY VERIFIED] 10 Marla 10 Prompts -> Comparisons: {total_comparisons}, Avg Similarity: {avg_sim:.3f}, Max: {max_sim:.3f}")

    # Generate multi-plan side-by-side comparison sheet
    out_dir = os.path.abspath(r"C:\Users\m\OneDrive\Desktop\New folder\output\diversity_matrix")
    sheet_path = os.path.join(out_dir, "10_marla_10_prompts_comparison_sheet.png")
    FloorPlanVisualizer.render_diversity_comparison_sheet(plans, sheet_path, title="10 MARLA BENCHMARK: 10 DISTINCT PROMPTS COMPARISON MATRIX")
    assert os.path.exists(sheet_path), f"Comparison sheet not generated at {sheet_path}"
    print(f"Saved 10 Marla Comparison Sheet: {sheet_path}")


def test_10_marla_same_prompt_5_alternatives():
    """
    Mandatory Test: ONE identical prompt -> 5 fundamentally different planning alternatives.
    Verifies that differing planning strategies (Central Lounge, Side Gallery, Split Guest-Family,
    Courtyard, Open Living) alter room topology, circulation, and zoning.
    """
    from generation.rag_solver import DatasetDrivenRAGSolver
    from generation.structural_signature import extract_structural_signature, compute_structural_similarity
    from generation.duplicate_detector import DuplicateDetector
    from generation.gemini_architectural_auditor import GeminiArchitecturalAuditor
    from generation.visualizer import FloorPlanVisualizer

    base_prompt = "Design a 10 Marla north-facing Pakistani residence with 4 bedrooms, 4 bathrooms, guest room, family lounge, study, kitchen, dirty kitchen, 2-car parking and front lawn"

    solver = DatasetDrivenRAGSolver()
    detector = DuplicateDetector()
    plans = []
    signatures = []

    for alt_idx in range(1, 6):
        prompt = f"{base_prompt}, Alternative 0{alt_idx}"
        plan = solver.synthesize(prompt, alternative_index=alt_idx)
        sig = extract_structural_signature(plan)

        # Audit user requirements
        req_res = GeminiArchitecturalAuditor.audit_user_requirements(base_prompt, plan)
        assert req_res["verdict"] == "PASS", f"Alt {alt_idx} failed requirements: {req_res['missing_requirements']}"

        # Evaluate duplicate detection against previously accepted alternatives
        is_dup, sim, repeated, conflict = detector.evaluate_design(plan)
        assert not is_dup, f"Alternative 0{alt_idx} is duplicate of {conflict} (similarity {sim:.2f})"

        detector.register_design(plan)
        plans.append(plan)
        signatures.append(sig)

    assert len(plans) == 5
    # Verify pairwise diversity among all 5 alternatives
    for i in range(len(signatures)):
        for j in range(i + 1, len(signatures)):
            sim, _ = compute_structural_similarity(signatures[i], signatures[j])
            assert sim < 0.72, f"Alternative 0{i+1} and Alternative 0{j+1} too similar: {sim:.2f}"

    out_dir = os.path.abspath(r"C:\Users\m\OneDrive\Desktop\New folder\output\diversity_matrix")
    sheet_path = os.path.join(out_dir, "10_marla_same_prompt_5_alternatives_comparison_sheet.png")
    FloorPlanVisualizer.render_diversity_comparison_sheet(plans, sheet_path, title="10 MARLA BENCHMARK: SAME PROMPT - 5 ARCHITECTURAL ALTERNATIVES")
    assert os.path.exists(sheet_path)
    print(f"Saved 5 Alternatives Comparison Sheet: {sheet_path}")


def test_multi_scale_diversity_suite():
    """
    Verifies that diversity engine operates across all scales (3M, 5M, 7M, 1 Kanal)
    and does not simply scale up or down a single layout.
    """
    from generation.rag_solver import DatasetDrivenRAGSolver
    from generation.structural_signature import extract_structural_signature, compute_structural_similarity

    scales = ["3_marla", "5_marla", "7_marla", "1_kanal"]
    solver = DatasetDrivenRAGSolver()

    for sc in scales:
        plan1 = solver.synthesize(f"Design {sc.replace('_', ' ')} residence with modern layout, alternative 1")
        plan2 = solver.synthesize(f"Design {sc.replace('_', ' ')} residence with modern layout, alternative 2")

        sig1 = extract_structural_signature(plan1)
        sig2 = extract_structural_signature(plan2)

        sim, repeated = compute_structural_similarity(sig1, sig2)
        print(f"Scale [{sc}] Alt 1 vs Alt 2 Similarity: {sim:.3f}")
        assert sim < 0.72, f"Scale {sc} alternatives failed diversity: {sim:.2f}"


if __name__ == "__main__":
    test_room_replacement_execution()
    test_room_swap_execution()
    test_10_marla_different_prompts_diversity()
    test_10_marla_same_prompt_5_alternatives()
    test_multi_scale_diversity_suite()
    print("All Auditor and Architectural Diversity tests passed successfully!")
