"""
Phase 7: Semantic Fusion and Room Entity Finalization.
Fuses segmented geometric room contours with OCR labels and dimension products.
Applies scale calibration (meters-per-pixel) to convert pixel spaces into real-world m2.
Strictly adheres to V4 Semantic Discipline:
- Polygons with verified room text -> target room category (confidence >= 0.80)
- Polygons with dimensions only -> unclassified space with dimension metadata (confidence ~0.60)
- Polygons without text or dimensions -> 'unclassified_closed_region' (confidence <= 0.40)
"""

from typing import Dict, List, Optional, Tuple, Any
from shapely.geometry import Polygon, Point
from dataset.schema.canonical import RoomModel


class RoomSemanticFuser:
    def __init__(self, default_scale_px_to_m: float = 0.02):
        # 0.02 m per px = 50 px per meter
        self.default_scale_px_to_m = default_scale_px_to_m

    def fuse_rooms(
        self,
        segmented_rooms: List[Dict[str, Any]],
        ocr_entries: List[Dict[str, Any]],
        dimension_entries: List[Dict[str, Any]],
        scale_px_to_m: Optional[float] = None
    ) -> List[RoomModel]:
        scale = scale_px_to_m if scale_px_to_m is not None else self.default_scale_px_to_m
        fused_rooms: List[RoomModel] = []

        for idx, s_room in enumerate(segmented_rooms):
            poly_px = s_room["polygon"]
            px_poly = Polygon(poly_px)
            if not px_poly.is_valid:
                px_poly = px_poly.buffer(0)

            # Convert coordinates to meters
            metric_coords = [[round(pt[0] * scale, 3), round(pt[1] * scale, 3)] for pt in poly_px]
            metric_poly = Polygon(metric_coords)
            area_m2 = round(metric_poly.area, 2)
            centroid_m = [round(metric_poly.centroid.x, 3), round(metric_poly.centroid.y, 3)]

            # Check point-in-polygon for OCR labels
            matched_ocr = None
            for entry in ocr_entries:
                pt = Point(entry["centroid"][0], entry["centroid"][1])
                if px_poly.contains(pt) and entry.get("is_room_label"):
                    matched_ocr = entry
                    break

            # Check point-in-polygon for dimension annotations
            matched_dim = None
            for dim in dimension_entries:
                if "position" in dim:
                    dim_pt = Point(dim["position"][0], dim["position"][1])
                    if px_poly.contains(dim_pt):
                        matched_dim = dim
                        break

            evidence = ["closed_polygon"]
            # Apply V4 Semantic Discipline
            if matched_ocr:
                room_type = matched_ocr["room_category"]
                room_name = matched_ocr["corrected_text"]
                confidence = float(matched_ocr.get("confidence", 0.85))
                evidence.append("ocr_text_label")
                if matched_dim:
                    evidence.append("associated_dimension")
            elif matched_dim:
                room_type = "unclassified_closed_region"
                dim_str = matched_dim.get("raw_text", "")
                room_name = f"Unclassified Space ({dim_str})"
                confidence = 0.55
                evidence.append("associated_dimension")
            else:
                # Strictly unclassified when zero text or fixtures exist
                room_type = "unclassified_closed_region"
                room_name = f"Unclassified Space {idx+1}"
                confidence = 0.35
                evidence.append("no_text_label")

            # Determine habitability
            non_habitable_types = {"bathroom", "corridor", "balcony", "garage", "unclassified_closed_region"}
            is_habitable = room_type not in non_habitable_types

            room_id = s_room.get("room_id", f"room_{idx+1:03d}")

            fused_rooms.append(RoomModel(
                room_id=room_id,
                room_type=room_type,
                room_name=room_name,
                polygon=metric_coords,
                area_m2=area_m2,
                centroid=centroid_m,
                level_index=0,
                is_habitable=is_habitable,
                confidence=confidence,
                evidence=evidence
            ))

        return fused_rooms
