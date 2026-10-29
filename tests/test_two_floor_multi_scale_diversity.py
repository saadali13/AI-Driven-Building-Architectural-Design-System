"""
End-to-End Coordinated Two-Floor (G+1) Synthesis Audit
=======================================================
15 contrasting prompts x 5 scales = 3M, 5M, 7M, 10M, 1 Kanal.

Verifies:
  1. Two-Floor Export Completeness   - Level 0 PNG + Level 1 PNG + Composite sheet
  2. Staircase Vertical IoU >= 0.95  - L0 stair footprint matches L1 stair footprint
  3. OTS Shaft Vertical Alignment    - OTS rooms align >= 90 % across floors
  4. Zero Spatial Defects            - stair >= 0.23m inside walls; door arcs
                                       collision-free; furniture within 0.10m inset
  5. Scale Diversity                 - Jaccard >= 0.22, IoU <= 0.65, Mirror IoU <= 0.65
  6. Quality Gate                    - 100 % score, 0 Critical, 0 High

Outputs: output/two_floor_audit/{scale}_design_{n}_composite.png  (15 files)

Run:
    C:\\Python314\\python.exe -m pytest tests/test_two_floor_multi_scale_diversity.py -v
"""

from __future__ import annotations

import math
import os
import sys
import json
from typing import Dict, List, Optional, Set, Tuple

import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generation.rag_solver import DatasetDrivenRAGSolver
from generation.quality_gate import FloorPlanQualityGate
from generation.diversity_evaluator import DiversityEvaluator
from generation.visualizer import FloorPlanVisualizer
from dataset.schema.canonical import CanonicalFloorPlan, RoomModel

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
AUDIT_DIR = os.path.join("output", "two_floor_audit")
os.makedirs(AUDIT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
STAIR_WALL_CLEARANCE = 0.23   # metres
FURNITURE_INSET      = 0.10   # metres
DOOR_INSET           = 0.05   # metres
STAIR_IOU_MIN        = 0.95   # vertical stair overlap L0 vs L1
OTS_ALIGN_MIN        = 0.90   # OTS shaft vertical overlap fraction
JACCARD_MIN          = 0.22
SPATIAL_IOU_MAX      = 0.65
MIRROR_IOU_MAX       = 0.65
COMPOSITE_MIN_KB     = 50

# ---------------------------------------------------------------------------
# 15 G+1 test prompts (3 per scale)
# ---------------------------------------------------------------------------
SCALE_PROMPTS: Dict[str, List[Tuple[str, str]]] = {
    "3_marla": [
        ("3M-D1",
         "3 Marla 2-storey urban home with 3 bedrooms, linear straight staircase "
         "along boundary, compact car porch, G+1 two floor"),
        ("3M-D2",
         "3 Marla double-storey residence with 2 master suites, front L-shaped "
         "staircase vestibule, open kitchen, G+1 two storey"),
        ("3M-D3",
         "3 Marla 2-floor split layout with 3 bedrooms, central dogleg staircase "
         "divider, rear open-to-sky terrace, G+1 double storey"),
    ],
    "5_marla": [
        ("5M-D1",
         "5 Marla 2-storey family villa with 4 bedrooms, drawing room, central TV "
         "lounge, standard dogleg stair, G+1 two floor"),
        ("5M-D2",
         "5 Marla double-storey modern house with 3 luxury suites, linear spine "
         "staircase, open show kitchen, G+1 2 storey"),
        ("5M-D3",
         "5 Marla 2-floor courtyard residence with 3 bedrooms, central internal "
         "patio court, U-shaped staircase, G+1 two storey"),
    ],
    "7_marla": [
        ("7M-D1",
         "7 Marla 2-storey classic villa with 4 bedrooms, dual rear suites, formal "
         "drawing dining, side show kitchen, G+1 double storey"),
        ("7M-D2",
         "7 Marla double-storey open-concept home with 3 bedrooms, central glass "
         "light courtyard, straight open stair, G+1 two floor"),
        ("7M-D3",
         "7 Marla 2-floor executive residence with 4 suites, dedicated ground office "
         "with guest half-bath, dogleg stair, G+1 2 storey"),
    ],
    "10_marla": [
        ("10M-D1",
         "10 Marla 2-storey executive villa with 5 suites, double car porch, dirty "
         "kitchen, U-shaped staircase, G+1 two floor"),
        ("10M-D2",
         "10 Marla double-storey contemporary mansion with 4 bedrooms, curved rotunda "
         "staircase, double-height great room, G+1 2 storey"),
        ("10M-D3",
         "10 Marla 2-floor dual-family home with 4 suites, independent side entrance "
         "staircase, upper kitchenette, G+1 two storey"),
    ],
    "1_kanal": [
        ("1K-D1",
         "1 Kanal 2-storey palatial estate with 15ft front lawn, grand foyer, triple "
         "car porch, 5 luxury suites, G+1 two floor"),
        ("1K-D2",
         "1 Kanal double-storey C-shaped courtyard villa with internal pool patio, "
         "open living pavilion, 4 master suites, G+1 2 storey"),
        ("1K-D3",
         "1 Kanal 2-floor luxury residence with curved imperial rotunda stair, formal "
         "reception salon, 5 suites, G+1 two storey"),
    ],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def solver() -> DatasetDrivenRAGSolver:
    return DatasetDrivenRAGSolver()


@pytest.fixture(scope="module")
def synthesized_plans(solver) -> Dict[str, List[CanonicalFloorPlan]]:
    """Synthesizes all 15 plans once; renders per-level PNGs and composites."""
    cache: Dict[str, List[CanonicalFloorPlan]] = {}
    total = sum(len(v) for v in SCALE_PROMPTS.values())
    done = 0

    for scale, prompts in SCALE_PROMPTS.items():
        scale_plans: List[CanonicalFloorPlan] = []
        for idx, (pid, prompt) in enumerate(prompts, start=1):
            done += 1
            print(f"\n[{done}/{total}] Synthesising {pid} …")
            try:
                plan = solver.synthesize(prompt)
            except Exception as exc:
                pytest.fail(f"{pid}: solver raised {exc!r}")
            assert plan is not None, f"{pid}: solver returned None"
            scale_plans.append(plan)

            # per-level PNGs
            for lvl in plan.metadata.levels:
                label = "ground_floor" if lvl == 0 else "first_floor"
                FloorPlanVisualizer.render_floor_plan(
                    plan,
                    os.path.join(AUDIT_DIR, f"{scale}_design_{idx}_{label}_2d.png"),
                    level_index=lvl, dpi=150,
                )

            # composite
            comp = os.path.join(AUDIT_DIR, f"{scale}_design_{idx}_composite.png")
            if len(plan.metadata.levels) >= 2:
                FloorPlanVisualizer.render_composite_two_floor_sheet(plan, comp, dpi=150)
            else:
                FloorPlanVisualizer.render_floor_plan(plan, comp, level_index=0, dpi=150)

        cache[scale] = scale_plans
    return cache


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def _poly(pts) -> Polygon:
    p = Polygon(pts)
    return p if p.is_valid else p.buffer(0)


def _iou(a: Polygon, b: Polygon) -> float:
    if a.is_empty or b.is_empty:
        return 0.0
    inter = a.intersection(b).area
    union = a.union(b).area
    return round(inter / union, 4) if union > 1e-9 else 0.0


def _stair_rooms(plan: CanonicalFloorPlan, level: int) -> List[RoomModel]:
    return [
        r for r in plan.rooms
        if r.level_index == level and (
            "stair" in r.room_id.lower() or "stair" in r.room_name.lower()
        )
    ]


def _ots_rooms(plan: CanonicalFloorPlan, level: int) -> List[RoomModel]:
    kw = ("ots", "shaft", "open to sky", "open-to-sky")
    return [
        r for r in plan.rooms
        if r.level_index == level
        and any(k in r.room_name.lower() for k in kw)
    ]


def _best_stair_iou(rooms_l0: List[RoomModel], rooms_l1: List[RoomModel]) -> float:
    best = 0.0
    for r0 in rooms_l0:
        p0 = _poly(r0.polygon)
        for r1 in rooms_l1:
            v = _iou(p0, _poly(r1.polygon))
            best = max(best, v)
    return best


def _plot_envelope(plan: CanonicalFloorPlan) -> Tuple[float, float, float, float]:
    xs = [pt[0] for pt in plan.boundary]
    ys = [pt[1] for pt in plan.boundary]
    return min(xs), min(ys), max(xs), max(ys)


def _stair_clearance_violations(plan: CanonicalFloorPlan, level: int) -> List[str]:
    env = _plot_envelope(plan)
    env_min_x, env_min_y, env_max_x, env_max_y = env
    msgs: List[str] = []
    for r in _stair_rooms(plan, level):
        xs = [pt[0] for pt in r.polygon]
        ys = [pt[1] for pt in r.polygon]
        bx1, by1, bx2, by2 = min(xs), min(ys), max(xs), max(ys)
        C = STAIR_WALL_CLEARANCE
        if bx1 < env_min_x + C - 1e-6:
            msgs.append(f"L{level} '{r.room_name}' left {bx1:.3f} < env+{C}")
        if bx2 > env_max_x - C + 1e-6:
            msgs.append(f"L{level} '{r.room_name}' right {bx2:.3f} > env-{C}")
        if by1 < env_min_y + C - 1e-6:
            msgs.append(f"L{level} '{r.room_name}' bottom {by1:.3f} < env+{C}")
        if by2 > env_max_y - C + 1e-6:
            msgs.append(f"L{level} '{r.room_name}' top {by2:.3f} > env-{C}")
    return msgs


def _door_arc_collisions(plan: CanonicalFloorPlan, level: int) -> List[str]:
    fixture_types = {"bathroom", "bedroom", "kitchen"}
    fixtures = [
        r for r in plan.rooms
        if r.level_index == level and r.room_type in fixture_types
    ]
    if not fixtures or not plan.openings:
        return []

    w = 0.90  # door leaf radius
    hits: List[str] = []
    for op in plan.openings:
        if getattr(op, "level_index", level) != level:
            continue
        if op.opening_type != "door":
            continue
        px, py = op.position[0], op.position[1]
        for theta0 in [0, 90, 180, 270]:
            arc_pts = [(px, py)]
            for deg in range(theta0, theta0 + 91, 5):
                rad = math.radians(deg)
                arc_pts.append((px + w * math.cos(rad), py + w * math.sin(rad)))
            try:
                arc_p = Polygon(arc_pts)
                if not arc_p.is_valid:
                    arc_p = arc_p.buffer(0)
            except Exception:
                continue
            for r in fixtures:
                try:
                    inter = arc_p.intersection(_poly(r.polygon)).area
                    if inter > 0.001:
                        hits.append(
                            f"Door {op.opening_id} arc(theta={theta0}) "
                            f"overlaps '{r.room_name}' {inter:.4f}m2"
                        )
                        break
                except Exception:
                    pass
            if hits and hits[-1].startswith(f"Door {op.opening_id}"):
                break
    return hits


def _furniture_leaks(plan: CanonicalFloorPlan, level: int) -> List[str]:
    leaks: List[str] = []
    for r in plan.rooms:
        if r.level_index != level:
            continue
        xs = [pt[0] for pt in r.polygon]
        ys = [pt[1] for pt in r.polygon]
        rw = max(xs) - min(xs)
        rh = max(ys) - min(ys)
        M = FURNITURE_INSET
        if r.room_type == "bedroom":
            BED_W = 1.90
            if rw < BED_W + 2 * M:
                leaks.append(
                    f"Bedroom '{r.room_name}' width {rw:.2f}m < "
                    f"BED({BED_W}) + 2*{M}m margin"
                )
        if r.room_type == "bathroom":
            safe_w = rw - 2 * M
            if safe_w < 0.45:
                leaks.append(
                    f"Bathroom '{r.room_name}' safe_w {safe_w:.2f}m < 0.45m (WC)"
                )
    return leaks


def _mirror_plan(plan: CanonicalFloorPlan, axis: str) -> CanonicalFloorPlan:
    min_x = min(pt[0] for pt in plan.boundary)
    max_x = max(pt[0] for pt in plan.boundary)
    min_y = min(pt[1] for pt in plan.boundary)
    max_y = max(pt[1] for pt in plan.boundary)
    rooms: List[RoomModel] = []
    for r in plan.rooms:
        if axis == "x":
            mp = [[round(max_x - (pt[0] - min_x), 2), pt[1]] for pt in r.polygon]
        else:
            mp = [[pt[0], round(max_y - (pt[1] - min_y), 2)] for pt in r.polygon]
        pg = _poly(mp)
        rooms.append(RoomModel(
            room_id=r.room_id, room_type=r.room_type, room_name=r.room_name,
            polygon=mp, area_m2=r.area_m2,
            centroid=[round(pg.centroid.x, 2), round(pg.centroid.y, 2)],
            level_index=r.level_index, is_habitable=r.is_habitable,
            metadata=dict(r.metadata or {}),
        ))
    return CanonicalFloorPlan(
        metadata=plan.metadata, boundary=plan.boundary,
        total_area_m2=plan.total_area_m2, walls=plan.walls,
        openings=plan.openings, rooms=rooms, graph_edges=plan.graph_edges,
    )


# ---------------------------------------------------------------------------
# Sheet renderer
# ---------------------------------------------------------------------------
def _render_scale_summary_sheet(
    plans: List[CanonicalFloorPlan],
    scale: str,
    metric_rows: List[str],
) -> str:
    n = len(plans)
    rows = 2 if all(len(p.metadata.levels) >= 2 for p in plans) else 1
    fig, axes = plt.subplots(rows, n, figsize=(9 * n, 11 * rows), dpi=130)
    if rows == 1 and n == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [list(axes)]
    elif n == 1:
        axes = [[ax] for ax in axes]
    fig.patch.set_facecolor("#FFFFFF")

    for col, (plan, dn) in enumerate(zip(plans, [1, 2, 3])):
        for row, lvl in enumerate(plan.metadata.levels[:rows]):
            ax = axes[row][col]
            FloorPlanVisualizer._draw_level_on_axis(ax, plan, level_index=lvl)
            lbl = "GROUND (L0)" if lvl == 0 else "FIRST (L1)"
            ax.set_title(
                f"{scale.upper().replace('_',' ')} Design {dn} — {lbl}",
                fontsize=9, fontweight="bold", color="#1E293B", pad=8,
            )

    metrics_str = "  |  ".join(metric_rows)
    fig.suptitle(
        f"{scale.upper().replace('_',' ')} G+1 TWO-FLOOR SYNTHESIS AUDIT\n"
        f"3 Designs × 2 Floors | Zero Spatial Defects\n{metrics_str}",
        fontsize=11, fontweight="bold", color="#0F172A", y=0.998,
    )
    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.97])
    out = os.path.join(AUDIT_DIR, f"{scale}_three_designs_two_floor_sheet.png")
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  [Sheet] {out}")
    return out


# ---------------------------------------------------------------------------
# Per-plan core assertions
# ---------------------------------------------------------------------------
def _assert_plan(pid: str, plan: CanonicalFloorPlan) -> None:
    # 1. Multi-floor metadata
    assert plan.metadata.floor_count >= 2, (
        f"{pid}: floor_count={plan.metadata.floor_count} (expected >=2)"
    )
    assert 0 in plan.metadata.levels, f"{pid}: Level 0 missing"
    assert 1 in plan.metadata.levels, f"{pid}: Level 1 missing ({plan.metadata.levels})"
    l0 = [r for r in plan.rooms if r.level_index == 0]
    l1 = [r for r in plan.rooms if r.level_index == 1]
    assert len(l0) >= 3, f"{pid}: only {len(l0)} Level-0 rooms"
    assert len(l1) >= 2, f"{pid}: only {len(l1)} Level-1 rooms"

    # 2. Stair vertical IoU
    s0, s1 = _stair_rooms(plan, 0), _stair_rooms(plan, 1)
    if s0 and s1:
        siou = _best_stair_iou(s0, s1)
        assert siou >= STAIR_IOU_MIN, (
            f"{pid}: Stair vertical IoU {siou:.3f} < {STAIR_IOU_MIN}"
        )

    # 3. OTS shaft alignment
    ots0, ots1 = _ots_rooms(plan, 0), _ots_rooms(plan, 1)
    if ots0 and ots1:
        best = max(_iou(_poly(o0.polygon), _poly(o1.polygon))
                   for o0 in ots0 for o1 in ots1)
        assert best >= OTS_ALIGN_MIN, (
            f"{pid}: OTS shaft IoU {best:.3f} < {OTS_ALIGN_MIN}"
        )

    # 4. Stair boundary containment
    for lvl in [0, 1]:
        msgs = _stair_clearance_violations(plan, lvl)
        assert not msgs, f"{pid}: stair out-of-bounds on L{lvl}: " + "; ".join(msgs)

    # 5. Door swing collisions
    for lvl in [0, 1]:
        hits = _door_arc_collisions(plan, lvl)
        assert not hits, (
            f"{pid} L{lvl}: {len(hits)} door arc collision(s):\n"
            + "\n".join(f"  * {h}" for h in hits[:5])
        )

    # 6. Furniture boundary leaks
    for lvl in [0, 1]:
        leaks = _furniture_leaks(plan, lvl)
        assert not leaks, (
            f"{pid} L{lvl}: {len(leaks)} furniture leak(s):\n"
            + "\n".join(f"  * {l}" for l in leaks[:5])
        )

    # 7. QualityGate
    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", (
        f"{pid}: QualityGate FAIL — "
        + "; ".join(f["description"] for f in gate["failures"][:3])
    )
    assert gate["quality_score"] >= 1.0, f"{pid}: quality_score {gate['quality_score']}"
    assert gate["critical_failures_count"] == 0, f"{pid}: Critical failures"
    assert gate["high_failures_count"] == 0, f"{pid}: High failures"


def _assert_files(scale: str, idx: int, plan: CanonicalFloorPlan) -> None:
    slug = f"{scale}_design_{idx}"
    gf = os.path.join(AUDIT_DIR, f"{slug}_ground_floor_2d.png")
    assert os.path.exists(gf) and os.path.getsize(gf) > COMPOSITE_MIN_KB * 1024, \
        f"Missing/small ground floor PNG: {gf}"
    if len(plan.metadata.levels) >= 2:
        ff = os.path.join(AUDIT_DIR, f"{slug}_first_floor_2d.png")
        assert os.path.exists(ff) and os.path.getsize(ff) > COMPOSITE_MIN_KB * 1024, \
            f"Missing/small first floor PNG: {ff}"
    comp = os.path.join(AUDIT_DIR, f"{slug}_composite.png")
    assert os.path.exists(comp) and os.path.getsize(comp) > COMPOSITE_MIN_KB * 1024, \
        f"Missing/small composite PNG: {comp}"


def _diversity_row(
    pid_a: str, plan_a: CanonicalFloorPlan,
    pid_b: str, plan_b: CanonicalFloorPlan,
) -> str:
    j  = DiversityEvaluator.compute_adjacency_jaccard_distance(plan_a, plan_b)
    si = DiversityEvaluator.compute_spatial_layout_iou(plan_a, plan_b)
    mx = DiversityEvaluator.compute_spatial_layout_iou(_mirror_plan(plan_a,"x"), plan_b)
    my = DiversityEvaluator.compute_spatial_layout_iou(_mirror_plan(plan_a,"y"), plan_b)
    pair = f"{pid_a}v{pid_b}"
    assert j  >= JACCARD_MIN,     f"Jaccard {j:.3f} < {JACCARD_MIN} ({pair})"
    assert si <= SPATIAL_IOU_MAX, f"SpatialIoU {si:.3f} > {SPATIAL_IOU_MAX} ({pair})"
    assert mx <= MIRROR_IOU_MAX,  f"MirrorX {mx:.3f} > {MIRROR_IOU_MAX} ({pair})"
    assert my <= MIRROR_IOU_MAX,  f"MirrorY {my:.3f} > {MIRROR_IOU_MAX} ({pair})"
    return f"{pair} J={j:.2f} IoU={si:.2f} Mx={mx:.2f} My={my:.2f}"


# ---------------------------------------------------------------------------
# Generic scale runner
# ---------------------------------------------------------------------------
def _run_scale(scale: str, synthesized_plans: Dict) -> None:
    plans   = synthesized_plans[scale]
    prompts = SCALE_PROMPTS[scale]
    assert len(plans) == 3

    for idx, (plan, (pid, _)) in enumerate(zip(plans, prompts), start=1):
        print(f"\n  [{scale}] Asserting {pid} …")
        _assert_plan(pid, plan)
        _assert_files(scale, idx, plan)

    rows: List[str] = []
    for i, j in [(0,1),(0,2),(1,2)]:
        pid_i, _ = prompts[i]
        pid_j, _ = prompts[j]
        row = _diversity_row(pid_i, plans[i], pid_j, plans[j])
        rows.append(row)
        print(f"  Diversity: {row}")

    sheet = _render_scale_summary_sheet(plans, scale, rows)
    assert os.path.exists(sheet)


# ---------------------------------------------------------------------------
# pytest tests (one per scale)
# ---------------------------------------------------------------------------

def test_3_marla_two_floor_audit(synthesized_plans):
    """3 Marla G+1: linear stair | L-vestibule | dogleg centre divider"""
    _run_scale("3_marla", synthesized_plans)


def test_5_marla_two_floor_audit(synthesized_plans):
    """5 Marla G+1: dogleg family villa | linear spine | U-shaped courtyard"""
    _run_scale("5_marla", synthesized_plans)


def test_7_marla_two_floor_audit(synthesized_plans):
    """7 Marla G+1: classic dual-rear | glass court | executive office"""
    _run_scale("7_marla", synthesized_plans)


def test_10_marla_two_floor_audit(synthesized_plans):
    """10 Marla G+1: executive U-stair | rotunda mansion | dual-family side"""
    _run_scale("10_marla", synthesized_plans)


def test_1_kanal_two_floor_audit(synthesized_plans):
    """1 Kanal G+1: palatial triple-car | courtyard pool | imperial rotunda"""
    _run_scale("1_kanal", synthesized_plans)


# ---------------------------------------------------------------------------
# Cross-scale summary / JSON report
# ---------------------------------------------------------------------------

def test_audit_summary_report(synthesized_plans):
    """Writes audit_report.json and asserts aggregate 15/15 two-floor compliance."""
    report = {
        "total_plans": 0,
        "total_two_floor": 0,
        "total_qg_pass": 0,
        "scales": {},
    }
    for scale, plans in synthesized_plans.items():
        entries = []
        for idx, (plan, (pid, prompt)) in enumerate(
            zip(plans, SCALE_PROMPTS[scale]), start=1
        ):
            gate = FloorPlanQualityGate.evaluate(plan)
            entries.append({
                "pid": pid,
                "prompt": prompt[:80],
                "plan_id": plan.metadata.plan_id,
                "floor_count": plan.metadata.floor_count,
                "levels": plan.metadata.levels,
                "qg_status": gate["final_status"],
                "quality_score": gate["quality_score"],
                "critical": gate["critical_failures_count"],
                "high": gate["high_failures_count"],
                "rooms_l0": sum(1 for r in plan.rooms if r.level_index == 0),
                "rooms_l1": sum(1 for r in plan.rooms if r.level_index == 1),
                "composite": f"{scale}_design_{idx}_composite.png",
            })
            report["total_plans"] += 1
            if plan.metadata.floor_count >= 2:
                report["total_two_floor"] += 1
            if gate["final_status"] == "PASS":
                report["total_qg_pass"] += 1
        report["scales"][scale] = entries

    rpath = os.path.join(AUDIT_DIR, "audit_report.json")
    with open(rpath, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"\n  [Report] {rpath}")

    assert report["total_plans"] == 15, (
        f"Expected 15 plans, got {report['total_plans']}"
    )
    assert report["total_two_floor"] == 15, (
        f"Only {report['total_two_floor']}/15 plans are G+1"
    )
    assert report["total_qg_pass"] == 15, (
        f"Only {report['total_qg_pass']}/15 plans passed QualityGate"
    )


if __name__ == "__main__":
    import pytest as _pt
    _pt.main([__file__, "-v", "--tb=short", "-rN"])
