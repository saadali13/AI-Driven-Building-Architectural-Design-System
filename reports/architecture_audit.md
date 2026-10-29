# Architectural & Algorithmic Engineering Audit

**Document:** `reports/architecture_audit.md`  
**Revision:** 3.0 (Post Independent Audit & Governance Integration)  
**Date:** September 17, 2026  
**Auditor:** Antigravity System Architecture Team  

---

## 1. Unified Hybrid Architectural Pipeline (Raster + DXF)

A critical architectural requirement is that the introduction of a raster computer vision pipeline must **not** discard or replace the existing strong DXF CAD parsing and computational geometry engine. Both modalities must feed the same central representation:

```
                          USER INPUT
              ┌───────────────┴───────────────┐
              ▼                               ▼
       [Raster Image]                   [DXF / CAD File]
              │                               │
              ▼                               ▼
    [Image Vision Pipeline]             [CAD Parser]
    ├── OCR & Dimensions                ├── Layer Segmentation
    ├── Wall Stroke Detection           ├── Polyline Centerlines
    ├── Door Swings & Openings          └── Block / Text Entities
    └── Multi-Signal Wall/Door Graph          │
              │                               │
              └───────────────┬───────────────┘
                              ▼
                       [FUSION ENGINE]
                              ▼
               Canonical Architecture Model
        (Building, Levels, Walls, Openings, Graph)
              │
    ┌─────────┴─────────┬─────────────────────┐
    ▼                   ▼                     ▼
[RAG & Retrieval]  [Constraint Solver]  [Procedural Blender 3D]
- Natural Language - Staged CP-SAT      - Extrusion & Booleans
- Metadata Filters - Layout Generation  - Parametric Facade
                        │                     │
                        ▼                     ▼
                 Canonical Generated      Rendered Images /
                     Floor Plan            GLTF 3D House
                        │
                        ▼
                 [DXF Generator]
                 AutoCAD Production
```

---

## 2. Preservation of V4 Semantic Discipline

A cornerstone principle established in earlier architectural engineering must be rigorously preserved:
> **Geometry-only enclosed areas must NEVER be hallucinated into functional rooms (bedrooms, bathrooms) without explicit semantic evidence.**

The semantic classification engine strictly distinguishes:
1. **Confirmed Functional Room**:
   - Closed polygon $+$ OCR room text label ($+$ plausible dimensions $+$ optional furniture fixture).
   - Example: Closed $16\text{m}^2$ polygon $+$ "BEDROOM" text $\rightarrow$ `confirmed_bedroom` (confidence $\ge 0.90$).
2. **Probable Functional Room**:
   - Closed polygon $+$ detected specialized fixture (e.g. toilet/sink) $+$ appropriate area ($3\text{--}6\text{m}^2$) without legible text.
   - Example: $\rightarrow$ `probable_bathroom` (confidence $\approx 0.70$).
3. **Unclassified Closed Region**:
   - Closed polygon $+$ zero text labels $+$ zero fixture icons.
   - Example: $\rightarrow$ `unclassified_closed_region` (confidence $< 0.50$).
   - *Never* default an unlabelled region to a "possible bedroom". Such regions may represent utility shafts, wall cavities, structural columns, or outdoor voids.

---

## 3. Multi-Signal Door-Aware Segmentation Architecture

Naive morphological flood-fill leaks through doorways. However, simply converting every detected doorway into a solid permanent wall creates an equally destructive failure mode: false door detections introduce artificial walls, corrupting room counts and circulation graphs.

The solution is a **Multi-Signal Wall/Door Graph**:

```
                  INPUT IMAGE
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Wall Evidence       Door Evidence
       (Thick strokes)     (Arcs, gaps, jambs)
             │                   │
             └─────────┬─────────┘
                       ▼
         Architectural Wall/Door Graph
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
Temporary Boundary Closure      Door Opening Preservation
(Strictly for seeded watershed) (Preserved in connectivity graph)
       │                               │
       ▼                               ▼
Watertight Room Polygons        Room Adjacency & Access Path
       │                               │
       └───────────────┬───────────────┘
                       ▼
           Canonical Geometry Model
```

- **Temporary Closure**: Thin virtual line segments are drawn across detected door jambs *only* during the computation of the distance transform for Watershed segmentation (seeded from OCR text centroids).
- **Permanent Preservation**: The door entity `{ "id": "door_1", "connects": ["room_1", "room_2"], "width_m": 0.9 }` is permanently recorded in the spatial relationship graph and canonical model.

---

## 4. Requirement Parser Architecture & Ambiguity Classification

Natural language must **never** directly generate CAD geometry. Ambiguous user prompts are formally classified:

| Test User Input | Classification | Constraint Type | Safe Architectural Action |
| :--- | :--- | :--- | :--- |
| *"4 bedrooms, 3 bathrooms, 40x60 ft plot"* | Explicit Quantitative | **HARD** | Enforce as strict solver equality / boundary constraints. |
| *"Large master bedroom"* | Ambiguous Relative | **SOFT** | Set target area $\ge 20\text{m}^2$ (standard: $14\text{--}18\text{m}^2$); lower bound $16\text{m}^2$. |
| *"Bathrooms near bedrooms"* | Spatial Proximity | **SOFT** | Graph proximity: $\text{distance}(\text{Bath}, \text{Bed}) \le 3.0\text{m}$. |
| *"Good natural lighting"* | Environmental Goal | **HARD** | Require habitable rooms to share edge with exterior building envelope. |
| *"Privacy"* | Layout Topology | **SOFT** | Buffer constraint: Bedrooms do not open directly into Living Room. |
| *"Open kitchen"* | Typological Spatial | **HARD** | Kitchen shares boundary with Dining/Living with zero partition wall. |
| *"Modern house"* | Aesthetic Style | **STYLE ONLY** | Routed to Facade/3D generator (materials, window trim); no 2D geometric distortion. |
| *"3 beds, one can be an office"* | Flex-Use Room | **SOFT** | Place Bed 3 adjacent to front entrance with private access (`bedroom_office_flex`). |

---

## 5. Constraint Solver Engineering Audit (OR-Tools CP-SAT)

Google OR-Tools CP-SAT solves integer interval packing efficiently, but standard formulations are strictly rectangular. A **5-stage progressive layout solver** is enforced:

```
[Stage 1: Orthogonal Room Packing]
   - Solves primary room rectangles within plot setbacks.
   - Enforces min/max width, aspect ratio (1.0 to 1.8), and non-overlap.
   ▼
[Stage 2: Circulation Spine Allocation]
   - Allocates dedicated hallway/circulation corridor (min width 1.0m to 1.2m) connecting entrance to room clusters.
   ▼
[Stage 3: Topological Graph Alignment]
   - Snaps room adjacencies to match target relationship graph edges (`connected_to`, `adjacent_to`).
   ▼
[Stage 4: Non-Convex / L-Shape Decomposition]
   - Decomposes non-rectangular rooms (L-shaped living/dining, courtyards) into 2 orthogonal sub-rectangles with zero-partition constraints.
   ▼
[Stage 5: Multi-Floor Vertical Alignment]
   - Solves Ground and First floors with shared vertical stairwell and plumbing shaft footprint constraints.
```

---

## 6. Ground Truth Benchmark Governance: The Stratified Golden 50

A benchmark of **50 diverse, 100% human-verified floor plans** must be established **BEFORE** algorithm tuning begins. Developing against subjective visual inspection is strictly prohibited.

### Stratification Matrix
* **1–2 Bedroom Apartments:** 10 plans (studios, urban compact flats)
* **3 Bedroom Houses:** 15 plans (standard family homes)
* **4+ Bedroom Luxury / Large Houses:** 10 plans (villas, multi-bathroom homes)
* **Irregular / L-Shaped / Courtyard Plans:** 5 plans (non-convex building envelopes)
* **Duplex / Multi-Storey Plans:** 5 plans (matched stairwells across floors)
* **Unusual / Commercial-Style Residential:** 5 plans (shop-houses, live-work lofts)

### Comprehensive Ground Truth Specification per Plan
Every Golden plan provides 100% human-verified annotations for:
1. `building_boundary` (outer perimeter polygon)
2. `walls` (exterior vs interior, thickness, centerlines)
3. `doors` (location, swing arc, width)
4. `windows` (location, width, exterior wall association)
5. `rooms` (watertight polygon, area in $\text{m}^2$, centroid)
6. `room_types` (canonical semantic classification)
7. `room_adjacency` (touching rooms)
8. `door_connectivity` (rooms directly connected via door)
9. `dimensions` (normalized value, unit, associated wall pair)
10. `levels` (floor index, ceiling height)
11. `provenance` (SHA-256 hash, annotator ID, verification date)
