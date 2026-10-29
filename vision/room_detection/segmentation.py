"""
Phase 6: Multi-Signal Room Segmentation and Geometry Snapping Engine.
Implements door-aware dual-path processing:
1. Applies temporary virtual threshold closure across doorway jambs STRICTLY
   during distance-transform / seeded Watershed calculation to prevent room leakage.
2. Seeds Watershed using verified interior OCR room text centroids.
3. Simplifies extracted room contours into orthogonal rectilinear Shapely polygons.
4. Preserves V4 semantic discipline: unlabelled enclosed regions are classified
   as 'unclassified_closed_region' (NEVER assumed to be bedrooms/baths).
5. Permanently links door openings to connecting room pairs for spatial graph generation.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Polygon, Point


class RoomSegmentor:
    def __init__(self, min_room_area_px: int = 1000, simplify_tolerance_px: float = 2.0):
        self.min_room_area_px = min_room_area_px
        self.simplify_tolerance_px = simplify_tolerance_px

    def segment_rooms(
        self,
        wall_mask: np.ndarray,
        door_openings: List[Dict[str, Any]],
        ocr_entries: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Executes multi-signal door-aware room segmentation.
        Returns:
            rooms: List of validated room entities with polygons, areas, and V4 semantic tags.
            doors: List of door entities linked to their connected room IDs.
        """
        h, w = wall_mask.shape[:2]

        # 1. Dual-Path: Create temporary closure mask
        temp_closure_mask = wall_mask.copy()
        
        # Bridge doorway jamb gaps strictly on the temporary segmentation mask
        for door in door_openings:
            jambs = door.get("jamb_endpoints")
            if jambs and len(jambs) == 2:
                p1 = (int(jambs[0][0]), int(jambs[0][1]))
                p2 = (int(jambs[1][0]), int(jambs[1][1]))
                cv2.line(temp_closure_mask, p1, p2, 255, thickness=5)

        # 2. Invert closed wall mask to obtain room interior spaces
        inv_mask = cv2.bitwise_not(temp_closure_mask)

        # 3. Distance transform on interior spaces
        dist_transform = cv2.distanceTransform(inv_mask, cv2.DIST_L2, 5)

        # 4. Prepare Watershed markers
        markers = np.zeros(wall_mask.shape, dtype=np.int32)
        marker_id = 1
        marker_to_ocr = {}

        # Seed markers with verified OCR room text centroids
        for entry in ocr_entries:
            cx, cy = int(entry["centroid"][0]), int(entry["centroid"][1])
            if 0 <= cy < h and 0 <= cx < w:
                if inv_mask[cy, cx] > 0 and dist_transform[cy, cx] > 5:
                    # Place a small seed circle at text centroid
                    cv2.circle(markers, (cx, cy), 5, marker_id, -1)
                    marker_to_ocr[marker_id] = entry
                    marker_id += 1

        # Also find local maxima in distance transform for unlabelled rooms
        _, sure_fg = cv2.threshold(dist_transform, 0.3 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(sure_fg)

        for j in range(1, num_labels):
            cx, cy = int(centroids[j][0]), int(centroids[j][1])
            if markers[cy, cx] == 0 and inv_mask[cy, cx] > 0 and stats[j][cv2.CC_STAT_AREA] > 50:
                cv2.circle(markers, (cx, cy), 3, marker_id, -1)
                marker_id += 1

        # If no seeds placed (e.g. clean vector plan), use connected components on inv_mask
        if marker_id == 1:
            num_cc, cc_labels, cc_stats, _ = cv2.connectedComponentsWithStats(inv_mask)
            for k in range(1, num_cc):
                if cc_stats[k][cv2.CC_STAT_AREA] > self.min_room_area_px:
                    markers[cc_labels == k] = marker_id
                    marker_id += 1

        # Run Watershed
        color_src = cv2.cvtColor(wall_mask, cv2.COLOR_GRAY2BGR)
        cv2.watershed(color_src, markers)

        # 5. Extract room polygons from markers
        room_entities = []
        shapely_polygons = {}

        for m_id in range(1, marker_id):
            room_mask = np.uint8(markers == m_id)
            contours, _ = cv2.findContours(room_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue

            largest_cnt = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_cnt)
            # Filter out tiny noise or the outer canvas frame
            if area < self.min_room_area_px or area > (w * h * 0.75):
                continue

            # Simplify contour with Douglas-Peucker to orthogonalize boundaries
            pts = largest_cnt.reshape(-1, 2).tolist()
            if len(pts) < 4:
                continue
            # Ensure closed ring
            if pts[0] != pts[-1]:
                pts.append(pts[0])

            poly = Polygon(pts)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty or poly.area < self.min_room_area_px:
                continue

            simplified_poly = poly.simplify(self.simplify_tolerance_px, preserve_topology=True)
            if not simplified_poly.is_valid or simplified_poly.is_empty:
                simplified_poly = poly

            room_id = f"room_{len(room_entities)+1:03d}"
            shapely_polygons[room_id] = simplified_poly

            # V4 Semantic Discipline: Check if seed had OCR label
            ocr_match = marker_to_ocr.get(m_id)
            if ocr_match and ocr_match.get("is_room_label"):
                room_type = ocr_match["room_category"]
                room_name = ocr_match["corrected_text"]
                conf = ocr_match["confidence"]
                evidence = ["closed_boundary", "ocr_text_label"]
            else:
                # Check point-in-polygon for any OCR text
                matched_ocr = None
                for entry in ocr_entries:
                    pt = Point(entry["centroid"][0], entry["centroid"][1])
                    if simplified_poly.contains(pt) and entry.get("is_room_label"):
                        matched_ocr = entry
                        break

                if matched_ocr:
                    room_type = matched_ocr["room_category"]
                    room_name = matched_ocr["corrected_text"]
                    conf = matched_ocr["confidence"]
                    evidence = ["closed_boundary", "ocr_text_label"]
                else:
                    # STRICT V4 RULE: Enclosed area with zero text is UNCLASSIFIED
                    room_type = "unclassified_closed_region"
                    room_name = f"Unclassified Space {len(room_entities)+1}"
                    conf = 0.40
                    evidence = ["closed_boundary", "no_text_label"]

            exterior_coords = [list(pt) for pt in simplified_poly.exterior.coords]
            centroid = [round(simplified_poly.centroid.x, 1), round(simplified_poly.centroid.y, 1)]

            room_entities.append({
                "room_id": room_id,
                "type": room_type,
                "name": room_name,
                "confidence": conf,
                "evidence": evidence,
                "polygon": exterior_coords,
                "area_px": round(simplified_poly.area, 1),
                "centroid": centroid
            })

        # 6. Link door openings to room pairs
        doors_linked = []
        for door in door_openings:
            d_pos = door["position"]
            d_pt = Point(d_pos[0], d_pos[1])
            connected_rooms = []

            # A door connects rooms whose polygons are within door width radius
            search_dist = door.get("width_px", 40.0) * 1.2
            for r_id, r_poly in shapely_polygons.items():
                if r_poly.distance(d_pt) <= search_dist:
                    connected_rooms.append(r_id)

            door_rec = dict(door)
            door_rec["connects_rooms"] = connected_rooms[:2] # Up to 2 rooms
            doors_linked.append(door_rec)

        return room_entities, doors_linked
