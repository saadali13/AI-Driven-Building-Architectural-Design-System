"""
Tests for Modular Procedural Staircase Subsystem (9 Typologies).
Validates:
1. Parametric geometry & riser calculation for all 9 typologies:
   - Straight
   - L-Shaped (Quarter Turn)
   - U-Shaped (Half Turn / Dogleg)
   - Winder (Radiating Treads)
   - Spiral (Helical around Newel Post)
   - Curved / Circular (Sweeping Arc)
   - Ladder / Ship's Stair (Steep Pitch)
   - Floating / Cantilever (Open Risers & Glass Balustrade)
   - Bifurcated / Split (Grand Central Flight & Dual Branches)
2. Quality Gate F10 Typology-Aware Compliance (headroom, landing depth, clearances).
3. Coordinated Multi-Floor Alignment & Invariance (IoU >= 0.98).
4. Full Visual Proof Sheet Generation (output/stair_typology_matrix.png).
"""

import os
import math
import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from generation.staircase_engine import (
    StairTypology,
    StaircaseEngine,
    StairParametricModel
)
from generation.quality_gate import FloorPlanQualityGate
from generation.visualizer import FloorPlanVisualizer
from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    RoomModel,
    WallModel,
    OpeningModel
)


class TestStaircaseGeneration:
    """Test suite for all 9 procedural staircase typologies."""

    @pytest.mark.parametrize("typology", list(StairTypology))
    def test_all_9_typologies_generate_valid_parametric_model(self, typology: StairTypology):
        """Ensures every typology produces a complete StairParametricModel with treads and risers."""
        model = StaircaseEngine.create_staircase(
            typology=typology,
            origin=(2.0, 3.0),
            floor_to_floor_height_m=3.15,
            width_m=2.20 if typology not in (StairTypology.SPIRAL, StairTypology.LADDER, StairTypology.BIFURCATED) else (
                1.50 if typology == StairTypology.SPIRAL else (0.75 if typology == StairTypology.LADDER else 3.60)
            ),
            length_m=3.20 if typology not in (StairTypology.SPIRAL, StairTypology.LADDER, StairTypology.BIFURCATED) else (
                1.50 if typology == StairTypology.SPIRAL else (2.40 if typology == StairTypology.LADDER else 4.00)
            )
        )
        assert isinstance(model, StairParametricModel)
        assert model.typology == typology
        assert model.riser_count >= 10
        assert 0.14 <= model.riser_height_m <= 0.23  # IBC compliant riser range
        assert len(model.treads) >= 8
        assert model.bounding_polygon.is_valid
        assert not model.bounding_polygon.is_empty
        assert model.headroom_clearance_m >= 2.032  # IBC standard

    def test_quality_gate_f10_passes_all_typologies(self):
        """Validates that QualityGate F10 correctly accepts each valid typology without false positives."""
        gate = FloorPlanQualityGate()
        
        for typ in StairTypology:
            model = StaircaseEngine.create_staircase(
                typology=typ,
                origin=(0.0, 0.0),
                floor_to_floor_height_m=3.15,
                width_m=2.20 if typ not in (StairTypology.SPIRAL, StairTypology.LADDER, StairTypology.BIFURCATED) else (
                    1.50 if typ == StairTypology.SPIRAL else (0.75 if typ == StairTypology.LADDER else 3.60)
                ),
                length_m=3.20 if typ not in (StairTypology.SPIRAL, StairTypology.LADDER, StairTypology.BIFURCATED) else (
                    1.50 if typ == StairTypology.SPIRAL else (2.40 if typ == StairTypology.LADDER else 4.00)
                )
            )
            # Create a 1-floor CanonicalFloorPlan wrapper
            room_l0 = StaircaseEngine.to_room_model(model, level_index=0, room_id=f"stair_{typ.value}_l0")
            
            # Boundary walls
            poly_coords = list(room_l0.polygon)
            walls = []
            for i in range(len(poly_coords) - 1):
                walls.append(WallModel(
                    wall_id=f"w_{typ.value}_{i}",
                    centerline=[poly_coords[i], poly_coords[i+1]],
                    wall_type="interior",
                    thickness_m=0.15,
                    level_index=0
                ))

            boundary = list(room_l0.polygon)
            plan = CanonicalFloorPlan(
                metadata=MetadataModel(
                    plan_id=f"test_stair_{typ.value}",
                    source_type="synthetic_generated",
                    floor_count=1,
                    levels=[0]
                ),
                total_area_m2=room_l0.area_m2,
                boundary=boundary,
                rooms=[room_l0],
                walls=walls,
                openings=[]
            )

            report = gate.evaluate(plan)
            # Check specifically for F10 failures
            f10_failures = [f for f in report["failures"] if f["code"] == "F10"]
            assert len(f10_failures) == 0, f"Typology {typ.value} failed F10 check: {f10_failures}"

    def test_multi_floor_stair_invariance(self):
        """Validates that Ground and First floor stair cores align exactly with IoU >= 0.98."""
        gate = FloorPlanQualityGate()
        model_l0 = StaircaseEngine.create_staircase(StairTypology.U_SHAPED, origin=(3.0, 4.0), width_m=2.20, length_m=3.20)
        room_0 = StaircaseEngine.to_room_model(model_l0, level_index=0, room_id="staircase_core_l0")
        
        # Upper landing with exact vertical match
        model_l1 = StaircaseEngine.create_staircase(StairTypology.U_SHAPED, origin=(3.0, 4.0), width_m=2.20, length_m=3.20)
        room_1 = StaircaseEngine.to_room_model(model_l1, level_index=1, room_id="staircase_core_l1")

        p0 = Polygon(room_0.polygon)
        p1 = Polygon(room_1.polygon)
        iou = p0.intersection(p1).area / p0.union(p1).area
        assert iou >= 0.98, f"Staircase IoU is {iou:.4f}, expected >= 0.98"

        boundary = list(room_0.polygon)
        plan = CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id="test_stair_invariance",
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1]
            ),
            total_area_m2=room_0.area_m2 * 2,
            boundary=boundary,
            rooms=[room_0, room_1],
            walls=[],
            openings=[]
        )
        report = gate.evaluate(plan)
        f10_failures = [f for f in report["failures"] if f["code"] == "F10"]
        assert len(f10_failures) == 0

    def test_generate_visual_proof_sheet(self):
        """Renders and saves output/stair_typology_matrix.png displaying all 9 typologies side-by-side."""
        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "stair_typology_matrix.png")

        fig, axes = plt.subplots(3, 3, figsize=(22, 22), dpi=200)
        fig.patch.set_facecolor("#0F172A")
        plt.subplots_adjust(left=0.04, right=0.96, top=0.93, bottom=0.04, wspace=0.22, hspace=0.26)

        typologies = list(StairTypology)
        
        for idx, typ in enumerate(typologies):
            row = idx // 3
            col = idx % 3
            ax = axes[row, col]
            ax.set_facecolor("#FFFFFF")
            ax.set_aspect("equal")

            # Determine appropriate bounding dimensions for typology
            if typ == StairTypology.SPIRAL:
                w, h = 1.60, 1.60
            elif typ == StairTypology.LADDER:
                w, h = 0.75, 2.60
            elif typ == StairTypology.BIFURCATED:
                w, h = 3.80, 3.80
            elif typ == StairTypology.CURVED:
                w, h = 2.80, 2.80
            else:
                w, h = 2.40, 3.40

            # Side-by-side within sub-cell: Left = Level 0 (UP), Right = Level 1 (DN)
            gap = 0.80
            total_w = w * 2 + gap
            margin = 0.50

            ax.set_xlim(-margin, total_w + margin)
            ax.set_ylim(-margin, h + margin)

            # L0 Stair on left
            room_l0 = RoomModel(
                room_id=f"stair_{typ.value}_l0",
                room_name=f"{typ.value.replace('_', ' ').title()} Stair (L0)",
                room_type="corridor",
                polygon=[(0, 0), (w, 0), (w, h), (0, h), (0, 0)],
                centroid=[w * 0.5, h * 0.5],
                area_m2=w * h,
                level_index=0,
                metadata={"typology": typ.value}
            )
            # Outer room boundary
            rect0 = plt.Rectangle((0, 0), w, h, fill=True, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.8, zorder=1)
            ax.add_patch(rect0)
            FloorPlanVisualizer._draw_modular_staircase(ax, room_l0, 0, 0, w, h, is_first_floor=False)

            # L1 Stair on right
            x1 = w + gap
            room_l1 = RoomModel(
                room_id=f"stair_{typ.value}_l1",
                room_name=f"{typ.value.replace('_', ' ').title()} Stair (L1)",
                room_type="corridor",
                polygon=[(x1, 0), (x1 + w, 0), (x1 + w, h), (x1, h), (x1, 0)],
                centroid=[x1 + w * 0.5, h * 0.5],
                area_m2=w * h,
                level_index=1,
                metadata={"typology": typ.value}
            )
            rect1 = plt.Rectangle((x1, 0), w, h, fill=True, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.8, zorder=1)
            ax.add_patch(rect1)
            FloorPlanVisualizer._draw_modular_staircase(ax, room_l1, x1, 0, w, h, is_first_floor=True)

            # Subplot Labels
            ax.text(w * 0.5, -0.30, "LEVEL 0 (GROUND)", ha="center", va="top", fontsize=7.5, fontweight="bold", color="#0F172A")
            ax.text(x1 + w * 0.5, -0.30, "LEVEL 1 (UPPER)", ha="center", va="top", fontsize=7.5, fontweight="bold", color="#2563EB")
            
            title_text = f"Typology {idx+1}: {typ.value.replace('_', ' ').upper()}"
            ax.set_title(title_text, fontsize=9.5, fontweight="bold", color="#FFFFFF", pad=10,
                         bbox=dict(boxstyle="round,pad=0.3", facecolor="#1E293B", edgecolor="#38BDF8", lw=1.0))
            ax.axis("off")

        fig.suptitle(
            "COMPREHENSIVE PROCEDURAL STAIRCASE ENGINE — 9 ARCHITECTURAL TYPOLOGIES\n"
            "High-Precision CAD 2D Drafting with Multi-Floor Alignment, Breaklines, Radiating Winders & Balustrades",
            fontsize=13, fontweight="bold", color="#F8FAFC", y=0.98
        )

        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 50000
