"""
Hệ thống recommendation cải tiến sử dụng vector embeddings
Kết hợp semantic similarity với rule-based scoring để có kết quả tối ưu
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import sqlite3
import pickle
import os
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import re

class EmbeddingRecommendationEngine:
    def __init__(self, db_path='restaurant.db', cache_dir='cache'):
        self.db_path = db_path
        self.cache_dir = cache_dir
        self.model = None
        self.dishes = []
        self.dish_embeddings = None
        
        # Tạo cache directory nếu chưa có
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load model và data
        self._load_model()
        self._load_dishes()
        self._load_or_create_embeddings()
        
        # Rule-based weights (giữ lại một số rules quan trọng)
        self.regional_keywords = {
            'north': ['bắc', 'hà nội', 'phở', 'bún chả', 'chả cá', 'nem rán', 'bánh cuốn', 'bún đậu', 'miến gà'],
            'central': ['trung', 'huế', 'bún bò huế', 'bánh khoái', 'bánh bèo', 'mì quảng', 'cao lầu', 'bánh căn'],
            'south': ['nam', 'sài gòn', 'cơm tấm', 'bánh xèo', 'hủ tiếu', 'bánh khọt', 'bún thịt nướng', 'gỏi cuốn']
        }
        
    def _load_model(self):
        """Load sentence transformer model"""
        try:
            # Sử dụng multilingual model cho tiếng Việt
            print("[INFO] Loading sentence transformer model...")
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("[INFO] Model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            print("[INFO] Fallback to simple text matching")
            self.model = None
    
    def _load_dishes(self):
        """Load dishes from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, description, price, region, ingredients, 
                       main_or_side, dry_or_soup, vegetarian_or_meat, mood,
                       calories, fat, fiber, sugar, protein
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
                    'mood': row[9] or '',
                    'calories': row[10] or 0,
                    'fat': row[11] or 0,
                    'fiber': row[12] or 0,
                    'sugar': row[13] or 0,
                    'protein': row[14] or 0
                }
                self.dishes.append(dish)
            
            print(f"[INFO] Loaded {len(self.dishes)} dishes")
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Failed to load dishes: {e}")
            self.dishes = []
    
    def _create_dish_text(self, dish: Dict) -> str:
        """Tạo text representation của món ăn để embedding"""
        # Kết hợp tên, mô tả, vùng miền, nguyên liệu
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
            text_parts.append(f"nguyên liệu {dish['ingredients']}")
        
        # Thêm thông tin dinh dưỡng vào text representation
        nutrition_parts = []
        if dish.get('calories', 0) > 0:
            nutrition_parts.append(f"{dish['calories']} calories")
        if dish.get('protein', 0) > 0:
            nutrition_parts.append(f"{dish['protein']}g protein")
        if dish.get('fat', 0) > 0:
            nutrition_parts.append(f"{dish['fat']}g fat")
        if dish.get('fiber', 0) > 0:
            nutrition_parts.append(f"{dish['fiber']}g fiber")
        if dish.get('sugar', 0) > 0:
            nutrition_parts.append(f"{dish['sugar']}g sugar")
        
        if nutrition_parts:
            text_parts.append(f"dinh dưỡng {' '.join(nutrition_parts)}")
        
        return ' '.join(text_parts)
    
    def _load_or_create_embeddings(self):
        """Load embeddings từ cache hoặc tạo mới"""
        embeddings_path = os.path.join(self.cache_dir, 'dish_embeddings.pkl')
        
        if os.path.exists(embeddings_path) and self.model:
            try:
                print("[INFO] Loading cached embeddings...")
                with open(embeddings_path, 'rb') as f:
                    self.dish_embeddings = pickle.load(f)
                
                # Kiểm tra xem số lượng embeddings có khớp với số món ăn không
                if len(self.dish_embeddings) == len(self.dishes):
                    print(f"[INFO] Loaded {len(self.dish_embeddings)} cached embeddings")
                    return
                else:
                    print("[INFO] Cache size mismatch, recreating embeddings...")
            except Exception as e:
                print(f"[WARNING] Failed to load cached embeddings: {e}")
        
        # Tạo embeddings mới
        self._create_embeddings()
    
    def _create_embeddings(self):
        """Tạo embeddings cho tất cả món ăn"""
        if not self.model:
            print("[WARNING] No model available for embeddings")
            return
            
        print("[INFO] Creating embeddings for all dishes...")
        
        # Tạo text representation cho tất cả món ăn
        dish_texts = [self._create_dish_text(dish) for dish in self.dishes]
        
        # Tạo embeddings
        self.dish_embeddings = self.model.encode(dish_texts, show_progress_bar=True)
        
        # Cache embeddings
        embeddings_path = os.path.join(self.cache_dir, 'dish_embeddings.pkl')
        try:
            with open(embeddings_path, 'wb') as f:
                pickle.dump(self.dish_embeddings, f)
            print(f"[INFO] Cached embeddings to {embeddings_path}")
        except Exception as e:
            print(f"[WARNING] Failed to cache embeddings: {e}")
    
    def _get_semantic_similarity_scores(self, user_query: str) -> np.ndarray:
        """Tính semantic similarity giữa user query và tất cả món ăn"""
        if not self.model or self.dish_embeddings is None:
            return np.zeros(len(self.dishes))
        
        # Encode user query
        query_embedding = self.model.encode([user_query])
        
        # Tính cosine similarity
        similarities = cosine_similarity(query_embedding, self.dish_embeddings)[0]
        
        return similarities
    
    def _get_regional_score(self, dish: Dict, user_query: str) -> float:
        """Tính điểm cho vùng miền (rule-based)"""
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
                    regional_bonus = 0.3  # Bonus mạnh cho đúng vùng
                else:
                    # Penalty nếu món thuộc vùng khác
                    other_regions = [k for k in self.regional_keywords.keys() if k != region]
                    for other_region in other_regions:
                        if any(keyword in full_dish_text for keyword in self.regional_keywords[other_region]):
                            regional_penalty = -0.5  # Penalty mạnh cho sai vùng
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
                score += 0.2
            elif any(keyword in full_dish_text for keyword in cold_keywords):
                score -= 0.1
        
        return score
    
    def _get_vegetarian_score(self, dish: Dict, user_query: str) -> float:
        """Tính điểm cho yêu cầu chay/mặn"""
        query_lower = user_query.lower()
        dish_vegetarian_or_meat = (dish.get('vegetarian_or_meat', '') or '').lower()
        dish_name = (dish.get('name', '') or '').lower()
        dish_desc = (dish.get('description', '') or '').lower()
        
        # Từ khóa chay
        vegetarian_keywords = [
            'chay', 'vegetarian', 'vegan', 'không thịt', 'rau củ', 'plant based',
            'xuất gia', 'ăn chay', 'đậu phụ', 'đậu hũ', 'tàu hũ', 'chả chay', 'thịt chay'
        ]
        
        # Từ khóa mặn
        meat_keywords = [
            'mặn', 'thịt', 'cá', 'tôm', 'cua', 'gà', 'bò', 'heo', 'lợn', 'hải sản',
            'meat', 'chicken', 'beef', 'pork', 'fish', 'seafood'
        ]
        
        score = 0
        
        # Nếu user yêu cầu món chay
        if any(keyword in query_lower for keyword in vegetarian_keywords):
            if dish_vegetarian_or_meat == 'chay':
                score += 0.5  # Bonus mạnh cho món chay đúng
            elif dish_vegetarian_or_meat == 'mặn':
                score -= 1.0  # Penalty rất mạnh cho món mặn khi yêu cầu chay
            elif any(keyword in dish_name + ' ' + dish_desc for keyword in vegetarian_keywords):
                score += 0.3  # Bonus cho món có từ khóa chay trong tên/mô tả
            elif any(keyword in dish_name + ' ' + dish_desc for keyword in meat_keywords):
                score -= 0.8  # Penalty cho món có từ khóa thịt khi yêu cầu chay
        
        # Nếu user yêu cầu món mặn
        elif any(keyword in query_lower for keyword in meat_keywords):
            if dish_vegetarian_or_meat == 'mặn':
                score += 0.3  # Bonus cho món mặn
            elif dish_vegetarian_or_meat == 'chay':
                score -= 0.2  # Penalty nhẹ cho món chay khi yêu cầu mặn
        
        return score
    
    def _get_nutrition_score(self, dish: Dict, user_query: str) -> float:
        """Tính điểm cho yêu cầu về dinh dưỡng"""
        query_lower = user_query.lower()
        score = 0
        
        # Từ khóa cho các yêu cầu dinh dưỡng
        nutrition_keywords = {
            'ít calo': {'keywords': ['ít calo', 'low calorie', 'giảm cân', 'diet'], 'type': 'low_calorie'},
            'nhiều protein': {'keywords': ['nhiều protein', 'high protein', 'đạm', 'tăng cơ'], 'type': 'high_protein'},
            'ít đường': {'keywords': ['ít đường', 'low sugar', 'không đường', 'sugar free'], 'type': 'low_sugar'},
            'ít béo': {'keywords': ['ít béo', 'low fat', 'không dầu mỡ', 'fat free'], 'type': 'low_fat'},
            'nhiều chất xơ': {'keywords': ['nhiều chất xơ', 'high fiber', 'chất xơ', 'tiêu hóa'], 'type': 'high_fiber'}
        }
        
        calories = dish.get('calories', 0)
        protein = dish.get('protein', 0)
        fat = dish.get('fat', 0)
        fiber = dish.get('fiber', 0)
        sugar = dish.get('sugar', 0)
        
        for category, info in nutrition_keywords.items():
            if any(keyword in query_lower for keyword in info['keywords']):
                if info['type'] == 'low_calorie' and calories > 0:
                    # Điểm cao cho món ít calo (dưới 300 calo)
                    if calories < 200:
                        score += 0.3
                    elif calories < 300:
                        score += 0.2
                    elif calories > 500:
                        score -= 0.2
                
                elif info['type'] == 'high_protein' and protein > 0:
                    # Điểm cao cho món nhiều protein (trên 15g)
                    if protein > 20:
                        score += 0.3
                    elif protein > 15:
                        score += 0.2
                    elif protein < 5:
                        score -= 0.1
                
                elif info['type'] == 'low_sugar' and sugar >= 0:
                    # Điểm cao cho món ít đường (dưới 5g)
                    if sugar < 2:
                        score += 0.3
                    elif sugar < 5:
                        score += 0.2
                    elif sugar > 15:
                        score -= 0.2
                
                elif info['type'] == 'low_fat' and fat >= 0:
                    # Điểm cao cho món ít béo (dưới 10g)
                    if fat < 5:
                        score += 0.3
                    elif fat < 10:
                        score += 0.2
                    elif fat > 20:
                        score -= 0.2
                
                elif info['type'] == 'high_fiber' and fiber > 0:
                    # Điểm cao cho món nhiều chất xơ (trên 5g)
                    if fiber > 8:
                        score += 0.3
                    elif fiber > 5:
                        score += 0.2
                    elif fiber < 2:
                        score -= 0.1
        
        return score
    
    def get_recommendations(self, user_query: str, top_k: int = 10) -> List[Tuple[Dict, float, str]]:
        """
        Lấy recommendations kết hợp semantic similarity và rule-based scoring
        
        Returns:
            List of tuples: (dish, final_score, explanation)
        """
        if not self.dishes:
            return []
        
        print(f"[INFO] Getting recommendations for: {user_query}")
        
        # 1. Tính semantic similarity scores
        semantic_scores = self._get_semantic_similarity_scores(user_query)
        print(f"[INFO] Computed semantic similarities (max: {semantic_scores.max():.3f})")
        
        # 2. Tính rule-based scores
        final_scores = []
        
        for i, dish in enumerate(self.dishes):
            # Base score từ semantic similarity (0-1)
            semantic_score = float(semantic_scores[i])
            
            # Rule-based adjustments
            regional_score = self._get_regional_score(dish, user_query)
            temperature_score = self._get_temperature_score(dish, user_query)
            vegetarian_score = self._get_vegetarian_score(dish, user_query)
            nutrition_score = self._get_nutrition_score(dish, user_query)
            
            # Combine scores (semantic có trọng số cao nhất)
            final_score = (
                semantic_score * 0.7 +  # Semantic similarity - 70%
                regional_score +        # Regional bonus/penalty
                temperature_score +     # Temperature bonus/penalty
                vegetarian_score +      # Vegetarian/meat bonus/penalty
                nutrition_score         # Nutrition bonus/penalty
            )
            
            # Tạo explanation
            explanations = []
            if semantic_score > 0.3:
                explanations.append(f"Phù hợp ngữ nghĩa ({semantic_score:.2f})")
            if regional_score > 0:
                explanations.append(f"Đúng vùng miền (+{regional_score:.2f})")
            elif regional_score < 0:
                explanations.append(f"Sai vùng miền ({regional_score:.2f})")
            if temperature_score > 0:
                explanations.append(f"Đúng nhiệt độ (+{temperature_score:.2f})")
            if vegetarian_score > 0:
                explanations.append(f"Món chay phù hợp (+{vegetarian_score:.2f})")
            elif vegetarian_score < -0.5:
                explanations.append(f"Món mặn không phù hợp ({vegetarian_score:.2f})")
            if nutrition_score > 0:
                explanations.append(f"Phù hợp dinh dưỡng (+{nutrition_score:.2f})")
            elif nutrition_score < -0.1:
                explanations.append(f"Không phù hợp dinh dưỡng ({nutrition_score:.2f})")
            
            explanation = "; ".join(explanations) if explanations else "Gợi ý chung"
            
            final_scores.append((dish, final_score, explanation))
        
        # Sắp xếp theo điểm và trả về top_k
        final_scores.sort(key=lambda x: x[1], reverse=True)
        
        print(f"[INFO] Returning top {min(top_k, len(final_scores))} recommendations")
        return final_scores[:top_k]
    
    def refresh_embeddings(self):
        """Refresh embeddings khi có dữ liệu mới"""
        print("[INFO] Refreshing embeddings...")
        self._load_dishes()
        self._create_embeddings()

# Global instance cho backward compatibility
embedding_recommendation_engine = EmbeddingRecommendationEngine()
