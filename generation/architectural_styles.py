"""
Architectural Style Knowledge & Classification Engine.
Supports 27 distinct residential architectural styles with complete
spatial layout rules, 3D facade parameters, roof geometries, and PBR material palettes.

Supported Styles:
1. Mid-Century Modern
2. Georgian
3. Tudor Revival
4. Greek Revival
5. Victorian
6. Colonial
7. Saltbox
8. French Provincial
9. Prairie School
10. Modern
11. Contemporary
12. Craftsman
13. Bungalow
14. Cottage
15. Ranch
16. Mediterranean Revival
17. Gothic Revival
18. Art Deco
19. International Style
20. Farmhouse
21. Cabin
22. Chalet
23. Mediterranean
24. Spanish Revival
25. Cape Cod
26. American Foursquare
27. Split-Level
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PBRColor:
    r: float
    g: float
    b: float
    roughness: float = 0.60
    metallic: float = 0.0
    transmission: float = 0.0
    ior: float = 1.45

    def to_rgb(self) -> Tuple[float, float, float]:
        return (self.r, self.g, self.b)


@dataclass
class ArchitecturalStyleConfig:
    style_id: str
    display_name: str
    family: str
    aliases: List[str]
    description: str
    
    # Spatial layout rules
    layout_archetype: str       # "courtyard_centric", "symmetrical_central_hall", "linear_horizontal_flow", "four_quadrant_box", "open_concept_pavilion", "split_level_staggered", "asymmetrical_picturesque", "deep_veranda_wrap"
    preferred_stair: str        # "curved", "bifurcated", "dogleg", "linear", "u_shaped", "floating"
    indoor_outdoor_focus: str   # "courtyard_loggia", "wrap_around_porch", "front_portico", "garden_terrace_glass", "lanai_patio", "screened_veranda"
    characteristic_spaces: List[str]
    
    # 3D Facade & Roof Generation
    roof_type: str              # "terracotta_barrel_tile", "steep_timber_gable", "classical_hipped", "low_pitch_overhang", "steep_gable_shingle", "box_parapet_stepped", "minimalist_flat_cantilever", "pitched_metal_seam", "asymmetrical_saltbox", "chalet_gable"
    roof_pitch_deg: float       # Slope angle in degrees (0 for flat, 14-18 for low, 30 for medium, 45-55 for steep)
    eave_overhang_m: float      # Roof overhang depth in meters (e.g. 0.2m for colonial, 0.9m for prairie/craftsman)
    wall_finish_type: str       # "stucco_terracotta", "half_timber_brick", "red_brick_quoin", "white_classical_stone", "board_batten_wood", "natural_fieldstone_wood", "sleek_glass_metal", "art_deco_carved_stone", "cedar_shake_siding"
    column_type: str            # "arched_arcade", "tapered_piers", "fluted_classical", "square_timber_posts", "slender_steel_columns", "heavy_stone_piers", "half_timber_frame"
    balcony_railing: str        # "wrought_iron_curved", "glass_frameless", "wood_spindle_baluster", "solid_parapet_stucco", "perforated_geometric"
    window_style: str           # "arched_recessed", "multi_pane_sash", "tall_leaded_diamond", "ribbon_casement", "floor_to_ceiling_curtain", "divided_lite_colonial"
    has_chimney: bool = False
    has_half_timbering: bool = False
    has_dormers: bool = False
    has_wrap_porch: bool = False
    has_arched_loggia: bool = False

    # PBR Palette
    wall_color: PBRColor = field(default_factory=lambda: PBRColor(0.92, 0.90, 0.88, roughness=0.80))
    accent_wall_color: PBRColor = field(default_factory=lambda: PBRColor(0.25, 0.20, 0.16, roughness=0.70))
    roof_color: PBRColor = field(default_factory=lambda: PBRColor(0.18, 0.20, 0.22, roughness=0.60))
    trim_color: PBRColor = field(default_factory=lambda: PBRColor(0.95, 0.95, 0.95, roughness=0.40))
    column_color: PBRColor = field(default_factory=lambda: PBRColor(0.90, 0.90, 0.88, roughness=0.60))
    glass_color: PBRColor = field(default_factory=lambda: PBRColor(0.82, 0.92, 0.96, roughness=0.04, transmission=0.90))


# =============================================================================
# COMPLETE CATALOG OF 27 ARCHITECTURAL STYLES
# =============================================================================

STYLE_CATALOG: Dict[str, ArchitecturalStyleConfig] = {

    # 1. Mid-Century Modern
    "mid_century_modern": ArchitecturalStyleConfig(
        style_id="mid_century_modern",
        display_name="Mid-Century Modern",
        family="Modernist & International",
        aliases=["mid-century modern", "mid century modern", "mcm", "midcentury modern", "mid century"],
        description="Celebrates flat or low-sloping roofs, post-and-beam openness, floor-to-ceiling glass pavilions, and natural stone accent planes.",
        layout_archetype="open_concept_pavilion",
        preferred_stair="floating",
        indoor_outdoor_focus="garden_terrace_glass",
        characteristic_spaces=["Glass Living Pavilion", "Natural Stone Hearth Room", "Sunken Conversation Pit", "Covered Carport", "Private Courtyard Terrace"],
        roof_type="minimalist_flat_cantilever",
        roof_pitch_deg=6.0,
        eave_overhang_m=0.75,
        wall_finish_type="natural_fieldstone_wood",
        column_type="slender_steel_columns",
        balcony_railing="glass_frameless",
        window_style="floor_to_ceiling_curtain",
        wall_color=PBRColor(0.88, 0.86, 0.82, roughness=0.75),
        accent_wall_color=PBRColor(0.42, 0.35, 0.28, roughness=0.85), # Stacked fieldstone
        roof_color=PBRColor(0.15, 0.16, 0.18, roughness=0.50),
        trim_color=PBRColor(0.12, 0.12, 0.12, roughness=0.30, metallic=0.7), # Dark metal fascia
    ),

    # 2. Georgian
    "georgian": ArchitecturalStyleConfig(
        style_id="georgian",
        display_name="Georgian",
        family="Classical & Colonial",
        aliases=["georgian", "georgian revival", "georgian style", "english georgian"],
        description="Classical formal symmetry, central front entrance pediment flanked by balanced multi-pane sash windows, dentil cornice, and red brick facing.",
        layout_archetype="symmetrical_central_hall",
        preferred_stair="bifurcated",
        indoor_outdoor_focus="front_portico",
        characteristic_spaces=["Symmetrical Grand Foyer", "Formal Salon Drawing", "Banquet Dining Hall", "Classic Library / Study", "Balanced Flanking Master Suites"],
        roof_type="classical_hipped",
        roof_pitch_deg=32.0,
        eave_overhang_m=0.30,
        wall_finish_type="red_brick_quoin",
        column_type="fluted_classical",
        balcony_railing="solid_parapet_stucco",
        window_style="multi_pane_sash",
        has_chimney=True,
        has_dormers=True,
        wall_color=PBRColor(0.65, 0.26, 0.20, roughness=0.85), # Red facing brick
        accent_wall_color=PBRColor(0.92, 0.91, 0.88, roughness=0.50), # White stone quoins
        roof_color=PBRColor(0.24, 0.26, 0.28, roughness=0.60), # Slate gray
        trim_color=PBRColor(0.95, 0.95, 0.94, roughness=0.40),
        column_color=PBRColor(0.95, 0.95, 0.94, roughness=0.40),
    ),

    # 3. Tudor Revival
    "tudor_revival": ArchitecturalStyleConfig(
        style_id="tudor_revival",
        display_name="Tudor Revival",
        family="English Tudor & Gothic",
        aliases=["tudor", "tudor revival", "mock tudor", "english tudor"],
        description="Dramatic steep cross-gabled rooflines, exposed dark oak half-timbering with light plaster infill, tall leaded mullioned casements, and massive brick chimneys.",
        layout_archetype="asymmetrical_picturesque",
        preferred_stair="dogleg",
        indoor_outdoor_focus="courtyard_loggia",
        characteristic_spaces=["Inglenook Hearth Lounge", "Great Timbered Hall", "Gothic Arched Foyer", "Country Scullery Kitchen", "Bay Alcove Parlor"],
        roof_type="steep_timber_gable",
        roof_pitch_deg=50.0,
        eave_overhang_m=0.35,
        wall_finish_type="half_timber_brick",
        column_type="half_timber_frame",
        balcony_railing="wood_spindle_baluster",
        window_style="tall_leaded_diamond",
        has_chimney=True,
        has_half_timbering=True,
        wall_color=PBRColor(0.92, 0.90, 0.84, roughness=0.80), # Light plaster
        accent_wall_color=PBRColor(0.22, 0.14, 0.09, roughness=0.70), # Dark oak half-timber
        roof_color=PBRColor(0.18, 0.17, 0.16, roughness=0.70), # Dark clay/slate
        trim_color=PBRColor(0.20, 0.13, 0.08, roughness=0.60),
    ),

    # 4. Greek Revival
    "greek_revival": ArchitecturalStyleConfig(
        style_id="greek_revival",
        display_name="Greek Revival",
        family="Classical & Colonial",
        aliases=["greek revival", "neo-grec", "hellenic revival", "temple style"],
        description="Monumental temple-front facade, prominent triangular pediment, towering fluted Doric or Ionic portico columns, and crisp white stone finish.",
        layout_archetype="symmetrical_central_hall",
        preferred_stair="bifurcated",
        indoor_outdoor_focus="front_portico",
        characteristic_spaces=["Colonnaded Temple Portico", "Grand Vestibule Rotunda", "Classical Banquet Hall", "Symmetrical Formal Salon", "Stately Master Chamber"],
        roof_type="classical_hipped",
        roof_pitch_deg=22.0,
        eave_overhang_m=0.45,
        wall_finish_type="white_classical_stone",
        column_type="fluted_classical",
        balcony_railing="solid_parapet_stucco",
        window_style="divided_lite_colonial",
        wall_color=PBRColor(0.96, 0.96, 0.94, roughness=0.55), # Crisp white stone
        accent_wall_color=PBRColor(0.90, 0.89, 0.86, roughness=0.50),
        roof_color=PBRColor(0.28, 0.30, 0.32, roughness=0.55),
        trim_color=PBRColor(0.98, 0.98, 0.98, roughness=0.35),
        column_color=PBRColor(0.97, 0.97, 0.95, roughness=0.40),
    ),

    # 5. Victorian
    "victorian": ArchitecturalStyleConfig(
        style_id="victorian",
        display_name="Victorian",
        family="Victorian & Eclectic",
        aliases=["victorian", "queen anne", "victorian revival", "ornate victorian"],
        description="Rich asymmetrical silhouette, octagonal corner turrets, wrap-around porch with ornate carved brackets/fretwork, and multi-faceted roof planes.",
        layout_archetype="asymmetrical_picturesque",
        preferred_stair="curved",
        indoor_outdoor_focus="wrap_around_porch",
        characteristic_spaces=["Wrap-Around Veranda", "Turret Bay Parlor", "Formal Tea Drawing Room", "Butler's Pantry & Kitchen", "Upper Sitting Gallery"],
        roof_type="steep_timber_gable",
        roof_pitch_deg=45.0,
        eave_overhang_m=0.45,
        wall_finish_type="cedar_shake_siding",
        column_type="fluted_classical",
        balcony_railing="wood_spindle_baluster",
        window_style="tall_leaded_diamond",
        has_chimney=True,
        has_dormers=True,
        has_wrap_porch=True,
        wall_color=PBRColor(0.78, 0.74, 0.68, roughness=0.75),
        accent_wall_color=PBRColor(0.45, 0.22, 0.20, roughness=0.65), # Victorian burgundy accent
        roof_color=PBRColor(0.22, 0.22, 0.25, roughness=0.60),
        trim_color=PBRColor(0.92, 0.90, 0.85, roughness=0.40),
    ),

    # 6. Colonial
    "colonial": ArchitecturalStyleConfig(
        style_id="colonial",
        display_name="Colonial",
        family="Classical & Colonial",
        aliases=["colonial", "american colonial", "colonial revival", "traditional colonial"],
        description="Rigorous rectangular two-storey massing, centered front entryway with pilasters, evenly spaced multi-pane double-hung windows with exterior shutters.",
        layout_archetype="four_quadrant_box",
        preferred_stair="dogleg",
        indoor_outdoor_focus="front_portico",
        characteristic_spaces=["Central Entrance Foyer", "Front Drawing Parlor", "Formal Dining Room", "Rear Family Kitchen", "Upper Corner Bedrooms"],
        roof_type="classical_hipped",
        roof_pitch_deg=35.0,
        eave_overhang_m=0.25,
        wall_finish_type="red_brick_quoin",
        column_type="fluted_classical",
        balcony_railing="wood_spindle_baluster",
        window_style="divided_lite_colonial",
        has_chimney=True,
        wall_color=PBRColor(0.62, 0.25, 0.20, roughness=0.85), # Red brick
        accent_wall_color=PBRColor(0.92, 0.92, 0.90, roughness=0.50), # White accents
        roof_color=PBRColor(0.20, 0.21, 0.23, roughness=0.60),
        trim_color=PBRColor(0.95, 0.95, 0.95, roughness=0.35),
    ),

    # 7. Saltbox
    "saltbox": ArchitecturalStyleConfig(
        style_id="saltbox",
        display_name="Saltbox",
        family="Classical & Colonial",
        aliases=["saltbox", "salt box", "new england saltbox", "colonial saltbox"],
        description="Iconic asymmetrical pitched roof sloping steeply from two storeys in the front down to a single storey in the rear, centered chimney, and compact timber framing.",
        layout_archetype="four_quadrant_box",
        preferred_stair="dogleg",
        indoor_outdoor_focus="front_portico",
        characteristic_spaces=["Front Keeping Room", "Hearth Kitchen Hall", "Rear Lean-To Utility", "Central Hearth Core", "Front Master Chamber"],
        roof_type="asymmetrical_saltbox",
        roof_pitch_deg=42.0,
        eave_overhang_m=0.20,
        wall_finish_type="board_batten_wood",
        column_type="square_timber_posts",
        balcony_railing="wood_spindle_baluster",
        window_style="divided_lite_colonial",
        has_chimney=True,
        wall_color=PBRColor(0.58, 0.32, 0.22, roughness=0.80), # Weathered barnwood or red clapboard
        accent_wall_color=PBRColor(0.85, 0.82, 0.78, roughness=0.60),
        roof_color=PBRColor(0.25, 0.26, 0.28, roughness=0.65),
        trim_color=PBRColor(0.90, 0.90, 0.88, roughness=0.45),
    ),

    # 8. French Provincial
    "french_provincial": ArchitecturalStyleConfig(
        style_id="french_provincial",
        display_name="French Provincial",
        family="European Revival",
        aliases=["french provincial", "french country", "normandy revival", "chateauesque"],
        description="Steep high-hipped mansard/slate roof, arched copper-hood dormers, symmetrical rusticated stone or stucco facade, and tall casement windows with wrought iron balustrades.",
        layout_archetype="symmetrical_central_hall",
        preferred_stair="curved",
        indoor_outdoor_focus="courtyard_loggia",
        characteristic_spaces=["French Grand Salon", "Formal Dining Gallery", "Provincial Country Kitchen", "Wine & Pantry Cellar", "Upper Chateau Suites"],
        roof_type="classical_hipped",
        roof_pitch_deg=45.0,
        eave_overhang_m=0.35,
        wall_finish_type="stucco_terracotta",
        column_type="fluted_classical",
        balcony_railing="wrought_iron_curved",
        window_style="arched_recessed",
        has_dormers=True,
        wall_color=PBRColor(0.88, 0.85, 0.80, roughness=0.75), # Parisian limestone/cream
        accent_wall_color=PBRColor(0.72, 0.68, 0.62, roughness=0.80),
        roof_color=PBRColor(0.25, 0.28, 0.32, roughness=0.55), # Blue-gray slate
        trim_color=PBRColor(0.92, 0.90, 0.86, roughness=0.40),
    ),

    # 9. Prairie School
    "prairie_school": ArchitecturalStyleConfig(
        style_id="prairie_school",
        display_name="Prairie School",
        family="American Arts & Crafts",
        aliases=["prairie", "prairie school", "frank lloyd wright style", "prairie modern"],
        description="Low horizontal profile harmonizing with the ground, wide cantilevered eaves, continuous bands of ribbon casement windows, and massive central hearth core.",
        layout_archetype="linear_horizontal_flow",
        preferred_stair="linear",
        indoor_outdoor_focus="garden_terrace_glass",
        characteristic_spaces=["Continuous Prairie Great Room", "Central Hearth Living Room", "Covered Cantilever Terrace", "Open Dining Pavilion", "Ribbon Window Family Wing"],
        roof_type="low_pitch_overhang",
        roof_pitch_deg=14.0,
        eave_overhang_m=0.90,
        wall_finish_type="stucco_terracotta",
        column_type="heavy_stone_piers",
        balcony_railing="solid_parapet_stucco",
        window_style="ribbon_casement",
        has_chimney=True,
        wall_color=PBRColor(0.84, 0.78, 0.70, roughness=0.80), # Warm prairie tan
        accent_wall_color=PBRColor(0.55, 0.30, 0.22, roughness=0.85), # Roman brick banding
        roof_color=PBRColor(0.28, 0.24, 0.22, roughness=0.65), # Earthy tile
        trim_color=PBRColor(0.35, 0.24, 0.16, roughness=0.50), # Dark wood fascia
    ),

    # 10. Modern
    "modern": ArchitecturalStyleConfig(
        style_id="modern",
        display_name="Modern",
        family="Modernist & International",
        aliases=["modern", "ultra modern", "modern house", "modern luxury"],
        description="Clean orthogonal rectilinear masses, floating cantilever slabs, expansive tempered glazing, open social zoning, and flush parapets.",
        layout_archetype="open_concept_pavilion",
        preferred_stair="floating",
        indoor_outdoor_focus="garden_terrace_glass",
        characteristic_spaces=["Double-Height Great Room", "Open Show Island Kitchen", "Seamless Glazed Lounge", "Executive Office", "Master Retreat with Terrace"],
        roof_type="minimalist_flat_cantilever",
        roof_pitch_deg=0.0,
        eave_overhang_m=0.50,
        wall_finish_type="sleek_glass_metal",
        column_type="slender_steel_columns",
        balcony_railing="glass_frameless",
        window_style="floor_to_ceiling_curtain",
        wall_color=PBRColor(0.94, 0.94, 0.94, roughness=0.60), # Pure stucco / alucobond
        accent_wall_color=PBRColor(0.18, 0.20, 0.22, roughness=0.40, metallic=0.3), # Charcoal accent panel
        roof_color=PBRColor(0.14, 0.15, 0.16, roughness=0.45),
        trim_color=PBRColor(0.10, 0.10, 0.10, roughness=0.20, metallic=0.8), # Dark graphite aluminum
    ),

    # 11. Contemporary
    "contemporary": ArchitecturalStyleConfig(
        style_id="contemporary",
        display_name="Contemporary",
        family="Modernist & International",
        aliases=["contemporary", "current contemporary", "contemporary villa"],
        description="Dynamic interplay of organic textures and sleek lines, curved feature walls, integrated eco-courtyards, large porcelain tiles, and warm louvres.",
        layout_archetype="courtyard_centric",
        preferred_stair="curved",
        indoor_outdoor_focus="garden_terrace_glass",
        characteristic_spaces=["Central Light Atrium", "Integrated Living & Dining", "Gourmet Open Kitchen", "Outdoor Patio Deck", "Spa Master Ensuite"],
        roof_type="minimalist_flat_cantilever",
        roof_pitch_deg=0.0,
        eave_overhang_m=0.45,
        wall_finish_type="sleek_glass_metal",
        column_type="slender_steel_columns",
        balcony_railing="glass_frameless",
        window_style="floor_to_ceiling_curtain",
        wall_color=PBRColor(0.91, 0.90, 0.88, roughness=0.65),
        accent_wall_color=PBRColor(0.58, 0.36, 0.18, roughness=0.50), # Warm oak louvres
        roof_color=PBRColor(0.16, 0.17, 0.19, roughness=0.50),
        trim_color=PBRColor(0.12, 0.13, 0.14, roughness=0.25, metallic=0.7),
    ),

    # 12. Craftsman
    "craftsman": ArchitecturalStyleConfig(
        style_id="craftsman",
        display_name="Craftsman",
        family="American Arts & Crafts",
        aliases=["craftsman", "american craftsman", "arts and crafts", "craftsman style"],
        description="Low-pitched gables with wide overhanging eaves, exposed rafter tails, heavy tapered square columns resting on stone piers, and deep welcoming front porch.",
        layout_archetype="deep_veranda_wrap",
        preferred_stair="dogleg",
        indoor_outdoor_focus="wrap_around_porch",
        characteristic_spaces=["Covered Craftsman Porch", "Inglenook Living Room", "Built-In Dining Buffet", "Farmhouse Style Kitchen", "Upper Sloping Eaves Bedrooms"],
        roof_type="low_pitch_overhang",
        roof_pitch_deg=18.0,
        eave_overhang_m=0.85,
        wall_finish_type="cedar_shake_siding",
        column_type="tapered_piers",
        balcony_railing="wood_spindle_baluster",
        window_style="divided_lite_colonial",
        has_chimney=True,
        has_wrap_porch=True,
        wall_color=PBRColor(0.72, 0.68, 0.58, roughness=0.80), # Earthy olive/taupe
        accent_wall_color=PBRColor(0.48, 0.44, 0.40, roughness=0.90), # River stone pier base
        roof_color=PBRColor(0.28, 0.26, 0.24, roughness=0.70), # Cedar shake / architectural shingle
        trim_color=PBRColor(0.22, 0.16, 0.12, roughness=0.60), # Dark bronze / wood trim
        column_color=PBRColor(0.85, 0.82, 0.78, roughness=0.60),
    ),

    # 13. Bungalow
    "bungalow": ArchitecturalStyleConfig(
        style_id="bungalow",
        display_name="Bungalow",
        family="American Arts & Crafts",
        aliases=["bungalow", "california bungalow", "craftsman bungalow", "cozy bungalow"],
        description="Compact single-storey or 1.5-storey layout, broad low-sloping gable roof, wide front veranda, open interior living-dining continuum with built-in millwork.",
        layout_archetype="deep_veranda_wrap",
        preferred_stair="dogleg",
        indoor_outdoor_focus="wrap_around_porch",
        characteristic_spaces=["Wide Front Veranda", "Central Open Living Hall", "Integrated Kitchenette & Dining", "Quiet Rear Bedrooms", "Private Bathroom Wing"],
        roof_type="low_pitch_overhang",
        roof_pitch_deg=16.0,
        eave_overhang_m=0.80,
        wall_finish_type="cedar_shake_siding",
        column_type="tapered_piers",
        balcony_railing="wood_spindle_baluster",
        window_style="divided_lite_colonial",
        has_wrap_porch=True,
        wall_color=PBRColor(0.80, 0.75, 0.68, roughness=0.80),
        accent_wall_color=PBRColor(0.42, 0.38, 0.32, roughness=0.85),
        roof_color=PBRColor(0.24, 0.22, 0.20, roughness=0.65),
        trim_color=PBRColor(0.90, 0.88, 0.82, roughness=0.45),
    ),

    # 14. Cottage
    "cottage": ArchitecturalStyleConfig(
        style_id="cottage",
        display_name="Cottage",
        family="Rustic & Vernacular",
        aliases=["cottage", "english cottage", "country cottage", "cozy cottage"],
        description="Charming intimate scale, steep thatched/shingle roofline, arched doorways, small mullioned paned windows, flower-box planters, and cozy hearth kitchen.",
        layout_archetype="asymmetrical_picturesque",
        preferred_stair="dogleg",
        indoor_outdoor_focus="courtyard_loggia",
        characteristic_spaces=["Arched Vestibule", "Snug Fireplace Parlor", "Country Hearth Kitchen", "Breakfast Nook", "Loft Bedroom under Gables"],
        roof_type="steep_gable_shingle",
        roof_pitch_deg=45.0,
        eave_overhang_m=0.35,
        wall_finish_type="stucco_terracotta",
        column_type="square_timber_posts",
        balcony_railing="wood_spindle_baluster",
        window_style="tall_leaded_diamond",
        has_chimney=True,
        wall_color=PBRColor(0.92, 0.89, 0.82, roughness=0.85), # Warm whitewash
        accent_wall_color=PBRColor(0.55, 0.45, 0.38, roughness=0.90), # Stone base
        roof_color=PBRColor(0.32, 0.28, 0.24, roughness=0.75), # Thatch / weathered shake
        trim_color=PBRColor(0.25, 0.18, 0.12, roughness=0.60),
    ),

    # 15. Ranch
    "ranch": ArchitecturalStyleConfig(
        style_id="ranch",
        display_name="Ranch",
        family="American Arts & Crafts",
        aliases=["ranch", "ranch style", "california ranch", "rambler", "single story ranch"],
        description="Sprawling single-storey horizontal profile, low-pitch gable/hip roof, attached garage, open family living room oriented to rear patio and lawn.",
        layout_archetype="linear_horizontal_flow",
        preferred_stair="linear",
        indoor_outdoor_focus="lanai_patio",
        characteristic_spaces=["Sprawling Family Great Room", "Open Country Kitchen with Bar", "Rear BBQ Patio & Lawn", "Dedicated Bedroom Wing", "Attached Car Porch / Garage"],
        roof_type="low_pitch_overhang",
        roof_pitch_deg=15.0,
        eave_overhang_m=0.60,
        wall_finish_type="board_batten_wood",
        column_type="square_timber_posts",
        balcony_railing="solid_parapet_stucco",
        window_style="ribbon_casement",
        wall_color=PBRColor(0.86, 0.82, 0.76, roughness=0.75),
        accent_wall_color=PBRColor(0.58, 0.35, 0.25, roughness=0.85), # Brick/wood accent
        roof_color=PBRColor(0.26, 0.24, 0.22, roughness=0.65),
        trim_color=PBRColor(0.92, 0.90, 0.85, roughness=0.45),
    ),

    # 16. Mediterranean Revival
    "mediterranean_revival": ArchitecturalStyleConfig(
        style_id="mediterranean_revival",
        display_name="Mediterranean Revival",
        family="Mediterranean / Iberian",
        aliases=["mediterranean revival", "italian renaissance revival", "mediterranean villa", "tuscan revival"],
        description="Stately two-storey villa, low-pitch terracotta tile roof, symmetrical classical archways, decorative wrought iron balconies, central fountain courtyard, and stone loggia.",
        layout_archetype="courtyard_centric",
        preferred_stair="curved",
        indoor_outdoor_focus="courtyard_loggia",
        characteristic_spaces=["Central Fountain Courtyard", "Arched Colonnaded Loggia", "Formal Italian Salon", "Gourmet Terracotta Kitchen", "Master Suite with Arched Balcony"],
        roof_type="terracotta_barrel_tile",
        roof_pitch_deg=18.0,
        eave_overhang_m=0.50,
        wall_finish_type="stucco_terracotta",
        column_type="arched_arcade",
        balcony_railing="wrought_iron_curved",
        window_style="arched_recessed",
        has_arched_loggia=True,
        wall_color=PBRColor(0.92, 0.88, 0.80, roughness=0.80), # Warm Tuscan stucco
        accent_wall_color=PBRColor(0.72, 0.32, 0.18, roughness=0.70), # Terracotta accent
        roof_color=PBRColor(0.74, 0.30, 0.16, roughness=0.60), # S-Tile terracotta barrel
        trim_color=PBRColor(0.18, 0.14, 0.10, roughness=0.40, metallic=0.7), # Wrought iron
        column_color=PBRColor(0.90, 0.86, 0.78, roughness=0.60),
    ),

    # 17. Gothic Revival
    "gothic_revival": ArchitecturalStyleConfig(
        style_id="gothic_revival",
        display_name="Gothic Revival",
        family="English Tudor & Gothic",
        aliases=["gothic revival", "carpenter gothic", "neo-gothic", "victorian gothic"],
        description="Dramatic lancet pointed-arch windows, steep vertical gables, decorative vergeboard/gingerbread trim on eaves, tall clustered chimneys, and stone masonry.",
        layout_archetype="asymmetrical_picturesque",
        preferred_stair="curved",
        indoor_outdoor_focus="front_portico",
        characteristic_spaces=["Lancet Arched Vestibule", "Vaulted Ceiling Great Room", "Gothic Study & Library", "Formal Banquet Dining", "Tower Bedroom Suite"],
        roof_type="steep_timber_gable",
        roof_pitch_deg=52.0,
        eave_overhang_m=0.35,
        wall_finish_type="white_classical_stone",
        column_type="half_timber_frame",
        balcony_railing="wood_spindle_baluster",
        window_style="tall_leaded_diamond",
        has_chimney=True,
        wall_color=PBRColor(0.85, 0.84, 0.80, roughness=0.75), # Weathered stone
        accent_wall_color=PBRColor(0.28, 0.26, 0.25, roughness=0.70),
        roof_color=PBRColor(0.18, 0.19, 0.22, roughness=0.60), # Slate black
        trim_color=PBRColor(0.15, 0.15, 0.16, roughness=0.40),
    ),

    # 18. Art Deco
    "art_deco": ArchitecturalStyleConfig(
        style_id="art_deco",
        display_name="Art Deco",
        family="Modernist & International",
        aliases=["art deco", "streamline moderne", "deco", "zigzag moderne"],
        description="Stepped ziggurat roofline parapets, aerodynamic curved corners, reeded vertical pilasters, bold geometric chevron reliefs, and polished chrome/brass detailing.",
        layout_archetype="open_concept_pavilion",
        preferred_stair="curved",
        indoor_outdoor_focus="garden_terrace_glass",
        characteristic_spaces=["Stepped Entrance Rotunda", "Curved Streamline Salon", "Deco Cocktail Lounge", "Geometric Chef Kitchen", "Upper Terrace Solarium"],
        roof_type="box_parapet_stepped",
        roof_pitch_deg=0.0,
        eave_overhang_m=0.15,
        wall_finish_type="art_deco_carved_stone",
        column_type="slender_steel_columns",
        balcony_railing="perforated_geometric",
        window_style="ribbon_casement",
        wall_color=PBRColor(0.92, 0.91, 0.88, roughness=0.55), # Smooth limestone
        accent_wall_color=PBRColor(0.72, 0.58, 0.32, roughness=0.35, metallic=0.7), # Brass / gold trim
        roof_color=PBRColor(0.20, 0.22, 0.24, roughness=0.50),
        trim_color=PBRColor(0.68, 0.54, 0.28, roughness=0.25, metallic=0.8), # Metallic brass
    ),

    # 19. International Style
    "international_style": ArchitecturalStyleConfig(
        style_id="international_style",
        display_name="International Style",
        family="Modernist & International",
        aliases=["international style", "bauhaus", "miesian", "functionalist"],
        description="Radical functionalism, absolute lack of applied ornament, pure geometric volumes of glass and reinforced concrete, pilotis (ground columns), and ribbon windows.",
        layout_archetype="open_concept_pavilion",
        preferred_stair="linear",
        indoor_outdoor_focus="garden_terrace_glass",
        characteristic_spaces=["Open Plan Living Core", "Cantilevered Floating Slabs", "Curtain Wall Glazed Gallery", "Minimalist Kitchen Cube", "Rooftop Terrace Garden"],
        roof_type="minimalist_flat_cantilever",
        roof_pitch_deg=0.0,
        eave_overhang_m=0.30,
        wall_finish_type="sleek_glass_metal",
        column_type="slender_steel_columns",
        balcony_railing="glass_frameless",
        window_style="floor_to_ceiling_curtain",
        wall_color=PBRColor(0.96, 0.96, 0.96, roughness=0.50), # Crisp white stucco
        accent_wall_color=PBRColor(0.30, 0.32, 0.35, roughness=0.40), # Exposed architectural concrete
        roof_color=PBRColor(0.15, 0.15, 0.16, roughness=0.40),
        trim_color=PBRColor(0.08, 0.08, 0.08, roughness=0.20, metallic=0.9), # Black steel
    ),

    # 20. Farmhouse
    "farmhouse": ArchitecturalStyleConfig(
        style_id="farmhouse",
        display_name="Farmhouse",
        family="Rustic & Vernacular",
        aliases=["farmhouse", "modern farmhouse", "american farmhouse", "country farmhouse"],
        description="Crisp vertical board-and-batten siding, black metal standing-seam gable roof, deep wrap-around front porch with square timber posts, and spacious country kitchen.",
        layout_archetype="deep_veranda_wrap",
        preferred_stair="dogleg",
        indoor_outdoor_focus="wrap_around_porch",
        characteristic_spaces=["Wrap-Around Front Porch", "Country Kitchen & Hearth", "Mudroom / Laundry Utility", "Great Family Living Hall", "Private Master Suite"],
        roof_type="pitched_metal_seam",
        roof_pitch_deg=38.0,
        eave_overhang_m=0.45,
        wall_finish_type="board_batten_wood",
        column_type="square_timber_posts",
        balcony_railing="wood_spindle_baluster",
        window_style="divided_lite_colonial",
        has_chimney=True,
        has_wrap_porch=True,
        wall_color=PBRColor(0.96, 0.96, 0.95, roughness=0.70), # Clean white board-and-batten
        accent_wall_color=PBRColor(0.20, 0.22, 0.24, roughness=0.50), # Charcoal accent
        roof_color=PBRColor(0.12, 0.13, 0.14, roughness=0.35, metallic=0.6), # Black standing-seam metal
        trim_color=PBRColor(0.12, 0.13, 0.14, roughness=0.30),
        column_color=PBRColor(0.55, 0.38, 0.22, roughness=0.75), # Natural cedar posts
    ),

    # 21. Cabin
    "cabin": ArchitecturalStyleConfig(
        style_id="cabin",
        display_name="Cabin",
        family="Rustic & Vernacular",
        aliases=["cabin", "log cabin", "rustic cabin", "timber cabin"],
        description="Heavy natural log/timber construction, river rock masonry fireplace, gabled roof with broad overhangs, covered outdoor deck, and cozy hearth living room.",
        layout_archetype="deep_veranda_wrap",
        preferred_stair="dogleg",
        indoor_outdoor_focus="wrap_around_porch",
        characteristic_spaces=["Covered Timber Porch", "Stone Hearth Great Room", "Open Rustic Kitchen", "Bunk / Loft Sleeping Area", "Ground Master Log Chamber"],
        roof_type="steep_gable_shingle",
        roof_pitch_deg=40.0,
        eave_overhang_m=0.70,
        wall_finish_type="natural_fieldstone_wood",
        column_type="square_timber_posts",
        balcony_railing="wood_spindle_baluster",
        window_style="divided_lite_colonial",
        has_chimney=True,
        wall_color=PBRColor(0.42, 0.28, 0.18, roughness=0.85), # Rich dark log stain
        accent_wall_color=PBRColor(0.48, 0.44, 0.40, roughness=0.90), # River rock
        roof_color=PBRColor(0.22, 0.20, 0.18, roughness=0.70),
        trim_color=PBRColor(0.30, 0.20, 0.12, roughness=0.75),
    ),

    # 22. Chalet
    "chalet": ArchitecturalStyleConfig(
        style_id="chalet",
        display_name="Chalet",
        family="Rustic & Vernacular",
        aliases=["chalet", "swiss chalet", "alpine chalet"],
        description="Alpine-inspired wide-pitched front-facing gable roof with expansive carved wooden eaves, cantilevered upper wooden balconies, stone plinth, and large picture windows.",
        layout_archetype="asymmetrical_picturesque",
        preferred_stair="dogleg",
        indoor_outdoor_focus="wrap_around_porch",
        characteristic_spaces=["Cantilevered Alpine Balcony", "Great Timber Living Hall", "Central Stone Fireplace", "Country Dining Table", "Loft Bedroom under Sloped Roof"],
        roof_type="chalet_gable",
        roof_pitch_deg=25.0,
        eave_overhang_m=1.00,
        wall_finish_type="natural_fieldstone_wood",
        column_type="square_timber_posts",
        balcony_railing="wood_spindle_baluster",
        window_style="divided_lite_colonial",
        has_chimney=True,
        wall_color=PBRColor(0.55, 0.38, 0.24, roughness=0.80), # Honey alpine timber
        accent_wall_color=PBRColor(0.75, 0.72, 0.68, roughness=0.85), # Rough fieldstone base
        roof_color=PBRColor(0.24, 0.22, 0.20, roughness=0.65), # Dark timber shingles
        trim_color=PBRColor(0.38, 0.25, 0.15, roughness=0.70),
    ),

    # 23. Mediterranean
    "mediterranean": ArchitecturalStyleConfig(
        style_id="mediterranean",
        display_name="Mediterranean",
        family="Mediterranean / Iberian",
        aliases=["mediterranean", "spanish mediterranean", "coastal mediterranean"],
        description="Sun-drenched light stucco walls, red clay barrel tile roofs, shaded loggias, wrought iron railings, private central courtyards, and lush garden integration.",
        layout_archetype="courtyard_centric",
        preferred_stair="curved",
        indoor_outdoor_focus="courtyard_loggia",
        characteristic_spaces=["Central Garden Courtyard", "Arched Breezeway Loggia", "Formal Drawing Room", "Open Mediterranean Kitchen", "Balcony Master Suite"],
        roof_type="terracotta_barrel_tile",
        roof_pitch_deg=18.0,
        eave_overhang_m=0.45,
        wall_finish_type="stucco_terracotta",
        column_type="arched_arcade",
        balcony_railing="wrought_iron_curved",
        window_style="arched_recessed",
        has_arched_loggia=True,
        wall_color=PBRColor(0.94, 0.90, 0.84, roughness=0.80), # Cream stucco
        accent_wall_color=PBRColor(0.70, 0.32, 0.18, roughness=0.65), # Terracotta trim
        roof_color=PBRColor(0.75, 0.29, 0.15, roughness=0.60), # S-tile clay roof
        trim_color=PBRColor(0.18, 0.14, 0.10, roughness=0.40, metallic=0.7),
        column_color=PBRColor(0.92, 0.88, 0.82, roughness=0.65),
    ),

    # 24. Spanish Revival
    "spanish_revival": ArchitecturalStyleConfig(
        style_id="spanish_revival",
        display_name="Spanish Revival",
        family="Mediterranean / Iberian",
        aliases=["spanish revival", "spanish", "spanish colonial revival", "mission revival", "spanish contemporary"],
        description="Authentic Spanish colonial silhouette with red barrel tile roof, heavy arched door and window openings, decorative hand-painted ceramic tile accents, and wrought iron grilles.",
        layout_archetype="courtyard_centric",
        preferred_stair="curved",
        indoor_outdoor_focus="courtyard_loggia",
        characteristic_spaces=["Spanish Central Courtyard / Fountain", "Arched Porch Arcade", "Formal Spanish Drawing Salon", "Spanish Gourmet Kitchen with Bar", "Arched Terracotta Balcony"],
        roof_type="terracotta_barrel_tile",
        roof_pitch_deg=18.0,
        eave_overhang_m=0.45,
        wall_finish_type="stucco_terracotta",
        column_type="arched_arcade",
        balcony_railing="wrought_iron_curved",
        window_style="arched_recessed",
        has_arched_loggia=True,
        wall_color=PBRColor(0.93, 0.89, 0.82, roughness=0.82), # Warm stucco
        accent_wall_color=PBRColor(0.72, 0.28, 0.16, roughness=0.65),
        roof_color=PBRColor(0.76, 0.28, 0.14, roughness=0.60), # Authentic red barrel clay
        trim_color=PBRColor(0.16, 0.12, 0.08, roughness=0.35, metallic=0.8), # Dark wrought iron
        column_color=PBRColor(0.91, 0.87, 0.80, roughness=0.70),
    ),

    # 25. Cape Cod
    "cape_cod": ArchitecturalStyleConfig(
        style_id="cape_cod",
        display_name="Cape Cod",
        family="Classical & Colonial",
        aliases=["cape cod", "cape-cod", "traditional cape cod"],
        description="Steep gabled roof, symmetrical 1.5-storey rectangular footprint, central front door, multi-pane double-hung windows, cedar shake siding, and gable dormers.",
        layout_archetype="four_quadrant_box",
        preferred_stair="dogleg",
        indoor_outdoor_focus="front_portico",
        characteristic_spaces=["Central Entrance Vestibule", "Front Parlor Living", "Hearth Kitchen & Dining", "Quiet Master Bedroom", "Upper Dormer Guest Suite"],
        roof_type="steep_gable_shingle",
        roof_pitch_deg=45.0,
        eave_overhang_m=0.20,
        wall_finish_type="cedar_shake_siding",
        column_type="square_timber_posts",
        balcony_railing="wood_spindle_baluster",
        window_style="divided_lite_colonial",
        has_chimney=True,
        has_dormers=True,
        wall_color=PBRColor(0.82, 0.82, 0.80, roughness=0.80), # Weathered cedar gray/white
        accent_wall_color=PBRColor(0.35, 0.45, 0.42, roughness=0.65), # Coastal blue-green shutters
        roof_color=PBRColor(0.24, 0.25, 0.27, roughness=0.65),
        trim_color=PBRColor(0.96, 0.96, 0.96, roughness=0.40),
    ),

    # 26. American Foursquare
    "american_foursquare": ArchitecturalStyleConfig(
        style_id="american_foursquare",
        display_name="American Foursquare",
        family="American Arts & Crafts",
        aliases=["american foursquare", "foursquare", "box house", "prairie box"],
        description="Boxy two-storey efficiency with a four-room quadrant layout on each floor, pyramidal hipped roof with a central front dormer, and wide covered front porch.",
        layout_archetype="four_quadrant_box",
        preferred_stair="dogleg",
        indoor_outdoor_focus="wrap_around_porch",
        characteristic_spaces=["Full-Width Front Porch", "Corner Entrance Foyer", "Living Room Quadrant", "Formal Dining Quadrant", "Corner Kitchen Quadrant"],
        roof_type="classical_hipped",
        roof_pitch_deg=30.0,
        eave_overhang_m=0.60,
        wall_finish_type="board_batten_wood",
        column_type="heavy_stone_piers",
        balcony_railing="solid_parapet_stucco",
        window_style="divided_lite_colonial",
        has_dormers=True,
        has_wrap_porch=True,
        wall_color=PBRColor(0.76, 0.70, 0.62, roughness=0.80),
        accent_wall_color=PBRColor(0.52, 0.30, 0.22, roughness=0.85),
        roof_color=PBRColor(0.25, 0.26, 0.28, roughness=0.65),
        trim_color=PBRColor(0.92, 0.90, 0.86, roughness=0.45),
        column_color=PBRColor(0.82, 0.78, 0.72, roughness=0.70),
    ),

    # 27. Split-Level
    "split_level": ArchitecturalStyleConfig(
        style_id="split_level",
        display_name="Split-Level",
        family="Modernist & International",
        aliases=["split-level", "split level", "tri-level", "staggered level"],
        description="Staggered floor levels connected by short half-flights of stairs, separating formal entertaining, casual family den, and private upper sleeping wings.",
        layout_archetype="split_level_staggered",
        preferred_stair="u_shaped",
        indoor_outdoor_focus="garden_terrace_glass",
        characteristic_spaces=["Mid-Level Foyer & Living", "Upper Level Bedroom Wing", "Lower Level Family Den", "Integrated Kitchen & Dining", "Direct Patio Access"],
        roof_type="low_pitch_overhang",
        roof_pitch_deg=16.0,
        eave_overhang_m=0.60,
        wall_finish_type="board_batten_wood",
        column_type="square_timber_posts",
        balcony_railing="glass_frameless",
        window_style="ribbon_casement",
        wall_color=PBRColor(0.85, 0.83, 0.80, roughness=0.75),
        accent_wall_color=PBRColor(0.50, 0.32, 0.22, roughness=0.80),
        roof_color=PBRColor(0.22, 0.24, 0.26, roughness=0.60),
        trim_color=PBRColor(0.90, 0.88, 0.85, roughness=0.40),
    )
}


class ArchitecturalStyleEngine:
    """
    Parser and classification engine for detecting architectural styles
    and mapping them to design rules and 3D visual parameters.
    """

    @classmethod
    def detect_style(cls, prompt: str) -> ArchitecturalStyleConfig:
        """
        Detects which of the 27 architectural styles is specified in the prompt.
        Defaults to Modern if no explicit style keyword is found.
        """
        p_lower = prompt.lower()

        # Score matching aliases
        best_style: Optional[ArchitecturalStyleConfig] = None
        longest_match_len = 0

        for style_cfg in STYLE_CATALOG.values():
            for alias in style_cfg.aliases:
                if re.search(r'\b' + re.escape(alias) + r'\b', p_lower):
                    if len(alias) > longest_match_len:
                        longest_match_len = len(alias)
                        best_style = style_cfg

        if best_style:
            return best_style

        # Secondary keyword heuristic
        if any(w in p_lower for w in ["spanish", "spinish", "andalusian", "mission"]):
            return STYLE_CATALOG["spanish_revival"]
        if any(w in p_lower for w in ["tudor", "half-timber", "timbering"]):
            return STYLE_CATALOG["tudor_revival"]
        if any(w in p_lower for w in ["georgian", "palladian"]):
            return STYLE_CATALOG["georgian"]
        if any(w in p_lower for w in ["farmhouse", "country kitchen", "board and batten"]):
            return STYLE_CATALOG["farmhouse"]
        if any(w in p_lower for w in ["craftsman", "arts and crafts"]):
            return STYLE_CATALOG["craftsman"]
        if any(w in p_lower for w in ["prairie", "wright", "cantilever eave"]):
            return STYLE_CATALOG["prairie_school"]
        if any(w in p_lower for w in ["mediterranean", "tuscan", "italianate"]):
            return STYLE_CATALOG["mediterranean_revival"]
        if any(w in p_lower for w in ["victorian", "queen anne", "turret"]):
            return STYLE_CATALOG["victorian"]
        if any(w in p_lower for w in ["art deco", "deco", "streamline"]):
            return STYLE_CATALOG["art_deco"]
        if any(w in p_lower for w in ["mid-century", "mid century", "eames", "post and beam"]):
            return STYLE_CATALOG["mid_century_modern"]
        if any(w in p_lower for w in ["colonial", "saltbox"]):
            return STYLE_CATALOG["colonial"]
        if any(w in p_lower for w in ["ranch", "rambler"]):
            return STYLE_CATALOG["ranch"]
        if any(w in p_lower for w in ["chalet", "alpine"]):
            return STYLE_CATALOG["chalet"]
        if any(w in p_lower for w in ["cabin", "log"]):
            return STYLE_CATALOG["cabin"]
        if any(w in p_lower for w in ["cottage", "snug"]):
            return STYLE_CATALOG["cottage"]
        if any(w in p_lower for w in ["bungalow"]):
            return STYLE_CATALOG["bungalow"]
        if any(w in p_lower for w in ["foursquare"]):
            return STYLE_CATALOG["american_foursquare"]
        if any(w in p_lower for w in ["split level", "split-level", "tri-level"]):
            return STYLE_CATALOG["split_level"]
        if any(w in p_lower for w in ["greek revival", "temple portico"]):
            return STYLE_CATALOG["greek_revival"]
        if any(w in p_lower for w in ["french provincial", "chateau"]):
            return STYLE_CATALOG["french_provincial"]
        if any(w in p_lower for w in ["international style", "bauhaus"]):
            return STYLE_CATALOG["international_style"]
        if any(w in p_lower for w in ["contemporary"]):
            return STYLE_CATALOG["contemporary"]

        # Default fallback
        return STYLE_CATALOG["modern"]

    @classmethod
    def get_style_by_id(cls, style_id: str) -> ArchitecturalStyleConfig:
        return STYLE_CATALOG.get(style_id.lower(), STYLE_CATALOG["modern"])

    @classmethod
    def get_all_styles(cls) -> List[ArchitecturalStyleConfig]:
        return list(STYLE_CATALOG.values())
