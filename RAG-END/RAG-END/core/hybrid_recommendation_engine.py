"""
Hybrid recommendation wrapper sử dụng EmbeddingRecommendationEngine nếu có dependencies,
fallback về SimpleEmbeddingRecommendationEngine nếu không có
"""

import os
import sys

# Thêm current directory vào Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class HybridRecommendationEngine:
    def __init__(self, db_path='restaurant.db'):
        self.engine = None
        self.db_path = db_path
        self._init_engine()
    
    def _init_engine(self):
        """Khởi tạo engine, ưu tiên EmbeddingRecommendationEngine trước"""
        try:
            # Thử import EmbeddingRecommendationEngine từ embedding_recommendation_engine.py
            from embedding_recommendation_engine import EmbeddingRecommendationEngine
            print("[INFO] Using EmbeddingRecommendationEngine with sentence transformers")
            self.engine = EmbeddingRecommendationEngine(self.db_path)
            self.engine_type = "embedding"
        except ImportError as e:
            print(f"[INFO] Failed to import EmbeddingRecommendationEngine: {e}")
            print("[INFO] Falling back to SimpleEmbeddingRecommendationEngine")
            try:
                # Fallback về SimpleEmbeddingRecommendationEngine
                from embedding_recommendation_wrapper import SimpleEmbeddingRecommendationEngine
                self.engine = SimpleEmbeddingRecommendationEngine(self.db_path)
                self.engine_type = "simple"
            except ImportError as e2:
                print(f"[ERROR] Failed to import both engines: {e2}")
                raise RuntimeError("Cannot initialize any recommendation engine")
    
    def get_recommendations(self, user_query: str, top_k: int = 10):
        """Proxy method để gọi engine"""
        if not self.engine:
            raise RuntimeError("No recommendation engine available")
        
        return self.engine.get_recommendations(user_query, top_k)
    
    def format_recommendation_response(self, recommendations, user_query):
        """Format response gọn gàng cho chatbot"""
        if not recommendations:
            return "Tôi không tìm thấy món ăn phù hợp với yêu cầu của bạn. Bạn có thể thử mô tả chi tiết hơn không?"
        
        # Tạo response header
        response_parts = [
            f"🍽️ **Dựa trên yêu cầu '{user_query}', tôi gợi ý {len(recommendations)} món ăn sau:**\n"
        ]
        
        # Format từng món (gọn gàng hơn)
        for i, (dish, score, explanation) in enumerate(recommendations, 1):
            dish_info = [
                f"**{i}. {dish['name']}**",
                f"💰 **Giá:** {dish['price']:,.0f}đ" if dish['price'] else "💰 **Giá:** Liên hệ",
                f"🌍 **Vùng miền:** {dish['region']}" if dish['region'] else "",
                f"📊 **Điểm phù hợp:** {score:.2f}/1.0",
                f"✨ **Lý do gợi ý:** {explanation}",
            ]
            
            # Lọc bỏ những dòng trống
            dish_info = [info for info in dish_info if info and not info.endswith(": ")]
            response_parts.append("\n".join(dish_info))
        
        response = "\n\n".join(response_parts)
        response += f"\n\n💡 **Gợi ý:** Bạn có thể hỏi thêm về cách làm hoặc thông tin dinh dưỡng!"
        response += f"\n🔧 **Engine:** {self.engine_type.title()}"
        
        return response

# Tạo global instance
recommendation_engine = HybridRecommendationEngine()