"""
Controlled Error Injection & Accuracy Monitor Auditor.

Tests whether the AccuracyMonitor correctly identifies known architectural mutations:
- Removed wall
- Added extra wall
- Shifted wall
- Removed door
- Moved door
- Merged / altered rooms
- Deleted room label
- Altered dimension annotation
- Erased staircase
- 90-degree unaligned rotation
- Unchanged copy (ground truth)
- Harmless JPEG re-compression (false positive test)
- Empty / corrupted extraction

Computes Monitor Precision, Recall, and F1 Score on ground-truth mutations.
"""

import os
import json
import csv
import copy
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np

from cv_agent.detector import ArchitecturalElementDetector
from cv_agent.reconstructor import FloorPlanReconstructor
from cv_agent.accuracy_monitor import AccuracyMonitor, AccuracyThresholds


class ControlledMonitorAuditor:
    """
    Evaluates the error-detection capability of AccuracyMonitor using controlled test cases.
    """

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = os.path.abspath(reports_dir)
        os.makedirs(self.reports_dir, exist_ok=True)
        self.monitor = AccuracyMonitor()
        self.reconstructor = FloorPlanReconstructor()

    def create_reference_blueprint(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Synthesizes a clean, unambiguous architectural floor plan with ground-truth geometry.
        Dimensions: 600 x 800 px.
        Contains: 2 Bedrooms, 1 Bathroom, 1 Kitchen, 1 Living Room, 1 Porch, 1 Staircase, 4 Doors, Text Labels.
        """
        w, h = 600, 800
        canvas = np.full((h, w, 3), 255, dtype=np.uint8)

        # 1. Outer Perimeter Walls (thickness: 8px)
        cv2.rectangle(canvas, (50, 50), (550, 750), (20, 20, 20), 8)

        # 2. Interior Walls (thickness: 6px)
        # Horizontal dividing wall at y=400 (separates front & rear)
        cv2.line(canvas, (50, 400), (550, 400), (20, 20, 20), 6)
        # Vertical wall separating Master Bed & Bed 2 (y=50 to 400, x=300)
        cv2.line(canvas, (300, 50), (300, 400), (20, 20, 20), 6)
        # Bath dividing wall (x=200 to 300, y=180)
        cv2.line(canvas, (200, 180), (300, 180), (20, 20, 20), 6)
        cv2.line(canvas, (200, 50), (200, 180), (20, 20, 20), 6)
        # Kitchen dividing wall (x=350 to 550, y=560)
        cv2.line(canvas, (350, 400), (350, 750), (20, 20, 20), 6)

        # 3. Doors (Wall openings + 90-degree swing arcs)
        doors = [
            {"cx": 260, "cy": 400, "r": 35, "desc": "Bed 1 Door"},
            {"cx": 340, "cy": 400, "r": 35, "desc": "Bed 2 Door"},
            {"cx": 200, "cy": 120, "r": 28, "desc": "Bath Door"},
            {"cx": 350, "cy": 500, "r": 35, "desc": "Kitchen Door"},
        ]
        for d in doors:
            # Cut opening
            if d["cx"] == 200:
                cv2.line(canvas, (d["cx"], d["cy"] - 16), (d["cx"], d["cy"] + 16), (255, 255, 255), 8)
            else:
                cv2.line(canvas, (d["cx"] - 16, d["cy"]), (d["cx"] + 16, d["cy"]), (255, 255, 255), 8)
            # Draw swing arc
            cv2.ellipse(canvas, (d["cx"], d["cy"]), (d["r"], d["r"]), 0, 0, 90, (80, 80, 80), 1)

        # 4. Staircase (steps at front porch)
        for sy in range(620, 740, 12):
            cv2.line(canvas, (70, sy), (180, sy), (60, 60, 60), 1)
        cv2.rectangle(canvas, (70, 620), (180, 740), (40, 40, 40), 1)

        # 5. Room Labels & Dimensions
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(canvas, "MASTER BEDROOM", (70, 250), font, 0.55, (10, 10, 10), 2)
        cv2.putText(canvas, "14' x 16'", (70, 275), font, 0.45, (120, 20, 20), 1)
        cv2.putText(canvas, "BEDROOM 2", (340, 250), font, 0.55, (10, 10, 10), 2)
        cv2.putText(canvas, "BATH", (215, 120), font, 0.45, (10, 10, 10), 1)
        cv2.putText(canvas, "LIVING LOUNGE", (100, 500), font, 0.6, (10, 10, 10), 2)
        cv2.putText(canvas, "KITCHEN", (400, 520), font, 0.55, (10, 10, 10), 2)
        cv2.putText(canvas, "CAR PORCH", (90, 720), font, 0.5, (10, 10, 10), 1)

        # Build ground-truth extracted data structure
        ground_truth_meta = {
            "image_size": [w, h],
            "walls": {
                "wall_thickness_px": 6.0,
                "wall_count": 24,
                "wall_contours": [
                    [[50, 50], [550, 50], [550, 750], [50, 750]],  # Outer perimeter envelope
                    [[50, 400], [550, 400]],                         # Horizontal dividing wall
                    [[300, 50], [300, 400]],                         # Bedroom divider
                    [[200, 50], [200, 180], [300, 180]],             # Bathroom wall
                    [[350, 400], [350, 750]],                        # Kitchen dividing wall
                ],
                "intersection_corners": [[50, 50], [550, 50], [550, 750], [50, 750], [300, 50], [300, 400], [350, 400]]
            },
            "rooms": [
                {"room_id": "room_1", "assigned_label": "MASTER BEDROOM", "assigned_category": "bedroom", "polygon_px": [[50, 50], [300, 50], [300, 400], [50, 400]], "area_px": 87500.0, "bbox_px": [50, 50, 300, 400]},
                {"room_id": "room_2", "assigned_label": "BEDROOM 2", "assigned_category": "bedroom", "polygon_px": [[300, 50], [550, 50], [550, 400], [300, 400]], "area_px": 87500.0, "bbox_px": [300, 50, 550, 400]},
                {"room_id": "room_3", "assigned_label": "BATH", "assigned_category": "bathroom", "polygon_px": [[200, 50], [300, 50], [300, 180], [200, 180]], "area_px": 13000.0, "bbox_px": [200, 50, 300, 180]},
                {"room_id": "room_4", "assigned_label": "LIVING LOUNGE", "assigned_category": "living_room", "polygon_px": [[50, 400], [350, 400], [350, 750], [50, 750]], "area_px": 105000.0, "bbox_px": [50, 400, 350, 750]},
                {"room_id": "room_5", "assigned_label": "KITCHEN", "assigned_category": "kitchen", "polygon_px": [[350, 400], [550, 400], [550, 750], [350, 750]], "area_px": 70000.0, "bbox_px": [350, 400, 550, 750]},
            ],
            "doors": [
                {"door_id": "door_1", "position_px": [260, 400], "swing_radius_px": 35},
                {"door_id": "door_2", "position_px": [340, 400], "swing_radius_px": 35},
                {"door_id": "door_3", "position_px": [200, 120], "swing_radius_px": 28},
                {"door_id": "door_4", "position_px": [350, 500], "swing_radius_px": 35},
            ],
            "stairs": [
                {"stair_id": "stair_1", "bbox_px": [70, 620, 180, 740], "approx_steps": 10}
            ],
            "text_annotations": [
                {"text": "MASTER BEDROOM", "center_px": [140, 250], "is_dimension": False, "confidence": 0.95},
                {"text": "14' x 16'", "center_px": [100, 275], "is_dimension": True, "confidence": 0.92},
                {"text": "BEDROOM 2", "center_px": [400, 250], "is_dimension": False, "confidence": 0.95},
                {"text": "BATH", "center_px": [240, 120], "is_dimension": False, "confidence": 0.90},
                {"text": "LIVING LOUNGE", "center_px": [170, 500], "is_dimension": False, "confidence": 0.95},
                {"text": "KITCHEN", "center_px": [440, 520], "is_dimension": False, "confidence": 0.95},
                {"text": "CAR PORCH", "center_px": [130, 720], "is_dimension": False, "confidence": 0.90},
            ],
            "ground_truth": {
                "min_expected_rooms": 5,
                "max_expected_rooms": 5,
                "min_expected_doors": 4,
                "max_expected_doors": 4,
                "has_stairs": True,
                "key_labels": ["MASTER BEDROOM", "BEDROOM 2", "BATH", "LIVING LOUNGE", "KITCHEN"],
                "key_dimensions": ["14' x 16'"]
            }
        }

        # Render ground-truth blueprint faithfully from structured architectural metadata
        canvas = self.reconstructor.render_faithful_raster(ground_truth_meta, target_size=(w, h))
        return canvas, ground_truth_meta

    def generate_controlled_test_cases(
        self,
        reference_img: np.ndarray,
        reference_meta: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Creates 13 isolated mutation test cases covering every architectural error category.
        """
        test_cases = []

        # Case 1: Unchanged Ground Truth (Baseline Positive)
        test_cases.append({
            "id": "TC01_unchanged_reference",
            "category": "baseline_integrity",
            "description": "Exact unchanged source image and extracted geometry",
            "modified_img": reference_img.copy(),
            "modified_meta": copy.deepcopy(reference_meta),
            "is_mutated": False,
            "expected_verdict": "Verified"
        })

        # Case 2: Harmless JPEG Re-encoding (False Positive Resistance)
        _, enc = cv2.imencode(".jpg", reference_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        jpeg_reencoded = cv2.imdecode(enc, cv2.IMREAD_COLOR)
        test_cases.append({
            "id": "TC02_harmless_compression",
            "category": "compression_invariance",
            "description": "Slight JPEG compression (Q=85) without any structural changes",
            "modified_img": jpeg_reencoded,
            "modified_meta": copy.deepcopy(reference_meta),
            "is_mutated": False,
            "expected_verdict": "Verified"
        })

        # Case 3: Removed Structural Wall (Critical Error)
        img_no_wall = reference_img.copy()
        # Erase the dividing wall between Bedroom 1 and Bedroom 2 (x=300, y=50 to 400)
        cv2.line(img_no_wall, (300, 50), (300, 400), (255, 255, 255), 14)
        meta_no_wall = copy.deepcopy(reference_meta)
        meta_no_wall["walls"]["wall_count"] = max(1, meta_no_wall["walls"]["wall_count"] - 4)
        test_cases.append({
            "id": "TC03_removed_wall",
            "category": "wall_deletion",
            "description": "Erased structural wall between Bedroom 1 and Bedroom 2",
            "modified_img": img_no_wall,
            "modified_meta": meta_no_wall,
            "is_mutated": True,
            "expected_verdict": "Failed"
        })

        # Case 4: Added Spurious Wall (Partition Discrepancy)
        img_extra_wall = reference_img.copy()
        # Draw arbitrary wall cutting Living Lounge in half (y=580, x=50 to 350)
        cv2.line(img_extra_wall, (50, 580), (350, 580), (20, 20, 20), 8)
        meta_extra_wall = copy.deepcopy(reference_meta)
        meta_extra_wall["walls"]["wall_count"] += 5
        test_cases.append({
            "id": "TC04_added_extra_wall",
            "category": "extra_structural_element",
            "description": "Added spurious 8px wall bisecting the Living Lounge",
            "modified_img": img_extra_wall,
            "modified_meta": meta_extra_wall,
            "is_mutated": True,
            "expected_verdict": "Failed"
        })

        # Case 5: Shifted Wall Geometry (Geometric Displacement)
        img_shifted_wall = reference_img.copy()
        # Erase kitchen wall at x=350, redraw at x=410 (60px shift)
        cv2.line(img_shifted_wall, (350, 400), (350, 750), (255, 255, 255), 12)
        cv2.line(img_shifted_wall, (410, 400), (410, 750), (20, 20, 20), 6)
        meta_shifted = copy.deepcopy(reference_meta)
        meta_shifted["walls"]["intersection_corners"].append([410, 400])
        test_cases.append({
            "id": "TC05_shifted_wall_geometry",
            "category": "geometric_deviation",
            "description": "Shifted kitchen boundary wall east by 60 pixels",
            "modified_img": img_shifted_wall,
            "modified_meta": meta_shifted,
            "is_mutated": True,
            "expected_verdict": "Failed"
        })

        # Case 6: Removed Door Swing (Missing Opening)
        meta_no_door = copy.deepcopy(reference_meta)
        meta_no_door["doors"] = meta_no_door["doors"][:2]  # Remove 2 doors
        test_cases.append({
            "id": "TC06_missing_doors",
            "category": "door_completeness",
            "description": "Erased Kitchen and Bath doors from architectural vector metadata",
            "modified_img": reference_img.copy(),
            "modified_meta": meta_no_door,
            "is_mutated": True,
            "expected_verdict": "Needs Review"
        })

        # Case 7: Relocated Door (Displaced Component)
        meta_moved_door = copy.deepcopy(reference_meta)
        meta_moved_door["doors"][0]["position_px"] = [100, 100]  # Moved to wrong corner
        test_cases.append({
            "id": "TC07_relocated_door",
            "category": "element_displacement",
            "description": "Moved Bed 1 door from (260, 400) to corner (100, 100)",
            "modified_img": reference_img.copy(),
            "modified_meta": meta_moved_door,
            "is_mutated": True,
            "expected_verdict": "Needs Review"
        })

        # Case 8: Room Merged / Room Count Altered
        meta_merged_rooms = copy.deepcopy(reference_meta)
        # Drop bedroom 2
        meta_merged_rooms["rooms"] = [r for r in meta_merged_rooms["rooms"] if r["assigned_label"] != "BEDROOM 2"]
        test_cases.append({
            "id": "TC08_altered_room_count",
            "category": "room_topology",
            "description": "Erased Bedroom 2 chamber; room count dropped from 5 to 4",
            "modified_img": reference_img.copy(),
            "modified_meta": meta_merged_rooms,
            "is_mutated": True,
            "expected_verdict": "Needs Review"
        })

        # Case 9: Deleted Room Label (Semantic Discrepancy)
        meta_no_label = copy.deepcopy(reference_meta)
        meta_no_label["text_annotations"] = [
            t for t in meta_no_label["text_annotations"] if "MASTER" not in t["text"]
        ]
        test_cases.append({
            "id": "TC09_deleted_room_label",
            "category": "ocr_label_missing",
            "description": "Erased 'MASTER BEDROOM' label from OCR extraction",
            "modified_img": reference_img.copy(),
            "modified_meta": meta_no_label,
            "is_mutated": True,
            "expected_verdict": "Needs Review"
        })

        # Case 10: Altered Dimension Annotation
        meta_dim_altered = copy.deepcopy(reference_meta)
        for t in meta_dim_altered["text_annotations"]:
            if t["is_dimension"]:
                t["text"] = "28' x 36'"  # Distorted dimension
        test_cases.append({
            "id": "TC10_altered_dimension",
            "category": "dimension_falsification",
            "description": "Changed dimension '14 x 16' to '28 x 36'",
            "modified_img": reference_img.copy(),
            "modified_meta": meta_dim_altered,
            "is_mutated": True,
            "expected_verdict": "Needs Review"
        })

        # Case 11: Erased Staircase
        meta_no_stairs = copy.deepcopy(reference_meta)
        meta_no_stairs["stairs"] = []  # No stairs
        test_cases.append({
            "id": "TC11_missing_staircase",
            "category": "stair_circulation",
            "description": "Erased staircase flight from architectural elements",
            "modified_img": reference_img.copy(),
            "modified_meta": meta_no_stairs,
            "is_mutated": True,
            "expected_verdict": "Needs Review"
        })

        # Case 12: Rotated Drawing Without Alignment Correction (90 deg)
        rotated_90 = cv2.rotate(reference_img, cv2.ROTATE_90_CLOCKWISE)
        test_cases.append({
            "id": "TC12_orientation_mismatch",
            "category": "canvas_orientation",
            "description": "Rotated source image 90 degrees clockwise without alignment",
            "modified_img": rotated_90,
            "modified_meta": copy.deepcopy(reference_meta),
            "is_mutated": True,
            "expected_verdict": "Failed"
        })

        # Case 13: Empty / Corrupted Extraction (Critical Failure)
        meta_empty = {
            "image_size": [600, 800],
            "walls": {"wall_count": 0, "wall_contours": [], "wall_thickness_px": 0},
            "rooms": [],
            "doors": [],
            "stairs": [],
            "text_annotations": []
        }
        test_cases.append({
            "id": "TC13_empty_corrupted_extraction",
            "category": "extraction_collapse",
            "description": "Corrupted extraction returning 0 walls, 0 rooms, 0 elements",
            "modified_img": reference_img.copy(),
            "modified_meta": meta_empty,
            "is_mutated": True,
            "expected_verdict": "Failed"
        })

        return test_cases

    def run_audit(self) -> Dict[str, Any]:
        """
        Executes the controlled error injection audit and measures monitor Precision, Recall, and F1.
        """
        ref_img, ref_meta = self.create_reference_blueprint()
        test_cases = self.generate_controlled_test_cases(ref_img, ref_meta)

        records = []
        tp = 0  # Mutated case correctly flagged as Failed or Needs Review
        tn = 0  # Clean case correctly flagged as Verified
        fp = 0  # Clean case incorrectly flagged as Failed/Needs Review
        fn = 0  # Mutated case missed and incorrectly declared Verified

        print(f"=== Starting Accuracy Monitor Controlled Audit ({len(test_cases)} Test Cases) ===")

        for tc in test_cases:
            tc_id = tc["id"]
            cat = tc["category"]
            desc = tc["description"]
            is_mutated = tc["is_mutated"]
            exp_verdict = tc["expected_verdict"]

            # Render reconstruction from metadata
            h, w = tc["modified_img"].shape[:2]
            recon_img = self.reconstructor.render_faithful_raster(tc["modified_meta"], target_size=(w, h))

            # Run AccuracyMonitor evaluation
            audit_res = self.monitor.evaluate(tc["modified_img"], recon_img, tc["modified_meta"])
            actual_verdict = audit_res["verdict"]
            score = audit_res["quality_score"]
            discrepancies = audit_res["discrepancies"]

            # Evaluate detection correctness:
            # For mutated cases: monitor MUST NOT say 'Verified'
            # For clean cases: monitor MUST say 'Verified'
            if is_mutated:
                detected = (actual_verdict != "Verified")
                if detected:
                    tp += 1
                    test_passed = True
                else:
                    fn += 1
                    test_passed = False
            else:
                detected = False
                if actual_verdict == "Verified":
                    tn += 1
                    test_passed = True
                else:
                    fp += 1
                    test_passed = False

            print(f"  [{tc_id}] {cat}: Exp={exp_verdict} | Act={actual_verdict} (Score: {score}) -> {'PASS' if test_passed else 'FAIL'}")

            records.append({
                "test_id": tc_id,
                "category": cat,
                "description": desc,
                "is_mutated": is_mutated,
                "expected_verdict": exp_verdict,
                "actual_verdict": actual_verdict,
                "quality_score": score,
                "ssim": audit_res["metrics"]["ssim"],
                "pixel_mae": audit_res["metrics"]["pixel_mae"],
                "edge_iou": audit_res["metrics"]["edge_iou"],
                "discrepancies": "; ".join(discrepancies) if discrepancies else "None",
                "test_passed": test_passed
            })

        # Calculate Precision, Recall, F1 Score
        precision = round(tp / max(1, tp + fp), 4)
        recall = round(tp / max(1, tp + fn), 4)
        f1 = round((2 * precision * recall) / max(1e-5, precision + recall), 4)
        accuracy = round((tp + tn) / len(test_cases), 4)

        audit_summary = {
            "total_test_cases": len(test_cases),
            "passed_tests": sum(1 for r in records if r["test_passed"]),
            "failed_tests": sum(1 for r in records if not r["test_passed"]),
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "monitor_precision": precision,
            "monitor_recall": recall,
            "monitor_f1_score": f1,
            "overall_accuracy": accuracy,
            "test_case_records": records
        }

        # Save JSON Report
        json_path = os.path.join(self.reports_dir, "controlled_audit_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(audit_summary, f, indent=2)

        # Save CSV Report
        csv_path = os.path.join(self.reports_dir, "controlled_audit_report.csv")
        fieldnames = [
            "test_id", "category", "description", "is_mutated",
            "expected_verdict", "actual_verdict", "quality_score",
            "ssim", "pixel_mae", "edge_iou", "discrepancies", "test_passed"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                writer.writerow(r)

        print("\n=== Controlled Audit Results ===")
        print(f"Total: {len(test_cases)} | Passed: {audit_summary['passed_tests']} | Failed: {audit_summary['failed_tests']}")
        print(f"Precision: {precision * 100}% | Recall: {recall * 100}% | F1 Score: {f1 * 100}% | Accuracy: {accuracy * 100}%")
        print(f"Audit reports written to: {json_path} and {csv_path}")

        return audit_summary


if __name__ == "__main__":
    auditor = ControlledMonitorAuditor()
    auditor.run_audit()
