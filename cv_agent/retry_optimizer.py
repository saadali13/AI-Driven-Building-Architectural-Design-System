"""
Continuous Improvement & Autonomous Retry Optimizer.

Executes iterative correction loop:
1. Diagnoses extraction defects from validation checks and comparison metrics.
2. Identifies pipeline stages responsible for each error.
3. Selects targeted parameter interventions (morphological dilation, adaptive thresholding,
   contrast tuning, room area threshold adjustments, text bounding box re-association).
4. Re-evaluates candidate against known-good checkpoint and rejects regressions.
5. Records comprehensive iteration audit trail for correction_history.json.
"""

from typing import Dict, List, Tuple, Any, Optional
import copy


class RetryOptimizer:
    """
    Autonomous error diagnosis and corrective retry manager.
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def diagnose_defects(
        self,
        audit_results: Dict[str, Any],
        geo_metrics: Dict[str, Any],
        extracted_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Classifies errors and pinpoints responsible pipeline stages.
        """
        defects = []
        metrics = audit_results.get("metrics", {})
        counts = audit_results.get("element_counts", {})
        score = audit_results.get("quality_score", 0.0)

        # 1. Structural wall discontinuity / missing walls
        wall_cont = geo_metrics.get("wall_continuity_ratio", 0.7)
        if wall_cont < 0.55 or counts.get("walls", 0) < 4:
            defects.append({
                "category": "broken_or_sparse_walls",
                "responsible_stage": "Stage D: Architectural geometry extraction",
                "evidence": f"Wall continuity ({wall_cont:.2f}) below threshold 0.55 or wall count ({counts.get('walls', 0)}) sparse",
                "action": "tune_morphology_and_dilate_walls"
            })

        # 2. Over-segmented or missing room chambers
        room_count = counts.get("rooms", 0)
        if room_count == 0:
            defects.append({
                "category": "missing_room_chambers",
                "responsible_stage": "Stage E: Room segmentation",
                "evidence": "Zero watertight rooms detected",
                "action": "lower_min_room_area_threshold"
            })
        elif room_count > 35:
            defects.append({
                "category": "room_over_segmentation",
                "responsible_stage": "Stage E: Room segmentation",
                "evidence": f"Plausibility failure: {room_count} micro-fragments detected",
                "action": "increase_min_room_area_filter"
            })

        # 3. Low Structural Similarity (SSIM)
        ssim_val = metrics.get("ssim", 0.0)
        if ssim_val < 0.45:
            defects.append({
                "category": "low_structural_similarity",
                "responsible_stage": "Stage B: Preprocessing and line enhancement",
                "evidence": f"SSIM ({ssim_val:.4f}) indicates significant layout mismatch",
                "action": "clahe_high_contrast_line_sharpening"
            })

        # 4. Door jamb attachment failure
        door_attach = geo_metrics.get("door_jamb_attachment_ratio", 1.0)
        if door_attach < 0.50 and counts.get("doors", 0) > 0:
            defects.append({
                "category": "detached_door_swings",
                "responsible_stage": "Stage D: Opening detection",
                "evidence": f"Door jamb attachment ratio ({door_attach:.2f}) below 0.50",
                "action": "expand_jamb_tolerance_and_wall_proximity"
            })

        # 5. Low OCR agreement on dimension text
        ocr_score = metrics.get("ocr_agreement_score", 0.5)
        if ocr_score < 0.25 and len(extracted_data.get("ocr_text", [])) == 0:
            defects.append({
                "category": "faint_or_unrecognized_text",
                "responsible_stage": "Stage C: OCR and text extraction",
                "evidence": "No legible text blocks extracted",
                "action": "apply_adaptive_threshold_contrast_boost"
            })

        return defects

    def select_correction_strategy(
        self,
        defects: List[Dict[str, str]],
        current_iteration: int
    ) -> Dict[str, Any]:
        """
        Determines targeted parameter interventions based on diagnosed defects.
        """
        if not defects:
            return {"action": "none", "parameters": {}}

        # Prioritize critical structural wall issues
        primary_defect = defects[0]
        action = primary_defect["action"]

        if action == "tune_morphology_and_dilate_walls":
            return {
                "action": action,
                "responsible_stage": primary_defect["responsible_stage"],
                "parameters": {
                    "wall_dilation_iterations": 1 + current_iteration,
                    "hough_min_length": 14,
                    "hough_max_gap": 18 + (current_iteration * 4)
                }
            }
        elif action == "lower_min_room_area_threshold":
            return {
                "action": action,
                "responsible_stage": primary_defect["responsible_stage"],
                "parameters": {
                    "min_room_area_factor": 0.0005,
                    "wall_bridge_kernel": 5
                }
            }
        elif action == "increase_min_room_area_filter":
            return {
                "action": action,
                "responsible_stage": primary_defect["responsible_stage"],
                "parameters": {
                    "min_room_area_factor": 0.008
                }
            }
        elif action == "clahe_high_contrast_line_sharpening":
            return {
                "action": action,
                "responsible_stage": primary_defect["responsible_stage"],
                "parameters": {
                    "clahe_clip": 3.5,
                    "bilateral_diameter": 9
                }
            }
        else:
            return {
                "action": "general_line_enhancement",
                "responsible_stage": "Stage B: Preprocessing",
                "parameters": {
                    "wall_dilation_iterations": 1
                }
            }

    @staticmethod
    def evaluate_candidate_improvement(
        baseline_metrics: Dict[str, Any],
        candidate_metrics: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Compares candidate against baseline. Strictly rejects regressions in critical metrics.
        Returns (is_better, reasoning).
        """
        base_score = baseline_metrics.get("quality_score", 0.0)
        cand_score = candidate_metrics.get("quality_score", 0.0)

        base_ssim = baseline_metrics.get("metrics", {}).get("ssim", 0.0)
        cand_ssim = candidate_metrics.get("metrics", {}).get("ssim", 0.0)

        base_rooms = baseline_metrics.get("element_counts", {}).get("rooms", 0)
        cand_rooms = candidate_metrics.get("element_counts", {}).get("rooms", 0)

        # Regression check: If SSIM drops significantly (> 0.05), reject candidate
        if cand_ssim < base_ssim - 0.05:
            return False, f"Regression rejected: SSIM dropped from {base_ssim:.4f} to {cand_ssim:.4f}"

        # If previous run had 0 rooms and candidate found rooms, accept
        if base_rooms == 0 and cand_rooms > 0:
            return True, f"Improvement verified: Recovered {cand_rooms} rooms from 0 previously"

        # Higher quality score with no major regression
        if cand_score > base_score + 1.5:
            return True, f"Improvement verified: Quality score increased from {base_score:.1f} to {cand_score:.1f}"

        return False, f"Candidate rejected: Quality score ({cand_score:.1f}) did not meaningfully improve over baseline ({base_score:.1f})"
