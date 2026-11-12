"""
Pakistan Architectural RAG Guardrails Engine
============================================
Vector-retrieval engine for authentic Pakistani residential construction bylaws:
- CDA (Islamabad), LDA (Lahore), DHA bylaws
- Exact plot dimensions & statutory setbacks (3, 5, 7, 10 Marla, 1 & 2 Kanal)
- Strict Pakistani room naming conventions (no 'guest room' or generic labels)
- Vertical elevation levels (Road, Plinth, GF, FF, Parapet, Mumty)
- Paper-and-ink CAD drafting specifications

Vector Store Location: data/pakistan_construction_rag_guardrails.json
"""

import os
import json
import math
import re
import hashlib
from typing import Dict, List, Any, Optional
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARDRAILS_JSON_PATH = os.path.join(PROJECT_ROOT, "data", "pakistan_construction_rag_guardrails.json")

class PakistanRAGGuardrails:
    _instance: Optional["PakistanRAGGuardrails"] = None

    def __init__(self, data_path: str = GUARDRAILS_JSON_PATH, embedding_dim: int = 128):
        self.data_path = data_path
        self.embedding_dim = embedding_dim
        self.rules: List[Dict[str, Any]] = []
        self.vectors: np.ndarray = np.zeros((0, embedding_dim), dtype=np.float32)
        self._load_and_index()

    @classmethod
    def get_instance(cls) -> "PakistanRAGGuardrails":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _hash_vectorize(self, text: str) -> np.ndarray:
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        tokens = re.findall(r'[a-zA-Z0-9_\-\.\+]+', text.lower())
        features = list(tokens)
        for i in range(len(tokens) - 1):
            features.append(f"{tokens[i]}_{tokens[i+1]}")

        for feat in features:
            h = int(hashlib.md5(feat.encode('utf-8')).hexdigest(), 16)
            idx = h % self.embedding_dim
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        return vec

    def _load_and_index(self):
        if not os.path.exists(self.data_path):
            return

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.rules = data.get("guardrail_rules", [])
        vec_list = []
        for rule in self.rules:
            # Combine title, description, and tags for vector representation
            text = f"{rule.get('title', '')} {rule.get('description', '')} {' '.join(rule.get('vector_embedding_tags', []))}"
            vec = self._hash_vectorize(text)
            vec_list.append(vec)

        if vec_list:
            self.vectors = np.vstack(vec_list)

    def retrieve_guardrails(self, query: str, plot_width: float, plot_length: float, floors: int = 2) -> Dict[str, Any]:
        """
        Retrieves matching Pakistani construction bylaws & naming guardrails via vector similarity.
        """
        query_text = f"{query} {plot_width}x{plot_length} ft {floors} storeys"
        q_vec = self._hash_vectorize(query_text)

        # Cosine similarity ranking
        scores = np.dot(self.vectors, q_vec) if len(self.vectors) > 0 else []
        top_indices = np.argsort(scores)[::-1] if len(scores) > 0 else []

        matched_rules = [self.rules[i] for i in top_indices[:3]] if len(top_indices) > 0 else self.rules

        # Deduce statutory plot preset
        area = plot_width * plot_length
        preset_key = "10_marla"
        if area <= 800:
            preset_key = "3_marla"
        elif area <= 1350:
            preset_key = "5_marla"
        elif area <= 1850:
            preset_key = "7_marla"
        elif area <= 2800:
            preset_key = "10_marla"
        elif area <= 5500:
            preset_key = "1_kanal"
        else:
            preset_key = "2_kanal"

        # Extract plot rule
        plot_rule = next((r for r in self.rules if r.get("id") == "GR-PLOT-01"), None)
        plot_spec = {}
        if plot_rule:
            plot_spec = plot_rule.get("bylaw_specifications", {}).get(preset_key, {})

        # Extract naming dictionary
        naming_rule = next((r for r in self.rules if r.get("id") == "GR-ROOM-02"), None)
        naming_dict = naming_rule.get("naming_dictionary", {}) if naming_rule else {}

        # Extract vertical level benchmarks
        elev_rule = next((r for r in self.rules if r.get("id") == "GR-ELEV-03"), None)
        levels = elev_rule.get("vertical_levels_ft", {}) if elev_rule else {}

        return {
            "preset_key": preset_key,
            "plot_spec": plot_spec,
            "naming_dictionary": naming_dict,
            "vertical_levels": levels,
            "matched_rules": matched_rules,
            "vector_scores": [float(scores[i]) for i in top_indices[:3]] if len(scores) > 0 else []
        }

    def format_llm_guardrail_prompt_fragment(self, query: str, plot_width: float, plot_length: float, floors: int) -> str:
        """
        Formats retrieved vector guardrail chunks into strict instructions for Gemini LLM.
        """
        info = self.retrieve_guardrails(query, plot_width, plot_length, floors)
        spec = info["plot_spec"]
        fs = spec.get("front_setback_ft", 7.5)
        rs = spec.get("rear_setback_ft", 5.0)
        ss = spec.get("side_setback_ft", 0.0)
        cov = spec.get("max_ground_coverage_pct", 65.0)

        naming_text = "\n".join([
            f"- {k}: Location rule: {v.get('location_rule')}. (NEVER name as: {', '.join(v.get('forbidden_aliases', []))})"
            for k, v in list(info["naming_dictionary"].items())[:9]
        ])

        return f"""
PAKISTANI BYLAW & SPATIAL GUARDRAILS (Retrieved via RAG Vector Store):
1. Plot Standards ({info['preset_key'].upper().replace('_', ' ')}):
   - Mandatory Front Setback: {fs} ft (contains Front Lawn and Covered Car Porch).
   - Mandatory Rear Setback: {rs} ft (clear cross-ventilation passage).
   - Side Setbacks: {ss} ft.
   - Max Ground Coverage: {cov}% of plot area.
2. Authentic Pakistani Spatial Naming (NO generic 'Guest Room' or 'Room 1'):
{naming_text}
3. Elevation & Storey Heights:
   - Road Level: ±0'-0" | Plinth Level: +2'-6"
   - Ground Floor FFL: +2'-6" to +13'-0"
   - First Floor FFL: +13'-6" to +24'-0"
   - Parapet / Mumty Top: +27'-6"
"""

