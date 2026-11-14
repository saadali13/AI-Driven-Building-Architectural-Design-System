# Project Status & Milestone Tracker

## Phase 0: Audit & Reuse Strategy
- **Done**: Audited existing codebase, diagnosed sound vs. defective modules, established mapping to clean target architecture in `docs/audit.md`, formulated `docs/adr/0001-reuse-plan.md`, saved `PROMPT.md` and `CLAUDE.md`.
- **Could not do and why**: None. (No code was altered, as Phase 0 strictly mandates audit and planning before modification).
- **Need from user**: Approval of the reuse plan (`docs/adr/0001-reuse-plan.md` & `docs/audit.md`) at the Phase 0 Gate to proceed to Phase 1 (Foundation).

---

## Phase Roadmap Status
- [x] **Phase 0: Audit** (At Gate: awaiting approval)
- [ ] **Phase 1: Foundation** (Repo layout, config, logging, errors, DB + migrations, CI, Docker, health endpoints)
- [ ] **Phase 2: Data layer** (Loaders, JSON Schemas, data audit, SOURCES.md, D2/D3/D6 ingestion)
- [ ] **Phase 3: Rules + validator** (Rules lookup, envelope, hard validator, soft metrics, door/connectivity fixes)
- [ ] **Phase 4: Engine** (Templates, ops, candidate generation, solver, upper floors, scorer, diversity)
- [ ] **Phase 5: 2D rendering** (Symbols D7, professional drawing quality, SVG to PNG/PDF)
- [ ] **Phase 6: LLM layer** (Providers + mock, parser, refine, explain, repair, prompt files, D10 corpora)
- [ ] **Phase 7: RAG** (ChromaDB indexes, hybrid retrieval, citations, plan-card ranking)
- [ ] **Phase 8: Elevation, roof, 3D** (Style presets D8, SVG elevation, roof plan, GLB + scene JSON, textures D9)
- [ ] **Phase 9: Cost** (D4/D5 ingestion, takeoff, estimator, validation against real costs)
- [ ] **Phase 10: Exports** (DXF, SVG, PNG, JPG, PDF, GLB, OBJ, STL, IFC, JSON, ZIP)
- [ ] **Phase 11: API, jobs, versions** (All endpoints, jobs + SSE, history/undo, feedback, auth, frontend connection)
- [ ] **Phase 12: Evaluation and hardening** (make eval, architect pack, performance, security pass, docs, viva notes)
