"""
Stage A: Image Preprocessing Engine.

Handles:
1. Skew and rotation detection & correction.
2. Noise reduction & artifact filtering while preserving architectural line sharpness.
3. Adaptive contrast enhancement and line-background binarization.
4. Segmenting combined elevation-and-floorplan drawings into discrete regions.
"""

import os
from typing import Dict, Tuple, Any, Optional
import cv2
import numpy as np


class ImagePreprocessor:
    """
    Preprocesses architectural blueprint scans for high-fidelity element detection.
    """

    @staticmethod
    def detect_and_correct_skew(image_bgr: np.ndarray, max_angle_deg: float = 15.0) -> Tuple[np.ndarray, float]:
        """
        Detects minor scan skew using Hough transform line angles and applies affine rotation correction.
        Returns (corrected_image, detected_angle_degrees).
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=120, minLineLength=80, maxLineGap=10)

        if lines is None or len(lines) == 0:
            return image_bgr, 0.0

        angles = []
        for line in lines:
            coords = line.flatten()
            if len(coords) < 4:
                continue
            x1, y1, x2, y2 = coords[:4]
            dx = x2 - x1
            dy = y2 - y1
            if dx == 0:
                continue
            angle = np.degrees(np.arctan2(dy, dx))
            # Filter nearly horizontal lines
            if abs(angle) < max_angle_deg:
                angles.append(angle)
            elif abs(angle - 90) < max_angle_deg:
                angles.append(angle - 90)
            elif abs(angle + 90) < max_angle_deg:
                angles.append(angle + 90)

        if not angles:
            return image_bgr, 0.0

        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.35:
            return image_bgr, 0.0  # Negligible skew

        h, w = image_bgr.shape[:2]
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        corrected = cv2.warpAffine(image_bgr, rot_mat, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return corrected, round(median_angle, 2)

    @staticmethod
    def enhance_contrast(image_bgr: np.ndarray) -> np.ndarray:
        """
        Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) on the L-channel
        in LAB color space to equalize blueprints and low-contrast scanned drawings.
        """
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    @staticmethod
    def extract_line_mask(image_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts binary architectural line mask and wall core mask:
        - Line mask: All crisp black/dark lines (walls, text, symbols).
        - Wall mask: Thick continuous structural lines (exterior & interior walls).
        Suppresses colored interior furnishings and furniture on rendered floor plans.
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        # Bilateral filter preserves sharp wall edges while eliminating paper noise
        denoised = cv2.bilateralFilter(gray, 7, 50, 50)

        # Adaptive thresholding to extract foreground lines
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6
        )

        # Structural wall extraction using morphological kernels
        # Horizontal lines
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
        h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)

        # Vertical lines
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
        v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)

        wall_mask = cv2.bitwise_or(h_lines, v_lines)

        # Suppress colored furniture / furnishings in rendered drawings
        if len(image_bgr.shape) == 3 and image_bgr.shape[2] == 3:
            hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
            sat = hsv[:, :, 1]
            val = hsv[:, :, 2]
            # Furniture (beds, sofas, tables, tiles) has high color saturation and brightness
            furniture_mask = (sat > 32) & (val > 65)
            wall_mask[furniture_mask] = 0

        return binary, wall_mask

    @staticmethod
    def isolate_floor_plan_region(image_bgr: np.ndarray, image_type: str = "floor_plan") -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        For combined drawings (`elevation_with_floorplan`), automatically identifies
        and crops the floor plan sub-panel while recording its bounding box offset:
        (x_min, y_min, x_max, y_max).
        Analyzes rectilinear wall line density and brightness distribution to separate 2D floor plans from 3D elevations.
        For pure floor plans, returns the full image with (0, 0, w, h).
        """
        h, w = image_bgr.shape[:2]
        if image_type != "elevation_with_floorplan":
            return image_bgr, (0, 0, w, h)

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # Detect rectilinear lines
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6)
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
        v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)
        rectilinear = cv2.bitwise_or(h_lines, v_lines)

        # Compute vertical projection profile of rectilinear density
        row_density = np.sum(rectilinear > 0, axis=1) / float(w)

        # Smooth the profile to identify the dividing gap/valley between elevation and floorplan
        kernel_smooth = np.ones(31) / 31.0
        smoothed = np.convolve(row_density, kernel_smooth, mode='same')

        # Compare top half vs bottom half line density and paper brightness
        top_slice = slice(int(h * 0.08), int(h * 0.45))
        bot_slice = slice(int(h * 0.52), int(h * 0.95))

        top_density = np.mean(smoothed[top_slice]) if h > 100 else 0
        bot_density = np.mean(smoothed[bot_slice]) if h > 100 else 0

        # Also check brightness: 2D floor plans are drawn on light paper (high mean/median),
        # while 3D elevations have darker rendered textures or shaded backgrounds.
        top_brightness = np.mean(gray[top_slice])
        bot_brightness = np.mean(gray[bot_slice])

        # Find the dividing transition in the central region (30% to 70% height)
        search_range = range(int(h * 0.35), int(h * 0.65))
        if search_range:
            # Find the minimum density valley (whitespace or border line separating panels)
            min_y = min(search_range, key=lambda y: smoothed[y])
        else:
            min_y = int(h * 0.5)

        # Decide whether floor plan is in lower or upper panel
        # Floor plan has higher rectilinear density and usually higher paper brightness
        floor_plan_is_bottom = (bot_density * 1.2 + (bot_brightness / 255.0)) >= (top_density * 1.2 + (top_brightness / 255.0))

        if floor_plan_is_bottom:
            # Floor plan is in bottom half
            split_y = max(int(h * 0.30), min(int(h * 0.65), min_y))
            panel = image_bgr[split_y:, :]
            return panel, (0, split_y, w, h)
        else:
            # Floor plan is in top half
            split_y = max(int(h * 0.35), min(int(h * 0.70), min_y))
            panel = image_bgr[:split_y, :]
            return panel, (0, 0, w, split_y)

    @staticmethod
    def extract_robust_background_color(image_bgr: np.ndarray, wall_mask: Optional[np.ndarray] = None) -> List[int]:
        """
        Samples dominant background paper tone of an architectural drawing,
        robustly rejecting black scan borders, margin frames, and dark title blocks.
        """
        h, w = image_bgr.shape[:2]
        # Inset 5% from all edges to avoid scanner cropping margins
        m_y = max(4, int(h * 0.05))
        m_x = max(4, int(w * 0.05))
        interior = image_bgr[m_y:h - m_y, m_x:w - m_x]

        if interior.size == 0:
            return [255, 255, 255]

        gray_int = cv2.cvtColor(interior, cv2.COLOR_BGR2GRAY)

        if wall_mask is not None and wall_mask.shape[:2] == image_bgr.shape[:2]:
            wm_int = wall_mask[m_y:h - m_y, m_x:w - m_x]
            non_wall_mask = (wm_int == 0)
        else:
            edges = cv2.Canny(gray_int, 30, 100)
            edges_dilated = cv2.dilate(edges, np.ones((5, 5), np.uint8))
            non_wall_mask = (edges_dilated == 0)

        if np.count_nonzero(non_wall_mask) > 100:
            valid_pixels = interior[non_wall_mask]
        else:
            valid_pixels = interior.reshape(-1, 3)

        gray_valid = cv2.cvtColor(valid_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY).flatten()
        median_val = float(np.median(gray_valid))

        if len(valid_pixels) > 0:
            bg = [int(v) for v in np.median(valid_pixels, axis=0)]
        else:
            bg = [255, 255, 255]

        # Never return pitch black [0, 0, 0] for an image whose interior is light
        if median_val > 120 and max(bg) < 60:
            bg = [250, 250, 250]

        return bg

    def preprocess(self, image_path: str, image_type: str = "floor_plan") -> Dict[str, Any]:
        """
        Full Stage A preprocessing pipeline:
        Reads, corrects skew, enhances contrast, extracts line masks, and isolates drawing panels.
        """
        original_bgr = cv2.imread(image_path)
        if original_bgr is None:
            raise ValueError(f"Could not load image: {image_path}")

        orig_h, orig_w, orig_c = original_bgr.shape

        # Step 1: Skew correction
        deskewed, angle = self.detect_and_correct_skew(original_bgr)

        # Step 2: Panel isolation if combined
        panel_bgr, crop_box = self.isolate_floor_plan_region(deskewed, image_type)

        # Step 3: Contrast enhancement
        enhanced = self.enhance_contrast(panel_bgr)

        # Step 4: Line and wall segmentation masks
        binary_mask, wall_mask = self.extract_line_mask(enhanced)

        # Step 5: Robust paper/background color tone extraction
        bg_bgr = self.extract_robust_background_color(panel_bgr, wall_mask)

        return {
            "original_image": original_bgr,
            "original_dimensions": [orig_w, orig_h],
            "deskewed_image": deskewed,
            "skew_angle_deg": angle,
            "panel_image": panel_bgr,
            "panel_crop_box": crop_box,  # (x1, y1, x2, y2)
            "enhanced_image": enhanced,
            "binary_mask": binary_mask,
            "wall_mask": wall_mask,
            "background_color_bgr": bg_bgr
        }
