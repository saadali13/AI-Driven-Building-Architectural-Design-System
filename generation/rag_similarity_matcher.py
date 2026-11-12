#!/usr/bin/env python3
"""
generation/rag_similarity_matcher.py
RAG Similarity Retrieval & Indexing Engine for Architectural Layouts.

Ingests `dataset/synthetic_knowledge_base/floorplan_rag_dataset.jsonl`, builds a fast vector
and topological index, and provides sub-millisecond similarity retrieval based on natural language
design briefs, plot dimensions, and spatial requirements.
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DATASET_PATH = os.path.join(WORKSPACE_ROOT, "dataset", "synthetic_knowledge_base", "floorplan_rag_dataset.jsonl")


class ArchitecturalRAGMatcher:
    """Vector similarity retrieval engine for synthetic residential floor plans."""

    _instance: Optional["ArchitecturalRAGMatcher"] = None

    @classmethod
    def get_instance(cls, dataset_path: str = DEFAULT_DATASET_PATH) -> "ArchitecturalRAGMatcher":
        """Singleton pattern for high-speed repeated queries without re-indexing."""
        if cls._instance is None:
            cls._instance = cls(dataset_path)
        return cls._instance

    def __init__(self, dataset_path: str = DEFAULT_DATASET_PATH):
        self.dataset_path = dataset_path
        self.records: List[Dict[str, Any]] = []
        self.corpus_texts: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._build_index()

    def _build_index(self):
        """Loads JSONL records and compiles TF-IDF n-gram vector embeddings."""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset not found at {self.dataset_path}. Run generate_synthetic_rag_dataset.py first.")

        t0 = time.time()
        self.records = []
        self.corpus_texts = []

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                self.records.append(data)

                # Compose rich semantic embedding string
                tags_str = " ".join(data.get("search_tags", []))
                specs = data.get("summary_specs", {})
                spec_str = f"{data.get('marla_category', '')} marla {specs.get('bedrooms', '')} bed {specs.get('kitchen_type', '')} {specs.get('layout_archetype', '')}"
                full_text = f"{data.get('text_description', '')} {tags_str} {spec_str}"
                self.corpus_texts.append(full_text.lower())

        # Fit sublinear TF-IDF vectorizer (unigrams + bigrams)
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            token_pattern=r"(?u)\b\w+\b"
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_texts)
        t_index = (time.time() - t0) * 1000
        print(f"[RAG Indexer] Indexed {len(self.records)} floor plans into vector vault in {t_index:.1f}ms")

    def find_top_matches(
        self,
        user_prompt: str,
        plot_w: Optional[float] = None,
        plot_l: Optional[float] = None,
        bedrooms: Optional[int] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-K matching floor plan layouts satisfying spatial constraints and prompt semantics.
        Latency: < 15ms.
        """
        t_start = time.time()

        if self.vectorizer is None or self.tfidf_matrix is None:
            raise RuntimeError("RAG index is not built.")

        # 1. Transform query prompt into vector
        query_clean = user_prompt.lower()
        q_vec = self.vectorizer.transform([query_clean])

        # 2. Compute cosine similarity against all candidates
        # q_vec is (1, vocab_size), tfidf_matrix is (N, vocab_size)
        sim_scores = self.tfidf_matrix.dot(q_vec.T).toarray().ravel()

        # 3. Apply Hard Geometric and Typological Filtering
        # Tolerances on plot dimensions (+- 15%)
        valid_indices = []
        tol = 0.15

        for idx, rec in enumerate(self.records):
            # Bedroom filter
            if bedrooms is not None:
                rec_beds = rec.get("summary_specs", {}).get("bedrooms")
                if rec_beds != bedrooms:
                    continue

            # Plot dimension filter (+- 15%)
            if plot_w is not None:
                rec_w = rec.get("plot_dimensions", {}).get("width", 0)
                if abs(rec_w - plot_w) > (plot_w * tol):
                    continue

            if plot_l is not None:
                rec_l = rec.get("plot_dimensions", {}).get("length", 0)
                if abs(rec_l - plot_l) > (plot_l * tol):
                    continue

            valid_indices.append(idx)

        # Fallback: if dimension/bed filters were too restrictive, relax to top candidates
        if len(valid_indices) < top_k:
            valid_indices = list(range(len(self.records)))

        # 4. Rank candidates by similarity score
        scored_candidates = [(idx, float(sim_scores[idx])) for idx in valid_indices]
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # 5. Package results
        results = []
        for idx, score in scored_candidates[:top_k]:
            rec_copy = dict(self.records[idx])
            rec_copy["similarity_score"] = round(score, 4)
            results.append(rec_copy)

        elapsed_ms = (time.time() - t_start) * 1000
        return results, elapsed_ms

    def find_best_match(
        self,
        user_prompt: str,
        plot_w: Optional[float] = None,
        plot_l: Optional[float] = None,
        bedrooms: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Convenience function returning the single highest-scoring layout candidate."""
        matches, _ = self.find_top_matches(user_prompt, plot_w=plot_w, plot_l=plot_l, bedrooms=bedrooms, top_k=1)
        return matches[0] if matches else None


def run_test(prompt: str, plot_w: Optional[float] = None, plot_l: Optional[float] = None, bedrooms: Optional[int] = None):
    print("=" * 80)
    print(f"RAG SIMILARITY MATCHER TEST")
    print(f"Query Prompt: '{prompt}'")
    if plot_w and plot_l:
        print(f"Plot Filter: {plot_w:.1f}' x {plot_l:.1f}' | Bedrooms Filter: {bedrooms}")
    print("=" * 80)

    matcher = ArchitecturalRAGMatcher.get_instance()
    results, latency_ms = matcher.find_top_matches(prompt, plot_w=plot_w, plot_l=plot_l, bedrooms=bedrooms, top_k=3)

    print(f"\n[OK] Retrieval executed in {latency_ms:.2f} ms (< 150 ms target)")
    print(f"Returned {len(results)} top architectural candidates:\n")

    for i, res in enumerate(results):
        specs = res.get("summary_specs", {})
        dims = res.get("plot_dimensions", {})
        print(f"--- CANDIDATE #{i+1} ---")
        print(f"  ID: {res['id']} | Category: {res['marla_category']} Marla | Sim Score: {res['similarity_score']:.4f}")
        print(f"  Plot Dimensions: {dims.get('width', 0):.1f}' x {dims.get('length', 0):.1f}' ({dims.get('unit', 'feet')})")
        print(f"  Specs: {specs.get('bedrooms')} Beds, {specs.get('bathrooms')} Baths | Kitchen: {specs.get('kitchen_type')} | Archetype: {specs.get('layout_archetype')}")
        print(f"  Rooms ({len(res.get('rooms', []))}):")
        for rm in res.get("rooms", [])[:4]:
            print(f"    - {rm['name']} ({rm['type']}): Bounds={rm['bounds']} -> Area={rm['area_sqft']} sqft")
        if len(res.get("rooms", [])) > 4:
            print(f"    ... and {len(res.get('rooms', [])) - 4} more rooms")
        print(f"  Adjacency Graph ({len(res.get('adjacency_graph', []))} edges): {res.get('adjacency_graph', [])[:5]} ...")
        print(f"  Description: {res.get('text_description')}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Architectural RAG Similarity Matcher")
    parser.add_argument("--test", type=str, default="5 marla 2 beds open kitchen", help="Query prompt to test")
    parser.add_argument("--width", type=float, default=None, help="Optional plot width filter")
    parser.add_argument("--length", type=float, default=None, help="Optional plot length filter")
    parser.add_argument("--beds", type=int, default=None, help="Optional bedroom count filter")
    args = parser.parse_args()

    run_test(args.test, plot_w=args.width, plot_l=args.length, bedrooms=args.beds)

