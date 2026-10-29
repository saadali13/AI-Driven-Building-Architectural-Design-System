"""
Unit tests for CAD / DXF Parser and Exporter.
Verifies:
1. DXF Generation produces valid file with standard layers.
2. DXF Parser ingests the exported DXF back into CanonicalFloorPlan.
3. Geometric properties (room count, wall count, area) are preserved across the round-trip.
"""

import os
import pytest
from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    WallModel,
    OpeningModel,
    RoomModel,
    GraphEdgeModel
)
from cad.dxf_generator import DXFGenerator
from cad.parser import DXFParser


@pytest.fixture
def sample_canonical_plan():
    return CanonicalFloorPlan(
        metadata=MetadataModel(
            plan_id="roundtrip_test_plan",
            source_type="synthetic_generated",
            unit="m"
        ),
        boundary=[[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]],
        total_area_m2=80.0,
        walls=[
            # Exterior envelope
            WallModel(wall_id="wall_ext_01", wall_type="exterior", centerline=[[0, 0], [10, 0]], thickness_m=0.25),
            WallModel(wall_id="wall_ext_02", wall_type="exterior", centerline=[[10, 0], [10, 8]], thickness_m=0.25),
            WallModel(wall_id="wall_ext_03", wall_type="exterior", centerline=[[10, 8], [0, 8]], thickness_m=0.25),
            WallModel(wall_id="wall_ext_04", wall_type="exterior", centerline=[[0, 8], [0, 0]], thickness_m=0.25),
            # Interior dividing wall
            WallModel(wall_id="wall_int_01", wall_type="interior", centerline=[[5, 0], [5, 8]], thickness_m=0.15),
        ],
        openings=[
            OpeningModel(opening_id="door_01", opening_type="door", position=[5.0, 4.0], width_m=0.9, connects_rooms=["room_001", "room_002"]),
            OpeningModel(opening_id="wind_01", opening_type="window", position=[2.5, 8.0], width_m=1.2)
        ],
        rooms=[
            RoomModel(
                room_id="room_001",
                room_type="living_room",
                room_name="Living Room",
                polygon=[[0, 0], [5, 0], [5, 8], [0, 8], [0, 0]],
                area_m2=40.0,
                centroid=[2.5, 4.0]
            ),
            RoomModel(
                room_id="room_002",
                room_type="bedroom",
                room_name="Master Bedroom",
                polygon=[[5, 0], [10, 0], [10, 8], [5, 8], [5, 0]],
                area_m2=40.0,
                centroid=[7.5, 4.0]
            )
        ]
    )


def test_dxf_export_and_parse_roundtrip(sample_canonical_plan, tmp_path):
    output_dxf = str(tmp_path / "test_export.dxf")

    # 1. Export canonical plan to DXF
    generator = DXFGenerator()
    generated_file = generator.export_dxf(sample_canonical_plan, output_dxf)
    assert os.path.exists(generated_file)
    assert os.path.getsize(generated_file) > 500

    # 2. Ingest exported DXF using DXFParser
    parser = DXFParser(unit_scale=1.0)
    parsed_plan = parser.parse_dxf(generated_file)

    # 3. Verify structure
    assert len(parsed_plan.walls) == 5
    assert len(parsed_plan.rooms) == 2

    # Check room classifications preserved via text labels
    r_types = [r.room_type for r in parsed_plan.rooms]
    assert "living_room" in r_types
    assert "bedroom" in r_types

    # Total area preserved within 1%
    assert abs(parsed_plan.total_area_m2 - 80.0) < 1.0
