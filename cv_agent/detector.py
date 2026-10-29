"""
Stage B: Architectural Element Detection Engine.

Extracts:
1. External & internal walls as discrete linear segments, thicknesses, and corner junctions.
2. Watertight room polygons with scale-adaptive area filtering (eliminating micro-fragment hallucination).
3. Doors and door swing arcs verified by wall opening jambs and hinge proximity.
4. Windows along exterior wall perimeters.
5. Staircases with step rungs and flight direction.
6. OCR text labels (room names, dimensions, annotations) associated with room chambers.
7. Spatial adjacency graph.
"""

import os
import re
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
from skimage.morphology import skeletonize
import easyocr
from cv_agent.dimension_engine import ArchitecturalDimensionEngine

DIMENSION_PATTERN = re.compile(
    r"(\d{1,2}\s*['’\-]\s*\d{0,2}\s*[\"”]?)\s*[\*xX×]\s*(\d{1,2}\s*['’\-]\s*\d{0,2}\s*[\"”]?)"
)

ROOM_TYPE_KEYWORDS = {
    "bedroom": ["bedroom", "bed", "master", "suite", "bed1", "bed2", "bed3", "bed4", "mbr", "mbed"],
    "bathroom": ["bathroom", "bath", "toilet", "wc", "washroom", "powder", "t&b", "c.t", "a.t", "d/bath", "dibath", "dress"],
    "kitchen": ["kitchen", "kit", "dirty kitchen", "scullery", "pantry", "cooking"],
    "living_room": ["tv lounge", "lounge", "living", "family", "hall", "sitting", "lobby"],
    "drawing_room": ["drawing", "formal", "guest room", "salon", "parlor", "d.r", "dr"],
    "dining_room": ["dining", "dinning", "dining area"],
    "car_porch": ["porch", "car porch", "garage", "car", "parking", "driveway"],
    "ots": ["ots", "shaft", "duct", "open to sky", "lightwell", "patio", "lawn", "court", "terrace", "open", "wash area"],
    "circulation": ["stairs", "staircase", "corridor", "passage", "entry", "foyer", "verandah", "veranda"]
}

_GLOBAL_OCR_READER: Optional[easyocr.Reader] = None


def get_ocr_reader(languages: Optional[List[str]] = None) -> easyocr.Reader:
    """Singleton getter for EasyOCR reader to eliminate redundant model loading."""
    global _GLOBAL_OCR_READER
    if _GLOBAL_OCR_READER is None:
        langs = languages or ["en"]
        _GLOBAL_OCR_READER = easyocr.Reader(langs, gpu=False, verbose=False)
    return _GLOBAL_OCR_READER


class ArchitecturalElementDetector:
    """
    Detects structural and architectural components from preprocessed blueprints.
    """

    def __init__(self, languages: Optional[List[str]] = None):
        self.languages = languages or ["en"]
        self._reader: Optional[easyocr.Reader] = None

    @property
    def reader(self) -> easyocr.Reader:
        if self._reader is None:
            self._reader = get_ocr_reader(self.languages)
        return self._reader

    @staticmethod
    def classify_room_text(text: str) -> str:
        tl = text.lower()
        for cat, kw_list in ROOM_TYPE_KEYWORDS.items():
            if any(kw in tl for kw in kw_list):
                return cat
        return "room"

    def detect_walls_and_thickness(
        self,
        wall_mask: np.ndarray,
        text_annotations: Optional[List[Dict[str, Any]]] = None,
        rooms: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extracts discrete wall segments (horizontal and vertical), wall contours,
        intersection corners, and measures wall thickness via distance transform.
        Suppresses OCR text strokes, gates on the architectural building envelope,
        and merges collinear segments along true structural axes.
        """
        h, w = wall_mask.shape[:2]
        dist_transform = cv2.distanceTransform(wall_mask, cv2.DIST_L2, 5)

        # True skeletonization using scikit-image medial thinning
        skel = skeletonize(wall_mask > 0)
        thinned = (skel.astype(np.uint8) * 255)

        # Measure wall thickness strictly along medial skeleton ridge
        skel_dist = dist_transform[skel]
        if len(skel_dist) > 0:
            avg_half_width = float(np.median(skel_dist))
        else:
            non_zero_dist = dist_transform[dist_transform > 0]
            avg_half_width = float(np.median(non_zero_dist)) * 2.0 if len(non_zero_dist) > 0 else 3.0
        wall_thickness_px = max(3.0, round(avg_half_width * 2.0, 1))

        # Clean skeleton: suppress text boxes and filter outside building envelope
        clean_skel = thinned.copy()
        if text_annotations:
            for t in text_annotations:
                tx1, ty1, tx2, ty2 = t.get("bbox_px", [0, 0, 0, 0])
                cv2.rectangle(
                    clean_skel,
                    (max(0, tx1 - 3), max(0, ty1 - 3)),
                    (min(w, tx2 + 3), min(h, ty2 + 3)),
                    0, -1
                )

        envelope_box = None
        if rooms and len(rooms) > 0:
            rx1 = [r["bbox_px"][0] for r in rooms if r.get("area_px", 0) > 2500]
            ry1 = [r["bbox_px"][1] for r in rooms if r.get("area_px", 0) > 2500]
            rx2 = [r["bbox_px"][2] for r in rooms if r.get("area_px", 0) > 2500]
            ry2 = [r["bbox_px"][3] for r in rooms if r.get("area_px", 0) > 2500]
            if rx1 and ry1 and rx2 and ry2:
                envelope_box = (min(rx1), min(ry1), max(rx2), max(ry2))
                ebx1, eby1, ebx2, eby2 = envelope_box
                clean_skel[:max(0, eby1 - 25), :] = 0
                clean_skel[min(h, eby2 + 25):, :] = 0
                clean_skel[:, :max(0, ebx1 - 25)] = 0
                clean_skel[:, min(w, ebx2 + 25):] = 0

        clean_skel[dist_transform < 1.0] = 0

        # Probabilistic Hough Transform on clean medial skeleton
        raw_lines = cv2.HoughLinesP(
            clean_skel, 1, np.pi / 180, threshold=26, minLineLength=20, maxLineGap=12
        )
        if raw_lines is None:
            raw_lines = cv2.HoughLinesP(
                thinned, 1, np.pi / 180, threshold=26, minLineLength=18, maxLineGap=12
            )

        discrete_walls = []
        if raw_lines is not None:
            h_segs = []
            v_segs = []
            diag_segs = []
            for line in raw_lines:
                coords = line.flatten()
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords[:4]
                    dx = abs(x2 - x1)
                    dy = abs(y2 - y1)
                    length = float(np.hypot(dx, dy))
                    if length < 18.0:
                        continue
                    if dy <= 4 and dx >= 20:
                        h_segs.append([min(x1, x2), int((y1 + y2) / 2), max(x1, x2), int((y1 + y2) / 2)])
                    elif dx <= 4 and dy >= 20:
                        v_segs.append([int((x1 + x2) / 2), min(y1, y2), int((x1 + x2) / 2), max(y1, y2)])
                    else:
                        diag_segs.append({
                            "start_px": [int(x1), int(y1)],
                            "end_px": [int(x2), int(y2)],
                            "length_px": round(length, 1),
                            "orientation": "diagonal"
                        })

            # Robust collinear horizontal merging
            merged_h = []
            h_segs.sort(key=lambda s: s[1])
            h_groups = []
            for s in h_segs:
                placed = False
                for grp in h_groups:
                    if abs(s[1] - grp[0][1]) <= 6:
                        grp.append(s)
                        placed = True
                        break
                if not placed:
                    h_groups.append([s])

            for grp in h_groups:
                avg_y = int(sum(s[1] for s in grp) / len(grp))
                grp.sort(key=lambda s: s[0])
                curr_x1, curr_x2 = grp[0][0], grp[0][2]
                for s in grp[1:]:
                    if s[0] <= curr_x2 + 35:
                        curr_x2 = max(curr_x2, s[2])
                    else:
                        if curr_x2 - curr_x1 >= 24:
                            merged_h.append([curr_x1, avg_y, curr_x2, avg_y])
                        curr_x1, curr_x2 = s[0], s[2]
                if curr_x2 - curr_x1 >= 24:
                    merged_h.append([curr_x1, avg_y, curr_x2, avg_y])

            # Robust collinear vertical merging
            merged_v = []
            v_segs.sort(key=lambda s: s[0])
            v_groups = []
            for s in v_segs:
                placed = False
                for grp in v_groups:
                    if abs(s[0] - grp[0][0]) <= 6:
                        grp.append(s)
                        placed = True
                        break
                if not placed:
                    v_groups.append([s])

            for grp in v_groups:
                avg_x = int(sum(s[0] for s in grp) / len(grp))
                grp.sort(key=lambda s: s[1])
                curr_y1, curr_y2 = grp[0][1], grp[0][3]
                for s in grp[1:]:
                    if s[1] <= curr_y2 + 35:
                        curr_y2 = max(curr_y2, s[3])
                    else:
                        if curr_y2 - curr_y1 >= 24:
                            merged_v.append([avg_x, curr_y1, avg_x, curr_y2])
                        curr_y1, curr_y2 = s[1], s[3]
                if curr_y2 - curr_y1 >= 24:
                    merged_v.append([avg_x, curr_y1, avg_x, curr_y2])

            wall_idx = 1
            if envelope_box:
                bx1, by1, bx2, by2 = envelope_box
            else:
                bx1, by1, bx2, by2 = int(w * 0.12), int(h * 0.12), int(w * 0.88), int(h * 0.88)

            for s in merged_h:
                w_len = float(s[2] - s[0])
                is_ext = abs(s[1] - by1) <= 22 or abs(s[1] - by2) <= 22 or s[0] <= bx1 + 15 or s[2] >= bx2 - 15
                discrete_walls.append({
                    "wall_id": f"wall_{wall_idx}",
                    "start_px": [int(s[0]), int(s[1])],
                    "end_px": [int(s[2]), int(s[1])],
                    "length_px": round(w_len, 1),
                    "thickness_px": max(2.0, wall_thickness_px),
                    "orientation": "horizontal",
                    "type": "exterior" if is_ext else "interior"
                })
                wall_idx += 1

            for s in merged_v:
                w_len = float(s[3] - s[1])
                is_ext = abs(s[0] - bx1) <= 22 or abs(s[0] - bx2) <= 22 or s[1] <= by1 + 15 or s[3] >= by2 - 15
                discrete_walls.append({
                    "wall_id": f"wall_{wall_idx}",
                    "start_px": [int(s[0]), int(s[1])],
                    "end_px": [int(s[0]), int(s[3])],
                    "length_px": round(w_len, 1),
                    "thickness_px": max(2.0, wall_thickness_px),
                    "orientation": "vertical",
                    "type": "exterior" if is_ext else "interior"
                })
                wall_idx += 1

            for d in diag_segs:
                discrete_walls.append({
                    "wall_id": f"wall_{wall_idx}",
                    "start_px": d["start_px"],
                    "end_px": d["end_px"],
                    "length_px": d["length_px"],
                    "thickness_px": max(2.0, wall_thickness_px),
                    "orientation": "diagonal",
                    "type": "interior"
                })
                wall_idx += 1

        # Wall polygon contours
        contours, _ = cv2.findContours(wall_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        wall_polygons = []
        for cnt in contours:
            if cv2.contourArea(cnt) > 20:
                epsilon = 0.01 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                if len(approx) >= 2:
                    wall_polygons.append(approx.reshape(-1, 2).tolist())

        # Wall intersection corners
        corners = cv2.goodFeaturesToTrack(wall_mask, maxCorners=140, qualityLevel=0.06, minDistance=12)
        corner_pts = []
        if corners is not None:
            corner_pts = [[round(float(c[0][0]), 1), round(float(c[0][1]), 1)] for c in corners]

        return {
            "wall_thickness_px": max(2.0, wall_thickness_px),
            "wall_segments": discrete_walls,
            "wall_count": max(len(discrete_walls), len(wall_polygons)),
            "wall_contours": wall_polygons,
            "intersection_corners": corner_pts,
            "exterior_walls_count": sum(1 for w in discrete_walls if w.get("type") == "exterior"),
            "interior_walls_count": sum(1 for w in discrete_walls if w.get("type") == "interior")
        }

    def detect_rooms(self, wall_mask: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extracts genuine architectural room chambers using scale-adaptive wall sealing,
        exterior flood-fill separation, and connected component analysis.
        """
        h, w = wall_mask.shape[:2]
        img_area = w * h

        # Scale-adaptive morphological wall sealing to bridge door openings (20px to 55px)
        bridge_w = max(48, int(w * 0.055))
        bridge_h = max(48, int(h * 0.055))

        h_close = cv2.morphologyEx(wall_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (bridge_w, 3)))
        v_close = cv2.morphologyEx(wall_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, bridge_h)))
        cross_close = cv2.morphologyEx(wall_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)))
        sealed_walls = cv2.bitwise_or(cv2.bitwise_or(h_close, v_close), cross_close)

        # Flood-fill from outer canvas border to strictly separate exterior background from building interior
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1:-1, 1:-1] = sealed_walls
        flood_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        flood_val = 128
        cv2.floodFill(padded, flood_mask, (0, 0), flood_val)
        exterior = (padded[1:-1, 1:-1] == flood_val)

        # Internal chambers are non-wall and non-exterior pixels
        chambers_mask = np.zeros((h, w), dtype=np.uint8)
        chambers_mask[(sealed_walls == 0) & (~exterior)] = 255

        # Slight morphological opening to disconnect hairline touches
        open_k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        chambers_mask = cv2.morphologyEx(chambers_mask, cv2.MORPH_OPEN, open_k)

        # Connected component analysis for watertight chambers
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(chambers_mask, connectivity=8)

        # Scale-adaptive minimum room area: preserves genuine powder rooms while suppressing tile hatching & sub-room artifacts
        min_room_area = max(1600.0, img_area * 0.005)
        max_room_area = img_area * 0.48

        rooms = []
        for i in range(1, num_labels):
            area = float(stats[i, cv2.CC_STAT_AREA])
            if not (min_room_area <= area <= max_room_area):
                continue

            x = int(stats[i, cv2.CC_STAT_LEFT])
            y = int(stats[i, cv2.CC_STAT_TOP])
            rw = int(stats[i, cv2.CC_STAT_WIDTH])
            rh = int(stats[i, cv2.CC_STAT_HEIGHT])

            # Aspect ratio check: avoid extreme hairline slivers
            aspect = rw / float(max(1, rh))
            if aspect < 0.12 or aspect > 8.0:
                continue

            # Minimum dimension requirement
            min_dim = max(18, int(min(w, h) * 0.025))
            if rw < min_dim or rh < min_dim:
                continue

            # Extract chamber polygon contour
            comp_mask = (labels == i).astype(np.uint8) * 255
            cnts, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not cnts:
                continue
            cnt = max(cnts, key=cv2.contourArea)

            epsilon = 0.012 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            pts = approx.reshape(-1, 2).tolist()

            if len(pts) >= 3:
                poly = Polygon(pts)
                if poly.is_valid and poly.area >= (min_room_area * 0.6):
                    cx, cy = centroids[i]
                    rooms.append({
                        "room_id": f"room_{len(rooms) + 1}",
                        "polygon_px": pts,
                        "bbox_px": [x, y, x + rw, y + rh],
                        "centroid_px": [round(cx, 1), round(cy, 1)],
                        "area_px": round(area, 1),
                        "aspect_ratio": round(aspect, 2),
                        "assigned_label": "Room",
                        "assigned_category": "room",
                        "dimension_text": ""
                    })

        # Sort rooms by area descending for consistent deterministic ordering
        rooms.sort(key=lambda r: r["area_px"], reverse=True)
        for i, r in enumerate(rooms, start=1):
            r["room_id"] = f"room_{i}"

        # Compute topological room adjacency graph
        for i, r1 in enumerate(rooms):
            r1["adjacent_room_ids"] = []
            poly1 = Polygon(r1["polygon_px"])
            for j, r2 in enumerate(rooms):
                if i != j:
                    poly2 = Polygon(r2["polygon_px"])
                    # Check distance between room chamber boundaries (shared wall <= 18px)
                    if poly1.distance(poly2) <= 18.0:
                        r1["adjacent_room_ids"].append(r2["room_id"])

        return rooms

    def detect_doors_and_swings(
        self,
        image_bgr: np.ndarray,
        wall_mask: np.ndarray,
        rooms: Optional[List[Dict[str, Any]]] = None,
        discrete_walls: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects genuine architectural doors, wall openings, and quarter-circle swing arcs.
        Validates genuine quadrant arc curvature, door leaf alignment, and wall-jamb attachment,
        strictly suppressing spurious circle hallucinations.
        """
        h, w = wall_mask.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 40, 120)
        arcs_only = cv2.bitwise_and(edges, cv2.bitwise_not(wall_mask))

        min_r = max(18, int(min(w, h) * 0.016))
        max_r = min(56, int(min(w, h) * 0.055))

        candidates = []

        # Strategy 1: Sensitive Hough Circles with strict 90-degree quadrant arc support verification
        circles = cv2.HoughCircles(
            arcs_only, cv2.HOUGH_GRADIENT, dp=1.2, minDist=28,
            param1=80, param2=28, minRadius=min_r, maxRadius=max_r
        )

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for cx, cy, r in circles:
                if not (r <= cx < w - r and r <= cy < h - r):
                    continue

                # Verify 90-degree quadrant arc curvature
                quadrant_support = []
                for q in range(4):
                    t_start = q * (np.pi / 2.0)
                    t_end = (q + 1) * (np.pi / 2.0)
                    angles = np.linspace(t_start, t_end, 20)
                    xs = np.clip((cx + r * np.cos(angles)).astype(int), 0, w - 1)
                    ys = np.clip((cy + r * np.sin(angles)).astype(int), 0, h - 1)
                    edge_hits = np.count_nonzero(arcs_only[ys, xs] > 0)
                    quadrant_support.append(edge_hits / 20.0)

                best_support = max(quadrant_support)
                best_q = int(np.argmax(quadrant_support))

                if best_support >= 0.36:
                    # Must touch a wall jamb at hinge or arc endpoint
                    chk_y1, chk_y2 = max(0, cy - 12), min(h, cy + 12)
                    chk_x1, chk_x2 = max(0, cx - 12), min(w, cx + 12)
                    if np.count_nonzero(wall_mask[chk_y1:chk_y2, chk_x1:chk_x2]) >= 4:
                        candidates.append({
                            "cx": int(cx),
                            "cy": int(cy),
                            "r": int(r),
                            "quadrant": best_q,
                            "confidence": round(float(best_support), 2),
                            "detection_method": "hough_quadrant"
                        })

        # Strategy 2: Direct curved contour arc analysis
        cnts, _ = cv2.findContours(arcs_only, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        for cnt in cnts:
            arc_len = cv2.arcLength(cnt, False)
            if 28 <= arc_len <= 110:
                (cx_f, cy_f), r_f = cv2.minEnclosingCircle(cnt)
                cx, cy, r = int(cx_f), int(cy_f), int(r_f)
                if min_r <= r <= max_r and 0 <= cx < w and 0 <= cy < h:
                    angles = np.arctan2([p[0][1] - cy for p in cnt], [p[0][0] - cx for p in cnt])
                    span = np.ptp(angles)
                    if 1.0 <= span <= 2.2: # ~60 to 125 degrees
                        p_start = cnt[0][0]
                        p_end = cnt[-1][0]
                        s_y1, s_y2 = max(0, p_start[1] - 8), min(h, p_start[1] + 8)
                        s_x1, s_x2 = max(0, p_start[0] - 8), min(w, p_start[0] + 8)
                        e_y1, e_y2 = max(0, p_end[1] - 8), min(h, p_end[1] + 8)
                        e_x1, e_x2 = max(0, p_end[0] - 8), min(w, p_end[0] + 8)
                        if (np.count_nonzero(wall_mask[s_y1:s_y2, s_x1:s_x2]) >= 2 or
                            np.count_nonzero(wall_mask[e_y1:e_y2, e_x1:e_x2]) >= 2):
                            candidates.append({
                                "cx": int(cx),
                                "cy": int(cy),
                                "r": int(r),
                                "quadrant": 0,
                                "confidence": 0.85,
                                "detection_method": "contour_arc"
                            })

        # Sort by confidence descending and deduplicate
        candidates.sort(key=lambda c: c["confidence"], reverse=True)
        seen = []
        doors = []
        for c in candidates:
            # Exclude title block / outer sheet margins
            if c["cy"] < 90 or c["cy"] > h - 30 or c["cx"] < 30 or c["cx"] > w - 30:
                continue

            if any(np.hypot(c["cx"] - sx, c["cy"] - sy) < 32 for sx, sy in seen):
                continue

            # Find nearest wall segment for attachment
            attached_wall_id = None
            if discrete_walls:
                min_dist = float("inf")
                for w_seg in discrete_walls:
                    sp = w_seg.get("start_px", [0, 0])
                    ep = w_seg.get("end_px", [0, 0])
                    p1 = np.array(sp)
                    p2 = np.array(ep)
                    p3 = np.array([c["cx"], c["cy"]])
                    l2 = np.sum((p2 - p1) ** 2)
                    if l2 == 0:
                        dist = np.linalg.norm(p3 - p1)
                    else:
                        t = max(0, min(1, np.dot(p3 - p1, p2 - p1) / l2))
                        proj = p1 + t * (p2 - p1)
                        dist = np.linalg.norm(p3 - proj)
                    if dist < min_dist:
                        min_dist = dist
                        if dist <= 24.0:
                            attached_wall_id = w_seg.get("wall_id")

                # Genuine doors must be attached to a structural wall segment
                if min_dist > 26.0:
                    continue

            seen.append((c["cx"], c["cy"]))
            doors.append({
                "door_id": f"door_{len(doors) + 1}",
                "position_px": [c["cx"], c["cy"]],
                "hinge_px": [c["cx"], c["cy"]],
                "swing_radius_px": c["r"],
                "width_px": c["r"],
                "swing_quadrant": c["quadrant"],
                "swing_angle_deg": c["quadrant"] * 90.0,
                "confidence": c["confidence"],
                "attached_wall_id": attached_wall_id,
                "type": "swing_door"
            })

        return doors

    def detect_windows(
        self,
        image_bgr: np.ndarray,
        wall_mask: np.ndarray,
        discrete_walls: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects genuine architectural windows along exterior building walls.
        Leverages parallel line pair detection (double-line fenestration) and exterior wall attachment,
        suppressing text serifs, dimension ticks, and title block lines.
        """
        h, w = wall_mask.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 130)
        non_wall_edges = cv2.bitwise_and(edges, cv2.bitwise_not(wall_mask))

        min_len = max(22, int(min(w, h) * 0.022))
        max_len = int(min(w, h) * 0.22)

        lines = cv2.HoughLinesP(
            non_wall_edges, 1, np.pi / 180, threshold=28, minLineLength=min_len, maxLineGap=4
        )

        windows = []
        if lines is not None:
            # Exclude title block at top/bottom and sheet margins
            top_bound = 90
            bottom_bound = h - 40
            left_bound = 35
            right_bound = w - 35

            segments = [l.flatten()[:4] for l in lines]
            h_lines = []
            v_lines = []
            for s in segments:
                x1, y1, x2, y2 = s
                dx, dy = abs(x2 - x1), abs(y2 - y1)
                length = float(np.hypot(dx, dy))
                if length < min_len or length > max_len:
                    continue
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                if not (left_bound <= mx <= right_bound and top_bound <= my <= bottom_bound):
                    continue
                if dy <= 2 and dx >= min_len:
                    h_lines.append(s)
                elif dx <= 2 and dy >= min_len:
                    v_lines.append(s)

            candidates = []

            # 1. Detect parallel line pairs (standard 2D architectural window symbol)
            for i, l1 in enumerate(h_lines):
                y1 = (l1[1] + l1[3]) / 2.0
                x1_min, x1_max = min(l1[0], l1[2]), max(l1[0], l1[2])
                for j in range(i + 1, len(h_lines)):
                    l2 = h_lines[j]
                    y2 = (l2[1] + l2[3]) / 2.0
                    if 2 <= abs(y1 - y2) <= 8:
                        x2_min, x2_max = min(l2[0], l2[2]), max(l2[0], l2[2])
                        overlap = min(x1_max, x2_max) - max(x1_min, x2_min)
                        if overlap >= 18:
                            cx = round((x1_min + x2_max) / 2.0, 1)
                            cy = round((y1 + y2) / 2.0, 1)
                            w_len = round(float(max(x1_max, x2_max) - min(x1_min, x2_min)), 1)
                            candidates.append({
                                "start_px": [int(min(x1_min, x2_min)), int((y1 + y2) / 2)],
                                "end_px": [int(max(x1_max, x2_max)), int((y1 + y2) / 2)],
                                "center_px": [cx, cy],
                                "length_px": w_len,
                                "orientation": "horizontal",
                                "confidence": 0.90
                            })

            for i, l1 in enumerate(v_lines):
                x1 = (l1[0] + l1[2]) / 2.0
                y1_min, y1_max = min(l1[1], l1[3]), max(l1[1], l1[3])
                for j in range(i + 1, len(v_lines)):
                    l2 = v_lines[j]
                    x2 = (l2[0] + l2[2]) / 2.0
                    if 2 <= abs(x1 - x2) <= 8:
                        y2_min, y2_max = min(l2[1], l2[3]), max(l2[1], l2[3])
                        overlap = min(y1_max, y2_max) - max(y1_min, y2_min)
                        if overlap >= 18:
                            cx = round((x1 + x2) / 2.0, 1)
                            cy = round((y1_min + y2_max) / 2.0, 1)
                            w_len = round(float(max(y1_max, y2_max) - min(y1_min, y2_min)), 1)
                            candidates.append({
                                "start_px": [int((x1 + x2) / 2), int(min(y1_min, y2_min))],
                                "end_px": [int((x1 + x2) / 2), int(max(y1_max, y2_max))],
                                "center_px": [cx, cy],
                                "length_px": w_len,
                                "orientation": "vertical",
                                "confidence": 0.90
                            })

            # 2. If discrete exterior walls are available, match single line fenestrations
            if discrete_walls and len(candidates) < 4:
                ext_walls = [w_seg for w_seg in discrete_walls if w_seg.get("type") == "exterior"]
                for s in h_lines + v_lines:
                    x1, y1, x2, y2 = s
                    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    orient = "horizontal" if abs(y2 - y1) <= 2 else "vertical"
                    for ew in ext_walls:
                        if ew.get("orientation") != orient:
                            continue
                        sp, ep = np.array(ew["start_px"]), np.array(ew["end_px"])
                        p3 = np.array([mx, my])
                        l2 = np.sum((ep - sp) ** 2)
                        if l2 == 0:
                            dist = np.linalg.norm(p3 - sp)
                        else:
                            t = max(0, min(1, np.dot(p3 - sp, ep - sp) / l2))
                            dist = np.linalg.norm(p3 - (sp + t * (ep - sp)))
                        if dist <= 14.0:
                            candidates.append({
                                "start_px": [int(x1), int(y1)],
                                "end_px": [int(x2), int(y2)],
                                "center_px": [round(mx, 1), round(my, 1)],
                                "length_px": round(float(np.hypot(x2 - x1, y2 - y1)), 1),
                                "orientation": orient,
                                "confidence": 0.82
                            })
                            break

            # Deduplicate collinear windows within 38px
            deduped = []
            seen = []
            for win in candidates:
                cx, cy = win["center_px"]
                if not any(np.hypot(cx - sx, cy - sy) < 38 for sx, sy in seen):
                    seen.append((cx, cy))
                    win["window_id"] = f"window_{len(deduped) + 1}"
                    deduped.append(win)

            windows = deduped

        return windows

    def detect_stairs(
        self,
        image_bgr: np.ndarray,
        text_annotations: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects staircases by finding localized spatial clusters of closely spaced parallel step rungs.
        Suppresses false positives from text strokes and merges multi-flight dog-leg staircases.
        """
        h, w = image_bgr.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 40, 130)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 26, minLineLength=14, maxLineGap=4)

        if lines is None or len(lines) < 4:
            return []

        segments = [line.flatten() for line in lines if len(line.flatten()) >= 4]

        # 1. Horizontal step rungs (step treads)
        h_rungs = [s for s in segments if abs(s[1] - s[3]) <= 3 and 14 <= abs(s[0] - s[2]) <= 160]
        h_rungs.sort(key=lambda s: (s[1] + s[3]) / 2.0)

        clusters = []
        curr = []
        for s in h_rungs:
            sy = (s[1] + s[3]) / 2.0
            sx_min, sx_max = min(s[0], s[2]), max(s[0], s[2])
            if not curr:
                curr.append(s)
            else:
                prev_s = curr[-1]
                prev_y = (prev_s[1] + prev_s[3]) / 2.0
                prev_x_min, prev_x_max = min(prev_s[0], prev_s[2]), max(prev_s[0], prev_s[2])
                dy = abs(sy - prev_y)
                overlap = max(0, min(sx_max, prev_x_max) - max(sx_min, prev_x_min))
                if 3 <= dy <= 22 and overlap >= 10:
                    curr.append(s)
                elif dy > 22:
                    if len(curr) >= 4:
                        clusters.append((curr, "vertical_flight"))
                    curr = [s]
        if len(curr) >= 4:
            clusters.append((curr, "vertical_flight"))

        # 2. Vertical step rungs
        v_rungs = [s for s in segments if abs(s[0] - s[2]) <= 3 and 14 <= abs(s[1] - s[3]) <= 160]
        v_rungs.sort(key=lambda s: (s[0] + s[2]) / 2.0)
        curr_v = []
        for s in v_rungs:
            sx = (s[0] + s[2]) / 2.0
            sy_min, sy_max = min(s[1], s[3]), max(s[1], s[3])
            if not curr_v:
                curr_v.append(s)
            else:
                prev_s = curr_v[-1]
                prev_x = (prev_s[0] + prev_s[2]) / 2.0
                prev_y_min, prev_y_max = min(prev_s[1], prev_s[3]), max(prev_s[1], prev_s[3])
                dx = abs(sx - prev_x)
                overlap = max(0, min(sy_max, prev_y_max) - max(sy_min, prev_y_min))
                if 3 <= dx <= 22 and overlap >= 10:
                    curr_v.append(s)
                elif dx > 22:
                    if len(curr_v) >= 4:
                        clusters.append((curr_v, "horizontal_flight"))
                    curr_v = [s]
        if len(curr_v) >= 4:
            clusters.append((curr_v, "horizontal_flight"))

        # Check for presence of staircase text
        stair_labels = []
        if text_annotations:
            for t in text_annotations:
                tc = t.get("text", "").upper()
                if any(k in tc for k in ("UP", "DN", "STAIR", "STEPS")):
                    stair_labels.append(t)
        has_stair_text = len(stair_labels) > 0

        stair_candidates = []
        for cl, orient in clusters:
            xs = [s[0] for s in cl] + [s[2] for s in cl]
            ys = [s[1] for s in cl] + [s[3] for s in cl]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            bw, bh = x2 - x1, y2 - y1
            area = bw * bh

            # Discard clusters in title block or outer sheet borders
            if y1 < 90 or y2 > h - 40 or x1 < 30 or x2 > w - 30:
                continue

            # Plausible staircase dimensions
            if not (18 <= bw <= (w * 0.40) and 18 <= bh <= (h * 0.40) and (400 <= area <= (w * h * 0.08))):
                continue

            conf = 0.85
            near_label = False
            if has_stair_text:
                for t in stair_labels:
                    tx, ty = t.get("center_px", [0, 0])
                    if x1 - 100 <= tx <= x2 + 100 and y1 - 100 <= ty <= y2 + 100:
                        conf = 0.95
                        near_label = True
                        break

            # If staircase text is present, suppress unrelated clusters far from the stair label
            if has_stair_text and not near_label and (len(cl) < 8 or area < 2200):
                continue

            # If no stair text, require substantial dimensions
            if not has_stair_text and (len(cl) < 6 or area < 1600):
                continue

            stair_candidates.append({
                "bbox_px": [int(x1), int(y1), int(x2), int(y2)],
                "approx_steps": len(cl),
                "flight_orientation": orient,
                "confidence": conf
            })

        # Merge adjacent multi-flight staircases (e.g. dog-leg flights within 75px)
        merged_stairs = []
        used = set()
        for i, s1 in enumerate(stair_candidates):
            if i in used:
                continue
            bx1, by1, bx2, by2 = s1["bbox_px"]
            steps = s1["approx_steps"]
            conf = s1["confidence"]
            orient = s1["flight_orientation"]
            for j in range(i + 1, len(stair_candidates)):
                if j in used:
                    continue
                s2 = stair_candidates[j]
                ox1, oy1, ox2, oy2 = s2["bbox_px"]
                # Check proximity / landing gap <= 75px
                if not (bx2 < ox1 - 75 or bx1 > ox2 + 75 or by2 < oy1 - 75 or by1 > oy2 + 75):
                    bx1 = min(bx1, ox1)
                    by1 = min(by1, oy1)
                    bx2 = max(bx2, ox2)
                    by2 = max(by2, oy2)
                    steps += s2["approx_steps"]
                    conf = max(conf, s2["confidence"])
                    used.add(j)

            merged_stairs.append({
                "stair_id": f"stair_{len(merged_stairs) + 1}",
                "bbox_px": [bx1, by1, bx2, by2],
                "approx_steps": steps,
                "flight_orientation": orient,
                "confidence": conf
            })

        return merged_stairs

    def detect_text_and_dimensions(self, image_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs OCR to detect text strings, room labels, and dimensional annotations.
        """
        results = self.reader.readtext(image_bgr)
        text_annotations = []

        for bbox, text, conf in results:
            text_clean = text.strip()
            if len(text_clean) < 2 or conf < 0.20:
                continue

            pts = [[int(pt[0]), int(pt[1])] for pt in bbox]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)

            dim_meta = ArchitecturalDimensionEngine.parse_dimension_string(text_clean)
            is_dim = dim_meta is not None or bool(DIMENSION_PATTERN.search(text_clean))
            category = self.classify_room_text(text_clean)
            norm_text = dim_meta["normalized_text"] if dim_meta else text_clean

            text_annotations.append({
                "text": text_clean,
                "normalized_text": norm_text,
                "confidence": round(float(conf), 2),
                "bbox_px": [min(xs), min(ys), max(xs), max(ys)],
                "center_px": [round(cx, 1), round(cy, 1)],
                "is_dimension": is_dim,
                "dimension_meta": dim_meta,
                "room_category": category
            })

        return text_annotations

    def match_labels_to_rooms(
        self,
        rooms: List[Dict[str, Any]],
        text_annotations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Associates detected text labels and dimensions with the corresponding room polygon.
        """
        for r in rooms:
            poly = Polygon(r["polygon_px"])
            for t in text_annotations:
                pt = Point(t["center_px"])
                if poly.contains(pt) or poly.distance(pt) < 18.0:
                    if t["is_dimension"]:
                        r["dimension_text"] = t["text"]
                        d_m = t.get("dimension_meta")
                        if d_m:
                            r["dimension_meta"] = d_m
                            r["normalized_width_m"] = d_m.get("width_m")
                            r["normalized_length_m"] = d_m.get("length_m")
                            r["normalized_width_ft"] = d_m.get("width_ft")
                            r["normalized_length_ft"] = d_m.get("length_ft")
                            r["real_world_area_sqm"] = d_m.get("area_sqm")
                            r["real_world_area_sqft"] = d_m.get("area_sqft")
                    elif t["room_category"] != "room" or r["assigned_label"] == "Room":
                        r["assigned_label"] = t["text"]
                        r["assigned_category"] = t["room_category"]

        # Filter out unlabelled tiny sub-room niches (< 5000 px and label is generic "Room")
        valid_rooms = []
        for r in rooms:
            if r["assigned_label"] == "Room" and not r.get("dimension_text") and r["area_px"] < 5000.0 and len(rooms) > 4:
                continue
            valid_rooms.append(r)

        for i, r in enumerate(valid_rooms, start=1):
            r["room_id"] = f"room_{i}"

        return valid_rooms

    def build_adjacency_graph(self, rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Computes spatial adjacency between rooms that share wall boundaries.
        """
        adjacencies = []
        n = len(rooms)
        for i in range(n):
            p1 = Polygon(rooms[i]["polygon_px"])
            for j in range(i + 1, n):
                p2 = Polygon(rooms[j]["polygon_px"])
                if p1.distance(p2) <= 18.0:
                    adjacencies.append({
                        "room_1": rooms[i]["room_id"],
                        "room_2": rooms[j]["room_id"],
                        "relationship": "shares_wall"
                    })
        return adjacencies

    def extract_all(self, image_bgr: np.ndarray, wall_mask: np.ndarray) -> Dict[str, Any]:
        """
        Executes full Stage B architectural element detection.
        """
        h, w = image_bgr.shape[:2]

        text_items = self.detect_text_and_dimensions(image_bgr)
        raw_rooms = self.detect_rooms(wall_mask)
        walls = self.detect_walls_and_thickness(wall_mask, text_annotations=text_items, rooms=raw_rooms)
        wall_segs = walls.get("wall_segments", [])
        doors = self.detect_doors_and_swings(image_bgr, wall_mask, raw_rooms, discrete_walls=wall_segs)
        windows = self.detect_windows(image_bgr, wall_mask, wall_segs)
        stairs = self.detect_stairs(image_bgr, text_annotations=text_items)

        labeled_rooms = self.match_labels_to_rooms(raw_rooms, text_items)
        adjacency = self.build_adjacency_graph(labeled_rooms)

        # Normalize coordinates [0.0 - 1.0]
        normalized_rooms = []
        for r in labeled_rooms:
            norm_pts = [[round(p[0] / w, 4), round(p[1] / h, 4)] for p in r["polygon_px"]]
            norm_bbox = [round(r["bbox_px"][0] / w, 4), round(r["bbox_px"][1] / h, 4),
                         round(r["bbox_px"][2] / w, 4), round(r["bbox_px"][3] / h, 4)]
            normalized_rooms.append({
                **r,
                "polygon_normalized": norm_pts,
                "bbox_normalized": norm_bbox
            })

        return {
            "image_size": [w, h],
            "walls": walls,
            "rooms": normalized_rooms,
            "doors": doors,
            "windows": windows,
            "stairs": stairs,
            "text_annotations": text_items,
            "adjacency": adjacency
        }
