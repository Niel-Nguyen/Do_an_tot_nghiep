from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from models.data_models import VietnameseDish, SearchResult
from models.ai_models import ai_models
from utils.text_processor import text_processor
from config.settings import settings

class RAGSystem:
    """Hệ thống Retrieval-Augmented Generation cho món ăn Việt Nam"""
    
    def __init__(self):
        self.is_initialized = False
        self.retriever: Optional[VectorStoreRetriever] = None
        self.dishes_lookup: Dict[str, VietnameseDish] = {}
    
    def initialize(self, dishes: List[VietnameseDish]) -> bool:
        """Khởi tạo hệ thống RAG với dữ liệu món ăn"""
        try:
            if not ai_models.is_initialized():
                raise ValueError("AI Models chưa được khởi tạo")
            
            # Tạo documents từ danh sách món ăn
            documents = []
            self.dishes_lookup = {}
            
            for dish in dishes:
                # Tạo nội dung tìm kiếm tối ưu
                content = text_processor.create_search_content(dish)
                
                # Tạo Document cho LangChain
                doc = Document(
                    page_content=content,
                    metadata=dish.to_metadata_dict()
                )
                
                documents.append(doc)
                self.dishes_lookup[dish.name] = dish
            
            # Thêm documents vào vector store
            vector_store = ai_models.get_vector_store()
            vector_store.add_documents(documents)
            
            # Tạo retriever
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
        """Tìm kiếm món ăn liên quan đến câu hỏi"""
        if not self.is_initialized or not self.retriever:
            return []
        
        try:
            # Phân tích ý định câu hỏi
            intent = text_processor.analyze_query_intent(query)
            
            # Tìm kiếm với retriever
            docs = self.retriever.invoke(query)
            
            # Chuyển đổi kết quả
            results = []
            for doc in docs:
                dish_name = doc.metadata.get('name', '')
                if dish_name in self.dishes_lookup:
                    dish = self.dishes_lookup[dish_name]
                    
                    # Tính toán điểm relevance (giả lập)
                    score = self._calculate_relevance_score(query, dish, intent)
                    
                    result = SearchResult(
                        dish=dish,
                        score=score,
                        relevance=self._get_relevance_reason(query, dish, intent)
                    )
                    results.append(result)
            
            # Sắp xếp theo điểm số
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results[:settings.MAX_DOCS_FOR_CONTEXT]
            
        except Exception as e:
            print(f"Lỗi khi tìm kiếm: {e}")
            return []
    
    def get_context_for_llm(self, query: str) -> str:
        """Tạo context cho LLM từ kết quả tìm kiếm"""
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
                # Rút gọn công thức nếu quá dài
                recipe = dish.recipe[:300] + "..." if len(dish.recipe) > 300 else dish.recipe
                context_parts.append(f"   Cách làm: {recipe}")
            
            # Thêm thông tin phân loại
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
        """Tính điểm relevance cho món ăn"""
        score = 0.0
        query_lower = query.lower()
        
        # Điểm cơ bản nếu tên món xuất hiện trong câu hỏi
        if dish.name.lower() in query_lower:
            score += 1.0
        
        # Điểm cho từ khóa trong mô tả
        for keyword in intent['keywords']:
            if keyword in dish.description.lower():
                score += 0.3
            if keyword in dish.ingredients.lower():
                score += 0.2
        
        # Điểm cho filters phù hợp
        filters = intent.get('filters', {})
        if 'dish_type' in filters and filters['dish_type'] == dish.dish_type.lower():
            score += 0.5
        if 'texture' in filters and filters['texture'] == dish.texture.lower():
            score += 0.3
        
        # Điểm cho vùng miền
        regions = ['miền bắc', 'miền nam', 'miền trung', 'hà nội', 'sài gòn']
        for region in regions:
            if region in query_lower and region in dish.region.lower():
                score += 0.4
        
        return score
    
    def _get_relevance_reason(self, query: str, dish: VietnameseDish, intent: Dict[str, Any]) -> str:
        """Tạo lý do tại sao món ăn này phù hợp"""
        reasons = []
        query_lower = query.lower()
        
        if dish.name.lower() in query_lower:
            reasons.append("tên món xuất hiện trong câu hỏi")
        
        if intent['type'] == 'recipe' and dish.recipe:
            reasons.append("có công thức chi tiết")
        
        if intent['type'] == 'ingredient' and dish.ingredients:
            reasons.append("có thông tin nguyên liệu đầy đủ")
        
        # Kiểm tra filters
        filters = intent.get('filters', {})
        if 'dish_type' in filters and filters['dish_type'] == dish.dish_type.lower():
            reasons.append(f"phù hợp với yêu cầu {filters['dish_type']}")
        
        if not reasons:
            reasons.append("có nội dung liên quan")
        
        return ", ".join(reasons)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Thống kê hệ thống RAG"""
        return {
            'is_initialized': self.is_initialized,
            'total_documents': len(self.dishes_lookup),
            'search_config': {
                'similarity_k': settings.SIMILARITY_SEARCH_K,
                'max_context_docs': settings.MAX_DOCS_FOR_CONTEXT
            }
        }

# Global instance
rag_system = RAGSystem()