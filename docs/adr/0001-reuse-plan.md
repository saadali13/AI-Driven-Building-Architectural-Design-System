# ADR 0001: Subsystem Reuse, Modularization, and Migration Plan

**Status**: Proposed (Awaiting Phase 0 Gate Approval)  
**Date**: 2026-11-14  
**Deciders**: Project Owner, Autonomous Software Engineering Agent  

---

## Context
The project requires building a complete, production-grade backend for an AI-driven Pakistani residential architectural design system. A previous external audit scored the legacy codebase at 22/100, citing monolithic coupling, broken dependencies from deleted extraction pipelines, FAISS binary crashes on Windows, and inconsistent validation enforcement.

However, the repository contains substantial, high-value architectural algorithms:
- `generation/door_clearance_engine.py`: Sophisticated geometric door swept-arc collision detection against furniture and vehicles.
- `generation/floor_plan_to_elevation_mapper.py`: Mathematically synchronized 1:1 floor-plan-to-facade projection.
- `layout_engine/edit_ops.py`: Pure functional room edit operations for slicing structures.
- `cad/dxf_generator.py`: Complete layered AIA AutoCAD DXF export.
- `frontend/`: Modern, responsive React 19 + TypeScript + Vite UI.

Re-writing everything from scratch would discard these verified geometric implementations and waste weeks. Conversely, leaving the current monolithic structure in `api_server.py` would prevent clean testing, OpenAPI generation, and proper neuro-symbolic separation.

---

## Decision

We will adopt a **measured reuse and migration strategy** following the architecture defined in `PROMPT.md`:

1. **Clean Modular Target (`backend/app/`)**:
   - Establish the target FastAPI package structure under `backend/app/` with strict domain separation (`domain/spec`, `domain/rules`, `domain/templates`, `domain/engine`, `domain/validate`, `domain/score`, `domain/render`, `domain/model3d`, `domain/cost`, `domain/export`).
2. **Direct Algorithmic Reuse**:
   - Directly port and integrate the sound geometric modules:
     - `generation/door_clearance_engine.py` & `generation/spatial_validator.py` $\rightarrow$ `app/domain/validate/hard.py`.
     - `layout_engine/edit_ops.py` $\rightarrow$ `app/domain/engine/ops.py`.
     - `generation/floor_plan_to_elevation_mapper.py` $\rightarrow$ `app/domain/render/elevation_svg.py`.
     - `cad/dxf_generator.py` $\rightarrow$ `app/domain/export/dxf.py`.
3. **Refactor and Isolate**:
   - Refactor `requirements/parser.py` into `app/domain/spec/` to support English, Urdu, and Roman Urdu with strict Pydantic v2 schemas and single-question missing info clarification.
   - Refactor cost estimation to read from `data/costs/rates.csv` and `data/costs/boq_factors.csv` rather than hardcoded heuristics.
   - Replace unstable Windows FAISS bindings with `ChromaDB` (persistent) + `sentence-transformers` (`BAAI/bge-m3`) + `rank_bm25` hybrid reciprocal rank fusion.
4. **Adapter Compatibility with Active Frontend**:
   - Maintain full backwards compatibility with the active React frontend (`frontend/`) by ensuring all API response structures, endpoints, and field names continue to function seamlessly behind FastAPI route adapters.
5. **No Model Training (Neuro-Symbolic Guarantee)**:
   - Enforce that the LLM only generates schema-validated edit operations or parses requirements; the deterministic parametric engine alone calculates all physical geometry and room coordinates.

---

## Consequences

### Positive
- **Rapid Acceleration**: Reuses over 4,000 lines of mathematically verified geometric CAD logic instead of rebuilding from scratch.
- **Stability & Clean CI**: Replaces brittle monolithic scripts with typed, testable, modular FastAPI services.
- **Windows Portability**: Eliminates C++ AVX2 binary crashes from FAISS; standardizes cross-platform tasks in `tasks.py`.
- **Zero Hallucination Guarantee**: All regulatory numbers come from cited tables (`data/rules/rules_table.csv`), never invented by an LLM.

### Negative / Trade-offs
- Requires migrating legacy tests that import purged CV/extraction directories.
- Legacy `api_server.py` will be kept as a transitional reference while `backend/app/` is validated in Phase 1.
