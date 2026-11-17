# AI-Driven Building Architectural Design System

Describe a house in plain words; get checked floor plans, a front elevation, 3D views and CAD exports.

Gemini does not draw. It writes a short script that cuts the plot into rectangles. A geometry engine (no AI)
turns that script into walls, doors, windows and furniture, walks through the house the way a person would, and
sends back whatever does not work. Gemini fixes its script until the engine finds nothing wrong. Every drawing is
then produced from that one checked model, so the plans, elevation and 3D always agree.

```
 Brief ("10 marla, 3 floors, 9 bedrooms ...")
   │
   ▼
 1. Read the brief ── plot, storeys, room counts, must-haves (guided interview asks about gaps)
   ▼
 2. Layout ideas ──── Gemini proposes several different concepts
   ▼
 3. Script ────────── Gemini writes an ArchiScript, one floor at a time  ◄──────────────┐
   ▼                                                                                   │
 4. Geometry engine ─ doors on shared walls · every room reachable (never through a    │
   │                  bedroom, bath or the stair) · daylight for living rooms · stair  │
   │                  holds its steps and stacks · listed furniture fits · terraces    │
   │                  stand on something                                               │
   ▼                                                                                   │
 5. Problems? ─────── few left → line edits only · many → repair or fresh start ───────┘
   ▼ none
 6. Self-review ───── Gemini reviews its own design as an architect in Pakistan
   ▼
 7. One model ─────── floor plans · front elevation · 3D (live and images) · DXF/PDF/SVG/OBJ/PNG/Blender
   ▼
 8. Regenerate ────── "make bedroom 1 deeper" edits the same script, re-checks it, lists what
                      changed, and keeps every earlier version to go back to
```

The prompt explains how the engine works; it carries no bylaw list and no RAG. This is software CAD
validation only - not a structural certificate or a municipal building approval.

## Files

| Path | Role |
|---|---|
| `api_server.py` | HTTP API on port 8000 (generate, interview, regenerate, exports, `/output` images) |
| `generation/gemini_cad_engine.py` | Pipeline: concepts, Gemini calls, repair loop, review, drawing sheets |
| `generation/design_script.py` | ArchiScript language, parser and the prompt text |
| `generation/plan_geometry_engine.py` | Walls, doors, windows, furniture and every physical check |
| `generation/massing_render.py` | One 3D model → front elevation, 3D views, 3D data for the viewer |
| `generation/brief_parser.py`, `brief_interview.py` | Reading the brief and the guided interview |
| `config/gemini_config.py` | Model list; reads `GEMINI_API_KEY` from the environment or `.env` |
| `frontend/` | React + Vite app on port 5173 |
| `tests/test_plan_geometry_engine.py` | Engine, parser, renderer and pipeline tests (no API calls) |

## Run locally

1. Python 3.11+: `pip install -r requirements.txt`; Node 20+: `cd frontend && npm install`
2. Put your key in a `.env` file in the project root (it is git-ignored):
   `GEMINI_API_KEY=your-key-here`
3. `powershell -File start_all.ps1`, or start the two parts yourself:
   - `python api_server.py --port 8000`
   - `cd frontend && npm run dev -- --host 127.0.0.1 --port 5173`
4. Open http://127.0.0.1:5173

Tests: `python -m pytest tests/test_plan_geometry_engine.py -q`
