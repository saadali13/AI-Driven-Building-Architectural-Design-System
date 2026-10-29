# Architectural Floor Plan Failure Taxonomy

**Document:** `reports/floorplan_failure_taxonomy.md`  
**Standard:** Antigravity AI Architectural Plan Validation Standard v4.2  
**Purpose:** Formal classification of structural, topological, geometric, dimensional, and semantic failures in automated floor-plan generation. Every plan validation failure must map to one or more deterministic failure codes.

---

## 1. Failure Codes Matrix (F01 – F20)

| Code | Failure Classification | Severity | Validation Domain | Mathematical / Algorithmic Trigger | Mitigation / Remedy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F01** | **Wrong Room Count** | **CRITICAL** | Program / Semantic | $\text{count}(\text{rooms}_{\text{generated}}[T]) \ne \text{count}(\text{rooms}_{\text{requested}}[T])$ for category $T$. | Reject layout before rendering; enforce deterministic node generation in program solver. |
| **F02** | **Missing Room** | **CRITICAL** | Program / Semantic | Room type requested in prompt $\notin \{\text{rooms}_{\text{generated}}\}$. | Check requirement parser; regenerate with hard constraint for missing room. |
| **F03** | **Fake Room Created by Text** | **CRITICAL** | Semantic / OCR | Text label exists at $(x, y)$ but point-in-polygon test returns no enclosing watertight polygon, or polygon area $< \text{min\_threshold}$. | Enforce V4 Semantic Discipline: text without enclosed polygon $\rightarrow$ rejected; geometry without text $\rightarrow$ `unclassified_closed_region`. |
| **F04** | **Incorrect Room Boundary** | **CRITICAL** | Geometry | Polygon self-intersection, non-closed coordinate ring, or interior overlap area $> 0.05\,\text{m}^2$ ($\text{IoU} > 0.01$). | Snap vertices to orthogonal grid; apply Shapely `buffer(0)` or boolean difference. |
| **F05** | **Bathroom Not Actually Enclosed** | **CRITICAL** | Geometry / Code | Bathroom polygon is unclosed, shares open boundary with non-bathroom space, or lacks 4 continuous enclosing wall segments. | Enforce watertight polygon enclosure check; bathrooms must have 100% boundary wall coverage minus door opening width ($0.75-0.85\,\text{m}$). |
| **F06** | **Master Bathroom Not Attached** | **CRITICAL** | Topological / Semantic | Master Bedroom and Master Bathroom do not share a 1D boundary segment of length $\ge 0.8\,\text{m}$, or no door connects them directly. | Compute $\text{length}(\text{poly}_{\text{bed}} \cap \text{poly}_{\text{bath}}) \ge 0.80\,\text{m}$ AND verify door opening $d$ with `connects_rooms = [bed_id, bath_id]`. |
| **F07** | **Inaccessible Room (Landlocked)** | **CRITICAL** | Circulation / Graph | Room node has degree $0$ in door-connectivity graph ($\text{deg}(r) = 0$), or shortest path to main entrance $\nexists$. | Graph traversal ($\text{BFS}/\text{Dijkstra}$) must find valid path from `room_entrance` to all habitable rooms. |
| **F08** | **Invalid Door** | **HIGH** | Circulation / Geometry | Door opening is not located on a shared boundary between two rooms, overlaps another door, or lacks wall host. | Distance from door midpoint to shared wall segment must be $\le 0.15\,\text{m}$; door width must fit along shared segment length. |
| **F09** | **Invalid Window** | **HIGH** | Envelope / Code | Window placed on interior partition wall between two interior rooms, or missing on exterior habitable rooms. | Distance from window centerline to exterior boundary must be $\le 0.25\,\text{m}$ (or open to verified OTS shaft). |
| **F10** | **Staircase Collision** | **CRITICAL** | 3D / Circulation | Staircase polygon collides with structural walls, blocks a door opening, lacks $\ge 1.0\,\text{m}$ landing clearance, or misaligns vertically across floors. | Enforce identical $(X, Y)$ stair bounding box across Level 0 and Level 1; verify landing clearance box $\ge 1.0\,\text{m} \times \text{stair\_width}$. |
| **F11** | **Circulation Failure** | **HIGH** | Functional / Flow | Corridor width $< 0.90\,\text{m}$, bedroom accessible only by crossing another bedroom, or bathroom opening into kitchen. | Enforce privacy adjacency matrix: $\text{edge}(\text{bedroom}, \text{kitchen}) = \emptyset$, $\text{edge}(\text{bath}_A, \text{bath}_B) = \emptyset$. |
| **F12** | **Impossible Dimensions** | **HIGH** | Computational Geometry | Room aspect ratio $> 2.5$, room width $< 2.4\,\text{m}$ for bedrooms, or bathroom area $>$ living room area. | Plausibility thresholds: Bedroom min width $2.8\,\text{m}$, min area $9.0\,\text{m}^2$; aspect ratio range $[0.5, 2.0]$. |
| **F13** | **Site / Plot Constraint Violation** | **CRITICAL** | Zoning / By-laws | Total building footprint area $>$ allowable covered area, or building violates front/rear/side setback lines. | $\text{poly}_{\text{footprint}} \subseteq \text{poly}_{\text{allowable\_envelope}}$; check setback distances to property boundary. |
| **F14** | **Exterior Area Counted as Room** | **MEDIUM** | Semantic / Program | Porch, lawn, balcony, terrace, or OTS counted in the requested indoor room count. | Strict partitioning of `is_habitable` and category flags: `garage`, `outdoor`, `lawn`, `ots` cannot satisfy bedroom/living room requirements. |
| **F15** | **Furniture Collision** | **MEDIUM** | Drafting / Geometry | Furniture bounding box intersects structural wall, blocks door swing arc, or overlaps sanitary fixture. | Collision check: $\text{furniture\_poly} \cap \text{wall\_poly} = \emptyset$; $\text{furniture\_poly} \cap \text{door\_swing\_arc} = \emptyset$. |
| **F16** | **Label / Geometry Mismatch** | **HIGH** | Annotation / CAD | Labeled area text (e.g., "$16.0\,\text{m}^2$") contradicts calculated polygon area by $> 5\%$, or labeled imperial dimensions contradict metric geometry. | Auto-calculate annotation strings directly from polygon: $\text{width} = \text{dx}$, $\text{length} = \text{dy}$, $\text{area} = \text{poly.area}$. |
| **F17** | **Visual Rendering Failure** | **MEDIUM** | Raster / Graphics | Missing line weights, clipped canvas boundaries, illegible overlapping typography, or cartoon graphic styling. | Automated Vision QA check for canvas edge padding, text bounding box overlaps, and standard CAD contrast ratios. |
| **F18** | **Inconsistent Scale** | **HIGH** | CAD / Cartography | Discrepancy between stated scale bar, pixel-to-meter factor, and dimension callouts. | Store global `scale_px_to_m` in metadata; assert that $\text{pixel\_distance} \times \text{scale} = \text{metric\_distance}$. |
| **F19** | **Architectural Implausibility** | **HIGH** | Structural / Spatial | Upper floor living spaces floating without ground-floor structural wall support below, or missing vertical plumbing stack. | Vertical stacking validation: ground and upper floor load-bearing walls must overlap $\ge 70\%$; bathrooms must vertically align. |
| **F20** | **Contradictory Semantic Graph** | **CRITICAL** | Graph / Logic | Graph contains conflicting edges (e.g. room marked both `interior` and `outdoor`, or directed cycle in vertical circulation). | Assert semantic consistency constraints on NetworkX graph before exporting plan. |

---

## 2. Quantitative Quality Gate Thresholds

A plan passes automated validation **if and only if**:
$$\text{Critical Failures} = 0 \quad \text{and} \quad \text{High Failures} = 0 \quad \text{and} \quad \text{Quality Score} \ge 95\%$$

The Quality Gate generates a standardized machine-readable JSON record:
```json
{
  "plan_id": "gen_5m_plan_001",
  "final_status": "PASS",
  "quality_score": 0.98,
  "validation_gates": {
    "program_valid": true,
    "room_count_valid": true,
    "bathroom_count_valid": true,
    "master_bath_attached": true,
    "circulation_valid": true,
    "door_graph_valid": true,
    "window_validation": true,
    "geometry_valid": true,
    "dimension_consistency": true,
    "site_constraint_valid": true,
    "visual_validation": true
  },
  "failure_codes": []
}
```
If any critical gate fails, `final_status` is marked `"FAIL"`, and the generator must trigger an iterative refinement or structural repair loop.
