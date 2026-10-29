"""
Unit tests for Dataset Governance and Licensing Enforcement.
"""

import pytest
from dataset.governance import DatasetGovernance


def test_manifest_loading_and_validation():
    gov = DatasetGovernance()
    assert gov.manifest.version == "1.0"
    assert len(gov.manifest.datasets) >= 4


def test_mechanical_licensing_gate_rejects_cubicasa5k():
    gov = DatasetGovernance()
    with pytest.raises(PermissionError) as exc_info:
        gov.verify_commercial_eligibility("ds_cubicasa5k")
    assert "COMMERCIAL GATING VIOLATION" in str(exc_info.value)
    assert "commercial_use=False" in str(exc_info.value)


def test_mechanical_licensing_gate_clears_resplan_github_release():
    gov = DatasetGovernance()
    assert gov.verify_commercial_eligibility("ds_resplan_2025") is True


def test_commercial_training_filter_strictly_excludes_research_only():
    gov = DatasetGovernance()
    commercial_sets = gov.get_commercial_training_datasets()
    dataset_ids = [ds.dataset_id for ds in commercial_sets]
    assert "ds_cubicasa5k" not in dataset_ids
    assert "ds_pilot_stress_187" not in dataset_ids
    assert "ds_resplan_2025" in dataset_ids


def test_evaluation_sets_included():
    gov = DatasetGovernance()
    eval_sets = gov.get_evaluation_datasets()
    dataset_ids = [ds.dataset_id for ds in eval_sets]
    assert "ds_pilot_stress_187" in dataset_ids
    assert "ds_golden_50_benchmark" in dataset_ids
