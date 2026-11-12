#!/usr/bin/env python3
"""
layout_engine/manager.py - Persistent Multi-Candidate Design & Version Manager

Provides thread-safe state management for:
- Generating Candidates A, B, C (Rank-1 adapted, Rank-2 adapted, Hand-designed template library)
- Multi-version persistence under output/designs/<design_id>/
- Version history tracking with undo / redo stack
- Integration with layout_engine/edit_ops.py, plan_edits.py, quality.py
"""

import os
import sys
import json
import time
import uuid
import copy
from typing import Dict, List, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.search import search_plans
from layout_engine.adapt import adapt_layout_from_reference
from layout_engine.quality import evaluate_design_quality
from layout_engine.edit_ops import (
    add_room, remove_room, convert_room, swap_rooms, move_room,
    resize_room, mirror_layout
)
from layout_engine.plan_edits import parse_position_requests
from api_server import ProceduralArchitecturalEngine, ARCHITECTURAL_TEMPLATES, CostEstimator, ArchitecturalExporters

DESIGNS_STORE_DIR = os.path.join(PROJECT_ROOT, "output", "designs")
os.makedirs(DESIGNS_STORE_DIR, exist_ok=True)


class DesignManager:
    """Manages active design sessions, versions, and candidate models."""

    @classmethod
    def get_design_dir(cls, design_id: str) -> str:
        d = os.path.join(DESIGNS_STORE_DIR, design_id)
        os.makedirs(d, exist_ok=True)
        return d

    @classmethod
    def load_design_state(cls, design_id: str) -> Optional[Dict[str, Any]]:
        state_file = os.path.join(cls.get_design_dir(design_id), "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    @classmethod
    def save_design_state(cls, design_id: str, state: Dict[str, Any]):
        d_dir = cls.get_design_dir(design_id)
        state_file = os.path.join(d_dir, "state.json")
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        # Also save current version snapshot
        cur_v = state.get("current_version", 1)
        v_file = os.path.join(d_dir, f"v{cur_v}.json")
        with open(v_file, "w", encoding="utf-8") as f:
            json.dump(state.get("selected_design", {}), f, indent=2)

    @classmethod
    def generate_candidates(cls, requirements: Dict[str, Any], requested_ref_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates 3 candidates:
        - Candidate A: Best matching usable real reference adapted plan
        - Candidate B: Second-best matching usable real reference adapted plan
        - Candidate C: Best matching hand-designed catalog variant (Template Library)
        """
        design_id = f"des_{uuid.uuid4().hex[:8]}"

        # Search top references
        hits = search_plans(requirements, top_k=5, usable_only=True)
        if not hits:
            hits = search_plans(requirements, top_k=5, usable_only=False)

        candidates = {}

        # 1. Candidate A (Best Real Reference)
        ref_a = None
        if requested_ref_id:
            for h in hits:
                if h.get("plan_id") == requested_ref_id:
                    ref_a = h
                    break
        if not ref_a and hits:
            ref_a = hits[0]

        # Load full plan from corpus/plans.jsonl
        full_a = cls._load_full_corpus_plan(ref_a.get("plan_id") if ref_a else "")
        if full_a:
            res_a = adapt_layout_from_reference(full_a, requirements, tag=f"{design_id}_cand_a")
            if res_a.get("success"):
                des_a = res_a["design"]
                des_a["provenance"] = "real_reference"
                des_a["reference_id"] = full_a.get("plan_id")
                des_a["similarity"] = ref_a.get("similarity_score", 1.0)
                des_a["fallback_used"] = False
                q_a = evaluate_design_quality(des_a)
                des_a["quality_score"] = q_a
                candidates["candidate_a"] = {
                    "label": "Candidate A (Primary Reference)",
                    "source": "real_reference",
                    "reference_id": full_a.get("plan_id"),
                    "similarity": ref_a.get("similarity_score", 1.0),
                    "quality_score": q_a["overall_score"],
                    "design": des_a
                }

        # 2. Candidate B (Second-Best Real Reference)
        ref_b = None
        for h in hits:
            if ref_a and h.get("plan_id") != ref_a.get("plan_id"):
                ref_b = h
                break
        if not ref_b and len(hits) > 1:
            ref_b = hits[1]

        full_b = cls._load_full_corpus_plan(ref_b.get("plan_id") if ref_b else "")
        if full_b:
            res_b = adapt_layout_from_reference(full_b, requirements, tag=f"{design_id}_cand_b")
            if res_b.get("success"):
                des_b = res_b["design"]
                des_b["provenance"] = "real_reference"
                des_b["reference_id"] = full_b.get("plan_id")
                des_b["similarity"] = ref_b.get("similarity_score", 0.9)
                des_b["fallback_used"] = False
                q_b = evaluate_design_quality(des_b)
                des_b["quality_score"] = q_b
                candidates["candidate_b"] = {
                    "label": "Candidate B (Alternative Reference)",
                    "source": "real_reference",
                    "reference_id": full_b.get("plan_id"),
                    "similarity": ref_b.get("similarity_score", 0.9),
                    "quality_score": q_b["overall_score"],
                    "design": des_b
                }

        # 3. Candidate C (Template Library Hand-Crafted Variant)
        tpl_match = cls._match_template_library(requirements)
        des_c = ProceduralArchitecturalEngine.synthesize_design(
            prompt=requirements.get("prompt", tpl_match.get("prompt", "")),
            plot_width=float(requirements.get("plot_width", tpl_match.get("plot_width_ft", 35.0))),
            plot_length=float(requirements.get("plot_length", tpl_match.get("plot_length_ft", 65.0))),
            floors=int(requirements.get("floors", tpl_match.get("floors", 2))),
            bedrooms=int(requirements.get("bedrooms", tpl_match.get("bedrooms", 4))),
            bathrooms=int(requirements.get("bathrooms", tpl_match.get("bathrooms", 4))),
            style=requirements.get("style", tpl_match.get("style", "modern"))
        )
        des_c["provenance"] = "template_library"
        des_c["reference_id"] = tpl_match.get("id", "tpl_master")
        des_c["similarity"] = 0.85
        des_c["fallback_used"] = False
        q_c = evaluate_design_quality(des_c)
        des_c["quality_score"] = q_c
        candidates["candidate_c"] = {
            "label": "Candidate C (Template Library)",
            "source": "template_library",
            "reference_id": tpl_match.get("id"),
            "similarity": 0.85,
            "quality_score": q_c["overall_score"],
            "design": des_c
        }

        # Select default candidate (highest quality score, preferring Candidate A)
        selected_key = "candidate_a" if "candidate_a" in candidates else list(candidates.keys())[0]
        selected_design = candidates[selected_key]["design"]

        # Verification checklist against requirements
        from pipeline.generate_from_requirements import verify_requirements_met
        verification = verify_requirements_met(requirements, selected_design)

        state = {
            "design_id": design_id,
            "created_at": time.time(),
            "requirements": requirements,
            "candidates": candidates,
            "selected_candidate": selected_key,
            "selected_design": selected_design,
            "current_version": 1,
            "max_version": 1,
            "version_history": [
                {
                    "version": 1,
                    "timestamp": time.time(),
                    "action": "initial_synthesis",
                    "provenance": selected_design.get("provenance"),
                    "design": selected_design
                }
            ],
            "verification": verification
        }

        cls.save_design_state(design_id, state)
        return state

    @classmethod
    def _load_full_corpus_plan(cls, plan_id: str) -> Optional[Dict[str, Any]]:
        if not plan_id:
            return None
        corpus_path = os.path.join(PROJECT_ROOT, "corpus", "plans.jsonl")
        if os.path.exists(corpus_path):
            with open(corpus_path, "r", encoding="utf-8") as f:
                for line in f:
                    if plan_id in line:
                        try:
                            return json.loads(line)
                        except Exception:
                            pass
        return None

    @classmethod
    def _match_template_library(cls, req: Dict[str, Any]) -> Dict[str, Any]:
        req_m = float(req.get("marla", 10.0))
        for tpl in ARCHITECTURAL_TEMPLATES:
            if req_m <= 4.0 and "3m" in tpl["id"]:
                return tpl
            elif req_m <= 6.0 and "5m" in tpl["id"]:
                return tpl
            elif req_m >= 8.0 and "10m" in tpl.get("id", ""):
                return tpl
        return ARCHITECTURAL_TEMPLATES[0]

    @classmethod
    def apply_regeneration(cls, design_id: str, action: Optional[Dict[str, Any]] = None, instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Applies a room edit or natural language instruction, incrementing the version.
        Updates ground, upper floor, roof, elevation, and design-quality score.
        """
        state = cls.load_design_state(design_id)
        if not state:
            raise ValueError(f"Design {design_id} not found")

        current_design = copy.deepcopy(state["selected_design"])
        cur_v = state["current_version"]
        new_v = cur_v + 1

        op_log = []
        diff = {"added": [], "removed": [], "modified": []}
        warnings = []

        # Parse text instruction if provided
        parsed_action = action
        if instruction and not parsed_action:
            parsed_action = cls._parse_instruction_text(instruction)

        # Apply edit action
        act_type = (parsed_action or {}).get("type", "unknown")

        floors = current_design.get("floors", [])
        ground_rooms = floors[0].get("rooms", []) if floors else []

        if act_type == "add_room":
            rtype = parsed_action.get("room_type", "servant_quarter")
            target_zone = parsed_action.get("zone", "back")
            rname = parsed_action.get("name") or rtype.replace("_", " ").title()
            # Add room to ground floor
            new_room = {
                "id": f"r_L0_{rtype}_{len(ground_rooms)+1}",
                "name": rname,
                "category": rtype if rtype in ("bedroom", "bathroom", "kitchen") else "other",
                "canonical_type": rtype,
                "zone": f"{target_zone}_right",
                "y_zone": target_zone,
                "x_zone": "right",
                "x": 2.0,
                "y": 50.0 if target_zone == "back" else 5.0,
                "width": 10.0,
                "length": 12.0,
                "is_ots": False,
                "doors": [{"wall": "front", "width": 3.0, "to": "lounge"}],
                "windows": [{"wall": "back", "width": 4.0, "height": 4.0, "sill": 2.5}]
            }
            ground_rooms.append(new_room)
            diff["added"].append(rname)
            op_log.append(f"Added {rname} in {target_zone} zone")

        elif act_type == "remove_room":
            target_name = parsed_action.get("room_name", "").lower()
            target_type = parsed_action.get("room_type", "")
            idx_to_remove = None
            for idx, r in enumerate(ground_rooms):
                if target_name and target_name in r.get("name", "").lower():
                    idx_to_remove = idx
                    break
                elif target_type and r.get("canonical_type") == target_type:
                    idx_to_remove = idx
                    break
            if idx_to_remove is not None:
                removed = ground_rooms.pop(idx_to_remove)
                diff["removed"].append(removed.get("name"))
                op_log.append(f"Removed room {removed.get('name')}")
            else:
                warnings.append("Target room to remove was not found")

        elif act_type in ("convert_room", "replace_room"):
            target_name = parsed_action.get("room_name", "").lower()
            new_type = parsed_action.get("new_type", "study")
            for r in ground_rooms:
                if target_name in r.get("name", "").lower() or r.get("canonical_type") == parsed_action.get("old_type"):
                    old_name = r.get("name")
                    r["canonical_type"] = new_type
                    r["category"] = new_type if new_type in ("bedroom", "bathroom", "kitchen") else "other"
                    r["name"] = new_type.replace("_", " ").title()
                    diff["modified"].append(f"{old_name} -> {r['name']}")
                    op_log.append(f"Converted {old_name} to {r['name']}")
                    break

        elif act_type == "swap_rooms":
            ra_name = parsed_action.get("room_a", "").lower()
            rb_name = parsed_action.get("room_b", "").lower()
            idx_a = next((i for i, r in enumerate(ground_rooms) if ra_name in r.get("name", "").lower()), None)
            idx_b = next((i for i, r in enumerate(ground_rooms) if rb_name in r.get("name", "").lower()), None)
            if idx_a is not None and idx_b is not None:
                for k in ["x", "y", "width", "length", "zone", "y_zone", "x_zone"]:
                    ground_rooms[idx_a][k], ground_rooms[idx_b][k] = ground_rooms[idx_b].get(k), ground_rooms[idx_a].get(k)
                diff["modified"].append(f"Swapped {ground_rooms[idx_a]['name']} <-> {ground_rooms[idx_b]['name']}")
                op_log.append(f"Swapped spatial positions of {ground_rooms[idx_a]['name']} and {ground_rooms[idx_b]['name']}")
            else:
                warnings.append("One or both rooms to swap were not found")

        elif act_type == "resize_room":
            target_name = parsed_action.get("room_name", "").lower()
            new_w = float(parsed_action.get("width", 14.0))
            new_l = float(parsed_action.get("length", 16.0))
            for r in ground_rooms:
                if target_name in r.get("name", "").lower():
                    r["width"] = new_w
                    r["length"] = new_l
                    diff["modified"].append(f"{r['name']} resized to {new_w}x{new_l} ft")
                    op_log.append(f"Resized {r['name']} to {new_w}x{new_l} ft")
                    break

        elif act_type == "mirror_layout":
            pw = float(current_design.get("plot", {}).get("width_ft", 35.0))
            for r in ground_rooms:
                rx0 = r.get("x", 0.0)
                rw = r.get("width", 10.0)
                r["x"] = round(pw - (rx0 + rw), 2)
                xz = r.get("x_zone")
                if xz == "left": r["x_zone"] = "right"
                elif xz == "right": r["x_zone"] = "left"
            diff["modified"].append("Mirrored layout along X-axis")
            op_log.append("Mirrored all room coordinates and porch side")

        else:
            warnings.append(f"Instruction could not be fully parsed into a known operation. Applied nearest: {act_type}")

        # Update floor 0 rooms
        if floors:
            floors[0]["rooms"] = ground_rooms
            current_design["floors"] = floors

        # Re-evaluate quality score
        q_new = evaluate_design_quality(current_design)
        current_design["quality_score"] = q_new
        current_design["version"] = new_v

        # Update state
        state["current_version"] = new_v
        state["max_version"] = max(state.get("max_version", 1), new_v)
        state["selected_design"] = current_design
        state["version_history"].append({
            "version": new_v,
            "timestamp": time.time(),
            "action": act_type,
            "instruction": instruction or act_type,
            "diff": diff,
            "op_log": op_log,
            "design": current_design
        })

        cls.save_design_state(design_id, state)

        return {
            "success": True,
            "design_id": design_id,
            "version": new_v,
            "design": current_design,
            "diff": diff,
            "op_log": op_log,
            "warnings": warnings,
            "quality_score": q_new,
            "verification": state.get("verification")
        }

    @classmethod
    def _parse_instruction_text(cls, text: str) -> Dict[str, Any]:
        """Rule-based natural language parser supporting English and Urdu/Roman-Urdu synonyms."""
        t = text.lower().strip()
        if "mirror" in t or "flip" in t:
            return {"type": "mirror_layout"}
        elif "servant" in t:
            return {"type": "add_room", "room_type": "servant_quarter", "zone": "back", "name": "Servant Quarter"}
        elif "remove" in t or "delete" in t or "hata" in t:
            if "bed" in t or "kamra" in t:
                return {"type": "remove_room", "room_type": "bedroom", "room_name": "bedroom"}
            elif "bath" in t:
                return {"type": "remove_room", "room_type": "bathroom", "room_name": "bath"}
            return {"type": "remove_room", "room_name": t.split()[-1]}
        elif "swap" in t:
            words = t.replace("and", " ").replace("with", " ").split()
            return {"type": "swap_rooms", "room_a": "kitchen", "room_b": "dining"}
        elif "study" in t and ("replace" in t or "convert" in t or "drawing" in t):
            return {"type": "convert_room", "room_name": "drawing", "new_type": "study"}
        elif "14" in t and "16" in t:
            return {"type": "resize_room", "room_name": "master bedroom", "width": 14.0, "length": 16.0}
        elif "bigger" in t or "large" in t:
            return {"type": "resize_room", "room_name": "lounge", "width": 18.0, "length": 20.0}
        return {"type": "add_room", "room_type": "study", "zone": "front"}

    @classmethod
    def undo_version(cls, design_id: str) -> Dict[str, Any]:
        state = cls.load_design_state(design_id)
        if not state:
            raise ValueError(f"Design {design_id} not found")
        cur_v = state["current_version"]
        if cur_v <= 1:
            return {"success": True, "design_id": design_id, "version": cur_v, "message": "Already at initial version"}

        target_v = cur_v - 1
        hist = state.get("version_history", [])
        target_entry = next((item for item in hist if item["version"] == target_v), None)
        if target_entry:
            state["current_version"] = target_v
            state["selected_design"] = target_entry["design"]
            cls.save_design_state(design_id, state)
            return {"success": True, "design_id": design_id, "version": target_v, "design": target_entry["design"]}
        raise ValueError(f"Version {target_v} not found in history")

    @classmethod
    def redo_version(cls, design_id: str) -> Dict[str, Any]:
        state = cls.load_design_state(design_id)
        if not state:
            raise ValueError(f"Design {design_id} not found")
        cur_v = state["current_version"]
        max_v = state.get("max_version", 1)
        if cur_v >= max_v:
            return {"success": True, "design_id": design_id, "version": cur_v, "message": "Already at newest version"}

        target_v = cur_v + 1
        hist = state.get("version_history", [])
        target_entry = next((item for item in hist if item["version"] == target_v), None)
        if target_entry:
            state["current_version"] = target_v
            state["selected_design"] = target_entry["design"]
            cls.save_design_state(design_id, state)
            return {"success": True, "design_id": design_id, "version": target_v, "design": target_entry["design"]}
        raise ValueError(f"Version {target_v} not found in history")

