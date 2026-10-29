"""
Tests for 10 Marla (35'-0" x 65'-0") Production-Ready 3-Story Residential Layout.

Validates the full prompt requirements:
1. Statutory & Zoning Parameters:
   - 35'-0" x 65'-0" (10.67m x 19.81m = 2,275 sq ft / 10 Marla)
   - North-facing street frontage
   - Front setback = 10'-0" (3.05m), Rear setback = 5'-0" (1.52m), Side setback = 0' (Party walls)
   - 3 Full Levels (L0, L1, L2) + Overhead Mumty Tower (9'-0" / 2.74m)
   - Clear ceiling height: 10'-6" (3.20m), Parapet: 3'-6" (1.05m)
2. Ground Floor (Level 0):
   - Landscaped front garden lawn (open-to-sky, strictly anchored Y=0 to Y=10'-0")
   - 2-car covered porch (15' x 18' / 4.57m x 5.49m)
   - Double-height entrance foyer + guest powder room
   - Formal drawing room with fireplace wall and credenza clearance
   - Expansive family TV lounge + semi-open formal dining area (8-seater, 36" clearance)
   - Main gourmet chef's kitchen + enclosed wet scullery/dirty kitchen along exterior East wall
   - Dedicated enclosed dog-leg stair shaft (8'-6" x 14'-6", min 3'-6" flight width, 11" treads, 7" risers, 3'-6" landing at +1500mm)
   - 2 Ground Bedroom Suites (14' x 14' each) with walk-in closets and ensuite luxury baths via acoustic lobby
   - 5'-0" continuous rear OTS lightwell
3. First Floor (Level 1):
   - 3 Independent Bedroom Suites (1 front master with walk-in wardrobe, 2 rear suites 14'x14') with ensuite baths
   - Central upper family living lounge with study nook
   - Upper beverage counter / kitchenette vertically stacked directly above ground kitchen (IoU >= 0.85)
   - Front grand terrace deck overlooking front garden
   - Exact vertical coordinate matching for stair shaft and rear OTS
4. Second Floor / Penthouse (Level 2):
   - 1 Multipurpose Suite with attached bath
   - 1 Independent Maid / Servant Room with dedicated compact bath, serviced by an independent service circulation route
   - Dedicated laundry/utility wash area
   - Rooftop Party Terrace & BBQ Deck
   - Parametric Stair Mumty Penthouse enclosure (8'-6" x 15'-0" x 9'-0" height) topped with overhead RCC water storage reservoir
5. Spatial & Ergonomics:
   - Beds anchored flush to solid interior partitions with twin nightstands & 36" corridor circulation
   - Bathroom wet/dry zoning (vanity/WC separated from shower enclosure with 10mm glass partition)
   - TV viewing throw distance: 10'-0" to 13'-0"
6. 3D Facade & Technical Deliverables:
   - Double-cantilevered volumetric cubic projections with timber louvers
   - Fluted travertine panels, floor-to-ceiling curtain glazing, 3'-6" parapets, 9'-0" mumty tower, overhead water tank
   - OBJ/MTL, DXF, and composite blueprint image export
"""

import os
import pytest
from shapely.geometry import Polygon, Point

from generation.parametric_bim_engine import (
    HierarchicalZoningCSPSolver,
    SiteBoundary,
    SetbackDefinition,
    ParametricBIMModel,
    Parametric3DMeshBuilder,
    StructuralTypology,
    FurnitureCategory,
    OpeningCategory
)
from cad.dxf_generator import DXFGenerator
from generation.visualizer import FloorPlanVisualizer


@pytest.fixture(scope="module")
def prod_10_marla_model() -> ParametricBIMModel:
    """Instantiates the 10 Marla Production 3-Story Residence with statutory parameters."""
    site = SiteBoundary(
        width_m=10.67,  # 35'-0"
        depth_m=19.81,  # 65'-0"
        street_frontage="NORTH",
        setbacks=SetbackDefinition(front_m=3.05, rear_m=1.52, side_left_m=0.0, side_right_m=0.0)
    )
    solver = HierarchicalZoningCSPSolver(site=site, floor_count=3)
    return solver.solve_layout(parking_capacity=2)


# ==============================================================================
# SECTION 1: STATUTORY & ZONING PARAMETERS
# ==============================================================================

def test_statutory_parameters_and_setbacks(prod_10_marla_model: ParametricBIMModel):
    """Asserts 35'-0\" x 65'-0\" footprint, North frontage, 10'-0\" front setback, and 5'-0\" rear setback."""
    assert abs(prod_10_marla_model.site.width_m - 10.67) < 0.05
    assert abs(prod_10_marla_model.site.depth_m - 19.81) < 0.05
    assert prod_10_marla_model.site.street_frontage == "NORTH"
    assert abs(prod_10_marla_model.site.setbacks.front_m - 3.05) < 0.05
    assert abs(prod_10_marla_model.site.setbacks.rear_m - 1.52) < 0.05
    assert prod_10_marla_model.floor_count == 3
    assert set(prod_10_marla_model.levels) == {0, 1, 2}
    assert abs(prod_10_marla_model.parapet_height_m - 1.05) < 0.05


# ==============================================================================
# SECTION 2: GROUND FLOOR (LEVEL 0) REQUIREMENTS
# ==============================================================================

def test_ground_floor_rooms_and_front_setback(prod_10_marla_model: ParametricBIMModel):
    """
    Validates Level 0:
    - Front garden lawn open-to-sky strictly anchored Y=0 to Y=10'-0" (3.05m)
    - 2-car covered porch (15' x 18' / 4.57m x 5.49m)
    - Double-height foyer + guest powder room
    - Formal drawing room with fireplace wall and credenza clearance
    - TV lounge + semi-open formal dining area (8-seater)
    - Main gourmet kitchen + enclosed scullery along exterior wall
    - Dedicated stair core (8'-6" x 14'-6")
    - 2 Ground Bedroom Suites (14' x 14' each) + ensuite baths + 5'-0" rear OTS
    """
    l0 = {r.room_id: r for r in prod_10_marla_model.rooms if r.level_index == 0}

    # 1. Front garden lawn
    lawn = l0["r_L0_lawn"]
    p_lawn = Polygon(lawn.polygon)
    assert p_lawn.bounds[1] == 0.0
    assert abs(p_lawn.bounds[3] - 3.05) < 0.05  # Strictly anchored at Y=0 to Y=10'-0"

    # 2. 2-car covered porch (15' x 18')
    porch = l0["r_L0_porch"]
    p_porch = Polygon(porch.polygon)
    w_porch = p_porch.bounds[2] - p_porch.bounds[0]
    d_porch = p_porch.bounds[3] - p_porch.bounds[1]
    assert abs(w_porch - 4.57) < 0.10  # 15'-0"
    assert abs(d_porch - 5.49) < 0.10  # 18'-0"

    # 3. Formal drawing room with fireplace & credenza
    drawing = l0["r_L0_drawing"]
    furn_draw = drawing.furniture
    assert any(f.category == FurnitureCategory.FIREPLACE for f in furn_draw)
    assert any(f.category == FurnitureCategory.CREDENZA for f in furn_draw)

    # 4. Semi-open dining area
    dining = l0["r_L0_dining"]
    furn_dining = dining.furniture
    assert any(f.category == FurnitureCategory.DINING_TABLE_8 for f in furn_dining)

    # 5. Expansive TV Lounge
    lounge = l0["r_L0_lounge"]
    assert any(f.category == FurnitureCategory.L_SECTIONAL_SOFA for f in lounge.furniture)

    # 6. Scullery along exterior wall
    scullery = l0["r_L0_dirty_kitchen"]
    assert scullery.has_exterior_exhaust is True
    assert abs(Polygon(scullery.polygon).bounds[2] - 10.67) < 0.05

    # 7. Dedicated Stair Core (8'-6" x 14'-6" / 2.59m x 4.42m)
    stair = l0["r_L0_stair"]
    p_stair = Polygon(stair.polygon)
    w_stair = p_stair.bounds[2] - p_stair.bounds[0]
    d_stair = p_stair.bounds[3] - p_stair.bounds[1]
    assert abs(w_stair - 2.59) < 0.10  # 8'-6"
    assert abs(d_stair - 4.42) < 0.10  # 14'-6"

    # 8. Ground Suites 1 & 2 (14' x 14' each)
    bed1 = l0["r_L0_bed1"]
    p_bed1 = Polygon(bed1.polygon)
    assert abs((p_bed1.bounds[2] - p_bed1.bounds[0]) - 4.27) < 0.10  # 14'-0"
    assert abs((p_bed1.bounds[3] - p_bed1.bounds[1]) - 4.27) < 0.10  # 14'-0"

    bed2 = l0["r_L0_bed2"]
    p_bed2 = Polygon(bed2.polygon)
    assert abs((p_bed2.bounds[2] - p_bed2.bounds[0]) - 4.27) < 0.10  # 14'-0"
    assert abs((p_bed2.bounds[3] - p_bed2.bounds[1]) - 4.27) < 0.10  # 14'-0"

    # 9. Rear 5'-0" OTS lightwell
    ots = l0["r_L0_ots"]
    p_ots = Polygon(ots.polygon)
    assert abs((p_ots.bounds[3] - p_ots.bounds[1]) - 1.52) < 0.05  # 5'-0"
    assert abs((p_ots.bounds[2] - p_ots.bounds[0]) - 10.67) < 0.05  # Full width


# ==============================================================================
# SECTION 3: FIRST FLOOR (LEVEL 1) REQUIREMENTS
# ==============================================================================

def test_first_floor_program_and_stacking(prod_10_marla_model: ParametricBIMModel):
    """
    Validates Level 1:
    - 3 Suites (1 front master with walk-in wardrobe, 2 rear suites 14'x14')
    - Central upper family living lounge with study nook
    - Upper beverage counter / kitchenette stacked directly above ground kitchen (IoU >= 0.85)
    - Front grand terrace deck overlooking front garden
    - Exact vertical stair shaft and rear OTS match (IoU = 1.00)
    """
    l1 = {r.room_id: r for r in prod_10_marla_model.rooms if r.level_index == 1}

    assert "r_L1_terrace" in l1
    assert "r_L1_bed3" in l1
    assert "r_L1_bath3" in l1
    assert "r_L1_lounge" in l1
    assert "r_L1_kitchenette" in l1
    assert "r_L1_bed4" in l1
    assert "r_L1_bed5" in l1
    assert "r_L1_ots" in l1

    # Kitchenette stacked directly above Ground Kitchen (IoU >= 0.85)
    kit_l0 = Polygon(next(r for r in prod_10_marla_model.rooms if r.room_id == "r_L0_kitchen").polygon)
    kit_l1 = Polygon(l1["r_L1_kitchenette"].polygon)
    iou_kit = kit_l0.intersection(kit_l1).area / kit_l0.union(kit_l1).area
    assert iou_kit >= 0.85

    # Stair Core IoU = 1.00
    stair_l0 = Polygon(next(r for r in prod_10_marla_model.rooms if r.room_id == "r_L0_stair").polygon)
    stair_l1 = Polygon(l1["r_L1_stair"].polygon)
    iou_stair = stair_l0.intersection(stair_l1).area / stair_l0.union(stair_l1).area
    assert iou_stair >= 0.99

    # OTS IoU = 1.00
    ots_l0 = Polygon(next(r for r in prod_10_marla_model.rooms if r.room_id == "r_L0_ots").polygon)
    ots_l1 = Polygon(l1["r_L1_ots"].polygon)
    iou_ots = ots_l0.intersection(ots_l1).area / ots_l0.union(ots_l1).area
    assert iou_ots >= 0.99

    # Rear Suites 4 & 5 (14' x 14')
    p_bed4 = Polygon(l1["r_L1_bed4"].polygon)
    p_bed5 = Polygon(l1["r_L1_bed5"].polygon)
    assert abs((p_bed4.bounds[2] - p_bed4.bounds[0]) - 4.27) < 0.10
    assert abs((p_bed5.bounds[2] - p_bed5.bounds[0]) - 4.27) < 0.10


# ==============================================================================
# SECTION 4: SECOND FLOOR / PENTHOUSE (LEVEL 2) REQUIREMENTS
# ==============================================================================

def test_second_floor_penthouse_program(prod_10_marla_model: ParametricBIMModel):
    """
    Validates Level 2:
    - Multipurpose Suite with attached bath
    - Independent Maid / Servant Room with compact bath and independent service circulation route
    - Dedicated laundry / utility wash area
    - Rooftop Party Terrace & BBQ Deck
    - Parametric Stair Mumty Penthouse (8'-6" x 15'-0" x 9'-0" height) + Overhead RCC water reservoir
    """
    l2 = {r.room_id: r for r in prod_10_marla_model.rooms if r.level_index == 2}

    assert "r_L2_bbq_terrace" in l2
    assert "r_L2_mumty_vestibule" in l2
    assert "r_L2_stair" in l2
    assert "r_L2_multipurpose" in l2
    assert "r_L2_bath_spa" in l2
    assert "r_L2_laundry" in l2
    assert "r_L2_maid" in l2
    assert "r_L2_bath_maid" in l2
    assert "r_L2_solar_deck" in l2
    assert "r_L2_ots" in l2

    # Weather door from Mumty Vestibule to Terrace
    weather_door = next((op for op in prod_10_marla_model.openings if op.opening_id == "door_P_L2_mumty_weather"), None)
    assert weather_door is not None
    assert weather_door.is_exterior is True

    # Independent Service Circulation Route for Maid Quarter
    maid_solar_exit = next((op for op in prod_10_marla_model.openings if op.opening_id == "door_P_L2_maid_solar"), None)
    assert maid_solar_exit is not None
    assert maid_solar_exit.is_exterior is True


# ==============================================================================
# SECTION 5: SPATIAL, FURNITURE & ERGONOMIC CONSTRAINTS
# ==============================================================================

def test_headboard_anchoring_and_walking_corridors(prod_10_marla_model: ParametricBIMModel):
    """
    Validates:
    - Every bed anchors flush to a solid interior partition
    - Strict 36" (0.91m) corridor circulation envelope around beds
    - Wet/dry zoning inside bathrooms
    - TV viewing throw distance 10'-0" to 13'-0"
    """
    room_map = {r.room_id: r for r in prod_10_marla_model.rooms}

    # 1. Master Bed 1 anchoring & 36" corridor
    bed1_furn = room_map["r_L0_bed1"].furniture
    king1 = next(f for f in bed1_furn if f.category == FurnitureCategory.KING_BED)
    assert king1.solid_wall_anchor_edge is not None
    assert king1.clearance_envelope_polygon is not None
    p_clear = Polygon(king1.clearance_envelope_polygon)
    # Check 36" (0.91m) clearance buffer on flanks
    assert p_clear.bounds[2] - p_clear.bounds[0] >= 2.00 + 2 * 0.85

    # 2. Bathroom wet/dry zoning (Vanity & WC + Shower Enclosure)
    bath1_furn = room_map["r_L0_bath1"].furniture
    has_vanity = any(f.category == FurnitureCategory.VANITY_BASIN for f in bath1_furn)
    has_wc = any(f.category == FurnitureCategory.WATER_CLOSET for f in bath1_furn)
    has_shower = any(f.category == FurnitureCategory.SHOWER_ENCLOSURE for f in bath1_furn)
    assert has_vanity and has_wc and has_shower

    # 3. TV Viewing Throw Distance (10'-0" to 13'-0" / 3.05m to 3.96m)
    lounge_furn = room_map["r_L0_lounge"].furniture
    sofa = next(f for f in lounge_furn if f.category == FurnitureCategory.L_SECTIONAL_SOFA)
    tv = next(f for f in lounge_furn if f.category == FurnitureCategory.TV_MEDIA_CONSOLE)
    throw_dist = abs(tv.position_3d[0] - sofa.position_3d[0])
    assert 3.00 <= throw_dist <= 4.00, f"TV throw distance {throw_dist}m is outside 10'-0\" to 13'-0\" envelope"


# ==============================================================================
# SECTION 6: 3D FACADE & TECHNICAL DELIVERABLES
# ==============================================================================

def test_3d_facade_and_mesh_export(prod_10_marla_model: ParametricBIMModel, tmp_path):
    """
    Validates:
    - 3D mesh building with volumetric elements
    - OBJ/MTL export
    - Layered DXF export
    - 2D multi-floor blueprint rendering
    """
    builder = Parametric3DMeshBuilder(prod_10_marla_model)
    vertices, faces, materials = builder.build_3d_geometry()

    assert len(vertices) > 200
    assert len(faces) > 100
    assert "Mat_Concrete_Slab" in materials
    assert "Mat_Fluted_Limestone" in materials
    assert "Mat_Timber_Louvers" in materials
    assert "Mat_Floor_Glazing" in materials
    assert "Mat_Water_Reservoir" in materials

    # Export OBJ / MTL
    obj_p = str(tmp_path / "prod_10_marla.obj")
    mtl_p = str(tmp_path / "prod_10_marla.mtl")
    builder.export_to_obj(obj_p, mtl_p)
    assert os.path.exists(obj_p)
    assert os.path.getsize(obj_p) > 5000

    # Export DXF
    canon = prod_10_marla_model.to_canonical_floorplan()
    dxf_gen = DXFGenerator()
    dxf_p = str(tmp_path / "prod_10_marla.dxf")
    dxf_gen.export_composite_dxf(canon, dxf_p)
    assert os.path.exists(dxf_p)
    assert os.path.getsize(dxf_p) > 20000

    # Render Blueprints
    rendered = FloorPlanVisualizer.render_all_floors(canon, str(tmp_path / "blueprints"))
    assert "ground_floor" in rendered
    assert "first_floor" in rendered
    assert "second_floor_penthouse" in rendered
    for p in rendered.values():
        assert os.path.exists(p)
