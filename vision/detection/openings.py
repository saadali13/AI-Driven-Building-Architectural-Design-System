"""
Phase 5: Architectural Opening Detection (Doors and Windows).
Detects door swing arcs, wall gap openings, and exterior windows.
Preserves opening coordinates and jamb endpoints for dual-path
temporary closure and spatial connectivity modeling.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional


class OpeningDetector:
    def __init__(self, min_door_width_px: int = 15, max_door_width_px: int = 100):
        self.min_door_width_px = min_door_width_px
        self.max_door_width_px = max_door_width_px

    def detect_door_swings(self, gray: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects circular door swing arcs using Hough gradient circle detection
        and contour curvature analysis.
        """
        # Door swing arcs are typically thin single lines
        edges = cv2.Canny(gray, 30, 100)
        
        # Detect arcs with radii corresponding to typical door widths (e.g. 20px to 80px)
        circles = cv2.HoughCircles(
            edges,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=30,
            param1=80,
            param2=25,
            minRadius=self.min_door_width_px,
            maxRadius=self.max_door_width_px
        )

        doors = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i, c in enumerate(circles[0, :]):
                cx, cy, r = int(c[0]), int(c[1]), int(c[2])
                doors.append({
                    "opening_id": f"door_swing_{i+1:03d}",
                    "type": "door",
                    "position": [cx, cy],
                    "radius_px": r,
                    "width_px": r,
                    "confidence": 0.85
                })

        return doors

    def detect_wall_gap_openings(self, wall_mask: np.ndarray) -> List[Dict[str, Any]]:
        """
        Identifies doorway gaps along wall centerlines where walls terminate abruptly
        facing an opposing wall endpoint.
        Returns jamb endpoints suitable for virtual threshold bridging.
        """
        # Detect wall line endpoints using corner Harris or morphological hit-or-miss
        corners = cv2.cornerHarris(wall_mask, blockSize=3, ksize=3, k=0.04)
        corners = cv2.dilate(corners, None)
        
        # Threshold to find corner/endpoint candidate coordinates
        endpoint_mask = corners > (0.01 * corners.max())
        y_pts, x_pts = np.where(endpoint_mask)
        endpoints = list(zip(x_pts, y_pts))

        # Cluster endpoints into pairs separated by doorway width
        openings = []
        visited = set()

        for i in range(len(endpoints)):
            if i in visited:
                continue
            p1 = np.array(endpoints[i])
            for j in range(i + 1, len(endpoints)):
                if j in visited:
                    continue
                p2 = np.array(endpoints[j])
                dist = np.linalg.norm(p1 - p2)

                # Check if distance matches standard doorway opening in pixels
                if self.min_door_width_px <= dist <= self.max_door_width_px:
                    # Check if midpoint lies in empty space (gap between walls)
                    mid_pt = ((p1 + p2) / 2.0).astype(int)
                    if 0 <= mid_pt[1] < wall_mask.shape[0] and 0 <= mid_pt[0] < wall_mask.shape[1]:
                        if wall_mask[mid_pt[1], mid_pt[0]] == 0: # Empty gap
                            visited.add(i)
                            visited.add(j)
                            openings.append({
                                "opening_id": f"door_gap_{len(openings)+1:03d}",
                                "type": "door",
                                "position": [int(mid_pt[0]), int(mid_pt[1])],
                                "jamb_endpoints": [p1.tolist(), p2.tolist()],
                                "width_px": round(float(dist), 1),
                                "confidence": 0.80
                            })
                            break

        return openings
