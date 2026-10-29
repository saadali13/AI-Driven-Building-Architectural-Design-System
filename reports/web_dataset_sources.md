# Real-World Architectural Dataset Research & Sources Report

**Date:** September 17, 2026  
**Auditor:** Lead AI/ML & Computational Geometry Engineer (Antigravity)  
**Objective:** Independent audit and evaluation of academic, open-source, and public-domain architectural floor plan and building exterior datasets to scale beyond the initial 187-image pilot collection.

---

## Executive Summary

The initial workspace pilot dataset consists of **187 floor-plan images**. While adequate for pipeline bootstrapping, schema verification, and unit tests, it is **wholly insufficient** for training production-grade computer vision models, room segmentors, or layout generation models. 

Through systematic web, academic, and open-source research, we identified and evaluated the primary global repositories of architectural floor plans, building facades, and 3D building models. Crucially, our research reveals **vital legal and licensing demarcations** that dictate which datasets can be used for commercial production versus strictly non-commercial research.

---

## Detailed Evaluation of Floor Plan Datasets

### 1. ResPlan (2025)
- **Source Name:** ResPlan (Permissive Residential Floor Plan Dataset)
- **Source URL:** https://github.com/standfest-science/resplan / https://huggingface.co/datasets/standfest-science/resplan
- **Image Count:** 17,000 floor plans
- **Floor Plan Count:** 17,000 residential units
- **Exterior Count:** 0
- **Annotation Types:** Clean vector geometry (polygons), metric-scale real-world coordinates ($m$), room semantic labels, room-connectivity adjacency graphs, boundary walls, doors, and windows.
- **License:** Permissive Open-Source (Apache 2.0 / MIT compatible)
- **Training Allowed:** Yes
- **Commercial Use:** Permitted
- **Attribution Required:** Yes (standard citation)
- **Download Method:** Direct download via Hugging Face Datasets API / Git LFS / Kaggle.
- **Data Quality & Diversity:** High. Modern residential multi-unit and single-family plans with uniform scale and verified topological boundaries.
- **Limitations:** Predominantly European modern residential layouts; lacks raw noisy raster scans (pure vector/clean raster).
- **Usefulness to Project:** **CRITICAL (P0 Core Resource)**. This is currently the largest permissively licensed dataset with clean vector geometry, metric dimensions, and spatial graphs. It avoids the legal contamination of non-commercial academic datasets.

---

### 2. CubiCasa5K
- **Source Name:** CubiCasa5K (University of Oulu & CubiCasa)
- **Source URL:** https://github.com/CubiCasa/CubiCasa5k
- **Image Count:** 5,000 real estate floor plan images
- **Floor Plan Count:** 5,000
- **Exterior Count:** 0
- **Annotation Types:** Dense vector annotations in SVG format covering 80+ architectural object categories (exterior/interior walls, doors, windows, stairs, kitchen fixtures, bathroom fixtures, furniture, room polygons).
- **License:** Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)
- **Training Allowed:** Research only (commercial training strictly restricted by original licensor)
- **Commercial Use:** **PROHIBITED** without private commercial enterprise agreement with CubiCasa.
- **Attribution Required:** Yes
- **Download Method:** Direct Git / AWS S3 archive scripts.
- **Data Quality & Diversity:** Very high real-world diversity: degraded scans, varied resolutions, architectural drafting styles, noisy artifacts.
- **Limitations:** Non-commercial restriction means weights trained directly on CubiCasa5k cannot be distributed in a proprietary commercial SaaS product.
- **Usefulness to Project:** **HIGH for Benchmark & Validation (P1)**. Serves as the golden academic benchmark for testing our CV extraction pipeline against degraded real-world scans.

---

### 3. FloorPlanCAD
- **Source Name:** FloorPlanCAD (Large-scale CAD Drawing Dataset)
- **Source URL:** https://github.com/FloorPlanCAD / https://opendatalab.com/FloorPlanCAD
- **Image Count:** 15,285 CAD drawings
- **Floor Plan Count:** 15,285
- **Exterior Count:** 0
- **Annotation Types:** Native vector CAD graphics (SVG / DXF) with line-grained annotations for 30 object categories (walls, doors, windows, furniture, stairs).
- **License:** Research / OpenDataLab Academic License
- **Training Allowed:** Research & Evaluation
- **Commercial Use:** Restricted / Unclear for commercial redistribution
- **Attribution Required:** Yes
- **Download Method:** OpenDataLab / Kaggle dataset download.
- **Data Quality & Diversity:** Authentic CAD vector graphics spanning residential, public, and commercial architectural drawings.
- **Limitations:** Primarily vector CAD drawings rather than raster photos/scans; contains commercial and industrial spaces requiring residential filtering.
- **Usefulness to Project:** **HIGH (P1)** for evaluating CAD layer generation, symbol spotting, and DXF topological consistency.

---

### 4. RPLAN
- **Source Name:** RPLAN (Data-driven Interior Plan Generation)
- **Source URL:** http://staff.ustc.edu.cn/~fuxm/projects/DeepLayout/
- **Image Count:** 80,788 floor plans
- **Floor Plan Count:** 80,788
- **Exterior Count:** 0
- **Annotation Types:** Structural boundary masks, wall masks, room masks, door positions, and room category labels.
- **License:** Non-commercial academic research only; redistribution explicitly prohibited.
- **Training Allowed:** Academic research only
- **Commercial Use:** **STRICTLY PROHIBITED**
- **Attribution Required:** Yes
- **Download Method:** Gated academic application form to original university authors.
- **Data Quality & Diversity:** Massive scale, but strictly limited to Chinese high-rise apartment floor plans. Near-zero detached single-family houses, villas, or US/European multi-storey houses.
- **Limitations:** Extreme geographical/typological bias; non-commercial restriction; gated access.
- **Usefulness to Project:** **MEDIUM (P2)**. Useful for generative layout inspiration and statistical distributions, but cannot form the training backbone of a commercial system.

---

### 5. SESYD (Systems Evaluation Synthetic Documents)
- **Source Name:** SESYD - FloorPlans Domain
- **Source URL:** http://mathieu.delalandre.free.fr/projects/sesyd/
- **Image Count:** ~284,000 synthetic document images (10 sub-collections of ~1,000 floor plans with varied degradation)
- **Floor Plan Count:** 10,000 floor plan layouts rendered at multiple noise levels
- **Exterior Count:** 0
- **Annotation Types:** Ground truth vector coordinates for 16 standard architectural symbols (doors, windows, armchairs, tables, sinks, tubs, etc.).
- **License:** Open Academic / Research
- **Training Allowed:** Yes
- **Commercial Use:** Permitted for synthetic benchmarking
- **Attribution Required:** Yes
- **Download Method:** Direct HTTP download from project repository.
- **Data Quality & Diversity:** Synthetic, clean symbol definitions with parameterized noise (scratches, ink bleeds, rotations).
- **Limitations:** Older graphical drafting style; lacks rich furniture and modern presentation colors.
- **Usefulness to Project:** **HIGH for Symbol Spotting Pretraining (P1)**. Excellent for pretraining classical and ML detectors on standardized architectural symbols without copyright ambiguity.

---

### 6. Structured3D
- **Source Name:** Structured3D (Large-scale Photorealistic Synthetic 3D Indoor Dataset)
- **Source URL:** https://structured3d-dataset.org/
- **Image Count:** 196k photorealistic renderings from 3,500 house designs
- **Floor Plan Count:** 3,500 complete residential floor plans
- **Exterior Count:** 0 (interior only)
- **Annotation Types:** Full 3D planes, line segments, junctions, 3D room bounding boxes, 2D floor plans, depth maps, and semantic segmentation masks.
- **License:** Structured3D Research License (Academic / Non-commercial)
- **Training Allowed:** Research use
- **Commercial Use:** Restricted
- **Attribution Required:** Yes
- **Download Method:** Request access form on official portal.
- **Data Quality & Diversity:** Extremely high mathematical precision. True 3D coordinate correspondence to 2D floor plan geometry.
- **Limitations:** Fully synthetic interiors; interior 3D only (no exterior facades/roofs).
- **Usefulness to Project:** **HIGH for 2D-to-3D Geometry Validation (P1)**. Perfect ground truth for testing 2D floor plan extrusion into 3D mesh representations.

---

### 7. ZInD (Zillow Indoor Dataset)
- **Source Name:** Zillow Indoor Dataset (ZInD)
- **Source URL:** https://github.com/zillow/zind
- **Image Count:** 71,474 panoramas across 1,573 real-world unfurnished residential homes
- **Floor Plan Count:** 1,573 primary floor plans + room boundary layouts
- **Exterior Count:** 0
- **Annotation Types:** Real-world residential floor plans, 2D room layouts, pinhole images, 3D room bounding boxes, door/window locations.
- **License:** CC BY-NC-SA 4.0
- **Training Allowed:** Research / Non-commercial
- **Commercial Use:** Restricted
- **Attribution Required:** Yes
- **Download Method:** AWS S3 requester-pays bucket via official GitHub registration.
- **Data Quality & Diversity:** Authentic US residential homes (single-family houses, townhomes, apartments) with real architectural layout quirks.
- **Limitations:** Non-commercial license; requires AWS credentials to download.
- **Usefulness to Project:** **HIGH (P1)** for US residential layout distribution and room adjacency ground truth.

---

## Detailed Evaluation of Exterior & Facade Datasets

### 1. CMP Facade Database (Czech Technical University)
- **Source Name:** CMP Facade Database
- **Source URL:** https://cmp.felk.cvut.cz/~tylecr1/facade/
- **Image Count:** 606 rectified facade images
- **Floor Plan Count:** 0
- **Exterior Count:** 606
- **Annotation Types:** 12 semantic classes (facade, window, door, cornice, sill, balcony, blind, pillar, deco, molding, roof, background).
- **License:** Academic Research License
- **Training Allowed:** Yes (Research)
- **Commercial Use:** Unclear / Academic provenance
- **Attribution Required:** Yes
- **Download Method:** Direct zip archive download.
- **Data Quality & Diversity:** Rectified orthogonal photos of European urban and suburban buildings.
- **Limitations:** Urban street facades; limited suburban single-family house variety.
- **Usefulness to Project:** **HIGH for Facade Grammar (P1)**. Establishes the relationship between wall openings and architectural facade elements.

---

### 2. CorbuAI & C3Po (Paired Architecture Datasets)
- **Source Name:** CorbuAI / C3Po Cross-Modality Architecture Repositories
- **Source URL:** https://github.com/rickkk856/ArchitectureDesign-DataSources
- **Image Count:** 2,335 plans paired with 1,570 elevations (CorbuAI); 90k photo-plan pairs across 597 scenes (C3Po).
- **Floor Plan Count:** 2,335
- **Exterior Count:** 1,570 elevation drawings
- **Annotation Types:** Paired 2D floor plans and 2D architectural elevation drawings.
- **License:** Research / Academic Use Only
- **Training Allowed:** Yes (Academic)
- **Commercial Use:** Restricted
- **Attribution Required:** Yes
- **Download Method:** GitHub / Academic request.
- **Data Quality & Diversity:** One of the few authentic paired architectural datasets where floor plan boundaries map to building exterior elevations.
- **Limitations:** Moderate sample size; regional styling (predominantly Chinese contemporary residential).
- **Usefulness to Project:** **CRITICAL for Cross-Modality Validation (P0)**. Directly answers how to correlate 2D floor plan exterior walls with elevation drawings without faking correspondences.

---

### 3. Open Buildings 2.5D & OpenStreetMap / CityGML Building Models
- **Source Name:** Google Open Buildings & OSM 3D Building Footprints
- **Source URL:** https://sites.research.google/open-buildings/ / https://www.openstreetmap.org/
- **Image/Record Count:** Hundreds of millions of building footprints with estimated heights ($2.5D$).
- **Annotation Types:** Vector building polygons, height in meters, roof presence.
- **License:** CC BY 4.0 / ODbL
- **Training Allowed:** Yes
- **Commercial Use:** Permitted with attribution
- **Usefulness to Project:** **P1 for Site Footprint & Setback Geometry**. Provides realistic building envelope constraints for plot-level floor plan generation.

---

## Summary Matrix of Candidate Sources

| Dataset | Modality | Samples | Annotations | License | Commercial Safe? | Primary Project Value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ResPlan (2025)** | Floor Plan (Vector) | 17,000 | Polygons, Graphs, Metric Scale | Open-Source Permissive | **YES** | **Core Training Backbone** |
| **FloorPlanCAD** | Floor Plan (CAD/SVG) | 15,285 | Line-grained Panoptic CAD | OpenDataLab Academic | Unclear | CAD & DXF layer validation |
| **CubiCasa5K** | Floor Plan (Raster/SVG) | 5,000 | 80+ classes, Polygons, Rooms | CC BY-NC 4.0 | **NO (Research Only)** | Real-world noisy scan benchmark |
| **SESYD** | Floor Plan (Synthetic) | 10,000+ | 16 standard symbols | Academic Open | Conditional | Symbol spotter pretraining |
| **Structured3D** | Floor Plan + 3D Mesh | 3,500 | 3D planes, wireframes, layouts | Academic License | **NO (Research Only)** | 2D-to-3D extrusion ground truth |
| **ZInD (Zillow)** | Floor Plan + Panos | 1,573 | Real-world US home layouts | CC BY-NC-SA 4.0 | **NO (Research Only)** | US residential layout patterns |
| **CMP Facades** | Facade (Rectified 2D) | 606 | 12 classes (windows, doors) | Academic Research | Unclear | Facade element parsing |
| **CorbuAI / C3Po**| Paired Plan + Elevation | 2,335 | Paired plan-elevation | Academic Research | **NO (Research Only)** | Ground truth for plan-to-facade |
| **Existing Pilot** | Floor Plan (Images) | 187 | None (Raw raster images) | Unverified Web Scrapes | **PILOT ONLY** | Pipeline testing & audit |
