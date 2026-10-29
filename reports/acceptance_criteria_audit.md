# Acceptance Criteria & Metric Architecture Audit

**Document:** `reports/acceptance_criteria_audit.md`  
**Date:** September 17, 2026  
**Auditor:** Antigravity System Architecture Team  

---

## 1. Executive Critique: The Fallacy of Absolute Acceptance Criteria

In engineering specifications, absolute claims such as `"100% polygon closure"`, `"100% deterministic parsing"`, and `"100% rejection of invalid plans"` appear rigorous on paper but are **technically flawed in real-world computer vision and computational geometry**. 

When confronted with ambiguous user prompts, noisy 200px scanned drawings, or non-convex curved walls, an absolute 100% threshold either:
1. Causes the pipeline to fail and abort on nearly all authentic real-world assets, or
2. Encourages engineers to fabricate or overfit synthetic test cases that pass artificially.

Below is the independent engineering audit challenging every V2 acceptance criterion and replacing brittle absolutes with **defensible, mathematically measurable engineering tolerances**.

---

## 2. Audit and Correction of Brittle Acceptance Criteria

### Criterion 1: "Polygon Closure = 100%"
* **V2 Assertion:** "All rooms are valid closed Shapely polygons (100%)."
* **Technical Reality:** On raw noisy scans with missing wall lines, broken lines, or open-plan living/dining areas without physical dividers, forcing 100% closed polygons on raw extraction produces self-intersecting or invalid topological geometries.
* **Measurable Dataset & Baseline:** Evaluated against the **Golden 50 Benchmark** and **ResPlan Vector Test Split**.
* **Realistic Engineering Threshold:**
  - **Golden Benchmark:** $\ge 98\%$ of extracted room polygons must be topologically valid (`is_valid == True`, closed exterior ring, zero self-intersections).
  - **Raw Web Scans:** On noisy scans, extract candidate polygons with a confidence threshold. Any polygon failing topological validation is tagged as `unclosed_boundary` (confidence $<0.5$) and rejected downstream rather than crashing the pipeline.
  - **Tolerance:** Polygon simplification tolerance $\epsilon = 2.0$ px; angle orthogonalization snapped if $| \theta - 90^\circ | \le 5^\circ$.

---

### Criterion 2: "100% Deterministic Requirement Parsing"
* **V2 Assertion:** "100% deterministic output: always produces valid constraint JSON."
* **Technical Reality:** Natural language contains inherently subjective, ambiguous, or contradictory statements (e.g. *"I want a huge master bedroom but the house must fit in 500 sq ft"*). Claiming 100% deterministic understanding conflates **JSON schema validity** with **architectural semantic correctness**.
* **Measurable Dataset & Baseline:** Test suite of 100 synthetic and real-world natural language prompts.
* **Realistic Engineering Threshold:**
  - **Syntactic Validity:** $100\%$ of outputs strictly validate against `RequirementSpecification` Pydantic schema (enforced by deterministic schema validation layer).
  - **Semantic Accuracy:** $\ge 95\%$ correct extraction of explicit quantitative facts (room counts, numeric plot dimensions, floor counts).
  - **Ambiguity Classification:** $100\%$ of subjective terms (*"large"*, *"airy"*, *"modern"*) are explicitly mapped to quantified defaults or categorized as `soft_preference` rather than fabricated hard numbers.

---

### Criterion 3: "Rejection of Invalid Generated Plans = 100%"
* **V2 Assertion:** "Rejects 100% of plans with room overlaps, orphan rooms, or inaccessible spaces."
* **Technical Reality:** "Validity" must be decoupled into formal mathematical layers. While geometric non-overlap can be checked deterministically with Shapely, architectural accessibility depends on door graph traversal, and code compliance requires regional jurisdiction rules.
* **Measurable Dataset & Baseline:** 500 candidate layouts generated across varied plot sizes.
* **Realistic Engineering Threshold:**
  - **Geometric Sanity:** $100\%$ rejection of plans with room intersection area $> 0.001\text{ m}^2$ or out-of-boundary vertices.
  - **Circulation Accessibility:** $100\%$ rejection of orphan rooms (every room must have a graph path to the main entrance).
  - **Dimensional Bounds:** $\ge 99\%$ satisfaction of minimum room dimension constraints ($W \ge 2.4\text{m}$ for bedrooms, $W \ge 1.5\text{m}$ for bathrooms).
  - **Code Compliance:** Labeled explicitly as `unverified_for_local_code` until jurisdictional zoning modules are added.

---

### Criterion 4: "100% Facade Opening Alignment"
* **V2 Assertion:** "Facade openings 100% geometrically aligned with 2D floor plan exterior windows and doors."
* **Technical Reality:** While 2D exterior wall openings map directly to 3D X/Y coordinates, vertical Z placement (sill height, window head height, lintels) cannot be derived from a 2D floor plan alone.
* **Realistic Engineering Threshold:**
  - **Horizontal (X, Y) Alignment:** $100\%$ collinearity with 2D wall opening coordinates.
  - **Vertical (Z) Parameterization:** Standardized architectural height parameters: window sill at $+0.9\text{m}$, window head at $+2.1\text{m}$, door head at $+2.1\text{m}$, ceiling height at $+2.8\text{m}$.

---

### Criterion 5: "Full End-to-End Pipeline in < 60 Seconds"
* **V2 Assertion:** "Full end-to-end flow executes in $<60$ seconds."
* **Technical Reality:** On CPU without hardware acceleration, running deep OCR (EasyOCR CRAFT + LSTM) on a $2000 \times 2000$ image takes ~15–25 seconds; OR-Tools CP-SAT solver can take 10–30 seconds on complex multi-room constraints; headless Blender rendering can take 20–40 seconds. On a low-end CPU, total time can exceed 60s.
* **Realistic Engineering Threshold:**
  - **Extraction Stage:** $<20$ seconds on CPU, $<5$ seconds on GPU.
  - **Solver Stage:** Hard timeout set to $15$ seconds in OR-Tools (`solver.parameters.max_time_in_seconds = 15.0`).
  - **CAD Generation:** $<2$ seconds via ezdxf.
  - **3D Generation & Headless Render:** $<30$ seconds in Blender (low sample EEVEE render for rapid preview; Cycles reserved for offline final renders).
  - **Total Pipeline Target:** $<45$s on GPU / $<90$s on CPU.

---

## 3. The 5-Layer Architectural Metric Hierarchy

To avoid confusing model accuracy with application validity, the system enforces five strictly separated metric tiers:

```
[Layer 1: Vision Metrics]
       │ (Precision, Recall, IoU, CER, mAP)
       ▼
[Layer 2: Geometry Metrics]
       │ (Polygon validity, Non-overlap, Planar closure, Orthogonal alignment)
       ▼
[Layer 3: Semantic Metrics]
       │ (Room classification accuracy, Ensuite detection, Dimension normalization)
       ▼
[Layer 4: Graph Metrics]
       │ (Graph edit distance, Adjacency precision, Doorway path connectivity)
       ▼
[Layer 5: End-to-End Requirement Metrics]
         (Constraint satisfaction %, Area budget delta, Circulation efficiency)
```

### Layer 1: Vision Metrics
* **Text Character Error Rate (CER)**: $\le 8\%$ on plans with resolution $\ge 800$px.
* **Wall Mask Mean Intersection-over-Union (mIoU)**: $\ge 0.75$ against ground-truth vector masks.
* **Door / Window Detection F1-Score**: $\ge 0.80$ on standard architectural symbols.

### Layer 2: Geometry Metrics
* **Polygon Validity Rate**: $100\%$ valid Shapely geometries (invalid geometries discarded or repaired).
* **Room Overlap Ratio**: $0.00\%$ area overlap among interior rooms.
* **Shared-Wall Collinearity**: Adjacent rooms must share identical vertex sequences for common wall segments ($\text{Hausdorff distance} < 0.05\text{m}$).

### Layer 3: Semantic Metrics
* **Room Classification Accuracy**: $\ge 90\%$ on plans containing readable text labels; $\ge 70\%$ on unlabelled plans using geometric area and fixture heuristics.
* **Ensuite Bathroom Attachment Accuracy**: $\ge 95\%$ correct classification of attached master bathrooms.
* **Dimension Parsing Precision**: $\ge 90\%$ valid numeric conversions without unit corruption.

### Layer 4: Graph Metrics
* **Graph Node Recovery**: $\ge 92\%$ of ground-truth functional rooms represented as graph nodes.
* **Adjacency Edge F1-Score**: $\ge 88\%$ correct `adjacent_to` relationship predictions.
* **Circulation Connectivity**: $100\%$ of generated plans must have a connected path between all habitable rooms and the primary entrance.

### Layer 5: End-to-End Requirement Metrics
* **Hard Constraint Satisfaction Rate**: $100\%$ of valid generated candidates must satisfy all hard constraints (bedroom count, bathroom count, plot envelope).
* **Area Budget Compliance**: Total generated floor area within $\pm 5\%$ of user target area.
* **Candidate Diversity**: Generating 3 candidates must exhibit minimum spatial variation (Jaccard dissimilarity of room placement $>0.30$).
