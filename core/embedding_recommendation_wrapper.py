"""
Module chứa SimpleEmbeddingRecommendationEngine để thay thế recommendation engine cũ
"""

import sqlite3
import re
import math
from typing import List, Dict, Any, Tuple
from collections import Counter

class SimpleEmbeddingRecommendationEngine:
    def __init__(self, db_path='restaurant.db'):
        self.db_path = db_path
        self.dishes = []
        self._load_dishes()
        
        # Rule-based weights
        self.regional_keywords = {
            'north': ['bắc', 'hà nội', 'phở', 'bún chả', 'chả cá', 'nem rán', 'bánh cuốn', 'bún đậu', 'miến gà'],
            'central': ['trung', 'huế', 'bún bò huế', 'bánh khoái', 'bánh bèo', 'mì quảng', 'cao lầu', 'bánh căn'],
            'south': ['nam', 'sài gòn', 'cơm tấm', 'bánh xèo', 'hủ tiếu', 'bánh khọt', 'bún thịt nướng', 'gỏi cuốn']
        }
        
        # Stopwords tiếng Việt
        self.stopwords = set([
            'tôi', 'muốn', 'ăn', 'món', 'và', 'với', 'có', 'là', 'của', 'trong', 'cho', 'về', 'đến',
            'từ', 'một', 'hai', 'ba', 'nhiều', 'ít', 'rất', 'khá', 'cũng', 'thì', 'nên', 'sẽ', 'đã'
        ])
    
    def _load_dishes(self):
        """Load dishes from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, description, price, region, ingredients, 
                       main_or_side, dry_or_soup, vegetarian_or_meat, mood
                FROM dishes 
                ORDER BY name
            """)
            
            rows = cursor.fetchall()
            self.dishes = []
            
            for row in rows:
                dish = {
                    'id': row[0],
                    'name': row[1] or '',
                    'description': row[2] or '',
                    'price': row[3] or 0,
                    'region': row[4] or '',
                    'ingredients': row[5] or '',
                    'main_or_side': row[6] or '',
                    'dry_or_soup': row[7] or '',
                    'vegetarian_or_meat': row[8] or '',
                    'mood': row[9] or ''
                }
                self.dishes.append(dish)
            
            print(f"[INFO] Loaded {len(self.dishes)} dishes")
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Failed to load dishes: {e}")
            self.dishes = []
    
    def _preprocess_text(self, text: str) -> List[str]:
        """Tiền xử lý text: lowercase, remove punctuation, tokenize, remove stopwords"""
        if not text:
            return []
        
        # Lowercase và remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Tokenize
        words = text.split()
        
        # Remove stopwords
        words = [word for word in words if word not in self.stopwords and len(word) > 1]
        
        return words
    
    def _create_dish_text(self, dish: Dict) -> str:
        """Tạo text representation của món ăn"""
        text_parts = []
        
        if dish['name']:
            text_parts.append(dish['name'])
        
        if dish['description']:
            text_parts.append(dish['description'])
            
        if dish['region']:
            text_parts.append(f"vùng miền {dish['region']}")
            
        if dish['main_or_side']:
            text_parts.append(f"{dish['main_or_side']}")
            
        if dish['dry_or_soup']:
            text_parts.append(f"{dish['dry_or_soup']}")
            
        if dish['vegetarian_or_meat']:
            text_parts.append(f"{dish['vegetarian_or_meat']}")
            
        if dish['mood']:
            text_parts.append(f"{dish['mood']}")
            
        if dish['ingredients']:
            text_parts.append(f"{dish['ingredients']}")
        
        return ' '.join(text_parts)
    
    def _calculate_tf_idf_similarity(self, query: str, dish_text: str) -> float:
        """Tính TF-IDF similarity đơn giản"""
        query_words = self._preprocess_text(query)
        dish_words = self._preprocess_text(dish_text)
        
        if not query_words or not dish_words:
            return 0.0
        
        # Tính intersection
        common_words = set(query_words) & set(dish_words)
        
        if not common_words:
            return 0.0
        
        # Simple similarity: số từ chung / sqrt(len(query) * len(dish))
        similarity = len(common_words) / math.sqrt(len(set(query_words)) * len(set(dish_words)))
        
        return similarity
    
    def _calculate_jaccard_similarity(self, query: str, dish_text: str) -> float:
        """Tính Jaccard similarity"""
        query_words = set(self._preprocess_text(query))
        dish_words = set(self._preprocess_text(dish_text))
        
        if not query_words or not dish_words:
            return 0.0
        
        intersection = len(query_words & dish_words)
        union = len(query_words | dish_words)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_semantic_similarity_score(self, query: str, dish: Dict) -> float:
        """Tính semantic similarity score"""
        dish_text = self._create_dish_text(dish)
        
        # Kết hợp TF-IDF và Jaccard
        tfidf_score = self._calculate_tf_idf_similarity(query, dish_text)
        jaccard_score = self._calculate_jaccard_similarity(query, dish_text)
        
        # Weighted combination
        semantic_score = (tfidf_score * 0.7) + (jaccard_score * 0.3)
        
        return semantic_score
    
    def _get_regional_score(self, dish: Dict, user_query: str) -> float:
        """Tính điểm cho vùng miền (rule-based) - MẠNH HƠN"""
        query_lower = user_query.lower()
        dish_region = (dish.get('region', '') or '').lower()
        dish_name = (dish.get('name', '') or '').lower()
        dish_desc = (dish.get('description', '') or '').lower()
        
        full_dish_text = f"{dish_name} {dish_desc} {dish_region}"
        
        # Kiểm tra yêu cầu vùng miền cụ thể
        regional_bonus = 0
        regional_penalty = 0
        
        for region, keywords in self.regional_keywords.items():
            # Nếu user yêu cầu vùng này
            if any(keyword in query_lower for keyword in keywords):
                # Kiểm tra món có thuộc vùng này không
                if any(keyword in full_dish_text for keyword in keywords):
                    regional_bonus = 0.5  # Bonus rất mạnh cho đúng vùng
                else:
                    # Penalty nếu món thuộc vùng khác
                    other_regions = [k for k in self.regional_keywords.keys() if k != region]
                    for other_region in other_regions:
                        if any(keyword in full_dish_text for keyword in self.regional_keywords[other_region]):
                            regional_penalty = -0.8  # Penalty rất mạnh cho sai vùng
                            break
        
        return regional_bonus + regional_penalty
    
    def _get_temperature_score(self, dish: Dict, user_query: str) -> float:
        """Tính điểm cho yêu cầu nóng/lạnh"""
        query_lower = user_query.lower()
        dish_name = (dish.get('name', '') or '').lower()
        dish_desc = (dish.get('description', '') or '').lower()
        
        full_dish_text = f"{dish_name} {dish_desc}"
        
        # Từ khóa cho món nóng/ấm
        hot_keywords = ['ấm áp', 'nóng', 'canh', 'súp', 'soup', 'nước dùng', 'lẩu', 'cháo', 'chè']
        cold_keywords = ['mát', 'lạnh', 'kem', 'chè đá', 'nước đá', 'sinh tố']
        
        score = 0
        
        # Nếu user muốn món ấm/nóng
        if any(keyword in query_lower for keyword in hot_keywords):
            if any(keyword in full_dish_text for keyword in hot_keywords):
                score += 0.3  # Tăng bonus
            elif any(keyword in full_dish_text for keyword in cold_keywords):
                score -= 0.2
        
        return score
    
    def _get_ingredient_score(self, dish: Dict, user_query: str) -> float:
        """Tính điểm cho nguyên liệu"""
        query_lower = user_query.lower()
        dish_ingredients = (dish.get('ingredients', '') or '').lower()
        dish_name = (dish.get('name', '') or '').lower()
        dish_desc = (dish.get('description', '') or '').lower()
        
        full_dish_text = f"{dish_name} {dish_desc} {dish_ingredients}"
        
        # Từ khóa rau
        vegetable_keywords = ['rau', 'củ', 'nhiều rau', 'đầy rau', 'toàn rau', 'rau xanh', 'rau củ']
        
        score = 0
        
        # Nếu user muốn nhiều rau
        if any(keyword in query_lower for keyword in vegetable_keywords):
            if any(keyword in full_dish_text for keyword in vegetable_keywords):
                score += 0.2
        
        return score
    
    def get_recommendations(self, user_query: str, top_k: int = 10) -> List[Tuple[Dict, float, str]]:
        """Lấy recommendations kết hợp text similarity và rule-based scoring"""
        if not self.dishes:
            return []
        
        print(f"[INFO] Getting recommendations for: '{user_query}'")
        
        final_scores = []
        
        for dish in self.dishes:
            # 1. Semantic similarity score (0-1)
            semantic_score = self._get_semantic_similarity_score(user_query, dish)
            
            # 2. Rule-based adjustments
            regional_score = self._get_regional_score(dish, user_query)
            temperature_score = self._get_temperature_score(dish, user_query)
            ingredient_score = self._get_ingredient_score(dish, user_query)
            
            # 3. Combine scores
            final_score = (
                semantic_score * 0.6 +    # Text similarity - 60%
                regional_score +          # Regional bonus/penalty (có thể âm)
                temperature_score +       # Temperature bonus/penalty
                ingredient_score          # Ingredient bonus
            )
            
            # 4. Tạo explanation
            explanations = []
            if semantic_score > 0.1:
                explanations.append(f"Khớp từ khóa ({semantic_score:.2f})")
            if regional_score > 0:
                explanations.append(f"Đúng vùng miền (+{regional_score:.2f})")
            elif regional_score < 0:
                explanations.append(f"Sai vùng miền ({regional_score:.2f})")
            if temperature_score > 0:
                explanations.append(f"Đúng nhiệt độ (+{temperature_score:.2f})")
            if ingredient_score > 0:
                explanations.append(f"Đúng nguyên liệu (+{ingredient_score:.2f})")
            
            explanation = "; ".join(explanations) if explanations else "Gợi ý chung"
            
            final_scores.append((dish, final_score, explanation))
        
        # Sắp xếp theo điểm và trả về top_k
        final_scores.sort(key=lambda x: x[1], reverse=True)
        
        print(f"[INFO] Returning top {min(top_k, len(final_scores))} recommendations")
        return final_scores[:top_k]

class EmbeddingRecommendationWrapper(SimpleEmbeddingRecommendationEngine):
    """Wrapper class để tương thích với interface cũ"""
    
    def format_recommendation_response(self, recommendations, user_query):
        """Format response giống như recommendation engine cũ"""
        if not recommendations:
            return "Tôi không tìm thấy món ăn phù hợp với yêu cầu của bạn. Bạn có thể thử mô tả chi tiết hơn không?"
        
        # Tạo response header
        response_parts = [
            f"🍽️ **Dựa trên yêu cầu '{user_query}', tôi gợi ý {len(recommendations)} món ăn sau:**\n"
        ]
        
        # Format từng món
        for i, (dish, score, explanation) in enumerate(recommendations, 1):
            dish_info = [
                f"**{i}. {dish['name']}**",
                f"💰 **Giá:** {dish['price']:,.0f}đ" if dish['price'] else "💰 **Giá:** Liên hệ",
                f"🌍 **Vùng miền:** {dish['region']}" if dish['region'] else "",
                f" **Điểm phù hợp:** {score:.2f}/1.0",
                f"✨ **Lý do gợi ý:** {explanation}",
            ]
            
            # Lọc bỏ những dòng trống
            dish_info = [info for info in dish_info if info and not info.endswith(": ")]
            response_parts.append("\n".join(dish_info))
        
        response = "\n\n".join(response_parts)
        response += "\n\n💡 **Gợi ý:** Bạn có thể hỏi thêm về cách làm, nguyên liệu, hoặc thông tin dinh dưỡng của món nào đó!"
        
        return response

# Tạo global instance để thay thế recommendation_engine cũ
recommendation_engine = EmbeddingRecommendationWrapper()

