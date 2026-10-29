"""
Phase 10: FAISS-Powered Hybrid Vector Store for Architectural Floor Plans.
Supports:
1. Fast, offline architectural feature vectorizer (zero network latency, instant initialization).
2. Deep dense embedding via sentence-transformers (when available and desired).
3. FAISS IndexFlatIP (cosine similarity search).
4. Strict metadata filtering (BHK category, area range, room count).
"""

import os
import re
import math
import hashlib
from typing import Dict, List, Optional, Any
import numpy as np
import faiss


class ArchitecturalVectorStore:
    def __init__(self, embedding_dim: int = 128, use_deep_model: bool = False, model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_dim = embedding_dim
        self.use_deep_model = use_deep_model
        self.model_name = model_name
        self._deep_model = None
        self.index = None
        self.documents: List[Dict[str, Any]] = []

    def _hash_vectorize(self, text: str) -> np.ndarray:
        """
        Fast deterministic hash-based architectural feature vectorizer.
        Extracts unigrams and bigrams, hashing each into the feature dimension with sign hashing.
        Returns L2-normalized float32 vector.
        """
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        tokens = re.findall(r'[a-zA-Z0-9_\-\.\+]+', text.lower())
        
        # Unigrams and bigrams
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

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        if self.use_deep_model:
            try:
                if self._deep_model is None:
                    from sentence_transformers import SentenceTransformer
                    self._deep_model = SentenceTransformer(self.model_name)
                    self.embedding_dim = self._deep_model.get_sentence_embedding_dimension()
                embs = self._deep_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embs.astype(np.float32)
            except Exception:
                # Fallback gracefully to fast hash vectorizer
                pass

        vectors = [self._hash_vectorize(t) for t in texts]
        return np.vstack(vectors).astype(np.float32)

    def initialize_index(self):
        # IndexFlatIP computes inner-product (cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dim)

    def add_documents(self, docs: List[Dict[str, Any]]):
        """
        Adds documents to FAISS index.
        Each doc has: 'plan_id', 'text', 'metadata'.
        """
        if not docs:
            return

        if self.index is None:
            self.initialize_index()

        texts = [d["text"] for d in docs]
        embeddings = self._encode_texts(texts)

        self.index.add(embeddings)
        self.documents.extend(docs)

    def search(
        self,
        query: str,
        top_k: int = 5,
        bhk_filter: Optional[str] = None,
        min_area_m2: Optional[float] = None,
        max_area_m2: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid search: semantic cosine similarity + metadata filtering.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        query_vec = self._encode_texts([query])
        candidate_k = min(top_k * 5, self.index.ntotal)
        scores, indices = self.index.search(query_vec, candidate_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            meta = doc.get("metadata", {})

            # Apply metadata filters
            if bhk_filter and meta.get("bhk_tag") != bhk_filter:
                continue
            if min_area_m2 is not None and meta.get("total_area_m2", 0) < min_area_m2:
                continue
            if max_area_m2 is not None and meta.get("total_area_m2", 0) > max_area_m2:
                continue

            results.append({
                "plan_id": doc["plan_id"],
                "score": float(score),
                "text": doc["text"],
                "metadata": meta
            })

            if len(results) >= top_k:
                break

        return results
