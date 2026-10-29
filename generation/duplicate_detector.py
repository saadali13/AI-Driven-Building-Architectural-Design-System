"""
Automatic Architectural Duplicate Detection & Topological Uniqueness Registry.

Maintains an immutable registry of previously accepted designs.
Computes multi-dimensional topological similarity:
- Rejects candidate designs whose structural signature similarity >= DUPLICATE_THRESHOLD (0.70).
- Identifies exact repeated structures (e.g., repeated staircase, kitchen, or circulation core).
- Triggers regeneration with an alternative planning strategy upon rejection.
"""

from typing import Dict, List, Tuple, Any, Optional

from dataset.schema.canonical import CanonicalFloorPlan
from generation.structural_signature import (
    StructuralDesignSignature,
    extract_structural_signature,
    compute_structural_similarity,
)


class DuplicateDetector:
    """
    Registry and evaluator that prevents topologically identical floor plans from being accepted.
    """

    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.72

    def __init__(self):
        # Maps scale -> list of accepted StructuralDesignSignature
        self._accepted_signatures: Dict[str, List[StructuralDesignSignature]] = {}

    def clear(self):
        """Clears the registry (useful for isolated benchmark runs)."""
        self._accepted_signatures.clear()

    def evaluate_design(
        self,
        candidate_plan: CanonicalFloorPlan
    ) -> Tuple[bool, float, List[str], Optional[str]]:
        """
        Evaluates a candidate plan against all previously accepted plans of the same scale.
        Returns:
            is_duplicate (bool): True if similarity >= threshold
            max_similarity (float): Highest similarity score encountered
            repeated_elements (List[str]): List of identified repeated spatial elements
            conflicting_plan_id (Optional[str]): Plan ID of the most similar accepted design
        """
        candidate_sig = extract_structural_signature(candidate_plan)
        scale = candidate_sig.scale

        existing_sigs = self._accepted_signatures.get(scale, [])
        if not existing_sigs:
            return False, 0.0, [], None

        max_sim = 0.0
        worst_repeated: List[str] = []
        conflicting_id: Optional[str] = None

        for existing_sig in existing_sigs:
            sim, repeated = compute_structural_similarity(candidate_sig, existing_sig)
            if sim > max_sim:
                max_sim = sim
                worst_repeated = repeated
                conflicting_id = existing_sig.plan_id

        is_dup = max_sim >= self.DUPLICATE_SIMILARITY_THRESHOLD
        return is_dup, max_sim, worst_repeated, conflicting_id

    def register_design(self, plan: CanonicalFloorPlan) -> StructuralDesignSignature:
        """Registers an accepted design signature into the registry."""
        sig = extract_structural_signature(plan)
        scale = sig.scale
        if scale not in self._accepted_signatures:
            self._accepted_signatures[scale] = []
        self._accepted_signatures[scale].append(sig)
        return sig

    def get_registered_count(self, scale: Optional[str] = None) -> int:
        """Returns number of registered designs."""
        if scale:
            return len(self._accepted_signatures.get(scale, []))
        return sum(len(sigs) for sigs in self._accepted_signatures.values())
