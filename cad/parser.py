"""
Phase 9: AutoCAD DXF Parser for Canonical Architectural Ingestion.
Parses standard AIA-layered DXF files into CanonicalFloorPlan:
- 'A-WALL*' -> WallModel
- 'A-DOOR*' -> OpeningModel (door)
- 'A-GLAZ*' / 'A-WIND*' -> OpeningModel (window)
- 'A-AREA*' / 'A-FLOR*' -> RoomModel
- 'A-ANNO-TEXT*' -> OCR/Text labels
- 'A-ANNO-DIMS*' -> Dimensions
"""

import os
from typing import Dict, List, Optional, Tuple, Any
import ezdxf
from shapely.geometry import Polygon, LineString, Point
from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    WallModel,
    OpeningModel,
    RoomModel,
    GraphEdgeModel
)
from extraction.relationships import SpatialRelationshipGraphExtractor


class DXFParser:
    def __init__(self, unit_scale: float = 1.0):
        """unit_scale: Multiplier to convert DXF units to meters (e.g. 0.001 if DXF in mm, 1.0 if meters, 0.0254 if inches)"""
        self.unit_scale = unit_scale

    def parse_dxf(self, file_path: str) -> CanonicalFloorPlan:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        plan_id = os.path.splitext(os.path.basename(file_path))[0]
        walls: List[WallModel] = []
        openings: List[OpeningModel] = []
        rooms: List[RoomModel] = []
        texts: List[Dict[str, Any]] = []

        # 1. Parse text entities
        for entity in msp.query("TEXT MTEXT"):
            layer = entity.dxf.layer.upper()
            if entity.dxftype() == "TEXT":
                txt = entity.dxf.text
                pos = [entity.dxf.insert.x * self.unit_scale, entity.dxf.insert.y * self.unit_scale]
            else: # MTEXT
                txt = entity.plain_text()
                pos = [entity.dxf.insert.x * self.unit_scale, entity.dxf.insert.y * self.unit_scale]
            
            if txt.strip():
                texts.append({
                    "text": txt.strip(),
                    "position": pos,
                    "layer": layer
                })

        # 2. Parse walls (LINE, LWPOLYLINE, POLYLINE)
        wall_idx = 1
        for entity in msp.query("LINE LWPOLYLINE POLYLINE"):
            layer = entity.dxf.layer.upper()
            if "WALL" in layer:
                wall_type = "exterior" if "EXT" in layer else "interior"
                if entity.dxftype() == "LINE":
                    start = [entity.dxf.start.x * self.unit_scale, entity.dxf.start.y * self.unit_scale]
                    end = [entity.dxf.end.x * self.unit_scale, entity.dxf.end.y * self.unit_scale]
                    walls.append(WallModel(
                        wall_id=f"wall_{wall_idx:03d}",
                        wall_type=wall_type,
                        centerline=[start, end],
                        thickness_m=0.25 if wall_type == "exterior" else 0.15
                    ))
                    wall_idx += 1
                elif entity.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                    pts = [[p[0] * self.unit_scale, p[1] * self.unit_scale] for p in entity.get_points()]
                    for k in range(len(pts) - 1):
                        walls.append(WallModel(
                            wall_id=f"wall_{wall_idx:03d}",
                            wall_type=wall_type,
                            centerline=[pts[k], pts[k+1]],
                            thickness_m=0.25 if wall_type == "exterior" else 0.15
                        ))
                        wall_idx += 1

        # 3. Parse openings (DOOR, WIND, GLAZ)
        opening_idx = 1
        for entity in msp.query("LINE CIRCLE ARC INSERT LWPOLYLINE"):
            layer = entity.dxf.layer.upper()
            is_door = "DOOR" in layer
            is_wind = "WIND" in layer or "GLAZ" in layer
            if is_door or is_wind:
                op_type = "door" if is_door else "window"
                if entity.dxftype() == "LINE":
                    start = [entity.dxf.start.x * self.unit_scale, entity.dxf.start.y * self.unit_scale]
                    end = [entity.dxf.end.x * self.unit_scale, entity.dxf.end.y * self.unit_scale]
                    mid = [(start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0]
                    width = ((start[0] - end[0])**2 + (start[1] - end[1])**2)**0.5
                    openings.append(OpeningModel(
                        opening_id=f"{op_type}_{opening_idx:03d}",
                        opening_type=op_type,
                        position=mid,
                        width_m=round(width, 2),
                        sill_height_m=0.0 if is_door else 0.90
                    ))
                    opening_idx += 1
                elif entity.dxftype() in ("CIRCLE", "ARC"):
                    center = [entity.dxf.center.x * self.unit_scale, entity.dxf.center.y * self.unit_scale]
                    r = entity.dxf.radius * self.unit_scale
                    openings.append(OpeningModel(
                        opening_id=f"{op_type}_{opening_idx:03d}",
                        opening_type=op_type,
                        position=center,
                        width_m=round(r, 2),
                        sill_height_m=0.0 if is_door else 0.90
                    ))
                    opening_idx += 1

        # 4. Parse closed room boundaries (A-AREA, A-FLOR, or closed LWPOLYLINE)
        room_idx = 1
        for entity in msp.query("LWPOLYLINE POLYLINE"):
            layer = entity.dxf.layer.upper()
            if "AREA" in layer or "FLOR" in layer or "ROOM" in layer:
                if entity.is_closed:
                    pts = [[p[0] * self.unit_scale, p[1] * self.unit_scale] for p in entity.get_points()]
                    if len(pts) >= 3:
                        if pts[0] != pts[-1]:
                            pts.append(pts[0])
                        poly = Polygon(pts)
                        if poly.is_valid and poly.area > 1.0:
                            centroid = [round(poly.centroid.x, 2), round(poly.centroid.y, 2)]
                            
                            # Match text label inside room polygon
                            matched_text = None
                            for t in texts:
                                pt = Point(t["position"][0], t["position"][1])
                                if poly.contains(pt):
                                    matched_text = t["text"]
                                    break

                            name = matched_text if matched_text else f"Room {room_idx}"
                            rtype = self._categorize_room_name(name)

                            rooms.append(RoomModel(
                                room_id=f"room_{room_idx:03d}",
                                room_type=rtype,
                                room_name=name,
                                polygon=pts,
                                area_m2=round(poly.area, 2),
                                centroid=centroid,
                                confidence=0.95 if matched_text else 0.50,
                                evidence=["dxf_closed_polyline"] + (["dxf_text_label"] if matched_text else ["no_text_label"])
                            ))
                            room_idx += 1

        # Calculate building boundary and total area
        if rooms:
            all_polys = [Polygon(r.polygon) for r in rooms if Polygon(r.polygon).is_valid]
            from shapely.ops import unary_union
            merged = unary_union(all_polys)
            total_area = round(sum(r.area_m2 for r in rooms), 2)
            if hasattr(merged, 'exterior'):
                boundary = [list(pt) for pt in merged.exterior.coords]
            else:
                boundary = [r.polygon[0] for r in rooms]
        else:
            boundary = [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]
            total_area = 100.0

        # Build graph edges
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(rooms, openings)

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="dxf_cad",
                unit="m"
            ),
            boundary=boundary,
            total_area_m2=total_area,
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )

    @staticmethod
    def _categorize_room_name(name: str) -> str:
        s = name.upper()
        if "BED" in s:
            return "bedroom"
        if "BATH" in s or "TOILET" in s or "WC" in s:
            return "bathroom"
        if "KIT" in s:
            return "kitchen"
        if "LIV" in s or "HALL" in s or "LOUNGE" in s:
            return "living_room"
        if "DIN" in s:
            return "dining_room"
        if "CORR" in s or "HALLWAY" in s or "PASS" in s:
            return "corridor"
        if "BALC" in s or "TERR" in s:
            return "balcony"
        if "GAR" in s:
            return "garage"
        return "unclassified_closed_region"
