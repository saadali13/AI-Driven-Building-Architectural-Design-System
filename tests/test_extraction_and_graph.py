"""
Unit tests for Phase 7 & 8:
Room Semantic Fusion, Spatial Relationship Graph Extraction, and Canonical Schema Integration.
"""

import pytest
from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    WallModel,
    OpeningModel,
    RoomModel,
    GraphEdgeModel
)
from extraction.rooms import RoomSemanticFuser
from extraction.relationships import SpatialRelationshipGraphExtractor


def test_room_semantic_fuser_and_v4_discipline():
    fuser = RoomSemanticFuser(default_scale_px_to_m=0.02)

    # 2 segmented rooms in pixels:
    # Room 1: (50, 50) to (250, 250) -> width 200px, height 200px -> in meters: 4m x 4m = 16 m2
    # Room 2: (250, 50) to (450, 250) -> width 200px, height 200px -> in meters: 4m x 4m = 16 m2
    seg_rooms = [
        {
            "room_id": "room_001",
            "polygon": [[50, 50], [250, 50], [250, 250], [50, 250], [50, 50]]
        },
        {
            "room_id": "room_002",
            "polygon": [[250, 50], [450, 50], [450, 250], [250, 250], [250, 50]]
        }
    ]

    # OCR text ONLY in room 1
    ocr_entries = [
        {
            "text": "BEDROOM",
            "corrected_text": "BEDROOM",
            "confidence": 0.95,
            "is_room_label": True,
            "room_category": "bedroom",
            "centroid": [150, 150]
        }
    ]

    # Dimension entry in room 2
    dim_entries = [
        {
            "raw_text": "13'x13'",
            "position": [350, 150]
        }
    ]

    fused = fuser.fuse_rooms(seg_rooms, ocr_entries, dim_entries, scale_px_to_m=0.02)

    assert len(fused) == 2

    r1 = next(r for r in fused if r.room_id == "room_001")
    r2 = next(r for r in fused if r.room_id == "room_002")

    # Room 1 assertions
    assert r1.room_type == "bedroom"
    assert r1.area_m2 == 16.0
    assert r1.confidence >= 0.85
    assert r1.is_habitable is True
    assert "ocr_text_label" in r1.evidence

    # Room 2 assertions: V4 Semantic Discipline
    assert r2.room_type == "unclassified_closed_region"
    assert r2.area_m2 == 16.0
    assert r2.confidence <= 0.60
    assert "associated_dimension" in r2.evidence


def test_spatial_relationship_graph_extractor():
    # Construct 3 rooms: Living Room, Kitchen, Bedroom
    # Room 1 (Living): [0, 0] to [5, 5] (area 25 m2)
    # Room 2 (Kitchen): [5.1, 0] to [9.1, 5] (adjacent to Living separated by 0.1m wall)
    # Room 3 (Bedroom): [0, 5.2] to [5, 9.2] (adjacent to Living separated by 0.2m wall)
    rooms = [
        RoomModel(
            room_id="room_living",
            room_type="living_room",
            room_name="Living Room",
            polygon=[[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]],
            area_m2=25.0,
            centroid=[2.5, 2.5],
            confidence=0.9
        ),
        RoomModel(
            room_id="room_kitchen",
            room_type="kitchen",
            room_name="Kitchen",
            polygon=[[5.1, 0], [9.1, 0], [9.1, 5], [5.1, 5], [5.1, 0]],
            area_m2=20.0,
            centroid=[7.1, 2.5],
            confidence=0.9
        ),
        RoomModel(
            room_id="room_bed",
            room_type="bedroom",
            room_name="Bedroom",
            polygon=[[0, 5.2], [5, 5.2], [5, 9.2], [0, 9.2], [0, 5.2]],
            area_m2=20.0,
            centroid=[2.5, 7.2],
            confidence=0.9
        )
    ]

    # Door opening between Living and Bedroom
    openings = [
        OpeningModel(
            opening_id="door_001",
            opening_type="door",
            position=[2.5, 5.1],
            width_m=0.9,
            connects_rooms=["room_living", "room_bed"]
        )
    ]

    extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.35)
    edges, metrics = extractor.build_graph(rooms, openings)

    assert len(edges) == 2, f"Expected 2 edges (1 door, 1 adjacency), got {len(edges)}"

    # Find the via_door edge
    door_edge = next((e for e in edges if e.relationship_type == "via_door"), None)
    assert door_edge is not None
    assert set([door_edge.source_room_id, door_edge.target_room_id]) == {"room_living", "room_bed"}

    # Find the adjacency edge (Living <-> Kitchen)
    adj_edge = next((e for e in edges if e.relationship_type == "adjacency"), None)
    assert adj_edge is not None
    assert set([adj_edge.source_room_id, adj_edge.target_room_id]) == {"room_living", "room_kitchen"}

    # Check metrics
    assert metrics["node_count"] == 3
    assert metrics["edge_count"] == 2
    assert metrics["is_connected"] is True


def test_canonical_floor_plan_serialization():
    plan = CanonicalFloorPlan(
        metadata=MetadataModel(
            plan_id="test_plan_001",
            source_type="raster_cv",
            scale_px_to_m=0.02
        ),
        boundary=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
        total_area_m2=100.0,
        rooms=[
            RoomModel(
                room_id="room_001",
                room_type="living_room",
                room_name="Main Living",
                polygon=[[0, 0], [6, 0], [6, 10], [0, 10], [0, 0]],
                area_m2=60.0,
                centroid=[3.0, 5.0]
            )
        ],
        walls=[
            WallModel(
                wall_id="wall_001",
                wall_type="exterior",
                centerline=[[0, 0], [10, 0]],
                thickness_m=0.25
            )
        ],
        openings=[
            OpeningModel(
                opening_id="door_001",
                opening_type="door",
                position=[3.0, 0.0],
                width_m=0.9
            )
        ]
    )

    # Validate JSON serialization & deserialization
    json_str = plan.to_json()
    reloaded = CanonicalFloorPlan.from_json(json_str)

    assert reloaded.metadata.plan_id == "test_plan_001"
    assert len(reloaded.rooms) == 1
    assert reloaded.rooms[0].area_m2 == 60.0
    assert len(reloaded.walls) == 1
