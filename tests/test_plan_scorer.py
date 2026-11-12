from dataset.catalog_10_marla import build_10m_v01
from dataset.catalog_5_marla import build_5m_v01
from dataset.catalog_1_kanal import build_1k_v01
from generation.plan_quality_scorer import PlanQualityScorer

def test_plan_scorer_10m():
    plan = build_10m_v01()
    r = PlanQualityScorer.score_canonical_plan(plan, '10_marla')
    print("\n10 Marla Score:", r["total_score"], r["verdict"])
    for k, v in r["hard_rules"].items():
        print(f"  {v['name']}: {'PASS' if v['passed'] else 'FAIL'} {v['violations']}")
    assert r["total_score"] >= 85.0
    assert r["hard_rules"]["no_room_containment"]["passed"]
    assert r["hard_rules"]["bedroom_bath_attachment"]["passed"]
    assert r["hard_rules"]["stair_vertical_stacking"]["passed"]
    assert r["hard_rules"]["room_door_accessibility"]["passed"]

def test_plan_scorer_5m():
    plan = build_5m_v01()
    r = PlanQualityScorer.score_canonical_plan(plan, '5_marla')
    print("\n5 Marla Score:", r["total_score"], r["verdict"])
    assert r["total_score"] >= 75.0
    assert r["hard_rules"]["no_room_containment"]["passed"]
    assert r["hard_rules"]["bedroom_bath_attachment"]["passed"]

def test_plan_scorer_1k():
    plan = build_1k_v01()
    r = PlanQualityScorer.score_canonical_plan(plan, '1_kanal')
    print("\n1 Kanal Score:", r["total_score"], r["verdict"])
    assert r["total_score"] >= 80.0
    assert r["hard_rules"]["no_room_containment"]["passed"]
    assert r["hard_rules"]["stair_vertical_stacking"]["passed"]
