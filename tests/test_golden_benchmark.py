"""
Unit tests for Phase 2: Golden 50 Ground-Truth Benchmark and Evaluation Harness.
"""

import os
import json
import pytest
from dataset.benchmark_validator import GoldenPlan, BenchmarkEvaluator, RoomGT


def test_golden_manifest_and_stratification():
    manifest_p = os.path.join("data", "ground_truth", "golden_50", "golden_manifest.json")
    assert os.path.exists(manifest_p)
    with open(manifest_p, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_plans"] == 50
    strat = data["stratification"]
    assert strat["1-2_bedroom"] == 10
    assert strat["3_bedroom"] == 15
    assert strat["4+_bedroom"] == 10
    assert strat["irregular_l_shaped"] == 5
    assert strat["duplex_multi_floor"] == 5
    assert strat["unusual_commercial"] == 5


def test_all_50_plans_pass_strict_pydantic_validation():
    plans_dir = os.path.join("data", "ground_truth", "golden_50", "plans")
    assert os.path.exists(plans_dir)
    files = [f for f in os.listdir(plans_dir) if f.endswith(".json")]
    assert len(files) == 50

    for fname in files:
        fpath = os.path.join(plans_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            raw = json.load(f)
        plan = GoldenPlan.model_validate(raw)
        assert plan.plan_id == fname.replace(".json", "")
        assert len(plan.rooms) >= 3
        assert len(plan.walls) >= 4
        assert len(plan.openings) >= 2


def test_benchmark_evaluator_room_iou_and_metrics():
    # Load first golden plan
    fpath = os.path.join("data", "ground_truth", "golden_50", "plans", "golden_001.json")
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    gt_plan = GoldenPlan.model_validate(data)

    # Perfect prediction test
    pred_rooms = [
        {"polygon": r.polygon, "type": r.room_type, "name": r.room_name}
        for r in gt_plan.rooms
    ]
    res = BenchmarkEvaluator.evaluate_rooms(pred_rooms, gt_plan.rooms, iou_threshold=0.5)

    assert res["room_precision"] == 1.0
    assert res["room_recall"] == 1.0
    assert res["room_f1"] == 1.0
    assert res["mean_iou"] == 1.0
    assert res["classification_accuracy"] == 1.0


def test_benchmark_evaluator_graph_metrics():
    fpath = os.path.join("data", "ground_truth", "golden_50", "plans", "golden_011.json")
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    gt_plan = GoldenPlan.model_validate(data)

    pred_edges = [
        {"source": e.source_room_id, "target": e.target_room_id, "type": e.relationship_type}
        for e in gt_plan.graph_edges
    ]
    res = BenchmarkEvaluator.evaluate_graph(pred_edges, gt_plan.graph_edges)

    assert res["graph_edge_precision"] == 1.0
    assert res["graph_edge_recall"] == 1.0
    assert res["graph_edge_f1"] == 1.0
