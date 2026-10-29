"""
Master Architectural Plot & Floor Plan Renderer.
Publication-quality CAD rendering engine conforming to CDA, DHA, and LDA bylaws.
Adheres to Arch D (24" x 36") 300 DPI vector presentation sheet standards.
Integrates authentic 1:100 CAD vector blocks and asset loader from 'furniture ,car,stairs'.
"""

import os
import sys
import math
from typing import Dict, List, Optional, Tuple, Any

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams['svg.fonttype'] = 'none'
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, WallModel, OpeningModel
from cad.asset_loader import CADAssetLoader
from generation.visualizer import FloorPlanVisualizer


class PlotRenderer:
    """
    High-Performance Architectural Plot & Blueprint Renderer.
    """

    @classmethod
    def render_presentation_sheet(
        cls,
        plan: CanonicalFloorPlan,
        output_path: str,
        paper_size: str = "ARCH_D",
        dpi: int = 300,
        title: Optional[str] = None
    ) -> str:
        """
        Renders a publication-grade composite multi-floor presentation sheet (Arch D 24"x36").
        Includes Ground Floor (Level 0), First Floor (Level 1), North Arrow, Professional
        AIA Title Block, Structural Wall Hatching, and authentic 1:100 CAD Vector Blocks.
        """
        return FloorPlanVisualizer.render_vector_sheet(
            plan=plan,
            output_path=output_path,
            paper_size=paper_size,
            dpi=dpi,
            title_override=title
        )

    @classmethod
    def render_single_floor(
        cls,
        plan: CanonicalFloorPlan,
        output_path: str,
        level_index: int = 0,
        dpi: int = 300
    ) -> str:
        """
        Renders a high-resolution 2D architectural blueprint for a single floor level.
        """
        return FloorPlanVisualizer.render_floor_plan(
            plan=plan,
            output_image_path=output_path,
            level_index=level_index,
            dpi=dpi
        )

    @classmethod
    def render_all(
        cls,
        plan: CanonicalFloorPlan,
        output_dir: str
    ) -> Dict[str, str]:
        """
        Renders all floors (Level 0, Level 1) and composite presentation sheet in PNG and PDF.
        """
        os.makedirs(output_dir, exist_ok=True)
        results = FloorPlanVisualizer.render_all_floors(plan, output_dir)
        
        # Also render Arch D PDF and high-res presentation PNG
        pdf_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_presentation_sheet.pdf")
        png_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_presentation_sheet.png")
        
        cls.render_presentation_sheet(plan, pdf_path, paper_size="ARCH_D", dpi=300)
        cls.render_presentation_sheet(plan, png_path, paper_size="ARCH_D", dpi=200)
        
        results["presentation_pdf"] = pdf_path
        results["presentation_png"] = png_path
        return results
