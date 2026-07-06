"""
Hybrid retrieval: BM25 (keyword) + sentence-transformer (semantic), combined
with a simple weighted score. Same pattern as the SHL FastAPI project —
reused here since it already handles exact-match terms (customer names,
ticket IDs) well alongside semantic similarity.
"""
import json, os
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "corpus.jsonl")

class HybridRetriever:
    def __init__(self, data_path=DATA_PATH, model_name="all-MiniLM-L6-v2"):
        self.docs = []
        with open(data_path) as f:
            for line in f:
                self.docs.append(json.loads(line))

        self.tokenized = [d["text"].lower().split() for d in self.docs]
        self.bm25 = BM25Okapi(self.tokenized)

        self.model = SentenceTransformer(model_name)
        self.embeddings = self.model.encode(
            [d["text"] for d in self.docs], convert_to_numpy=True, normalize_embeddings=True
        )

    def search(self, query, top_k=8, source_type=None, bm25_weight=0.4, sem_weight=0.6):
        bm25_scores = np.array(self.bm25.get_scores(query.lower().split()))
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()

        q_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        sem_scores = (self.embeddings @ q_emb.T).flatten()

        combined = bm25_weight * bm25_scores + sem_weight * sem_scores

        idx_sorted = np.argsort(-combined)
        results = []
        for i in idx_sorted:
            d = self.docs[i]
            if source_type and d["source_type"] != source_type:
                continue
            results.append({**d, "score": float(combined[i])})
            if len(results) >= top_k:
                break
        return results

    def all_by_theme(self):
        """Aggregation helper: count docs per theme, used by the analyst agent
        for frequency-style questions ('most common complaint')."""
        counts = {}
        for d in self.docs:
            theme = d.get("theme")
            if theme:
                counts[theme] = counts.get(theme, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))


if __name__ == "__main__":
    r = HybridRetriever()
    res = r.search("checkout payment failing", top_k=3)
    for d in res:
        print(round(d["score"], 3), d["id"], d["text"][:60])
    print("\nTheme frequency:", r.all_by_theme())
