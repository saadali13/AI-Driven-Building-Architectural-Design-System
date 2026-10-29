"""
Generates high-resolution 2D architectural blueprint images (PNG),
layered AutoCAD drawings (DXF), and 3D Wavefront models (OBJ/MTL)
for the 10 Marla luxury & production multi-level residential layouts.
Outputs directly to the project's 'output/' directory.
"""

import os
import sys

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from generation.parametric_bim_engine import (
    HierarchicalZoningCSPSolver,
    SiteBoundary,
    SetbackDefinition,
    Parametric3DMeshBuilder
)
from cad.dxf_generator import DXFGenerator
from generation.visualizer import FloorPlanVisualizer


def generate_all_visuals():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_base = os.path.join(workspace_dir, "output")

    # =========================================================================
    # 1. 10 MARLA PRODUCTION 3-STORY LAYOUT (10'-0" Front, 5'-0" Rear Setbacks)
    # =========================================================================
    print("--- Generating 10 Marla Production 3-Story Residence Visuals ---")
    site_prod = SiteBoundary(
        width_m=10.67,  # 35'-0"
        depth_m=19.81,  # 65'-0"
        street_frontage="NORTH",
        setbacks=SetbackDefinition(front_m=3.05, rear_m=1.52, side_left_m=0.0, side_right_m=0.0)
    )
    solver_prod = HierarchicalZoningCSPSolver(site=site_prod, floor_count=3)
    model_prod = solver_prod.solve_10_marla_production_3story(parking_capacity=2)
    canon_prod = model_prod.to_canonical_floorplan()

    dir_prod = os.path.join(output_base, "10_marla_production_3story")
    os.makedirs(dir_prod, exist_ok=True)

    # 2D Blueprint PNGs
    rendered_prod = FloorPlanVisualizer.render_all_floors(canon_prod, dir_prod)
    for name, path in rendered_prod.items():
        print(f"  [PNG] {name} -> {path}")

    # CAD DXF
    dxf_gen = DXFGenerator()
    dxf_prod_path = os.path.join(dir_prod, "10_marla_production_coordinated.dxf")
    dxf_gen.export_composite_dxf(canon_prod, dxf_prod_path)
    print(f"  [DXF] Coordinated AutoCAD Drawing -> {dxf_prod_path}")

    # 3D OBJ & MTL
    mesh_prod = Parametric3DMeshBuilder(model_prod)
    obj_prod_path = os.path.join(dir_prod, "10_marla_production_3d.obj")
    mtl_prod_path = os.path.join(dir_prod, "10_marla_production_3d.mtl")
    mesh_prod.export_to_obj(obj_prod_path, mtl_prod_path)
    print(f"  [3D] Wavefront OBJ Mesh -> {obj_prod_path}")

    # =========================================================================
    # 2. 10 MARLA LUXURY 3-STORY LAYOUT (15'-0" Front, 6'-6" Rear Setbacks)
    # =========================================================================
    print("\n--- Generating 10 Marla Luxury 3-Story Residence Visuals ---")
    site_lux = SiteBoundary(
        width_m=10.67,  # 35'-0"
        depth_m=19.81,  # 65'-0"
        street_frontage="SOUTH",
        setbacks=SetbackDefinition(front_m=4.57, rear_m=1.98, side_left_m=0.0, side_right_m=0.0)
    )
    solver_lux = HierarchicalZoningCSPSolver(site=site_lux, floor_count=3)
    model_lux = solver_lux.solve_10_marla_luxury_layout(parking_capacity=2)
    canon_lux = model_lux.to_canonical_floorplan()

    dir_lux = os.path.join(output_base, "10_marla_luxury_residence")
    os.makedirs(dir_lux, exist_ok=True)

    # 2D Blueprint PNGs
    rendered_lux = FloorPlanVisualizer.render_all_floors(canon_lux, dir_lux)
    for name, path in rendered_lux.items():
        print(f"  [PNG] {name} -> {path}")

    # CAD DXF
    dxf_lux_path = os.path.join(dir_lux, "10_marla_luxury_coordinated.dxf")
    dxf_gen.export_composite_dxf(canon_lux, dxf_lux_path)
    print(f"  [DXF] Coordinated AutoCAD Drawing -> {dxf_lux_path}")

    # 3D OBJ & MTL
    mesh_lux = Parametric3DMeshBuilder(model_lux)
    obj_lux_path = os.path.join(dir_lux, "10_marla_luxury_3d.obj")
    mtl_lux_path = os.path.join(dir_lux, "10_marla_luxury_3d.mtl")
    mesh_lux.export_to_obj(obj_lux_path, mtl_lux_path)
    print(f"  [3D] Wavefront OBJ Mesh -> {obj_lux_path}")

    print("\nAll architectural visuals generated successfully!")


if __name__ == "__main__":
    generate_all_visuals()
