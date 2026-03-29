#ai_reranker.py
import os
from typing import List, Tuple
from sentence_transformers import CrossEncoder

_MODEL_DIR = os.environ.get("FOOD_RERANKER_DIR", "model_fine_turn_0.4/model/reranker_food_attr/best")
_MAX_LEN   = int(os.environ.get("FOOD_RERANKER_MAX_LEN", 224))

class FoodReranker:
    def __init__(self, model_dir: str = _MODEL_DIR, max_len: int = _MAX_LEN):
        self.model = CrossEncoder(model_dir, num_labels=1, max_length=max_len)

    def score_pairs(self, pairs: List[Tuple[str, str]]) -> List[float]:
        return self.model.predict(pairs, batch_size=64, convert_to_numpy=True, show_progress_bar=False).tolist()

    def score_one(self, query: str, ce_text: str) -> float:
        return float(self.score_pairs([(query, ce_text)])[0])

food_reranker = FoodReranker()
