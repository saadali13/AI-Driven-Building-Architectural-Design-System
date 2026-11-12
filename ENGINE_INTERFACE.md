# ArchiCraft CAD Engine Interface Specification

## 1. Primary Entry Functions & Signatures

### Primary Server Synthesis Entry Point
Location: `api_server.py:588-604`
```python
@classmethod
def synthesize_design(
    cls,
    prompt: str = "",
    plot_width: float = 25.0,
    plot_length: float = 45.0,
    floors: int = 2,
    bedrooms: int = 4,
    bathrooms: int = 4,
    style: str = "spanish",
    shape: str = "rectangular",
    budget_tier: str = "standard",
    currency: str = "PKR",
    seed: int = 1,
    variant_index: Optional[int] = None,
    strategy: Optional[str] = None,
    custom_room_dimensions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
```

### Dataset RAG Engine Entry Point
Location: `generation/rag_solver.py:464-473`
```python
def synthesize(
    self,
    prompt: str,
    target_dimensions_ft: Optional[Tuple[float, float]] = None,
    plan_id: Optional[str] = None,
    strategy: Optional[str] = None,
    alternative_index: Optional[int] = None,
    disallowed_strategies: Optional[List[str]] = None,
    seed: Optional[int] = None
) -> CanonicalFloorPlan:
```

---

## 2. Exact Input Schema

| Field | Type | Default | Description | Example |
|---|---|---|---|---|
| `prompt` | `str` | `""` | User architectural prompt / description | `"10 Marla Spanish residence with 4 beds, 4 baths"` |
| `plot_width` | `float` | `25.0` | Plot front width in feet | `35.0` |
| `plot_length` | `float` | `45.0` | Plot depth in feet | `65.0` |
| `floors` | `int` | `2` | Number of above-ground storeys | `1`, `2`, `3` |
| `bedrooms` | `int` | `4` | Target bedroom count | `3`, `4`, `5` |
| `bathrooms` | `int` | `4` | Target bathroom count | `3`, `4`, `5` |
| `style` | `str` | `"spanish"` | Architectural aesthetic | `"spanish"`, `"modern"`, `"contemporary"` |
| `shape` | `str` | `"rectangular"`| Plot topology | `"rectangular"`, `"corner"` |
| `budget_tier` | `str` | `"standard"` | Material finish specification | `"economy"`, `"standard"`, `"luxury"` |
| `currency` | `str` | `"PKR"` | Currency for Bill of Quantities | `"PKR"`, `"USD"` |
| `seed` | `int` | `1` | Random generator seed | `42` |
| `strategy` | `Optional[str]` | `None` | Layout planning strategy | `"central_family_lounge"`, `"courtyard_inward_focus"` |
| `custom_room_dimensions` | `Optional[List[Dict]]` | `None` | Overrides for specific room sizes | `[{"name": "Master Bed", "width": 14, "length": 16}]` |

---

## 3. Output Format

The synthesis returns a rich dictionary containing:
```json
{
  "id": "archi_35x65_spanish_1_a1b2c3",
  "title": "10 Marla Spanish Residence (35'x65')",
  "plot": {
    "width": 35.0,
    "length": 65.0,
    "area_sqft": 2275.0,
    "marla": 10.1
  },
  "floors": [
    {
      "level": 0,
      "name": "Ground Floor",
      "covered_sqft": 1350,
      "rooms": [
        {
          "id": "GF_BED1",
          "name": "Master Bedroom",
          "category": "bedroom",
          "x": 2.0,
          "y": 14.5,
          "width": 14.0,
          "length": 15.0,
          "doors": [{"wall": "front", "width": 3.5}],
          "windows": [{"wall": "rear", "width": 5.0}]
        }
      ]
    }
  ],
  "quality_gate": {
    "status": "PASS",
    "score": 0.98,
    "checks": [
      {"code": "F01", "name": "Envelope Boundary Containment", "passed": true, "detail": "..."},
      {"code": "F06", "name": "Master Bedroom Attachment", "passed": true, "detail": "..."}
    ]
  },
  "compliance_checklist": {
    "score_pct": 100,
    "has_fail": false,
    "items": []
  },
  "front_elevation": {
    "svg_drawing": "<svg ...>",
    "raycast_verified": true
  },
  "boq": {
    "total_cost": 18500000,
    "items": []
  },
  "images": {
    "ground": "/output/web_generated/archi_35x65_.../archi_..._ground_floor_2d.png",
    "first": "/output/web_generated/archi_35x65_.../archi_..._first_floor_2d.png",
    "elevation": "/output/web_generated/archi_35x65_.../archi_..._front_elevation_2d.png",
    "elevation_svg": "/output/web_generated/archi_35x65_.../archi_..._elevation.svg",
    "elevation_dxf": "/output/web_generated/archi_35x65_.../archi_..._elevation.dxf"
  }
}
```

---

## 4. Constraints Enforced by FloorPlanQualityGate

Location: `generation/quality_gate.py:25-340`

1. **F01 Room Count & Completeness**:
   - Matches requested bedroom count `len(gen_bedrooms) == req_beds`
   - Matches requested bathroom count `len(gen_bathrooms) >= min(req_baths, req_beds)`
2. **F02 Missing Program Rooms**:
   - Ensures mandatory habitable spaces (`living_room`, `kitchen`) exist.
3. **F03 Degenerate Room Areas**:
   - Habitable rooms area $\ge 5.0\text{ m}^2$ ($\approx 54\text{ sq ft}$)
   - Utility/service rooms area $\ge 1.5\text{ m}^2$ ($\approx 16\text{ sq ft}$)
4. **F04 Geometry Overlaps & Convexity**:
   - Room overlap threshold $< 0.05\text{ m}^2$
   - Habitable bedroom convexity ratio $\text{area}/\text{convex\_hull} \ge 0.95$
5. **F05 Bathroom Enclosure**:
   - Bathrooms must have fully closed $\ge 4$-vertex polygons.
6. **F06 Master Bedroom Ensuite**:
   - Master bedroom must share boundary $\ge 0.70\text{ m}$ or direct door/dressing vestibule to private bath.
7. **F07 Circulation Reachability**:
   - Every habitable room must have unbroken door path from entrance porch/foyer.
8. **F08 Door Placement**:
   - Doors must lie within $0.40\text{ m}$ of room boundaries (no floating doors).
9. **F09 Natural Daylight & Window Ventilation**:
   - Habitable rooms must have windows within $0.40\text{ m}$ of exterior envelope or OTS lightwell.
10. **F10 Staircase Headroom & Alignment**:
    - Staircases verify headroom $\ge 2.1\text{ m}$ and width standards.
11. **F11 Privacy & Odor Containment**:
    - Zero direct doors between two bathrooms.
    - Zero direct doors between bedroom and kitchen.
    - Zero direct doors between formal drawing room and dirty kitchen.

---

## 5. How Frontend Calls Backend

File: `archai_frontend/archai_frontend/src/components/editor/RequirementsGenerator.jsx:395-416`
```javascript
const requestPayload = {
  prompt: promptText,
  plot_width: pw,
  plot_length: pl,
  floors: floorsCount,
  bedrooms: bedCount,
  bathrooms: bathCount,
  style: currentStyleStr.toLowerCase().includes('spanish') ? 'spanish' : 'modern',
  shape: formData.isCorner ? 'corner' : 'rectangular',
  budget_tier: 'standard',
  currency: 'PKR',
  has_plot_image: !!plotImage,
  plot_image_name: plotImage ? plotImage.name : null
};

const response = await fetch('/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(requestPayload)
});
```

---

## 6. Guidance Compatibility: What Engine Accepts vs. Drops

| Guidance from Retrieved Plan | Accepted by Engine? | Handling in Adapter |
|---|---|---|
| Plot dimensions (`width`, `depth`) | **Accepted** | Overridden if user provides explicit plot size |
| Bedroom count | **Accepted** | Overridden if user provides explicit bedroom count |
| Bathroom count | **Accepted** | Overridden if user provides explicit bathroom count |
| Floor count | **Accepted** | Overridden if user provides explicit floor count |
| Architectural Strategy archetype | **Accepted** | Mapped to closest strategy (e.g. `central_family_lounge`, `courtyard_inward_focus`) |
| Custom room dimensions | **Accepted** (`custom_room_dimensions`) | Passed for known spaces (Master Bed, Kitchen, Lounge) |
| Normalized (x,y) room coordinates | **Dropped** | Engine uses internal procedural snapping / layout solver; cannot accept arbitrary polygon coordinates |
| Wall pixel segment masks | **Dropped** | Engine generates parametric walls from CAD polygon geometry |

