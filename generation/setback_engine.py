"""
Statutory Setback Clipping & Usable Envelope Engine.
Applies municipal building bylaws (CDA/LDA/IBC) to arbitrary polygonal plots
via segment-specific inward offset clipping, computing the legal buildable footprint.
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import orient

from requirements.parser import InfeasibleProgramError
from requirements.site_geometry import SiteBoundary, BoundaryEdge, FT_TO_M, M_TO_FT


@dataclass
class SetbackConfig:
    front_m: float
    rear_m: float
    side_left_m: float
    side_right_m: float
    chamfer_m: float

    @classmethod
    def for_scale(cls, plot_category: str) -> "SetbackConfig":
        """
        Standard Pakistani municipal statutory setbacks (in meters) based on plot scale:
        - 3 Marla (20' x 33.75'): 0ft (0m) front, 3ft (0.91m) rear OTS, 0ft (0m) sides. (G+2 / 3 Floors).
        - 5 Marla (25' x 45'): 5ft (1.52m) front lawn, 3ft (0.91m) rear OTS, 0ft (0m) side setbacks. (G+1 & G+2).
        - 7 Marla (30' x 53'): 5ft (1.52m) front lawn, 3ft (0.91m) rear OTS, 3ft (0.91m) side service passage. (G+1).
        - 10 Marla (35' x 65'): 10ft (3.05m) front lawn, 5ft (1.52m) rear garden, 5ft (1.52m) side service passage. (G+1).
        - 1 Kanal (50' x 90'): 15ft (4.57m) front lawn, 7ft (2.13m) rear garden, 5ft (1.52m) side passages on BOTH sides. (G+1).
        """
        if plot_category == "3_marla":
            return cls(front_m=0.0, rear_m=0.91, side_left_m=0.0, side_right_m=0.0, chamfer_m=0.0)
        elif plot_category == "5_marla":
            return cls(front_m=1.52, rear_m=0.91, side_left_m=0.0, side_right_m=0.0, chamfer_m=1.52)
        elif plot_category == "7_marla":
            return cls(front_m=1.52, rear_m=0.91, side_left_m=0.91, side_right_m=0.0, chamfer_m=1.52)
        elif plot_category == "10_marla":
            return cls(front_m=3.05, rear_m=1.52, side_left_m=1.52, side_right_m=0.0, chamfer_m=2.0)
        else:  # 1_kanal
            return cls(front_m=4.57, rear_m=2.13, side_left_m=1.52, side_right_m=1.52, chamfer_m=3.0)


@dataclass
class BuildableEnvelope:
    site_boundary: SiteBoundary
    poly_buildable: Polygon
    setbacks: SetbackConfig
    usable_coverage: float  # Ratio of buildable area to total site area
    area_m2: float
    area_sqft: float
    bounds: Tuple[float, float, float, float]  # minx, miny, maxx, maxy in meters


class SetbackEngine:
    """
    Computes statutory setback offsets on arbitrary 2D plots and extracts the legal buildable footprint.
    """

    MIN_HABITABLE_ENVELOPE_SQM = 45.0  # F13 minimum viable ground floor footprint (~484 sq ft)

    @classmethod
    def compute_buildable_envelope(
        cls,
        site_boundary: SiteBoundary,
        custom_setbacks: Optional[SetbackConfig] = None
    ) -> BuildableEnvelope:
        """
        Clips the site boundary polygon by edge-specific inward statutory setbacks:
        - FRONT: Front street setback (8' to 15')
        - REAR: Rear setback / OTS light court (5' to 7')
        - SIDES: Lateral side passages (0' to 5')
        - CHAMFER: Corner splay setback
        """
        setbacks = custom_setbacks or SetbackConfig.for_scale(site_boundary.plot_category)
        site_poly = site_boundary.polygon

        minx, miny, maxx, maxy = site_boundary.bounds
        diag = math.hypot(maxx - minx, maxy - miny) * 3.0

        buildable = site_poly

        for edge in site_boundary.edges:
            # Determine inward setback distance for this edge
            if edge.semantic == "FRONT":
                d_offset = setbacks.front_m
            elif edge.semantic == "REAR":
                d_offset = setbacks.rear_m
            elif edge.semantic == "LEFT":
                d_offset = setbacks.side_left_m
            elif edge.semantic == "RIGHT":
                d_offset = setbacks.side_right_m
            elif edge.semantic == "CHAMFER":
                d_offset = setbacks.chamfer_m
            else:
                d_offset = min(setbacks.side_left_m, setbacks.side_right_m)

            if d_offset <= 0.001:
                continue

            # Compute inward normal vector
            p1 = edge.start
            p2 = edge.end
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            L = math.hypot(dx, dy)
            if L <= 0.001:
                continue

            # In CCW polygon, inward normal is to the left of the edge: (-dy/L, dx/L)
            nx = -dy / L
            ny = dx / L

            # Shift the edge inward by d_offset
            sp1 = (p1[0] + d_offset * nx, p1[1] + d_offset * ny)
            sp2 = (p2[0] + d_offset * nx, p2[1] + d_offset * ny)

            # Construct large half-plane polygon covering the interior side of the shifted line
            tx = dx / L
            ty = dy / L

            # Points of the interior half-space
            hp_pt1 = (sp1[0] - diag * tx, sp1[1] - diag * ty)
            hp_pt2 = (sp2[0] + diag * tx, sp2[1] + diag * ty)
            hp_pt3 = (hp_pt2[0] + diag * nx, hp_pt2[1] + diag * ny)
            hp_pt4 = (hp_pt1[0] + diag * nx, hp_pt1[1] + diag * ny)

            half_plane = Polygon([hp_pt1, hp_pt2, hp_pt3, hp_pt4, hp_pt1])
            if half_plane.is_valid:
                buildable = buildable.intersection(half_plane)

        # Clean resulting geometry
        if buildable.geom_type == "MultiPolygon":
            # Select largest contiguous polygon
            buildable = max(buildable.geoms, key=lambda g: g.area)

        if not buildable.is_valid:
            buildable = buildable.buffer(0)

        area_m2 = round(buildable.area, 2)
        area_sqft = round(area_m2 * 10.7639, 1)
        usable_coverage = round(area_m2 / max(0.1, site_boundary.area_m2), 3)

        # F13 Infeasibility Guard check:
        if area_m2 < cls.MIN_HABITABLE_ENVELOPE_SQM:
            raise InfeasibleProgramError(
                f"F13 Infeasible: Plot geometry too constrained for habitable residence after applying mandatory setbacks. "
                f"Buildable area is {area_m2:.1f} m² ({area_sqft:.0f} sq ft), which is less than statutory minimum "
                f"{cls.MIN_HABITABLE_ENVELOPE_SQM:.1f} m²."
            )

        return BuildableEnvelope(
            site_boundary=site_boundary,
            poly_buildable=buildable,
            setbacks=setbacks,
            usable_coverage=usable_coverage,
            area_m2=area_m2,
            area_sqft=area_sqft,
            bounds=buildable.bounds
        )
