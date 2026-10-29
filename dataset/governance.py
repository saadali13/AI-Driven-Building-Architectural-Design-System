"""
Dataset Governance and Licensing Enforcement Engine.
Enforces auditable provenance, release-specific licensing verification,
and mechanical gating to prevent non-commercial or unverified data leakage
into commercial production training runs.
"""

import json
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetEntry(BaseModel):
    dataset_id: str
    dataset_name: str
    category: str
    source_url: str
    paper_reference: Optional[str] = None
    release_or_version: Optional[str] = None
    download_date: Optional[str] = None
    license: str
    license_url: Optional[str] = None
    copyright_or_provenance_notes: str
    allowed_use: str
    commercial_use: bool = Field(default=False)
    derivative_use: bool = Field(default=False)
    attribution_requirement: str
    train_val_test_assignment: str
    checksum: Optional[str] = None
    status: str


class GovernancePolicy(BaseModel):
    strict_commercial_enforcement: bool = True
    disallowed_for_commercial: List[str] = Field(default_factory=lambda: ["research_only", "evaluation_only", "unverified"])
    allowed_for_commercial: List[str] = Field(default_factory=lambda: ["commercial_allowed", "commercial_allowed_pending_release_verification"])
    mandatory_provenance_fields: List[str] = Field(default_factory=list)


class ManifestDocument(BaseModel):
    version: str
    generated_at: str
    governance_policy: GovernancePolicy
    datasets: List[DatasetEntry]


class DatasetGovernance:
    def __init__(self, manifest_path: Optional[str] = None):
        if manifest_path is None:
            # Default to data/dataset_manifest.json relative to repository root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            manifest_path = os.path.join(base_dir, "data", "dataset_manifest.json")
        self.manifest_path = manifest_path
        self.manifest = self._load_and_validate_manifest()

    def _load_and_validate_manifest(self) -> ManifestDocument:
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Dataset governance manifest missing: {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ManifestDocument.model_validate(data)

    def get_dataset(self, dataset_id: str) -> DatasetEntry:
        for ds in self.manifest.datasets:
            if ds.dataset_id == dataset_id:
                return ds
        raise KeyError(f"Dataset '{dataset_id}' not found in governance manifest.")

    def verify_commercial_eligibility(self, dataset_id: str) -> bool:
        """
        Mechanical licensing gate.
        Raises PermissionError if dataset is not cleared for commercial deployment.
        """
        ds = self.get_dataset(dataset_id)
        policy = self.manifest.governance_policy

        if policy.strict_commercial_enforcement:
            if not ds.commercial_use:
                raise PermissionError(
                    f"COMMERCIAL GATING VIOLATION: Dataset '{ds.dataset_name}' ({ds.dataset_id}) "
                    f"is flagged commercial_use=False under license '{ds.license}'. "
                    f"It cannot be loaded for commercial model training or production weights generation."
                )
            if ds.category in policy.disallowed_for_commercial:
                raise PermissionError(
                    f"COMMERCIAL GATING VIOLATION: Dataset '{ds.dataset_name}' category '{ds.category}' "
                    f"is forbidden for commercial production training."
                )
        return True

    def get_commercial_training_datasets(self) -> List[DatasetEntry]:
        """Returns only datasets cleared for commercial production training."""
        cleared = []
        for ds in self.manifest.datasets:
            try:
                if self.verify_commercial_eligibility(ds.dataset_id):
                    cleared.append(ds)
            except PermissionError:
                continue
        return cleared

    def get_evaluation_datasets(self) -> List[DatasetEntry]:
        """Returns datasets authorized for evaluation, benchmark, and stress testing."""
        return [
            ds for ds in self.manifest.datasets 
            if "evaluation" in ds.train_val_test_assignment 
            or "stress" in ds.train_val_test_assignment
            or "benchmark" in ds.train_val_test_assignment
            or "evaluation" in ds.category
        ]
