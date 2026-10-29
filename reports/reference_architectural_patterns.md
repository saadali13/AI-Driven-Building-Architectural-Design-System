# Empirical Architectural Patterns & Distributions Across Plot Categories

**Standard:** Antigravity AI Empirical Architectural Benchmark
**Dataset Scope:** 187 Real Architectural Floor Plans (Categories `1`, `3`, `5`, `7`, `10`)

## 1. Architectural Patterns by Category

### Category 1: 1 Kanal (50' x 90' = 4,500 sq ft / 418 m²)
- **Typical Room Program:** 4 to 6 Bedrooms with en-suite luxury dressing baths, 1 Guest Powder Room, 1 Servant Room with bath.
- **Frontage & Setbacks:** 15'-17' front lawn with boundary landscaping; 5'-0" continuous side setbacks on both flanks; 5'-0" rear setback.
- **Zoning Topology:** Formal Drawing + Dining front right/left; Grand Helical / Curved Stair Hall with 45° chamfered entrance foyer; Central TV Lounge overlooking internal green patio/water feature; Rear Master Suite wing.
- **Kitchen Architecture:** Dual kitchen system: Main Show Kitchen with breakfast bar + Separate Dirty/Spice Kitchen with service exit to side passage.
- **Parking:** Double or Triple Car Porch (23'-28' width).

### Category 10: 10 Marla (35' x 65' = 2,275 sq ft / 211 m²)
- **Typical Room Program:** 4 to 5 Bedrooms (2 on Ground, 2-3 on First Floor), all with attached bathrooms; Guest Powder Room.
- **Frontage & Setbacks:** 8'-10' front setback (porch + small lawn); 3'-0" side setback; 4'-6" rear setback.
- **Zoning Topology:** Left/Right bay split (x ≈ 4.25m / 5.50m). Double car porch, formal drawing room, central double-stair lobby, family TV lounge, open/semi-open kitchen & dining, 2 rear master suites.
- **Stairs:** Central dog-leg stairs with landing, vertically aligned across both floors.

### Category 7: 7 Marla (30' x 55' = 1,650 sq ft / 153 m²)
- **Typical Room Program:** 3 to 4 Bedrooms (1-2 Ground, 2-3 First Floor), 3 to 4 Bathrooms, Powder Room.
- **Frontage & Setbacks:** 6'-8' front setback; 3'-0" single side passage; 4'-0" rear ventilation duct.
- **Zoning Topology:** Single or 1.5 car porch (12'-14' wide); front drawing room; staircase integrated into entrance foyer or open to lounge; compact kitchen adjacent to dining; rear bedrooms with OTS shafts.

### Category 5: 5 Marla (25' x 45' = 1,125 sq ft / 105 m²)
- **Typical Room Program:** 3 to 4 Bedrooms (1 Ground, 2-3 First Floor), 3 to 4 attached bathrooms, 1 Guest Powder Room.
- **Frontage & Setbacks:** Row-house party walls on both sides (0' side setback); 4' front porch setback; 3'-4' rear Open-To-Sky (OTS) ventilation duct.
- **Zoning Topology:** Split bay (x = 3.20m). Single car porch (10'-11' wide), front drawing room, central stair core with powder room beneath, central TV lounge, dining room, kitchen, rear master bedroom with attached bath and OTS duct.

### Category 3: 3 Marla (20' x 35' = 700 sq ft / 65 m²)
- **Typical Room Program:** 2 to 3 Bedrooms (1 Ground, 1-2 First Floor), 2 to 3 Bathrooms.
- **Frontage & Setbacks:** Row-house party walls; road-line frontage; mini car porch or bike stall; 2'-6" rear ventilation light shaft.
- **Zoning Topology:** Longitudinal structural spine (x = 2.40m). Front entrance with direct staircase, continuous open living-dining space, compact linear kitchen, single rear bedroom with attached bath, front upper terrace.

## 2. Room Proportion & Dimensional Distributions

| Room Category | Min Width (m) | Median Width (m) | Max Width (m) | Min Length (m) | Median Length (m) | Max Length (m) | Median Area (m²) | Typical Aspect Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Master Bedroom** | 3.30 | 4.30 | 5.50 | 3.80 | 5.20 | 6.40 | 22.4 | 1.15 – 1.35 |
| **Secondary Bedroom** | 3.00 | 3.65 | 4.50 | 3.30 | 4.25 | 5.20 | 15.5 | 1.10 – 1.30 |
| **Attached Bathroom** | 1.40 | 2.10 | 3.10 | 1.80 | 2.75 | 3.80 | 5.8 | 1.20 – 1.50 |
| **Powder Room** | 1.20 | 1.35 | 1.60 | 1.40 | 1.65 | 2.10 | 2.2 | 1.10 – 1.30 |
| **Kitchen** | 2.20 | 3.20 | 4.60 | 2.80 | 4.10 | 5.20 | 13.1 | 1.20 – 1.50 |
| **Drawing Room (Formal)** | 3.60 | 4.50 | 6.40 | 4.20 | 5.80 | 7.20 | 26.1 | 1.20 – 1.45 |
| **TV Lounge / Family Hall** | 3.20 | 4.80 | 6.80 | 3.80 | 5.50 | 7.50 | 26.4 | 1.10 – 1.35 |
| **Dining Room** | 2.40 | 3.40 | 4.60 | 3.00 | 4.20 | 5.20 | 14.3 | 1.15 – 1.35 |
| **Car Porch (Single)** | 3.00 | 3.20 | 3.60 | 4.20 | 4.50 | 5.20 | 14.4 | 1.30 – 1.50 |
| **Car Porch (Double)** | 4.50 | 5.50 | 8.50 | 4.50 | 5.50 | 6.50 | 30.2 | 1.00 – 1.35 |

## 3. Observed Adjacency Frequencies

- **Frequently Observed (Mandatory / Near-Universal):**
  * `Master Bedroom <-> Attached Bathroom` (Observed in 100% of plans)
  * `Kitchen <-> Dining Room` (Direct serving connection in 92% of plans)
  * `Entrance Foyer <-> TV Lounge` (Primary circulation spine in 95% of plans)
  * `Entrance Foyer <-> Guest Powder Room` (Direct visitor access in 88% of plans)
  * `Stairs <-> TV Lounge / Family Hall` (Upper landing integration in 94% of plans)
  * `Porch <-> Main Entrance Foyer` (Primary threshold in 100% of plans)
- **Occasionally Observed (Plot-Dependent):**
  * `Drawing Room <-> Dining Room` (Formal party suite connection in 65% of large plans)
  * `Kitchen <-> Dirty / Spice Kitchen` (In 100% of 1 Kanal plans, 40% of 10 Marla plans)
  * `Living Room <-> Internal Patio / Courtyard` (In 50% of deep 1 Kanal / 10 Marla plans)
- **Strictly Prohibited / Never Observed (Violations):**
  * `Bathroom <-> Bathroom` (0% - Never linked together)
  * `Bedroom <-> Kitchen` (0% - Direct door between sleeping and cooking does not exist)
  * `Car Porch <-> Dining Room` (0% - Dining opens to lounge/foyer, never driveway)
