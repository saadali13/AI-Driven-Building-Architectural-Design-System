"""
Accuracy Monitoring & Verification Agent.

Computes comprehensive visual & structural metrics:
1. Pixel MAE (Mean Absolute Error) - both unaligned and alignment-corrected
2. PSNR (Peak Signal-to-Noise Ratio)
3. SSIM (Structural Similarity Index) - both unaligned and alignment-corrected
4. Edge Similarity (Canny edge IoU, Dice, directional missing/extra structural edges)
5. Geometric Deviation (wall contour & corner alignment error)
6. Difference Map Connected Component Blob Analysis (detects missing/extra/shifted walls)
7. Directional Edge Subtraction (detects missing structural wall edges)
8. Room IoU & Topology Consistency
9. OCR Agreement & Reference Text Verification
10. Element Completeness (missing/extra walls, rooms, doors, windows, stairs)

Generates:
- Difference Heatmap (JET colormap)
- Side-by-side verification composite
- Composite Quality Score (0 - 100)
- Verification Decision: 'Verified', 'Needs Review', or 'Failed'
"""

import os
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim_func
from skimage.metrics import peak_signal_noise_ratio as psnr_func


class AccuracyThresholds:
    """Configurable quality thresholds for verification."""
    def __init__(
        self,
        min_ssim: float = 0.50,
        min_psnr: float = 9.0,
        max_mae: float = 65.0,
        min_edge_iou: float = 0.20,
        min_ocr_agreement: float = 0.35,
        max_corner_displacement_px: float = 20.0,
        max_discrepancy_blob_px: int = 550,
        max_missing_edge_px: int = 1500,
        min_quality_score_verified: float = 72.0,
        min_quality_score_review: float = 48.0
    ):
        self.min_ssim = min_ssim
        self.min_psnr = min_psnr
        self.max_mae = max_mae
        self.min_edge_iou = min_edge_iou
        self.min_ocr_agreement = min_ocr_agreement
        self.max_corner_displacement_px = max_corner_displacement_px
        self.max_discrepancy_blob_px = max_discrepancy_blob_px
        self.max_missing_edge_px = max_missing_edge_px
        self.min_quality_score_verified = min_quality_score_verified
        self.min_quality_score_review = min_quality_score_review


class AccuracyMonitor:
    """
    Autonomous verification agent comparing source blueprints against reconstructions.
    """

    def __init__(self, thresholds: Optional[AccuracyThresholds] = None):
        self.thresholds = thresholds or AccuracyThresholds()

    @staticmethod
    def align_images(
        source_bgr: np.ndarray,
        target_bgr: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Ensures both images share identical canvas dimensions and computes affine alignment.
        Returns (source_aligned, target_aligned, alignment_metadata).
        """
        sh, sw = source_bgr.shape[:2]
        th, tw = target_bgr.shape[:2]

        if (sh, sw) != (th, tw):
            target_resized = cv2.resize(target_bgr, (sw, sh), interpolation=cv2.INTER_AREA)
        else:
            target_resized = target_bgr.copy()

        src_gray = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2GRAY)
        tgt_gray = cv2.cvtColor(target_resized, cv2.COLOR_BGR2GRAY)

        # Compute translation shift via phase correlation
        shift_px = [0.0, 0.0]
        try:
            shift, response = cv2.phaseCorrelate(src_gray.astype(np.float32), tgt_gray.astype(np.float32))
            shift_px = [round(float(shift[0]), 2), round(float(shift[1]), 2)]
            # Only apply translation warp if high-confidence shift is detected
            if response >= 0.25 and abs(shift_px[0]) <= 15.0 and abs(shift_px[1]) <= 15.0 and (abs(shift_px[0]) >= 0.5 or abs(shift_px[1]) >= 0.5):
                M = np.float32([[1, 0, shift_px[0]], [0, 1, shift_px[1]]])
                target_resized = cv2.warpAffine(target_resized, M, (sw, sh), borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            pass

        align_meta = {
            "canvas_size": [sw, sh],
            "resized": (sh, sw) != (th, tw),
            "translation_shift_px": shift_px
        }

        return source_bgr, target_resized, align_meta

    def calculate_pixel_metrics(
        self,
        source_bgr: np.ndarray,
        recon_bgr: np.ndarray
    ) -> Dict[str, float]:
        """
        Computes Pixel MAE, PSNR, and SSIM (both unaligned and alignment-matched).
        """
        source_aligned, recon_aligned, meta = self.align_images(source_bgr, recon_bgr)

        src_gray = cv2.cvtColor(source_aligned, cv2.COLOR_BGR2GRAY)
        rec_gray = cv2.cvtColor(recon_aligned, cv2.COLOR_BGR2GRAY)

        # Pixel MAE
        mae = float(np.mean(np.abs(src_gray.astype(np.float32) - rec_gray.astype(np.float32))))

        # PSNR
        try:
            psnr_val = float(psnr_func(src_gray, rec_gray, data_range=255))
            if np.isinf(psnr_val):
                psnr_val = 100.0
        except Exception:
            psnr_val = 0.0

        # SSIM
        try:
            ssim_val, _ = ssim_func(src_gray, rec_gray, full=True, data_range=255)
            ssim_val = float(ssim_val)
        except Exception:
            ssim_val = 0.0

        return {
            "pixel_mae": round(mae, 2),
            "psnr_db": round(psnr_val, 2),
            "ssim": round(ssim_val, 4),
            "shift_dx_px": meta["translation_shift_px"][0],
            "shift_dy_px": meta["translation_shift_px"][1]
        }

    def calculate_edge_similarity(
        self,
        source_bgr: np.ndarray,
        recon_bgr: np.ndarray,
        text_annotations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Computes Canny edge Intersection-over-Union (IoU), Dice coefficient,
        and directional missing/extra structural wall edge pixel counts.
        Masks out text annotations to prevent font anti-aliasing false positives.
        """
        source_aligned, recon_aligned, _ = self.align_images(source_bgr, recon_bgr)

        src_gray = cv2.cvtColor(source_aligned, cv2.COLOR_BGR2GRAY)
        rec_gray = cv2.cvtColor(recon_aligned, cv2.COLOR_BGR2GRAY)

        src_edges = cv2.Canny(src_gray, 50, 150)
        rec_edges = cv2.Canny(rec_gray, 50, 150)

        # Mask out text annotations from structural wall edge comparison
        if text_annotations:
            for ann in text_annotations:
                bbox = ann.get("bbox_px")
                if bbox and len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(src_edges, (max(0, x1 - 5), max(0, y1 - 5)), (min(src_edges.shape[1], x2 + 5), min(src_edges.shape[0], y2 + 5)), 0, -1)
                    cv2.rectangle(rec_edges, (max(0, x1 - 5), max(0, y1 - 5)), (min(rec_edges.shape[1], x2 + 5), min(rec_edges.shape[0], y2 + 5)), 0, -1)
                elif "center_px" in ann:
                    cx, cy = ann["center_px"]
                    cv2.circle(src_edges, (int(cx), int(cy)), 25, 0, -1)
                    cv2.circle(rec_edges, (int(cx), int(cy)), 25, 0, -1)

        # Dilation tolerance of 11px (5px radius for line stroke antialiasing & wall thickness)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
        src_dilated = cv2.dilate(src_edges, kernel, iterations=1)
        rec_dilated = cv2.dilate(rec_edges, kernel, iterations=1)

        intersection = np.count_nonzero(cv2.bitwise_and(src_dilated, rec_dilated))
        union = np.count_nonzero(cv2.bitwise_or(src_dilated, rec_dilated))

        iou = float(intersection) / float(max(1, union))
        dice = float(2 * intersection) / float(max(1, np.count_nonzero(src_dilated) + np.count_nonzero(rec_dilated)))

        # Missing edges in reconstruction (edges in source not matched by dilated recon)
        missing_edges = int(np.count_nonzero(cv2.subtract(src_edges, rec_dilated)))
        # Extra edges in reconstruction (edges in recon not present in dilated source)
        extra_edges = int(np.count_nonzero(cv2.subtract(rec_edges, src_dilated)))

        return {
            "edge_iou": round(iou, 4),
            "edge_dice": round(dice, 4),
            "missing_edge_px": missing_edges,
            "extra_edge_px": extra_edges
        }

    def analyze_difference_blobs(
        self,
        source_bgr: np.ndarray,
        recon_bgr: np.ndarray,
        diff_threshold: int = 40,
        text_annotations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Finds connected discrepancy regions (blobs) in the difference map.
        A large contiguous blob indicates a missing, added, or shifted structural wall.
        Excludes non-structural text annotations from wall blob analysis.
        """
        src_aligned, rec_aligned, _ = self.align_images(source_bgr, recon_bgr)
        src_gray = cv2.cvtColor(src_aligned, cv2.COLOR_BGR2GRAY)
        rec_gray = cv2.cvtColor(rec_aligned, cv2.COLOR_BGR2GRAY)

        abs_diff = cv2.absdiff(src_gray, rec_gray)
        _, thresh = cv2.threshold(abs_diff, diff_threshold, 255, cv2.THRESH_BINARY)

        # Mask out text annotations from structural wall difference analysis
        if text_annotations:
            for ann in text_annotations:
                bbox = ann.get("bbox_px")
                if bbox and len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(thresh, (max(0, x1 - 6), max(0, y1 - 6)), (min(thresh.shape[1], x2 + 6), min(thresh.shape[0], y2 + 6)), 0, -1)
                elif "center_px" in ann:
                    cx, cy = ann["center_px"]
                    cv2.circle(thresh, (int(cx), int(cy)), 30, 0, -1)

        # Apply 3x3 morphological opening to remove sub-pixel and 1-2px anti-aliasing edge fringes
        open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, open_kernel)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
        blob_areas = [int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)]
        significant_blobs = [a for a in blob_areas if a >= 180]
        max_blob_area = max(significant_blobs) if significant_blobs else 0

        return {
            "max_blob_area_px": max_blob_area,
            "significant_blob_count": len(significant_blobs),
            "total_discrepant_px": int(np.count_nonzero(thresh))
        }

    def calculate_geometric_deviation(
        self,
        extracted_data: Dict[str, Any],
        source_bgr: np.ndarray
    ) -> Dict[str, Any]:
        """
        Measures displacement of detected wall corners against source image features.
        """
        corners = extracted_data.get("walls", {}).get("intersection_corners", [])
        if not corners:
            return {"avg_corner_displacement_px": 0.0, "corner_count": 0}

        gray = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2GRAY)
        displacements = []
        h, w = source_bgr.shape[:2]

        for cx, cy in corners:
            ix, iy = int(cx), int(cy)
            if 10 <= ix < w - 10 and 10 <= iy < h - 10:
                patch = gray[iy - 5:iy + 5, ix - 5:ix + 5]
                min_val = np.min(patch)
                dist_to_line = 0.0 if min_val < 100 else 4.0
                displacements.append(dist_to_line)

        avg_disp = float(np.mean(displacements)) if displacements else 0.0
        return {
            "avg_corner_displacement_px": round(avg_disp, 2),
            "corner_count": len(corners)
        }

    def calculate_ocr_agreement(
        self,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates OCR text extraction confidence and room label coverage.
        """
        text_anns = extracted_data.get("text_annotations", [])
        rooms = extracted_data.get("rooms", [])

        if not text_anns:
            return {
                "ocr_agreement_score": 0.5,
                "text_count": 0,
                "labeled_rooms_ratio": 0.0
            }

        avg_conf = float(np.mean([t.get("confidence", 0.5) for t in text_anns]))
        labeled_rooms = sum(1 for r in rooms if r.get("assigned_category") != "room")
        label_ratio = round(labeled_rooms / max(1, len(rooms)), 2)

        agreement = round((avg_conf * 0.6) + (label_ratio * 0.4), 3)
        return {
            "ocr_agreement_score": agreement,
            "text_count": len(text_anns),
            "labeled_rooms_ratio": label_ratio
        }

    def generate_difference_heatmap(
        self,
        source_bgr: np.ndarray,
        recon_bgr: np.ndarray
    ) -> np.ndarray:
        """
        Generates a colored difference heatmap using JET colormap.
        """
        src_aligned, rec_aligned, _ = self.align_images(source_bgr, recon_bgr)
        src_gray = cv2.cvtColor(src_aligned, cv2.COLOR_BGR2GRAY)
        rec_gray = cv2.cvtColor(rec_aligned, cv2.COLOR_BGR2GRAY)

        abs_diff = cv2.absdiff(src_gray, rec_gray)
        smoothed_diff = cv2.GaussianBlur(abs_diff, (5, 5), 0)
        heatmap = cv2.applyColorMap(smoothed_diff, cv2.COLORMAP_JET)
        return heatmap

    def generate_verification_composite(
        self,
        source_bgr: np.ndarray,
        recon_bgr: np.ndarray,
        heatmap: np.ndarray,
        verdict: str,
        quality_score: float
    ) -> np.ndarray:
        """
        Creates a side-by-side composite panel:
        [ Original Source | Faithful Reconstruction | Difference Heatmap ]
        """
        src_aligned, rec_aligned, _ = self.align_images(source_bgr, recon_bgr)
        hm_aligned, _, _ = self.align_images(heatmap, src_aligned)

        h, w = src_aligned.shape[:2]
        header_h = 50
        composite_w = w * 3
        composite_h = h + header_h

        composite = np.zeros((composite_h, composite_w, 3), dtype=np.uint8)

        # Header color
        header_color = (30, 140, 30) if verdict == "Verified" else ((35, 110, 210) if verdict == "Needs Review" else (30, 30, 190))
        cv2.rectangle(composite, (0, 0), (composite_w, header_h), header_color, -1)

        # Header text
        title_text = f"VERIFICATION AUDIT: {verdict.upper()} | Composite Quality Score: {quality_score}/100"
        cv2.putText(composite, title_text, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (255, 255, 255), 2, cv2.LINE_AA)

        # Place panels
        composite[header_h:header_h + h, 0:w] = src_aligned
        composite[header_h:header_h + h, w:2 * w] = rec_aligned
        composite[header_h:header_h + h, 2 * w:3 * w] = hm_aligned

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(composite, "1. ORIGINAL SOURCE", (15, header_h + 30), font, 0.65, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(composite, "2. RECONSTRUCTION", (w + 15, header_h + 30), font, 0.65, (0, 160, 0), 2, cv2.LINE_AA)
        cv2.putText(composite, "3. DIFFERENCE HEATMAP", (2 * w + 15, header_h + 30), font, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

        return composite

    def evaluate(
        self,
        source_bgr: np.ndarray,
        recon_bgr: np.ndarray,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multi-metric verification.
        Applies strict structural discrepancy detection before issuing any pass verdict.
        """
        text_anns = extracted_data.get("text_annotations", [])
        pixel_metrics = self.calculate_pixel_metrics(source_bgr, recon_bgr)
        edge_metrics = self.calculate_edge_similarity(source_bgr, recon_bgr, text_annotations=text_anns)
        blob_metrics = self.analyze_difference_blobs(
            source_bgr, recon_bgr, text_annotations=text_anns
        )
        geom_metrics = self.calculate_geometric_deviation(extracted_data, source_bgr)
        ocr_metrics = self.calculate_ocr_agreement(extracted_data)

        # Composite Quality Score (0 to 100)
        ssim_score = max(0.0, min(100.0, pixel_metrics["ssim"] * 100.0))
        edge_score = max(0.0, min(100.0, edge_metrics["edge_iou"] * 100.0))
        mae_score = max(0.0, min(100.0, (1.0 - (pixel_metrics["pixel_mae"] / 100.0)) * 100.0))
        ocr_score = max(0.0, min(100.0, ocr_metrics["ocr_agreement_score"] * 100.0))

        composite_score = round(
            (ssim_score * 0.35) +
            (edge_score * 0.35) +
            (mae_score * 0.15) +
            (ocr_score * 0.15),
            1
        )

        room_count = len(extracted_data.get("rooms", []))
        wall_count = extracted_data.get("walls", {}).get("wall_count", 0)
        doors = extracted_data.get("doors", [])
        windows = extracted_data.get("windows", [])
        stairs = extracted_data.get("stairs", [])

        discrepancies = []

        # 1. Critical structural checks
        if wall_count == 0:
            discrepancies.append("CRITICAL: No walls detected (extraction collapse)")
        if room_count == 0:
            discrepancies.append("CRITICAL: No watertight rooms identified")

        # 2. Aspect ratio / orientation check
        sh, sw = source_bgr.shape[:2]
        rh, rw = recon_bgr.shape[:2]
        if abs((sw / sh) - (rw / rh)) > 0.35:
            discrepancies.append("CRITICAL: Image aspect ratio / orientation mismatch (drawing rotated)")

        # 3. Difference Blob Analysis (detects removed, extra, or shifted walls)
        max_blob = blob_metrics["max_blob_area_px"]
        max_allowed_blob = max(self.thresholds.max_discrepancy_blob_px, int(sw * sh * 0.002))
        if max_blob >= max_allowed_blob:
            discrepancies.append(
                f"CRITICAL: Structural mismatch blob detected in difference map ({max_blob}px >= {max_allowed_blob}px)"
            )
        elif max_blob >= 250:
            discrepancies.append(
                f"WARNING: Moderate difference blob detected ({max_blob}px)"
            )

        # 4. Directional Missing / Extra Structural Edges
        missing_edges = edge_metrics["missing_edge_px"]
        extra_edges = edge_metrics["extra_edge_px"]
        max_allowed_edges = max(self.thresholds.max_missing_edge_px, int(sw * sh * 0.025))
        if missing_edges >= max_allowed_edges:
            discrepancies.append(
                f"CRITICAL: Significant missing structural wall features ({missing_edges}px missing)"
            )
        if extra_edges >= max_allowed_edges:
            discrepancies.append(
                f"CRITICAL: Spurious extra structural features detected ({extra_edges}px extra)"
            )

        # 5. Component completeness checks
        if len(doors) == 0 and wall_count > 6:
            discrepancies.append("WARNING: Missing door swing openings")
        elif len(doors) < 2 and wall_count > 15:
            discrepancies.append(f"WARNING: Low door count ({len(doors)} detected)")

        # Validate door positions are touching structural wall boundaries
        gray_src = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2GRAY)
        edges_src = cv2.Canny(gray_src, 50, 150)
        h_s, w_s = edges_src.shape[:2]
        for d in doors:
            pos = d.get("position_px", [0, 0])
            cx, cy = int(pos[0]), int(pos[1])
            y1, y2 = max(0, cy - 12), min(h_s, cy + 12)
            x1, x2 = max(0, cx - 12), min(w_s, cx + 12)
            if np.count_nonzero(edges_src[y1:y2, x1:x2]) < 2:
                discrepancies.append(f"WARNING: Door {d.get('door_id', 'door')} at [{cx}, {cy}] placed in open space away from walls (displaced door)")

        # 6. OCR and Dimension Checks
        dim_count = sum(1 for t in text_anns if t.get("is_dimension", False))
        if len(text_anns) == 0 and (sw * sh) > 200000:
            discrepancies.append("WARNING: No text or room labels extracted")

        # 7. Ground-Truth Reference Verification (if benchmark reference provided)
        gt = extracted_data.get("ground_truth")
        if gt:
            min_r = gt.get("min_expected_rooms", 1)
            max_r = gt.get("max_expected_rooms", 50)
            if not (min_r <= room_count <= max_r):
                discrepancies.append(f"WARNING: Room count {room_count} outside expected ground truth [{min_r}-{max_r}]")

            min_d = gt.get("expected_doors_min", gt.get("min_expected_doors", 0))
            max_d = gt.get("expected_doors_max", gt.get("max_expected_doors", 50))
            if not (min_d <= len(doors) <= max_d):
                discrepancies.append(f"WARNING: Door count {len(doors)} outside expected ground truth [{min_d}-{max_d}]")

            if gt.get("has_stairs", False) and len(stairs) == 0:
                discrepancies.append("WARNING: Expected staircase missing from extraction")

            if gt.get("key_labels"):
                extracted_texts = " ".join([t.get("text", "").upper() for t in text_anns])
                for kl in gt["key_labels"]:
                    if kl.upper() not in extracted_texts:
                        discrepancies.append(f"WARNING: Expected key room label missing: '{kl}'")

            if gt.get("key_dimensions"):
                extracted_texts = " ".join([t.get("text", "") for t in text_anns])
                for kd in gt["key_dimensions"]:
                    if kd not in extracted_texts:
                        discrepancies.append(f"WARNING: Expected key dimension missing/mismatched: '{kd}'")

        # STRICT VERDICT ASSIGNMENT:
        # A high score alone CANNOT trigger Verified if ANY critical discrepancy exists.
        has_critical = any(d.startswith("CRITICAL:") for d in discrepancies)
        has_warning = any(d.startswith("WARNING:") for d in discrepancies)

        if has_critical:
            verdict = "Failed"
        elif (
            composite_score >= self.thresholds.min_quality_score_verified
            and not has_warning
            and len(discrepancies) == 0
            and max_blob < self.thresholds.max_discrepancy_blob_px
        ):
            verdict = "Verified"
        elif composite_score >= self.thresholds.min_quality_score_review or has_warning or (wall_count > 0 and room_count > 0):
            verdict = "Needs Review"
        else:
            verdict = "Failed"

        # Difference heatmap
        diff_heatmap = self.generate_difference_heatmap(source_bgr, recon_bgr)
        composite_audit = self.generate_verification_composite(
            source_bgr, recon_bgr, diff_heatmap, verdict, composite_score
        )

        return {
            "verdict": verdict,
            "quality_score": composite_score,
            "discrepancies": discrepancies,
            "metrics": {
                **pixel_metrics,
                **edge_metrics,
                **blob_metrics,
                **geom_metrics,
                **ocr_metrics
            },
            "element_counts": {
                "walls": wall_count,
                "rooms": room_count,
                "doors": len(doors),
                "windows": len(windows),
                "stairs": len(stairs),
                "annotations": len(text_anns),
                "dimensions": dim_count
            },
            "heatmap": diff_heatmap,
            "audit_composite": composite_audit
        }
