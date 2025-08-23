
from sentence_transformers import CrossEncoder

class RerankerService:
    def __init__(self, model_path="ai_training/models/reranker_food", enabled=True):
        self.enabled = enabled
        self.model = None
        if enabled:
            try:
                self.model = CrossEncoder(model_path, num_labels=1, max_length=256)
            except Exception as e:
                print("[RERANKER] Load failed:", e)
                self.enabled = False

    def rerank(self, query, candidates, top_n=3):
        """
        candidates: list[str] or list[dict with 'text']
        return: top_n ranked candidates (same type as input)
        """
        if not self.enabled or not candidates:
            return candidates[:top_n]
        texts = [(query, (c["text"] if isinstance(c, dict) else str(c))) for c in candidates]
        scores = self.model.predict(texts)
        idxs = sorted(range(len(candidates)), key=lambda i: scores[i], reverse=True)
        return [candidates[i] for i in idxs[:top_n]]
