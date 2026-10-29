"""
Unit tests for Phase 1: Pilot Dataset Cleanup and Stress-Set Isolation.
"""

import os
import json


def test_stress_manifest_exists_and_accurate():
    manifest_p = os.path.join("data", "evaluation_only", "pilot_stress_187", "stress_manifest.json")
    assert os.path.exists(manifest_p)
    with open(manifest_p, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["clean_unique_count"] == 183
    assert data["quarantined_exact_count"] == 2
    assert data["quarantined_near_count"] == 2
    assert len(data["items"]) == 183


def test_quarantined_files_exist():
    exact_dir = os.path.join("data", "quarantine", "exact_duplicates")
    near_dir = os.path.join("data", "quarantine", "near_duplicates_downscaled")
    assert os.path.exists(exact_dir)
    assert os.path.exists(near_dir)
    assert len(os.listdir(exact_dir)) == 2
    assert len(os.listdir(near_dir)) == 2


def test_all_clean_images_accessible():
    images_dir = os.path.join("data", "evaluation_only", "pilot_stress_187", "images")
    assert os.path.exists(images_dir)
    files = os.listdir(images_dir)
    assert len(files) == 183
