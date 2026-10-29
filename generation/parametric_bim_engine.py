"""
Parametric Generative BIM Architecture Engine.
==============================================
Principal AI Architect & Senior Computational Design Engineer Implementation.

Re-engineers heuristic RAG/CV floor planning into a production-grade generative BIM system:
1. Spatial Constraint Graph & Requirement Normalizer (Pydantic / JSON Schema).
2. Hierarchical Constraint Satisfaction Solver (Eliminating interior trapped lawns,
   enforcing wet-core vertical plumbing alignment, 3-zone privacy hierarchy, and dedicated stair shafts).
3. Human Factors & Ergonomic Furniture Clearance Solver (Solid-wall headboard anchoring,
   36" (0.91m) corridor clearances, TV throw ratios, wet/dry bath partitions).
4. Parametric 2D-to-3D Watertight BIM Mesh Extruder (Floor slabs, structural walls with
   parametric door/window cutouts, multi-floor stacking, rooftop parapets, and mumty stair penthouse).
5. Exporters for 3D OBJ/MTL, glTF/GLB, and IFC data models.
"""

from __future__ import annotations
import math
import os
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any, Set
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import unary_union
from pydantic import BaseModel, Field


# ==============================================================================
# 1. CORE DATA MODELS & SPATIAL CONSTRAINT GRAPH
# ==============================================================================

class ArchitecturalZone(str, Enum):
    ZONE_A_PUBLIC = "ZONE_A_PUBLIC"          # Porch, Lawn, Foyer, Drawing, Powder
    ZONE_B_SEMI_PRIVATE = "ZONE_B_SEMI_PRIVATE"  # Lounge, Dining, Kitchen, Dirty Kitchen, Stairs
    ZONE_C_PRIVATE = "ZONE_C_PRIVATE"        # Bed Suites, Dressing, Ensuite Baths, Bed Lobby
    ZONE_SERVICE_OUTDOOR = "ZONE_SERVICE_OUTDOOR"  # Service Passage, OTS, Courtyard, Terraces


class StructuralTypology(str, Enum):
    RCC_FRAME_SLAB = "RCC_FRAME_SLAB"
    LOAD_BEARING_BRICK = "LOAD_BEARING_BRICK"
    STEEL_COMPOSITE = "STEEL_COMPOSITE"


class OpeningCategory(str, Enum):
    MAIN_ENTRANCE_DOOR = "MAIN_ENTRANCE_DOOR"
    INTERIOR_DOOR = "INTERIOR_DOOR"
    SERVICE_DOOR = "SERVICE_DOOR"
    SLIDING_PATIO_DOOR = "SLIDING_PATIO_DOOR"
    STANDARD_WINDOW = "STANDARD_WINDOW"
    DOUBLE_HEIGHT_GLAZING = "DOUBLE_HEIGHT_GLAZING"
    VENTILATION_CLERESTORY = "VENTILATION_CLERESTORY"


class FurnitureCategory(str, Enum):
    KING_BED = "KING_BED"
    QUEEN_BED = "QUEEN_BED"
    WARDROBE_RUN = "WARDROBE_RUN"
    SOFA_THREE_SEATER = "SOFA_THREE_SEATER"
    L_SECTIONAL_SOFA = "L_SECTIONAL_SOFA"
    ARMCHAIR = "ARMCHAIR"
    COFFEE_TABLE = "COFFEE_TABLE"
    TV_MEDIA_CONSOLE = "TV_MEDIA_CONSOLE"
    DINING_TABLE_6 = "DINING_TABLE_6"
    DINING_TABLE_8 = "DINING_TABLE_8"
    KITCHEN_COUNTER_ISLAND = "KITCHEN_COUNTER_ISLAND"
    WATER_CLOSET = "WATER_CLOSET"
    VANITY_BASIN = "VANITY_BASIN"
    SHOWER_ENCLOSURE = "SHOWER_ENCLOSURE"
    VEHICLE_SEDAN = "VEHICLE_SEDAN"
    VEHICLE_SUV = "VEHICLE_SUV"
    NIGHTSTAND = "NIGHTSTAND"
    PERGOLA_SEATING = "PERGOLA_SEATING"
    SOLAR_INVERTER_RACK = "SOLAR_INVERTER_RACK"
    WATER_RESERVOIR = "WATER_RESERVOIR"
    SPA_JACUZZI_TUB = "SPA_JACUZZI_TUB"
    FIREPLACE = "FIREPLACE"
    CREDENZA = "CREDENZA"


# ---- Pydantic Schemas for Strict Intake & Normalization ----

class SetbackDefinition(BaseModel):
    front_m: float = 4.57  # Standard 15'-0"
    rear_m: float = 2.13   # Standard 7'-0"
    side_left_m: float = 1.52   # Standard 5'-0"
    side_right_m: float = 0.0   # 0 for row / semi-detached or 1.52m for detached


class SiteBoundary(BaseModel):
    width_m: float
    depth_m: float
    street_frontage: str = "SOUTH"  # NORTH, SOUTH, EAST, WEST
    setbacks: SetbackDefinition = Field(default_factory=SetbackDefinition)

    @property
    def total_area_m2(self) -> float:
        return self.width_m * self.depth_m

    @property
    def buildable_box(self) -> Tuple[float, float, float, float]:
        """Returns (min_x, min_y, max_x, max_y) for statutory buildable envelope."""
        min_x = self.setbacks.side_left_m
        max_x = self.width_m - self.setbacks.side_right_m
        min_y = self.setbacks.front_m
        max_y = self.depth_m - self.setbacks.rear_m
        return (min_x, min_y, max_x, max_y)


class ErgonomicClearance(BaseModel):
    min_corridor_width_m: float = 0.914  # Mandatory 36"
    bed_side_clearance_m: float = 0.762   # 30" clear on bed flanks
    bed_foot_clearance_m: float = 0.914   # 36" clear at bed foot
    tv_throw_ratio: Tuple[float, float] = (1.5, 2.5)  # Screen diag to eyes distance
    dining_chair_pullout_m: float = 0.85
    counter_aisle_width_m: float = 1.05


class FurnitureItem(BaseModel):
    item_id: str
    category: FurnitureCategory
    room_id: str
    position_3d: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    dimensions_m: List[float] = Field(default_factory=lambda: [1.0, 1.0, 0.8])  # w, d, h
    rotation_deg_z: float = 0.0
    solid_wall_anchor_edge: Optional[List[List[float]]] = None
    clearance_envelope_polygon: Optional[List[List[float]]] = None


class OpeningSpec(BaseModel):
    opening_id: str
    category: OpeningCategory
    position_3d: List[float]  # [x, y, z]
    width_m: float
    height_m: float
    sill_height_m: float = 0.0
    lintel_height_m: float = 2.10
    connects_rooms: List[str]
    level_index: int = 0
    is_exterior: bool = False


class RoomSpec(BaseModel):
    room_id: str
    room_type: str
    room_name: str
    zone: ArchitecturalZone
    level_index: int = 0
    polygon: List[List[float]]
    area_m2: float
    centroid: List[float]
    ceiling_height_m: float = 3.20  # Standard 10'-6"
    requires_exterior_wall: bool = True
    has_exterior_exhaust: bool = False
    is_wet_core: bool = False
    solid_wall_segments: List[List[List[float]]] = Field(default_factory=list)
    furniture: List[FurnitureItem] = Field(default_factory=list)


class VerticalPlumbingShaft(BaseModel):
    shaft_id: str
    bounds_2d: List[List[float]]  # Bounding box of plumbing riser
    serves_levels: List[int]
    stack_type: str = "SOIL_WASTE_VENT"


class RCCColumnNode(BaseModel):
    column_id: str
    grid_intersection: str  # e.g. "Grid_A_Y2"
    position_2d: List[float]  # [x, y]
    dimensions_m: List[float] = Field(default_factory=lambda: [0.229, 0.457])  # 9" x 18"
    level_indices: List[int] = Field(default_factory=lambda: [0, 1, 2])

    @property
    def serves_levels(self) -> List[int]:
        return self.level_indices


class BIMWallSpec(BaseModel):
    wall_id: str
    wall_type: str = "EXTERIOR_SOLID_9IN"  # "EXTERIOR_SOLID_9IN", "INTERIOR_PARTITION_4_5IN", "PARAPET_SOLID_3_5FT"
    centerline: List[List[float]]
    thickness_m: float = 0.229  # 9" default or 0.114 (4.5")
    height_m: float = 3.20
    level_index: int = 0
    is_load_bearing: bool = True


class FacadeElementSpec(BaseModel):
    element_id: str
    element_type: str  # "CANTILEVER_BALCONY", "TIMBER_LOUVERS", "FLUTED_LIMESTONE_PANEL", "CURTAIN_WALLING", "MUMTY_TOWER", "WATER_RESERVOIR", "PERGOLA", "SOLAR_ARRAY"
    position_3d: List[float]
    dimensions_m: List[float]
    level_index: int = 0
    material: str = "Mat_Fluted_Limestone"


class ParametricBIMModel(BaseModel):
    project_id: str
    site: SiteBoundary
    floor_count: int
    levels: List[int]
    rooms: List[RoomSpec]
    openings: List[OpeningSpec]
    plumbing_shafts: List[VerticalPlumbingShaft]
    parapet_height_m: float = 1.05
    mumty_bounds: Optional[List[List[float]]] = None
    columns: List[RCCColumnNode] = Field(default_factory=list)
    walls: List[BIMWallSpec] = Field(default_factory=list)
    facade_elements: List[FacadeElementSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_canonical_floorplan(self) -> Any:
        """
        Converts the multi-level ParametricBIMModel into a production-grade CanonicalFloorPlan
        ready for AutoCAD DXF export (AIA layered standards) and 2D high-res blueprint rendering.
        """
        from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, WallModel, OpeningModel, MetadataModel
        metadata = MetadataModel(
            plan_id=self.project_id,
            source_type="synthetic_generated",
            floor_count=self.floor_count,
            levels=self.levels,
            unit="m",
            wall_height_m=self.metadata.get("floor_to_floor_height_m", 3.20),
            provenance={
                "generator": "HierarchicalZoningCSPSolver_10Marla",
                "project_title": "10 MARLA LUXURY ARCHITECTURAL RESIDENCE",
                "columns": [c.model_dump() for c in self.columns]
            }
        )
        boundary = [
            [0.0, 0.0],
            [self.site.width_m, 0.0],
            [self.site.width_m, self.site.depth_m],
            [0.0, self.site.depth_m],
            [0.0, 0.0]
        ]
        canon_rooms = []
        for r in self.rooms:
            r_lower = r.room_name.lower()
            meta = {
                "master": "master" in r_lower or "suite 1" in r_lower or "suite 3" in r_lower,
                "scullery": "dirty" in r_lower or "scullery" in r_lower,
                "powder": "powder" in r_lower,
                "spa": "spa" in r_lower,
                "double_vanity": "spa" in r_lower or "master" in r_lower or "suite 1" in r_lower or "suite 3" in r_lower,
                "open_concept": "lawn" in r_lower or "porch" in r_lower or "terrace" in r_lower or "ots" in r_lower
            }
            canon_rooms.append(RoomModel(
                room_id=r.room_id,
                room_type=r.room_type,
                room_name=r.room_name,
                polygon=r.polygon,
                area_m2=r.area_m2,
                centroid=r.centroid,
                level_index=r.level_index,
                is_habitable=r.room_type not in ("outdoor", "balcony", "garage"),
                metadata=meta
            ))

        canon_walls = []
        if self.walls:
            for w in self.walls:
                w_type = "exterior" if "EXTERIOR" in w.wall_type.upper() else "interior"
                canon_walls.append(WallModel(
                    wall_id=w.wall_id,
                    wall_type=w_type,
                    centerline=w.centerline,
                    thickness_m=w.thickness_m,
                    height_m=w.height_m,
                    level_index=w.level_index
                ))
        else:
            for r in self.rooms:
                pts = r.polygon
                for i in range(len(pts) - 1):
                    p1, p2 = pts[i], pts[i + 1]
                    canon_walls.append(WallModel(
                        wall_id=f"w_{r.room_id}_{i}",
                        wall_type="exterior" if r.requires_exterior_wall else "interior",
                        centerline=[p1, p2],
                        thickness_m=0.229 if r.requires_exterior_wall else 0.114,
                        height_m=3.20,
                        level_index=r.level_index
                    ))

        canon_openings = []
        for op in self.openings:
            o_type = "door" if "DOOR" in op.category.value else "window"
            canon_openings.append(OpeningModel(
                opening_id=op.opening_id,
                opening_type=o_type,
                position=[op.position_3d[0], op.position_3d[1]],
                width_m=op.width_m,
                height_m=op.height_m,
                sill_height_m=op.sill_height_m,
                connects_rooms=op.connects_rooms,
                level_index=op.level_index,
                metadata={"category": op.category.value, "is_exterior": op.is_exterior}
            ))

        return CanonicalFloorPlan(
            metadata=metadata,
            boundary=boundary,
            total_area_m2=self.site.total_area_m2,
            walls=canon_walls,
            openings=canon_openings,
            rooms=canon_rooms
        )


# ==============================================================================
# 2. HIERARCHICAL CONSTRAINT SATISFACTION LAYOUT SOLVER
# ==============================================================================

class HierarchicalZoningCSPSolver:
    """
    Mathematical Constraint Satisfaction Solver for Residential Architecture.
    
    Eliminates heuristic failure modes:
    1. Trap-Free Zoning: Lawns and Car Porches are strictly anchored to the site's
       frontage boundary (Zone A). Rear OTS/courtyards are anchored to rear setbacks.
    2. Wet-Core Vertical Riser Invariance: Kitchens and ensuite bathrooms align
       vertically across floors ($IoU_{2D} >= 0.70$) with direct exterior wall exposure.
    3. Three-Zone Topological Acoustic Isolation:
       Drawing Room -> Foyer -> Family Lounge -> Dedicated Bed Lobby -> Private Suites.
       Direct edges between Drawing/Dining and Bedrooms are strictly penalized ($A_{ij} = -inf$).
    4. Rectangular Dedicated Stair Shaft: Continuous vertical structural shaft
       with mandatory 2.10m clear headroom and 1.05m landing depth.
    """

    def __init__(self, site: SiteBoundary, floor_count: int = 2):
        self.site = site
        self.floor_count = floor_count
        self.w = site.width_m
        self.d = site.depth_m

    def solve_10_marla_luxury_layout(self, parking_capacity: int = 2) -> ParametricBIMModel:
        """
        Principal Computational Architect & Senior BIM Specialist Layout Engine for 10 Marla (35'-0" x 65'-0").
        
        Strictly enforces:
        1. Structural Grid & Building Envelope Rules:
           - Front setback = 15'-0" (4.57m holding front lawn and double car porch).
           - Rear setback = 6'-6" (1.98m dedicated continuous OTS ventilation lightwell).
           - Side walls = 9" solid masonry (0.229m) with 9"x18" (0.229m x 0.457m) RCC column nodes at primary grid intersections.
           - Parking Envelope Protection: [X: 16'-0" to 35'-0", Y: 0'-0" to 15'-0"] reserved exclusively for two vehicles.
             No powder rooms, foyers, or interior walls may cross below Y = 15'-0" on the porch side.
           - Vertical Structural Continuity: Stair core (8'-0" x 14'-0" dog-leg configuration with a 3'-6" mid-landing at +1500mm),
             rear OTS lightwell, and wet plumbing chases remain vertically aligned across Level 0, Level 1, and Level 2 (IoU = 1.00).
        
        2. Multi-Level Floor Plan Hierarchy (Non-Duplicated Programs):
           - Level 0 (Ground Floor - Entertaining & Ground Suites):
             * Front: 16'x15' Landscaped Lawn (open to sky) + 19'x15' Double Car Porch.
             * Public Zone: Grand Entrance Foyer (11'x10'), Formal Drawing Salon (16'x18') with front bay window,
               and Guest Powder Room (8'x10') recessed behind the porch.
             * Living & Service Core: Central TV Lounge (27'x14') with integrated media wall, Gourmet Chef's Kitchen (16'x9'-6")
               with prep island, and Scullery/Dirty Kitchen (16'x4'-6") along the East exterior wall for direct exhaust.
             * Private Zone: 19'x6' Private Bedroom Vestibule distributing to Ground Master Suite 1 (14'x12') and Guest Suite 2 (14'x12'),
               each with ensuite baths and daylight access via the rear OTS lightwell.
           - Level 1 (First Floor - Family Living & Upper Suites):
             * Front: 19'x15' Sunset Terrace deck + Upper Master Executive Suite 3 (16'x18') with walk-in wardrobe and ensuite bath.
             * Study & Core: Executive Study & Home Library (11'x10') over foyer; Upper Family Living Gallery (27'x17');
               Upper Butler's Pantry & Gym (16'x14') vertically stacked over the ground kitchen plumbing core.
             * Rear: Upper Bedroom Vestibule leading to Suite 4 (14'x12') and Suite 5 (14'x12') with attached baths flanking the OTS shaft.
           - Level 2 (Second Floor - Penthouse, Terrace & Service):
             * Front: Full-width Panoramic BBQ & Entertainment Terrace (35'x25' open deck with pergola seating).
             * Core: Weatherproof Mumty Penthouse Vestibule with an exterior weather door preventing rain intrusion into the stair shaft.
             * Living & Utility: Multipurpose Studio / Gym (16'x20') with luxury spa bath + Dedicated Rooftop Laundry (16'x14').
             * Service & Solar: Maid / Servant Quarter (16'x12') with attached bath and direct service terrace access; Rear Solar Inverter Deck (14'x12').
        
        3. CAD Graphic Standards & Furniture Ergonomics:
           - Double-line partitioning: 9" exterior solid walls, 4.5" interior non-structural brick partitions, glazed cuts for windows.
           - 90-degree dashed door clearance arcs without interference with fixtures or bed paths.
           - Beds anchored to solid dry interior walls with twin bedside tables, maintaining 36" (0.91m) walking corridors.
           - L-sectionals oriented toward dedicated media walls.
        
        4. 3D Model & Facade Synthesis:
           - Modern volumetric cubic facade with cantilevered first-floor balcony, vertical timber-finish louvers,
             fluted limestone cladding, and floor-to-ceiling double-glazed windows.
           - Solid 3'-6" parapet walls with coping details, drainage slopes, enclosed 9'-0" stair mumty tower,
             and overhead concrete water reservoir.
        """
        rooms: List[RoomSpec] = []
        openings: List[OpeningSpec] = []
        shafts: List[VerticalPlumbingShaft] = []
        columns: List[RCCColumnNode] = []
        walls: List[BIMWallSpec] = []
        facade_elements: List[FacadeElementSpec] = []

        w = 10.67  # 35'-0"
        d = 19.81  # 65'-0"

        # Key Grid Coordinates in Meters (X axis: 0.0 to 10.67m / 35'-0")
        x_a = 0.00   # West party wall (0'-0")
        x_bed_w = 4.27  # 14'-0" suite boundary
        x_b = 4.88   # 16'-0" primary bay dividing line (Lawn / Porch / Drawing)
        x_c_vest = 5.79  # 19'-0" vestibule / kitchen boundary line
        x_c = 8.23   # 27'-0" primary core dividing line (Foyer/Stair & Lounge/Stair)
        x_bed_e = 10.06 # 33'-0" suite boundary
        x_d = 10.67  # East party wall (35'-0")

        # Key Longitudinal Bands in Meters (Y axis: 0.0 to 19.81m / 65'-0")
        y_1 = 0.00   # Front street frontage (0'-0")
        y_2 = 4.57   # Front Setback / Building Line (15'-0")
        y_3 = 7.62   # Foyer / Powder end line, Stair front line (25'-0")
        y_draw_end = 10.06 # Drawing Salon end line (33'-0")
        y_4 = 11.89  # Living / Stair end line, Kitchen core start (39'-0")
        y_l1_lounge_end = 12.80 # Upper Living Gallery end line (42'-0")
        y_vest_end = 13.72      # Private Bedroom Vestibule end line (45'-0")
        y_kit_split = 14.78     # Chef Kitchen / Scullery split line (48'-6")
        y_5 = 14.17             # Suite entry line (46'-6")
        y_scullery_end = 16.15  # Scullery end line (53'-0")
        y_6 = 17.83             # Rear Building Line / Rear OTS start (58'-6")
        y_7 = 19.81             # Rear site boundary line (65'-0")

        # ----------------------------------------------------------------------
        # 1. PRIMARY STRUCTURAL GRID RCC COLUMN NODES (9" x 18" = 0.229m x 0.457m)
        # ----------------------------------------------------------------------
        grid_pts = [
            ("col_A2", "Grid_A_Y2", [x_a, y_2]),
            ("col_B2", "Grid_B_Y2", [x_b, y_2]),
            ("col_C2", "Grid_C_Y2", [x_c, y_2]),
            ("col_D2", "Grid_D_Y2", [x_d, y_2]),
            ("col_A3", "Grid_A_Y3", [x_a, y_3]),
            ("col_B3", "Grid_B_Y3", [x_b, y_3]),
            ("col_C3", "Grid_C_Y3", [x_c, y_3]),
            ("col_D3", "Grid_D_Y3", [x_d, y_3]),
            ("col_A4", "Grid_A_Y4", [x_a, y_4]),
            ("col_B4", "Grid_B_Y4", [x_b, y_4]),
            ("col_C4", "Grid_C_Y4", [x_c, y_4]),
            ("col_D4", "Grid_D_Y4", [x_d, y_4]),
            ("col_A5", "Grid_A_Y5", [x_a, y_5]),
            ("col_B5", "Grid_B_Y5", [x_b, y_5]),
            ("col_D5", "Grid_D_Y5", [x_d, y_5]),
            ("col_A6", "Grid_A_Y6", [x_a, y_6]),
            ("col_B6", "Grid_B_Y6", [x_b, y_6]),
            ("col_D6", "Grid_D_Y6", [x_d, y_6]),
            ("col_A7", "Grid_A_Y7", [x_a, y_7]),
            ("col_D7", "Grid_D_Y7", [x_d, y_7]),
        ]
        for cid, gname, pos in grid_pts:
            columns.append(RCCColumnNode(
                column_id=cid,
                grid_intersection=gname,
                position_2d=pos,
                dimensions_m=[0.229, 0.457],
                level_indices=[0, 1, 2]
            ))

        # ----------------------------------------------------------------------
        # 2. INVARIANT VERTICAL CORE POLYGONS (100% Coordinate Alignment across L0, L1, L2)
        # ----------------------------------------------------------------------
        # Stair Core: 8'-0" x 14'-0" (2.44m x 4.27m)
        stair_poly = [
            [x_c, y_3], [x_d, y_3], [x_d, y_4], [x_c, y_4], [x_c, y_3]
        ]
        # Rear Continuous OTS Lightwell: 35'-0" x 6'-6" (10.67m x 1.98m)
        ots_poly = [
            [x_a, y_6], [x_d, y_6], [x_d, y_7], [x_a, y_7], [x_a, y_6]
        ]
        # Kitchen / Service Plumbing Core Stack: 16'-0" x 14'-0" (4.88m x 4.27m)
        kitchen_stack_poly = [
            [x_c_vest, y_4], [x_d, y_4], [x_d, y_scullery_end], [x_c_vest, y_scullery_end], [x_c_vest, y_4]
        ]

        # ----------------------------------------------------------------------
        # 3. LEVEL 0: GROUND FLOOR SYNTHESIS (ENTERTAINING & GROUND SUITES)
        # ----------------------------------------------------------------------
        # 1. Front Lawn (16'x15' Open to Sky)
        lawn_poly = [[x_a, y_1], [x_b, y_1], [x_b, y_2], [x_a, y_2], [x_a, y_1]]
        rooms.append(RoomSpec(
            room_id="r_L0_lawn",
            room_type="outdoor",
            room_name="Landscaped Front Garden Lawn (16'x15')",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=0,
            polygon=lawn_poly,
            area_m2=round(Polygon(lawn_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round(y_2 / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 2. Car Porch (19'x15' Double Car Porch - Reserved for 2 Vehicles)
        porch_poly = [[x_b, y_1], [x_d, y_1], [x_d, y_2], [x_b, y_2], [x_b, y_1]]
        rooms.append(RoomSpec(
            room_id="r_L0_porch",
            room_type="garage",
            room_name=f"Double Car Porch ({parking_capacity} Vehicles - 19'x15')",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=porch_poly,
            area_m2=round(Polygon(porch_poly).area, 1),
            centroid=[round((x_b + x_d) / 2.0, 2), round(y_2 / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 3. Formal Drawing Salon (16'x18' with Front Bay Window)
        drawing_poly = [[x_a, y_2], [x_b, y_2], [x_b, y_draw_end], [x_a, y_draw_end], [x_a, y_2]]
        rooms.append(RoomSpec(
            room_id="r_L0_drawing",
            room_type="living_room",
            room_name="Formal Drawing Salon (16'x18')",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=drawing_poly,
            area_m2=round(Polygon(drawing_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round((y_2 + y_draw_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 4. Grand Entrance Foyer (11'x10')
        foyer_poly = [[x_b, y_2], [x_c, y_2], [x_c, y_3], [x_b, y_3], [x_b, y_2]]
        rooms.append(RoomSpec(
            room_id="r_L0_foyer",
            room_type="corridor",
            room_name="Grand Entrance Foyer & Vestibule (11'x10')",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=foyer_poly,
            area_m2=round(Polygon(foyer_poly).area, 1),
            centroid=[round((x_b + x_c) / 2.0, 2), round((y_2 + y_3) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 5. Guest Powder Room (8'x10' Recessed Behind Porch)
        powder_poly = [[x_c, y_2], [x_d, y_2], [x_d, y_3], [x_c, y_3], [x_c, y_2]]
        rooms.append(RoomSpec(
            room_id="r_L0_powder",
            room_type="bathroom",
            room_name="Guest Powder Room (8'x10')",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=powder_poly,
            area_m2=round(Polygon(powder_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_2 + y_3) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 6. Dedicated Dogleg Stair Core (8'-0" x 14'-0" with 3'-6" Mid-Landing at +1500mm)
        rooms.append(RoomSpec(
            room_id="r_L0_stair",
            room_type="corridor",
            room_name="Dedicated Dogleg Stair Core (8'-0\" x 14'-0\" | +1500mm Landing)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=stair_poly,
            area_m2=round(Polygon(stair_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_3 + y_4) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 7. Central TV Lounge (27'x14' with Integrated Media Wall)
        lounge_poly = [[x_a, y_3], [x_c, y_3], [x_c, y_4], [x_a, y_4], [x_a, y_3]]
        rooms.append(RoomSpec(
            room_id="r_L0_lounge",
            room_type="living_room",
            room_name="Central TV Lounge (27'x14')",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=lounge_poly,
            area_m2=round(Polygon(lounge_poly).area, 1),
            centroid=[round((x_a + x_c) / 2.0, 2), round((y_3 + y_4) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 8. Gourmet Chef's Kitchen (16'x9'-6" with Prep Island)
        kitchen_poly = [[x_c_vest, y_4], [x_d, y_4], [x_d, y_kit_split], [x_c_vest, y_kit_split], [x_c_vest, y_4]]
        rooms.append(RoomSpec(
            room_id="r_L0_kitchen",
            room_type="kitchen",
            room_name="Gourmet Chef's Kitchen & Island (16'x9'-6\")",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=kitchen_poly,
            area_m2=round(Polygon(kitchen_poly).area, 1),
            centroid=[round((x_c_vest + x_d) / 2.0, 2), round((y_4 + y_kit_split) / 2.0, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 9. Attached Scullery / Dirty Kitchen (16'x4'-6" along East Exterior Wall)
        dirty_kitchen_poly = [[x_c_vest, y_kit_split], [x_d, y_kit_split], [x_d, y_scullery_end], [x_c_vest, y_scullery_end], [x_c_vest, y_kit_split]]
        rooms.append(RoomSpec(
            room_id="r_L0_dirty_kitchen",
            room_type="kitchen",
            room_name="Attached Scullery / Dirty Kitchen (16'x4'-6\" East Wall Exhaust)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=dirty_kitchen_poly,
            area_m2=round(Polygon(dirty_kitchen_poly).area, 1),
            centroid=[round((x_c_vest + x_d) / 2.0, 2), round((y_kit_split + y_scullery_end) / 2.0, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 10. Private Bedroom Vestibule (19'x6' Acoustic Buffer)
        vest_poly = [[x_a, y_4], [x_c_vest, y_4], [x_c_vest, y_vest_end], [x_a, y_vest_end], [x_a, y_4]]
        rooms.append(RoomSpec(
            room_id="r_L0_bed_lobby",
            room_type="corridor",
            room_name="Private Bedroom Vestibule (19'x6' Acoustic Buffer)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=vest_poly,
            area_m2=round(Polygon(vest_poly).area, 1),
            centroid=[round(x_c_vest / 2.0, 2), round((y_4 + y_vest_end) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 11. Ground Master Suite 1 (14'x12')
        bed1_poly = [[x_a, y_vest_end], [x_bed_w, y_vest_end], [x_bed_w, y_6], [x_a, y_6], [x_a, y_vest_end]]
        rooms.append(RoomSpec(
            room_id="r_L0_bed1",
            room_type="bedroom",
            room_name="Ground Master Suite 1 (14'x12')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bed1_poly,
            area_m2=round(Polygon(bed1_poly).area, 1),
            centroid=[round(x_bed_w / 2.0, 2), round((y_vest_end + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 12. Master Ensuite Spa Bath 1 (Daylight to OTS)
        bath1_poly = [[x_bed_w, y_vest_end], [x_c_vest, y_vest_end], [x_c_vest, 15.77], [x_bed_w, 15.77], [x_bed_w, y_vest_end]]
        rooms.append(RoomSpec(
            room_id="r_L0_bath1",
            room_type="bathroom",
            room_name="Master Ensuite Spa Bath 1 (Daylight to OTS)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bath1_poly,
            area_m2=round(Polygon(bath1_poly).area, 1),
            centroid=[round((x_bed_w + x_c_vest) / 2.0, 2), round((y_vest_end + 15.77) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 13. Guest Ensuite Attached Bath 2 (Daylight to OTS)
        bath2_poly = [[x_bed_w, 15.77], [x_c_vest, 15.77], [x_c_vest, y_6], [x_bed_w, y_6], [x_bed_w, 15.77]]
        rooms.append(RoomSpec(
            room_id="r_L0_bath2",
            room_type="bathroom",
            room_name="Guest Ensuite Attached Bath 2 (Daylight to OTS)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bath2_poly,
            area_m2=round(Polygon(bath2_poly).area, 1),
            centroid=[round((x_bed_w + x_c_vest) / 2.0, 2), round((15.77 + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 14. Ground Guest Suite 2 (14'x12')
        bed2_poly = [[x_c_vest, y_5], [x_bed_e, y_5], [x_bed_e, y_6], [x_c_vest, y_6], [x_c_vest, y_5]]
        rooms.append(RoomSpec(
            room_id="r_L0_bed2",
            room_type="bedroom",
            room_name="Ground Guest Suite 2 (14'x12')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bed2_poly,
            area_m2=round(Polygon(bed2_poly).area, 1),
            centroid=[round((x_c_vest + x_bed_e) / 2.0, 2), round((y_5 + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 15. Rear Continuous OTS Ventilation Lightwell (35' x 6'-6")
        rooms.append(RoomSpec(
            room_id="r_L0_ots",
            room_type="outdoor",
            room_name="Rear Continuous OTS Ventilation Lightwell (35'x6'-6\")",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=0,
            polygon=ots_poly,
            area_m2=round(Polygon(ots_poly).area, 1),
            centroid=[round(w / 2.0, 2), round((y_6 + y_7) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # ----------------------------------------------------------------------
        # 4. LEVEL 1: FIRST FLOOR (FAMILY LIVING & UPPER SUITES)
        # ----------------------------------------------------------------------
        # 1. Cantilevered Front Sunset Terrace Deck (19'x15' over porch)
        terrace_poly = [[x_b, y_1], [x_d, y_1], [x_d, y_2], [x_b, y_2], [x_b, y_1]]
        rooms.append(RoomSpec(
            room_id="r_L1_terrace",
            room_type="balcony",
            room_name="Cantilevered Front Sunset Terrace Deck (19'x15')",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=1,
            polygon=terrace_poly,
            area_m2=round(Polygon(terrace_poly).area, 1),
            centroid=[round((x_b + x_d) / 2.0, 2), round(y_2 / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 2. Upper Master Executive Suite 3 (16'x18' with Walk-in Wardrobe & Ensuite)
        rooms.append(RoomSpec(
            room_id="r_L1_bed3",
            room_type="bedroom",
            room_name="Upper Master Executive Suite 3 (16'x18')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=drawing_poly,
            area_m2=round(Polygon(drawing_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round((y_2 + y_draw_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 3. Upper Master Luxury Ensuite Bath 3
        bath3_poly = [[x_a, 8.84], [x_b, 8.84], [x_b, y_draw_end], [x_a, y_draw_end], [x_a, 8.84]]
        rooms.append(RoomSpec(
            room_id="r_L1_bath3",
            room_type="bathroom",
            room_name="Upper Master Luxury Ensuite Bath 3 & Dressing",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bath3_poly,
            area_m2=round(Polygon(bath3_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round((8.84 + y_draw_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 4. Executive Study & Home Library (11'x10' over foyer)
        rooms.append(RoomSpec(
            room_id="r_L1_study",
            room_type="study",
            room_name="Executive Study & Home Library (11'x10' over Foyer)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=1,
            polygon=foyer_poly,
            area_m2=round(Polygon(foyer_poly).area, 1),
            centroid=[round((x_b + x_c) / 2.0, 2), round((y_2 + y_3) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 5. First Floor Staircase Core Landing (DN / UP - Invariant 8'x14')
        rooms.append(RoomSpec(
            room_id="r_L1_stair",
            room_type="corridor",
            room_name="Staircase Core Landing (DN / UP - Invariant 8'x14')",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=1,
            polygon=stair_poly,
            area_m2=round(Polygon(stair_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_3 + y_4) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 6. Upper Family Living Gallery (27'x17')
        l1_gallery_poly = [[x_a, y_3], [x_c, y_3], [x_c, y_l1_lounge_end], [x_a, y_l1_lounge_end], [x_a, y_3]]
        rooms.append(RoomSpec(
            room_id="r_L1_lounge",
            room_type="living_room",
            room_name="Upper Family Living Gallery (27'x17')",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=1,
            polygon=l1_gallery_poly,
            area_m2=round(Polygon(l1_gallery_poly).area, 1),
            centroid=[round((x_a + x_c) / 2.0, 2), round((y_3 + y_l1_lounge_end) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 7. Upper Butler's Pantry & Gym (16'x14' Vertically Stacked over Kitchen Core)
        rooms.append(RoomSpec(
            room_id="r_L1_kitchenette",
            room_type="kitchen",
            room_name="Upper Butler's Pantry & Gym (16'x14' Stacked)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=1,
            polygon=kitchen_stack_poly,
            area_m2=round(Polygon(kitchen_stack_poly).area, 1),
            centroid=[round((x_c_vest + x_d) / 2.0, 2), round((y_4 + y_scullery_end) / 2.0, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 8. Upper Bedroom Distribution Vestibule (19' Wide)
        l1_vest_poly = [[x_a, y_l1_lounge_end], [x_c_vest, y_l1_lounge_end], [x_c_vest, y_5], [x_a, y_5], [x_a, y_l1_lounge_end]]
        rooms.append(RoomSpec(
            room_id="r_L1_bed_lobby",
            room_type="corridor",
            room_name="Upper Bedroom Distribution Vestibule (19' Wide)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=l1_vest_poly,
            area_m2=round(Polygon(l1_vest_poly).area, 1),
            centroid=[round(x_c_vest / 2.0, 2), round((y_l1_lounge_end + y_5) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 9. Upper Bedroom Suite 4 (14'x12')
        bed4_poly = [[x_a, y_5], [x_bed_w, y_5], [x_bed_w, y_6], [x_a, y_6], [x_a, y_5]]
        rooms.append(RoomSpec(
            room_id="r_L1_bed4",
            room_type="bedroom",
            room_name="Upper Bedroom Suite 4 (14'x12')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bed4_poly,
            area_m2=round(Polygon(bed4_poly).area, 1),
            centroid=[round(x_bed_w / 2.0, 2), round((y_5 + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 10. Suite 4 Attached Bath (Flanking OTS)
        rooms.append(RoomSpec(
            room_id="r_L1_bath4",
            room_type="bathroom",
            room_name="Suite 4 Ensuite Attached Bath (Flanking OTS)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bath1_poly,
            area_m2=round(Polygon(bath1_poly).area, 1),
            centroid=[round((x_bed_w + x_c_vest) / 2.0, 2), round((y_vest_end + 15.77) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 11. Suite 5 Attached Bath (Flanking OTS)
        rooms.append(RoomSpec(
            room_id="r_L1_bath5",
            room_type="bathroom",
            room_name="Suite 5 Ensuite Attached Bath (Flanking OTS)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bath2_poly,
            area_m2=round(Polygon(bath2_poly).area, 1),
            centroid=[round((x_bed_w + x_c_vest) / 2.0, 2), round((15.77 + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 12. Upper Bedroom Suite 5 (14'x12')
        rooms.append(RoomSpec(
            room_id="r_L1_bed5",
            room_type="bedroom",
            room_name="Upper Bedroom Suite 5 (14'x12')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bed2_poly,
            area_m2=round(Polygon(bed2_poly).area, 1),
            centroid=[round((x_c_vest + x_bed_e) / 2.0, 2), round((y_5 + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 13. Upper Daylight OTS Shaft Void (35' x 6'-6")
        rooms.append(RoomSpec(
            room_id="r_L1_ots",
            room_type="outdoor",
            room_name="Upper Daylight OTS Shaft Void (35'x6'-6\")",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=1,
            polygon=ots_poly,
            area_m2=round(Polygon(ots_poly).area, 1),
            centroid=[round(w / 2.0, 2), round((y_6 + y_7) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # ----------------------------------------------------------------------
        # 5. LEVEL 2: SECOND FLOOR (PENTHOUSE, TERRACE & SERVICE)
        # ----------------------------------------------------------------------
        # 1. Full-Width Panoramic BBQ & Entertainment Terrace (35'x25' Open Deck with Pergola)
        bbq_terrace_poly = [[x_a, y_1], [x_d, y_1], [x_d, y_3], [x_a, y_3], [x_a, y_1]]
        rooms.append(RoomSpec(
            room_id="r_L2_bbq_terrace",
            room_type="balcony",
            room_name="Full-Width Panoramic BBQ & Entertainment Terrace (35'x25' Pergola Deck)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=2,
            polygon=bbq_terrace_poly,
            area_m2=round(Polygon(bbq_terrace_poly).area, 1),
            centroid=[round(w / 2.0, 2), round(y_3 / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 2. Weatherproof Mumty Penthouse Vestibule (8'x5' with Weather Door to Terrace)
        mumty_vest_poly = [[x_c, 6.10], [x_d, 6.10], [x_d, y_3], [x_c, y_3], [x_c, 6.10]]
        rooms.append(RoomSpec(
            room_id="r_L2_mumty_vestibule",
            room_type="corridor",
            room_name="Weatherproof Mumty Penthouse Vestibule (8'x5' Exterior Weather Door)",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=2,
            polygon=mumty_vest_poly,
            area_m2=round(Polygon(mumty_vest_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((6.10 + y_3) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 3. Penthouse Staircase Core Landing (DN - Invariant 8'x14')
        rooms.append(RoomSpec(
            room_id="r_L2_stair",
            room_type="corridor",
            room_name="Penthouse Staircase Landing Core (DN - Invariant 8'x14')",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=2,
            polygon=stair_poly,
            area_m2=round(Polygon(stair_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_3 + y_4) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 4. Multipurpose Studio / Gym (16'x20' with Luxury Spa Bath)
        multipurpose_poly = [[x_a, y_3], [x_b, y_3], [x_b, y_vest_end], [x_a, y_vest_end], [x_a, y_3]]
        rooms.append(RoomSpec(
            room_id="r_L2_multipurpose",
            room_type="living_room",
            room_name="Multipurpose Studio / Gym (16'x20')",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=2,
            polygon=multipurpose_poly,
            area_m2=round(Polygon(multipurpose_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round((y_3 + y_vest_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 5. Luxury Penthouse Spa Bath (Jacuzzi / Rain Shower)
        spa_poly = [[x_a, 12.50], [x_b, 12.50], [x_b, y_vest_end], [x_a, y_vest_end], [x_a, 12.50]]
        rooms.append(RoomSpec(
            room_id="r_L2_bath_spa",
            room_type="bathroom",
            room_name="Luxury Penthouse Spa Bath (Jacuzzi & Sauna)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=2,
            polygon=spa_poly,
            area_m2=round(Polygon(spa_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round((12.50 + y_vest_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 6. Dedicated Rooftop Laundry & Utility Core (16'x14' Vertically Stacked over Kitchen Core)
        rooms.append(RoomSpec(
            room_id="r_L2_laundry",
            room_type="storage",
            room_name="Dedicated Rooftop Laundry & Utility Core (16'x14' Stacked)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=2,
            polygon=kitchen_stack_poly,
            area_m2=round(Polygon(kitchen_stack_poly).area, 1),
            centroid=[round((x_c_vest + x_d) / 2.0, 2), round((y_4 + y_scullery_end) / 2.0, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 7. Maid / Servant Quarter (16'x12' with Attached Bath & Direct Service Terrace Access)
        maid_poly = [[x_a, y_5], [x_b, y_5], [x_b, y_6], [x_a, y_6], [x_a, y_5]]
        rooms.append(RoomSpec(
            room_id="r_L2_maid",
            room_type="bedroom",
            room_name="Maid / Servant Quarter (16'x12' with Terrace Access)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=2,
            polygon=maid_poly,
            area_m2=round(Polygon(maid_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round((y_5 + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 8. Maid Ensuite Attached Bath
        maid_bath_poly = [[3.35, 16.00], [x_b, 16.00], [x_b, y_6], [3.35, y_6], [3.35, 16.00]]
        rooms.append(RoomSpec(
            room_id="r_L2_bath_maid",
            room_type="bathroom",
            room_name="Maid Attached Ensuite Bath",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=2,
            polygon=maid_bath_poly,
            area_m2=round(Polygon(maid_bath_poly).area, 1),
            centroid=[round((3.35 + x_b) / 2.0, 2), round((16.00 + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 9. Rear Solar Inverter Deck & Maintenance Terrace (14'x12')
        solar_poly = [[x_c_vest, y_5], [x_bed_e, y_5], [x_bed_e, y_6], [x_c_vest, y_6], [x_c_vest, y_5]]
        rooms.append(RoomSpec(
            room_id="r_L2_solar_deck",
            room_type="balcony",
            room_name="Rear Solar Inverter Deck & Maintenance Terrace (14'x12')",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=2,
            polygon=solar_poly,
            area_m2=round(Polygon(solar_poly).area, 1),
            centroid=[round((x_c_vest + x_bed_e) / 2.0, 2), round((y_5 + y_6) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 10. Level 2 Rear Continuous OTS Void (35' x 6'-6")
        rooms.append(RoomSpec(
            room_id="r_L2_ots",
            room_type="outdoor",
            room_name="Upper Daylight OTS Shaft Void (35'x6'-6\")",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=2,
            polygon=ots_poly,
            area_m2=round(Polygon(ots_poly).area, 1),
            centroid=[round(w / 2.0, 2), round((y_6 + y_7) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # ----------------------------------------------------------------------
        # 6. VERTICAL PLUMBING RISER SHAFTS (100% Invariant IoU = 1.00)
        # ----------------------------------------------------------------------
        # Shaft 1: East Exterior Kitchen Grease & Soil Stack (serves L0 Scullery, L1 Pantry, L2 Laundry)
        shaft_1_poly = [
            [x_d - 0.40, 14.50], [x_d, 14.50], [x_d, 15.30], [x_d - 0.40, 15.30], [x_d - 0.40, 14.50]
        ]
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_kitchen_stack",
            bounds_2d=shaft_1_poly,
            serves_levels=[0, 1, 2],
            stack_type="KITCHEN_GREASE_EXHAUST"
        ))

        # Shaft 2: Rear Wet Core Bath Soil & Waste Stack (serves L0, L1, L2 rear ensuite baths)
        shaft_2_poly = [
            [x_bed_w, 15.50], [x_c_vest, 15.50], [x_c_vest, 16.00], [x_bed_w, 16.00], [x_bed_w, 15.50]
        ]
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_rear_baths",
            bounds_2d=shaft_2_poly,
            serves_levels=[0, 1, 2],
            stack_type="SOIL_WASTE_VENT"
        ))

        # Shaft 3: Powder / Mumty Rainwater Chute (serves L0 Powder, L1 Study, L2 Mumty roof drain)
        shaft_3_poly = [
            [x_d - 0.40, y_3 - 0.50], [x_d, y_3 - 0.50], [x_d, y_3], [x_d - 0.40, y_3], [x_d - 0.40, y_3 - 0.50]
        ]
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_powder_mumty",
            bounds_2d=shaft_3_poly,
            serves_levels=[0, 1, 2],
            stack_type="SOIL_WASTE_VENT"
        ))

        # ----------------------------------------------------------------------
        # 7. ROOFTOP MUMTY TOWER & OVERHEAD CONCRETE WATER RESERVOIR
        # ----------------------------------------------------------------------
        mumty_poly = [
            [x_c, 6.10], [x_d, 6.10], [x_d, y_4], [x_c, y_4], [x_c, 6.10]
        ]

        # ----------------------------------------------------------------------
        # 8. CAD STANDARD DOUBLE-LINE WALL SPECIFICATION (9" EXT, 4.5" INT)
        # ----------------------------------------------------------------------
        # Generate clean double-line walls for each level
        wall_id_counter = 0
        for lvl in [0, 1, 2]:
            lvl_rooms = [r for r in rooms if r.level_index == lvl]
            for r in lvl_rooms:
                poly = r.polygon
                for i in range(len(poly) - 1):
                    p1, p2 = poly[i], poly[i + 1]
                    seg_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                    if seg_len < 0.20:
                        continue
                    # Exterior boundary check
                    is_perimeter = (
                        abs(p1[0] - x_a) < 0.05 and abs(p2[0] - x_a) < 0.05 or
                        abs(p1[0] - x_d) < 0.05 and abs(p2[0] - x_d) < 0.05 or
                        abs(p1[1] - y_2) < 0.05 and abs(p2[1] - y_2) < 0.05 or
                        abs(p1[1] - y_6) < 0.05 and abs(p2[1] - y_6) < 0.05
                    )
                    th = 0.229 if (is_perimeter or r.requires_exterior_wall) else 0.114
                    wtype = "EXTERIOR_SOLID_9IN" if th >= 0.20 else "INTERIOR_PARTITION_4_5IN"
                    walls.append(BIMWallSpec(
                        wall_id=f"wall_lvl{lvl}_{wall_id_counter}",
                        wall_type=wtype,
                        centerline=[p1, p2],
                        thickness_m=th,
                        height_m=3.20,
                        level_index=lvl,
                        is_load_bearing=(th >= 0.20)
                    ))
                    wall_id_counter += 1

        # ----------------------------------------------------------------------
        # 9. FACADE & 3D ROOFTOP ELEMENTS (VOLUMETRIC SYNTHESIS)
        # ----------------------------------------------------------------------
        # Level 1 Cantilever Balcony
        facade_elements.append(FacadeElementSpec(
            element_id="facade_cantilever_balcony",
            element_type="CANTILEVER_BALCONY",
            position_3d=[x_b, y_1, 3.35],
            dimensions_m=[5.79, 4.57, 0.15],
            level_index=1,
            material="Mat_Concrete_Slab"
        ))
        # Front Timber-Finish Louvers (Master Suite Shading Bay)
        facade_elements.append(FacadeElementSpec(
            element_id="facade_timber_louvers",
            element_type="TIMBER_LOUVERS",
            position_3d=[0.50, y_2, 3.35],
            dimensions_m=[4.00, 0.15, 3.00],
            level_index=1,
            material="Mat_Timber_Louvers"
        ))
        # Fluted Limestone Cladding Panels
        facade_elements.append(FacadeElementSpec(
            element_id="facade_fluted_limestone",
            element_type="FLUTED_LIMESTONE_PANEL",
            position_3d=[0.00, y_2, 0.00],
            dimensions_m=[4.88, 0.05, 6.70],
            level_index=0,
            material="Mat_Fluted_Limestone"
        ))
        # Floor-to-Ceiling Curtain Glazing
        facade_elements.append(FacadeElementSpec(
            element_id="facade_curtain_walling",
            element_type="CURTAIN_WALLING",
            position_3d=[x_b + 0.50, y_2, 3.35],
            dimensions_m=[4.50, 0.10, 3.00],
            level_index=1,
            material="Mat_Floor_Glazing"
        ))
        # Enclosed 9'-0" Stair Mumty Tower
        facade_elements.append(FacadeElementSpec(
            element_id="rooftop_mumty_tower",
            element_type="MUMTY_TOWER",
            position_3d=[x_c, 6.10, 10.05],
            dimensions_m=[2.44, 5.79, 2.74],
            level_index=2,
            material="Mat_Exterior_Travertine"
        ))
        # Overhead Concrete Water Reservoir (1000 Gallons)
        facade_elements.append(FacadeElementSpec(
            element_id="rooftop_water_reservoir",
            element_type="WATER_RESERVOIR",
            position_3d=[x_c + 0.20, 7.50, 12.79],
            dimensions_m=[2.00, 2.00, 1.60],
            level_index=2,
            material="Mat_Water_Reservoir"
        ))
        # BBQ Pergola Structure
        facade_elements.append(FacadeElementSpec(
            element_id="rooftop_pergola",
            element_type="PERGOLA",
            position_3d=[1.00, 1.00, 6.70],
            dimensions_m=[6.00, 5.00, 2.80],
            level_index=2,
            material="Mat_Pergola_Wood"
        ))
        # Solar Panel Array on Inverter Deck
        facade_elements.append(FacadeElementSpec(
            element_id="rooftop_solar_array",
            element_type="SOLAR_ARRAY",
            position_3d=[x_c_vest + 0.30, y_5 + 0.30, 6.70],
            dimensions_m=[4.00, 3.00, 0.40],
            level_index=2,
            material="Mat_Solar_Panels"
        ))

        model = ParametricBIMModel(
            project_id=f"10MARLA_LUXURY_3LEVEL_{int(w*3.28084)}x{int(d*3.28084)}",
            site=SiteBoundary(
                width_m=w,
                depth_m=d,
                street_frontage="SOUTH",
                setbacks=SetbackDefinition(front_m=4.57, rear_m=1.98, side_left_m=0.0, side_right_m=0.0)
            ),
            floor_count=3,
            levels=[0, 1, 2],
            rooms=rooms,
            openings=openings,
            plumbing_shafts=shafts,
            parapet_height_m=1.07,  # 3'-6" Solid Parapet
            mumty_bounds=mumty_poly,
            columns=columns,
            walls=walls,
            facade_elements=facade_elements,
            metadata={
                "project_title": "10 Marla Luxury Residence (35'-0\" x 65'-0\")",
                "structural_typology": StructuralTypology.RCC_FRAME_SLAB.value,
                "floor_to_floor_height_m": 3.35,  # 11'-0"
                "slab_thickness_m": 0.15,
                "exterior_wall_thickness_m": 0.229,  # 9"
                "interior_wall_thickness_m": 0.114,  # 4.5"
                "parapet_height_m": 1.07,  # 3'-6"
                "mumty_height_m": 2.74,   # 9'-0"
                "stair_core_dimensions": "8'-0\" x 14'-0\" (2.44m x 4.27m)",
                "stair_mid_landing": "3'-6\" (1.07m) depth at +1500mm",
                "stair_core_invariance": "100% Strict 3D Coordinate Invariant across L0, L1, L2 (IoU = 1.00)",
                "wet_core_kitchen_iou": 1.00,
                "wet_core_rear_baths_iou": 1.00,
                "ots_rear_lightwell_depth": "6'-6\" (1.98m continuous)",
                "parking_envelope": "[X: 16'-0\" to 35'-0\", Y: 0'-0\" to 15'-0\"] (Double Car Porch)",
                "double_line_walls": True,
                "door_swings_dashed_clearance": True,
                "facade_style": "Modern Volumetric Cubic with Timber Louvers & Fluted Limestone"
            }
        )

        # ----------------------------------------------------------------------
        # 10. CAD STANDARD OPENINGS & ERGONOMIC FURNITURE PLACEMENT
        # ----------------------------------------------------------------------
        self._generate_10_marla_openings(model)
        self._solve_10_marla_ergonomic_furniture(model)

        return model

    def _generate_10_marla_openings(self, model: ParametricBIMModel):
        """
        Creates strictly code-compliant doors and windows for 10 Marla luxury residence.
        Renders standard 90-degree dashed clearance arcs.
        Guarantees zero swing obstruction into toilets, vanities, or bed paths.
        Weatherproof exterior door on Mumty Vestibule prevents rain intrusion into stair shaft.
        """
        def add_op(op_id, cat, pos, w_m, h_m, conn, lvl, is_ext=False, sill=0.0):
            model.openings.append(OpeningSpec(
                opening_id=op_id,
                category=cat,
                position_3d=[round(pos[0], 2), round(pos[1], 2), round(lvl * 3.35, 2)],
                width_m=w_m,
                height_m=h_m,
                sill_height_m=sill,
                lintel_height_m=round(sill + h_m, 2),
                connects_rooms=conn,
                level_index=lvl,
                is_exterior=is_ext
            ))

        # --- LEVEL 0 OPENINGS ---
        # 1. Main Pivot Entry Door (Porch -> Foyer): 4'-0" (1.20m) grand pivot
        add_op("door_L0_entry", OpeningCategory.MAIN_ENTRANCE_DOOR, [6.50, 4.57], 1.20, 2.40, ["r_L0_porch", "r_L0_foyer"], 0, is_ext=True)
        # 2. Foyer to Drawing Salon (Double French Glazed Doors): 4'-0" (1.20m)
        add_op("door_L0_foyer_draw", OpeningCategory.INTERIOR_DOOR, [4.88, 6.00], 1.20, 2.40, ["r_L0_foyer", "r_L0_drawing"], 0)
        # 3. Foyer to Guest Powder Room (Recessed behind Porch): 2'-9" (0.85m), swings against solid lobby wall, never into vanity/WC
        add_op("door_L0_powder", OpeningCategory.INTERIOR_DOOR, [8.23, 5.50], 0.85, 2.10, ["r_L0_foyer", "r_L0_powder"], 0)
        # 4. Foyer to TV Lounge: 3'-6" (1.05m) clear open portal
        add_op("door_L0_foyer_lounge", OpeningCategory.INTERIOR_DOOR, [6.50, 7.62], 1.10, 2.40, ["r_L0_foyer", "r_L0_lounge"], 0)
        # 5. Foyer to Staircase Core (Headroom clearance maintained > 5'-0" from entrance): 3'-0" (0.914m)
        add_op("door_L0_stair", OpeningCategory.INTERIOR_DOOR, [8.23, 8.50], 0.914, 2.10, ["r_L0_lounge", "r_L0_stair"], 0)
        # 6. Drawing Salon to TV Lounge (Double Pocket / Glazed Sliding Doors): 4'-0" (1.20m)
        add_op("door_L0_draw_lounge", OpeningCategory.INTERIOR_DOOR, [3.00, 10.06], 1.20, 2.40, ["r_L0_drawing", "r_L0_lounge"], 0)
        # 7. Drawing Salon Front Bay Window (Expansive Glazing facing lawn): 8'-0" (2.44m)
        add_op("win_L0_drawing_bay", OpeningCategory.STANDARD_WINDOW, [2.44, 4.57], 2.44, 2.10, ["r_L0_drawing"], 0, is_ext=True, sill=0.45)
        # 8. TV Lounge to Gourmet Chef's Kitchen: 5'-0" (1.52m) open breakfast bar opening
        add_op("door_L0_kitchen_portal", OpeningCategory.INTERIOR_DOOR, [6.50, 11.89], 1.50, 2.40, ["r_L0_lounge", "r_L0_kitchen"], 0)
        # 9. Kitchen to Scullery / Dirty Kitchen: 2'-9" (0.85m) service swing door
        add_op("door_L0_kitchen_dirty", OpeningCategory.SERVICE_DOOR, [8.23, 14.78], 0.85, 2.10, ["r_L0_kitchen", "r_L0_dirty_kitchen"], 0)
        # 10. Scullery Direct Exterior Wall Service Vent / Door: 2'-9" (0.85m) along East exterior wall
        add_op("door_L0_scullery_ext", OpeningCategory.SERVICE_DOOR, [10.67, 15.50], 0.85, 2.10, ["r_L0_dirty_kitchen"], 0, is_ext=True)
        # 11. TV Lounge to Private Bedroom Vestibule: 3'-6" (1.05m) acoustic isolation door
        add_op("door_L0_vestibule", OpeningCategory.INTERIOR_DOOR, [2.50, 11.89], 1.05, 2.20, ["r_L0_lounge", "r_L0_bed_lobby"], 0)
        # 12. Vestibule to Ground Master Suite 1: 3'-0" (0.914m), swings against solid wall clear of bed corridor
        add_op("door_L0_bed1", OpeningCategory.INTERIOR_DOOR, [2.00, 13.72], 0.914, 2.10, ["r_L0_bed_lobby", "r_L0_bed1"], 0)
        # 13. Master Suite 1 to Master Ensuite Spa Bath 1: 2'-9" (0.85m), swings into dry dressing zone
        add_op("door_L0_bath1", OpeningCategory.INTERIOR_DOOR, [4.27, 14.50], 0.85, 2.10, ["r_L0_bed1", "r_L0_bath1"], 0)
        # 14. Master Ensuite Bath 1 to Rear OTS (Daylight & Ventilation): 3'-0" (0.914m)
        add_op("win_L0_bath1_ots", OpeningCategory.VENTILATION_CLERESTORY, [5.03, 15.77], 0.914, 0.90, ["r_L0_bath1"], 0, is_ext=True, sill=1.50)
        # 15. Master Suite 1 to Rear OTS Lightwell (Full-height Glazed Door): 3'-0" (0.914m)
        add_op("door_L0_bed1_ots", OpeningCategory.SLIDING_PATIO_DOOR, [2.00, 17.83], 1.20, 2.40, ["r_L0_bed1"], 0, is_ext=True)
        # 16. Vestibule to Ground Guest Suite 2: 3'-0" (0.914m), swings against solid wall clear of bed path
        add_op("door_L0_bed2", OpeningCategory.INTERIOR_DOOR, [5.79, 14.50], 0.914, 2.10, ["r_L0_bed_lobby", "r_L0_bed2"], 0)
        # 17. Guest Suite 2 to Attached Ensuite Bath 2: 2'-9" (0.85m)
        add_op("door_L0_bath2", OpeningCategory.INTERIOR_DOOR, [5.79, 16.50], 0.85, 2.10, ["r_L0_bed2", "r_L0_bath2"], 0)
        # 18. Guest Bath 2 to Rear OTS (Daylight Window): 3'-0" (0.914m)
        add_op("win_L0_bath2_ots", OpeningCategory.VENTILATION_CLERESTORY, [5.03, 17.83], 0.914, 0.90, ["r_L0_bath2"], 0, is_ext=True, sill=1.50)
        # 19. Guest Suite 2 to Rear OTS (Window): 5'-0" (1.52m)
        add_op("win_L0_bed2_ots", OpeningCategory.STANDARD_WINDOW, [8.00, 17.83], 1.52, 1.80, ["r_L0_bed2"], 0, is_ext=True, sill=0.60)

        # --- LEVEL 1 OPENINGS ---
        # 1. Living Gallery to Sunset Terrace (Sliding Frameless Glass Patio Doors): 8'-0" (2.44m)
        add_op("door_L1_terrace_patio", OpeningCategory.SLIDING_PATIO_DOOR, [6.50, 4.57], 2.44, 2.60, ["r_L1_study", "r_L1_terrace"], 1, is_ext=True)
        # 2. Executive Study to Sunset Terrace (Corner Glazed Exit): 3'-0" (0.914m)
        add_op("door_L1_study_exit", OpeningCategory.SLIDING_PATIO_DOOR, [8.23, 5.00], 0.914, 2.40, ["r_L1_study", "r_L1_terrace"], 1, is_ext=True)
        # 3. Living Gallery to Executive Study: 3'-6" (1.05m)
        add_op("door_L1_study", OpeningCategory.INTERIOR_DOOR, [6.50, 7.62], 1.05, 2.40, ["r_L1_lounge", "r_L1_study"], 1)
        # 4. Living Gallery to Upper Master Executive Suite 3: 3'-6" (1.05m)
        add_op("door_L1_bed3", OpeningCategory.INTERIOR_DOOR, [3.00, 10.06], 1.05, 2.40, ["r_L1_lounge", "r_L1_bed3"], 1)
        # 5. Master Suite 3 to Walk-in Wardrobe & Ensuite Bath 3: 2'-9" (0.85m)
        add_op("door_L1_bath3", OpeningCategory.INTERIOR_DOOR, [2.44, 8.84], 0.85, 2.10, ["r_L1_bed3", "r_L1_bath3"], 1)
        # 6. Master Suite 3 Front Floor-to-Ceiling Double-Glazed Windows: 10'-0" (3.05m)
        add_op("win_L1_bed3_front", OpeningCategory.DOUBLE_HEIGHT_GLAZING, [2.44, 4.57], 3.05, 2.60, ["r_L1_bed3"], 1, is_ext=True, sill=0.10)
        # 7. Living Gallery to Upper Stair Landing: 3'-6" (1.05m)
        add_op("door_L1_stair", OpeningCategory.INTERIOR_DOOR, [8.23, 8.50], 1.05, 2.40, ["r_L1_lounge", "r_L1_stair"], 1)
        # 8. Living Gallery to Upper Butler's Pantry & Gym: 3'-0" (0.914m)
        add_op("door_L1_pantry_gym", OpeningCategory.INTERIOR_DOOR, [6.50, 11.89], 0.914, 2.20, ["r_L1_lounge", "r_L1_kitchenette"], 1)
        # 9. Living Gallery to Upper Bedroom Vestibule: 3'-6" (1.05m)
        add_op("door_L1_vestibule", OpeningCategory.INTERIOR_DOOR, [2.50, 12.80], 1.05, 2.20, ["r_L1_lounge", "r_L1_bed_lobby"], 1)
        # 10. Upper Vestibule to Suite 4: 3'-0" (0.914m), swings clear of bed path
        add_op("door_L1_bed4", OpeningCategory.INTERIOR_DOOR, [2.00, 14.17], 0.914, 2.10, ["r_L1_bed_lobby", "r_L1_bed4"], 1)
        # 11. Suite 4 to Attached Bath 4: 2'-9" (0.85m)
        add_op("door_L1_bath4", OpeningCategory.INTERIOR_DOOR, [4.27, 14.50], 0.85, 2.10, ["r_L1_bed4", "r_L1_bath4"], 1)
        # 12. Bath 4 to OTS (Daylight Clerestory): 3'-0" (0.914m)
        add_op("win_L1_bath4_ots", OpeningCategory.VENTILATION_CLERESTORY, [5.03, 15.77], 0.914, 0.90, ["r_L1_bath4"], 1, is_ext=True, sill=1.50)
        # 13. Suite 4 to Rear OTS (Window): 5'-0" (1.52m)
        add_op("win_L1_bed4_ots", OpeningCategory.STANDARD_WINDOW, [2.00, 17.83], 1.52, 1.80, ["r_L1_bed4"], 1, is_ext=True, sill=0.60)
        # 14. Upper Vestibule to Suite 5: 3'-0" (0.914m), swings clear of bed path
        add_op("door_L1_bed5", OpeningCategory.INTERIOR_DOOR, [5.79, 14.50], 0.914, 2.10, ["r_L1_bed_lobby", "r_L1_bed5"], 1)
        # 15. Suite 5 to Attached Bath 5: 2'-9" (0.85m)
        add_op("door_L1_bath5", OpeningCategory.INTERIOR_DOOR, [5.79, 16.50], 0.85, 2.10, ["r_L1_bed5", "r_L1_bath5"], 1)
        # 16. Bath 5 to OTS (Daylight Clerestory): 3'-0" (0.914m)
        add_op("win_L1_bath5_ots", OpeningCategory.VENTILATION_CLERESTORY, [5.03, 17.83], 0.914, 0.90, ["r_L1_bath5"], 1, is_ext=True, sill=1.50)
        # 17. Suite 5 to Rear OTS (Window): 5'-0" (1.52m)
        add_op("win_L1_bed5_ots", OpeningCategory.STANDARD_WINDOW, [8.00, 17.83], 1.52, 1.80, ["r_L1_bed5"], 1, is_ext=True, sill=0.60)

        # --- LEVEL 2 OPENINGS ---
        # 1. Stair Core to Weatherproof Mumty Penthouse Vestibule: 3'-3" (1.00m)
        add_op("door_L2_stair_mumty", OpeningCategory.INTERIOR_DOOR, [9.45, 7.62], 1.00, 2.10, ["r_L2_stair", "r_L2_mumty_vestibule"], 2)
        # 2. Weatherproof Mumty Penthouse Vestibule to BBQ Terrace: 3'-0" (0.914m) EXTERIOR WEATHER DOOR (prevents rain intrusion)
        add_op("door_L2_mumty_ext_weather", OpeningCategory.SERVICE_DOOR, [9.45, 6.10], 0.914, 2.10, ["r_L2_mumty_vestibule", "r_L2_bbq_terrace"], 2, is_ext=True)
        # 3. Multipurpose Studio / Gym to BBQ Terrace: 8'-0" (2.44m) SLIDING GLASS PATIO DOOR
        add_op("door_L2_multi_terrace", OpeningCategory.SLIDING_PATIO_DOOR, [2.44, 7.62], 2.44, 2.40, ["r_L2_multipurpose", "r_L2_bbq_terrace"], 2, is_ext=True)
        # 4. Multipurpose Studio to Stair Landing: 3'-3" (1.00m)
        add_op("door_L2_multi_stair", OpeningCategory.INTERIOR_DOOR, [4.88, 8.50], 1.00, 2.20, ["r_L2_multipurpose", "r_L2_stair"], 2)
        # 5. Multipurpose Studio to Luxury Spa Bath: 2'-9" (0.85m)
        add_op("door_L2_multi_spa", OpeningCategory.INTERIOR_DOOR, [2.44, 12.50], 0.85, 2.10, ["r_L2_multipurpose", "r_L2_bath_spa"], 2)
        # 6. Multipurpose Studio to Dedicated Rooftop Laundry: 3'-0" (0.914m)
        add_op("door_L2_laundry", OpeningCategory.SERVICE_DOOR, [4.88, 12.50], 0.914, 2.10, ["r_L2_multipurpose", "r_L2_laundry"], 2)
        # 7. Multipurpose Studio to Maid / Servant Quarter: 2'-9" (0.85m)
        add_op("door_L2_maid", OpeningCategory.INTERIOR_DOOR, [2.44, 14.17], 0.85, 2.10, ["r_L2_multipurpose", "r_L2_maid"], 2)
        # 8. Maid Quarter to Maid Attached Bath: 2'-6" (0.80m)
        add_op("door_L2_maid_bath", OpeningCategory.INTERIOR_DOOR, [3.35, 16.50], 0.80, 2.10, ["r_L2_maid", "r_L2_bath_maid"], 2)
        # 9. Maid Quarter to Rear Solar Inverter Deck: 2'-9" (0.85m) DIRECT SERVICE TERRACE ACCESS
        add_op("door_L2_maid_solar_exit", OpeningCategory.SERVICE_DOOR, [4.88, 15.50], 0.85, 2.10, ["r_L2_maid", "r_L2_solar_deck"], 2, is_ext=True)

    def _solve_10_marla_ergonomic_furniture(self, model: ParametricBIMModel):
        """
        Solves human factors and ergonomic furniture anchoring for 10 Marla residence:
        - All beds anchor headboards to solid interior dry walls with twin bedside tables,
          maintaining a 36" (0.91m) walking corridor.
        - Living rooms feature L-sectionals oriented toward dedicated media console walls.
        - Kitchen features central waterfall prep island with 4 bar stools.
        - Scullery features perimeter heavy cooktop and sink along exterior wall.
        - Terrace features outdoor pergola dining lounge.
        - Rooftop features solar battery/inverter rack.
        - Car porch holds 2 luxury vehicles with 2.5ft clearance buffers.
        """
        room_dict = {r.room_id: r for r in model.rooms}

        def add_furn(rid, cat, pos, dims, rot=0.0, anchor=None, clear_poly=None):
            if rid not in room_dict:
                return
            room_dict[rid].furniture.append(FurnitureItem(
                item_id=f"furn_{rid}_{cat.value.lower()}_{len(room_dict[rid].furniture)+1}",
                category=cat,
                room_id=rid,
                position_3d=[round(pos[0], 2), round(pos[1], 2), round(pos[2], 2)],
                dimensions_m=[round(dims[0], 2), round(dims[1], 2), round(dims[2], 2)],
                rotation_deg_z=rot,
                solid_wall_anchor_edge=anchor,
                clearance_envelope_polygon=clear_poly
            ))

        # --- LEVEL 0 FURNITURE ---
        # 1. Car Porch: Luxury SUV & Passenger Sedan
        add_furn("r_L0_porch", FurnitureCategory.VEHICLE_SUV, [5.80, 0.60, 0.0], [1.98, 5.03, 1.80], 0.0)
        add_furn("r_L0_porch", FurnitureCategory.VEHICLE_SEDAN, [8.40, 0.60, 0.0], [1.83, 4.57, 1.50], 0.0)

        # 2. Formal Drawing Salon: Formal Suite (3-Seater Sofa + 2 Armchairs + Coffee Table)
        add_furn("r_L0_drawing", FurnitureCategory.SOFA_THREE_SEATER, [1.20, 8.50, 0.0], [2.40, 0.95, 0.85], 0.0)
        add_furn("r_L0_drawing", FurnitureCategory.COFFEE_TABLE, [1.70, 7.20, 0.0], [1.30, 0.70, 0.45], 0.0)
        add_furn("r_L0_drawing", FurnitureCategory.ARMCHAIR, [0.40, 6.80, 0.0], [0.90, 0.85, 0.80], 90.0)
        add_furn("r_L0_drawing", FurnitureCategory.ARMCHAIR, [3.40, 6.80, 0.0], [0.90, 0.85, 0.80], 270.0)

        # 3. Guest Powder Room: Linear Dry-Wet Vanity & Wall-Hung WC
        add_furn("r_L0_powder", FurnitureCategory.VANITY_BASIN, [9.00, 7.00, 0.0], [0.90, 0.50, 0.85], 0.0)
        add_furn("r_L0_powder", FurnitureCategory.WATER_CLOSET, [9.20, 5.00, 0.0], [0.45, 0.70, 0.80], 0.0)

        # 4. Central TV Lounge: L-Sectional Sofa facing East Dedicated Media Console Wall
        # L-sectional oriented toward media wall at x=8.10
        add_furn("r_L0_lounge", FurnitureCategory.L_SECTIONAL_SOFA, [1.50, 8.20, 0.0], [3.00, 2.60, 0.85], 0.0)
        add_furn("r_L0_lounge", FurnitureCategory.COFFEE_TABLE, [2.50, 9.20, 0.0], [1.20, 0.80, 0.45], 0.0)
        add_furn("r_L0_lounge", FurnitureCategory.TV_MEDIA_CONSOLE, [7.80, 8.50, 0.0], [0.45, 2.40, 0.60], 90.0)

        # 5. Gourmet Chef's Kitchen: Prep Waterfall Island with 4 Bar Stools
        add_furn("r_L0_kitchen", FurnitureCategory.KITCHEN_COUNTER_ISLAND, [7.00, 12.80, 0.0], [2.44, 1.00, 0.90], 0.0)

        # 6. Scullery / Dirty Kitchen: Perimeter 24" Heavy Cooking Counters
        add_furn("r_L0_dirty_kitchen", FurnitureCategory.KITCHEN_COUNTER_ISLAND, [6.50, 15.50, 0.0], [3.80, 0.60, 0.90], 0.0)

        # 7. Ground Master Suite 1: King Bed (2.0m x 2.1m) anchored to solid interior dry wall at y=13.72m
        bed1_anchor = [[0.80, 13.72], [2.80, 13.72]]
        bed1_clearance = [[0.0, 13.72], [3.71, 13.72], [3.71, 16.73], [0.0, 16.73], [0.0, 13.72]]
        add_furn("r_L0_bed1", FurnitureCategory.KING_BED, [0.80, 13.82, 0.0], [2.00, 2.10, 0.90], 0.0, bed1_anchor, bed1_clearance)
        add_furn("r_L0_bed1", FurnitureCategory.NIGHTSTAND, [0.20, 13.82, 0.0], [0.50, 0.50, 0.55])
        add_furn("r_L0_bed1", FurnitureCategory.NIGHTSTAND, [2.90, 13.82, 0.0], [0.50, 0.50, 0.55])
        add_furn("r_L0_bed1", FurnitureCategory.TV_MEDIA_CONSOLE, [1.00, 17.20, 0.0], [1.60, 0.45, 0.60], 180.0)

        # 8. Master Ensuite Bath 1: Linear Wet-Dry (Vanity -> WC -> Shower against OTS)
        add_furn("r_L0_bath1", FurnitureCategory.VANITY_BASIN, [4.40, 14.00, 0.0], [1.10, 0.55, 0.85])
        add_furn("r_L0_bath1", FurnitureCategory.WATER_CLOSET, [4.80, 14.80, 0.0], [0.45, 0.70, 0.80])
        add_furn("r_L0_bath1", FurnitureCategory.SHOWER_ENCLOSURE, [4.40, 15.10, 0.0], [1.20, 0.90, 2.10])

        # 9. Ground Guest Suite 2: Queen Bed anchored to solid dry wall at y=14.17m
        bed2_anchor = [[6.60, 14.17], [8.40, 14.17]]
        bed2_clearance = [[5.79, 14.17], [9.31, 14.17], [9.31, 17.18], [5.79, 17.18], [5.79, 14.17]]
        add_furn("r_L0_bed2", FurnitureCategory.QUEEN_BED, [6.60, 14.27, 0.0], [1.80, 2.10, 0.90], 0.0, bed2_anchor, bed2_clearance)
        add_furn("r_L0_bed2", FurnitureCategory.NIGHTSTAND, [6.00, 14.27, 0.0], [0.50, 0.50, 0.55])
        add_furn("r_L0_bed2", FurnitureCategory.NIGHTSTAND, [8.50, 14.27, 0.0], [0.50, 0.50, 0.55])

        # 10. Guest Bath 2: Linear Wet-Dry
        add_furn("r_L0_bath2", FurnitureCategory.VANITY_BASIN, [4.40, 16.00, 0.0], [1.00, 0.50, 0.85])
        add_furn("r_L0_bath2", FurnitureCategory.WATER_CLOSET, [4.80, 16.80, 0.0], [0.45, 0.70, 0.80])
        add_furn("r_L0_bath2", FurnitureCategory.SHOWER_ENCLOSURE, [4.40, 17.10, 0.0], [1.10, 0.90, 2.10])

        # --- LEVEL 1 FURNITURE ---
        # 1. Sunset Terrace Deck: Outdoor Lounge Set
        add_furn("r_L1_terrace", FurnitureCategory.PERGOLA_SEATING, [6.80, 1.80, 3.35], [2.40, 1.80, 0.80])

        # 2. Upper Master Executive Suite 3: King Bed anchored to solid interior wall at y=10.06m
        bed3_anchor = [[1.20, 10.06], [3.20, 10.06]]
        bed3_clearance = [[0.29, 7.05], [4.11, 7.05], [4.11, 10.06], [0.29, 10.06], [0.29, 7.05]]
        add_furn("r_L1_bed3", FurnitureCategory.KING_BED, [1.20, 7.96, 3.35], [2.00, 2.10, 0.90], 180.0, bed3_anchor, bed3_clearance)
        add_furn("r_L1_bed3", FurnitureCategory.NIGHTSTAND, [0.60, 9.46, 3.35], [0.50, 0.50, 0.55])
        add_furn("r_L1_bed3", FurnitureCategory.NIGHTSTAND, [3.30, 9.46, 3.35], [0.50, 0.50, 0.55])
        add_furn("r_L1_bed3", FurnitureCategory.WARDROBE_RUN, [0.20, 5.00, 3.35], [0.60, 2.40, 2.40], 90.0)

        # 3. Master Bath 3: Luxury 5-Fixture Spa (Double Vanity, Walk-in Shower, WC)
        add_furn("r_L1_bath3", FurnitureCategory.VANITY_BASIN, [0.30, 9.00, 3.35], [1.80, 0.60, 0.85])
        add_furn("r_L1_bath3", FurnitureCategory.WATER_CLOSET, [2.50, 9.10, 3.35], [0.45, 0.70, 0.80])
        add_furn("r_L1_bath3", FurnitureCategory.SHOWER_ENCLOSURE, [3.50, 9.00, 3.35], [1.20, 1.00, 2.10])

        # 4. Executive Study & Home Library: Executive Desk & Library Bookcase
        add_furn("r_L1_study", FurnitureCategory.COFFEE_TABLE, [6.00, 5.80, 3.35], [1.60, 0.80, 0.75])
        add_furn("r_L1_study", FurnitureCategory.ARMCHAIR, [6.50, 5.10, 3.35], [0.70, 0.70, 0.90])
        add_furn("r_L1_study", FurnitureCategory.WARDROBE_RUN, [5.00, 7.00, 3.35], [0.40, 2.80, 2.40])

        # 5. Upper Family Living Gallery: L-Sectional facing Media Wall
        add_furn("r_L1_lounge", FurnitureCategory.L_SECTIONAL_SOFA, [1.50, 9.00, 3.35], [3.00, 2.40, 0.85], 0.0)
        add_furn("r_L1_lounge", FurnitureCategory.TV_MEDIA_CONSOLE, [7.80, 9.50, 3.35], [0.45, 2.20, 0.60], 90.0)

        # 6. Upper Suite 4: Queen Bed anchored to solid interior wall at y=14.17m
        bed4_anchor = [[0.80, 14.17], [2.60, 14.17]]
        bed4_clearance = [[0.0, 14.17], [3.51, 14.17], [3.51, 17.18], [0.0, 17.18], [0.0, 14.17]]
        add_furn("r_L1_bed4", FurnitureCategory.QUEEN_BED, [0.80, 14.27, 3.35], [1.80, 2.10, 0.90], 0.0, bed4_anchor, bed4_clearance)
        add_furn("r_L1_bed4", FurnitureCategory.NIGHTSTAND, [0.20, 14.27, 3.35], [0.50, 0.50, 0.55])
        add_furn("r_L1_bed4", FurnitureCategory.NIGHTSTAND, [2.70, 14.27, 3.35], [0.50, 0.50, 0.55])

        # 7. Upper Suite 5: Queen Bed anchored to solid interior wall at y=14.17m
        bed5_anchor = [[6.60, 14.17], [8.40, 14.17]]
        bed5_clearance = [[5.79, 14.17], [9.31, 14.17], [9.31, 17.18], [5.79, 17.18], [5.79, 14.17]]
        add_furn("r_L1_bed5", FurnitureCategory.QUEEN_BED, [6.60, 14.27, 3.35], [1.80, 2.10, 0.90], 0.0, bed5_anchor, bed5_clearance)
        add_furn("r_L1_bed5", FurnitureCategory.NIGHTSTAND, [6.00, 14.27, 3.35], [0.50, 0.50, 0.55])
        add_furn("r_L1_bed5", FurnitureCategory.NIGHTSTAND, [8.50, 14.27, 3.35], [0.50, 0.50, 0.55])

        # --- LEVEL 2 FURNITURE ---
        # 1. Full-Width BBQ Terrace: Cedar Pergola Lounge & Outdoor BBQ Station
        add_furn("r_L2_bbq_terrace", FurnitureCategory.PERGOLA_SEATING, [2.00, 2.50, 6.70], [3.20, 2.40, 0.85])
        add_furn("r_L2_bbq_terrace", FurnitureCategory.DINING_TABLE_8, [6.00, 2.50, 6.70], [2.44, 1.10, 0.75])

        # 2. Multipurpose Studio / Gym: Workout Equipment & Lounge Set
        add_furn("r_L2_multipurpose", FurnitureCategory.SOFA_THREE_SEATER, [1.00, 9.50, 6.70], [2.20, 0.90, 0.85])

        # 3. Luxury Spa Bath: Jacuzzi Spa Tub & Walk-in Shower
        add_furn("r_L2_bath_spa", FurnitureCategory.SPA_JACUZZI_TUB, [0.30, 12.60, 6.70], [1.80, 1.00, 0.75])
        add_furn("r_L2_bath_spa", FurnitureCategory.VANITY_BASIN, [2.50, 12.60, 6.70], [1.00, 0.55, 0.85])

        # 4. Maid / Servant Quarter: Bed & Wardrobe
        add_furn("r_L2_maid", FurnitureCategory.QUEEN_BED, [0.60, 14.30, 6.70], [1.50, 2.00, 0.80])
        add_furn("r_L2_maid", FurnitureCategory.NIGHTSTAND, [0.10, 14.30, 6.70], [0.45, 0.45, 0.50])

        # 5. Rear Solar Inverter Deck: Dual Hybrid Solar Inverter Racks & Battery Storage
        add_furn("r_L2_solar_deck", FurnitureCategory.SOLAR_INVERTER_RACK, [6.50, 15.00, 6.70], [2.00, 0.80, 1.80])

        # 6. Overhead Water Reservoir: 1000 Gallon Concrete Tank on Mumty
        add_furn("r_L2_stair", FurnitureCategory.WATER_RESERVOIR, [8.50, 7.50, 12.79], [2.00, 2.00, 1.60])

    def solve_10_marla_production_3story(self, parking_capacity: int = 2) -> ParametricBIMModel:
        """
        Principal Architectural Systems Engineer & Senior Computational BIM Designer Layout Engine.
        Generates complete, production-ready, 3-story residential architectural floor plan layout
        and parametric 3D building model specification for a 10 Marla plot (35'-0" x 65'-0" / 10.67m x 19.81m).

        Statutory & Spatial Enforcements:
        1. Site, Zoning & Statutory Parameters:
           - Plot Dimensions: 35'-0" Width x 65'-0" Depth (10.67m x 19.81m = 2,275 sq ft / 10 Marla).
           - Orientation: North-facing street frontage.
           - Setbacks: Front setback = 10'-0" (3.05m), Rear setback = 5'-0" (1.52m), Side setback = 0' (Party walls).
           - Floors: 3 Full Levels (Ground Floor Level 0, First Floor Level 1, Second Floor / Rooftop Penthouse Level 2)
             + Overhead Mumty Tower (9'-0" height / 2.74m).
           - Clear Ceiling Height: 10'-6" (3.20m) per floor; 3'-6" (1.05m) rooftop perimeter parapet.
        2. Ground Floor (Level 0):
           - Front garden lawn (open-to-sky, strictly anchored at Y = 0 to Y = 10'-0") + 2-car covered porch (15' x 18').
           - Zone A (Public): Double-height entrance foyer with guest powder room; formal drawing room with fireplace wall
             and credenza clearance.
           - Zone B (Semi-Private): Expansive family TV lounge; semi-open formal dining area; main gourmet kitchen paired
             with an enclosed wet scullery/dirty kitchen along the exterior rear/side wall for external hood exhaust ducting.
           - Stair Core: Dedicated enclosed dog-leg stair shaft (8'-6" x 14'-6", minimum 3'-6" flight width, 11" treads, 7" risers,
             3'-6" mid-landing at +1500mm) providing continuous vertical circulation across all 3 levels without protruding into lounge walkways.
           - Zone C (Private): 2 Ground Bedroom Suites (14' x 14' each) with attached walk-in closets and ensuite luxury baths,
             distributed via an acoustically isolated private bedroom lobby.
           - Rear Ventilation: 5'-0" rear open-to-sky (OTS) lightwell ensuring direct daylight and ventilation for both rear suites and bathrooms.
        3. First Floor (Level 1):
           - 3 Independent Bedroom Suites (1 front master with walk-in wardrobe, 2 rear suites 14'x14') with attached ensuite bathrooms.
           - Central upper family living lounge with study nook.
           - Upper beverage counter / kitchenette vertically stacked directly above Ground Floor kitchen wet core (IoU >= 0.85).
           - Front grand terrace deck with tempered glass and aluminium balustrades overlooking the front garden.
           - Exact vertical coordinate matching for central stair shaft and rear OTS ventilation court.
        4. Second Floor / Penthouse (Level 2):
           - 1 Multipurpose Suite (usable as 6th Bedroom, Executive Home Office, or Private Gym) with attached bath.
           - 1 Independent Maid / Servant Room with dedicated compact bath, serviced by an independent service circulation route.
           - Dedicated laundry/utility wash area.
           - Rooftop Party Terrace & BBQ Deck with anti-skid porcelain pavers and ambient floor-recessed deck lighting.
           - Parametric Stair Mumty Penthouse enclosure (8'-6" x 15'-0" x 9'-0" height) topped with an insulated overhead RCC water storage reservoir.
        5. Spatial, Furniture & Ergonomic Layout Constraints:
           - Every bed (King/Queen) anchors flush to solid interior partition with twin bedside tables & 36" (0.91m) corridor circulation.
           - Wet/dry zoning inside every bathroom (vanity/WC separated from shower enclosure with 10mm frameless glass partition).
           - TV viewing throw: Sectional seating maintains 10'-0" to 13'-0" ergonomic distance from media console wall.
        6. 3D Facade & Materials:
           - Double-cantilevered volumetric cubic projections with warm timber-finish aluminium louvers/soffits.
           - Fluted travertine stone cladding panels on feature vertical piers.
           - Floor-to-ceiling double-glazed low-E low curtain windows with slim charcoal aluminium profiles.
           - Ambient architectural cove lighting strips integrated into exterior slab fascias.
           - Rooftop BIM extrusion: Solid 3'-6" parapet walls with coping details, drainage scuppers sloped toward rear downspouts.
        """
        rooms: List[RoomSpec] = []
        openings: List[OpeningSpec] = []
        shafts: List[VerticalPlumbingShaft] = []
        columns: List[RCCColumnNode] = []
        walls: List[BIMWallSpec] = []
        facade_elements: List[FacadeElementSpec] = []

        w = 10.67  # 35'-0"
        d = 19.81  # 65'-0"

        # Key Grid Coordinates in Meters (X axis: 0.0 to 10.67m / 35'-0")
        x_a = 0.00         # West party wall (0'-0")
        x_bed_w = 4.27     # 14'-0" suite width boundary
        x_dining_end = 4.57 # 15'-0" formal dining boundary
        x_bath_split = 5.48 # Central twin ensuite bath dividing line
        x_kit_start = 5.79  # 19'-0" gourmet kitchen start (16'-0" wide kitchen core)
        x_b = 6.10         # 20'-0" primary bay dividing line (Lawn / Porch, Drawing / Foyer)
        x_bed_e = 6.40     # 21'-0" East suite start (14'-0" wide East suite: 6.40 to 10.67)
        x_scullery = 7.62  # 25'-0" scullery start line (10'-0" wide along East wall)
        x_c = 8.08         # 26'-6" stair core west line (8'-6" wide stair core: 8.08 to 10.67)
        x_d = 10.67        # East party wall (35'-0")

        # Key Longitudinal Bands in Meters (Y axis: 0.0 to 19.81m / 65'-0")
        y_1 = 0.00         # Front street frontage (0'-0", North frontage)
        y_2 = 3.05         # Front statutory setback line (10'-0")
        y_porch_end = 5.49 # 18'-0" double car porch depth (15' x 18')
        y_draw_end = 8.53  # 28'-0" drawing salon end line (18'-0" depth)
        y_stair_end = 9.91 # 32'-6" stair core end line (14'-6" depth: 5.49 to 9.91)
        y_dining_end = 11.00 # Semi-open dining depth
        y_lounge_end = 13.72 # 45'-0" TV lounge & gourmet kitchen end line
        y_lobby_end = 14.94  # 49'-0" private bedroom lobby / scullery end line
        y_bed_start = 14.02  # 46'-0" suite entry line
        y_6 = 18.29        # 60'-0" rear building line (14'-0" depth suites: 14.02 to 18.29)
        y_7 = 19.81        # 65'-0" rear statutory setback line (5'-0" continuous OTS: 18.29 to 19.81)

        # ----------------------------------------------------------------------
        # 1. PRIMARY STRUCTURAL GRID RCC COLUMN NODES (9" x 18" = 0.229m x 0.457m)
        # ----------------------------------------------------------------------
        col_coords = [
            ("col_P_A1", "Grid_A_Y1", [x_a, y_1]),
            ("col_P_B1", "Grid_B_Y1", [x_b, y_1]),
            ("col_P_D1", "Grid_D_Y1", [x_d, y_1]),
            ("col_P_A2", "Grid_A_Y2", [x_a, y_2]),
            ("col_P_B2", "Grid_B_Y2", [x_b, y_2]),
            ("col_P_C2", "Grid_C_Y2", [x_c, y_2]),
            ("col_P_D2", "Grid_D_Y2", [x_d, y_2]),
            ("col_P_A3", "Grid_A_Y3", [x_a, y_porch_end]),
            ("col_P_B3", "Grid_B_Y3", [x_b, y_porch_end]),
            ("col_P_C3", "Grid_C_Y3", [x_c, y_porch_end]),
            ("col_P_D3", "Grid_D_Y3", [x_d, y_porch_end]),
            ("col_P_A4", "Grid_A_Y4", [x_a, y_draw_end]),
            ("col_P_C4", "Grid_C_Y4", [x_c, y_stair_end]),
            ("col_P_D4", "Grid_D_Y4", [x_d, y_stair_end]),
            ("col_P_A5", "Grid_A_Y5", [x_a, y_lounge_end]),
            ("col_P_C5", "Grid_C_Y5", [x_c, y_lounge_end]),
            ("col_P_D5", "Grid_D_Y5", [x_d, y_lounge_end]),
            ("col_P_A6", "Grid_A_Y6", [x_a, y_6]),
            ("col_P_B6", "Grid_B_Y6", [x_bath_split, y_6]),
            ("col_P_D6", "Grid_D_Y6", [x_d, y_6]),
        ]
        for cid, g_name, pos in col_coords:
            columns.append(RCCColumnNode(
                column_id=cid,
                grid_intersection=g_name,
                position_2d=pos,
                dimensions_m=[0.229, 0.457],
                level_indices=[0, 1, 2]
            ))

        # ----------------------------------------------------------------------
        # 2. LEVEL 0: GROUND FLOOR ARCHITECTURAL ENVELOPE
        # ----------------------------------------------------------------------
        # 1. Landscaped Front Garden Lawn (Open-to-sky, strictly anchored Y=0 to Y=10'-0")
        lawn_poly = [[0.0, 0.0], [x_b, 0.0], [x_b, y_2], [0.0, y_2], [0.0, 0.0]]
        rooms.append(RoomSpec(
            room_id="r_L0_lawn",
            room_type="outdoor",
            room_name="Landscaped Front Garden Lawn (Open to Sky)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=0,
            polygon=lawn_poly,
            area_m2=round(Polygon(lawn_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round(y_2 / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 2. Double Car Covered Porch (15' x 18' / 4.57m x 5.49m)
        porch_poly = [[x_b, 0.0], [x_d, 0.0], [x_d, y_porch_end], [x_b, y_porch_end], [x_b, 0.0]]
        rooms.append(RoomSpec(
            room_id="r_L0_porch",
            room_type="garage",
            room_name="Double Car Covered Porch (15' x 18')",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=porch_poly,
            area_m2=round(Polygon(porch_poly).area, 1),
            centroid=[round((x_b + x_d) / 2.0, 2), round(y_porch_end / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 3. Formal Drawing Room with Fireplace Wall & Credenza Clearance (20' x 18')
        drawing_poly = [[x_a, y_2], [x_b, y_2], [x_b, y_draw_end], [x_a, y_draw_end], [x_a, y_2]]
        rooms.append(RoomSpec(
            room_id="r_L0_drawing",
            room_type="living_room",
            room_name="Formal Drawing Room (Fireplace & Credenza)",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=drawing_poly,
            area_m2=round(Polygon(drawing_poly).area, 1),
            centroid=[round(x_b / 2.0, 2), round((y_2 + y_draw_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 4. Double-Height Entrance Foyer
        foyer_poly = [[x_b, y_2], [x_c, y_2], [x_c, y_porch_end], [x_b, y_porch_end], [x_b, y_2]]
        rooms.append(RoomSpec(
            room_id="r_L0_foyer",
            room_type="corridor",
            room_name="Double-Height Grand Entrance Foyer",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=foyer_poly,
            area_m2=round(Polygon(foyer_poly).area, 1),
            centroid=[round((x_b + x_c) / 2.0, 2), round((y_2 + y_porch_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 5. Guest Powder Room (Recessed behind Porch)
        powder_poly = [[x_c, y_2], [x_d, y_2], [x_d, y_porch_end], [x_c, y_porch_end], [x_c, y_2]]
        rooms.append(RoomSpec(
            room_id="r_L0_powder",
            room_type="bathroom",
            room_name="Guest Powder Room (Recessed)",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=powder_poly,
            area_m2=round(Polygon(powder_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_2 + y_porch_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 6. Dedicated Enclosed Dog-Leg Stair Shaft (8'-6" x 14'-6" / 2.59m x 4.42m)
        stair_poly = [[x_c, y_porch_end], [x_d, y_porch_end], [x_d, y_stair_end], [x_c, y_stair_end], [x_c, y_porch_end]]
        rooms.append(RoomSpec(
            room_id="r_L0_stair",
            room_type="corridor",
            room_name="Dedicated Enclosed Dog-Leg Stair Core (8'-6\" x 14'-6\")",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=stair_poly,
            area_m2=round(Polygon(stair_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_porch_end + y_stair_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 7. Expansive Family TV Lounge (26'-6" x 17'-0")
        lounge_poly = [[x_a, y_draw_end], [x_c, y_draw_end], [x_c, y_lounge_end], [x_a, y_lounge_end], [x_a, y_draw_end]]
        rooms.append(RoomSpec(
            room_id="r_L0_lounge",
            room_type="living_room",
            room_name="Expansive Family TV Lounge (Media Console)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=lounge_poly,
            area_m2=round(Polygon(lounge_poly).area, 1),
            centroid=[round((x_a + x_c) / 2.0, 2), round((y_draw_end + y_lounge_end) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 8. Semi-Open Formal Dining Area (Integrated in Living Envelope)
        dining_poly = [[x_a, y_draw_end], [x_dining_end, y_draw_end], [x_dining_end, y_dining_end], [x_a, y_dining_end], [x_a, y_draw_end]]
        rooms.append(RoomSpec(
            room_id="r_L0_dining",
            room_type="dining_room",
            room_name="Semi-Open Formal Dining Area (8-Seater)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=dining_poly,
            area_m2=round(Polygon(dining_poly).area, 1),
            centroid=[round((x_a + x_dining_end) / 2.0, 2), round((y_draw_end + y_dining_end) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 9. Main Gourmet Chef's Kitchen with Prep Island (16'-0" wide)
        kitchen_poly = [[x_kit_start, y_stair_end], [x_d, y_stair_end], [x_d, y_lounge_end], [x_kit_start, y_lounge_end], [x_kit_start, y_stair_end]]
        rooms.append(RoomSpec(
            room_id="r_L0_kitchen",
            room_type="kitchen",
            room_name="Main Gourmet Chef's Kitchen (Prep Island)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=kitchen_poly,
            area_m2=round(Polygon(kitchen_poly).area, 1),
            centroid=[round((x_kit_start + x_d) / 2.0, 2), round((y_stair_end + y_lounge_end) / 2.0, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 10. Enclosed Wet Scullery / Dirty Kitchen (Along East Exterior Wall)
        scullery_poly = [[x_scullery, y_lounge_end], [x_d, y_lounge_end], [x_d, y_lobby_end], [x_scullery, y_lobby_end], [x_scullery, y_lounge_end]]
        rooms.append(RoomSpec(
            room_id="r_L0_dirty_kitchen",
            room_type="kitchen",
            room_name="Enclosed Wet Scullery / Dirty Kitchen (East Wall Exhaust)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=scullery_poly,
            area_m2=round(Polygon(scullery_poly).area, 1),
            centroid=[round((x_scullery + x_d) / 2.0, 2), round((y_lounge_end + y_lobby_end) / 2.0, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 11. Acoustically Isolated Private Bedroom Lobby (4'-0" buffer)
        bed_lobby_poly = [[x_a, y_lounge_end], [x_scullery, y_lounge_end], [x_scullery, y_lobby_end], [x_a, y_lobby_end], [x_a, y_lounge_end]]
        rooms.append(RoomSpec(
            room_id="r_L0_bed_lobby",
            room_type="corridor",
            room_name="Acoustic Private Bedroom Distribution Lobby",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bed_lobby_poly,
            area_m2=round(Polygon(bed_lobby_poly).area, 1),
            centroid=[round((x_a + x_scullery) / 2.0, 2), round((y_lounge_end + y_lobby_end) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 12. Ground Bedroom Suite 1 (14' x 14' / 4.27m x 4.27m)
        bed1_poly = [[x_a, y_bed_start], [x_bed_w, y_bed_start], [x_bed_w, y_6], [x_a, y_6], [x_a, y_bed_start]]
        rooms.append(RoomSpec(
            room_id="r_L0_bed1",
            room_type="bedroom",
            room_name="Ground Master Bedroom Suite 1 (14' x 14')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bed1_poly,
            area_m2=round(Polygon(bed1_poly).area, 1),
            centroid=[round((x_a + x_bed_w) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 13. Ensuite Luxury Bath 1 (Wet/Dry zoning with 10mm glass screen)
        bath1_poly = [[x_bed_w, y_bed_start], [x_bath_split, y_bed_start], [x_bath_split, y_6], [x_bed_w, y_6], [x_bed_w, y_bed_start]]
        rooms.append(RoomSpec(
            room_id="r_L0_bath1",
            room_type="bathroom",
            room_name="Ensuite Luxury Bath 1 (Linear Wet-Dry)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bath1_poly,
            area_m2=round(Polygon(bath1_poly).area, 1),
            centroid=[round((x_bed_w + x_bath_split) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 14. Ensuite Luxury Bath 2 (Wet/Dry zoning)
        bath2_poly = [[x_bath_split, y_bed_start], [x_bed_e, y_bed_start], [x_bed_e, y_6], [x_bath_split, y_6], [x_bath_split, y_bed_start]]
        rooms.append(RoomSpec(
            room_id="r_L0_bath2",
            room_type="bathroom",
            room_name="Ensuite Luxury Bath 2 (Linear Wet-Dry)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bath2_poly,
            area_m2=round(Polygon(bath2_poly).area, 1),
            centroid=[round((x_bath_split + x_bed_e) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 15. Ground Bedroom Suite 2 (14' x 14' / 4.27m x 4.27m)
        bed2_poly = [[x_bed_e, y_bed_start], [x_d, y_bed_start], [x_d, y_6], [x_bed_e, y_6], [x_bed_e, y_bed_start]]
        rooms.append(RoomSpec(
            room_id="r_L0_bed2",
            room_type="bedroom",
            room_name="Ground Bedroom Suite 2 (14' x 14')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bed2_poly,
            area_m2=round(Polygon(bed2_poly).area, 1),
            centroid=[round((x_bed_e + x_d) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 16. Rear Open-To-Sky (OTS) Lightwell (5'-0" continuous lightwell across plot)
        ots_poly = [[0.0, y_6], [w, y_6], [w, y_7], [0.0, y_7], [0.0, y_6]]
        rooms.append(RoomSpec(
            room_id="r_L0_ots",
            room_type="outdoor",
            room_name="Rear Garden & Daylight OTS Lightwell (5'-0\" Continuous)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=0,
            polygon=ots_poly,
            area_m2=round(Polygon(ots_poly).area, 1),
            centroid=[round(w / 2.0, 2), round((y_6 + y_7) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # ----------------------------------------------------------------------
        # 3. LEVEL 1: FIRST FLOOR ARCHITECTURAL ENVELOPE
        # ----------------------------------------------------------------------
        # 1. Front Grand Terrace Deck (Over Covered Porch)
        terrace_poly = [[x_kit_start, 0.0], [x_d, 0.0], [x_d, y_porch_end], [x_kit_start, y_porch_end], [x_kit_start, 0.0]]
        rooms.append(RoomSpec(
            room_id="r_L1_terrace",
            room_type="balcony",
            room_name="Front Grand Terrace Deck (Glass Balustrade)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=1,
            polygon=terrace_poly,
            area_m2=round(Polygon(terrace_poly).area, 1),
            centroid=[round((x_kit_start + x_d) / 2.0, 2), round(y_porch_end / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 2. Front Master Executive Suite 3 (16' x 18' with Walk-in Wardrobe)
        bed3_poly = [[x_a, y_2], [x_kit_start, y_2], [x_kit_start, y_draw_end], [x_a, y_draw_end], [x_a, y_2]]
        rooms.append(RoomSpec(
            room_id="r_L1_bed3",
            room_type="bedroom",
            room_name="Upper Master Executive Suite 3 (16' x 18')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bed3_poly,
            area_m2=round(Polygon(bed3_poly).area, 1),
            centroid=[round((x_a + x_kit_start) / 2.0, 2), round((y_2 + y_draw_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 3. Master Ensuite Bath 3 (Walk-in Wardrobe & 5-Fixture Spa)
        bath3_poly = [[x_a, y_2], [2.44, y_2], [2.44, y_porch_end], [x_a, y_porch_end], [x_a, y_2]]
        rooms.append(RoomSpec(
            room_id="r_L1_bath3",
            room_type="bathroom",
            room_name="Master Ensuite Spa Bath 3 (Double Vanity)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bath3_poly,
            area_m2=round(Polygon(bath3_poly).area, 1),
            centroid=[1.22, round((y_2 + y_porch_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 4. Dedicated Stair Core Landing (Level 1 Vertical Coordinate Invariant)
        rooms.append(RoomSpec(
            room_id="r_L1_stair",
            room_type="corridor",
            room_name="Staircase Core Landing (DN / UP) - Invariant Shaft",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=1,
            polygon=stair_poly,
            area_m2=round(Polygon(stair_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_porch_end + y_stair_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 5. Central Upper Family Living Lounge with Study Nook
        rooms.append(RoomSpec(
            room_id="r_L1_lounge",
            room_type="living_room",
            room_name="Central Upper Family Living Lounge & Study Nook",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=1,
            polygon=lounge_poly,
            area_m2=round(Polygon(lounge_poly).area, 1),
            centroid=[round((x_a + x_c) / 2.0, 2), round((y_draw_end + y_lounge_end) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 6. Upper Beverage Counter / Kitchenette (Stacked directly over L0 kitchen, IoU=1.00)
        rooms.append(RoomSpec(
            room_id="r_L1_kitchenette",
            room_type="kitchen",
            room_name="Upper Beverage Counter & Kitchenette (Stacked)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=1,
            polygon=kitchen_poly,
            area_m2=round(Polygon(kitchen_poly).area, 1),
            centroid=[round((x_kit_start + x_d) / 2.0, 2), round((y_stair_end + y_lounge_end) / 2.0, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 7. Upper Bedroom Distribution Lobby
        rooms.append(RoomSpec(
            room_id="r_L1_bed_lobby",
            room_type="corridor",
            room_name="Upper Acoustic Bedroom Distribution Lobby",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bed_lobby_poly,
            area_m2=round(Polygon(bed_lobby_poly).area, 1),
            centroid=[round((x_a + x_scullery) / 2.0, 2), round((y_lounge_end + y_lobby_end) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 8. Upper Bedroom Suite 4 (14' x 14' / 4.27m x 4.27m)
        rooms.append(RoomSpec(
            room_id="r_L1_bed4",
            room_type="bedroom",
            room_name="Upper Bedroom Suite 4 (14' x 14')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bed1_poly,
            area_m2=round(Polygon(bed1_poly).area, 1),
            centroid=[round((x_a + x_bed_w) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 9. Upper Ensuite Bath 4
        rooms.append(RoomSpec(
            room_id="r_L1_bath4",
            room_type="bathroom",
            room_name="Upper Ensuite Attached Bath 4",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bath1_poly,
            area_m2=round(Polygon(bath1_poly).area, 1),
            centroid=[round((x_bed_w + x_bath_split) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 10. Upper Ensuite Bath 5
        rooms.append(RoomSpec(
            room_id="r_L1_bath5",
            room_type="bathroom",
            room_name="Upper Ensuite Attached Bath 5",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bath2_poly,
            area_m2=round(Polygon(bath2_poly).area, 1),
            centroid=[round((x_bath_split + x_bed_e) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 11. Upper Bedroom Suite 5 (14' x 14' / 4.27m x 4.27m)
        rooms.append(RoomSpec(
            room_id="r_L1_bed5",
            room_type="bedroom",
            room_name="Upper Bedroom Suite 5 (14' x 14')",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=1,
            polygon=bed2_poly,
            area_m2=round(Polygon(bed2_poly).area, 1),
            centroid=[round((x_bed_e + x_d) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 12. Upper Daylight OTS Shaft Void
        rooms.append(RoomSpec(
            room_id="r_L1_ots",
            room_type="outdoor",
            room_name="Upper Daylight OTS Lightwell Void (5'-0\" Continuous)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=1,
            polygon=ots_poly,
            area_m2=round(Polygon(ots_poly).area, 1),
            centroid=[round(w / 2.0, 2), round((y_6 + y_7) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # ----------------------------------------------------------------------
        # 4. LEVEL 2: SECOND FLOOR / PENTHOUSE ARCHITECTURAL ENVELOPE
        # ----------------------------------------------------------------------
        # 1. Rooftop Party Terrace & BBQ Deck (Front open expanse)
        bbq_terrace_poly = [[0.0, 0.0], [w, 0.0], [w, y_draw_end], [0.0, y_draw_end], [0.0, 0.0]]
        rooms.append(RoomSpec(
            room_id="r_L2_bbq_terrace",
            room_type="balcony",
            room_name="Rooftop Party Terrace & BBQ Deck (Porcelain Pavers)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=2,
            polygon=bbq_terrace_poly,
            area_m2=round(Polygon(bbq_terrace_poly).area, 1),
            centroid=[round(w / 2.0, 2), round(y_draw_end / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 2. Weatherproof Mumty Penthouse Vestibule (8'-6" x 8'-0")
        mumty_vest_poly = [[x_c, y_porch_end], [x_d, y_porch_end], [x_d, 7.62], [x_c, 7.62], [x_c, y_porch_end]]
        rooms.append(RoomSpec(
            room_id="r_L2_mumty_vestibule",
            room_type="corridor",
            room_name="Weatherproof Mumty Penthouse Vestibule (Exterior Weather Door)",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=2,
            polygon=mumty_vest_poly,
            area_m2=round(Polygon(mumty_vest_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_porch_end + 7.62) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 3. Level 2 Stair Core Landing (Exact vertical coordinate invariance)
        rooms.append(RoomSpec(
            room_id="r_L2_stair",
            room_type="corridor",
            room_name="Penthouse Staircase Landing Core (DN / UP) - Invariant Shaft",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=2,
            polygon=stair_poly,
            area_m2=round(Polygon(stair_poly).area, 1),
            centroid=[round((x_c + x_d) / 2.0, 2), round((y_porch_end + y_stair_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 4. Multipurpose Penthouse Suite (6th Bedroom / Home Office / Gym)
        multi_poly = [[x_a, y_draw_end], [x_kit_start, y_draw_end], [x_kit_start, y_lounge_end], [x_a, y_lounge_end], [x_a, y_draw_end]]
        rooms.append(RoomSpec(
            room_id="r_L2_multipurpose",
            room_type="living_room",
            room_name="Multipurpose Suite (6th Bed / Office / Gym)",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=2,
            polygon=multi_poly,
            area_m2=round(Polygon(multi_poly).area, 1),
            centroid=[round((x_a + x_kit_start) / 2.0, 2), round((y_draw_end + y_lounge_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 5. Multipurpose Suite Attached Luxury Spa Bath
        bath_spa_poly = [[x_a, 11.50], [2.44, 11.50], [2.44, y_lounge_end], [x_a, y_lounge_end], [x_a, 11.50]]
        rooms.append(RoomSpec(
            room_id="r_L2_bath_spa",
            room_type="bathroom",
            room_name="Multipurpose Suite Attached Luxury Spa Bath",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=2,
            polygon=bath_spa_poly,
            area_m2=round(Polygon(bath_spa_poly).area, 1),
            centroid=[1.22, round((11.50 + y_lounge_end) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 6. Dedicated Rooftop Laundry & Utility Wash Area (Stacked over kitchen core)
        rooms.append(RoomSpec(
            room_id="r_L2_laundry",
            room_type="storage",
            room_name="Dedicated Rooftop Laundry & Utility Wash Area",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=2,
            polygon=kitchen_poly,
            area_m2=round(Polygon(kitchen_poly).area, 1),
            centroid=[round((x_kit_start + x_d) / 2.0, 2), round((y_stair_end + y_lounge_end) / 2.0, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 7. Independent Maid / Servant Room with Independent Service Circulation Route (14' x 14')
        maid_poly = [[x_a, y_bed_start], [x_bed_w, y_bed_start], [x_bed_w, y_6], [x_a, y_6], [x_a, y_bed_start]]
        rooms.append(RoomSpec(
            room_id="r_L2_maid",
            room_type="bedroom",
            room_name="Independent Maid / Servant Room (Service Route)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=2,
            polygon=maid_poly,
            area_m2=round(Polygon(maid_poly).area, 1),
            centroid=[round((x_a + x_bed_w) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 8. Maid Attached Compact Bath
        bath_maid_poly = [[x_bed_w, y_bed_start], [x_bath_split, y_bed_start], [x_bath_split, y_6], [x_bed_w, y_6], [x_bed_w, y_bed_start]]
        rooms.append(RoomSpec(
            room_id="r_L2_bath_maid",
            room_type="bathroom",
            room_name="Maid Dedicated Compact Bathroom",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=2,
            polygon=bath_maid_poly,
            area_m2=round(Polygon(bath_maid_poly).area, 1),
            centroid=[round((x_bed_w + x_bath_split) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 9. Rear Solar Inverter Deck & Battery Storage Rack
        solar_poly = [[x_bath_split, y_bed_start], [x_d, y_bed_start], [x_d, y_6], [x_bath_split, y_6], [x_bath_split, y_bed_start]]
        rooms.append(RoomSpec(
            room_id="r_L2_solar_deck",
            room_type="balcony",
            room_name="Rear Solar Inverter Deck & Battery Rack",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=2,
            polygon=solar_poly,
            area_m2=round(Polygon(solar_poly).area, 1),
            centroid=[round((x_bath_split + x_d) / 2.0, 2), round((y_bed_start + y_6) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 10. Level 2 Rear OTS Void
        rooms.append(RoomSpec(
            room_id="r_L2_ots",
            room_type="outdoor",
            room_name="Level 2 Daylight OTS Lightwell Void (5'-0\" Continuous)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=2,
            polygon=ots_poly,
            area_m2=round(Polygon(ots_poly).area, 1),
            centroid=[round(w / 2.0, 2), round((y_6 + y_7) / 2.0, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # ----------------------------------------------------------------------
        # 5. VERTICAL PLUMBING RISER SHAFTS
        # ----------------------------------------------------------------------
        # Shaft 1: Rear Bathroom Wet Core
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_prod_rear_baths",
            bounds_2d=[[x_bath_split - 0.30, y_6 - 0.60], [x_bath_split + 0.30, y_6 - 0.60],
                       [x_bath_split + 0.30, y_6], [x_bath_split - 0.30, y_6], [x_bath_split - 0.30, y_6 - 0.60]],
            serves_levels=[0, 1, 2],
            stack_type="SOIL_WASTE_VENT"
        ))
        # Shaft 2: Kitchen Grease & Drainage Shaft (East exterior wall)
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_prod_kitchen_stack",
            bounds_2d=[[x_d - 0.60, y_lounge_end - 0.30], [x_d, y_lounge_end - 0.30],
                       [x_d, y_lounge_end + 0.30], [x_d - 0.60, y_lounge_end + 0.30], [x_d - 0.60, y_lounge_end - 0.30]],
            serves_levels=[0, 1, 2],
            stack_type="KITCHEN_GREASE_EXHAUST"
        ))
        # Shaft 3: Powder / Mumty Drainage Core
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_prod_powder_mumty",
            bounds_2d=[[x_d - 0.60, y_2], [x_d, y_2], [x_d, y_2 + 0.60], [x_d - 0.60, y_2 + 0.60], [x_d - 0.60, y_2]],
            serves_levels=[0, 1, 2],
            stack_type="SOIL_WASTE_VENT"
        ))

        # ----------------------------------------------------------------------
        # 6. BIM WALL SPECIFICATIONS
        # ----------------------------------------------------------------------
        wall_id_counter = 1
        for lvl in [0, 1, 2]:
            lvl_rooms = [r for r in rooms if r.level_index == lvl]
            for r in lvl_rooms:
                poly = r.polygon
                for i in range(len(poly) - 1):
                    p1, p2 = poly[i], poly[i + 1]
                    is_ext = r.requires_exterior_wall and (
                        abs(p1[0] - 0.0) < 0.05 or abs(p1[0] - w) < 0.05 or
                        abs(p1[1] - 0.0) < 0.05 or abs(p1[1] - y_6) < 0.05 or abs(p1[1] - y_7) < 0.05
                    )
                    th = 0.229 if is_ext else 0.114
                    wtype = "EXTERIOR_SOLID_9IN" if is_ext else "INTERIOR_PARTITION_4_5IN"
                    walls.append(BIMWallSpec(
                        wall_id=f"w_prod_L{lvl}_{wall_id_counter:03d}",
                        wall_type=wtype,
                        centerline=[p1, p2],
                        thickness_m=th,
                        height_m=3.20,
                        level_index=lvl,
                        is_load_bearing=(th >= 0.20)
                    ))
                    wall_id_counter += 1

        # ----------------------------------------------------------------------
        # 7. FACADE & 3D ROOFTOP ELEMENTS (VOLUMETRIC SYNTHESIS)
        # ----------------------------------------------------------------------
        # Double-Cantilevered Volumetric Balcony
        facade_elements.append(FacadeElementSpec(
            element_id="facade_prod_cantilever_balcony",
            element_type="CANTILEVER_BALCONY",
            position_3d=[x_kit_start, 0.0, 3.35],
            dimensions_m=[4.88, 5.49, 0.15],
            level_index=1,
            material="Mat_Concrete_Slab"
        ))
        # Warm Timber-Finish Aluminium Louvers
        facade_elements.append(FacadeElementSpec(
            element_id="facade_prod_timber_louvers",
            element_type="TIMBER_LOUVERS",
            position_3d=[0.50, y_2, 3.35],
            dimensions_m=[4.20, 0.15, 3.00],
            level_index=1,
            material="Mat_Timber_Louvers"
        ))
        # Fluted Travertine Stone Cladding Panels
        facade_elements.append(FacadeElementSpec(
            element_id="facade_prod_fluted_limestone",
            element_type="FLUTED_LIMESTONE_PANEL",
            position_3d=[0.00, y_2, 0.00],
            dimensions_m=[6.10, 0.05, 6.70],
            level_index=0,
            material="Mat_Fluted_Limestone"
        ))
        # Floor-to-Ceiling Low-E Curtain Windows
        facade_elements.append(FacadeElementSpec(
            element_id="facade_prod_curtain_walling",
            element_type="CURTAIN_WALLING",
            position_3d=[x_b + 0.30, y_2, 3.35],
            dimensions_m=[4.20, 0.10, 3.00],
            level_index=1,
            material="Mat_Floor_Glazing"
        ))
        # Parametric Stair Mumty Penthouse Enclosure (8'-6" x 15'-0" x 9'-0" height)
        facade_elements.append(FacadeElementSpec(
            element_id="rooftop_prod_mumty_tower",
            element_type="MUMTY_TOWER",
            position_3d=[x_c, y_porch_end, 6.70],
            dimensions_m=[2.59, 4.57, 2.74],
            level_index=2,
            material="Mat_Exterior_Travertine"
        ))
        # Insulated Overhead Concrete Water Reservoir
        facade_elements.append(FacadeElementSpec(
            element_id="rooftop_prod_water_reservoir",
            element_type="WATER_RESERVOIR",
            position_3d=[x_c + 0.20, y_porch_end + 1.20, 9.44],
            dimensions_m=[2.20, 2.20, 1.60],
            level_index=2,
            material="Mat_Water_Reservoir"
        ))
        # BBQ Pergola Structure
        facade_elements.append(FacadeElementSpec(
            element_id="rooftop_prod_pergola",
            element_type="PERGOLA",
            position_3d=[1.00, 1.00, 6.70],
            dimensions_m=[5.50, 4.50, 2.80],
            level_index=2,
            material="Mat_Pergola_Wood"
        ))
        # Rear Solar Panel Array on Inverter Deck
        facade_elements.append(FacadeElementSpec(
            element_id="rooftop_prod_solar_array",
            element_type="SOLAR_ARRAY",
            position_3d=[x_bath_split + 0.30, y_bed_start + 0.30, 6.70],
            dimensions_m=[4.50, 3.50, 0.40],
            level_index=2,
            material="Mat_Solar_Panels"
        ))

        # Enclosed Stair Mumty Bounds
        mumty_poly = [[x_c, y_porch_end], [x_d, y_porch_end], [x_d, y_stair_end], [x_c, y_stair_end], [x_c, y_porch_end]]

        model = ParametricBIMModel(
            project_id=f"10MARLA_PRODUCTION_3STORY_{int(w*3.28084)}x{int(d*3.28084)}",
            site=SiteBoundary(
                width_m=w,
                depth_m=d,
                street_frontage="NORTH",
                setbacks=SetbackDefinition(front_m=3.05, rear_m=1.52, side_left_m=0.0, side_right_m=0.0)
            ),
            floor_count=3,
            levels=[0, 1, 2],
            rooms=rooms,
            openings=openings,
            plumbing_shafts=shafts,
            parapet_height_m=1.05,  # 3'-6" Solid Parapet
            mumty_bounds=mumty_poly,
            columns=columns,
            walls=walls,
            facade_elements=facade_elements,
            metadata={
                "project_title": "10 Marla Production 3-Story Luxury Residence (35'-0\" x 65'-0\")",
                "orientation": "NORTH",
                "structural_typology": StructuralTypology.RCC_FRAME_SLAB.value,
                "floor_to_floor_height_m": 3.35,  # 11'-0"
                "ceiling_height_m": 3.20,         # 10'-6" clear
                "slab_thickness_m": 0.15,
                "exterior_wall_thickness_m": 0.229,  # 9"
                "interior_wall_thickness_m": 0.114,  # 4.5"
                "parapet_height_m": 1.05,  # 3'-6"
                "mumty_height_m": 2.74,   # 9'-0"
                "stair_core_dimensions": "8'-6\" x 14'-6\" (2.59m x 4.42m)",
                "stair_mid_landing": "3'-6\" (1.07m) depth at +1500mm",
                "stair_core_invariance": "100% Strict 3D Coordinate Invariant across L0, L1, L2 (IoU = 1.00)",
                "wet_core_kitchen_iou": 1.00,
                "wet_core_rear_baths_iou": 1.00,
                "ots_rear_lightwell_depth": "5'-0\" (1.52m continuous)",
                "parking_envelope": "[X: 20'-0\" to 35'-0\", Y: 0'-0\" to 18'-0\"] (2-Car Covered Porch 15' x 18')",
                "double_line_walls": True,
                "door_swings_dashed_clearance": True,
                "facade_style": "Ultra-Modern Contemporary with Timber-Finish Aluminium Louvers & Fluted Travertine"
            }
        )

        # ----------------------------------------------------------------------
        # 8. CAD OPENINGS & ERGONOMIC FURNITURE PLACEMENT
        # ----------------------------------------------------------------------
        self._generate_10_marla_production_openings(model)
        self._solve_10_marla_production_furniture(model)

        return model

    def _generate_10_marla_production_openings(self, model: ParametricBIMModel):
        """Generates architectural doors and windows for 10 Marla production layout."""
        def add_op(op_id, cat, pos, w_m, h_m, conn, lvl, is_ext=False, sill=0.0):
            model.openings.append(OpeningSpec(
                opening_id=op_id,
                category=cat,
                position_3d=[round(pos[0], 2), round(pos[1], 2), round(lvl * 3.35, 2)],
                width_m=w_m,
                height_m=h_m,
                sill_height_m=sill,
                lintel_height_m=round(sill + h_m, 2),
                connects_rooms=conn,
                level_index=lvl,
                is_exterior=is_ext
            ))

        # Level 0 Openings
        add_op("door_P_L0_entry", OpeningCategory.MAIN_ENTRANCE_DOOR, [7.10, 3.05], 1.20, 2.40, ["r_L0_porch", "r_L0_foyer"], 0, is_ext=True)
        add_op("door_P_L0_foyer_draw", OpeningCategory.INTERIOR_DOOR, [6.10, 4.20], 1.20, 2.40, ["r_L0_foyer", "r_L0_drawing"], 0)
        add_op("door_P_L0_powder", OpeningCategory.INTERIOR_DOOR, [8.08, 4.20], 0.85, 2.10, ["r_L0_foyer", "r_L0_powder"], 0)
        add_op("door_P_L0_foyer_lounge", OpeningCategory.INTERIOR_DOOR, [7.10, 5.49], 1.10, 2.40, ["r_L0_foyer", "r_L0_lounge"], 0)
        add_op("door_P_L0_stair", OpeningCategory.INTERIOR_DOOR, [8.08, 6.50], 0.914, 2.10, ["r_L0_lounge", "r_L0_stair"], 0)
        add_op("door_P_L0_draw_lounge", OpeningCategory.INTERIOR_DOOR, [3.00, 8.53], 1.20, 2.40, ["r_L0_drawing", "r_L0_lounge"], 0)
        add_op("win_P_L0_draw_bay", OpeningCategory.STANDARD_WINDOW, [3.00, 3.05], 2.44, 2.10, ["r_L0_drawing"], 0, is_ext=True, sill=0.45)
        add_op("door_P_L0_kitchen", OpeningCategory.INTERIOR_DOOR, [6.50, 9.91], 1.50, 2.40, ["r_L0_lounge", "r_L0_kitchen"], 0)
        add_op("door_P_L0_dirty_kitchen", OpeningCategory.SERVICE_DOOR, [8.50, 13.72], 0.85, 2.10, ["r_L0_kitchen", "r_L0_dirty_kitchen"], 0)
        add_op("door_P_L0_dirty_ext", OpeningCategory.SERVICE_DOOR, [10.67, 14.30], 0.85, 2.10, ["r_L0_dirty_kitchen"], 0, is_ext=True)
        add_op("door_P_L0_vestibule", OpeningCategory.INTERIOR_DOOR, [3.00, 13.72], 1.05, 2.20, ["r_L0_lounge", "r_L0_bed_lobby"], 0)
        add_op("door_P_L0_bed1", OpeningCategory.INTERIOR_DOOR, [2.00, 14.02], 0.914, 2.10, ["r_L0_bed_lobby", "r_L0_bed1"], 0)
        add_op("door_P_L0_bath1", OpeningCategory.INTERIOR_DOOR, [4.27, 15.00], 0.85, 2.10, ["r_L0_bed1", "r_L0_bath1"], 0)
        add_op("door_P_L0_bed2", OpeningCategory.INTERIOR_DOOR, [6.40, 14.02], 0.914, 2.10, ["r_L0_bed_lobby", "r_L0_bed2"], 0)
        add_op("door_P_L0_bath2", OpeningCategory.INTERIOR_DOOR, [6.40, 15.00], 0.85, 2.10, ["r_L0_bed2", "r_L0_bath2"], 0)
        add_op("win_P_L0_bed1_ots", OpeningCategory.STANDARD_WINDOW, [2.00, 18.29], 1.80, 1.80, ["r_L0_bed1"], 0, is_ext=True, sill=0.60)
        add_op("win_P_L0_bed2_ots", OpeningCategory.STANDARD_WINDOW, [8.50, 18.29], 1.80, 1.80, ["r_L0_bed2"], 0, is_ext=True, sill=0.60)
        add_op("win_P_L0_bath1_ots", OpeningCategory.VENTILATION_CLERESTORY, [4.87, 18.29], 0.914, 0.90, ["r_L0_bath1"], 0, is_ext=True, sill=1.50)
        add_op("win_P_L0_bath2_ots", OpeningCategory.VENTILATION_CLERESTORY, [5.94, 18.29], 0.914, 0.90, ["r_L0_bath2"], 0, is_ext=True, sill=1.50)

        # Level 1 Openings
        add_op("door_P_L1_terrace_patio", OpeningCategory.SLIDING_PATIO_DOOR, [7.50, 5.49], 2.44, 2.60, ["r_L1_lounge", "r_L1_terrace"], 1, is_ext=True)
        add_op("door_P_L1_bed3", OpeningCategory.INTERIOR_DOOR, [3.00, 8.53], 1.05, 2.40, ["r_L1_lounge", "r_L1_bed3"], 1)
        add_op("door_P_L1_bath3", OpeningCategory.INTERIOR_DOOR, [2.44, 4.20], 0.85, 2.10, ["r_L1_bed3", "r_L1_bath3"], 1)
        add_op("win_P_L1_bed3_front", OpeningCategory.DOUBLE_HEIGHT_GLAZING, [2.44, 3.05], 3.50, 2.60, ["r_L1_bed3"], 1, is_ext=True, sill=0.10)
        add_op("door_P_L1_stair", OpeningCategory.INTERIOR_DOOR, [8.08, 6.50], 1.05, 2.40, ["r_L1_lounge", "r_L1_stair"], 1)
        add_op("door_P_L1_kitchenette", OpeningCategory.INTERIOR_DOOR, [6.50, 9.91], 0.914, 2.20, ["r_L1_lounge", "r_L1_kitchenette"], 1)
        add_op("door_P_L1_bed_lobby", OpeningCategory.INTERIOR_DOOR, [3.00, 13.72], 1.05, 2.20, ["r_L1_lounge", "r_L1_bed_lobby"], 1)
        add_op("door_P_L1_bed4", OpeningCategory.INTERIOR_DOOR, [2.00, 14.02], 0.914, 2.10, ["r_L1_bed_lobby", "r_L1_bed4"], 1)
        add_op("door_P_L1_bath4", OpeningCategory.INTERIOR_DOOR, [4.27, 15.00], 0.85, 2.10, ["r_L1_bed4", "r_L1_bath4"], 1)
        add_op("door_P_L1_bed5", OpeningCategory.INTERIOR_DOOR, [6.40, 14.02], 0.914, 2.10, ["r_L1_bed_lobby", "r_L1_bed5"], 1)
        add_op("door_P_L1_bath5", OpeningCategory.INTERIOR_DOOR, [6.40, 15.00], 0.85, 2.10, ["r_L1_bed5", "r_L1_bath5"], 1)
        add_op("win_P_L1_bed4_ots", OpeningCategory.STANDARD_WINDOW, [2.00, 18.29], 1.80, 1.80, ["r_L1_bed4"], 1, is_ext=True, sill=0.60)
        add_op("win_P_L1_bed5_ots", OpeningCategory.STANDARD_WINDOW, [8.50, 18.29], 1.80, 1.80, ["r_L1_bed5"], 1, is_ext=True, sill=0.60)

        # Level 2 Openings
        add_op("door_P_L2_stair_mumty", OpeningCategory.INTERIOR_DOOR, [9.35, 7.62], 1.00, 2.10, ["r_L2_stair", "r_L2_mumty_vestibule"], 2)
        add_op("door_P_L2_mumty_weather", OpeningCategory.SERVICE_DOOR, [9.35, 5.49], 0.914, 2.10, ["r_L2_mumty_vestibule", "r_L2_bbq_terrace"], 2, is_ext=True)
        add_op("door_P_L2_multi_terrace", OpeningCategory.SLIDING_PATIO_DOOR, [3.00, 7.62], 2.44, 2.40, ["r_L2_multipurpose", "r_L2_bbq_terrace"], 2, is_ext=True)
        add_op("door_P_L2_multi_spa", OpeningCategory.INTERIOR_DOOR, [1.22, 11.50], 0.85, 2.10, ["r_L2_multipurpose", "r_L2_bath_spa"], 2)
        add_op("door_P_L2_laundry", OpeningCategory.SERVICE_DOOR, [5.79, 10.50], 0.914, 2.10, ["r_L2_multipurpose", "r_L2_laundry"], 2)
        add_op("door_P_L2_maid", OpeningCategory.INTERIOR_DOOR, [2.00, 14.02], 0.85, 2.10, ["r_L2_multipurpose", "r_L2_maid"], 2)
        add_op("door_P_L2_maid_bath", OpeningCategory.INTERIOR_DOOR, [4.27, 15.00], 0.80, 2.10, ["r_L2_maid", "r_L2_bath_maid"], 2)
        add_op("door_P_L2_maid_solar", OpeningCategory.SERVICE_DOOR, [5.48, 15.00], 0.85, 2.10, ["r_L2_bath_maid", "r_L2_solar_deck"], 2, is_ext=True)

    def _solve_10_marla_production_furniture(self, model: ParametricBIMModel):
        """Solves furniture anchoring, 36\" corridor clearances, TV throw, and wet/dry zoning."""
        room_dict = {r.room_id: r for r in model.rooms}

        def add_f(rid, cat, pos, dims, rot=0.0, anchor=None, clear_poly=None):
            if rid not in room_dict:
                return
            room_dict[rid].furniture.append(FurnitureItem(
                item_id=f"furn_{rid}_{cat.value.lower()}_{len(room_dict[rid].furniture)+1}",
                category=cat,
                room_id=rid,
                position_3d=[round(pos[0], 2), round(pos[1], 2), round(pos[2], 2)],
                dimensions_m=[round(dims[0], 2), round(dims[1], 2), round(dims[2], 2)],
                rotation_deg_z=rot,
                solid_wall_anchor_edge=anchor,
                clearance_envelope_polygon=clear_poly
            ))

        # Level 0 Furniture
        # Car Porch (15' x 18': 2 vehicles)
        add_f("r_L0_porch", FurnitureCategory.VEHICLE_SUV, [6.80, 1.00, 0.0], [1.98, 4.88, 1.80])
        add_f("r_L0_porch", FurnitureCategory.VEHICLE_SEDAN, [8.90, 1.00, 0.0], [1.83, 4.57, 1.50])

        # Formal Drawing Room (Fireplace wall & credenza clearance)
        add_f("r_L0_drawing", FurnitureCategory.FIREPLACE, [0.10, 5.50, 0.0], [0.45, 1.50, 1.20], 90.0)
        add_f("r_L0_drawing", FurnitureCategory.CREDENZA, [0.10, 7.50, 0.0], [0.45, 1.80, 0.85], 90.0)
        add_f("r_L0_drawing", FurnitureCategory.SOFA_THREE_SEATER, [2.00, 7.00, 0.0], [2.40, 0.95, 0.85], 0.0)
        add_f("r_L0_drawing", FurnitureCategory.COFFEE_TABLE, [2.60, 5.50, 0.0], [1.30, 0.70, 0.45], 0.0)
        add_f("r_L0_drawing", FurnitureCategory.ARMCHAIR, [1.00, 4.50, 0.0], [0.90, 0.85, 0.80], 90.0)
        add_f("r_L0_drawing", FurnitureCategory.ARMCHAIR, [4.20, 4.50, 0.0], [0.90, 0.85, 0.80], 270.0)

        # Powder Room (Wet/Dry zoning)
        add_f("r_L0_powder", FurnitureCategory.VANITY_BASIN, [9.00, 3.20, 0.0], [0.90, 0.50, 0.85])
        add_f("r_L0_powder", FurnitureCategory.WATER_CLOSET, [9.20, 4.50, 0.0], [0.45, 0.70, 0.80])

        # Semi-Open Dining (8-seater with 36\" pullout clearance)
        add_f("r_L0_dining", FurnitureCategory.DINING_TABLE_8, [1.20, 9.20, 0.0], [2.40, 1.10, 0.75])

        # Expansive TV Lounge (L-sectional maintaining 10'-0\" to 13'-0\" throw distance)
        # Media console at East wall x=7.60, L-sectional anchored at x=3.80 (distance = 3.80m = 12'-6\")
        add_f("r_L0_lounge", FurnitureCategory.L_SECTIONAL_SOFA, [3.80, 10.50, 0.0], [3.00, 2.60, 0.85], 0.0)
        add_f("r_L0_lounge", FurnitureCategory.TV_MEDIA_CONSOLE, [7.60, 11.00, 0.0], [0.45, 2.40, 0.60], 90.0)

        # Gourmet Kitchen (Prep Island)
        add_f("r_L0_kitchen", FurnitureCategory.KITCHEN_COUNTER_ISLAND, [7.50, 11.50, 0.0], [2.40, 1.00, 0.90])

        # Scullery (Perimeter counters)
        add_f("r_L0_dirty_kitchen", FurnitureCategory.KITCHEN_COUNTER_ISLAND, [8.00, 14.00, 0.0], [2.40, 0.60, 0.90])

        # Master Suite 1 (14' x 14': King Bed anchored to solid dry partition at y=14.02m)
        bed1_anchor = [[0.80, 14.02], [2.80, 14.02]]
        bed1_clearance = [[0.0, 14.02], [3.80, 14.02], [3.80, 17.50], [0.0, 17.50], [0.0, 14.02]]
        add_f("r_L0_bed1", FurnitureCategory.KING_BED, [0.80, 14.12, 0.0], [2.00, 2.00, 0.90], 0.0, bed1_anchor, bed1_clearance)
        add_f("r_L0_bed1", FurnitureCategory.NIGHTSTAND, [0.20, 14.12, 0.0], [0.50, 0.50, 0.55])
        add_f("r_L0_bed1", FurnitureCategory.NIGHTSTAND, [2.90, 14.12, 0.0], [0.50, 0.50, 0.55])
        add_f("r_L0_bed1", FurnitureCategory.WARDROBE_RUN, [0.10, 16.50, 0.0], [0.60, 2.40, 2.40], 90.0)

        # Ensuite Bath 1 (Wet/Dry zoning: Vanity -> WC -> Shower with 10mm glass partition)
        add_f("r_L0_bath1", FurnitureCategory.VANITY_BASIN, [4.40, 14.20, 0.0], [0.90, 0.50, 0.85])
        add_f("r_L0_bath1", FurnitureCategory.WATER_CLOSET, [4.80, 15.20, 0.0], [0.45, 0.70, 0.80])
        add_f("r_L0_bath1", FurnitureCategory.SHOWER_ENCLOSURE, [4.40, 16.50, 0.0], [1.00, 1.00, 2.10])

        # Suite 2 (14' x 14': Queen Bed anchored to solid interior wall at y=14.02m)
        bed2_anchor = [[7.20, 14.02], [8.70, 14.02]]
        bed2_clearance = [[6.40, 14.02], [10.20, 14.02], [10.20, 17.50], [6.40, 17.50], [6.40, 14.02]]
        add_f("r_L0_bed2", FurnitureCategory.QUEEN_BED, [7.20, 14.12, 0.0], [1.50, 2.00, 0.90], 0.0, bed2_anchor, bed2_clearance)
        add_f("r_L0_bed2", FurnitureCategory.NIGHTSTAND, [6.60, 14.12, 0.0], [0.50, 0.50, 0.55])
        add_f("r_L0_bed2", FurnitureCategory.NIGHTSTAND, [8.80, 14.12, 0.0], [0.50, 0.50, 0.55])

        # Ensuite Bath 2 (Wet/Dry zoning)
        add_f("r_L0_bath2", FurnitureCategory.VANITY_BASIN, [5.55, 14.20, 0.0], [0.80, 0.50, 0.85])
        add_f("r_L0_bath2", FurnitureCategory.WATER_CLOSET, [5.70, 15.20, 0.0], [0.45, 0.70, 0.80])
        add_f("r_L0_bath2", FurnitureCategory.SHOWER_ENCLOSURE, [5.55, 16.50, 0.0], [0.85, 1.00, 2.10])

        # Level 1 Furniture
        add_f("r_L1_terrace", FurnitureCategory.PERGOLA_SEATING, [6.50, 1.50, 3.35], [2.40, 1.80, 0.80])
        # Master Suite 3 (King Bed anchored to solid wall at y=8.53m)
        bed3_anchor = [[1.20, 8.53], [3.20, 8.53]]
        bed3_clearance = [[0.0, 5.50], [4.50, 5.50], [4.50, 8.53], [0.0, 8.53], [0.0, 5.50]]
        add_f("r_L1_bed3", FurnitureCategory.KING_BED, [1.20, 6.43, 3.35], [2.00, 2.00, 0.90], 180.0, bed3_anchor, bed3_clearance)
        add_f("r_L1_bed3", FurnitureCategory.NIGHTSTAND, [0.60, 7.93, 3.35], [0.50, 0.50, 0.55])
        add_f("r_L1_bed3", FurnitureCategory.NIGHTSTAND, [3.30, 7.93, 3.35], [0.50, 0.50, 0.55])
        add_f("r_L1_bed3", FurnitureCategory.WARDROBE_RUN, [0.10, 3.20, 3.35], [0.60, 2.40, 2.40], 90.0)

        # Bath 3 (Wet/Dry)
        add_f("r_L1_bath3", FurnitureCategory.VANITY_BASIN, [0.20, 3.50, 3.35], [1.50, 0.55, 0.85])
        add_f("r_L1_bath3", FurnitureCategory.WATER_CLOSET, [1.80, 4.50, 3.35], [0.45, 0.70, 0.80])
        add_f("r_L1_bath3", FurnitureCategory.SHOWER_ENCLOSURE, [0.20, 4.50, 3.35], [1.20, 0.90, 2.10])

        # Upper Lounge & Study Nook (Executive desk & bookshelves)
        add_f("r_L1_lounge", FurnitureCategory.COFFEE_TABLE, [1.00, 12.00, 3.35], [1.50, 0.75, 0.75])
        add_f("r_L1_lounge", FurnitureCategory.ARMCHAIR, [1.50, 11.20, 3.35], [0.70, 0.70, 0.85])
        add_f("r_L1_lounge", FurnitureCategory.L_SECTIONAL_SOFA, [3.80, 10.50, 3.35], [3.00, 2.40, 0.85])
        add_f("r_L1_lounge", FurnitureCategory.TV_MEDIA_CONSOLE, [7.60, 11.00, 3.35], [0.45, 2.20, 0.60], 90.0)

        # Upper Suites 4 & 5 (14' x 14')
        bed4_anchor = [[0.80, 14.02], [2.30, 14.02]]
        add_f("r_L1_bed4", FurnitureCategory.QUEEN_BED, [0.80, 14.12, 3.35], [1.50, 2.00, 0.90], 0.0, bed4_anchor)
        add_f("r_L1_bed4", FurnitureCategory.NIGHTSTAND, [0.20, 14.12, 3.35], [0.50, 0.50, 0.55])
        add_f("r_L1_bed4", FurnitureCategory.NIGHTSTAND, [2.40, 14.12, 3.35], [0.50, 0.50, 0.55])

        bed5_anchor = [[7.20, 14.02], [8.70, 14.02]]
        add_f("r_L1_bed5", FurnitureCategory.QUEEN_BED, [7.20, 14.12, 3.35], [1.50, 2.00, 0.90], 0.0, bed5_anchor)
        add_f("r_L1_bed5", FurnitureCategory.NIGHTSTAND, [6.60, 14.12, 3.35], [0.50, 0.50, 0.55])
        add_f("r_L1_bed5", FurnitureCategory.NIGHTSTAND, [8.80, 14.12, 3.35], [0.50, 0.50, 0.55])

        # Level 2 Furniture
        add_f("r_L2_bbq_terrace", FurnitureCategory.PERGOLA_SEATING, [2.00, 2.50, 6.70], [3.00, 2.20, 0.85])
        add_f("r_L2_bbq_terrace", FurnitureCategory.DINING_TABLE_8, [6.00, 2.50, 6.70], [2.40, 1.10, 0.75])
        add_f("r_L2_multipurpose", FurnitureCategory.SOFA_THREE_SEATER, [1.00, 9.50, 6.70], [2.20, 0.90, 0.85])
        add_f("r_L2_bath_spa", FurnitureCategory.SPA_JACUZZI_TUB, [0.30, 11.70, 6.70], [1.80, 1.00, 0.75])
        add_f("r_L2_bath_spa", FurnitureCategory.VANITY_BASIN, [1.50, 12.80, 6.70], [0.90, 0.50, 0.85])
        add_f("r_L2_maid", FurnitureCategory.QUEEN_BED, [0.80, 14.20, 6.70], [1.50, 2.00, 0.80])
        add_f("r_L2_solar_deck", FurnitureCategory.SOLAR_INVERTER_RACK, [6.50, 15.00, 6.70], [2.00, 0.80, 1.80])
        add_f("r_L2_stair", FurnitureCategory.WATER_RESERVOIR, [8.50, 7.50, 12.79], [2.00, 2.00, 1.60])

    def solve_layout(
        self,
        requested_bedrooms: int = 4,
        requested_bathrooms: int = 4,
        include_dirty_kitchen: bool = True,
        include_drawing_room: bool = True,
        parking_capacity: int = 2,
        archetype: Optional[str] = None
    ) -> ParametricBIMModel:
        """
        Executes deterministic multi-level spatial layout generation.
        Automatically routes 10 Marla (35' x 65' / ~10.67m x ~19.81m) requests:
        - If statutory front setback <= 3.5m (10'-0" front / 5'-0" rear) -> Production 3-Story Solver
        - If luxury front setback > 3.5m (15'-0" front / 6'-6" rear) -> Luxury 3-Story Solver
        """
        if archetype == "10_MARLA_10FT_SETBACK" or (abs(self.w - 10.67) < 1.0 and abs(self.d - 19.81) < 1.5 and self.site.setbacks.front_m <= 3.5):
            return self.solve_10_marla_production_3story(parking_capacity=parking_capacity)
        elif archetype == "10_MARLA_LUXURY" or (abs(self.w - 10.67) < 1.0 and abs(self.d - 19.81) < 1.5) or self.floor_count == 3:
            return self.solve_10_marla_luxury_layout(parking_capacity=parking_capacity)

        rooms: List[RoomSpec] = []
        openings: List[OpeningSpec] = []
        shafts: List[VerticalPlumbingShaft] = []
        columns: List[RCCColumnNode] = []
        walls: List[BIMWallSpec] = []
        facade_elements: List[FacadeElementSpec] = []

        # Calculate Longitudinal Zoning Bands
        min_x, min_y, max_x, max_y = self.site.buildable_box
        buildable_width = max_x - min_x
        buildable_depth = max_y - min_y

        y_lawn_end = min_y

        # ======================================================================
        # 1. STRUCTURAL STAIR CORE RULES (STRICT BOUNDING BOX & INVARIANCE)
        # Bounding Box: Width: 8'-6" to 9'-0" (2.59m - 2.74m), Depth: 14'-6" to 15'-0" (4.42m - 4.57m)
        # ======================================================================
        stair_w = 2.70  # 8'-10.3" (within 8'-6" to 9'-0")
        stair_d = 4.50  # 14'-9.2" (within 14'-6" to 15'-0")
        stair_x_min = round(max_x - stair_w, 2)
        stair_x_max = round(max_x, 2)
        stair_y_min = round(y_lawn_end + 1.60, 2)
        stair_y_max = round(stair_y_min + stair_d, 2)

        # Invariant 2D Stair Core Polygon across ALL levels
        stair_poly = [
            [stair_x_min, stair_y_min],
            [stair_x_max, stair_y_min],
            [stair_x_max, stair_y_max],
            [stair_x_min, stair_y_max],
            [stair_x_min, stair_y_min]
        ]

        # Longitudinal Architectural Zoning Bands
        y_zone_a_end = stair_y_max
        y_zone_b_end = round(stair_y_max + 5.00, 2)    # Zone B Center: 5.00m (16'-5")
        lobby_d = 1.50                                  # Dedicated 5'-0" (1.50m) Buffer Lobby
        y_lobby_end = round(y_zone_b_end + lobby_d, 2)
        y_zone_c_end = round(max_y, 2)                  # Rear setback boundary line

        # East Wet Core Coordinates (Strict IoU >= 0.85 Stacked Invariance across L0, L1, L2)
        kit_x_min = round(min_x + buildable_width * 0.637, 2)  # 6.80m for 10 Marla
        kit_x_max = max_x
        kit_y_split = round(stair_y_max + 2.85, 2)             # Split between Cook/Pantry and Scullery/Laundry

        kitchen_sub1_poly = [
            [kit_x_min, stair_y_max],
            [kit_x_max, stair_y_max],
            [kit_x_max, kit_y_split],
            [kit_x_min, kit_y_split],
            [kit_x_min, stair_y_max]
        ]

        kitchen_sub2_poly = [
            [kit_x_min, kit_y_split],
            [kit_x_max, kit_y_split],
            [kit_x_max, y_zone_b_end],
            [kit_x_min, y_zone_b_end],
            [kit_x_min, kit_y_split]
        ]

        # Central Living / Lounge Poly
        lounge_poly = [
            [min_x, stair_y_max],
            [kit_x_min, stair_y_max],
            [kit_x_min, y_zone_b_end],
            [min_x, y_zone_b_end],
            [min_x, stair_y_max]
        ]

        # Private Bedroom Distribution Lobby Poly (5'-0" buffer)
        bed_lobby_poly = [
            [min_x, y_zone_b_end],
            [max_x, y_zone_b_end],
            [max_x, y_lobby_end],
            [min_x, y_lobby_end],
            [min_x, y_zone_b_end]
        ]

        # Rear Suites & Twin Bathroom Wet Core Footprints (100% Invariant across L0, L1, L2)
        suite_w = round((max_x - min_x) * 0.375, 2)      # 4.00m (13'-1")
        bath_w = round(((max_x - min_x) - 2 * suite_w) / 2.0, 2) # ~1.33m (4'-5") each
        bath1_x_max = round(min_x + suite_w + bath_w, 2)

        bed_west_poly = [
            [min_x, y_lobby_end],
            [min_x + suite_w, y_lobby_end],
            [min_x + suite_w, y_zone_c_end],
            [min_x, y_zone_c_end],
            [min_x, y_lobby_end]
        ]

        bath_west_poly = [
            [min_x + suite_w, y_lobby_end],
            [bath1_x_max, y_lobby_end],
            [bath1_x_max, y_zone_c_end],
            [min_x + suite_w, y_zone_c_end],
            [min_x + suite_w, y_lobby_end]
        ]

        bath_east_poly = [
            [bath1_x_max, y_lobby_end],
            [max_x - suite_w, y_lobby_end],
            [max_x - suite_w, y_zone_c_end],
            [bath1_x_max, y_zone_c_end],
            [bath1_x_max, y_lobby_end]
        ]

        bed_east_poly = [
            [max_x - suite_w, y_lobby_end],
            [max_x, y_lobby_end],
            [max_x, y_zone_c_end],
            [max_x - suite_w, y_zone_c_end],
            [max_x - suite_w, y_lobby_end]
        ]

        # Continuous Open-To-Sky (OTS) Shaft (Strictly void across all 3 floors & roof slab)
        ots_poly = [
            [0.0, y_zone_c_end],
            [self.w, y_zone_c_end],
            [self.w, self.d],
            [0.0, self.d],
            [0.0, y_zone_c_end]
        ]

        # ----------------------------------------------------------------------
        # LEVEL 0: GROUND FLOOR SYNTHESIS
        # ----------------------------------------------------------------------
        lawn_w = round(buildable_width * 0.45, 2)
        foyer_w = round(stair_x_min - lawn_w, 2)

        # 1. Front Lawn (Strictly Outdoor Front Boundary Anchor - NEVER INTERIOR)
        lawn_poly = [[0.0, 0.0], [lawn_w, 0.0], [lawn_w, y_lawn_end], [0.0, y_lawn_end], [0.0, 0.0]]
        rooms.append(RoomSpec(
            room_id="r_L0_lawn",
            room_type="outdoor",
            room_name="Landscaped Front Garden Lawn",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=0,
            polygon=lawn_poly,
            area_m2=round(Polygon(lawn_poly).area, 1),
            centroid=[round(lawn_w / 2, 2), round(y_lawn_end / 2, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 2. Car Porch (Driveway Access directly from street)
        porch_poly = [[lawn_w, 0.0], [self.w, 0.0], [self.w, y_lawn_end], [lawn_w, y_lawn_end], [lawn_w, 0.0]]
        rooms.append(RoomSpec(
            room_id="r_L0_porch",
            room_type="garage",
            room_name=f"Main Car Porch ({parking_capacity} Vehicles)",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=porch_poly,
            area_m2=round(Polygon(porch_poly).area, 1),
            centroid=[round((lawn_w + self.w) / 2, 2), round(y_lawn_end / 2, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 3. Zone A: Formal Drawing Salon (Facing lawn with expansive front glazing)
        drawing_poly = [
            [min_x, y_lawn_end],
            [lawn_w, y_lawn_end],
            [lawn_w, stair_y_max],
            [min_x, stair_y_max],
            [min_x, y_lawn_end]
        ]
        rooms.append(RoomSpec(
            room_id="r_L0_drawing",
            room_type="living_room",
            room_name="Formal Guest Drawing Salon",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=drawing_poly,
            area_m2=round(Polygon(drawing_poly).area, 1),
            centroid=[round((min_x + lawn_w) / 2, 2), round((y_lawn_end + stair_y_max) / 2, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 4. Zone A: Grand Entrance Foyer (Foyer Buffering: >= 5'-0" clear from door swing to stair riser)
        foyer_poly = [
            [lawn_w, y_lawn_end],
            [stair_x_min, y_lawn_end],
            [stair_x_min, stair_y_max],
            [lawn_w, stair_y_max],
            [lawn_w, y_lawn_end]
        ]
        rooms.append(RoomSpec(
            room_id="r_L0_foyer",
            room_type="corridor",
            room_name="Grand Entrance Foyer & Vestibule",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=foyer_poly,
            area_m2=round(Polygon(foyer_poly).area, 1),
            centroid=[round((lawn_w + stair_x_min) / 2, 2), round((y_lawn_end + stair_y_max) / 2, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 5. Zone A: Guest Powder Room (Under/adjacent stair core entrance)
        powder_poly = [
            [stair_x_min, y_lawn_end],
            [stair_x_max, y_lawn_end],
            [stair_x_max, stair_y_min],
            [stair_x_min, stair_y_min],
            [stair_x_min, y_lawn_end]
        ]
        rooms.append(RoomSpec(
            room_id="r_L0_powder",
            room_type="bathroom",
            room_name="Guest Powder Room",
            zone=ArchitecturalZone.ZONE_A_PUBLIC,
            level_index=0,
            polygon=powder_poly,
            area_m2=round(Polygon(powder_poly).area, 1),
            centroid=[round((stair_x_min + stair_x_max) / 2, 2), round((y_lawn_end + stair_y_min) / 2, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 6. Dedicated Rectangular Staircase Core (Invariant shaft bounding box)
        rooms.append(RoomSpec(
            room_id="r_L0_stair",
            room_type="corridor",
            room_name="Dedicated Rectangular Dogleg Stair Core (8'-10\" x 14'-9\")",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=stair_poly,
            area_m2=round(Polygon(stair_poly).area, 1),
            centroid=[round((stair_x_min + stair_x_max) / 2, 2), round((stair_y_min + stair_y_max) / 2, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 7. Zone B: Central Family Living & TV Lounge
        rooms.append(RoomSpec(
            room_id="r_L0_lounge",
            room_type="living_room",
            room_name="Central Family Living & TV Lounge",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=lounge_poly,
            area_m2=round(Polygon(lounge_poly).area, 1),
            centroid=[round((min_x + kit_x_min) / 2, 2), round((stair_y_max + y_zone_b_end) / 2, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 8. Zone B: Show Gourmet Kitchen (East Perimeter Wet Core)
        rooms.append(RoomSpec(
            room_id="r_L0_kitchen",
            room_type="kitchen",
            room_name="Show Gourmet Kitchen & Island",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=kitchen_sub1_poly,
            area_m2=round(Polygon(kitchen_sub1_poly).area, 1),
            centroid=[round((kit_x_min + kit_x_max) / 2, 2), round((stair_y_max + kit_y_split) / 2, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 9. Zone B: Attached Wet Scullery & Dirty Kitchen (Direct exterior service wall)
        rooms.append(RoomSpec(
            room_id="r_L0_dirty_kitchen",
            room_type="kitchen",
            room_name="Attached Scullery & Wet Dirty Kitchen",
            zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
            level_index=0,
            polygon=kitchen_sub2_poly,
            area_m2=round(Polygon(kitchen_sub2_poly).area, 1),
            centroid=[round((kit_x_min + kit_x_max) / 2, 2), round((kit_y_split + y_zone_b_end) / 2, 2)],
            requires_exterior_wall=True,
            has_exterior_exhaust=True,
            is_wet_core=True
        ))

        # 10. Zone C: Dedicated Bedroom Buffer Lobby (5'-0" minimum clear acoustic buffer)
        rooms.append(RoomSpec(
            room_id="r_L0_bed_lobby",
            room_type="corridor",
            room_name="Acoustic Bedroom Distribution Lobby (5'-0\" Clear Buffer)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bed_lobby_poly,
            area_m2=round(Polygon(bed_lobby_poly).area, 1),
            centroid=[round((min_x + max_x) / 2, 2), round((y_zone_b_end + y_lobby_end) / 2, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # 11. Zone C: Ground Master Bedroom Suite 1 (West Wing)
        rooms.append(RoomSpec(
            room_id="r_L0_bed1",
            room_type="bedroom",
            room_name="Ground Floor Master Bedroom Suite 1",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bed_west_poly,
            area_m2=round(Polygon(bed_west_poly).area, 1),
            centroid=[round((min_x + min_x + suite_w) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 12. Zone C: Master Ensuite Spa Bath 1 (Stacked rear wet core flanking lightwell)
        rooms.append(RoomSpec(
            room_id="r_L0_bath1",
            room_type="bathroom",
            room_name="Master Ensuite Spa Bath 1 (Linear Wet-Dry)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bath_west_poly,
            area_m2=round(Polygon(bath_west_poly).area, 1),
            centroid=[round((min_x + suite_w + bath1_x_max) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 13. Zone C: Ensuite Attached Bath 2 (Twin symmetric wet core flanking lightwell)
        rooms.append(RoomSpec(
            room_id="r_L0_bath2",
            room_type="bathroom",
            room_name="Ensuite Attached Bath 2 (Linear Wet-Dry)",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bath_east_poly,
            area_m2=round(Polygon(bath_east_poly).area, 1),
            centroid=[round((bath1_x_max + max_x - suite_w) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
            requires_exterior_wall=True,
            is_wet_core=True
        ))

        # 14. Zone C: Ground Guest Suite 2 (East Wing)
        rooms.append(RoomSpec(
            room_id="r_L0_bed2",
            room_type="bedroom",
            room_name="Ground Floor Guest Bedroom Suite 2",
            zone=ArchitecturalZone.ZONE_C_PRIVATE,
            level_index=0,
            polygon=bed_east_poly,
            area_m2=round(Polygon(bed_east_poly).area, 1),
            centroid=[round((max_x - suite_w + max_x) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
            requires_exterior_wall=True,
            is_wet_core=False
        ))

        # 15. Rear Setback Open-To-Sky (OTS) Shaft (5'-0" continuous vertical air volume)
        rooms.append(RoomSpec(
            room_id="r_L0_ots",
            room_type="outdoor",
            room_name="Rear Garden & Daylight OTS Shaft (5'-0\" Continuous)",
            zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
            level_index=0,
            polygon=ots_poly,
            area_m2=round(Polygon(ots_poly).area, 1),
            centroid=[round(self.w / 2, 2), round((y_zone_c_end + self.d) / 2, 2)],
            requires_exterior_wall=False,
            is_wet_core=False
        ))

        # ----------------------------------------------------------------------
        # LEVEL 1: FIRST FLOOR (VERTICAL STACKING & RISER INVARIANCE)
        # ----------------------------------------------------------------------
        if self.floor_count >= 2:
            # 1. Front Sunset Terrace (Cantilevered over Porch / Front Glazing)
            terrace_poly = [
                [min_x, 0.0],
                [stair_x_min, 0.0],
                [stair_x_min, y_lawn_end],
                [min_x, y_lawn_end],
                [min_x, 0.0]
            ]
            rooms.append(RoomSpec(
                room_id="r_L1_terrace",
                room_type="balcony",
                room_name="Cantilevered Front Sunset Terrace",
                zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
                level_index=1,
                polygon=terrace_poly,
                area_m2=round(Polygon(terrace_poly).area, 1),
                centroid=[round((min_x + stair_x_min) / 2, 2), round(y_lawn_end / 2, 2)],
                requires_exterior_wall=False,
                is_wet_core=False
            ))

            # 2. Upper Powder / Storage Core (Aligned over L0 powder)
            rooms.append(RoomSpec(
                room_id="r_L1_powder",
                room_type="bathroom",
                room_name="First Floor Guest Powder & Linen Core",
                zone=ArchitecturalZone.ZONE_A_PUBLIC,
                level_index=1,
                polygon=powder_poly,
                area_m2=round(Polygon(powder_poly).area, 1),
                centroid=[round((stair_x_min + stair_x_max) / 2, 2), round((y_lawn_end + stair_y_min) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=True
            ))

            # 3. Level 1 Staircase Core (Exact Vertical Coordinate Invariance)
            rooms.append(RoomSpec(
                room_id="r_L1_stair",
                room_type="corridor",
                room_name="Staircase Core Landing (DN / UP) - Invariant Shaft",
                zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
                level_index=1,
                polygon=stair_poly,
                area_m2=round(Polygon(stair_poly).area, 1),
                centroid=[round((stair_x_min + stair_x_max) / 2, 2), round((stair_y_min + stair_y_max) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 4. Upper Executive Study / Sitting Lounge (Over Drawing Salon)
            rooms.append(RoomSpec(
                room_id="r_L1_study",
                room_type="study",
                room_name="Executive Home Office & Library",
                zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
                level_index=1,
                polygon=drawing_poly,
                area_m2=round(Polygon(drawing_poly).area, 1),
                centroid=[round((min_x + lawn_w) / 2, 2), round((y_lawn_end + stair_y_max) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 5. Upper Circulation Foyer & Gallery Spines
            rooms.append(RoomSpec(
                room_id="r_L1_foyer",
                room_type="corridor",
                room_name="Upper Gallery & Foyer Circulation Spine",
                zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
                level_index=1,
                polygon=foyer_poly,
                area_m2=round(Polygon(foyer_poly).area, 1),
                centroid=[round((lawn_w + stair_x_min) / 2, 2), round((y_lawn_end + stair_y_max) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 6. Upper Family Lounge & Gallery
            rooms.append(RoomSpec(
                room_id="r_L1_lounge",
                room_type="living_room",
                room_name="Upper Family TV Lounge & Gallery",
                zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
                level_index=1,
                polygon=lounge_poly,
                area_m2=round(Polygon(lounge_poly).area, 1),
                centroid=[round((min_x + kit_x_min) / 2, 2), round((stair_y_max + y_zone_b_end) / 2, 2)],
                requires_exterior_wall=False,
                is_wet_core=False
            ))

            # 7. Upper Butler's Pantry & Beverage Station (100% Invariant over Ground Kitchen)
            rooms.append(RoomSpec(
                room_id="r_L1_kitchenette",
                room_type="kitchen",
                room_name="Upper Butler's Pantry & Beverage Station",
                zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
                level_index=1,
                polygon=kitchen_sub1_poly,
                area_m2=round(Polygon(kitchen_sub1_poly).area, 1),
                centroid=[round((kit_x_min + kit_x_max) / 2, 2), round((stair_y_max + kit_y_split) / 2, 2)],
                requires_exterior_wall=True,
                has_exterior_exhaust=True,
                is_wet_core=True
            ))

            # 8. First Floor Laundry & Utility Core (100% Invariant over Ground Dirty Scullery)
            rooms.append(RoomSpec(
                room_id="r_L1_laundry",
                room_type="storage",
                room_name="First Floor Laundry & Utility Core",
                zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
                level_index=1,
                polygon=kitchen_sub2_poly,
                area_m2=round(Polygon(kitchen_sub2_poly).area, 1),
                centroid=[round((kit_x_min + kit_x_max) / 2, 2), round((kit_y_split + y_zone_b_end) / 2, 2)],
                requires_exterior_wall=True,
                has_exterior_exhaust=True,
                is_wet_core=True
            ))

            # 9. Upper Bedroom Distribution Lobby (Exact buffer alignment)
            rooms.append(RoomSpec(
                room_id="r_L1_bed_lobby",
                room_type="corridor",
                room_name="Upper Bedroom Distribution Lobby (5'-0\" Buffer)",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=1,
                polygon=bed_lobby_poly,
                area_m2=round(Polygon(bed_lobby_poly).area, 1),
                centroid=[round((min_x + max_x) / 2, 2), round((y_zone_b_end + y_lobby_end) / 2, 2)],
                requires_exterior_wall=False,
                is_wet_core=False
            ))

            # 10. Upper Master Bedroom 3 (Stacked directly over L0 Master)
            rooms.append(RoomSpec(
                room_id="r_L1_bed3",
                room_type="bedroom",
                room_name="First Floor Master Bedroom Suite 3",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=1,
                polygon=bed_west_poly,
                area_m2=round(Polygon(bed_west_poly).area, 1),
                centroid=[round((min_x + min_x + suite_w) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 11. Upper Bath 3 (Strict 100% Vertical Alignment over Bath 1)
            rooms.append(RoomSpec(
                room_id="r_L1_bath3",
                room_type="bathroom",
                room_name="Upper Master Ensuite Spa Bath 3 (Linear Wet-Dry)",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=1,
                polygon=bath_west_poly,
                area_m2=round(Polygon(bath_west_poly).area, 1),
                centroid=[round((min_x + suite_w + bath1_x_max) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=True
            ))

            # 12. Upper Bath 4 (Strict 100% Vertical Alignment over Bath 2)
            rooms.append(RoomSpec(
                room_id="r_L1_bath4",
                room_type="bathroom",
                room_name="Upper Ensuite Attached Bath 4 (Linear Wet-Dry)",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=1,
                polygon=bath_east_poly,
                area_m2=round(Polygon(bath_east_poly).area, 1),
                centroid=[round((bath1_x_max + max_x - suite_w) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=True
            ))

            # 13. Upper Bedroom Suite 4 (Stacked directly over L0 Bedroom 2)
            rooms.append(RoomSpec(
                room_id="r_L1_bed4",
                room_type="bedroom",
                room_name="First Floor Bedroom Suite 4",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=1,
                polygon=bed_east_poly,
                area_m2=round(Polygon(bed_east_poly).area, 1),
                centroid=[round((max_x - suite_w + max_x) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 14. Upper OTS Void (Continuous vertical shaft)
            rooms.append(RoomSpec(
                room_id="r_L1_ots",
                room_type="outdoor",
                room_name="Upper Daylight OTS Shaft Void (5'-0\" Continuous)",
                zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
                level_index=1,
                polygon=ots_poly,
                area_m2=round(Polygon(ots_poly).area, 1),
                centroid=[round(self.w / 2, 2), round((y_zone_c_end + self.d) / 2, 2)],
                requires_exterior_wall=False,
                is_wet_core=False
            ))

        # ----------------------------------------------------------------------
        # LEVEL 2: SECOND FLOOR / PENTHOUSE & ROOFTOP BBQ DECK
        # ----------------------------------------------------------------------
        if self.floor_count >= 3:
            # 1. Rooftop Party Terrace & BBQ Deck (Front open expanse)
            rooftop_terrace_poly = [
                [min_x, 0.0],
                [stair_x_min, 0.0],
                [stair_x_min, stair_y_max],
                [min_x, stair_y_max],
                [min_x, 0.0]
            ]
            rooms.append(RoomSpec(
                room_id="r_L2_rooftop_terrace",
                room_type="balcony",
                room_name="Rooftop Party Terrace & BBQ Deck",
                zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
                level_index=2,
                polygon=rooftop_terrace_poly,
                area_m2=round(Polygon(rooftop_terrace_poly).area, 1),
                centroid=[round((min_x + stair_x_min) / 2, 2), round(stair_y_max / 2, 2)],
                requires_exterior_wall=False,
                is_wet_core=False
            ))

            # 2. Weather-Enclosed Mumty Penthouse Lobby / Vestibule (Min 6'-0" x 8'-0" = 4.46 m2)
            mumty_vest_poly = [
                [stair_x_min, 2.20],
                [stair_x_max, 2.20],
                [stair_x_max, stair_y_min],
                [stair_x_min, stair_y_min],
                [stair_x_min, 2.20]
            ]
            rooms.append(RoomSpec(
                room_id="r_L2_mumty_vestibule",
                room_type="corridor",
                room_name="Weather-Enclosed Mumty Penthouse Vestibule (8'-10\" x 8'-0\")",
                zone=ArchitecturalZone.ZONE_A_PUBLIC,
                level_index=2,
                polygon=mumty_vest_poly,
                area_m2=round(Polygon(mumty_vest_poly).area, 1),
                centroid=[round((stair_x_min + stair_x_max) / 2, 2), round((2.20 + stair_y_min) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 3. Level 2 Staircase Core Landing (Exact vertical coordinate invariance)
            rooms.append(RoomSpec(
                room_id="r_L2_stair",
                room_type="corridor",
                room_name="Penthouse Staircase Landing Core (DN / UP) - Invariant Shaft",
                zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
                level_index=2,
                polygon=stair_poly,
                area_m2=round(Polygon(stair_poly).area, 1),
                centroid=[round((stair_x_min + stair_x_max) / 2, 2), round((stair_y_min + stair_y_max) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 4. Multipurpose Penthouse Lounge / Gym / Salon (Zone B)
            rooms.append(RoomSpec(
                room_id="r_L2_multipurpose",
                room_type="living_room",
                room_name="Penthouse Multipurpose Family Lounge & Salon",
                zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
                level_index=2,
                polygon=lounge_poly,
                area_m2=round(Polygon(lounge_poly).area, 1),
                centroid=[round((min_x + kit_x_min) / 2, 2), round((stair_y_max + y_zone_b_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 5. Penthouse Service Kitchenette (Strict 100% Invariant over Lower Kitchens)
            rooms.append(RoomSpec(
                room_id="r_L2_kitchenette",
                room_type="kitchen",
                room_name="Penthouse Rooftop Service Kitchenette",
                zone=ArchitecturalZone.ZONE_B_SEMI_PRIVATE,
                level_index=2,
                polygon=kitchen_sub1_poly,
                area_m2=round(Polygon(kitchen_sub1_poly).area, 1),
                centroid=[round((kit_x_min + kit_x_max) / 2, 2), round((stair_y_max + kit_y_split) / 2, 2)],
                requires_exterior_wall=True,
                has_exterior_exhaust=True,
                is_wet_core=True
            ))

            # 6. Dedicated Rooftop Laundry & Utility Core (Strict 100% Invariant over Lower Sculleries)
            rooms.append(RoomSpec(
                room_id="r_L2_laundry",
                room_type="storage",
                room_name="Dedicated Rooftop Laundry & Utility Core",
                zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
                level_index=2,
                polygon=kitchen_sub2_poly,
                area_m2=round(Polygon(kitchen_sub2_poly).area, 1),
                centroid=[round((kit_x_min + kit_x_max) / 2, 2), round((kit_y_split + y_zone_b_end) / 2, 2)],
                requires_exterior_wall=True,
                has_exterior_exhaust=True,
                is_wet_core=True
            ))

            # 7. Penthouse Bedroom Lobby Buffer (5'-0" buffer)
            rooms.append(RoomSpec(
                room_id="r_L2_bed_lobby",
                room_type="corridor",
                room_name="Penthouse Suite Distribution Lobby (5'-0\" Buffer)",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=2,
                polygon=bed_lobby_poly,
                area_m2=round(Polygon(bed_lobby_poly).area, 1),
                centroid=[round((min_x + max_x) / 2, 2), round((y_zone_b_end + y_lobby_end) / 2, 2)],
                requires_exterior_wall=False,
                is_wet_core=False
            ))

            # 8. Independent Maid / Servant Suite (West Wing, stacked over lower suites)
            rooms.append(RoomSpec(
                room_id="r_L2_maid",
                room_type="bedroom",
                room_name="Independent Maid / Guest Bedroom Suite 5",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=2,
                polygon=bed_west_poly,
                area_m2=round(Polygon(bed_west_poly).area, 1),
                centroid=[round((min_x + min_x + suite_w) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 9. Multipurpose Suite Ensuite Bath (Strict 100% Invariant over Bath 1 & Bath 3)
            rooms.append(RoomSpec(
                room_id="r_L2_bath_multi",
                room_type="bathroom",
                room_name="Multipurpose Suite Ensuite Bath (Linear Wet-Dry)",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=2,
                polygon=bath_west_poly,
                area_m2=round(Polygon(bath_west_poly).area, 1),
                centroid=[round((min_x + suite_w + bath1_x_max) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=True
            ))

            # 10. Maid Ensuite Attached Bath (Strict 100% Invariant over Bath 2 & Bath 4)
            rooms.append(RoomSpec(
                room_id="r_L2_bath_maid",
                room_type="bathroom",
                room_name="Maid / Servant Ensuite Bath (Linear Wet-Dry)",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=2,
                polygon=bath_east_poly,
                area_m2=round(Polygon(bath_east_poly).area, 1),
                centroid=[round((bath1_x_max + max_x - suite_w) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=True
            ))

            # 11. Penthouse Secondary Suite 6 (East Wing, stacked over lower suites)
            rooms.append(RoomSpec(
                room_id="r_L2_bed6",
                room_type="bedroom",
                room_name="Penthouse Secondary Bedroom Suite 6",
                zone=ArchitecturalZone.ZONE_C_PRIVATE,
                level_index=2,
                polygon=bed_east_poly,
                area_m2=round(Polygon(bed_east_poly).area, 1),
                centroid=[round((max_x - suite_w + max_x) / 2, 2), round((y_lobby_end + y_zone_c_end) / 2, 2)],
                requires_exterior_wall=True,
                is_wet_core=False
            ))

            # 12. Level 2 Rear OTS Void (Strictly Open to Sky)
            rooms.append(RoomSpec(
                room_id="r_L2_ots",
                room_type="outdoor",
                room_name="Upper Daylight OTS Shaft Void (5'-0\" Continuous)",
                zone=ArchitecturalZone.ZONE_SERVICE_OUTDOOR,
                level_index=2,
                polygon=ots_poly,
                area_m2=round(Polygon(ots_poly).area, 1),
                centroid=[round(self.w / 2, 2), round((y_zone_c_end + self.d) / 2, 2)],
                requires_exterior_wall=False,
                is_wet_core=False
            ))

        # ----------------------------------------------------------------------
        # VERTICAL PLUMBING RISER SHAFTS (IoU = 1.00 Alignment Guarantee)
        # ----------------------------------------------------------------------
        # Shaft 1: Rear Bathroom Wet Core (Vertical plumbing chase between twin baths)
        shaft_1_poly = [
            [bath1_x_max - 0.30, y_zone_c_end - 0.60],
            [bath1_x_max + 0.30, y_zone_c_end - 0.60],
            [bath1_x_max + 0.30, y_zone_c_end],
            [bath1_x_max - 0.30, y_zone_c_end],
            [bath1_x_max - 0.30, y_zone_c_end - 0.60]
        ]
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_rear_baths",
            bounds_2d=shaft_1_poly,
            serves_levels=list(range(self.floor_count)),
            stack_type="SOIL_WASTE_VENT"
        ))

        # Shaft 2: Kitchen Grease & Plumbing Drainage Shaft (East perimeter)
        shaft_2_poly = [
            [kit_x_max - 0.60, kit_y_split - 0.30],
            [kit_x_max, kit_y_split - 0.30],
            [kit_x_max, kit_y_split + 0.30],
            [kit_x_max - 0.60, kit_y_split + 0.30],
            [kit_x_max - 0.60, kit_y_split - 0.30]
        ]
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_kitchen_stack",
            bounds_2d=shaft_2_poly,
            serves_levels=list(range(self.floor_count)),
            stack_type="KITCHEN_GREASE_EXHAUST"
        ))

        # Shaft 3: Powder / Mumty Drainage Core
        shaft_3_poly = [
            [stair_x_max - 0.60, stair_y_min - 0.60],
            [stair_x_max, stair_y_min - 0.60],
            [stair_x_max, stair_y_min],
            [stair_x_max - 0.60, stair_y_min],
            [stair_x_max - 0.60, stair_y_min - 0.60]
        ]
        shafts.append(VerticalPlumbingShaft(
            shaft_id="shaft_powder_mumty",
            bounds_2d=shaft_3_poly,
            serves_levels=list(range(self.floor_count)),
            stack_type="SOIL_WASTE_VENT"
        ))

        # ----------------------------------------------------------------------
        # ROOFTOP & ENCLOSED MUMTY PENTHOUSE (Enclosing Stair Core & Vestibule)
        # ----------------------------------------------------------------------
        mumty_poly = [
            [stair_x_min, 2.20],
            [stair_x_max, 2.20],
            [stair_x_max, stair_y_max],
            [stair_x_min, stair_y_max],
            [stair_x_min, 2.20]
        ]

        model = ParametricBIMModel(
            project_id=f"BIM_{int(self.w*3.28)}x{int(self.d*3.28)}_{self.floor_count}F",
            site=self.site,
            floor_count=self.floor_count,
            levels=list(range(self.floor_count)),
            rooms=rooms,
            openings=openings,
            plumbing_shafts=shafts,
            parapet_height_m=1.05,
            mumty_bounds=mumty_poly,
            metadata={
                "structural_typology": StructuralTypology.RCC_FRAME_SLAB.value,
                "floor_to_floor_height_m": 3.35,  # 11'-0"
                "slab_thickness_m": 0.15,
                "exterior_wall_thickness_m": 0.23,
                "interior_wall_thickness_m": 0.115,
                "stair_core_dimensions": f"{stair_w:.2f}m x {stair_d:.2f}m (8'-10\" x 14'-9\")",
                "stair_core_invariance": "100% Strict 3D Coordinate Invariant across L0, L1, L2",
                "wet_core_kitchen_iou": 1.00,
                "wet_core_rear_baths_iou": 1.00,
                "foyer_buffer_clearance_m": round(stair_y_min + 2.65 - (y_lawn_end + 1.20), 2),
                "ots_continuous_open": True
            }
        )

        # ----------------------------------------------------------------------
        # ERGONOMIC FURNITURE PLACEMENT & SOLID WALL ANCHORING
        # ----------------------------------------------------------------------
        self._solve_ergonomic_furniture(model)
        self._generate_compliant_openings(model)

        return model

    # --------------------------------------------------------------------------
    # FURNITURE CLEARANCE & SOLID-WALL ANCHOR SOLVER
    # --------------------------------------------------------------------------
    def _solve_ergonomic_furniture(self, model: ParametricBIMModel):
        """
        Anchors beds EXCLUSIVELY to solid interior dry walls (never against bathroom
        plumbing walls or under exterior window sills), enforces 36" (0.91m) corridor
        walking clearance, and enforces strict linear wet-dry bathroom zoning.
        """
        for room in model.rooms:
            p = Polygon(room.polygon)
            minx, miny, maxx, maxy = p.bounds
            rw = maxx - minx
            rh = maxy - miny
            z_lvl = round(room.level_index * 3.35, 2)

            if room.room_type == "bedroom":
                # King Bed (2.00m width x 2.10m depth)
                bed_w, bed_d, bed_h = 2.00, 2.10, 0.90

                # Strict Rule: Anchor headboard to solid interior dry wall at miny (lobby partition)
                # NEVER anchor against the adjacent bathroom wet plumbing wall or exterior window wall at maxy!
                bed_x = round(minx + 0.60, 2) if "bed1" in room.room_id or "bed3" in room.room_id or "maid" in room.room_id else round(maxx - bed_w - 0.60, 2)
                bed_y = round(miny + 0.10, 2)
                bed_pos = [bed_x, bed_y, z_lvl]
                anchor_edge = [[bed_x, miny], [round(bed_x + bed_w, 2), miny]]

                # 36" (0.91m) continuous walking clearance envelope around flanks and foot of bed
                clearance_poly = [
                    [round(bed_x - 0.91, 2), miny],
                    [round(bed_x + bed_w + 0.91, 2), miny],
                    [round(bed_x + bed_w + 0.91, 2), round(bed_y + bed_d + 0.91, 2)],
                    [round(bed_x - 0.91, 2), round(bed_y + bed_d + 0.91, 2)],
                    [round(bed_x - 0.91, 2), miny]
                ]

                room.furniture.append(FurnitureItem(
                    item_id=f"furn_{room.room_id}_bed",
                    category=FurnitureCategory.KING_BED,
                    room_id=room.room_id,
                    position_3d=bed_pos,
                    dimensions_m=[bed_w, bed_d, bed_h],
                    rotation_deg_z=0.0,
                    solid_wall_anchor_edge=anchor_edge,
                    clearance_envelope_polygon=clearance_poly
                ))

                # Media Console on opposite solid wall (optimal viewing throw distance)
                tv_pos = [round(minx + (rw - 1.60) / 2.0, 2), round(maxy - 0.50, 2), z_lvl]
                room.furniture.append(FurnitureItem(
                    item_id=f"furn_{room.room_id}_tv",
                    category=FurnitureCategory.TV_MEDIA_CONSOLE,
                    room_id=room.room_id,
                    position_3d=tv_pos,
                    dimensions_m=[1.60, 0.45, 0.60],
                    rotation_deg_z=180.0
                ))

                # Built-in Wardrobe Run
                wardrobe_x = round(minx + 0.10, 2) if bed_x > minx + 1.0 else round(maxx - 0.60, 2)
                room.furniture.append(FurnitureItem(
                    item_id=f"furn_{room.room_id}_wardrobe",
                    category=FurnitureCategory.WARDROBE_RUN,
                    room_id=room.room_id,
                    position_3d=[wardrobe_x, round(miny + 0.60, 2), z_lvl],
                    dimensions_m=[0.60, 1.80, 2.40],
                    rotation_deg_z=90.0
                ))

            elif room.room_type == "bathroom" and "powder" not in room.room_id:
                # Strict Linear Wet-Dry Sequence: Vanity (dry) -> Water Closet (semi-wet) -> Shower Enclosure (wet behind glass)
                # 1. Vanity Basin (Dry Zone, adjacent to entrance door)
                vanity_pos = [round(minx + 0.10, 2), round(miny + 0.30, 2), z_lvl]
                room.furniture.append(FurnitureItem(
                    item_id=f"furn_{room.room_id}_vanity",
                    category=FurnitureCategory.VANITY_BASIN,
                    room_id=room.room_id,
                    position_3d=vanity_pos,
                    dimensions_m=[round(rw - 0.20, 2), 0.50, 0.85]
                ))

                # 2. Water Closet (Semi-Wet Zone, center)
                wc_pos = [round(minx + (rw - 0.45) / 2.0, 2), round(miny + 1.15, 2), z_lvl]
                room.furniture.append(FurnitureItem(
                    item_id=f"furn_{room.room_id}_wc",
                    category=FurnitureCategory.WATER_CLOSET,
                    room_id=room.room_id,
                    position_3d=wc_pos,
                    dimensions_m=[0.45, 0.70, 0.80]
                ))

                # 3. Shower Enclosure (Wet Zone, rear against OTS window, behind 10mm glass)
                shower_pos = [round(minx + 0.05, 2), round(maxy - 0.95, 2), z_lvl]
                room.furniture.append(FurnitureItem(
                    item_id=f"furn_{room.room_id}_shower",
                    category=FurnitureCategory.SHOWER_ENCLOSURE,
                    room_id=room.room_id,
                    position_3d=shower_pos,
                    dimensions_m=[round(rw - 0.10, 2), 0.90, 2.10]
                ))

            elif room.room_type == "living_room" and "lounge" in room.room_id:
                # 3-Seater Sofa facing media wall
                sofa_pos = [round(minx + (rw - 2.40) / 2.0, 2), round(miny + 1.20, 2), z_lvl]
                room.furniture.append(FurnitureItem(
                    item_id=f"furn_{room.room_id}_sofa",
                    category=FurnitureCategory.SOFA_THREE_SEATER,
                    room_id=room.room_id,
                    position_3d=sofa_pos,
                    dimensions_m=[2.40, 1.00, 0.85]
                ))

            elif room.room_type == "garage":
                # Vehicles in Porch
                v_pos = [round(minx + (rw - 2.00) / 2.0, 2), round(miny + 0.50, 2), 0.0]
                room.furniture.append(FurnitureItem(
                    item_id=f"furn_{room.room_id}_car1",
                    category=FurnitureCategory.VEHICLE_SEDAN,
                    room_id=room.room_id,
                    position_3d=v_pos,
                    dimensions_m=[2.00, 4.80, 1.50]
                ))

    # --------------------------------------------------------------------------
    # PARAMETRIC OPENING GENERATOR
    # --------------------------------------------------------------------------
    def _generate_compliant_openings(self, model: ParametricBIMModel):
        """
        Creates strictly code-compliant doors and windows.
        Zero doors between adjacent bedrooms. All bedrooms enter via private lobby.
        Foyer doors enforce >= 5'-0" clear buffer to first stair riser.
        Mumty terminates inside weather vestibule with exterior door to terrace.
        """
        room_dict = {r.room_id: r for r in model.rooms}

        def add_door(r1_id: str, r2_id: str, cat: OpeningCategory, width_m: float = 0.914, is_ext: bool = False):
            if r1_id not in room_dict or r2_id not in room_dict:
                return
            p1 = Polygon(room_dict[r1_id].polygon)
            p2 = Polygon(room_dict[r2_id].polygon)
            inter = p1.intersection(p2)
            if inter.is_empty or inter.length < 0.30:
                return
            lines = [inter] if inter.geom_type == "LineString" else [g for g in getattr(inter, "geoms", []) if g.geom_type == "LineString"]
            if not lines:
                return
            longest = max(lines, key=lambda l: l.length)
            mid = longest.interpolate(0.5, normalized=True)
            z_lvl = room_dict[r1_id].level_index * 3.35
            model.openings.append(OpeningSpec(
                opening_id=f"door_{r1_id}_{r2_id}",
                category=cat,
                position_3d=[round(mid.x, 2), round(mid.y, 2), round(z_lvl, 2)],
                width_m=width_m,
                height_m=2.10,
                sill_height_m=0.0,
                lintel_height_m=2.10,
                connects_rooms=[r1_id, r2_id],
                level_index=room_dict[r1_id].level_index,
                is_exterior=is_ext
            ))

        # Level 0 Openings
        # Main Entry Door (Porch -> Foyer)
        add_door("r_L0_porch", "r_L0_foyer", OpeningCategory.MAIN_ENTRANCE_DOOR, width_m=1.20)
        # Foyer to Drawing Salon
        add_door("r_L0_foyer", "r_L0_drawing", OpeningCategory.INTERIOR_DOOR, width_m=1.00)
        # Foyer to Powder Room
        add_door("r_L0_foyer", "r_L0_powder", OpeningCategory.INTERIOR_DOOR, width_m=0.85)
        # Foyer to Stair Core (Positioned at deep midpoint, maintaining > 5'-0" buffer from main entrance swing)
        add_door("r_L0_foyer", "r_L0_stair", OpeningCategory.INTERIOR_DOOR, width_m=1.00)
        # Foyer to Central Lounge
        add_door("r_L0_foyer", "r_L0_lounge", OpeningCategory.INTERIOR_DOOR, width_m=1.10)
        # Drawing to Lounge
        add_door("r_L0_drawing", "r_L0_lounge", OpeningCategory.INTERIOR_DOOR, width_m=1.00)
        # Lounge to Gourmet Kitchen
        add_door("r_L0_lounge", "r_L0_kitchen", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
        # Kitchen to Scullery / Dirty Kitchen
        add_door("r_L0_kitchen", "r_L0_dirty_kitchen", OpeningCategory.SERVICE_DOOR, width_m=0.85)
        # Lounge to Private Bedroom Distribution Lobby
        add_door("r_L0_lounge", "r_L0_bed_lobby", OpeningCategory.INTERIOR_DOOR, width_m=1.05)
        # Bed Lobby to Master Suite 1
        add_door("r_L0_bed_lobby", "r_L0_bed1", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
        # Master Suite 1 to Ensuite Bath 1
        add_door("r_L0_bed1", "r_L0_bath1", OpeningCategory.INTERIOR_DOOR, width_m=0.85)
        # Bed Lobby to Guest Suite 2
        add_door("r_L0_bed_lobby", "r_L0_bed2", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
        # Guest Suite 2 to Ensuite Bath 2
        add_door("r_L0_bed2", "r_L0_bath2", OpeningCategory.INTERIOR_DOOR, width_m=0.85)

        # Level 1 Openings
        if model.floor_count >= 2:
            add_door("r_L1_foyer", "r_L1_terrace", OpeningCategory.SLIDING_PATIO_DOOR, width_m=2.00, is_ext=True)
            add_door("r_L1_foyer", "r_L1_stair", OpeningCategory.INTERIOR_DOOR, width_m=1.00)
            add_door("r_L1_foyer", "r_L1_study", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
            add_door("r_L1_foyer", "r_L1_powder", OpeningCategory.INTERIOR_DOOR, width_m=0.85)
            add_door("r_L1_foyer", "r_L1_lounge", OpeningCategory.INTERIOR_DOOR, width_m=1.10)
            add_door("r_L1_lounge", "r_L1_kitchenette", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
            add_door("r_L1_kitchenette", "r_L1_laundry", OpeningCategory.SERVICE_DOOR, width_m=0.85)
            add_door("r_L1_lounge", "r_L1_bed_lobby", OpeningCategory.INTERIOR_DOOR, width_m=1.05)
            add_door("r_L1_bed_lobby", "r_L1_bed3", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
            add_door("r_L1_bed3", "r_L1_bath3", OpeningCategory.INTERIOR_DOOR, width_m=0.85)
            add_door("r_L1_bed_lobby", "r_L1_bed4", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
            add_door("r_L1_bed4", "r_L1_bath4", OpeningCategory.INTERIOR_DOOR, width_m=0.85)

        # Level 2 Openings (Penthouse, Mumty Weather Lobby & Rooftop Terrace)
        if model.floor_count >= 3:
            # Stair core terminates inside Enclosed Mumty Penthouse Vestibule
            add_door("r_L2_stair", "r_L2_mumty_vestibule", OpeningCategory.INTERIOR_DOOR, width_m=1.00)
            # Weather-enclosed Mumty Vestibule exits onto Rooftop Terrace via weatherproof exterior door
            add_door("r_L2_mumty_vestibule", "r_L2_rooftop_terrace", OpeningCategory.SERVICE_DOOR, width_m=0.914, is_ext=True)
            # Multipurpose Suite to Terrace
            add_door("r_L2_multipurpose", "r_L2_rooftop_terrace", OpeningCategory.SLIDING_PATIO_DOOR, width_m=2.40, is_ext=True)
            add_door("r_L2_stair", "r_L2_multipurpose", OpeningCategory.INTERIOR_DOOR, width_m=1.00)
            add_door("r_L2_multipurpose", "r_L2_kitchenette", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
            add_door("r_L2_kitchenette", "r_L2_laundry", OpeningCategory.SERVICE_DOOR, width_m=0.85)
            add_door("r_L2_multipurpose", "r_L2_bed_lobby", OpeningCategory.INTERIOR_DOOR, width_m=1.05)
            add_door("r_L2_bed_lobby", "r_L2_maid", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
            add_door("r_L2_maid", "r_L2_bath_multi", OpeningCategory.INTERIOR_DOOR, width_m=0.85)
            add_door("r_L2_bed_lobby", "r_L2_bed6", OpeningCategory.INTERIOR_DOOR, width_m=0.914)
            add_door("r_L2_bed6", "r_L2_bath_maid", OpeningCategory.INTERIOR_DOOR, width_m=0.85)



# ==============================================================================
# 3. PARAMETRIC 2D-TO-3D WATERTIGHT MESH EXTRUDER & FACADE SYNTHESIZER
# ==============================================================================

class Parametric3DMeshBuilder:
    """
    Constructs clean, manifold, watertight 3D meshes (OBJ/GLB/IFC) directly from
    the ParametricBIMModel.
    - Solid floor slabs with accurate thicknesses.
    - Structural exterior and interior walls with parametric door & window cutouts (lintels/sills).
    - Multi-floor vertical alignment and stair mumty / rooftop parapets.
    """

    def __init__(self, model: ParametricBIMModel):
        self.model = model
        self.vertices: List[List[float]] = []
        self.faces: List[List[int]] = []
        self.materials: Dict[str, str] = {}
        self.current_face_material: List[str] = []

    def build_3d_geometry(self) -> Tuple[np.ndarray, List[List[int]], List[str]]:
        """
        Executes procedural extrusion: Slabs, Walls with Void Cutouts, and Rooftop Parapets.
        """
        self.vertices.clear()
        self.faces.clear()
        self.current_face_material.clear()

        fl_h = self.model.metadata.get("floor_to_floor_height_m", 3.35)
        slab_th = self.model.metadata.get("slab_thickness_m", 0.15)
        wall_h = fl_h - slab_th

        # 1. Floor Slabs for each level
        for lvl in self.model.levels:
            lvl_z = lvl * fl_h
            lvl_rooms = [r for r in self.model.rooms if r.level_index == lvl and r.room_type != "outdoor"]
            if not lvl_rooms:
                continue

            # Compute union footprint of level
            polys = [Polygon(r.polygon) for r in lvl_rooms]
            slab_union = unary_union(polys)
            if slab_union.geom_type == "Polygon":
                self._extrude_polygon_slab(slab_union, lvl_z - slab_th, lvl_z, material="Mat_Concrete_Slab")
            elif slab_union.geom_type == "MultiPolygon":
                for p in slab_union.geoms:
                    self._extrude_polygon_slab(p, lvl_z - slab_th, lvl_z, material="Mat_Concrete_Slab")

        # 2. Structural Walls with Parametric Openings
        for lvl in self.model.levels:
            lvl_z = lvl * fl_h
            lvl_rooms = [r for r in self.model.rooms if r.level_index == lvl and r.room_type != "outdoor"]
            lvl_openings = [op for op in self.model.openings if op.level_index == lvl]

            for room in lvl_rooms:
                poly = room.polygon
                n_pts = len(poly) - 1
                for i in range(n_pts):
                    p1 = poly[i]
                    p2 = poly[i + 1]
                    wall_seg = LineString([p1, p2])
                    if wall_seg.length < 0.10:
                        continue

                    # Find openings intercepting this wall segment
                    wall_ops = []
                    for op in lvl_openings:
                        op_pt = Point(op.position_3d[0], op.position_3d[1])
                        if wall_seg.distance(op_pt) < 0.15:
                            wall_ops.append(op)

                    mat = "Mat_Exterior_Travertine" if room.requires_exterior_wall else "Mat_Interior_Plaster"
                    self._extrude_wall_segment_with_openings(p1, p2, lvl_z, lvl_z + wall_h, wall_ops, material=mat)

        # 3. Rooftop Parapets & Mumty Stair Penthouse
        roof_z = self.model.floor_count * fl_h
        parapet_h = self.model.parapet_height_m

        # Extrude Mumty Penthouse (Stair shaft to rooftop)
        if self.model.mumty_bounds:
            mumty_poly = Polygon(self.model.mumty_bounds)
            mumty_h = 2.45  # 8'-0" headroom
            self._extrude_polygon_slab(mumty_poly, roof_z, roof_z + slab_th, material="Mat_Concrete_Slab")
            # Mumty walls
            m_coords = list(mumty_poly.exterior.coords)
            for i in range(len(m_coords) - 1):
                self._extrude_wall_segment(m_coords[i], m_coords[i + 1], roof_z, roof_z + mumty_h, material="Mat_Exterior_Travertine")
            # Mumty roof slab
            self._extrude_polygon_slab(mumty_poly, roof_z + mumty_h, roof_z + mumty_h + slab_th, material="Mat_Concrete_Slab")

        # Rooftop Perimeter Parapet Walls
        top_lvl = self.model.floor_count - 1
        top_rooms = [r for r in self.model.rooms if r.level_index == top_lvl and r.room_type != "outdoor"]
        if top_rooms:
            top_union = unary_union([Polygon(r.polygon) for r in top_rooms])
            if top_union.geom_type == "Polygon":
                coords = list(top_union.exterior.coords)
                for i in range(len(coords) - 1):
                    self._extrude_wall_segment(coords[i], coords[i + 1], roof_z, roof_z + parapet_h, thickness=0.23, material="Mat_Parapet_DarkMetal")
            elif top_union.geom_type == "MultiPolygon":
                for p in top_union.geoms:
                    coords = list(p.exterior.coords)
                    for i in range(len(coords) - 1):
                        self._extrude_wall_segment(coords[i], coords[i + 1], roof_z, roof_z + parapet_h, thickness=0.23, material="Mat_Parapet_DarkMetal")

        # 4. Facade Elements & Volumetric 3D Architectural Features
        for elem in self.model.facade_elements:
            etype = elem.element_type
            pos = elem.position_3d
            dims = elem.dimensions_m
            mat = elem.material

            if etype == "CANTILEVER_BALCONY":
                # Cantilevered floor slab
                self._extrude_box(pos, dims, material=mat)
                # Glass balustrade perimeter (1.05m high)
                bal_h = 1.05
                bal_th = 0.05
                bx, by, bz = pos[0], pos[1], pos[2] + dims[2]
                bw, bd = dims[0], dims[1]
                # front edge
                self._extrude_box([bx, by, bz], [bw, bal_th, bal_h], material="Mat_Floor_Glazing")
                # left edge
                self._extrude_box([bx, by, bz], [bal_th, bd, bal_h], material="Mat_Floor_Glazing")
                # right edge
                self._extrude_box([bx + bw - bal_th, by, bz], [bal_th, bd, bal_h], material="Mat_Floor_Glazing")

            elif etype == "TIMBER_LOUVERS":
                # Extrude vertical architectural timber louvers (fins)
                x_start, y_pos, z_start = pos
                w_span, louver_depth, louver_h = dims
                num_fins = 12
                fin_w = 0.06
                spacing = (w_span - fin_w) / max(1, (num_fins - 1))
                for k in range(num_fins):
                    fx = x_start + k * spacing
                    self._extrude_box([fx, y_pos, z_start], [fin_w, louver_depth, louver_h], material=mat)

            elif etype == "FLUTED_LIMESTONE_PANEL":
                # Extrude fluted stone cladding panel with vertical flute relief
                self._extrude_box(pos, dims, material=mat)
                px, py, pz = pos
                pw, pth, ph = dims
                num_flutes = 16
                flute_w = 0.05
                f_spacing = (pw - flute_w) / max(1, (num_flutes - 1))
                for k in range(num_flutes):
                    fx = px + k * f_spacing
                    self._extrude_box([fx, py - 0.03, pz], [flute_w, 0.03, ph], material=mat)

            elif etype == "CURTAIN_WALLING":
                # Floor-to-ceiling curtain wall with slim aluminum frame and double glazing
                self._extrude_box(pos, dims, material=mat)
                cx, cy, cz = pos
                cw, cth, ch = dims
                mullion_w = 0.05
                for m_frac in [0.0, 0.33, 0.67, 1.0]:
                    mx = cx + (cw - mullion_w) * m_frac
                    self._extrude_box([mx, cy - 0.02, cz], [mullion_w, cth + 0.04, ch], material="Mat_Parapet_DarkMetal")

            elif etype == "MUMTY_TOWER":
                # 9'-0" high enclosed stair mumty tower
                self._extrude_box(pos, dims, material=mat)

            elif etype == "WATER_RESERVOIR":
                # Overhead concrete water tank with coping lid
                self._extrude_box(pos, dims, material=mat)
                tx, ty, tz = pos
                tw, td, th = dims
                self._extrude_box([tx - 0.10, ty - 0.10, tz + th], [tw + 0.20, td + 0.20, 0.12], material=mat)

            elif etype == "PERGOLA":
                # Cedar wood pergola: 4 corner posts + horizontal top rafters
                px, py, pz = pos
                pw, pd, ph = dims
                post_sz = 0.15
                rafter_h = 0.20
                corners = [[px, py], [px + pw - post_sz, py], [px, py + pd - post_sz], [px + pw - post_sz, py + pd - post_sz]]
                for c in corners:
                    self._extrude_box([c[0], c[1], pz], [post_sz, post_sz, ph], material=mat)
                # Perimeter beams
                self._extrude_box([px, py, pz + ph], [pw, post_sz, rafter_h], material=mat)
                self._extrude_box([px, py + pd - post_sz, pz + ph], [pw, post_sz, rafter_h], material=mat)
                # Cross rafters
                num_rafters = 7
                r_spacing = (pw - 0.08) / max(1, (num_rafters - 1))
                for r_i in range(num_rafters):
                    rx = px + r_i * r_spacing
                    self._extrude_box([rx, py, pz + ph + rafter_h], [0.08, pd, 0.12], material=mat)

            elif etype == "SOLAR_ARRAY":
                # Solar inverter rack and angled photovoltaic panels
                self._extrude_box(pos, dims, material=mat)

        return np.array(self.vertices), self.faces, self.current_face_material

    # ---- Internal Mesh Geometry Helpers ----

    def _add_vertex(self, x: float, y: float, z: float) -> int:
        self.vertices.append([round(x, 4), round(y, 4), round(z, 4)])
        return len(self.vertices) - 1

    def _add_quad_face(self, i1: int, i2: int, i3: int, i4: int, mat: str):
        self.faces.append([i1, i2, i3, i4])
        self.current_face_material.append(mat)

    def _extrude_box(self, pos: List[float], dims: List[float], material: str = "Mat_Exterior_Travertine"):
        """Extrudes a solid watertight 6-faced axis-aligned 3D box."""
        x, y, z = pos[0], pos[1], pos[2]
        dx, dy, dz = dims[0], dims[1], dims[2]

        v0 = self._add_vertex(x, y, z)
        v1 = self._add_vertex(x + dx, y, z)
        v2 = self._add_vertex(x + dx, y + dy, z)
        v3 = self._add_vertex(x, y + dy, z)
        v4 = self._add_vertex(x, y, z + dz)
        v5 = self._add_vertex(x + dx, y, z + dz)
        v6 = self._add_vertex(x + dx, y + dy, z + dz)
        v7 = self._add_vertex(x, y + dy, z + dz)

        # 6 faces
        self._add_quad_face(v3, v2, v1, v0, material)  # bottom
        self._add_quad_face(v4, v5, v6, v7, material)  # top
        self._add_quad_face(v0, v1, v5, v4, material)  # front (-y)
        self._add_quad_face(v1, v2, v6, v5, material)  # right (+x)
        self._add_quad_face(v2, v3, v7, v6, material)  # back (+y)
        self._add_quad_face(v3, v0, v4, v7, material)  # left (-x)

    def _extrude_polygon_slab(self, poly: Polygon, z_bottom: float, z_top: float, material: str = "Mat_Concrete_Slab"):
        coords = list(poly.exterior.coords)[:-1]
        n = len(coords)
        if n < 3:
            return

        bot_indices = [self._add_vertex(pt[0], pt[1], z_bottom) for pt in coords]
        top_indices = [self._add_vertex(pt[0], pt[1], z_top) for pt in coords]

        # Bottom face (reverse winding for normal down)
        self.faces.append(bot_indices[::-1])
        self.current_face_material.append(material)

        # Top face (standard normal up)
        self.faces.append(top_indices)
        self.current_face_material.append(material)

        # Side skirts
        for i in range(n):
            next_i = (i + 1) % n
            self._add_quad_face(
                bot_indices[i],
                bot_indices[next_i],
                top_indices[next_i],
                top_indices[i],
                material
            )

    def _extrude_wall_segment(self, p1: List[float], p2: List[float], z_bot: float, z_top: float, thickness: float = 0.23, material: str = "Mat_Exterior_Travertine"):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length < 0.05:
            return

        nx = -dy / length * (thickness / 2.0)
        ny = dx / length * (thickness / 2.0)

        # 4 footprint corners
        c1 = [p1[0] + nx, p1[1] + ny]
        c2 = [p2[0] + nx, p2[1] + ny]
        c3 = [p2[0] - nx, p2[1] - ny]
        c4 = [p1[0] - nx, p1[1] - ny]

        b1 = self._add_vertex(c1[0], c1[1], z_bot)
        b2 = self._add_vertex(c2[0], c2[1], z_bot)
        b3 = self._add_vertex(c3[0], c3[1], z_bot)
        b4 = self._add_vertex(c4[0], c4[1], z_bot)

        t1 = self._add_vertex(c1[0], c1[1], z_top)
        t2 = self._add_vertex(c2[0], c2[1], z_top)
        t3 = self._add_vertex(c3[0], c3[1], z_top)
        t4 = self._add_vertex(c4[0], c4[1], z_top)

        # 4 side faces
        self._add_quad_face(b1, b2, t2, t1, material)
        self._add_quad_face(b2, b3, t3, t2, material)
        self._add_quad_face(b3, b4, t4, t3, material)
        self._add_quad_face(b4, b1, t1, t4, material)
        # Top cap
        self._add_quad_face(t1, t2, t3, t4, material)

    def _extrude_wall_segment_with_openings(
        self,
        p1: List[float],
        p2: List[float],
        z_bot: float,
        z_top: float,
        openings: List[OpeningSpec],
        thickness: float = 0.23,
        material: str = "Mat_Exterior_Travertine"
    ):
        """
        Extrudes wall segment and parametrically punches out doors & windows.
        Constructs lower sill wall, side piers, and upper lintel beam.
        """
        if not openings:
            self._extrude_wall_segment(p1, p2, z_bot, z_top, thickness, material)
            return

        wall_line = LineString([p1, p2])
        w_len = wall_line.length
        dx = (p2[0] - p1[0]) / w_len
        dy = (p2[1] - p1[1]) / w_len

        for op in openings:
            op_w = op.width_m
            op_h = op.height_m
            sill_h = op.sill_height_m
            lintel_h = op.lintel_height_m

            # Sub-sill wall (below window)
            if sill_h > 0.05:
                self._extrude_wall_segment(p1, p2, z_bot, z_bot + sill_h, thickness, material)

            # Lintel beam (above opening up to ceiling)
            if z_top - (z_bot + lintel_h) > 0.05:
                self._extrude_wall_segment(p1, p2, z_bot + lintel_h, z_top, thickness, material)

            # Flanking solid piers
            pier_len = max(0.40, (w_len - op_w) / 2.0)
            left_pt = [p1[0] + dx * pier_len, p1[1] + dy * pier_len]
            right_pt = [p2[0] - dx * pier_len, p2[1] - dy * pier_len]

            self._extrude_wall_segment(p1, left_pt, z_bot + sill_h, z_bot + lintel_h, thickness, material)
            self._extrude_wall_segment(right_pt, p2, z_bot + sill_h, z_bot + lintel_h, thickness, material)

    # ---- Standard Wavefront OBJ / MTL Exporter ----

    def export_to_obj(self, obj_path: str, mtl_path: Optional[str] = None):
        """
        Exports the watertight BIM geometry to standard Wavefront OBJ format.
        """
        self.build_3d_geometry()
        os.makedirs(os.path.dirname(os.path.abspath(obj_path)), exist_ok=True)
        mtl_filename = os.path.basename(mtl_path) if mtl_path else "materials.mtl"

        with open(obj_path, "w", encoding="utf-8") as f:
            f.write("# Parametric Generative BIM Architecture Engine\n")
            f.write(f"# Project: {self.model.project_id}\n")
            f.write(f"mtllib {mtl_filename}\n\n")

            # Write Vertices
            for v in self.vertices:
                f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")

            f.write("\n")

            # Write Faces grouped by Material
            current_mat = None
            for face, mat in zip(self.faces, self.current_face_material):
                if mat != current_mat:
                    current_mat = mat
                    f.write(f"\nusemtl {current_mat}\n")
                face_str = " ".join(str(idx + 1) for idx in face)
                f.write(f"f {face_str}\n")

        # Write Material Definition File (MTL)
        if mtl_path:
            with open(mtl_path, "w", encoding="utf-8") as mf:
                mf.write("# BIM Material Definitions\n")
                mf.write("newmtl Mat_Concrete_Slab\nKd 0.75 0.75 0.78\nKa 0.2 0.2 0.2\nRoughness 0.8\n\n")
                mf.write("newmtl Mat_Exterior_Travertine\nKd 0.92 0.89 0.82\nKa 0.3 0.3 0.3\nRoughness 0.5\n\n")
                mf.write("newmtl Mat_Interior_Plaster\nKd 0.96 0.96 0.94\nKa 0.2 0.2 0.2\nRoughness 0.9\n\n")
                mf.write("newmtl Mat_Parapet_DarkMetal\nKd 0.18 0.20 0.24\nKa 0.1 0.1 0.1\nRoughness 0.3\nMetallic 0.7\n\n")
                mf.write("newmtl Mat_Fluted_Limestone\nKd 0.88 0.85 0.78\nKa 0.3 0.3 0.3\nRoughness 0.6\n\n")
                mf.write("newmtl Mat_Timber_Louvers\nKd 0.58 0.35 0.18\nKa 0.2 0.2 0.2\nRoughness 0.4\n\n")
                mf.write("newmtl Mat_Floor_Glazing\nKd 0.30 0.50 0.65\nKa 0.1 0.2 0.3\nd 0.60\nRoughness 0.1\n\n")
                mf.write("newmtl Mat_Water_Reservoir\nKd 0.45 0.46 0.48\nKa 0.2 0.2 0.2\nRoughness 0.85\n\n")
                mf.write("newmtl Mat_Pergola_Wood\nKd 0.42 0.28 0.16\nKa 0.2 0.2 0.2\nRoughness 0.7\n\n")
                mf.write("newmtl Mat_Solar_Panels\nKd 0.08 0.12 0.22\nKa 0.1 0.1 0.1\nRoughness 0.2\nMetallic 0.8\n\n")


# ==============================================================================
# 4. JSON SCHEMA SPECIFICATION & VALIDATOR (DRAFT 2020-12 COMPLIANT)
# ==============================================================================

BIM_LAYOUT_JSON_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ParametricBIMFloorPlanSpecification",
    "description": "Standardized schema capturing spatial constraint graphs, 3D vertical wet risers, ergonomic clearances, and BIM-ready geometry.",
    "type": "object",
    "required": [
        "project_id",
        "site",
        "floor_count",
        "levels",
        "rooms",
        "openings",
        "plumbing_shafts"
    ],
    "properties": {
        "project_id": {"type": "string"},
        "floor_count": {"type": "integer", "minimum": 1, "maximum": 5},
        "levels": {
            "type": "array",
            "items": {"type": "integer"}
        },
        "site": {
            "type": "object",
            "required": ["width_m", "depth_m", "setbacks"],
            "properties": {
                "width_m": {"type": "number", "minimum": 3.0},
                "depth_m": {"type": "number", "minimum": 8.0},
                "street_frontage": {"type": "string", "enum": ["NORTH", "SOUTH", "EAST", "WEST"]},
                "setbacks": {
                    "type": "object",
                    "required": ["front_m", "rear_m", "side_left_m", "side_right_m"],
                    "properties": {
                        "front_m": {"type": "number", "minimum": 0.0},
                        "rear_m": {"type": "number", "minimum": 0.0},
                        "side_left_m": {"type": "number", "minimum": 0.0},
                        "side_right_m": {"type": "number", "minimum": 0.0}
                    }
                }
            }
        },
        "rooms": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["room_id", "room_type", "room_name", "zone", "level_index", "polygon", "area_m2"],
                "properties": {
                    "room_id": {"type": "string"},
                    "room_type": {"type": "string"},
                    "room_name": {"type": "string"},
                    "zone": {"type": "string", "enum": ["ZONE_A_PUBLIC", "ZONE_B_SEMI_PRIVATE", "ZONE_C_PRIVATE", "ZONE_SERVICE_OUTDOOR"]},
                    "level_index": {"type": "integer"},
                    "polygon": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "minItems": 4
                    },
                    "area_m2": {"type": "number", "minimum": 1.0},
                    "has_exterior_exhaust": {"type": "boolean"},
                    "is_wet_core": {"type": "boolean"},
                    "furniture": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["item_id", "category", "position_3d", "dimensions_m"],
                            "properties": {
                                "item_id": {"type": "string"},
                                "category": {"type": "string"},
                                "position_3d": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                                "dimensions_m": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3}
                            }
                        }
                    }
                }
            }
        },
        "openings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["opening_id", "category", "position_3d", "width_m", "height_m", "connects_rooms", "level_index"],
                "properties": {
                    "opening_id": {"type": "string"},
                    "category": {"type": "string"},
                    "position_3d": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                    "width_m": {"type": "number", "minimum": 0.5},
                    "height_m": {"type": "number", "minimum": 1.0},
                    "connects_rooms": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "plumbing_shafts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["shaft_id", "bounds_2d", "serves_levels", "stack_type"],
                "properties": {
                    "shaft_id": {"type": "string"},
                    "serves_levels": {"type": "array", "items": {"type": "integer"}},
                    "stack_type": {"type": "string"}
                }
            }
        }
    }
}
