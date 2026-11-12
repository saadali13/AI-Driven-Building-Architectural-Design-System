"""
ArchiCraft AI — Vision-Capable GPT Architectural Reviewer (Phase 8A Standard)
=============================================================================
Inspects actual generated architectural images (2D floor plans, front elevation,
and 3D volumetric massing renders) using OpenAI's Vision-capable models.

Guiding Principles:
1. Server-side only; never expose API credentials to frontend or client bundle.
2. Submit real rendered image data (high-detail base64 data URIs).
3. Structured output schema complying with professional architectural audit criteria.
4. Honest error handling: transparently surfaces 401 Unauthorized, 429 Quota Exceeded,
   timeouts, and network errors without fabricating synthetic critiques.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = Path(r"C:\Users\m\OneDrive\Desktop\New folder")

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """Safely reads and base64-encodes an image file on disk."""
    if not image_path:
        return None
    p = Path(image_path)
    if not p.exists():
        return None
    try:
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None

def review_architectural_design_with_gpt(
    design_result: Dict[str, Any],
    model_name: Optional[str] = None,
    timeout_sec: int = 35
) -> Dict[str, Any]:
    """
    Submits actual generated images to OpenAI Vision API for professional architectural evaluation.
    Handles missing keys, invalid keys (401), rate limits (429), and timeouts gracefully without fabrication.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    target_model = model_name or os.environ.get("OPENAI_VISION_MODEL", "gpt-4o")

    if not api_key:
        return {
            "gpt_review_status": "CONFIGURATION_REQUIRED",
            "is_available": False,
            "message": "OpenAI API key is missing from environment (OPENAI_API_KEY). Set the environment variable to enable live vision review.",
            "review": None,
            "recommended_improvements": []
        }

    # Gather images to send
    image_contents = []
    
    # 1. Floor plan images (Ground, First, etc.)
    for fp in design_result.get("floor_plans", []):
        img_p = fp.get("image_path")
        b64 = encode_image_to_base64(img_p)
        if b64:
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64}",
                    "detail": "high"
                }
            })

    # 2. Elevation image
    elev_p = design_result.get("elevation", {}).get("image_path")
    if elev_p:
        b64 = encode_image_to_base64(elev_p)
        if b64:
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64}",
                    "detail": "high"
                }
            })

    # 3. 3D Render images (Perspective & Top-down)
    mesh = design_result.get("mesh_3d", {})
    for k in ["image_path", "image_path_top"]:
        mp = mesh.get(k)
        if mp:
            b64 = encode_image_to_base64(mp)
            if b64:
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64}",
                        "detail": "high"
                    }
                })

    if not image_contents:
        return {
            "gpt_review_status": "NO_IMAGES_AVAILABLE",
            "is_available": False,
            "message": "Generated design images were not found on disk for visual review.",
            "review": None,
            "recommended_improvements": []
        }

    canonical = design_result.get("canonical_model", {})
    site = canonical.get("site", {})
    meta = canonical.get("metadata", {})

    prompt_text = (
        f"You are a Senior Principal Pakistani Residential Architect (PCATP licensed) and building code expert.\n"
        f"Critically inspect the attached real generated floor plans, technical front elevation, and 3D volumetric massing renders for:\n"
        f"- Project Name: {meta.get('project_name', 'Residence')}\n"
        f"- Plot Dimensions: {site.get('plot_width', 25)}ft frontage x {site.get('plot_depth', 45)}ft depth ({meta.get('marla_category', '5 Marla')})\n"
        f"- Storeys: {meta.get('storeys_count', 2)}\n"
        f"- Architectural Style: {meta.get('architectural_style', 'Modern Contemporary')}\n\n"
        f"Provide your critique strictly in pure JSON matching this exact schema:\n"
        f"{{\n"
        f'  "overall_visual_quality_score": 8.8,\n'
        f'  "floor_plan_quality_score": 9.2,\n'
        f'  "elevation_quality_score": 8.7,\n'
        f'  "three_d_quality_score": 8.5,\n'
        f'  "cross_view_consistency_score": 9.0,\n'
        f'  "overall_summary": "1-2 sentence overall assessment",\n'
        f'  "critical_issues": [\n'
        f'    {{"issue": "Short summary", "location": "Room/Elevation coordinate", "explanation": "Detailed explanation"}}\n'
        f'  ],\n'
        f'  "minor_issues": [\n'
        f'    {{"issue": "Short summary", "location": "Location", "explanation": "Detailed explanation"}}\n'
        f'  ],\n'
        f'  "missing_architectural_elements": ["List of missing elements if any"],\n'
        f'  "incorrect_proportions": ["List of proportion issues if any"],\n'
        f'  "room_planning_problems": ["List of zoning/circulation issues if any"],\n'
        f'  "opening_mismatches": ["List of mismatches between elevation and floor plan if any"],\n'
        f'  "suggested_corrections": [\n'
        f'    {{"target": "floor_plan|elevation|3d", "action": "Specific architectural adjustment", "priority": "high|medium"}}\n'
        f'  ],\n'
        f'  "human_review_required": false\n'
        f"}}"
    )

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": target_model,
        "messages": [
            {
                "role": "system",
                "content": "You are a licensed Pakistani PCATP architect providing rigorous architectural design reviews. Always respond with pure JSON."
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt_text}] + image_contents
            }
        ],
        "max_tokens": 1500,
        "response_format": {"type": "json_object"}
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content_str = data["choices"][0]["message"]["content"]
            review_json = json.loads(content_str)
            return {
                "gpt_review_status": "COMPLETED",
                "is_available": True,
                "model_used": target_model,
                "review": review_json,
                "recommended_improvements": review_json.get("suggested_corrections", [])
            }
    except urllib.error.HTTPError as he:
        err_msg = f"HTTP {he.code}"
        if he.code == 401:
            err_msg = "Invalid or expired OpenAI API Key."
        elif he.code == 429:
            err_msg = "OpenAI API rate limit or quota exceeded."
        return {
            "gpt_review_status": "API_ERROR",
            "is_available": False,
            "http_code": he.code,
            "message": f"GPT Architectural Review unavailable: {err_msg}",
            "review": None,
            "recommended_improvements": []
        }
    except Exception as e:
        return {
            "gpt_review_status": "NETWORK_ERROR",
            "is_available": False,
            "message": f"GPT Architectural Review connection failed: {str(e)}",
            "review": None,
            "recommended_improvements": []
        }

if __name__ == "__main__":
    test_design = {
        "canonical_model": {
            "metadata": {"project_name": "Test Residence", "marla_category": "5 Marla", "storeys_count": 2},
            "site": {"plot_width": 25.0, "plot_depth": 45.0}
        },
        "floor_plans": [],
        "elevation": {},
        "mesh_3d": {}
    }
    res = review_architectural_design_with_gpt(test_design)
    print("Reviewer status:", res["gpt_review_status"], "Message:", res["message"])
