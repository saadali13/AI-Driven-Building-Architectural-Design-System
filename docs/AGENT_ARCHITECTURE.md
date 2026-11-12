# Autonomous Architectural AI Engineering System Architecture

**Document Version**: 2.0.0  
**Project**: AI-Driven Building Architectural Design System — ArchiCraft AI Studio  
**Workspace**: `C:\Users\m\OneDrive\Desktop\New folder`  
**Status**: Active Production Standard  

---

## 1. System Topology & Multi-Role Engineering Structure

The system is engineered as an autonomous, multi-disciplinary residential CAD platform combining computational geometry, dataset-driven spatial retrieval, parametric 2D/3D synthesis, and automated architectural QA:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             USER DESIGN REQUEST                             │
│                  (Natural Language Prompt + Plot Geometry)                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 NATURAL LANGUAGE REQUIREMENTS PARSER                         │
│                     (requirements/parser.py)                                │
│          - Extracts Plot Size, Floors, Bedrooms, Style, Amenities           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│             CANONICAL DESIGN MODEL (SINGLE SOURCE OF TRUTH)                 │
│                 - Standardized Metric Coordinates (Meters)                  │
│                 - Closed Room Polygons & Parametric Walls                   │
│                 - Integrated Openings (Hinge, Swing, Wall Cutout)           │
└───────────────────┬───────────────────┬───────────────────┬─────────────────┘
                    │                   │                   │
                    ▼                   ▼                   ▼
       ┌────────────────────┐ ┌───────────────────┐ ┌─────────────────┐
       │ 2D BLUEPRINT VIEW  │ │  FRONT ELEVATION  │ │   3D MODELING   │
       │ (FloorPlanEditor2D)│ │   (Mapper & SVG)  │ │ (Building3DView)│
       └────────────────────┘ └───────────────────┘ └─────────────────┘
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                ARCHITECTURAL QUALITY GATE & VALIDATOR                       │
│              (generation/architectural_validator_engine.py)                 │
│         - Geometric Non-Overlap & Setback Compliance                        │
│         - 90° Swept Arc Door Collision & Circulation Clearance              │
│         - 1:1 Floor-Plan to Elevation Opening Correspondence                │
│         - Multi-Floor Vertical Alignment & Stair Stack Integrity            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Backend API Server (`api_server.py`)
- **Technology**: Python 3 standard library `http.server` running on `http://localhost:8000`.
- **Primary Routes**:
  - `POST /api/generate`: Synthesizes full canonical architectural design.
  - `POST /api/regenerate`: Parametrically mutates selected rooms while preserving exterior envelope.
  - `GET /api/projects` & `POST /api/projects/save`: JSON project persistence.
  - `POST /api/export/dxf`: Exports layered CAD drawing conforming to AIA CAD layer standards.
  - `POST /api/export/svg`: Exports vector architectural presentation sheets.
  - `POST /api/export/obj`: Exports 3D Wavefront OBJ mesh with materials.
  - `POST /api/export/blend`: Generates Blender 5.1 procedural solid extrusion script.

### 2.2 Primary Frontend (`archai_frontend/archai_frontend`)
- **Technology**: React 19, Vite, Three.js, Tailwind CSS v4 running on `http://localhost:5173`.
- **Components**:
  - `WorkspacePage.jsx`: Central studio workspace coordinating 2D canvas, 3D viewport, and elevations.
  - `FloorPlanEditor2D.jsx`: Interactive SVG architectural floor-plan editor.
  - `BuildingViewport3D.jsx`: Real-time Three.js 3D parametric scene renderer.
  - `RequirementsGenerator.jsx`: Structured design intent input and prompt guidance.
  - `CostEstimationModule.jsx`: Dynamic Bill of Quantities (BOQ) calculator.

### 2.3 Secondary Frontend (`frontend`)
- **Technology**: React 19, TypeScript, React Router.
- **Directive**: Kept intact as secondary architecture dashboard; zero modifications unless explicitly approved.

---

## 3. Canonical Architectural Design Model (Single Source of Truth)

All subsystems (2D floor plan, front elevation, 3D extrusion, DXF export) derive strictly from a unified, validated canonical design model:

```json
{
  "design_id": "uuid-v4",
  "version": 1,
  "units": "meters",
  "plot": {
    "width_m": 7.62,
    "length_m": 13.72,
    "road_orientation": "north",
    "setbacks": {"front_m": 1.5, "rear_m": 1.5, "side_m": 0.0}
  },
  "floors": [
    {
      "floor_index": 0,
      "floor_name": "Ground Floor",
      "elevation_m": 0.0,
      "ceiling_height_m": 3.05,
      "rooms": [
        {
          "id": "room_01",
          "name": "Master Bedroom",
          "category": "bedroom",
          "polygon_m": [[0.0, 0.0], [4.0, 0.0], [4.0, 3.5], [0.0, 3.5]],
          "area_m2": 14.0
        }
      ],
      "walls": [
        {
          "id": "wall_01",
          "start_m": [0.0, 0.0],
          "end_m": [4.0, 0.0],
          "thickness_m": 0.2286,
          "is_exterior": true,
          "openings": [
            {
              "id": "op_01",
              "type": "door",
              "width_m": 0.914,
              "height_m": 2.134,
              "distance_along_wall_m": 0.5,
              "hinge_side": "start",
              "swing_direction": "inward",
              "swing_arc_deg": 90
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 4. Coordinate Transformations & Axis Conventions

- **Backend Canonical Coordinates**: Metric Cartesian $(X, Y)$ in meters where $+X$ is East and $+Y$ is North. Floor elevation $+Z$ is up.
- **2D Frontend Canvas**: SVG coordinate space $(X_{px}, Y_{px})$ scaled via `scaleFactor = canvas_width / plot_width`.
- **Three.js 3D Viewport**: World coordinates $(X_{3D}, Y_{3D}, Z_{3D})$ where Three.js $+Y$ corresponds to vertical architectural height ($Z_{canonical}$).
- **AutoCAD DXF**: Inches or millimeters conforming to AIA standard layers (`A-WALL`, `A-DOOR`, `A-GLAZ`, `A-FLOR`).

