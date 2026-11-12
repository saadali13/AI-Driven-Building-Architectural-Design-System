# Architectural Quality & Geometric Validation Specification

**Standard**: ArchiCraft Engineering Validation Rules  
**Module**: `generation/architectural_validator_engine.py`  
**Compliance Target**: Professional Residential Architectural CAD Standard  

---

## 1. Geometric Integrity & Boundary Standards

### 1.1 Room Boundary Closure & Non-Overlap
- **Closed Polygons**: Every room must form a topologically closed Shapely `Polygon` with $N \ge 4$ vertices.
- **Zero Self-Intersection**: $\text{polygon.is\_valid} == \text{True}$. Polygons failing validity checks must be resolved via buffer zero or rejected.
- **Interior Space Non-Overlap**: For any two distinct rooms $A$ and $B$, $\text{Area}(A \cap B) \le 0.05\text{ m}^2$ (allowing numerical floating-point contact tolerances along shared partition walls).
- **Plot Setback Adherence**: All habitable rooms must lie strictly within the permissible building envelope defined by front, rear, and side setback offsets.

---

## 2. Door Openings, Swings & Circulation Clearance

### 2.1 Wall Hosting & Punch-Through Cutouts
- **Host Wall Constraint**: Every door opening $[(x_{start}, y_{start}), (x_{end}, y_{end})]$ must lie collinear with and contained within a valid wall segment.
- **Punch-Through Wall Cutout**: The host wall must be partitioned into two solid segments separated by an opening gap of width equal to the door clear opening ($0.75\text{m} \le W \le 1.10\text{m}$ for pedestrian doors, $2.4\text{m} \le W \le 3.0\text{m}$ for garage portals).
- **Floating Door Prohibition**: Zero doors may float in open space or slice across perpendicular walls without a host.

### 2.2 90-Degree Swept Arc Collision Detection
- **Swept Arc Geometry**: A door leaf of length $L$ swinging through angle $\theta = 90^\circ$ sweeps a circular sector polygon:
  $$\text{ArcPolygon} = \text{HingePoint} \cup \{ \text{ArcPoints}(\alpha) \mid \alpha \in [\alpha_{start}, \alpha_{start} \pm 90^\circ] \}$$
- **Room Interior Confinement**: The swept arc polygon must lie strictly inside the room it services (unless explicitly configured as an exterior swing).
- **Collision Rules**:
  - $\text{Area}(\text{SweptArc} \cap \text{Furniture}) == 0.0$.
  - $\text{Area}(\text{SweptArc} \cap \text{Vehicle}) == 0.0$.
  - $\text{Area}(\text{SweptArc} \cap \text{PerpendicularWalls}) == 0.0$.
  - Adjacent doors must maintain at least $0.30\text{m}$ clearance between their respective swept arcs to avoid pinch-point collisions.

---

## 3. Floor-Plan to Elevation Coherence Standards

- **1:1 Facade Opening Mapping**:
  For every exterior opening on the road-facing wall:
  $$\text{Opening}_{\text{elevation}}.X == \text{Opening}_{\text{floorplan}}.X \pm 0.05\text{m}$$
- **Zero Invented Openings**: The front elevation must never render aesthetic windows on rooms that lack a front exterior window in the floor plan.
- **Floor Level Stacking**: First-floor plinths, lintel heights ($2.13\text{m}$), and floor slabs ($3.05\text{m}$ floor-to-floor) must match canonical height attributes.

---

## 4. Multi-Floor Vertical Alignment Standards

- **Staircase Stacking**: In multi-floor residences ($G+1$ / $G+2$), staircase footprints on the lower floor must align with the upper floor stair well opening within $\pm 0.05\text{m}$.
- **Mumty Tower Alignment**: The rooftop stair mumty tower must envelope the staircase landing to guarantee watertight vertical egress.
- **Plumbing Stacking**: Bathrooms and wet kitchen zones must align or stack vertically over lower wet walls to minimize horizontal drain pipe runs.

