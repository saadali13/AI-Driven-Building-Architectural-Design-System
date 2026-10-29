"""
Phase 11 / Upgraded: Natural-Language Architectural Requirements Parser.
Extracts rigorous, deterministic architectural programs (rooms, target areas, zoning,
multi-floor levels, hard/soft constraints, and adjacencies) from user design prompts.

Key Principles:
1. Exact Room Count Determinism: Requested count == Generated program nodes.
2. Hard vs. Soft Constraints: User explicit rules are immutable Hard Constraints.
3. Master Suite Attachment: Explicit pairing of Master Bedroom and Master Bathroom.
4. Feasibility Engine: Detects impossible single-storey spatial programs and emits INFEASIBLE_PROGRAM.
"""

import re
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from pydantic import BaseModel, Field


class SpatialTypology(str, Enum):
    TRADITIONAL_SEGREGATED = "TRADITIONAL_SEGREGATED"
    MODERN_OPEN_CONCEPT = "MODERN_OPEN_CONCEPT"
    COURTYARD_CENTRIC = "COURTYARD_CENTRIC"
    MULTI_GENERATIONAL = "MULTI_GENERATIONAL"


class InfeasibleProgramError(ValueError):
    """Raised when an architectural program violates physical scale limits or statutory by-laws (F13)."""
    pass


class RoomRequirement(BaseModel):
    room_id: str
    room_type: str
    room_name: str
    min_area_m2: float
    max_area_m2: float
    requires_exterior_wall: bool = True
    aspect_ratio_range: Tuple[float, float] = (0.5, 2.0)
    level_index: int = 0
    is_master: bool = False
    is_attached_to: Optional[str] = None  # Links attached bath to specific bedroom_id


class AdjacencyRequirement(BaseModel):
    source_room_name: str
    target_room_name: str
    relationship_type: str = "via_door"  # "via_door", "adjacency", "direct"
    is_mandatory: bool = True


class ArchitecturalProgram(BaseModel):
    project_title: str = "Residential House"
    plot_category: str = "5_marla"  # "1_kanal", "10_marla", "7_marla", "5_marla", "3_marla"
    plot_size_desc: Optional[str] = None
    plot_dimensions_ft: Optional[str] = None
    spatial_typology: str = SpatialTypology.MODERN_OPEN_CONCEPT.value
    layout_style: str = SpatialTypology.MODERN_OPEN_CONCEPT.value
    stair_type: str = "dogleg"
    stair_engine_class: str = "DoglegStaircase"
    max_ground_coverage_m2: float = 75.0
    total_target_area_m2: float = 100.0
    floor_count: int = 1
    levels: List[int] = Field(default_factory=lambda: [0])
    is_single_storey_explicit: bool = False
    is_feasible: bool = True
    feasibility_status: str = "FEASIBLE"  # "FEASIBLE" | "INFEASIBLE_PROGRAM"
    infeasibility_reason: Optional[str] = None
    infeasibility_reasons: List[str] = Field(default_factory=list)
    requested_room_counts: Dict[str, int] = Field(default_factory=dict)
    ground_room_counts: Dict[str, int] = Field(default_factory=dict)
    show_kitchen_count: int = 1
    dirty_kitchen_count: int = 0
    car_porch_capacity: int = 1
    has_landlocked_bedrooms: bool = False
    has_separate_formal_dining: bool = False
    total_ground_footprint_m2: float = 0.0
    rooms: List[RoomRequirement] = Field(default_factory=list)
    adjacencies: List[AdjacencyRequirement] = Field(default_factory=list)
    hard_constraints: List[str] = Field(default_factory=list)
    soft_constraints: List[str] = Field(default_factory=list)
    raw_prompt: str = ""
    statutory_red_note: Optional[str] = None
    has_servant_quarter: bool = False
    warnings: List[str] = Field(default_factory=list)



def validate_architectural_feasibility(program: ArchitecturalProgram, raise_on_error: bool = True) -> Tuple[bool, List[str]]:
    """
    Hard architectural rules engine validating physical and statutory program feasibility (F13).
    """
    reasons = []
    cat = program.plot_category
    gf_counts = program.ground_room_counts
    beds = program.requested_room_counts.get("bedroom", 0)
    floors = program.floor_count
    p_lower = (program.raw_prompt or "").lower()

    # 0. Multi-Floor Capacity Logic
    if cat == "3_marla":
        if floors <= 2:
            if beds >= 4:
                reasons.append(
                    f"F13 Infeasible: A 2-storey 3 Marla plot cannot fit {beds} bedrooms without violating "
                    f"IBC Section 1207 minimum room sizes (70 sq ft). You must specify 3 floors (G+2) or reduce bedroom count."
                )
        elif floors == 3:
            if beds > 5:
                reasons.append(
                    f"F13 Infeasible: A 3-storey (G+2) 3 Marla plot allows maximum 5 bedrooms (1 on Ground, 2 on Level 1, 2 on Level 2). Requested: {beds}."
                )

    elif cat == "5_marla":
        # Check for 2 full kitchens on Ground Floor
        if "2 full kitchen" in p_lower or ("2 kitchen" in p_lower and "ground" in p_lower) or program.ground_room_counts.get("kitchen", 0) > 1:
            reasons.append("F13 Infeasible: 5 Marla cannot accommodate 2 full kitchens on Ground Floor.")
        if floors <= 2:
            # Max 4 beds, or 5 beds ONLY if formal Drawing Room is converted into Ground Bed 1
            has_formal_drawing = program.ground_room_counts.get("drawing", 0) > 0 and not any(k in p_lower for k in ["convert drawing", "no drawing", "drawing as bed", "drawing converted"])
            if beds > 5:
                reasons.append(f"F13 Infeasible: A 2-storey 5 Marla plot cannot fit {beds} bedrooms. Maximum 5 bedrooms allowed with drawing conversion, or specify 3 floors (G+2).")
            elif beds == 5 and has_formal_drawing:
                reasons.append("F13 Infeasible: 5 bedrooms on a 2-storey 5 Marla plot is only possible if the formal Drawing Room is converted into Ground Bed 1.")
        elif floors == 3:
            if beds > 7:
                reasons.append(f"F13 Infeasible: A 3-storey (G+2) 5 Marla plot allows up to 6-7 bedrooms. Requested: {beds}.")

    elif cat == "7_marla":
        if floors <= 2:
            if beds > 5:
                # Statutory Compliance Guard: Auto-adapt to legal limit (5 beds) and generate prominent red notice
                program.statutory_red_note = (
                    f"6 Bedrooms on 2 Floors is physically & legally IMPOSSIBLE in 7 Marla (30'x55') under CDA/DHA Regulations "
                    f"(Mandatory Setbacks & min 120 sq ft room rules). Auto-adapted to maximum legal capacity of 5 Master Suites. "
                    f"To construct 6 or more bedrooms, a 3-Storey Triplex (G+2) is required."
                )
                program.requested_room_counts["bedroom"] = 5
                if program.ground_room_counts.get("bedroom", 0) > 2:
                    program.ground_room_counts["bedroom"] = 2
                if program.requested_room_counts.get("bathroom", 0) > 5:
                    program.requested_room_counts["bathroom"] = 5
        elif floors == 3:
            if beds > 7:
                reasons.append(f"F13 Infeasible: A 3-storey (G+2) 7 Marla plot allows up to 7 bedrooms. Requested: {beds}.")

    elif cat == "10_marla":
        if floors <= 2:
            if beds > 6:
                reasons.append(
                    f"F13 Infeasible: A 2-storey (G+1) 10 Marla plot allows a maximum of 6 bedrooms "
                    f"(2 on Ground Floor, 4 on First Floor) under CDA/DHA building bylaws (mandating minimum bedroom size 100 sq ft, "
                    f"master bedroom 120 sq ft, and 10ft front / 5ft rear setbacks). Requested {beds} bedrooms is physically and legally infeasible. "
                    f"Please reduce bedroom count or specify 3 floors (G+2)."
                )
        elif floors == 3:
            if beds > 9:
                reasons.append(f"F13 Infeasible: A 3-storey (G+2) 10 Marla plot allows up to 9 bedrooms. Requested: {beds}.")

    elif cat == "1_kanal":
        if floors <= 2:
            if beds > 8:
                reasons.append(
                    f"F13 Infeasible: A 2-storey (G+1) 1 Kanal plot allows a maximum of 8 bedrooms "
                    f"(3 on Ground Floor, 5 on First Floor) under CDA/DHA building regulations (15ft front lawn, 8ft rear setback). "
                    f"Requested {beds} bedrooms exceeds allowable capacity. Please reduce bedroom count or specify 3 floors (G+2)."
                )
        elif floors == 3:
            if beds > 12:
                reasons.append(f"F13 Infeasible: A 3-storey (G+2) 1 Kanal plot allows up to 12 bedrooms. Requested: {beds}.")

    # Enforce mandatory front lawn setbacks across all Pakistani residential scales
    setback_map = {"5_marla": 5, "7_marla": 6, "10_marla": 10, "1_kanal": 15}
    if cat in setback_map:
        setback_ft = setback_map[cat]
        if any(term in p_lower for term in [
            "100% covered", "100 percent covered", "cover 100%", "zero setback", "no setback",
            "no lawn", "cover entire plot", "zero lawn", "without lawn", "without setback", "no front lawn"
        ]):
            reasons.append(
                f"F13 Infeasible: Building bylaws mandate minimum front lawn setbacks ({setback_ft}' for {cat.replace('_', ' ').title()}). "
                f"100% covered footprint requests violate municipal regulations."
            )

    # Dirty Kitchen isolation rule
    has_dirty_req = any(k in p_lower for k in ["dirty kitchen", "dirty-kitchen", "wet kitchen", "grease kitchen", "spice kitchen", "scullery"])
    if has_dirty_req:
        if any(k in p_lower for k in ["dirty kitchen to drawing", "dirty kitchen into drawing", "dirty kitchen door to drawing", "connect dirty kitchen to drawing"]):
            reasons.append(
                "F13 Infeasible: Architectural building regulations strictly forbid connecting a dirty/wet kitchen to a formal drawing room or front public foyer. "
                "A dirty kitchen must connect exclusively to the rear/backside of the main show kitchen."
            )

    # 1. Scale-Based Room Limits (Ground Floor):
    if cat == "3_marla":
        if gf_counts.get("bedroom", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 3 Marla permits maximum 1 bedroom on Ground Floor (requested {gf_counts.get('bedroom')}).")
        if gf_counts.get("lounge", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 3 Marla permits maximum 1 TV lounge on Ground Floor (requested {gf_counts.get('lounge')}).")
        if program.show_kitchen_count > 1 or gf_counts.get("kitchen", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 3 Marla permits maximum 1 kitchen (requested {program.show_kitchen_count}).")
        if program.car_porch_capacity > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 3 Marla permits maximum 1 car porch (requested {program.car_porch_capacity}).")
        if program.has_separate_formal_dining:
            reasons.append("F13: Program Infeasible - 3 Marla cannot accommodate a separate formal dining room.")

    elif cat == "5_marla":
        if gf_counts.get("bedroom", 0) > 3 or (gf_counts.get("bedroom", 0) == 3 and (gf_counts.get("bathroom", 0) > 2 or "on ground floor" in p_lower or not program.is_single_storey_explicit)):
            reasons.append(f"F13: Scale-Based Limit Exceeded - 5 Marla permits maximum 2 bedrooms on Ground Floor (requested {gf_counts.get('bedroom')}).")
        if gf_counts.get("lounge", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 5 Marla permits maximum 1 TV lounge on Ground Floor (requested {gf_counts.get('lounge')}).")
        if program.show_kitchen_count > 1 and "5 Marla cannot accommodate" not in " ".join(reasons):
            reasons.append(f"F13: Scale-Based Limit Exceeded - 5 Marla permits maximum 1 show kitchen (requested {program.show_kitchen_count}).")
        if gf_counts.get("drawing", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 5 Marla permits maximum 1 drawing room (requested {gf_counts.get('drawing')}).")
        if program.car_porch_capacity > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 5 Marla permits maximum 1 car porch (requested {program.car_porch_capacity}).")

    elif cat == "7_marla":
        if gf_counts.get("bedroom", 0) > 2:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 7 Marla permits maximum 2 bedrooms on Ground Floor (requested {gf_counts.get('bedroom')}).")
        if gf_counts.get("lounge", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 7 Marla permits maximum 1 TV lounge on Ground Floor (requested {gf_counts.get('lounge')}).")
        if program.show_kitchen_count > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 7 Marla permits maximum 1 show kitchen (requested {program.show_kitchen_count}).")
        if gf_counts.get("drawing", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 7 Marla permits maximum 1 drawing room (requested {gf_counts.get('drawing')}).")
        if gf_counts.get("dining", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 7 Marla permits maximum 1 dining room (requested {gf_counts.get('dining')}).")

    elif cat == "10_marla":
        if gf_counts.get("bedroom", 0) > 2:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 10 Marla permits maximum 2 bedrooms on Ground Floor (requested {gf_counts.get('bedroom')}).")
        if gf_counts.get("lounge", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 10 Marla permits maximum 1 TV lounge on Ground Floor (requested {gf_counts.get('lounge')}).")
        if program.show_kitchen_count > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 10 Marla permits maximum 1 show kitchen (requested {program.show_kitchen_count}).")
        if gf_counts.get("drawing", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 10 Marla permits maximum 1 drawing room (requested {gf_counts.get('drawing')}).")
        if gf_counts.get("dining", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 10 Marla permits maximum 1 dining room (requested {gf_counts.get('dining')}).")
        if program.car_porch_capacity > 2:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 10 Marla permits maximum 2 car porch capacity (requested {program.car_porch_capacity}).")

    elif cat == "1_kanal":
        if gf_counts.get("bedroom", 0) > 3:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 1 Kanal permits maximum 3 bedrooms on Ground Floor (requested {gf_counts.get('bedroom')}).")
        if gf_counts.get("lounge", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 1 Kanal permits maximum 1 TV lounge on Ground Floor (requested {gf_counts.get('lounge')}).")
        if program.show_kitchen_count > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 1 Kanal permits maximum 1 show kitchen (requested {program.show_kitchen_count}).")
        if gf_counts.get("drawing", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 1 Kanal permits maximum 1 drawing room (requested {gf_counts.get('drawing')}).")
        if gf_counts.get("dining", 0) > 1:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 1 Kanal permits maximum 1 dining room (requested {gf_counts.get('dining')}).")
        if program.car_porch_capacity > 3:
            reasons.append(f"F13: Scale-Based Limit Exceeded - 1 Kanal permits maximum 3 car porch capacity (requested {program.car_porch_capacity}).")

    # 2. Universal Invalid Combinations:
    if program.show_kitchen_count > 1 and not any("show kitchen" in r for r in reasons):
        reasons.append(f"F13: Invalid Combination - Multiple main/show kitchens ({program.show_kitchen_count}) requested on the same floor plate.")

    if gf_counts.get("lounge", 0) > 1 and not any("TV lounge" in r for r in reasons):
        reasons.append(f"F13: Invalid Combination - Multiple TV lounges ({gf_counts.get('lounge')}) requested on the same Ground Floor.")

    if program.has_landlocked_bedrooms:
        reasons.append("F13: Invalid Combination - Landlocked habitable bedrooms without exterior setback or OTS access violate building codes.")

    if program.total_ground_footprint_m2 > program.max_ground_coverage_m2:
        reasons.append(
            f"F13: Maximum Covered Area Exceeded - Requested ground footprint ({program.total_ground_footprint_m2:.1f} m²) "
            f"exceeds statutory 75% plot limit ({program.max_ground_coverage_m2:.1f} m²)."
        )

    is_valid = len(reasons) == 0
    if not is_valid:
        program.is_feasible = False
        program.feasibility_status = "INFEASIBLE_PROGRAM"
        program.infeasibility_reasons = reasons
        program.infeasibility_reason = "; ".join(reasons)
        if raise_on_error:
            raise InfeasibleProgramError("; ".join(reasons))

    return is_valid, reasons


class NaturalLanguageRequirementsParser:
    """
    Parses user design prompts into an immutable, mathematically verifiable ArchitecturalProgram.
    """

    PLOT_PROFILES = {
        "1_kanal": {
            "plot_name": "1 Kanal",
            "dim_ft": "50' x 90'",
            "gross_sqft": 4500,
            "max_coverage_m2": 250.0,
            "standard_floors": 2,
            "setbacks": {"front": 17.0, "rear": 5.0, "sides": 5.0}
        },
        "10_marla": {
            "plot_name": "10 Marla",
            "dim_ft": "35' x 65'",
            "gross_sqft": 2275,
            "max_coverage_m2": 145.0,
            "standard_floors": 2,
            "setbacks": {"front": 8.0, "rear": 4.5, "sides": 3.0}
        },
        "7_marla": {
            "plot_name": "7 Marla",
            "dim_ft": "30' x 55'",
            "gross_sqft": 1650,
            "max_coverage_m2": 110.0,
            "standard_floors": 2,
            "setbacks": {"front": 6.0, "rear": 4.0, "sides": 3.0}
        },
        "5_marla": {
            "plot_name": "5 Marla",
            "dim_ft": "25' x 45'",
            "gross_sqft": 1125,
            "max_coverage_m2": 76.0,
            "standard_floors": 2,
            "setbacks": {"front": 4.0, "rear": 3.5, "sides": 0.0}
        },
        "3_marla": {
            "plot_name": "3 Marla",
            "dim_ft": "20' x 35'",
            "gross_sqft": 700,
            "max_coverage_m2": 48.0,
            "standard_floors": 2,
            "setbacks": {"front": 0.0, "rear": 2.5, "sides": 0.0}
        }
    }

    @classmethod
    def parse(cls, prompt: str, validate: bool = True, raise_on_error: bool = False) -> ArchitecturalProgram:
        p_lower = prompt.lower()
        hard_constraints = []
        soft_constraints = []

        # 1. Detect Category
        explicit_category = None
        if "1 kanal" in p_lower or "one kanal" in p_lower or "kanal" in p_lower:
            explicit_category = "1_kanal"
        elif "10 marla" in p_lower or "ten marla" in p_lower:
            explicit_category = "10_marla"
        elif "7 marla" in p_lower or "seven marla" in p_lower:
            explicit_category = "7_marla"
        elif "5 marla" in p_lower or "five marla" in p_lower:
            explicit_category = "5_marla"
        elif "3 marla" in p_lower or "three marla" in p_lower or "3m" in p_lower:
            explicit_category = "3_marla"

        category = explicit_category or "5_marla"
        profile = cls.PLOT_PROFILES[category]
        hard_constraints.append(f"Plot Category: {profile['plot_name']} ({profile['dim_ft']})")

        # 1b. Detect Spatial Typology Tag
        if any(k in p_lower for k in ["multi-generational", "multigenerational", "dual master", "rental", "independent external stair", "side external", "two family"]):
            spatial_typology = SpatialTypology.MULTI_GENERATIONAL.value
        elif any(k in p_lower for k in ["courtyard", "courtyard-centric", "ots patio", "internal green", "daylight core"]):
            spatial_typology = SpatialTypology.COURTYARD_CENTRIC.value
        elif any(k in p_lower for k in ["traditional", "segregated", "closed kitchen", "formal drawing dining", "separate lawn", "isolated formal"]):
            spatial_typology = SpatialTypology.TRADITIONAL_SEGREGATED.value
        elif any(k in p_lower for k in ["modern", "open kitchen", "open-plan", "open plan", "open concept", "executive", "island counter", "glazed patio"]):
            spatial_typology = SpatialTypology.MODERN_OPEN_CONCEPT.value
        else:
            spatial_typology = SpatialTypology.MODERN_OPEN_CONCEPT.value
        hard_constraints.append(f"Spatial Typology: {spatial_typology}")

        # 1c. Vertical Circulation Mapping
        if any(k in p_lower for k in ["bifurcated", "grand stair", "split flight", "split stair"]):
            stair_type = "bifurcated"
            stair_engine_class = "SplitFlightGrandStaircase"
        elif any(k in p_lower for k in ["curved", "rotunda", "spiral", "helical", "circular"]):
            stair_type = "spiral" if "spiral" in p_lower else "curved"
            stair_engine_class = "CurvedOrCircularStaircase"
        elif any(k in p_lower for k in ["straight", "linear", "side stair", "side staircase"]):
            stair_type = "straight"
            stair_engine_class = "LinearFlightStaircase"
        elif any(k in p_lower for k in ["side external", "external stair", "rental stair", "independent stair"]):
            stair_type = "side_external"
            stair_engine_class = "BoundaryPassageStaircase"
        elif any(k in p_lower for k in ["dogleg", "dog-leg", "u-shaped", "u_shaped", "u shape", "switchback"]):
            stair_type = "u_shaped" if ("u-shaped" in p_lower or "u_shaped" in p_lower or "u shape" in p_lower) else "dogleg"
            stair_engine_class = "DoglegStaircase"
        elif "winder" in p_lower:
            stair_type = "winder"
            stair_engine_class = "DoglegStaircase"
        elif "floating" in p_lower:
            stair_type = "floating"
            stair_engine_class = "LinearFlightStaircase"
        elif "ladder" in p_lower:
            stair_type = "ladder"
            stair_engine_class = "LinearFlightStaircase"
        else:
            stair_type = "dogleg"
            stair_engine_class = "DoglegStaircase"

        # 2. Detect Storey Mandates
        has_single_floor_phrase = any(term in p_lower for term in [
            "single storey", "single-storey", "single floor", "single-floor", "single story", "single-story",
            "1 storey", "one storey", "1-storey", "1 story", "one story", "1-story", "1 floor", "one floor", "ground floor only"
        ])
        is_multi_storey_explicit = any(term in p_lower for term in [
            "2 floor", "2 storey", "two floor", "two storey", "2 story", "two story", "2-story", "two-story", "duplex",
            "double storey", "double-storey", "double story", "double-story", "first floor", "2 floors", "two floors", "2-floor",
            "3 floor", "3 storey", "3 story", "3-story", "three floor", "three storey", "three story", "g+2", "triple storey", "triple story",
            "g+1", "g + 1", "multi-storey", "multi storey"
        ])


        # 3. Detect Requested Room Counts
        # Check explicit Ground Floor Bedrooms
        gf_bed_match = re.search(r'(\d+|one|two|three|four)\s*(?:beds?|bedrooms?)\s*(?:on|in)\s*(?:gf|ground\s*floor|ground)', p_lower)
        if not gf_bed_match:
            gf_bed_match = re.search(r'(?:on|in)?\s*(?:gf|ground\s*floor|ground)\s*(?:with|has|having|have)?\s*(\d+|one|two|three|four)\s*(?:beds?|bedrooms?)', p_lower)

        # Check explicit Upper Floor Bedrooms (First Floor, Second Floor, Upper Floor)
        uf_bed_match = re.search(r'(\d+|one|two|three|four|five|six)\s*(?:beds?|bedrooms?)\s*(?:on|in)\s*(?:ff|first\s*floor|second\s*floor|upper\s*floor|upper|2nd\s*floor|1st\s*floor)', p_lower)
        if not uf_bed_match:
            uf_bed_match = re.search(r'(?:on|in)?\s*(?:ff|first\s*floor|second\s*floor|upper\s*floor|upper|2nd\s*floor|1st\s*floor)\s*(?:with|has|having|have)?\s*(\d+|one|two|three|four|five|six)\s*(?:beds?|bedrooms?)', p_lower)

        num_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}

        if gf_bed_match and uf_bed_match:
            gf_val = num_map.get(gf_bed_match.group(1), int(gf_bed_match.group(1)) if gf_bed_match.group(1).isdigit() else 2)
            uf_val = num_map.get(uf_bed_match.group(1), int(uf_bed_match.group(1)) if uf_bed_match.group(1).isdigit() else 2)
            gf_bed_count = gf_val
            bedroom_count = gf_val + uf_val
        elif gf_bed_match:
            val = gf_bed_match.group(1)
            gf_bed_count = num_map.get(val, int(val) if val.isdigit() else 1)
            bed_match = re.search(r'(\d+)\s*[-]?\s*(?:luxury\s+|master\s+|executive\s+)*(?:bhk|bed|bedroom|suite|br)s?', p_lower)
            if bed_match:
                bedroom_count = int(bed_match.group(1))
            else:
                bedroom_count = gf_bed_count
            if ("stair" in p_lower or is_multi_storey_explicit) and bedroom_count <= gf_bed_count:
                bedroom_count = max(bedroom_count, gf_bed_count + 1)
            else:
                bedroom_count = max(bedroom_count, gf_bed_count)
        else:
            bedroom_count = 3
            bed_match = re.search(r'(\d+)\s*[-]?\s*(?:luxury\s+|master\s+|executive\s+)*(?:bhk|bed|bedroom|suite|br)s?', p_lower)
            if bed_match:
                bedroom_count = int(bed_match.group(1))
            elif "one bed" in p_lower or "1 bed" in p_lower or "1 master" in p_lower or "one master" in p_lower:
                bedroom_count = 1
            elif "two bed" in p_lower or "2 bed" in p_lower or "two suite" in p_lower:
                bedroom_count = 2
            elif "three bed" in p_lower or "3 bed" in p_lower or "three suite" in p_lower:
                bedroom_count = 3
            elif "four bed" in p_lower or "4 bed" in p_lower or "four suite" in p_lower:
                bedroom_count = 4
            elif "five bed" in p_lower or "5 bed" in p_lower or "five suite" in p_lower:
                bedroom_count = 5
            elif "six bed" in p_lower or "6 bed" in p_lower:
                bedroom_count = 6
            else:
                word_bed = re.search(r'\b(one|two|three|four|five|six|seven|eight)\s*[-]?\s*(?:luxury\s+|master\s+|executive\s+)*(?:bhk|bed|bedroom|suite|br)s?\b', p_lower)
                if word_bed:
                    bedroom_count = num_map.get(word_bed.group(1), 3)

            is_one_bed_program = (bedroom_count == 1 and not is_multi_storey_explicit and "stair" not in p_lower)
            is_single_storey_explicit = (has_single_floor_phrase or is_one_bed_program) and not is_multi_storey_explicit
            if is_single_storey_explicit:
                gf_bed_count = bedroom_count
            else:
                # Rigorous Programmatic Floor-Distribution Matrix for G+1:
                if category == "3_marla":
                    gf_bed_count = 1 if bedroom_count >= 2 else (1 if bedroom_count == 1 else 0)
                elif category in ["5_marla", "7_marla"]:
                    if bedroom_count <= 3:
                        gf_bed_count = 1
                    elif bedroom_count == 4:
                        gf_bed_count = 2 if (category == "7_marla" and any(k in p_lower for k in ["dual rear", "dual suite", "2 bed on ground", "two suite"])) else 1
                    else:
                        gf_bed_count = 2
                elif category in ["10_marla", "1_kanal"]:
                    if bedroom_count <= 3:
                        gf_bed_count = 1
                    else:
                        gf_bed_count = 2
                else:
                    gf_bed_count = 1

        is_one_bed_program = (bedroom_count == 1 and not is_multi_storey_explicit and "stair" not in p_lower)
        is_single_storey_explicit = (has_single_floor_phrase or is_one_bed_program) and not is_multi_storey_explicit

        # Infer category if not explicitly stated in prompt
        if not explicit_category:
            if bedroom_count >= 5 or (gf_bed_count >= 2 and any(k in p_lower for k in ["dirty kitchen", "dining", "mansion", "banquet", "triple car", "triple porch", "stairs is placed in living", "stairs in living"])) or ("dirty kitchen" in p_lower and "dining" in p_lower and bedroom_count >= 5):
                category = "1_kanal"
            elif bedroom_count == 4 or ("dirty kitchen" in p_lower and "dining" in p_lower):
                category = "10_marla"
            elif bedroom_count == 3:
                category = "5_marla"
            else:
                category = "5_marla"
            profile = cls.PLOT_PROFILES[category]
            hard_constraints[0] = f"Plot Category: {profile['plot_name']} ({profile['dim_ft']})"

        hard_constraints.append(f"Exact Bedroom Count: {bedroom_count} (GF: {gf_bed_count})")

        # Attached bathrooms
        has_all_attached = any(term in p_lower for term in [
            "attach bathroom in each", "attached bathroom in each", "each bedroom and attach",
            "attach bathroom in every", "all attached", "each attached", "en-suite"
        ])
        has_master_attached = "master" in p_lower and "attach" in p_lower or bedroom_count >= 1

        # Bathrooms count
        bath_count = bedroom_count if has_all_attached else max(1, bedroom_count - 1)
        bath_match = re.search(r'(\d+)\s*(?:bath|bathroom|washroom|toilet)', p_lower)
        if bath_match:
            bath_count = int(bath_match.group(1))

        # Powder room
        has_powder = "powder" in p_lower or "guest bath" in p_lower or "half bath" in p_lower
        if has_powder:
            bath_count = max(bath_count, bedroom_count + 1 if has_all_attached else bath_count)

        # Kitchens: Show vs Dirty
        has_dirty_kitchen = any(k in p_lower for k in [
            "dirty kitchen", "dirty-kitchen", "grease kitchen", "spice kitchen", "wet kitchen", "service kitchen"
        ])
        dirty_kitchen_count = 1 if has_dirty_kitchen else 0

        k_match = re.search(r'(\d+|one|two|three)\s*(?:full\s*kitchens?|main\s*kitchens?|show\s*kitchens?|kitchens?)', p_lower)
        if k_match:
            val = k_match.group(1)
            num_map = {"one": 1, "two": 2, "three": 3}
            show_kitchen_count = num_map.get(val, int(val) if val.isdigit() else 1)
        else:
            show_kitchen_count = 1 if ("kitchen" in p_lower or "cooking" in p_lower or "bawarchi khana" in p_lower) else 0

        # TV Lounge / Family Lounge count on GF
        l_match = re.search(r'(\d+|one|two|three)\s*(?:tv\s*lounges?|family\s*lounges?|lounges?)', p_lower)
        if l_match:
            val = l_match.group(1)
            num_map = {"one": 1, "two": 2, "three": 3}
            lounge_count = num_map.get(val, int(val) if val.isdigit() else 1)
        else:
            lounge_count = 1 if ("tv lounge" in p_lower or "lounge" in p_lower) else 0

        # Functional Spaces
        # Support both English drawing tokens and Urdu baithak
        has_living = any(k in p_lower for k in ["drawing", "formal living", "salon", "formal sitting", "reception salon", "formal guest", "drawing room", "baithak"])
        # On 3 Marla G+1, Ground Floor has open living lounge and compact bedroom suite, never a separate formal drawing room
        if category == "3_marla" and not is_single_storey_explicit:
            has_living = False
            lounge_count = max(1, lounge_count)

        has_dining = "dining" in p_lower
        has_separate_formal_dining = any(term in p_lower for term in [
            "formal dining", "separate dining", "dedicated dining", "dining room"
        ]) or ("dining" in p_lower and "breakfast" not in p_lower and category == "3_marla")
        has_garage = "garage" in p_lower or "garge" in p_lower or "car porch" in p_lower or "porch" in p_lower or "gari porch" in p_lower
        has_stairs = any(k in p_lower for k in ["stairs", "staircase", "stair", "rotunda", "dogleg", "winder", "spiral", "linear flight", "curved flight", "u-shaped"])
        if has_stairs:
            hard_constraints.append(f"Vertical Circulation: {stair_engine_class} ({stair_type})")

        # Servant Quarter Detection & Warning Logic
        has_servant = any(k in p_lower for k in ["servant quarter", "servant", "maid's room", "maid room", "maid", "servant room"])
        warnings: List[str] = []
        if has_servant:
            if category in ["3_marla", "5_marla", "7_marla"]:
                warnings.append(f"Statutory Warning: {profile['plot_name']} plot footprint cannot legally accommodate a separate servant quarter under municipal setback bylaws.")
            else:
                hard_constraints.append("Dedicated Servant Quarter with Independent Egress")


        # Car Porch Capacity
        c_match = re.search(r'(\d+|one|two|three)\s*(?:cars?|car\s*porch|car\s*garage)', p_lower)
        if c_match:
            val = c_match.group(1)
            num_map = {"one": 1, "two": 2, "three": 3}
            car_porch_capacity = num_map.get(val, int(val) if val.isdigit() else 1)
        elif "double car" in p_lower or "2 car" in p_lower:
            car_porch_capacity = 2
        elif "3 car" in p_lower or "three car" in p_lower:
            car_porch_capacity = 3
        else:
            car_porch_capacity = 2 if category in ["10_marla", "1_kanal"] else 1

        has_landlocked = any(term in p_lower for term in [
            "landlocked", "without window", "no window", "no exterior wall", "without ots", "no ventilation"
        ])

        has_kitchen = (show_kitchen_count > 0 or dirty_kitchen_count > 0)
        has_tv_lounge = (lounge_count > 0)

        requested_counts = {
            "bedroom": bedroom_count,
            "bathroom": bath_count,
            "living_room": 1 if has_living else 0,
            "tv_lounge": lounge_count,
            "dining_room": 1 if has_dining else 0,
            "kitchen": show_kitchen_count + dirty_kitchen_count,
            "garage": 1 if has_garage else 0,
            "powder_room": 1 if has_powder else 0,
            "stairs": 1 if has_stairs else 0
        }

        ground_room_counts = {
            "bedroom": gf_bed_count,
            "bathroom": min(bath_count, gf_bed_count + (1 if has_powder else 0)),
            "drawing": 0 if (category in ["3_marla", "5_marla"] and (category == "3_marla" or bedroom_count >= 5)) else (1 if has_living else 0),
            "lounge": lounge_count,
            "kitchen": show_kitchen_count,
            "dirty_kitchen": dirty_kitchen_count,
            "dining": 1 if has_dining else 0,
            "garage": 1 if has_garage else 0
        }

        # 4. Feasibility Analysis & Area Calculation (Balancing small plots to statutory limits)
        if category == "3_marla":
            min_bed_area = 10.5
            min_bath_area = 3.2
            min_powder_area = 2.0
            min_living_area = 0.0 if (not is_single_storey_explicit and gf_bed_count > 0) else 12.0
            min_lounge_area = 11.0
            min_dining_area = 0.0
            min_kitchen_area = 4.5
            min_garage_area = 10.0
            min_stairs_area = 4.0
            coverage_multiplier = 1.05
        else:
            min_bed_area = 11.5
            min_bath_area = 3.5
            min_powder_area = 2.0
            min_living_area = 14.0
            min_lounge_area = 11.0
            min_dining_area = 7.0
            min_kitchen_area = 7.0
            min_garage_area = 13.0
            min_stairs_area = 4.5
            coverage_multiplier = 1.15

        total_min_net_area = (
            bedroom_count * min_bed_area +
            (bath_count - (1 if has_powder else 0)) * min_bath_area +
            (min_powder_area if has_powder else 0.0) +
            (min_living_area if has_living else 0.0) +
            (min_lounge_area if lounge_count > 0 else 0.0) +
            (min_dining_area if has_dining else 0.0) +
            (min_kitchen_area if show_kitchen_count > 0 else 0.0) +
            (min_garage_area if has_garage else 0.0) +
            (min_stairs_area if has_stairs else 0.0)
        )
        total_min_gross_footprint = total_min_net_area * coverage_multiplier

        total_ground_footprint_m2 = (
            gf_bed_count * min_bed_area +
            min(bath_count, gf_bed_count) * min_bath_area +
            (min_powder_area if has_powder else 0.0) +
            (min_living_area if has_living and (category != "3_marla" or gf_bed_count == 0) else 0.0) +
            (lounge_count * min_lounge_area) +
            (min_dining_area if has_dining else 0.0) +
            (show_kitchen_count * min_kitchen_area) +
            (dirty_kitchen_count * 5.0) +
            (min_garage_area if has_garage else 0.0) +
            (min_stairs_area if has_stairs else 0.0)
        ) * coverage_multiplier

        max_allowable_ground = profile["max_coverage_m2"]

        is_three_storey = any(term in p_lower for term in [
            "3 floor", "3 storey", "3 story", "3-story", "three floor", "three storey", "three story",
            "g+2", "g + 2", "triple storey", "triple story", "3-storey", "3-floor", "3 floors", "three floors", "third floor",
            "roof top", "roof-top", "rooftop", "roof plan", "penthouse", "triplex"
        ]) or (bedroom_count >= 6 and category in ["3_marla", "5_marla", "7_marla"])
        if is_three_storey:
            floor_count = 3
            levels = [0, 1, 2]
        elif is_single_storey_explicit:
            floor_count = 1
            levels = [0]
        else:
            floor_count = 2
            levels = [0, 1]

        has_bhk = bool(re.search(r'\d+\s*bhk', p_lower))
        # Hard override: 1-bedroom (or 0-bed or BHK apartments/flats) without stairs are ALWAYS single-storey.
        # A 1-bed or 2BHK flat/house without stairs never has a staircase, Level 1, or terrace regardless of
        # what the plot category's "standard_floors" suggests.
        if ((bedroom_count <= 1 or has_bhk) and not has_stairs and "stair" not in p_lower and not is_multi_storey_explicit) or has_single_floor_phrase:
            floor_count = 1
            levels = [0]
            is_single_storey_explicit = True

        hard_constraints.append(f"Storey Count: {floor_count} ({'Single-Storey' if floor_count==1 else ('Double-Storey' if floor_count==2 else 'Triple-Storey G+2')})")
        if floor_count == 1:
            hard_constraints.append("Roof Layer: Standard Weather-Proof Ceiling Slab")


        # 5. Construct Deterministic Room Requirements & Adjacencies
        rooms: List[RoomRequirement] = []
        adjacencies: List[AdjacencyRequirement] = []

        if floor_count >= 2:
            # Multi-Storey Distribution
            ground_bed_count = gf_bed_count
            if floor_count == 3:
                rem_beds = bedroom_count - ground_bed_count
                first_bed_count = min(2, (rem_beds + 1) // 2) if rem_beds > 0 else 0
                second_bed_count = rem_beds - first_bed_count
            else:
                first_bed_count = bedroom_count - ground_bed_count
                second_bed_count = 0

            # Ground Floor Spaces
            if has_garage:
                rooms.append(RoomRequirement(
                    room_id="req_L0_porch",
                    room_type="garage",
                    room_name="Car Porch (Garage)",
                    min_area_m2=10.0 if category == "3_marla" else 12.0,
                    max_area_m2=16.0 if category == "3_marla" else 24.0,
                    requires_exterior_wall=True,
                    level_index=0
                ))
            if has_living and not (category == "5_marla" and bedroom_count >= 5) and not (category == "3_marla" and ground_bed_count > 0):
                rooms.append(RoomRequirement(
                    room_id="req_L0_drawing",
                    room_type="living_room",
                    room_name="Drawing Room (Living)",
                    min_area_m2=14.0,
                    max_area_m2=22.0,
                    requires_exterior_wall=True,
                    level_index=0
                ))
            if has_stairs:
                rooms.append(RoomRequirement(
                    room_id="req_L0_stairs",
                    room_type="corridor",
                    room_name="Entrance & Stair Lobby",
                    min_area_m2=4.0 if category == "3_marla" else 4.5,
                    max_area_m2=8.0,
                    requires_exterior_wall=False,
                    level_index=0
                ))
            if has_powder:
                rooms.append(RoomRequirement(
                    room_id="req_L0_powder",
                    room_type="bathroom",
                    room_name="Powder Room (Guest Bath)",
                    min_area_m2=2.0,
                    max_area_m2=3.5,
                    requires_exterior_wall=False,
                    level_index=0
                ))
                adjacencies.append(AdjacencyRequirement(
                    source_room_name="Entrance & Stair Lobby",
                    target_room_name="Powder Room (Guest Bath)",
                    relationship_type="via_door"
                ))
            if has_tv_lounge or category == "3_marla":
                rooms.append(RoomRequirement(
                    room_id="req_L0_tv_lounge",
                    room_type="lounge",
                    room_name="TV Lounge (Family Living)",
                    min_area_m2=9.0 if category == "3_marla" else 10.0,
                    max_area_m2=20.0,
                    requires_exterior_wall=True,
                    level_index=0
                ))
            if has_dining:
                rooms.append(RoomRequirement(
                    room_id="req_L0_dining",
                    room_type="dining",
                    room_name="Dining Room",
                    min_area_m2=6.5,
                    max_area_m2=12.0,
                    requires_exterior_wall=False,
                    level_index=0
                ))
            if has_kitchen:
                rooms.append(RoomRequirement(
                    room_id="req_L0_kitchen",
                    room_type="kitchen",
                    room_name="Modern Kitchen",
                    min_area_m2=4.5 if category == "3_marla" else 6.5,
                    max_area_m2=12.0,
                    requires_exterior_wall=True,
                    level_index=0
                ))
                if has_dining:
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name="Dining Room",
                        target_room_name="Modern Kitchen",
                        relationship_type="via_door"
                    ))
            if has_dirty_kitchen:
                rooms.append(RoomRequirement(
                    room_id="req_L0_dirty_kitchen",
                    room_type="kitchen",
                    room_name="Dirty Kitchen (Wet Kitchen)",
                    min_area_m2=3.5,
                    max_area_m2=8.0,
                    requires_exterior_wall=True,
                    level_index=0
                ))
                if has_kitchen:
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name="Modern Kitchen",
                        target_room_name="Dirty Kitchen (Wet Kitchen)",
                        relationship_type="via_door"
                    ))

            # Ground Bedrooms + Attached Baths
            for g_i in range(ground_bed_count):
                b_id = f"req_L0_bed{g_i+1}"
                bath_id = f"req_L0_bath{g_i+1}"
                b_name = f"Bedroom {g_i+1}" if g_i > 0 else "Master Bedroom"
                bath_name = f"Attached Bath {g_i+1}" if g_i > 0 else "Master Bathroom"

                rooms.append(RoomRequirement(
                    room_id=b_id,
                    room_type="bedroom",
                    room_name=b_name,
                    min_area_m2=10.0 if category == "3_marla" else 12.0,
                    max_area_m2=18.0,
                    requires_exterior_wall=True,
                    level_index=0,
                    is_master=(g_i == 0),
                    is_attached_to=bath_id
                ))
                rooms.append(RoomRequirement(
                    room_id=bath_id,
                    room_type="bathroom",
                    room_name=bath_name,
                    min_area_m2=3.0,
                    max_area_m2=6.0,
                    requires_exterior_wall=False,
                    level_index=0,
                    is_attached_to=b_id
                ))
                adjacencies.append(AdjacencyRequirement(
                    source_room_name=b_name,
                    target_room_name=bath_name,
                    relationship_type="via_door",
                    is_mandatory=True
                ))
                primary_living = "TV Lounge (Family Living)" if (has_tv_lounge or category == "3_marla") else ("Drawing Room (Living)" if has_living else None)
                if primary_living:
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name=primary_living,
                        target_room_name=b_name,
                        relationship_type="via_door"
                    ))

            # First Floor Spaces
            if has_stairs:
                rooms.append(RoomRequirement(
                    room_id="req_L1_stairs",
                    room_type="corridor",
                    room_name="Staircase Landing",
                    min_area_m2=4.0 if category == "3_marla" else 4.5,
                    max_area_m2=8.0,
                    requires_exterior_wall=False,
                    level_index=1
                ))
            if has_garage:
                rooms.append(RoomRequirement(
                    room_id="req_L1_terrace",
                    room_type="balcony",
                    room_name="Front Open Terrace / Balcony",
                    min_area_m2=8.0,
                    max_area_m2=20.0,
                    requires_exterior_wall=True,
                    level_index=1
                ))
            if has_tv_lounge or floor_count >= 2:
                rooms.append(RoomRequirement(
                    room_id="req_L1_tv_lounge",
                    room_type="lounge",
                    room_name="Upper TV Lounge & Gallery",
                    min_area_m2=8.0 if category == "3_marla" else 9.0,
                    max_area_m2=18.0,
                    requires_exterior_wall=True,
                    level_index=1
                ))
                if has_stairs:
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name="Staircase Landing",
                        target_room_name="Upper TV Lounge & Gallery",
                        relationship_type="via_door"
                    ))

            # First Floor Bedrooms + Attached Baths
            for f_i in range(first_bed_count):
                total_bed_idx = ground_bed_count + f_i + 1
                b_id = f"req_L1_bed{total_bed_idx}"
                bath_id = f"req_L1_bath{total_bed_idx}"
                b_name = f"Bedroom {total_bed_idx}"

                curr_bath_count = len([r for r in rooms if r.room_type == "bathroom"])
                add_bath = (curr_bath_count < bath_count)

                rooms.append(RoomRequirement(
                    room_id=b_id,
                    room_type="bedroom",
                    room_name=b_name,
                    min_area_m2=11.5,
                    max_area_m2=17.0,
                    requires_exterior_wall=True,
                    level_index=1,
                    is_attached_to=bath_id if add_bath else None
                ))
                if add_bath:
                    rooms.append(RoomRequirement(
                        room_id=bath_id,
                        room_type="bathroom",
                        room_name=f"Attached Bath {total_bed_idx}",
                        min_area_m2=2.8,
                        max_area_m2=5.5,
                        requires_exterior_wall=False,
                        level_index=1,
                        is_attached_to=b_id
                    ))
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name=b_name,
                        target_room_name=f"Attached Bath {total_bed_idx}",
                        relationship_type="via_door",
                        is_mandatory=True
                    ))
                if has_tv_lounge:
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name="Upper TV Lounge & Gallery",
                        target_room_name=b_name,
                        relationship_type="via_door"
                    ))

            if floor_count == 3 and second_bed_count > 0:
                # Level 2 Spaces
                if has_stairs:
                    rooms.append(RoomRequirement(
                        room_id="req_L2_stairs",
                        room_type="corridor",
                        room_name="Second Floor Staircase Landing",
                        min_area_m2=4.5,
                        max_area_m2=8.0,
                        requires_exterior_wall=False,
                        level_index=2
                    ))
                for s_i in range(second_bed_count):
                    total_bed_idx = ground_bed_count + first_bed_count + s_i + 1
                    b_id = f"req_L2_bed{total_bed_idx}"
                    bath_id = f"req_L2_bath{total_bed_idx}"
                    b_name = f"Bedroom {total_bed_idx}"
                    rooms.append(RoomRequirement(
                        room_id=b_id,
                        room_type="bedroom",
                        room_name=b_name,
                        min_area_m2=11.5,
                        max_area_m2=17.0,
                        requires_exterior_wall=True,
                        level_index=2,
                        is_attached_to=bath_id
                    ))
                    rooms.append(RoomRequirement(
                        room_id=bath_id,
                        room_type="bathroom",
                        room_name=f"Attached Bath {total_bed_idx}",
                        min_area_m2=2.8,
                        max_area_m2=5.5,
                        requires_exterior_wall=False,
                        level_index=2,
                        is_attached_to=b_id
                    ))
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name=b_name,
                        target_room_name=f"Attached Bath {total_bed_idx}",
                        relationship_type="via_door",
                        is_mandatory=True
                    ))

        else:
            # Single-Storey Program
            if has_garage:
                rooms.append(RoomRequirement(
                    room_id="req_L0_porch",
                    room_type="garage",
                    room_name="Car Porch (Garage)",
                    min_area_m2=12.0,
                    max_area_m2=20.0,
                    requires_exterior_wall=True,
                    level_index=0
                ))
            if has_living:
                rooms.append(RoomRequirement(
                    room_id="req_L0_living",
                    room_type="living_room",
                    room_name="Living Room",
                    min_area_m2=14.0,
                    max_area_m2=22.0,
                    requires_exterior_wall=True,
                    level_index=0
                ))
            if has_kitchen:
                rooms.append(RoomRequirement(
                    room_id="req_L0_kitchen",
                    room_type="kitchen",
                    room_name="Kitchen",
                    min_area_m2=6.5,
                    max_area_m2=12.0,
                    requires_exterior_wall=True,
                    level_index=0
                ))
            if has_dining:
                rooms.append(RoomRequirement(
                    room_id="req_L0_dining",
                    room_type="dining",
                    room_name="Dining Room",
                    min_area_m2=6.0,
                    max_area_m2=10.0,
                    requires_exterior_wall=False,
                    level_index=0
                ))

            if has_powder or bedroom_count <= 1:
                rooms.append(RoomRequirement(
                    room_id="req_L0_powder",
                    room_type="bathroom",
                    room_name="Powder Room (Guest Bath)",
                    min_area_m2=1.8,
                    max_area_m2=2.5,
                    requires_exterior_wall=False,
                    level_index=0
                ))

            for b_i in range(bedroom_count):
                b_id = f"req_L0_bed{b_i+1}"
                is_m = (b_i == 0)
                b_name = "Master Bedroom" if is_m else f"Bedroom {b_i+1}"
                attached_bath_id = f"req_L0_bath{b_i+1}" if (is_m or b_i < bath_count) else None

                rooms.append(RoomRequirement(
                    room_id=b_id,
                    room_type="bedroom",
                    room_name=b_name,
                    min_area_m2=11.5,
                    max_area_m2=16.0,
                    requires_exterior_wall=True,
                    level_index=0,
                    is_master=is_m,
                    is_attached_to=attached_bath_id
                ))

                if attached_bath_id:
                    bath_name = "Master Bathroom" if is_m else f"Bathroom {b_i+1}"
                    rooms.append(RoomRequirement(
                        room_id=attached_bath_id,
                        room_type="bathroom",
                        room_name=bath_name,
                        min_area_m2=3.0,
                        max_area_m2=5.5,
                        requires_exterior_wall=False,
                        level_index=0,
                        is_attached_to=b_id
                    ))
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name=b_name,
                        target_room_name=bath_name,
                        relationship_type="via_door",
                        is_mandatory=True
                    ))
                primary_living = "Living Room" if has_living else ("TV Lounge" if has_tv_lounge else None)
                if primary_living:
                    adjacencies.append(AdjacencyRequirement(
                        source_room_name=primary_living,
                        target_room_name=b_name,
                        relationship_type="via_door"
                    ))

        area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:sqm|m2|sq\s*m)', p_lower)
        if area_match:
            target_total_area = float(area_match.group(1))
        else:
            target_total_area = sum(r.min_area_m2 for r in rooms) * 1.15

        program = ArchitecturalProgram(
            project_title=f"{bedroom_count} Bed Residence ({profile['plot_name']})",
            plot_category=category,
            plot_size_desc=f"{profile['plot_name']} ({profile['dim_ft']})",
            plot_dimensions_ft=profile["dim_ft"],
            spatial_typology=spatial_typology,
            layout_style=spatial_typology,
            stair_type=stair_type,
            stair_engine_class=stair_engine_class,
            max_ground_coverage_m2=max_allowable_ground,
            total_target_area_m2=round(target_total_area, 1),
            total_ground_footprint_m2=round(total_ground_footprint_m2, 1),
            floor_count=floor_count,
            levels=levels,
            is_single_storey_explicit=is_single_storey_explicit,
            is_feasible=True,
            feasibility_status="FEASIBLE",
            requested_room_counts=requested_counts,
            ground_room_counts=ground_room_counts,
            show_kitchen_count=show_kitchen_count,
            dirty_kitchen_count=dirty_kitchen_count,
            car_porch_capacity=car_porch_capacity,
            has_landlocked_bedrooms=has_landlocked,
            has_separate_formal_dining=has_separate_formal_dining,
            rooms=rooms,
            adjacencies=adjacencies,
            hard_constraints=hard_constraints,
            soft_constraints=soft_constraints,
            raw_prompt=prompt,
            has_servant_quarter=has_servant,
            warnings=warnings
        )

        if validate:
            validate_architectural_feasibility(program, raise_on_error=raise_on_error)

        return program
