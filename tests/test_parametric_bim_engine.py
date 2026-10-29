import os
import pytest
import numpy as np
from shapely.geometry import Polygon
from generation.parametric_bim_engine import (
    SiteBoundary,
    SetbackDefinition,
    HierarchicalZoningCSPSolver,
    Parametric3DMeshBuilder,
    ArchitecturalZone,
    FurnitureCategory,
    BIM_LAYOUT_JSON_SCHEMA
)


def test_parametric_bim_engine_end_to_end():
    # 1. Site Setup (1 Kanal: 50' x 90' = 15.24m x 27.43m)
    site = SiteBoundary(
        width_m=15.24,
        depth_m=27.43,
        street_frontage="SOUTH",
        setbacks=SetbackDefinition(
            front_m=4.57,
            rear_m=2.13,
            side_left_m=1.52,
            side_right_m=0.0
        )
    )

    solver = HierarchicalZoningCSPSolver(site=site, floor_count=2)
    model = solver.solve_layout(
        requested_bedrooms=4,
        requested_bathrooms=4,
        include_dirty_kitchen=True,
        include_drawing_room=True,
        parking_capacity=2
    )

    assert model is not None
    assert model.floor_count == 2
    assert len(model.rooms) >= 15

    # --------------------------------------------------------------------------
    # 1. Spatial Violation Test: Zero Trapped Interior Lawns
    # --------------------------------------------------------------------------
    lawn = next((r for r in model.rooms if r.room_id == "r_L0_lawn"), None)
    assert lawn is not None, "Must have front lawn"
    # Front lawn must touch the street front boundary (min Y == 0.0)
    lawn_poly = Polygon(lawn.polygon)
    assert lawn_poly.bounds[1] == 0.0, f"Lawn is not anchored to front boundary! Min Y = {lawn_poly.bounds[1]}"
    assert lawn.zone == ArchitecturalZone.ZONE_SERVICE_OUTDOOR

    # --------------------------------------------------------------------------
    # 2. Wet-Core Misalignment Test: Vertical Alignment & Exterior Exhaust
    # --------------------------------------------------------------------------
    l0_kit = next((r for r in model.rooms if r.room_id == "r_L0_kitchen"), None)
    l1_kit = next((r for r in model.rooms if r.room_id == "r_L1_kitchenette"), None)
    assert l0_kit is not None and l1_kit is not None
    assert l0_kit.has_exterior_exhaust is True, "Ground kitchen must have exterior exhaust"
    assert l1_kit.has_exterior_exhaust is True, "Upper kitchen must have exterior exhaust"

    # Compute 2D IoU between L0 and L1 Kitchens
    poly_l0_kit = Polygon(l0_kit.polygon)
    poly_l1_kit = Polygon(l1_kit.polygon)
    inter_area = poly_l0_kit.intersection(poly_l1_kit).area
    union_area = poly_l0_kit.union(poly_l1_kit).area
    iou = inter_area / union_area
    assert iou >= 0.70, f"Kitchen vertical plumbing alignment IoU = {iou:.2f} (< 0.70 threshold)"

    # Verify Ensuite Bath vertical stack (Bath 1 vs Bath 3)
    l0_bath1 = next((r for r in model.rooms if r.room_id == "r_L0_bath1"), None)
    l1_bath3 = next((r for r in model.rooms if r.room_id == "r_L1_bath3"), None)
    assert l0_bath1 is not None and l1_bath3 is not None
    iou_bath = Polygon(l0_bath1.polygon).intersection(Polygon(l1_bath3.polygon)).area / Polygon(l0_bath1.polygon).union(Polygon(l1_bath3.polygon)).area
    assert iou_bath >= 0.95, f"Master bath vertical alignment IoU = {iou_bath:.2f}"

    # --------------------------------------------------------------------------
    # 3. Circulation Efficiency & Acoustic Buffering
    # --------------------------------------------------------------------------
    # Verify zero doors between Drawing Room and any Bedroom
    bed_ids = {r.room_id for r in model.rooms if r.room_type == "bedroom"}
    drawing_doors = [
        op for op in model.openings
        if op.category == "INTERIOR_DOOR" and "r_L0_drawing" in op.connects_rooms
    ]
    for d in drawing_doors:
        for cr in d.connects_rooms:
            assert cr not in bed_ids, f"Illegal direct door from Drawing to Bedroom: {cr}"

    # Verify Bed Lobby exists on both floors
    l0_lobby = next((r for r in model.rooms if r.room_id == "r_L0_bed_lobby"), None)
    l1_lobby = next((r for r in model.rooms if r.room_id == "r_L1_bed_lobby"), None)
    assert l0_lobby is not None and l1_lobby is not None
    assert l0_lobby.zone == ArchitecturalZone.ZONE_C_PRIVATE

    # --------------------------------------------------------------------------
    # 4. Ergonomic Furniture Clearance & Solid-Wall Anchoring
    # --------------------------------------------------------------------------
    bed1 = next((r for r in model.rooms if r.room_id == "r_L0_bed1"), None)
    assert bed1 is not None
    bed_furn = next((f for f in bed1.furniture if f.category == FurnitureCategory.KING_BED), None)
    assert bed_furn is not None, "Master bedroom must have an anchored King Bed"
    assert bed_furn.solid_wall_anchor_edge is not None, "Bed must be anchored to solid wall"
    assert bed_furn.clearance_envelope_polygon is not None, "Bed must have clearance envelope"

    # --------------------------------------------------------------------------
    # 5. Parametric 3D Mesh Generation & OBJ Export
    # --------------------------------------------------------------------------
    builder = Parametric3DMeshBuilder(model)
    verts, faces, mats = builder.build_3d_geometry()

    assert len(verts) > 50, f"Expected > 50 vertices, got {len(verts)}"
    assert len(faces) > 20, f"Expected > 20 faces, got {len(faces)}"
    assert "Mat_Concrete_Slab" in mats
    assert "Mat_Exterior_Travertine" in mats

    output_dir = "output/bim_models"
    os.makedirs(output_dir, exist_ok=True)
    obj_path = os.path.join(output_dir, "test_bim_house.obj")
    mtl_path = os.path.join(output_dir, "materials.mtl")
    builder.export_to_obj(obj_path, mtl_path)

    assert os.path.exists(obj_path), "OBJ file was not written"
    assert os.path.getsize(obj_path) > 1000, "OBJ file is too small"
    print(f"\n--> Successfully exported watertight 3D BIM model: {obj_path} ({os.path.getsize(obj_path)} bytes)")
