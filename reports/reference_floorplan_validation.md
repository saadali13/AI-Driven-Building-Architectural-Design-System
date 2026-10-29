# Reference Floor Plan Validation & Current Failure Case Report

**Standard:** Antigravity Plan Validation & Failure Diagnosis
**Benchmark Source:** 187 Real Architectural Plans

## 1. Failure Case Diagnosis of the Previous Generated Floor Plan

The previously generated floor plan was subjected to rigorous architectural auditing against real benchmark blueprints. It exhibited the following critical failure modes:

| Failure Code | Failure Type | Root Cause in Previous Pipeline | Real Benchmark Counter-Proof |
| :--- | :--- | :--- | :--- |
| **F01 / F02** | Room Count & Missing Room | The requirement parser extracted rooms as soft keywords rather than immutable program nodes, causing room count drift between prompt and geometry. | Real plans have exact room counts matching the project title schedule. |
| **F05 / F06** | Master Bathroom Attachment | An attached bathroom label was placed adjacent to a bedroom, but the boundary was not verified as an exclusive shared 1D segment with a dedicated private door. | In real blueprints, every attached bathroom shares a physical wall with its bedroom and has an interior private door. |
| **F08** | Door Placement on Wall | Automatic door generation loops placed doors on all intersecting walls, creating cross-bathroom and bedroom-to-kitchen connections. | Real plans place doors strictly according to circulation hierarchy (public $\rightarrow$ semi-private $\rightarrow$ private). |
| **F09** | Window on Interior Wall | Windows were placed based on polygon edges without checking distance to the exterior envelope, risking windows on interior partitions. | Real plans place windows strictly along exterior facades or open-to-sky (OTS) shafts. |
| **F10** | Staircase Alignment | Upper floor stairs landed without verifying that the mid-landing and flight geometry matched the lower floor coordinates. | Real plans feature identical $(X, Y)$ stair bounding boxes on Ground and First floors. |
| **F16** | Label / Geometry Contradiction | Text labels displayed area strings that did not calculate directly from polygon vertices. | Real architectural CAD drawings calculate dimensions and areas directly from physical geometry. |
| **F17** | Decorative Infographic Obfuscation | The visualizer used colorful fills and large callout boxes that concealed boundary defects rather than cleanly communicating construction geometry. | Real blueprints use solid wall hierarchy ($0.30\text{mm}$ exterior, $0.15\text{mm}$ interior) and thin vector symbols. |

## 2. Validation Harness Against Benchmark Exemplars

To verify the upgraded pipeline, five distinct real-world test cases are established:
1. **TEST 1 (5 Marla Single-Storey):** 3 beds, 2 baths, master attached bath.
2. **TEST 2 (5 Marla Double-Storey):** 4 beds, 4 attached baths, powder room, single garage, kitchen, dining, TV lounge.
3. **TEST 3 (10 Marla Double-Storey):** 5 beds, attached baths, drawing, dining, kitchen, TV lounge, double garage.
4. **TEST 4 (1 Kanal Luxury Estate):** 5 beds, attached baths, drawing, dining, double kitchen, patio courtyard, double garage.
5. **TEST 5 (Infeasible Program Detection):** Impossible single-storey program $\rightarrow$ must return `INFEASIBLE_PROGRAM`.
