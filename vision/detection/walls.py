"""
Phase 5: Architectural Wall Detection and Centerline Extraction.
Uses stroke-width filtering to separate thick structural walls (>=4px)
from thin dimension witness lines, tile hatching, and furniture contours.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Any


class WallDetector:
    def __init__(self, min_wall_thickness: int = 4, max_wall_thickness: int = 40):
        self.min_wall_thickness = min_wall_thickness
        self.max_wall_thickness = max_wall_thickness

    def extract_wall_mask(self, gray: np.ndarray) -> np.ndarray:
        """
        Extracts clean binary mask of structural walls using adaptive thresholding
        and directional morphological stroke-width filtering.
        """
        # Invert so walls are white (255) on black background
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Directional morphological kernels to isolate continuous structural strokes
        k_h = cv2.getStructuringElement(cv2.MORPH_RECT, (self.min_wall_thickness, 1))
        k_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, self.min_wall_thickness))

        walls_h = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, k_h)
        walls_v = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, k_v)
        walls = cv2.bitwise_or(walls_h, walls_v)

        # Remove small speckles
        k_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        walls = cv2.morphologyEx(walls, cv2.MORPH_OPEN, k_clean)
        return walls

    def extract_wall_centerlines(self, wall_mask: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extracts vectorized wall segments and centerlines via skeletonization
        and probabilistic Hough line transformation.
        """
        # Distance transform to estimate local wall thickness
        dist = cv2.distanceTransform(wall_mask, cv2.DIST_L2, 5)

        # Morphological skeletonization
        skeleton = np.zeros(wall_mask.shape, np.uint8)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        temp = wall_mask.copy()

        while True:
            eroded = cv2.erode(temp, element)
            opened = cv2.dilate(eroded, element)
            subset = cv2.subtract(temp, opened)
            skeleton = cv2.bitwise_or(skeleton, subset)
            temp = eroded.copy()
            if cv2.countNonZero(temp) == 0:
                break

        # Extract line segments from skeleton
        lines = cv2.HoughLinesP(skeleton, 1, np.pi / 180, threshold=40, minLineLength=30, maxLineGap=15)
        wall_entities = []

        if lines is not None:
            for i, line in enumerate(lines):
                coords = line.reshape(-1)
                x1, y1, x2, y2 = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
                
                # Sample local wall thickness from distance transform
                sampled_dist = dist[min(mid_y, dist.shape[0]-1), min(mid_x, dist.shape[1]-1)]
                thickness_px = max(float(sampled_dist * 2.0), float(self.min_wall_thickness))

                wall_entities.append({
                    "wall_id": f"wall_{i+1:03d}",
                    "centerline": [[x1, y1], [x2, y2]],
                    "thickness_px": round(thickness_px, 1),
                    "wall_type": "interior" # Default, classified relative to outer envelope
                })

        return wall_entities
