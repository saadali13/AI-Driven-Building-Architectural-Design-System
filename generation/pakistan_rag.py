"""
Pakistan Construction Rules Vector RAG — The LLM Planner Brain
==============================================================
Retrieves region-, authority-, and society-specific Pakistani construction rules
and architectural planning knowledge using Gemini embeddings (`gemini-embedding-001`)
stored locally in `knowledge/pakistan_bylaws_vectors.npz` + `knowledge/pakistan_bylaws.jsonl`.

DESIGN PRINCIPLE:
  This RAG is a PLANNER BRAIN for the LLM — NEVER a stopper, blocker, or hard fixer.
  It gives the LLM accurate regional context (LDA, CDA, SBCA, DHA, Bahria Town,
  PDA, QDA, GDA, FDA/MDA, AJK/ERRA, BCP-2021 Seismic/Fire/Energy, climate & zoning)
  so the AI designs smarter, locally grounded houses while ALWAYS honoring explicit
  client instructions (e.g. custom setbacks, dense room counts, room deletions/additions).
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
JSONL_PATH = KNOWLEDGE_DIR / "pakistan_bylaws.jsonl"
VECTORS_PATH = KNOWLEDGE_DIR / "pakistan_bylaws_vectors.npz"

EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768

_CACHE: Optional[Dict[str, Any]] = None
_QUERY_VEC_CACHE: Dict[str, np.ndarray] = {}


def _load_index() -> Dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    rows: List[Dict[str, Any]] = []
    if JSONL_PATH.exists():
        with open(JSONL_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))

    vectors: Optional[np.ndarray] = None
    if VECTORS_PATH.exists() and rows:
        data = np.load(VECTORS_PATH, allow_pickle=False)
        vecs = np.asarray(data["vectors"], dtype=np.float32)
        if vecs.shape[0] == len(rows):
            vectors = vecs

    _CACHE = {"rows": rows, "vectors": vectors}
    return _CACHE


def _embed_query(query: str, api_key: Optional[str] = None) -> Optional[np.ndarray]:
    q = (query or "").strip()
    if not q:
        return None
    if q in _QUERY_VEC_CACHE:
        return _QUERY_VEC_CACHE[q]

    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}:embedContent?key={key}"
    payload = {
        "model": f"models/{EMBED_MODEL}",
        "content": {"parts": [{"text": q}]},
        "outputDimensionality": EMBED_DIM,
        "taskType": "RETRIEVAL_QUERY",
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        vals = data.get("embedding", {}).get("values")
        if not vals:
            return None
        v = np.asarray(vals, dtype=np.float32)
        n = float(np.linalg.norm(v))
        if n > 0:
            v = v / n
        if len(_QUERY_VEC_CACHE) > 128:
            _QUERY_VEC_CACHE.clear()
        _QUERY_VEC_CACHE[q] = v
        return v
    except Exception:
        return None


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _metadata_affinity(query_lower: str, q_toks: set, row: Dict[str, Any]) -> float:
    """Computes a 0..1 affinity boost when city, society, authority, province, or plot size matches."""
    score = 0.0
    # Society match (strongest signal: e.g. DHA Lahore, Bahria Town, B-17, Lake City, Wapda Town, Askari)
    soc = (row.get("society") or "").lower()
    if soc:
        for s_part in [p.strip() for p in soc.split(",") if p.strip()]:
            if s_part in query_lower:
                score += 0.55
                break

    # Authority acronym / name match (LDA, CDA, SBCA, CBC, PDA, QDA, RDA, FDA, MDA, GDA, ERRA, BCP)
    auth = (row.get("authority") or "").lower()
    for acronym in ("lda", "cda", "sbca", "cbc", "pda", "qda", "rda", "fda", "mda", "gda", "erra", "dha", "bahria", "mpchs", "pec", "bcp"):
        if re.search(rf"\b{acronym}\b", query_lower) and re.search(rf"\b{acronym}\b", auth):
            score += 0.42
            break

    # City / Province match
    city = (row.get("city") or "").lower()
    if city and city != "all":
        for c_part in [p.strip() for p in city.split(",") if p.strip()]:
            if c_part in query_lower:
                score += 0.42
                break
    prov = (row.get("province") or "").lower()
    if prov and prov != "national" and prov in query_lower:
        score += 0.25

    # Plot size match (e.g. "5 marla", "10 marla", "1 kanal", "240 sq yd", "500 sq yd")
    ps = (row.get("plot_sizes") or "").lower()
    if ps and ps != "all":
        for p_part in [p.strip() for p in ps.split(",") if p.strip()]:
            if p_part in query_lower:
                score += 0.18
                break

    # Lexical overlap fallback signal
    doc_toks = _tokens(f"{row.get('title', '')} {row.get('text', '')} {row.get('topic', '')}")
    if q_toks and doc_toks:
        overlap = len(q_toks & doc_toks) / max(1.0, len(q_toks))
        score += 0.20 * min(1.0, overlap)

    return min(1.0, score)


def retrieve_pakistan_rules(
    query: str,
    top_k: int = 6,
    api_key: Optional[str] = None,
    use_embeddings: bool = True,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Retrieves top_k relevant Pakistan construction rules & planning guidelines.
    Returns (entries_with_scores, mode) where mode is 'vector' or 'lexical'.
    """
    idx = _load_index()
    rows = idx["rows"]
    vectors = idx["vectors"]
    if not rows:
        return [], "empty"

    q_lower = (query or "").lower()
    q_toks = _tokens(q_lower)

    q_vec = _embed_query(query, api_key=api_key) if (use_embeddings and vectors is not None) else None
    mode = "vector" if q_vec is not None else "lexical"

    scored: List[Tuple[float, Dict[str, Any]]] = []
    if q_vec is not None and vectors is not None:
        sims = vectors @ q_vec  # cosine similarity (vectors are L2-normalized)
        for i, row in enumerate(rows):
            vec_sim = float(sims[i])
            meta_aff = _metadata_affinity(q_lower, q_toks, row)
            final = 0.68 * vec_sim + 0.32 * meta_aff
            item = dict(row)
            item["score"] = round(final, 4)
            scored.append((final, item))
    else:
        for row in rows:
            meta_aff = _metadata_affinity(q_lower, q_toks, row)
            item = dict(row)
            item["score"] = round(meta_aff, 4)
            scored.append((meta_aff, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[: max(1, top_k)]], mode


def _infer_plot_label(plot_w: float, plot_l: float) -> str:
    if plot_w <= 0 or plot_l <= 0:
        return ""
    area = plot_w * plot_l
    marla = area / 225.0
    sqyd = area / 9.0
    if abs(marla - 20.0) <= 2.5:
        return f"1 kanal ({int(round(sqyd))} sq yd, {plot_w:g}x{plot_l:g} ft)"
    if abs(marla - 40.0) <= 4.0:
        return f"2 kanal ({int(round(sqyd))} sq yd, {plot_w:g}x{plot_l:g} ft)"
    return f"{marla:.1f} marla ({int(round(sqyd))} sq yd, {plot_w:g}x{plot_l:g} ft)"


def build_planner_context(
    brief: str,
    plot_w: float = 0.0,
    plot_l: float = 0.0,
    floors: int = 0,
    top_k: int = 5,
    api_key: Optional[str] = None,
    use_embeddings: bool = True,
) -> Dict[str, Any]:
    """
    Builds an advisory PLANNER BRIEFING from the Pakistan Construction Rules Vector DB.
    Explicitly instructs the LLM to use it as architectural intelligence — NEVER as a blocker.
    """
    plot_label = _infer_plot_label(plot_w, plot_l)
    query_parts = [brief.strip()]
    if plot_label:
        query_parts.append(plot_label)
    if floors:
        query_parts.append(f"{floors} storey residential house")
    query = " | ".join(p for p in query_parts if p)

    hits, mode = retrieve_pakistan_rules(query, top_k=top_k, api_key=api_key, use_embeddings=use_embeddings)
    if not hits:
        return {"context_text": "", "references": [], "mode": mode}

    lines = [
        "=== PAKISTAN ARCHITECTURAL & BYLAW PLANNER BRAIN (ADVISORY CONTEXT — NOT A STOPPER) ===",
        "Use these retrieved regional Pakistan construction rules & planning standards to design smarter,",
        "context-aware layouts (zoning, privacy, climate, ventilation, local norms). IMPORTANT: These are",
        "PLANNER REFERENCES, NOT hard blockers — ALWAYS honor the client's explicit requirements (such as",
        "custom setbacks, zero setbacks, dense room counts, or requested additions/deletions) first.",
    ]
    refs: List[Dict[str, Any]] = []
    for i, h in enumerate(hits, 1):
        cite = h.get("source_title") or h.get("authority")
        if h.get("year"):
            cite = f"{cite} ({h['year']})"
        lines.append(
            f"{i}. [{h['authority']} — {h['title']}] {h['text']} "
            f"(Source: {cite}, {h.get('source_type', 'secondary')})"
        )
        refs.append({
            "id": h["id"],
            "title": h["title"],
            "authority": h["authority"],
            "province": h["province"],
            "city": h["city"],
            "society": h["society"],
            "topic": h["topic"],
            "source_title": h["source_title"],
            "source_url": h["source_url"],
            "source_type": h["source_type"],
            "score": h.get("score", 0.0),
        })

    return {
        "context_text": "\n".join(lines),
        "references": refs,
        "mode": mode,
    }
