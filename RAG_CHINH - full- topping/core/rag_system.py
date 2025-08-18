from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from models.data_models import VietnameseDish, SearchResult
from models.ai_models import ai_models
from utils.text_processor import text_processor
from config.settings import settings

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
        import app
        return getattr(app, 'dish_status_map', {})
    except Exception as e:
        print(f"[DEBUG] Error getting dish_status_map in RAG: {e}")
        return {}

class RAGSystem:
    def __init__(self):
        self.is_initialized = False
        self.retriever: Optional[VectorStoreRetriever] = None
        self.dishes_lookup: Dict[str, VietnameseDish] = {}
    
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
        if not self.is_initialized or not self.retriever:
            return []
        try:
            intent = text_processor.analyze_query_intent(query)
            docs = self.retriever.invoke(query)
            results = []
            for doc in docs:
                dish_name = doc.metadata.get('name', '')
                if dish_name in self.dishes_lookup and self._is_dish_available(dish_name):
                    dish = self.dishes_lookup[dish_name]
                    score = self._calculate_relevance_score(query, dish, intent)
                    result = SearchResult(
                        dish=dish,
                        score=score,
                        relevance=self._get_relevance_reason(query, dish, intent)
                    )
                    results.append(result)
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:settings.MAX_DOCS_FOR_CONTEXT]
        except Exception as e:
            print(f"Lỗi khi tìm kiếm: {e}")
            return []

    def get_context_for_llm(self, query: str) -> str:
        search_results = self.search_relevant_dishes(query)
        if not search_results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở dữ liệu món ăn."
        context_parts = []
        context_parts.append("Thông tin món ăn liên quan:")
        context_parts.append("=" * 50)
        for i, result in enumerate(search_results, 1):
            dish = result.dish
            context_parts.append(f"\n{i}. {dish.name}")
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
            if dish.dish_type:
                classifications.append(f"Loại: {dish.dish_type}")
            if dish.meal_category:
                classifications.append(f"Phân loại: {dish.meal_category}")
            if dish.texture:
                classifications.append(f"Tính chất: {dish.texture}")
            if classifications:
                context_parts.append(f"   Phân loại: {' | '.join(classifications)}")
            if dish.link:
                context_parts.append(f"   Tham khảo: {dish.link}")
            context_parts.append("-" * 30)
        return "\n".join(context_parts)

    def _calculate_relevance_score(self, query: str, dish: VietnameseDish, intent: Dict[str, Any]) -> float:
        score = 0.0
        query_lower = query.lower()
        # Ưu tiên match vùng miền Việt Nam nếu intent/filter là region
        region_filter = intent.get('filters', {}).get('region', None)
        if region_filter and region_filter in dish.region.lower():
            score += 1.2  # tăng mạnh điểm nếu đúng vùng miền
        if dish.name.lower() in query_lower:
            score += 1.0
        for keyword in intent['keywords']:
            if keyword in dish.description.lower():
                score += 0.3
            if keyword in dish.ingredients.lower():
                score += 0.2
        filters = intent.get('filters', {})
        if 'dish_type' in filters and filters['dish_type'] == dish.dish_type.lower():
            score += 0.5
        if 'texture' in filters and filters['texture'] == dish.texture.lower():
            score += 0.3
        regions = ['miền bắc', 'miền nam', 'miền trung', 'hà nội', 'sài gòn']
        for region in regions:
            if region in query_lower and region in dish.region.lower():
                score += 0.4
        return score

    def _get_relevance_reason(self, query: str, dish: VietnameseDish, intent: Dict[str, Any]) -> str:
        reasons = []
        query_lower = query.lower()
        if dish.name.lower() in query_lower:
            reasons.append("tên món xuất hiện trong câu hỏi")
        if intent['type'] == 'recipe' and dish.recipe:
            reasons.append("có công thức chi tiết")
        if intent['type'] == 'ingredient' and dish.ingredients:
            reasons.append("có thông tin nguyên liệu đầy đủ")
        filters = intent.get('filters', {})
        if 'dish_type' in filters and filters['dish_type'] == dish.dish_type.lower():
            reasons.append(f"phù hợp với yêu cầu {filters['dish_type']}")
        if not reasons:
            reasons.append("có nội dung liên quan")
        return ", ".join(reasons)

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'is_initialized': self.is_initialized,
            'total_documents': len(self.dishes_lookup),
            'search_config': {
                'similarity_k': settings.SIMILARITY_SEARCH_K,
                'max_context_docs': settings.MAX_DOCS_FOR_CONTEXT
            }
        }

rag_system = RAGSystem()
