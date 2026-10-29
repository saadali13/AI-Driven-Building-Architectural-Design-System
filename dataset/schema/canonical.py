"""
Canonical Architectural Schema v1.0.
Single Source of Truth across:
- Computer Vision Raster Pipeline
- CAD / DXF Ingestion and Generation
- RAG Vector Indexing
- Procedural Blender 3D Solid Modeling
"""

from typing import Dict, List, Optional, Tuple, Any, Literal
from pydantic import BaseModel, Field
import json


class MetadataModel(BaseModel):
    plan_id: str
    source_type: Literal["raster_cv", "dxf_cad", "synthetic_generated", "ground_truth"]
    scale_px_to_m: Optional[float] = Field(default=None, description="Meters per pixel scale factor")
    unit: str = "m"
    north_angle_deg: float = 0.0
    floor_count: int = 1
    levels: List[int] = Field(default_factory=lambda: [0])
    wall_height_m: float = 2.80
    provenance: Dict[str, Any] = Field(default_factory=dict)


class WallModel(BaseModel):
    wall_id: str
    wall_type: Literal["exterior", "interior", "partition"] = "interior"
    centerline: List[List[float]] = Field(description="[[x1, y1], [x2, y2]] in meters")
    thickness_m: float = 0.20
    height_m: float = 2.80
    level_index: int = 0


class OpeningModel(BaseModel):
    opening_id: str
    opening_type: Literal["door", "window", "cased_opening"] = "door"
    position: List[float] = Field(description="[x, y] coordinates in meters")
    width_m: float = 0.90
    height_m: float = 2.10
    sill_height_m: float = 0.0  # 0.0 for doors, ~0.90 for windows
    connects_rooms: List[str] = Field(default_factory=list, description="IDs of connecting rooms")
    associated_wall_id: Optional[str] = None
    level_index: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoomModel(BaseModel):
    room_id: str
    room_type: str = Field(
        description="Standard architectural category: 'bedroom', 'bathroom', 'kitchen', 'living_room', 'dining_room', 'corridor', 'balcony', 'garage', 'unclassified_closed_region'"
    )
    room_name: str
    polygon: List[List[float]] = Field(description="Closed polygon ring [[x1, y1], ... [x1, y1]] in meters")
    area_m2: float
    centroid: List[float] = Field(description="[x, y] in meters")
    level_index: int = 0
    is_habitable: bool = True
    confidence: float = 1.0
    evidence: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdgeModel(BaseModel):
    source_room_id: str
    target_room_id: str
    relationship_type: Literal["via_door", "adjacency", "direct", "via_window"]
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalFloorPlan(BaseModel):
    metadata: MetadataModel
    boundary: List[List[float]] = Field(description="Closed outer building envelope [[x1, y1], ...] in meters")
    total_area_m2: float
    walls: List[WallModel] = Field(default_factory=list)
    openings: List[OpeningModel] = Field(default_factory=list)
    rooms: List[RoomModel] = Field(default_factory=list)
    graph_edges: List[GraphEdgeModel] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanonicalFloorPlan":
        return cls.model_validate(data)

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "CanonicalFloorPlan":
        return cls.model_validate_json(json_str)

    def get_room_by_id(self, room_id: str) -> Optional[RoomModel]:
        for r in self.rooms:
            if r.room_id == room_id:
                return r
        return None

    @property
    def floor_count(self) -> int:
        return self.metadata.floor_count

    @property
    def levels(self) -> List[int]:
        return self.metadata.levels


    def get_adjacent_rooms(self, room_id: str, rel_type: Optional[str] = None) -> List[str]:
        neighbors = []
        for edge in self.graph_edges:
            if rel_type is not None and edge.relationship_type != rel_type:
                continue
            if edge.source_room_id == room_id:
                neighbors.append(edge.target_room_id)
            elif edge.target_room_id == room_id:
                neighbors.append(edge.source_room_id)
        return list(set(neighbors))
