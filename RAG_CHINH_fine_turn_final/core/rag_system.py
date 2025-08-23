# rag_system.py
# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional, Tuple
import os
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from models.data_models import VietnameseDish, SearchResult
from models.ai_models import ai_models
from utils.text_processor import text_processor
from config.settings import settings

# === (NEW) Cross-Encoder Reranker ===
# - Chỉ cần thư mục model có: config.json, model.safetensors, tokenizer.json, vocab.txt, ...
# - Mặc định trỏ tới bản BEST; đổi qua env nếu bạn muốn:
#     export FOOD_RERANKER_DIR="model_fine_turn_0.4/model/reranker_food_attr/best"
#     export FOOD_RERANKER_MAX_LEN=224
try:
    from sentence_transformers import CrossEncoder  # type: ignore
except Exception as _e:
    CrossEncoder = None  # fallback nếu môi trường chưa cài đặt

DEFAULT_RERANKER_DIR = os.environ.get(
    "FOOD_RERANKER_DIR",
    "model_fine_turn_0.4/model/reranker_food_attr/best"
)
DEFAULT_MAX_LEN = int(os.environ.get("FOOD_RERANKER_MAX_LEN", "224"))

def _nz(v: Any) -> str:
    return (str(v).strip() if v is not None else "")

def _price_bucket(v: Any) -> str:
    try:
        x = float(str(v).replace(",", "."))
    except Exception:
        return ""
    if x <= 40000:
        return "rẻ"
    if x <= 80000:
        return "trung"
    return "nhỉnh"

def _time_bucket(v: Any) -> str:
    try:
        m = int(float(str(v).replace(",", ".")))
    except Exception:
        return ""
    if m <= 20:
        return "nhanh"
    if m <= 40:
        return "trung"
    return "bận"

def _clip(s: str, n: int) -> str:
    s = (s or "").replace("\n", " ").strip()
    return s[:n]

def build_ce_text_from_dish(d: VietnameseDish) -> str:
    """
    Khớp format data train: TAGS mạnh ở đầu -> 'Món ăn: <name>' -> body mô tả ngắn.
    Không đưa recipe dài để tránh nhiễu.
    """
    region   = _nz(getattr(d, "region", ""))
    mood     = _nz(getattr(d, "mood", "")) or _nz(getattr(d, "taste_mood", ""))
    typ      = _nz(getattr(d, "dish_type", "")) or _nz(getattr(d, "type", ""))
    veg      = _nz(getattr(d, "meal_category", "")) or _nz(getattr(d, "veg", ""))
    texture  = _nz(getattr(d, "texture", ""))
    p_bucket = _price_bucket(getattr(d, "price", ""))
    t_bucket = _time_bucket(getattr(d, "cook_time", ""))

    desc = _clip(_nz(getattr(d, "description", "")), 160)

    tags = "".join([
        f"[Region: {region or 'unknown'}]",
        f"[Mood: {mood or 'unknown'}]",
        f"[Type: {typ or 'unknown'}]",
        f"[Veg: {veg or 'unknown'}]",
        f"[Texture: {texture or 'unknown'}]",
        f"[PriceBucket: {p_bucket or 'unknown'}]",
        f"[TimeBucket: {t_bucket or 'unknown'}]",
    ])
    body = f"Mô tả: {desc}." if desc else ""
    ce_text = (tags + "\n" + f"Món ăn: {d.name}" + ("\n" + body if body else "")).strip()
    return ce_text

# Function to get dish_status_map dynamically
def get_dish_status_map():
    try:
        import sys
        import os
        # Thêm đường dẫn root để import app
        root_path = os.path.dirname(os.path.dirname(__file__))
        if root_path not in sys.path:
            sys.path.insert(0, root_path)

        # Import app module và lấy dish_status_map
        import app  # type: ignore
        return getattr(app, 'dish_status_map', {})
    except Exception as e:
        print(f"[DEBUG] Error getting dish_status_map in RAG: {e}")
        return {}

class RAGSystem:
    def __init__(self):
        self.is_initialized = False
        self.retriever: Optional[VectorStoreRetriever] = None
        self.dishes_lookup: Dict[str, VietnameseDish] = {}
        # (NEW) lazy cross-encoder
        self._reranker: Optional["CrossEncoder"] = None
        self._reranker_dir = DEFAULT_RERANKER_DIR
        self._reranker_max_len = DEFAULT_MAX_LEN

    # ---------- Reranker helpers ----------
    def _ensure_reranker(self):
        """Khởi tạo cross-encoder khi cần (lười tải)."""
        if self._reranker is None and CrossEncoder is not None:
            try:
                self._reranker = CrossEncoder(
                    self._reranker_dir,
                    num_labels=1,
                    max_length=self._reranker_max_len
                )
                print(f"[RERANKER] Loaded from: {self._reranker_dir}")
            except Exception as e:
                print(f"[RERANKER] Load failed: {e}")
                self._reranker = None

    def _rerank_scores(self, query: str, ce_texts: List[str]) -> Optional[List[float]]:
        """Trả về list score (float) theo thứ tự ce_texts; None nếu không dùng được model."""
        self._ensure_reranker()
        if not self._reranker:
            return None
        try:
            pairs: List[Tuple[str, str]] = [(query, c) for c in ce_texts]
            scores = self._reranker.predict(
                pairs, batch_size=64, show_progress_bar=False, convert_to_numpy=True
            )
            return [float(s) for s in scores]
        except Exception as e:
            print(f"[RERANKER] Predict error: {e}")
            return None

    def _is_dish_available(self, dish_name: str) -> bool:
        """Check if a dish is available (not disabled by admin)"""
        dish_status_map = get_dish_status_map()
        return dish_status_map.get(dish_name, True)  # Default to True if not in map

    def initialize(self, dishes: List[VietnameseDish]) -> bool:
        try:
            if not ai_models.is_initialized():
                raise ValueError("AI Models chưa được khởi tạo")
            documents = []
            self.dishes_lookup = {}
            for dish in dishes:
                content = text_processor.create_search_content(dish)
                doc = Document(
                    page_content=content,
                    metadata=dish.to_metadata_dict()
                )
                documents.append(doc)
                self.dishes_lookup[dish.name] = dish
            vector_store = ai_models.get_vector_store()
            vector_store.add_documents(documents)
            self.retriever = vector_store.as_retriever(
                search_kwargs={"k": settings.SIMILARITY_SEARCH_K}
            )
            self.is_initialized = True
            print(f"RAG System đã được khởi tạo với {len(documents)} món ăn")
            return True
        except Exception as e:
            print(f"Lỗi khi khởi tạo RAG System: {e}")
            return False

    def search_relevant_dishes(self, query: str) -> List[SearchResult]:
        """
        Bước 1: Lấy top-k ứng viên từ retriever.
        Bước 2: Rerank các ứng viên bằng cross-encoder fine-tune (nếu sẵn sàng).
        Score trả về là 'điểm AI'.
        """
        if not self.is_initialized or not self.retriever:
            return []
        try:
            # Lấy ứng viên ban đầu
            _ = text_processor.analyze_query_intent(query)  # vẫn giữ phân tích intent cho nơi khác nếu cần
            docs = self.retriever.invoke(query)

            # Tạo danh sách ứng viên hợp lệ + CE text tương ứng
            cands: List[Tuple[VietnameseDish, str]] = []
            for doc in docs:
                dish_name = doc.metadata.get('name', '')
                if dish_name in self.dishes_lookup and self._is_dish_available(dish_name):
                    dish = self.dishes_lookup[dish_name]
                    ce_text = build_ce_text_from_dish(dish)
                    cands.append((dish, ce_text))

            if not cands:
                return []

            # Rerank bằng model fine-tuned
            ce_texts = [c[1] for c in cands]
            scores = self._rerank_scores(query, ce_texts)

            results: List[SearchResult] = []
            if scores is not None:
                # Dùng điểm AI từ model
                for (dish, _), sc in zip(cands, scores):
                    results.append(SearchResult(
                        dish=dish,
                        score=float(sc),
                        relevance=f"AI score={float(sc):.3f}"
                    ))
                results.sort(key=lambda x: x.score, reverse=True)
            else:
                # Fallback: nếu không có model, dùng heuristic cũ rất nhẹ (name match)
                ql = query.lower()
                for (dish, _) in cands:
                    sc = 1.0 if dish.name.lower() in ql else 0.0
                    results.append(SearchResult(
                        dish=dish,
                        score=sc,
                        relevance="fallback"
                    ))
                results.sort(key=lambda x: x.score, reverse=True)

            return results[:settings.MAX_DOCS_FOR_CONTEXT]

        except Exception as e:
            print(f"Lỗi khi tìm kiếm: {e}")
            return []

    def get_context_for_llm(self, query: str) -> str:
        search_results = self.search_relevant_dishes(query)
        if not search_results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở dữ liệu món ăn."
        context_parts: List[str] = []
        context_parts.append("Thông tin món ăn liên quan:")
        context_parts.append("=" * 50)
        for i, result in enumerate(search_results, 1):
            dish = result.dish
            ai_score = getattr(result, "score", None)
            score_line = f"   Điểm AI: {ai_score:.3f}" if ai_score is not None else ""
            context_parts.append(f"\n{i}. {dish.name}")
            if score_line:
                context_parts.append(score_line)
            context_parts.append(f"   Vùng miền: {dish.region}")
            context_parts.append(f"   Mô tả: {dish.description}")
            if dish.ingredients:
                context_parts.append(f"   Nguyên liệu: {dish.ingredients}")
            if dish.recipe:
                recipe = dish.recipe[:300] + "..." if len(dish.recipe) > 300 else dish.recipe
                context_parts.append(f"   Cách làm: {recipe}")
            if dish.price:
                context_parts.append(f"   Giá: {dish.price}")
            if dish.unit:
                context_parts.append(f"   Đơn vị tính: {dish.unit}")
            if dish.cook_time:
                context_parts.append(f"   Thời gian nấu: {dish.cook_time}")
            if dish.calories:
                context_parts.append(f"   Calories: {dish.calories}")
            if dish.fat:
                context_parts.append(f"   Fat: {dish.fat}")
            if dish.fiber:
                context_parts.append(f"   Fiber: {dish.fiber}")
            if dish.sugar:
                context_parts.append(f"   Sugar: {dish.sugar}")
            if dish.protein:
                context_parts.append(f"   Protein: {dish.protein}")
            classifications = []
            if getattr(dish, "dish_type", ""):
                classifications.append(f"Loại: {dish.dish_type}")
            if getattr(dish, "meal_category", ""):
                classifications.append(f"Phân loại: {dish.meal_category}")
            if getattr(dish, "texture", ""):
                classifications.append(f"Tính chất: {dish.texture}")
            if classifications:
                context_parts.append(f"   Phân loại: {' | '.join(classifications)}")
            if getattr(dish, "link", ""):
                context_parts.append(f"   Tham khảo: {dish.link}")
            context_parts.append("-" * 30)
        return "\n".join(context_parts)

    # (Giữ lại cho thống kê hệ thống)
    def get_statistics(self) -> Dict[str, Any]:
        return {
            'is_initialized': self.is_initialized,
            'total_documents': len(self.dishes_lookup),
            'search_config': {
                'similarity_k': settings.SIMILARITY_SEARCH_K,
                'max_context_docs': settings.MAX_DOCS_FOR_CONTEXT,
                'reranker_loaded': bool(self._reranker is not None),
                'reranker_dir': self._reranker_dir
            }
        }

rag_system = RAGSystem()
