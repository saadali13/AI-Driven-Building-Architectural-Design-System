"""
Non-Orthogonal & Arbitrary Polygonal Site Engine - Site Geometry Module.
Ingests, validates, and reconstructs closed 2D planar plot boundaries from:
1. Explicit coordinate vertices (feet or meters)
2. Surveyor traverse / side-length and angle measurements
3. Common geometric presets (triangles, trapezoids, chamfered corner plots)
"""

import math
from typing import List, Tuple, Dict, Optional, Union
from dataclasses import dataclass, field
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import orient
import re


M_TO_FT = 3.28084
FT_TO_M = 0.3048
SQFT_PER_MARLA = 225.0  # Standard CDA / LDA residential plot metric (225 sq ft / Marla)


@dataclass
class BoundaryEdge:
    start: Tuple[float, float]
    end: Tuple[float, float]
    length_m: float
    length_ft: float
    semantic: str  # "FRONT", "REAR", "LEFT", "RIGHT", "CHAMFER"
    angle_deg: float = 0.0


@dataclass
class SiteBoundary:
    polygon: Polygon
    vertices: List[Tuple[float, float]]  # In meters, closed (vertex_0 == vertex_N), CCW
    vertices_ft: List[Tuple[float, float]]  # In feet, closed
    edges: List[BoundaryEdge] = field(default_factory=list)
    unit: str = "ft"
    shape_type: str = "arbitrary_polygon"  # "triangle", "trapezoid", "corner_plot", "polygon"
    area_m2: float = 0.0
    area_sqft: float = 0.0
    frontage_ft: float = 0.0
    depth_ft: float = 0.0
    plot_category: str = "5_marla"

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Returns (minx, miny, maxx, maxy) in meters."""
        return self.polygon.bounds

    @property
    def width_m(self) -> float:
        minx, _, maxx, _ = self.bounds
        return maxx - minx

    @property
    def depth_m(self) -> float:
        _, miny, _, maxy = self.bounds
        return maxy - miny


class SiteGeometryParser:
    """
    Constructs, normalizes, and validates arbitrary 2D site polygons.
    """

    @classmethod
    def from_vertices(
        cls,
        vertices: List[Tuple[float, float]],
        unit: str = "ft",
        shape_type: str = "arbitrary_polygon"
    ) -> SiteBoundary:
        """
        Builds a SiteBoundary from ordered Cartesian points.
        Automatically checks closure, non-self-intersection, and forces CCW winding.
        """
        if len(vertices) < 3:
            raise ValueError(f"A polygon site requires at least 3 vertices, got {len(vertices)}")

        # Convert to meters if input is in feet
        pts_m = []
        for x, y in vertices:
            if unit.lower() in ("ft", "feet"):
                pts_m.append((round(x * FT_TO_M, 4), round(y * FT_TO_M, 4)))
            else:
                pts_m.append((round(float(x), 4), round(float(y), 4)))

        # Ensure closure (distance between first and last point <= 0.01m)
        p0 = pts_m[0]
        pn = pts_m[-1]
        dist_closure = math.hypot(p0[0] - pn[0], p0[1] - pn[1])
        if dist_closure > 0.01:
            # Append initial vertex to close ring
            pts_m.append(p0)
        else:
            # Snap exact coordinates
            pts_m[-1] = p0

        # Construct Shapely Polygon
        poly = Polygon(pts_m)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty or not poly.is_valid:
            raise ValueError("Invalid polygon: Site boundary self-intersects or has degenerate zero area.")

        # Force Counter-Clockwise (CCW) orientation
        poly = orient(poly, sign=1.0)
        norm_coords_m = list(poly.exterior.coords)

        # Coordinate list in feet
        norm_coords_ft = [
            (round(x * M_TO_FT, 2), round(y * M_TO_FT, 2)) for x, y in norm_coords_m
        ]

        # Categorize scale based on area
        area_m2 = round(poly.area, 2)
        area_sqft = round(area_m2 * 10.7639, 1)
        plot_category = cls._categorize_plot_scale(area_sqft)

        # Analyze edges and assign semantic roles (FRONT, REAR, SIDES, CHAMFER)
        edges = cls._classify_boundary_edges(norm_coords_m, shape_type)

        # Calculate bounding frontage and depth
        minx, miny, maxx, maxy = poly.bounds
        width_m = maxx - minx
        depth_m = maxy - miny
        frontage_ft = round(width_m * M_TO_FT, 1)
        depth_ft = round(depth_m * M_TO_FT, 1)

        return SiteBoundary(
            polygon=poly,
            vertices=norm_coords_m,
            vertices_ft=norm_coords_ft,
            edges=edges,
            unit=unit,
            shape_type=shape_type,
            area_m2=area_m2,
            area_sqft=area_sqft,
            frontage_ft=frontage_ft,
            depth_ft=depth_ft,
            plot_category=plot_category
        )

    @classmethod
    def from_vertex_string(cls, vertex_str: str, unit: str = "ft") -> SiteBoundary:
        """
        Parses semicolon or comma-delimited coordinate string:
        e.g. "0,0; 12,0; 10,18; 0,16" or "0,0, 45,0, 45,65, 0,65"
        """
        pts = []
        clean_str = vertex_str.strip()
        
        # Split by semicolon if present, otherwise by whitespace or comma-pairs
        if ";" in clean_str:
            tokens = [t.strip() for t in clean_str.split(";") if t.strip()]
        else:
            # Split by comma or whitespace pairs
            tokens = [t.strip() for t in re.split(r"[\s]+", clean_str) if t.strip()]
            if len(tokens) == 1 and "," in tokens[0]:
                raw_nums = [float(n.strip()) for n in clean_str.split(",") if n.strip()]
                if len(raw_nums) % 2 != 0:
                    raise ValueError(f"Vertex string contains odd number of coordinates: {clean_str}")
                for i in range(0, len(raw_nums), 2):
                    pts.append((raw_nums[i], raw_nums[i+1]))
                return cls.from_vertices(pts, unit=unit)

        for token in tokens:
            coords = [float(c.strip()) for c in token.split(",") if c.strip()]
            if len(coords) != 2:
                raise ValueError(f"Invalid vertex coordinate format '{token}'. Expected 'X,Y'.")
            pts.append((coords[0], coords[1]))

        return cls.from_vertices(pts, unit=unit)

    @classmethod
    def create_triangle(
        cls,
        front: float,
        left: float,
        hypotenuse: float,
        unit: str = "ft"
    ) -> SiteBoundary:
        """
        Constructs a triangular plot from 3 boundary side lengths:
        - front: base along X axis from (0,0) to (front, 0)
        - left: flank from (0,0) to apex (x_apex, y_apex)
        - hypotenuse: closing diagonal from apex to (front, 0)
        """
        a = float(front)
        b = float(left)
        c = float(hypotenuse)

        # Triangle inequality validation
        if (a + b <= c) or (a + c <= b) or (b + c <= a):
            raise ValueError(f"Triangle inequality violated: sides {a}, {b}, {c} cannot form a valid triangle.")

        # Law of Cosines to solve internal angle at (0,0): cos(theta) = (a^2 + b^2 - c^2) / (2ab)
        cos_theta = (a**2 + b**2 - c**2) / (2.0 * a * b)
        cos_theta = max(-1.0, min(1.0, cos_theta))
        theta = math.acos(cos_theta)

        apex_x = round(b * math.cos(theta), 4)
        apex_y = round(b * math.sin(theta), 4)

        vertices = [(0.0, 0.0), (a, 0.0), (apex_x, apex_y)]
        return cls.from_vertices(vertices, unit=unit, shape_type="triangle")

    @classmethod
    def create_trapezoid(
        cls,
        front: float,
        rear: float,
        left: float,
        right: float,
        unit: str = "ft"
    ) -> SiteBoundary:
        """
        Constructs a trapezoidal / skewed quadrilateral plot:
        - front: bottom street frontage from (0,0) to (front, 0)
        - left: left flank rising from (0,0) to (x_left, y_left)
        - rear: top boundary parallel or skewed relative to front
        - right: right flank closing to (front, 0)
        """
        f = float(front)
        r = float(rear)
        l = float(left)
        rt = float(right)

        # If left flank is approximately orthogonal to front, place it at (0, l)
        # and rear parallel at y ~ avg(l, rt)
        y_rear = min(l, rt)
        x_left = 0.0
        y_left = l
        x_right = r
        y_right = rt

        # Splay coordinates so front aligns with X=0 to X=f
        # Left boundary: (0,0) to (0, l)
        # Rear boundary: (0, l) to (r, y_right)
        # Right boundary: (r, y_right) to (f, 0)
        vertices = [(0.0, 0.0), (f, 0.0), (r, y_right), (0.0, l)]
        return cls.from_vertices(vertices, unit=unit, shape_type="trapezoid")

    @classmethod
    def create_corner_plot(
        cls,
        front: float,
        depth: float,
        splay: float,
        unit: str = "ft"
    ) -> SiteBoundary:
        """
        Constructs a 5-sided chamfered corner plot (road intersection splay):
        The front-left corner (0,0) is splayed by `splay` ft at 45°:
        Vertices (CCW):
        (splay, 0) -> (front, 0) -> (front, depth) -> (0, depth) -> (0, splay) -> (splay, 0)
        """
        f = float(front)
        d = float(depth)
        s = float(splay)

        if s >= min(f, d) / 2.0:
            raise ValueError(f"Splay {s} is too large for plot dimensions {f}x{d}.")

        vertices = [
            (s, 0.0),
            (f, 0.0),
            (f, d),
            (0.0, d),
            (0.0, s)
        ]
        return cls.from_vertices(vertices, unit=unit, shape_type="corner_plot")

    @classmethod
    def create_square(
        cls,
        side_a: float,
        side_b: Optional[float] = None,
        unit: str = "ft"
    ) -> SiteBoundary:
        """
        Constructs a square or orthogonal rectangular plot:
        - side_a: frontage width
        - side_b: depth (defaults to side_a for a true square)
        """
        w = float(side_a)
        d = float(side_b) if side_b is not None else w
        vertices = [(0.0, 0.0), (w, 0.0), (w, d), (0.0, d)]
        return cls.from_vertices(vertices, unit=unit, shape_type="square")

    @classmethod
    def create_lshape(
        cls,
        front_width: float,
        total_depth: float,
        notch_width: float,
        notch_depth: float,
        unit: str = "ft"
    ) -> "SiteBoundary":
        """
        Constructs an L-shaped (notched-corner) plot by cutting a rectangular
        notch from the rear-right corner of a full rectangle:

            (0,D) -----(Fw-Nw, D)
              |              |
              |         (Fw-Nw, D-Nd)
              |              |----(Fw, D-Nd)
              |                       |
            (0,0) -----------(Fw, 0)

        - front_width  (Fw): full frontage
        - total_depth  (D):  full depth
        - notch_width  (Nw): width of the cut-out (from the right side)
        - notch_depth  (Nd): depth of the cut-out (from the rear)
        """
        fw = float(front_width)
        d  = float(total_depth)
        nw = float(notch_width)
        nd = float(notch_depth)

        if nw >= fw or nd >= d:
            raise ValueError(
                f"Notch ({nw}x{nd}) must be smaller than the full plot ({fw}x{d})."
            )

        # Six vertices, counter-clockwise from origin (front-left)
        vertices = [
            (0.0,       0.0),
            (fw,        0.0),
            (fw,        d - nd),
            (fw - nw,   d - nd),
            (fw - nw,   d),
            (0.0,       d),
        ]
        return cls.from_vertices(vertices, unit=unit, shape_type="lshape")


    @classmethod
    def _categorize_plot_scale(cls, area_sqft: float) -> str:
        """Estimates standard Pakistani plot scale category from square footage."""
        if area_sqft < 900:
            return "3_marla"
        elif area_sqft < 1400:
            return "5_marla"
        elif area_sqft < 1900:
            return "7_marla"
        elif area_sqft < 3500:
            return "10_marla"
        else:
            return "1_kanal"

    @classmethod
    def _classify_boundary_edges(
        cls,
        coords_m: List[Tuple[float, float]],
        shape_type: str
    ) -> List[BoundaryEdge]:
        """
        Classifies each polygon boundary segment into FRONT, REAR, SIDES, or CHAMFER.
        """
        edges = []
        n = len(coords_m) - 1  # Last coordinate is closure point

        min_y = min(c[1] for c in coords_m)
        max_y = max(c[1] for c in coords_m)
        depth_span = max(0.01, max_y - min_y)

        for i in range(n):
            p1 = coords_m[i]
            p2 = coords_m[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length_m = round(math.hypot(dx, dy), 3)
            length_ft = round(length_m * M_TO_FT, 2)
            angle_deg = round(math.degrees(math.atan2(dy, dx)), 1)
            mid_y = (p1[1] + p2[1]) / 2.0

            # Default classification logic
            semantic = "SIDES"

            # Check if this edge is the corner chamfer (tilted at ~45° near front)
            if shape_type == "corner_plot" and (abs(abs(angle_deg) - 45.0) < 15.0 or abs(abs(angle_deg) - 135.0) < 15.0) and mid_y < min_y + depth_span * 0.35:
                semantic = "CHAMFER"
            elif mid_y <= min_y + depth_span * 0.20 and abs(dy) <= abs(dx):
                semantic = "FRONT"
            elif mid_y >= max_y - depth_span * 0.25:
                semantic = "REAR"
            else:
                semantic = "LEFT" if (p1[0] + p2[0]) / 2.0 < 0.5 * (min(c[0] for c in coords_m) + max(c[0] for c in coords_m)) else "RIGHT"

            edges.append(BoundaryEdge(
                start=p1,
                end=p2,
                length_m=length_m,
                length_ft=length_ft,
                semantic=semantic,
                angle_deg=angle_deg
            ))

        return edges


# Module-level convenience functions
create_triangle = SiteGeometryParser.create_triangle
create_trapezoid = SiteGeometryParser.create_trapezoid
create_corner_plot = SiteGeometryParser.create_corner_plot
create_square = SiteGeometryParser.create_square
create_lshape = SiteGeometryParser.create_lshape
from_vertices = SiteGeometryParser.from_vertices
from_vertex_string = SiteGeometryParser.from_vertex_string

