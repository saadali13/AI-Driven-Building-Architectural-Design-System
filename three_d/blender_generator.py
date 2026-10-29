"""
Phase 13 & 14: Procedural 3D Blender Model Generator.
Executes headless Blender 5.1 to construct solid 3D models with boolean void cutters
and generates architectural perspective renders directly from CanonicalFloorPlan.
"""

import os
import subprocess
import tempfile
import json
from typing import Dict, Optional, Tuple, Any
from dataset.schema.canonical import CanonicalFloorPlan


class Blender3DGenerator:
    DEFAULT_BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"

    def __init__(self, blender_path: Optional[str] = None):
        self.blender_path = blender_path or self.DEFAULT_BLENDER_PATH
        self.worker_script = os.path.join(os.path.dirname(__file__), "blender_arch_v2_worker.py")

    def is_blender_available(self) -> bool:
        if os.path.exists(self.blender_path):
            return True
        import shutil
        return shutil.which("blender") is not None

    def generate_3d_model(
        self,
        plan: CanonicalFloorPlan,
        output_blend_path: str,
        output_render_path: str,
        timeout_seconds: float = 180.0
    ) -> Dict[str, Any]:
        """
        Executes headless procedural extrusion, boolean void cutting, and rendering in Blender.
        """
        if not os.path.exists(self.blender_path):
            raise FileNotFoundError(f"Blender executable not found at {self.blender_path}")

        output_blend_path = os.path.abspath(output_blend_path)
        output_render_path = os.path.abspath(output_render_path)

        os.makedirs(os.path.dirname(output_blend_path), exist_ok=True)
        os.makedirs(os.path.dirname(output_render_path), exist_ok=True)

        plan_json_path = output_blend_path.replace(".blend", "_plan.json")
        with open(plan_json_path, "w", encoding="utf-8") as f:
            f.write(plan.to_json())

        cmd = [
            self.blender_path,
            "--background",
            "--python",
            self.worker_script,
            "--",
            plan_json_path,
            output_blend_path,
            output_render_path
        ]

        env = dict(os.environ)
        env.setdefault("CYCLES_SAMPLES", "16")
        env.setdefault("RENDER_RES_PCT", "50")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=timeout_seconds
        )

        success = os.path.exists(output_blend_path) and os.path.exists(output_render_path)

        return {
            "success": success,
            "blend_path": output_blend_path,
            "render_path": output_render_path,
            "stdout": result.stdout[-500:],
            "stderr": result.stderr[-500:] if result.stderr else "",
            "returncode": result.returncode
        }
