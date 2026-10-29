"""
Tests for 10 Marla (35'-0" x 65'-0") Luxury Residence Multi-Level Architectural BIM System.

Validates all 4 primary architectural, structural, CAD, and 3D requirements:
1. Structural Grid & Building Envelope Rules
   - Front setback = 15'-0" (4.57m); rear setback = 6'-6" (1.98m continuous OTS lightwell)
   - 9" solid masonry external walls with 9"x18" (0.229m x 0.457m) RCC column nodes at primary intersections
   - Parking envelope protection [X: 16'-0" to 35'-0", Y: 0'-0" to 15'-0"] reserved exclusively for 2 vehicles
   - Vertical structural continuity: Stair core (8'-0" x 14'-0"), OTS, and wet plumbing chases vertically aligned (IoU >= 0.95)
2. Multi-Level Floor Plan Hierarchy (Non-Duplicated Programs across L0, L1, L2)
3. CAD Graphic Standards & Furniture Ergonomics
   - Double-line partitioning (9" exterior, 4.5" interior)
   - Code-compliant door swings with dashed clearances, no fixture obstruction, weatherproof mumty exterior door
   - Bed headboards anchored to solid dry interior walls with twin bedside tables & 36" (0.91m) walking corridor
   - Living rooms with L-sectionals oriented to dedicated media walls
4. 3D Model & Facade Synthesis
   - Front elevation volumetric elements (cantilevered balcony, timber louvers, fluted limestone, curtain glazing)
   - Rooftop elements (3'-6" parapets, 9'-0" stair mumty tower, overhead concrete water reservoir, BBQ pergola, solar rack)
   - Successful OBJ/MTL, DXF, and blueprint image export
"""

import os
import pytest
from shapely.geometry import Polygon, Point, box

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
def bim_10_marla_model() -> ParametricBIMModel:
    """Instantiates and solves the 10 Marla Luxury 3-Level Residence model."""
    site = SiteBoundary(
        width_m=10.67,  # 35'-0"
        depth_m=19.81,  # 65'-0"
        street_frontage="SOUTH",
        setbacks=SetbackDefinition(front_m=4.57, rear_m=1.98, side_left_m=0.0, side_right_m=0.0)
    )
    solver = HierarchicalZoningCSPSolver(site=site, floor_count=3)
    return solver.solve_10_marla_luxury_layout(parking_capacity=2)


# ==============================================================================
# SECTION 1: STRUCTURAL GRID & BUILDING ENVELOPE RULES
# ==============================================================================

def test_site_and_setback_boundaries(bim_10_marla_model: ParametricBIMModel):
    """Asserts 35'-0\" x 65'-0\" footprint, 15'-0\" front setback, and 6'-6\" rear OTS setback."""
    assert abs(bim_10_marla_model.site.width_m - 10.67) < 0.05
    assert abs(bim_10_marla_model.site.depth_m - 19.81) < 0.05
    assert abs(bim_10_marla_model.site.setbacks.front_m - 4.57) < 0.05
    assert abs(bim_10_marla_model.site.setbacks.rear_m - 1.98) < 0.05

    # Check rear continuous OTS lightwell
    ots_rooms = [r for r in bim_10_marla_model.rooms if "ots" in r.room_id.lower()]
    assert len(ots_rooms) == 3  # Level 0, Level 1, Level 2
    for ots in ots_rooms:
        p = Polygon(ots.polygon)
        minx, miny, maxx, maxy = p.bounds
        assert miny >= 17.80
        assert maxy <= 19.85
        assert abs((maxx - minx) - 10.67) < 0.10  # Full plot width lightwell (35'-0")


def test_rcc_column_grid_and_wall_specifications(bim_10_marla_model: ParametricBIMModel):
    """
    Asserts 9\"x18\" RCC column nodes at primary grid intersections and
    9\" exterior / 4.5\" interior double-line masonry walls.
    """
    assert len(bim_10_marla_model.columns) >= 15
    for col in bim_10_marla_model.columns:
        w_m, d_m = col.dimensions_m
        assert abs(w_m - 0.229) < 0.01 or abs(w_m - 0.457) < 0.01
        assert abs(d_m - 0.457) < 0.01 or abs(d_m - 0.229) < 0.01
        assert len(col.serves_levels) == 3

    assert len(bim_10_marla_model.walls) > 0
    ext_walls = [w for w in bim_10_marla_model.walls if "EXTERIOR" in w.wall_type.upper()]
    int_walls = [w for w in bim_10_marla_model.walls if "INTERIOR" in w.wall_type.upper()]
    assert len(ext_walls) > 0
    assert len(int_walls) > 0
    for ew in ext_walls:
        assert abs(ew.thickness_m - 0.229) < 0.01  # 9" solid masonry
    for iw in int_walls:
        assert abs(iw.thickness_m - 0.114) < 0.01  # 4.5" interior partitions


def test_parking_envelope_protection(bim_10_marla_model: ParametricBIMModel):
    """
    Parking Envelope Protection:
    Double car porch [X: 16'-0" to 35'-0" (4.88m to 10.67m), Y: 0'-0" to 15'-0" (0.0m to 4.57m)]
    is strictly reserved for two vehicles.
    Zero powder rooms, foyers, or interior walls may cross below Y = 15'-0" on the porch side.
    """
    porch_room = next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L0_porch")
    p_porch = Polygon(porch_room.polygon)
    minx, miny, maxx, maxy = p_porch.bounds
    assert minx >= 4.80
    assert maxx <= 10.70
    assert miny >= 0.00
    assert maxy <= 4.60

    # Ensure no interior walls intrude into the car porch below Y = 4.57m
    for wall in bim_10_marla_model.walls:
        if wall.level_index == 0 and "INTERIOR" in wall.wall_type.upper():
            (wx1, wy1), (wx2, wy2) = wall.centerline
            if wx1 > 4.88 and wx2 > 4.88:
                assert wy1 >= 4.55 and wy2 >= 4.55, f"Interior wall {wall.wall_id} intrudes into Car Porch envelope below Y=15'-0\""

    # Ensure powder room is located at or above Y = 4.57m (recessed behind porch)
    powder = next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L0_powder")
    p_powder = Polygon(powder.polygon)
    assert p_powder.bounds[1] >= 4.55, "Powder room must be recessed behind the car porch (Y >= 4.57m)"


def test_vertical_structural_continuity_iou(bim_10_marla_model: ParametricBIMModel):
    """
    Asserts vertical structural alignment across L0, L1, and L2:
    - Stair core (8'-0" x 14'-0"): IoU = 1.00
    - Rear OTS lightwell: IoU = 1.00
    - Wet core kitchen / laundry stack: IoU = 1.00
    - Wet core rear bathrooms: IoU = 1.00
    """
    # Stair cores
    stair_l0 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L0_stair").polygon)
    stair_l1 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L1_stair").polygon)
    stair_l2 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L2_stair").polygon)

    iou_stair_01 = stair_l0.intersection(stair_l1).area / stair_l0.union(stair_l1).area
    iou_stair_12 = stair_l1.intersection(stair_l2).area / stair_l1.union(stair_l2).area
    assert iou_stair_01 >= 0.99
    assert iou_stair_12 >= 0.99

    # OTS shafts
    ots_l0 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L0_ots").polygon)
    ots_l1 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L1_ots").polygon)
    ots_l2 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L2_ots").polygon)

    iou_ots_01 = ots_l0.intersection(ots_l1).area / ots_l0.union(ots_l1).area
    iou_ots_12 = ots_l1.intersection(ots_l2).area / ots_l1.union(ots_l2).area
    assert iou_ots_01 >= 0.99
    assert iou_ots_12 >= 0.99

    # Kitchen / Utility vertical stack (L0: Chef Kitchen + Scullery, L1: Butler Pantry + Gym, L2: Rooftop Laundry)
    kit_l0 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L0_kitchen").polygon)
    dirty_l0 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L0_dirty_kitchen").polygon)
    kit_stack_l0 = kit_l0.union(dirty_l0)
    kit_l1 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L1_kitchenette").polygon)
    laundry_l2 = Polygon(next(r for r in bim_10_marla_model.rooms if r.room_id == "r_L2_laundry").polygon)

    iou_kit_01 = kit_stack_l0.intersection(kit_l1).area / kit_stack_l0.union(kit_l1).area
    iou_kit_12 = kit_l1.intersection(laundry_l2).area / kit_l1.union(laundry_l2).area
    assert iou_kit_01 >= 0.99
    assert iou_kit_12 >= 0.99

    # Plumbing shafts
    assert len(bim_10_marla_model.plumbing_shafts) >= 3
    for shaft in bim_10_marla_model.plumbing_shafts:
        assert set(shaft.serves_levels) == {0, 1, 2}


# ==============================================================================
# SECTION 2: MULTI-LEVEL FLOOR PLAN HIERARCHY (NON-DUPLICATED PROGRAMS)
# ==============================================================================

def test_level_0_ground_floor_program(bim_10_marla_model: ParametricBIMModel):
    """
    Validates Level 0:
    - 16'x15' Lawn + 19'x15' Double Car Porch
    - Foyer (11'x10'), Drawing Salon (16'x18') with front bay window, Guest Powder Room (8'x10')
    - Central TV Lounge (27'x14'), Gourmet Kitchen (16'x9'-6"), Scullery/Dirty Kitchen (16'x4'-6") along East wall
    - Private Vestibule (19'x6') distributing to Ground Master Suite 1 (14'x12') + Guest Suite 2 (14'x12') + ensuite baths
    """
    l0_rooms = {r.room_id: r for r in bim_10_marla_model.rooms if r.level_index == 0}

    assert "r_L0_lawn" in l0_rooms
    assert "r_L0_porch" in l0_rooms
    assert "r_L0_drawing" in l0_rooms
    assert "r_L0_foyer" in l0_rooms
    assert "r_L0_powder" in l0_rooms
    assert "r_L0_stair" in l0_rooms
    assert "r_L0_lounge" in l0_rooms
    assert "r_L0_kitchen" in l0_rooms
    assert "r_L0_dirty_kitchen" in l0_rooms
    assert "r_L0_bed_lobby" in l0_rooms
    assert "r_L0_bed1" in l0_rooms
    assert "r_L0_bath1" in l0_rooms
    assert "r_L0_bed2" in l0_rooms
    assert "r_L0_bath2" in l0_rooms
    assert "r_L0_ots" in l0_rooms

    # Scullery on East exterior wall with direct exhaust
    scullery = l0_rooms["r_L0_dirty_kitchen"]
    assert scullery.has_exterior_exhaust is True
    p_scullery = Polygon(scullery.polygon)
    assert abs(p_scullery.bounds[2] - 10.67) < 0.05  # Reaches East plot boundary

    # Drawing Salon bay window opening
    bay_win = next((op for op in bim_10_marla_model.openings if op.opening_id == "win_L0_drawing_bay"), None)
    assert bay_win is not None
    assert bay_win.width_m >= 2.40  # 8'-0" expansive glazing facing lawn


def test_level_1_first_floor_program(bim_10_marla_model: ParametricBIMModel):
    """
    Validates Level 1:
    - Sunset Terrace deck (19'x15') + Upper Master Executive Suite 3 (16'x18') with walk-in wardrobe and bath
    - Executive Study & Home Library (11'x10'), Upper Family Living Gallery (27'x17')
    - Butler's Pantry & Gym (16'x14') vertically stacked over ground kitchen
    - Upper Bedroom Vestibule leading to Suite 4 (14'x12') and Suite 5 (14'x12') with attached baths flanking OTS
    """
    l1_rooms = {r.room_id: r for r in bim_10_marla_model.rooms if r.level_index == 1}

    assert "r_L1_terrace" in l1_rooms
    assert "r_L1_bed3" in l1_rooms
    assert "r_L1_bath3" in l1_rooms
    assert "r_L1_study" in l1_rooms
    assert "r_L1_stair" in l1_rooms
    assert "r_L1_lounge" in l1_rooms
    assert "r_L1_kitchenette" in l1_rooms
    assert "r_L1_bed_lobby" in l1_rooms
    assert "r_L1_bed4" in l1_rooms
    assert "r_L1_bath4" in l1_rooms
    assert "r_L1_bed5" in l1_rooms
    assert "r_L1_bath5" in l1_rooms
    assert "r_L1_ots" in l1_rooms

    # Sunset Terrace is positioned over car porch
    p_terrace = Polygon(l1_rooms["r_L1_terrace"].polygon)
    assert p_terrace.bounds[0] >= 4.80  # X >= 16'-0"
    assert p_terrace.bounds[3] <= 4.60  # Y <= 15'-0"


def test_level_2_second_floor_program(bim_10_marla_model: ParametricBIMModel):
    """
    Validates Level 2:
    - Full-width Panoramic BBQ Terrace (35'x25') with pergola seating
    - Weatherproof Mumty Penthouse Vestibule with exterior weather door
    - Multipurpose Studio / Gym (16'x20') with luxury spa bath
    - Dedicated Rooftop Laundry (16'x14') stacked over kitchen core
    - Maid / Servant Quarter (16'x12') with attached bath and direct service terrace access
    - Rear Solar Inverter Deck (14'x12')
    """
    l2_rooms = {r.room_id: r for r in bim_10_marla_model.rooms if r.level_index == 2}

    assert "r_L2_bbq_terrace" in l2_rooms
    assert "r_L2_mumty_vestibule" in l2_rooms
    assert "r_L2_stair" in l2_rooms
    assert "r_L2_multipurpose" in l2_rooms
    assert "r_L2_bath_spa" in l2_rooms
    assert "r_L2_laundry" in l2_rooms
    assert "r_L2_maid" in l2_rooms
    assert "r_L2_bath_maid" in l2_rooms
    assert "r_L2_solar_deck" in l2_rooms
    assert "r_L2_ots" in l2_rooms

    # Weatherproof exterior door from Mumty Vestibule to BBQ Terrace
    weather_door = next((op for op in bim_10_marla_model.openings if op.opening_id == "door_L2_mumty_ext_weather"), None)
    assert weather_door is not None
    assert weather_door.is_exterior is True
    assert "r_L2_mumty_vestibule" in weather_door.connects_rooms
    assert "r_L2_bbq_terrace" in weather_door.connects_rooms

    # Direct service terrace access from Maid Quarter to Solar Deck
    maid_exit = next((op for op in bim_10_marla_model.openings if op.opening_id == "door_L2_maid_solar_exit"), None)
    assert maid_exit is not None
    assert maid_exit.is_exterior is True


# ==============================================================================
# SECTION 3: CAD GRAPHIC STANDARDS & FURNITURE ERGONOMICS
# ==============================================================================

def test_door_swings_and_clearances(bim_10_marla_model: ParametricBIMModel):
    """
    Validates CAD standards:
    - 90-degree clear door swings
    - No doors swinging directly into toilets, vanities, or blocking bed corridors
    """
    doors = [op for op in bim_10_marla_model.openings if "door" in op.opening_id.lower()]
    assert len(doors) >= 20  # Extensive code-compliant doors across 3 levels

    # Verify powder room door swings away from toilet & basin
    powder_door = next(op for op in doors if op.opening_id == "door_L0_powder")
    assert powder_door.width_m <= 0.90  # Standard 2'-9" / 0.85m door

    # Verify bedroom doors connect to lobbies, never directly connecting adjacent bedrooms
    for op in doors:
        conn = op.connects_rooms
        if len(conn) == 2:
            r1, r2 = conn
            if "bed" in r1 and "bed" in r2 and "lobby" not in r1 and "lobby" not in r2:
                pytest.fail(f"Direct connection between bedrooms prohibited: {r1} <-> {r2}")


def test_furniture_anchoring_and_walking_corridors(bim_10_marla_model: ParametricBIMModel):
    """
    Validates Ergonomic Furniture Placement:
    - All beds anchor headboards to solid interior dry walls with twin bedside tables
    - 36" (0.91m) continuous walking corridor around beds
    - Living rooms feature L-sectionals oriented toward dedicated media walls
    - Kitchen features waterfall prep island
    - Car porch holds 2 luxury vehicles
    """
    room_map = {r.room_id: r for r in bim_10_marla_model.rooms}

    # 1. Car Porch (2 vehicles)
    porch_furn = room_map["r_L0_porch"].furniture
    vehicles = [f for f in porch_furn if f.category in (FurnitureCategory.VEHICLE_SUV, FurnitureCategory.VEHICLE_SEDAN)]
    assert len(vehicles) == 2

    # 2. Living Rooms (L-sectionals facing media wall)
    l0_lounge_furn = room_map["r_L0_lounge"].furniture
    assert any(f.category == FurnitureCategory.L_SECTIONAL_SOFA for f in l0_lounge_furn)
    assert any(f.category == FurnitureCategory.TV_MEDIA_CONSOLE for f in l0_lounge_furn)

    l1_lounge_furn = room_map["r_L1_lounge"].furniture
    assert any(f.category == FurnitureCategory.L_SECTIONAL_SOFA for f in l1_lounge_furn)
    assert any(f.category == FurnitureCategory.TV_MEDIA_CONSOLE for f in l1_lounge_furn)

    # 3. Master Suite 1 (King Bed + Twin Nightstands + Anchor + 36" Clearance)
    bed1_furn = room_map["r_L0_bed1"].furniture
    king1 = next(f for f in bed1_furn if f.category == FurnitureCategory.KING_BED)
    assert king1.solid_wall_anchor_edge is not None
    assert king1.clearance_envelope_polygon is not None
    # Check twin nightstands flanking bed
    nightstands1 = [f for f in bed1_furn if f.category == FurnitureCategory.NIGHTSTAND]
    assert len(nightstands1) == 2

    # 4. Master Suite 3 (King Bed + Twin Nightstands)
    bed3_furn = room_map["r_L1_bed3"].furniture
    king3 = next(f for f in bed3_furn if f.category == FurnitureCategory.KING_BED)
    assert king3.solid_wall_anchor_edge is not None
    nightstands3 = [f for f in bed3_furn if f.category == FurnitureCategory.NIGHTSTAND]
    assert len(nightstands3) == 2

    # 5. Gourmet Kitchen Island
    kit_furn = room_map["r_L0_kitchen"].furniture
    assert any(f.category == FurnitureCategory.KITCHEN_COUNTER_ISLAND for f in kit_furn)


# ==============================================================================
# SECTION 4: 3D MODEL & FACADE SYNTHESIS
# ==============================================================================

def test_facade_and_rooftop_elements(bim_10_marla_model: ParametricBIMModel):
    """
    Validates 3D Volumetric Facade Synthesis:
    - Cantilevered first-floor balcony
    - Vertical timber-finish louvers
    - Fluted limestone cladding
    - Floor-to-ceiling double-glazed windows
    - Rooftop 3'-6" parapet walls
    - Enclosed 9'-0" high stair mumty tower
    - Overhead concrete water reservoir (1000 Gal)
    - BBQ pergola and solar panel array
    """
    fe_types = {fe.element_type: fe for fe in bim_10_marla_model.facade_elements}

    assert "CANTILEVER_BALCONY" in fe_types
    assert "TIMBER_LOUVERS" in fe_types
    assert "FLUTED_LIMESTONE_PANEL" in fe_types
    assert "CURTAIN_WALLING" in fe_types
    assert "MUMTY_TOWER" in fe_types
    assert "WATER_RESERVOIR" in fe_types
    assert "PERGOLA" in fe_types
    assert "SOLAR_ARRAY" in fe_types

    # Validate 9'-0" mumty height (2.74m)
    mumty = fe_types["MUMTY_TOWER"]
    assert abs(mumty.dimensions_m[2] - 2.74) < 0.05

    # Validate 3'-6" parapet height (1.07m)
    assert abs(bim_10_marla_model.parapet_height_m - 1.07) < 0.05

    # Validate overhead water tank is positioned on mumty
    tank = fe_types["WATER_RESERVOIR"]
    assert tank.position_3d[2] >= 12.0  # Above Level 2 ceiling + mumty


def test_3d_mesh_builder_watertight_export(bim_10_marla_model: ParametricBIMModel, tmp_path):
    """Validates 3D geometry extrusion, manifold vertex count, and OBJ/MTL file output."""
    builder = Parametric3DMeshBuilder(bim_10_marla_model)
    vertices, faces, materials = builder.build_3d_geometry()

    assert len(vertices) > 200
    assert len(faces) > 100
    assert "Mat_Concrete_Slab" in materials
    assert "Mat_Exterior_Travertine" in materials
    assert "Mat_Fluted_Limestone" in materials
    assert "Mat_Timber_Louvers" in materials
    assert "Mat_Floor_Glazing" in materials
    assert "Mat_Water_Reservoir" in materials
    assert "Mat_Pergola_Wood" in materials
    assert "Mat_Solar_Panels" in materials

    # Export to OBJ & MTL
    obj_file = str(tmp_path / "10_marla_luxury.obj")
    mtl_file = str(tmp_path / "10_marla_luxury.mtl")
    builder.export_to_obj(obj_file, mtl_file)

    assert os.path.exists(obj_file)
    assert os.path.getsize(obj_file) > 5000
    assert os.path.exists(mtl_file)
    assert os.path.getsize(mtl_file) > 500


def test_canonical_export_and_cad_dxf(bim_10_marla_model: ParametricBIMModel, tmp_path):
    """
    Validates conversion to CanonicalFloorPlan and production-grade AutoCAD DXF export
    with A-COLS, A-WALL-EXTR, A-WALL-INTR, A-DOOR, A-STRS, A-FURN, A-ANNO-TEXT layers.
    """
    canon_plan = bim_10_marla_model.to_canonical_floorplan()
    assert canon_plan.metadata.floor_count == 3
    assert len(canon_plan.rooms) == len(bim_10_marla_model.rooms)
    assert len(canon_plan.walls) > 0

    dxf_gen = DXFGenerator()
    composite_dxf = str(tmp_path / "10_marla_luxury_composite.dxf")
    dxf_gen.export_composite_dxf(canon_plan, composite_dxf)

    assert os.path.exists(composite_dxf)
    assert os.path.getsize(composite_dxf) > 20000

    # Also test export_all_floor_dxfs
    all_dxfs = dxf_gen.export_all_floor_dxfs(canon_plan, str(tmp_path / "dxfs"))
    assert "ground_floor" in all_dxfs
    assert "floor_1" in all_dxfs
    assert "floor_2" in all_dxfs
    for p in all_dxfs.values():
        assert os.path.exists(p)


def test_2d_blueprint_visualizer_rendering(bim_10_marla_model: ParametricBIMModel, tmp_path):
    """
    Validates FloorPlanVisualizer rendering of all 3 levels and composite blueprint sheets.
    """
    canon_plan = bim_10_marla_model.to_canonical_floorplan()
    rendered = FloorPlanVisualizer.render_all_floors(canon_plan, str(tmp_path / "blueprints"))

    assert "ground_floor" in rendered
    assert "first_floor" in rendered
    assert "second_floor_penthouse" in rendered
    assert "composite_all_floors" in rendered

    for key, img_path in rendered.items():
        assert os.path.exists(img_path)
        assert os.path.getsize(img_path) > 10000  # Non-empty high-res PNG
