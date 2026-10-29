"""
Phase 3: Image Preprocessing, Resolution Gating, Deskewing, and Border Suppression.
Preserves raw images non-destructively while producing normalized, deskewed,
and contrast-enhanced architectural line drawings with processing metadata.
"""

import os
import cv2
import numpy as np
from typing import Dict, Tuple, Optional, Any


class Preprocessor:
    def __init__(self, min_resolution: int = 600):
        self.min_resolution = min_resolution

    def check_resolution(self, img: np.ndarray) -> Dict[str, Any]:
        """Evaluates image resolution against architectural OCR/dimension thresholds."""
        h, w = img.shape[:2]
        is_low_res = (w < self.min_resolution or h < self.min_resolution)
        return {
            "width": w,
            "height": h,
            "is_low_res": is_low_res,
            "requires_upscaling": is_low_res,
            "resolution_status": "insufficient_for_small_ocr" if is_low_res else "adequate"
        }

    def estimate_skew_angle(self, gray: np.ndarray) -> float:
        """Estimates tilt/skew angle using probabilistic Hough line transform on architectural walls."""
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=80, maxLineGap=10)
        if lines is None:
            return 0.0

        angles = []
        for line in lines:
            coords = line.reshape(-1)
            if len(coords) < 4:
                continue
            x1, y1, x2, y2 = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Wrap to [-45, 45] range relative to horizontal/vertical axes
            angle = (angle + 45) % 90 - 45
            if abs(angle) < 15.0: # Filter out diagonals
                angles.append(angle)

        if not angles:
            return 0.0
        # Return median skew
        return float(np.median(angles))

    def deskew_image(self, img: np.ndarray, angle: float) -> np.ndarray:
        """Rotates image around center by estimated angle with white background fill."""
        if abs(angle) < 0.2:
            return img
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

    def suppress_borders(self, gray: np.ndarray, border_ratio: float = 0.03) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Detects and suppresses dark sheet borders and outer margin framing."""
        h, w = gray.shape[:2]
        pad_x = int(w * border_ratio)
        pad_y = int(h * border_ratio)

        # Inspect margin edge density
        margins = [
            gray[:pad_y, :],
            gray[-pad_y:, :],
            gray[:, :pad_x],
            gray[:, -pad_x:]
        ]
        has_heavy_border = any(np.mean(m < 80) > 0.25 for m in margins)

        clean_gray = gray.copy()
        if has_heavy_border:
            # Mask the outermost margin with white (255)
            clean_gray[:pad_y, :] = 255
            clean_gray[-pad_y:, :] = 255
            clean_gray[:, :pad_x] = 255
            clean_gray[:, -pad_x:] = 255

        return clean_gray, {
            "border_detected": has_heavy_border,
            "border_cropped": has_heavy_border,
            "margin_pads": [pad_x, pad_y]
        }

    def enhance_contrast(self, gray: np.ndarray) -> np.ndarray:
        """Applies CLAHE for local contrast normalization across faded scans."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def process(self, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Executes full preprocessing pipeline.
        Returns:
            processed_bgr: Deskewed, normalized BGR image.
            processed_gray: Deskewed, border-suppressed, enhanced grayscale image.
            metadata: Comprehensive processing metadata dict.
        """
        res_info = self.check_resolution(img)

        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # 1. Deskew
        angle = self.estimate_skew_angle(gray)
        deskewed_bgr = self.deskew_image(img, angle)
        deskewed_gray = self.deskew_image(gray, angle)

        # 2. Border suppression
        clean_gray, border_info = self.suppress_borders(deskewed_gray)

        # 3. Contrast enhancement
        enhanced_gray = self.enhance_contrast(clean_gray)

        metadata = {
            "resolution": res_info,
            "deskew_angle_deg": round(angle, 2),
            "border_suppression": border_info,
            "contrast_enhanced": True
        }

        return deskewed_bgr, enhanced_gray, metadata
