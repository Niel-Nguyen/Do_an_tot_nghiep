"""
Hệ thống đề xuất món ăn thông minh dựa trên sở thích người dùng
"""
import re
import json
from typing import List, Dict, Any
from utils.database_loader import load_dishes_from_database

class SmartRecommendationEngine:
    def __init__(self):
        self.dishes = []
        self.load_menu()
        
        # Từ điển mapping sở thích
        self.diet_keywords = {
            'low-carb': ['low carb', 'ít tinh bột', 'không tinh bột', 'giảm cân'],
            'keto': ['keto', 'ketogenic', 'nhiều chất béo', 'ít carb'],
            'chay': ['chay', 'vegetarian', 'vegan', 'không thịt', 'rau củ'],
            'high-protein': ['protein', 'nhiều đạm', 'thịt', 'cá', 'tôm', 'trứng', 'giàu protein', 'tập gym', 'gym', 'thể hình'],
            'low-fat': ['ít béo', 'ít chất béo', 'low fat', 'không dầu mỡ', 'ít dầu'],
            'healthy': ['healthy', 'lành mạnh', 'sạch', 'eat clean', 'thanh đạm']
        }
        
        self.spicy_keywords = {
            'no-spicy': ['không cay', 'nhạt', 'không ớt'],
            'mild': ['ít cay', 'vừa cay', 'nhẹ'],
            'hot': ['cay', 'rất cay', 'ớt', 'nhiều ớt']
        }
        
        self.ingredient_keywords = {
            'seafood': ['hải sản', 'tôm', 'cua', 'ốc', 'sò', 'mực', 'cá'],
            'beef': ['bò', 'thịt bò'],
            'pork': ['heo', 'thịt heo', 'thịt lợn'],
            'chicken': ['gà', 'thịt gà'],
            'vegetables': ['rau', 'củ', 'cải', 'rau xanh', 'rau củ'],
            'noodles': ['bún', 'phở', 'mì', 'bánh canh'],
            'rice': ['cơm', 'gạo']
        }
        
        self.dislike_keywords = [
            'không thích', 'không ăn', 'dị ứng', 'không được', 'tránh'
        ]
    
    def load_menu(self):
        """Load menu từ database"""
        try:
            self.dishes = load_dishes_from_database()
            print(f"[INFO] Loaded {len(self.dishes)} dishes for recommendation")
        except Exception as e:
            print(f"[ERROR] Failed to load dishes: {e}")
            self.dishes = []
    
    def analyze_preferences(self, preference_text: str) -> Dict[str, Any]:
        """Phân tích sở thích người dùng từ text"""
        preference_text = preference_text.lower()
        
        analysis = {
            'diet_type': [],
            'spicy_level': None,
            'liked_ingredients': [],
            'disliked_ingredients': [],
            'special_requests': [],
            'health_conscious': False
        }
        
        # Phân tích chế độ ăn
        for diet, keywords in self.diet_keywords.items():
            if any(keyword in preference_text for keyword in keywords):
                analysis['diet_type'].append(diet)
        
        # Phân tích độ cay
        for spicy_level, keywords in self.spicy_keywords.items():
            if any(keyword in preference_text for keyword in keywords):
                analysis['spicy_level'] = spicy_level
                break
        
        # Phân tích nguyên liệu yêu thích
        for ingredient_type, keywords in self.ingredient_keywords.items():
            if any(keyword in preference_text for keyword in keywords):
                # Kiểm tra xem có phải là không thích không
                context = self._get_keyword_context(preference_text, keywords[0])
                if not any(dislike in context for dislike in self.dislike_keywords):
                    analysis['liked_ingredients'].append(ingredient_type)
                else:
                    analysis['disliked_ingredients'].append(ingredient_type)
        
        # Phân tích yêu cầu đặc biệt
        health_keywords = ['thanh đạm', 'ít dầu', 'lành mạnh', 'sạch', 'tươi']
        if any(keyword in preference_text for keyword in health_keywords):
            analysis['health_conscious'] = True
            analysis['special_requests'].extend([kw for kw in health_keywords if kw in preference_text])
        
        return analysis
    
    def _get_keyword_context(self, text: str, keyword: str, context_length: int = 10) -> str:
        """Lấy context xung quanh keyword để phân tích"""
        words = text.split()
        for i, word in enumerate(words):
            if keyword in word:
                start = max(0, i - context_length)
                end = min(len(words), i + context_length + 1)
                return ' '.join(words[start:end])
        return ''
    
    def _get_dish_attr(self, dish, attr_name: str, default=''):
        """Safely get dish attribute whether it's an object or dictionary"""
        if hasattr(dish, attr_name):
            return getattr(dish, attr_name, default)
        elif isinstance(dish, dict):
            return dish.get(attr_name, default)
        else:
            return default
    
    def score_dish(self, dish, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Tính điểm cho món ăn dựa trên phân tích sở thích"""
        score = 0
        reasons = []
        
        dish_name = (self._get_dish_attr(dish, 'name') or '').lower()
        dish_desc = (self._get_dish_attr(dish, 'description') or '').lower()
        dish_ingredients = (self._get_dish_attr(dish, 'ingredients') or '').lower()
        
        # Điểm cho chế độ ăn
        for diet in analysis['diet_type']:
            diet_score, diet_reason = self._score_diet_compatibility(dish, diet)
            score += diet_score
            if diet_reason:
                reasons.append(diet_reason)
        
        # Điểm penalty cho giá quá cao/thấp để tạo sự đa dạng
        dish_price = self._get_dish_attr(dish, 'price', 0)
        if dish_price:
            if dish_price > 80000:
                score -= 3  # Món đắt bị trừ điểm nhẹ
            elif dish_price < 20000:
                score += 2  # Món rẻ được cộng điểm nhẹ
        
        # Random factor nhỏ để tránh nhiều món có điểm giống nhau
        import random
        random_factor = random.randint(-2, 2)
        score += random_factor
        
        # Điểm cho độ cay
        if analysis['spicy_level']:
            spicy_score, spicy_reason = self._score_spicy_level(dish, analysis['spicy_level'])
            score += spicy_score
            if spicy_reason:
                reasons.append(spicy_reason)
        
        # Điểm cho nguyên liệu yêu thích với lý do chi tiết
        for ingredient in analysis['liked_ingredients']:
            if self._dish_contains_ingredient(dish, ingredient):
                score += 15
                detailed_reason = self._get_detailed_ingredient_reason(dish, ingredient)
                reasons.append(detailed_reason)
        
        # Trừ điểm cho nguyên liệu không thích
        for ingredient in analysis['disliked_ingredients']:
            if self._dish_contains_ingredient(dish, ingredient):
                score -= 20
                reasons.append(f"Có {self._get_ingredient_name(ingredient)} mà bạn không thích")
        
        # Điểm cho yêu cầu sức khỏe với lý do cụ thể
        if analysis['health_conscious']:
            health_reason = self._get_health_reason(dish)
            if health_reason:
                if health_reason.startswith("Tốt:"):
                    score += 10
                    reasons.append(health_reason.replace("Tốt:", ""))
                elif health_reason.startswith("Xấu:"):
                    score -= 5
                    reasons.append(health_reason.replace("Xấu:", ""))
        
        # Bonus đặc biệt cho diet kết hợp (gym diet) với lý do chi tiết
        if 'high-protein' in analysis['diet_type'] and 'low-fat' in analysis['diet_type']:
            gym_reason = self._get_gym_diet_reason(dish)
            if gym_reason:
                if "Xuất sắc" in gym_reason:
                    score += 20
                elif "Tốt" in gym_reason:
                    score += 15
                elif "Phù hợp" in gym_reason:
                    score += 10
                reasons.append(gym_reason)
        
        # Điểm thưởng cho món phổ biến
        if dish_price and dish_price < 100000:
            score += 2  # Món bình dân
        
        # Thêm yếu tố ngẫu nhiên để tạo sự đa dạng
        import random
        random.seed(hash(dish_name) % 1000)  # Seed dựa trên tên món để consistent
        random_factor = random.randint(-3, 5)
        score += random_factor
        
        # Cải thiện confidence calculation để có sự đa dạng hơn
        if score < 0:
            confidence = random.randint(20, 35)  # Món không phù hợp
        elif score < 10:
            confidence = random.randint(40, 60)  # Món phù hợp vừa
        elif score < 20:
            confidence = random.randint(65, 80)  # Món khá phù hợp
        else:
            confidence = random.randint(85, 98)  # Món rất phù hợp
        
        return {
            'dish': dish,
            'score': score,
            'reasons': reasons,
            'confidence': confidence
        }
    
    def _score_diet_compatibility(self, dish, diet_type: str) -> tuple:
        """Tính điểm tương thích chế độ ăn với lý do chi tiết"""
        dish_name = (self._get_dish_attr(dish, 'name') or '').lower()
        dish_desc = (self._get_dish_attr(dish, 'description') or '').lower()
        
        if diet_type == 'low-carb':
            # Tránh tinh bột
            if any(word in dish_name for word in ['cơm', 'bún', 'phở', 'bánh', 'chè']):
                return -10, "Có tinh bột cao (không phù hợp low-carb)"
            if 'cá' in dish_name:
                return 12, "Cá giàu protein, không tinh bột"
            elif 'tôm' in dish_name:
                return 12, "Tôm ít carb, nhiều protein"
            elif 'thịt' in dish_name:
                return 10, "Thịt phù hợp chế độ low-carb"
            elif 'rau' in dish_name:
                return 8, "Rau củ ít carb"
                
        elif diet_type == 'chay':
            if any(word in dish_name for word in ['thịt', 'cá', 'tôm', 'gà', 'heo', 'bò']):
                return -15, "Có thịt/cá (không phù hợp chay)"
            if 'chay' in dish_name:
                return 15, "Món chay thuần túy"
            elif any(word in dish_name for word in ['rau', 'đậu']):
                return 12, "Từ thực vật tự nhiên"
                
        elif diet_type == 'high-protein':
            # Protein cao từ thịt, cá, tôm với lý do cụ thể
            if 'cá' in dish_name and any(method in dish_name + ' ' + dish_desc for method in ['nướng', 'hấp']):
                return 18, "Cá nướng/hấp - protein cao, ít béo"
            elif 'tôm' in dish_name:
                return 16, "Tôm giàu protein, ít calo"
            elif 'gà' in dish_name and 'chiên' not in dish_name:
                return 15, "Thịt gà nạc, protein chất lượng"
            elif 'bò' in dish_name:
                return 14, "Thịt bò giàu protein và sắt"
            elif any(word in dish_name for word in ['thịt', 'cá', 'trứng']):
                return 12, "Nguồn protein động vật"
            elif any(word in dish_name for word in ['đậu', 'chả']):
                return 8, "Protein thực vật"
                
        elif diet_type == 'low-fat':
            # Ưu tiên món hấp, luộc, nướng với lý do cụ thể
            if 'hấp' in dish_name or 'hấp' in dish_desc:
                return 15, "Món hấp không dầu mỡ"
            elif 'luộc' in dish_name or 'luộc' in dish_desc:
                return 14, "Luộc giữ nguyên dinh dưỡng"
            elif 'gỏi' in dish_name:
                return 13, "Gỏi tươi, ít chất béo"
            elif 'nướng' in dish_name and 'dầu' not in dish_desc:
                return 11, "Nướng không dầu"
            elif 'canh' in dish_name:
                return 10, "Canh thanh đạm"
            # Tránh món chiên, rang
            elif any(word in dish_name + ' ' + dish_desc for word in ['chiên', 'rang', 'xào dầu']):
                return -8, "Nhiều dầu mỡ khi chế biến"
                
        elif diet_type == 'healthy':
            if 'gỏi' in dish_name:
                return 12, "Gỏi tươi, giàu vitamin"
            elif 'salad' in dish_name:
                return 11, "Salad bổ dưỡng"
            elif 'luộc' in dish_name:
                return 10, "Chế biến lành mạnh"
            elif 'hấp' in dish_name:
                return 10, "Hấp giữ dinh dưỡng"
        
        return 0, None
    
    def _score_spicy_level(self, dish, preferred_level: str) -> tuple:
        """Tính điểm độ cay"""
        dish_name = dish.name.lower()
        dish_desc = (dish.description or '').lower()
        
        is_spicy = any(word in dish_name + ' ' + dish_desc for word in ['cay', 'ớt', 'tiêu'])
        
        if preferred_level == 'no-spicy' and not is_spicy:
            return 8, "Không cay như bạn yêu cầu"
        elif preferred_level == 'no-spicy' and is_spicy:
            return -8, "Món cay (không phù hợp)"
        elif preferred_level in ['mild', 'hot'] and is_spicy:
            return 8, "Độ cay phù hợp"
        
        return 0, None
    
    def _dish_contains_ingredient(self, dish, ingredient_type: str) -> bool:
        """Kiểm tra món ăn có chứa nguyên liệu không"""
        dish_name = self._get_dish_attr(dish, 'name') or ''
        dish_desc = self._get_dish_attr(dish, 'description') or ''
        dish_ingredients = self._get_dish_attr(dish, 'ingredients') or ''
        dish_text = f"{dish_name} {dish_desc} {dish_ingredients}".lower()
        
        keywords = self.ingredient_keywords.get(ingredient_type, [])
        return any(keyword in dish_text for keyword in keywords)
    
    def _get_ingredient_name(self, ingredient_type: str) -> str:
        """Lấy tên tiếng Việt của loại nguyên liệu"""
        name_map = {
            'seafood': 'hải sản',
            'beef': 'thịt bò',
            'pork': 'thịt heo',
            'chicken': 'thịt gà',
            'vegetables': 'rau củ',
            'noodles': 'bún/phở',
            'rice': 'cơm'
        }
        return name_map.get(ingredient_type, ingredient_type)
    
    def _get_detailed_ingredient_reason(self, dish, ingredient_type: str) -> str:
        """Tạo lý do chi tiết cho nguyên liệu yêu thích"""
        dish_name = (self._get_dish_attr(dish, 'name') or '').lower()
        
        if ingredient_type == 'seafood':
            if 'tôm' in dish_name:
                return "Tôm tươi ngon, giàu protein"
            elif 'cá' in dish_name:
                if 'nướng' in dish_name:
                    return "Cá nướng thơm, ít béo"
                elif 'hấp' in dish_name:
                    return "Cá hấp giữ nguyên dinh dưỡng"
                else:
                    return "Cá tươi, omega-3 cao"
            elif 'cua' in dish_name:
                return "Cua biển ngọt thịt"
            elif 'ốc' in dish_name:
                return "Ốc giàu khoáng chất"
            else:
                return "Hải sản tươi ngon"
                
        elif ingredient_type == 'chicken':
            if 'nướng' in dish_name:
                return "Gà nướng thơm lừng"
            elif 'luộc' in dish_name:
                return "Gà luộc thanh đạm"
            else:
                return "Thịt gà mềm ngon"
                
        elif ingredient_type == 'beef':
            if 'nướng' in dish_name:
                return "Thịt bò nướng đậm đà"
            elif 'phở' in dish_name:
                return "Thịt bò phở thơm ngon"
            else:
                return "Thịt bò chất lượng"
                
        elif ingredient_type == 'vegetables':
            if 'gỏi' in dish_name:
                return "Rau củ tươi mát"
            elif 'luộc' in dish_name:
                return "Rau luộc giữ vitamin"
            else:
                return "Rau xanh bổ dưỡng"
                
        return f"Có {self._get_ingredient_name(ingredient_type)} yêu thích"
    
    def _get_health_reason(self, dish) -> str:
        """Tạo lý do sức khỏe chi tiết"""
        dish_name = (self._get_dish_attr(dish, 'name') or '').lower()
        dish_desc = (self._get_dish_attr(dish, 'description') or '').lower()
        
        # Các món tốt cho sức khỏe
        if 'gỏi' in dish_name:
            return "Tốt:Gỏi tươi, nhiều chất xơ"
        elif 'salad' in dish_name:
            return "Tốt:Salad bổ sung vitamin"
        elif 'luộc' in dish_name:
            return "Tốt:Luộc không mất chất dinh dưỡng"
        elif 'hấp' in dish_name:
            return "Tốt:Hấp giữ nguyên giá trị dinh dưỡng"
        elif 'canh' in dish_name:
            if 'rau' in dish_name:
                return "Tốt:Canh rau thanh mát"
            else:
                return "Tốt:Canh nước trong, ít calo"
        elif any(word in dish_name for word in ['chiên', 'rang']):
            return "Xấu:Chiên/rang nhiều dầu mỡ"
        elif 'nướng' in dish_name and 'dầu' not in dish_desc:
            return "Tốt:Nướng không dầu, thơm ngon"
        
        return None
    
    def _get_gym_diet_reason(self, dish) -> str:
        """Tạo lý do cho chế độ ăn gym"""
        dish_name = (self._get_dish_attr(dish, 'name') or '').lower()
        dish_desc = (self._get_dish_attr(dish, 'description') or '').lower()
        
        # Kiểm tra protein + low fat
        if 'tôm' in dish_name:
            if 'hấp' in dish_name or 'luộc' in dish_name:
                return "Xuất sắc cho gym: Tôm protein cao, hấp/luộc không béo"
            elif 'nướng' in dish_name:
                return "Tốt cho gym: Tôm nướng protein cao"
            else:
                return "Phù hợp gym: Tôm giàu protein"
                
        elif 'cá' in dish_name:
            if any(method in dish_name + ' ' + dish_desc for method in ['hấp', 'luộc', 'nướng']):
                return "Xuất sắc cho gym: Cá omega-3, chế biến lành mạnh"
            else:
                return "Tốt cho gym: Cá giàu protein và omega-3"
                
        elif 'gà' in dish_name and 'chiên' not in dish_name:
            return "Tốt cho gym: Gà protein cao, ít béo"
            
        elif 'bò' in dish_name and not any(fatty in dish_name for fatty in ['chiên', 'rang']):
            return "Phù hợp gym: Thịt bò protein + sắt"
            
        return None
    
    def get_recommendations(self, preference_text: str, top_k: int = 7) -> List[Dict[str, Any]]:
        """Lấy danh sách đề xuất món ăn"""
        if not self.dishes:
            return []
        
        # Phân tích sở thích
        analysis = self.analyze_preferences(preference_text)
        print(f"[DEBUG] Preference analysis: {analysis}")
        
        # Tính điểm cho từng món
        scored_dishes = []
        for dish in self.dishes:
            result = self.score_dish(dish, analysis)
            if result['score'] > 0:  # Chỉ lấy món có điểm dương
                scored_dishes.append(result)
        
        # Sắp xếp theo điểm (cao nhất trước), nếu điểm bằng nhau thì ưu tiên giá thấp
        scored_dishes.sort(key=lambda x: (-x['score'], self._get_dish_attr(x['dish'], 'price', 0)))
        
        # Lấy top k
        recommendations = scored_dishes[:top_k]
        
        print(f"[DEBUG] Generated {len(recommendations)} recommendations")
        
        return recommendations
    
    def format_recommendation_response(self, recommendations: List[Dict[str, Any]], preference_text: str) -> str:
        """Format kết quả đề xuất thành HTML compact cho chatbot"""
        if not recommendations:
            return """
            <div style="text-align: center; padding: 15px; color: #666;">
                <i class="fas fa-search" style="font-size: 24px; margin-bottom: 8px;"></i>
                <p>Xin lỗi, tôi không tìm thấy món nào phù hợp với sở thích của bạn.</p>
                <p style="font-size: 0.9em;">Bạn có thể thử mô tả chi tiết hơn không?</p>
            </div>
            """
        
        # Build compact HTML response
        html = f"""
        <div style="max-width: 100%; font-family: 'Segoe UI', sans-serif;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                <div style="font-size: 16px; font-weight: 600; margin-bottom: 6px;">
                    🎯 ĐỀ XUẤT MÓN ĂN THEO SỞ THÍCH
                </div>
                <div style="font-size: 13px; opacity: 0.9; margin-bottom: 6px;">
                    <strong>Sở thích:</strong> "{preference_text[:100]}{'...' if len(preference_text) > 100 else ''}"
                </div>
                <div style="font-size: 12px; opacity: 0.8;">
                    ✨ {len(recommendations)} món được đề xuất
                </div>
            </div>
        """
        
        for i, rec in enumerate(recommendations, 1):
            dish = rec['dish']
            reasons = rec['reasons']
            confidence = rec['confidence']
            
            # Tạo màu sắc dựa trên confidence
            if confidence >= 85:
                confidence_color = "#28a745"
                stars = "⭐⭐⭐⭐⭐"
            elif confidence >= 70:
                confidence_color = "#ffc107"
                stars = "⭐⭐⭐⭐"
            else:
                confidence_color = "#6c757d"
                stars = "⭐⭐⭐"
            
            reasons_text = ", ".join(reasons[:2]) if reasons else "Phù hợp với sở thích"
            
            html += f"""
            <div style="border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 8px; background: white; overflow: hidden;">
                <div style="padding: 8px 12px; border-bottom: 1px solid #f0f0f0;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                        <div style="font-weight: 600; color: #333; font-size: 14px;">{i}. {self._get_dish_attr(dish, 'name', 'Món ăn')}</div>
                        <div style="color: {confidence_color}; font-size: 12px; font-weight: 600;">
                            {stars} {confidence}%
                        </div>
                    </div>
                    <div style="color: #28a745; font-weight: 600; font-size: 13px; margin-bottom: 6px;">
                        💰 {self._get_dish_attr(dish, 'price', 0):,.0f} đ/{self._get_dish_attr(dish, 'unit', 'Suất')}
                    </div>
                </div>
                
                <div style="padding: 8px 12px; font-size: 12px; line-height: 1.4;">
                    <div style="color: #666; margin-bottom: 6px;">
                        {(self._get_dish_attr(dish, 'description', '') or '')[:80]}{'...' if len(self._get_dish_attr(dish, 'description', '') or '') > 80 else ''}
                    </div>
                    
                    <div style="display: flex; align-items: center; margin-bottom: 4px; color: #28a745;">
                        <span style="margin-right: 4px;">✅</span>
                        <strong style="margin-right: 4px;">Phù hợp:</strong> {reasons_text}
                    </div>
                    
                    <div style="display: flex; align-items: center; color: #007bff;">
                        <span style="margin-right: 4px;">🌍</span>
                        <strong style="margin-right: 4px;">Vùng:</strong> {self._get_dish_attr(dish, 'region', 'Không xác định')}
                    </div>
                </div>
            </div>
            """
        
        html += """
            <div style="text-align: center; padding: 12px; background: #f8f9fa; border-radius: 8px; margin-top: 8px;">
                <div style="color: #666; font-size: 13px;">
                    💡 <strong>Bạn có muốn biết thêm chi tiết về món nào không?</strong> 😊
                </div>
            </div>
        </div>
        """
        
        return html

# Instance global để sử dụng
recommendation_engine = SmartRecommendationEngine()