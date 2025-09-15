from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from models.data_models import VietnameseDish, SearchResult
from models.ai_models import ai_models
from utils.text_processor import text_processor
from config.settings import settings
from core.embedding_cache import embedding_cache

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
            
            # Tạo dishes lookup
            self.dishes_lookup = {}
            for dish in dishes:
                self.dishes_lookup[dish.name] = dish
            
            # Kiểm tra cache trước
            if embedding_cache.is_cache_valid(dishes):
                print("🚀 Using cached embeddings...")
                vector_store = embedding_cache.load_vector_store()
                if vector_store:
                    self.retriever = vector_store.as_retriever(
                        search_kwargs={"k": settings.SIMILARITY_SEARCH_K}
                    )
                    self.is_initialized = True
                    print(f"✅ RAG System initialized with cached embeddings for {len(dishes)} dishes")
                    return True
            
            # Nếu không có cache hoặc cache không hợp lệ, tạo mới
            print("🔄 Creating new embeddings (this may take a while)...")
            documents = []
            for dish in dishes:
                content = text_processor.create_search_content(dish)
                doc = Document(
                    page_content=content,
                    metadata=dish.to_metadata_dict()
                )
                documents.append(doc)
            
            vector_store = ai_models.get_vector_store()
            vector_store.add_documents(documents)
            
            # Lưu vào cache
            embedding_cache.save_vector_store(vector_store, dishes)
            
            self.retriever = vector_store.as_retriever(
                search_kwargs={"k": settings.SIMILARITY_SEARCH_K}
            )
            self.is_initialized = True
            print(f"✅ RAG System initialized with new embeddings for {len(documents)} dishes")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing RAG System: {e}")
            # Nếu lỗi có thể do quota, thử load cache cũ
            if "quota" in str(e).lower() or "limit" in str(e).lower() or "429" in str(e):
                print("🔄 Quota exceeded, trying to use existing cache...")
                vector_store = embedding_cache.load_vector_store()
                if vector_store:
                    self.retriever = vector_store.as_retriever(
                        search_kwargs={"k": settings.SIMILARITY_SEARCH_K}
                    )
                    self.is_initialized = True
                    print(f"✅ RAG System recovered using cached embeddings")
                    return True
            return False

    def search_relevant_dishes(self, query: str, exclude_dishes: List[str] = None) -> List[SearchResult]:
        if not self.is_initialized or not self.retriever:
            return []
        try:
            intent = text_processor.analyze_query_intent(query)
            docs = self.retriever.invoke(query)
            results = []
            
            # Chuẩn hóa danh sách món cần loại trừ
            excluded_normalized = []
            if exclude_dishes:
                excluded_normalized = [text_processor.normalize(dish) for dish in exclude_dishes]
                print(f"[DEBUG] Excluding dishes: {exclude_dishes}")
            
            # LOGIC ĐẶC BIỆT CHO MÓN CHAY: Nếu user hỏi về món chay, đảm bảo include tất cả món chay
            vegetarian_keywords = ['chay', 'vegetarian', 'thuần chay']
            is_vegetarian_query = any(veg_keyword in query.lower() for veg_keyword in vegetarian_keywords)
            
            if is_vegetarian_query:
                print(f"[DEBUG] Detected vegetarian query, ensuring all vegetarian dishes are included")
                # Tìm tất cả món chay trong database
                all_vegetarian_dishes = []
                for dish_name, dish in self.dishes_lookup.items():
                    if self._is_dish_available(dish_name):
                        # Kiểm tra xem có phải món chay không
                        is_vegetarian = False
                        if (hasattr(dish, 'meal_category') and dish.meal_category and 'chay' in dish.meal_category.lower()) or \
                           (hasattr(dish, 'dish_type') and dish.dish_type and 'chay' in dish.dish_type.lower()) or \
                           ('chay' in dish.name.lower()) or \
                           (dish.description and 'chay' in dish.description.lower()):
                            is_vegetarian = True
                        
                        if is_vegetarian:
                            # Kiểm tra exclude
                            dish_normalized = text_processor.normalize(dish_name)
                            if exclude_dishes and dish_normalized in excluded_normalized:
                                print(f"[DEBUG] Skipping excluded vegetarian dish: {dish_name}")
                                continue
                            
                            score = self._calculate_relevance_score(query, dish, intent)
                            result = SearchResult(
                                dish=dish,
                                score=score,
                                relevance=self._get_relevance_reason(query, dish, intent)
                            )
                            all_vegetarian_dishes.append(result)
                            print(f"[DEBUG] Added vegetarian dish: {dish_name} (score: {score})")
                
                # Thêm các món chay vào kết quả
                results.extend(all_vegetarian_dishes)
            
            # Xử lý các món khác từ vector search
            for doc in docs:
                dish_name = doc.metadata.get('name', '')
                if dish_name in self.dishes_lookup and self._is_dish_available(dish_name):
                    # Kiểm tra xem đã có trong results chưa (tránh duplicate)
                    if any(result.dish.name == dish_name for result in results):
                        continue
                        
                    # Kiểm tra exclude
                    dish_normalized = text_processor.normalize(dish_name)
                    if exclude_dishes and dish_normalized in excluded_normalized:
                        print(f"[DEBUG] Skipping excluded dish: {dish_name}")
                        continue
                        
                    dish = self.dishes_lookup[dish_name]
                    score = self._calculate_relevance_score(query, dish, intent)
                    result = SearchResult(
                        dish=dish,
                        score=score,
                        relevance=self._get_relevance_reason(query, dish, intent)
                    )
                    results.append(result)
            
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Thêm randomization để tăng tính đa dạng
            import random
            if len(results) > settings.MAX_DOCS_FOR_CONTEXT:
                # Lấy top 50% theo score cao nhất
                top_results = results[:len(results)//2] if len(results) > 20 else results
                # Random trong top results để tăng diversity
                random.shuffle(top_results)
                # Kết hợp với một số results ngẫu nhiên từ phần còn lại
                remaining_results = results[len(results)//2:]
                if remaining_results:
                    random.shuffle(remaining_results)
                    # Lấy thêm 25% từ remaining
                    extra_count = min(len(remaining_results), settings.MAX_DOCS_FOR_CONTEXT//4)
                    top_results.extend(remaining_results[:extra_count])
                results = top_results
            
            return results[:settings.MAX_DOCS_FOR_CONTEXT]
        except Exception as e:
            print(f"Lỗi khi tìm kiếm: {e}")
            return []

    def get_context_for_llm(self, query: str, exclude_dishes: List[str] = None) -> str:
        search_results = self.search_relevant_dishes(query, exclude_dishes)
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
        
        # TĂNG ĐIỂM CHO MÓN CHAY KHI USER HỎI VỀ MÓN CHAY - DỰA TRÊN TRƯỜNG CHÍNH XÁC
        vegetarian_keywords = ['chay', 'vegetarian', 'thuần chay']
        if any(veg_keyword in query_lower for veg_keyword in vegetarian_keywords):
            # Kiểm tra trường meal_category hoặc dish_type có chứa "chay" chính xác
            is_vegetarian = False
            base_vegetarian_score = 10.0  # Base score rất cao cho món chay
            
            # Ưu tiên kiểm tra meal_category trước
            if hasattr(dish, 'meal_category') and dish.meal_category and 'chay' in dish.meal_category.lower():
                score += base_vegetarian_score
                is_vegetarian = True
                print(f"[DEBUG] VEGETARIAN MATCH meal_category: {dish.name} = {dish.meal_category}")
            
            # Kiểm tra dish_type
            elif hasattr(dish, 'dish_type') and dish.dish_type and 'chay' in dish.dish_type.lower():
                score += base_vegetarian_score
                is_vegetarian = True
                print(f"[DEBUG] VEGETARIAN MATCH dish_type: {dish.name} = {dish.dish_type}")
            
            # Kiểm tra tên món có từ "chay" - QUAN TRỌNG để bắt "Bún chay lá chanh"
            elif 'chay' in dish.name.lower():
                score += base_vegetarian_score
                is_vegetarian = True
                print(f"[DEBUG] VEGETARIAN MATCH name: {dish.name}")
            
            # Kiểm tra mô tả có từ "chay"
            elif dish.description and 'chay' in dish.description.lower():
                score += base_vegetarian_score * 0.8  # Điểm thấp hơn một chút nhưng vẫn cao
                is_vegetarian = True
                print(f"[DEBUG] VEGETARIAN MATCH description: {dish.name}")
            
            # Thêm điểm cho nguyên liệu chay điển hình
            if dish.ingredients:
                vegetarian_ingredients = ['tàu hũ', 'đậu hũ', 'nấm', 'rau', 'đậu phộng', 'cà rốt', 'bắp cải', 'rau muống', 'rau cải', 'bún gạo', 'lá chanh']
                veg_ingredient_count = sum(1 for ing in vegetarian_ingredients if ing in dish.ingredients.lower())
                if veg_ingredient_count >= 1:  # Chỉ cần 1 nguyên liệu chay
                    score += min(veg_ingredient_count * 2.0, 5.0)  # Tối đa +5 điểm
                    print(f"[DEBUG] VEGETARIAN ingredient bonus: {dish.name} = {veg_ingredient_count} ingredients (+{min(veg_ingredient_count * 2.0, 5.0)} points)")
            
            # LOẠI TRỪ MÓN CÓ THỊT CÁ - nhưng chỉ khi không phải món chay rõ ràng
            if not is_vegetarian:
                dish_text = f"{dish.name} {dish.description} {dish.ingredients}".lower()
                meat_keywords = ['thịt', 'cá', 'tôm', 'gà', 'heo', 'bò', 'vịt', 'khô cá', 'tôm chua', 'hải sản']
                has_meat = any(meat in dish_text for meat in meat_keywords)
                
                if has_meat:
                    score -= 3.0  # Penalty cho món có thịt
                    print(f"[DEBUG] MEAT DETECTED, reducing score: {dish.name}")
            
            print(f"[DEBUG] Final vegetarian score for {dish.name}: {score} (is_vegetarian: {is_vegetarian})")
        
        # Ưu tiên match vùng miền Việt Nam nếu intent/filter là region
        region_filter = intent.get('filters', {}).get('region', None)
        if region_filter and region_filter in dish.region.lower():
            score += 1.2  # tăng mạnh điểm nếu đúng vùng miền
        if dish.name.lower() in query_lower:
            score += 1.0
        for keyword in intent['keywords']:
            if keyword in dish.description.lower():
                score += 0.3
            if dish.ingredients and keyword in dish.ingredients.lower():
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
