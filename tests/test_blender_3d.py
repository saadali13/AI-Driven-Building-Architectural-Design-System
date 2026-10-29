"""
Unit tests for Phase 13 & 14:
Procedural 3D Blender Model Generation and Perspective Rendering.
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
from three_d.blender_generator import Blender3DGenerator


@pytest.fixture
def simple_3d_test_plan():
    return CanonicalFloorPlan(
        metadata=MetadataModel(plan_id="blender_unit_test", source_type="synthetic_generated", wall_height_m=2.80),
        boundary=[[0, 0], [8, 0], [8, 6], [0, 6], [0, 0]],
        total_area_m2=48.0,
        walls=[
            WallModel(wall_id="w_ext_1", wall_type="exterior", centerline=[[0, 0], [8, 0]], thickness_m=0.25),
            WallModel(wall_id="w_ext_2", wall_type="exterior", centerline=[[8, 0], [8, 6]], thickness_m=0.25),
            WallModel(wall_id="w_ext_3", wall_type="exterior", centerline=[[8, 6], [0, 6]], thickness_m=0.25),
            WallModel(wall_id="w_ext_4", wall_type="exterior", centerline=[[0, 6], [0, 0]], thickness_m=0.25),
            WallModel(wall_id="w_int_1", wall_type="interior", centerline=[[4, 0], [4, 6]], thickness_m=0.15),
        ],
        openings=[
            OpeningModel(opening_id="door_01", opening_type="door", position=[4.0, 3.0], width_m=0.9, height_m=2.1),
            OpeningModel(opening_id="wind_01", opening_type="window", position=[2.0, 6.0], width_m=1.2, height_m=1.2, sill_height_m=0.90)
        ],
        rooms=[
            RoomModel(room_id="r1", room_type="living_room", room_name="Living", polygon=[[0,0],[4,0],[4,6],[0,6],[0,0]], area_m2=24.0, centroid=[2,3]),
            RoomModel(room_id="r2", room_type="bedroom", room_name="Bedroom", polygon=[[4,0],[8,0],[8,6],[4,6],[4,0]], area_m2=24.0, centroid=[6,3])
        ]
    )


def test_blender_availability_and_generation(simple_3d_test_plan, tmp_path):
    gen = Blender3DGenerator()
    if not gen.is_blender_available():
        pytest.skip("Blender 5.1 is not installed or accessible on this system.")

    blend_file = str(tmp_path / "model.blend")
    png_file = str(tmp_path / "render.png")

    res = gen.generate_3d_model(
        plan=simple_3d_test_plan,
        output_blend_path=blend_file,
        output_render_path=png_file,
        timeout_seconds=45.0
    )

    assert res["success"] is True, f"Blender generation failed: {res.get('stderr')}"
    assert os.path.exists(blend_file)
    assert os.path.getsize(blend_file) > 1000, "Blend file should be non-empty"

    assert os.path.exists(png_file)
    assert os.path.getsize(png_file) > 1000, "Rendered PNG should be non-empty"

    # Verify PNG header
    with open(png_file, "rb") as f:
        header = f.read(8)
    assert header == b'\x89PNG\r\n\x1a\n', "Output file must be a valid PNG image"
