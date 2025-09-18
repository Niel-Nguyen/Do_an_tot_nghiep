"""
Hệ thống đề xuất món ăn thông minh dựa trên sở thích người dùng
"""
import re
import json
import os
from typing import List, Dict, Any
from utils.database_loader import load_dishes_from_database

class SmartRecommendationEngine:
    def __init__(self):
        self.dishes = []
        self.load_menu()
        
        # Từ điển mapping sở thích mở rộng
        self.diet_keywords = {
            'low-carb': ['low carb', 'ít tinh bột', 'không tinh bột', 'giảm cân', 'atkins'],
            'keto': ['keto', 'ketogenic', 'nhiều chất béo', 'ít carb', 'lchf'],
            'chay': ['chay', 'vegetarian', 'vegan', 'không thịt', 'rau củ', 'plant based'],
            'high-protein': ['protein', 'nhiều đạm', 'thịt', 'cá', 'tôm', 'trứng', 'giàu protein', 'tập gym', 'gym', 'thể hình', 'bodybuilding'],
            'low-fat': ['ít béo', 'ít chất béo', 'low fat', 'không dầu mỡ', 'ít dầu', 'giảm béo'],
            'healthy': ['healthy', 'lành mạnh', 'sạch', 'eat clean', 'thanh đạm', 'organic'],
            'paleo': ['paleo', 'paleolithic', 'nguyên thủy', 'tự nhiên', 'không chế biến'],
            'dash': ['dash', 'giảm huyết áp', 'ít muối', 'tim mạch'],
            'mediterranean': ['địa trung hải', 'mediterranean', 'olive', 'dầu ô liu'],
            'gluten-free': ['không gluten', 'gluten free', 'celiac', 'dị ứng gluten'],
            'lactose-free': ['không lactose', 'lactose free', 'dị ứng sữa'],
            'diabetic': ['tiểu đường', 'diabetic', 'ít đường', 'không đường', 'kiểm soát đường huyết']
        }
        
        self.spicy_keywords = {
            'no-spicy': ['không cay', 'nhạt', 'không ớt'],
            'mild': ['ít cay', 'vừa cay', 'nhẹ'],
            'hot': ['cay', 'rất cay', 'ớt', 'nhiều ớt']
        }
        
        self.ingredient_keywords = {
            'seafood': ['hải sản', 'tôm', 'cua', 'ốc', 'sò', 'mực', 'cá', 'tép', 'ghẹ', 'bào ngư'],
            'beef': ['bò', 'thịt bò', 'beef'],  
            'pork': ['heo', 'thịt heo', 'thịt lợn', 'ba chỉ', 'sườn'],
            'chicken': ['gà', 'thịt gà', 'chicken', 'gà tây'],
            'vegetables': ['rau', 'củ', 'cải', 'rau xanh', 'rau củ', 'súp lơ', 'bông cải', 'cà', 'dưa', 'rau muống', 'rau lang', 'cải thìa', 'xà lách', 'cải bó xôi', 'rau dền', 'mồng tơi', 'canh rau', 'gỏi rau', 'nhiều rau', 'đầy rau', 'toàn rau'],
            'noodles': ['bún', 'phở', 'mì', 'bánh canh', 'bánh tráng', 'nem', 'cuốn'],
            'rice': ['cơm', 'gạo', 'xôi', 'chè'],
            'tofu': ['đậu phụ', 'đậu hũ', 'tàu hũ', 'chả chay', 'thịt chay']
        }
        
        # Từ khóa chay/mặn chính xác hơn
        self.vegetarian_keywords = [
            'chay', 'vegetarian', 'vegan', 'đậu phụ', 'đậu hũ', 'tàu hũ', 
            'chả chay', 'thịt chay', 'nấm', 'rau củ', 'chay nguyên chất'
        ]
        
        self.meat_keywords = [
            'thịt', 'bò', 'heo', 'gà', 'vịt', 'cá', 'tôm', 'cua', 'ốc', 'sò', 
            'mực', 'beef', 'pork', 'chicken', 'seafood'
        ]
        
        # Texture preferences
        self.texture_keywords = {
            'crispy': ['giòn', 'crispy', 'giòn tan', 'giòn rụm'],
            'soft': ['mềm', 'soft', 'mềm mại', 'tan chảy'],
            'chewy': ['dai', 'chewy', 'dẻo', 'có độ nhai'],
            'smooth': ['mịn', 'smooth', 'láng mịn', 'mượt'],
            'rough': ['thô', 'sần sùi', 'có độ nhám']
        }
        
        # Cooking methods
        self.cooking_methods = {
            'grilled': ['nướng', 'grilled', 'nướng than', 'nướng lửa'],
            'steamed': ['hấp', 'steamed', 'hấp cách thủy'],
            'boiled': ['luộc', 'boiled', 'niêu nước'],
            'fried': ['chiên', 'fried', 'chiên giòn', 'chiên ngập dầu'],
            'stir-fried': ['xào', 'stir-fried', 'xào tỏi', 'áp chảo'],
            'braised': ['kho', 'braised', 'om', 'niêu'],
            'raw': ['sống', 'raw', 'tái', 'gỏi'],
            'soup': ['canh', 'soup', 'súp', 'nước dùng']
        }
        
        # Regional preferences
        self.regional_keywords = {
            'north': ['bắc', 'hà nội', 'miền bắc', 'northern', 'phở bắc'],
            'central': ['trung', 'huế', 'miền trung', 'central', 'bún bò huế'],
            'south': ['nam', 'sài gòn', 'miền nam', 'southern', 'bún thịt nướng']
        }
        
        # Health conditions
        self.health_keywords = {
            'weight-loss': ['giảm cân', 'weight loss', 'béo phì', 'slimming'],
            'muscle-gain': ['tăng cơ', 'muscle gain', 'tập gym', 'bodybuilding'],
            'heart-healthy': ['tim mạch', 'heart healthy', 'cholesterol', 'huyết áp'],
            'digestive': ['tiêu hóa', 'digestive', 'dạ dày', 'đại tràng'],
            'anti-inflammatory': ['chống viêm', 'anti inflammatory', 'khớp', 'arthritis'],
            'energy-boost': ['tăng năng lượng', 'energy boost', 'mệt mỏi', 'suy nhược']
        }
        
        # Temperature preferences - mới thêm
        self.temperature_keywords = {
            'hot': ['ấm áp', 'nóng', 'hot', 'canh nóng', 'súp nóng', 'ấm', 'nóng hổi'],
            'warm': ['ấm', 'warm', 'ấm áp', 'ấm lòng'],
            'cold': ['lạnh', 'cold', 'mát', 'đá', 'iced']
        }
        
        self.dislike_keywords = [
            'không thích', 'không ăn', 'dị ứng', 'không được', 'tránh', 'ghét'
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
            'health_conscious': False,
            'texture_preferences': [],
            'cooking_methods': [],
            'regional_preferences': [],
            'health_conditions': [],
            'temperature_preferences': []
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
        
        # Phân tích texture preferences
        for texture, keywords in self.texture_keywords.items():
            if any(keyword in preference_text for keyword in keywords):
                analysis['texture_preferences'].append(texture)
        
        # Phân tích cooking methods
        for method, keywords in self.cooking_methods.items():
            if any(keyword in preference_text for keyword in keywords):
                context = self._get_keyword_context(preference_text, keywords[0])
                if not any(dislike in context for dislike in self.dislike_keywords):
                    analysis['cooking_methods'].append(method)
        
        # Phân tích regional preferences
        for region, keywords in self.regional_keywords.items():
            if any(keyword in preference_text for keyword in keywords):
                analysis['regional_preferences'].append(region)
        
        # Phân tích health conditions
        for condition, keywords in self.health_keywords.items():
            if any(keyword in preference_text for keyword in keywords):
                analysis['health_conditions'].append(condition)
        
        # Phân tích temperature preferences
        for temp, keywords in self.temperature_keywords.items():
            if any(keyword in preference_text for keyword in keywords):
                analysis['temperature_preferences'].append(temp)
        
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
    
    def _classify_vegetarian_meat(self, dish) -> str:
        """Phân loại món ăn chay/mặn dựa trên database và keyword analysis"""
        # Ưu tiên thông tin từ database
        vegetarian_or_meat = self._get_dish_attr(dish, 'vegetarian_or_meat', '').lower()
        
        if vegetarian_or_meat:
            if any(veg_word in vegetarian_or_meat for veg_word in ['chay', 'vegetarian', 'vegan']):
                return 'vegetarian'
            elif any(meat_word in vegetarian_or_meat for meat_word in ['mặn', 'meat', 'thịt']):
                return 'meat'
        
        # Fallback: phân tích từ tên và mô tả
        dish_name = (self._get_dish_attr(dish, 'name') or '').lower()
        dish_desc = (self._get_dish_attr(dish, 'description') or '').lower()
        dish_ingredients = (self._get_dish_attr(dish, 'ingredients') or '').lower()
        
        full_text = f"{dish_name} {dish_desc} {dish_ingredients}"
        
        # Kiểm tra từ khóa chay
        vegetarian_score = sum(1 for keyword in self.vegetarian_keywords if keyword in full_text)
        
        # Kiểm tra từ khóa mặn  
        meat_score = sum(1 for keyword in self.meat_keywords if keyword in full_text)
        
        if vegetarian_score > meat_score:
            return 'vegetarian'
        elif meat_score > 0:
            return 'meat'
        else:
            return 'unknown'
    
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
        
        # Điểm cho vùng miền yêu thích
        for region in analysis['regional_preferences']:
            regional_score, regional_reason = self._score_regional_preference(dish, region)
            score += regional_score
            if regional_reason:
                reasons.append(regional_reason)
        
        # Điểm cho temperature preferences
        for temp in analysis['temperature_preferences']:
            temp_score, temp_reason = self._score_temperature_preference(dish, temp)
            score += temp_score
            if temp_reason:
                reasons.append(temp_reason)
        
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
            classification = self._classify_vegetarian_meat(dish)
            
            if classification == 'meat':
                return -15, "Có thịt/cá (không phù hợp chay)"
            elif classification == 'vegetarian':
                if 'chay' in dish_name:
                    return 15, "Món chay thuần túy 100%"
                elif 'đậu phụ' in dish_name or 'tàu hũ' in dish_name:
                    return 14, "Đậu phụ giàu protein thực vật"
                elif 'nấm' in dish_name:
                    return 13, "Nấm bổ dưỡng, umami tự nhiên"
                else:
                    return 12, "Thực phẩm thực vật tự nhiên"
            elif any(word in dish_name for word in ['rau', 'củ', 'gỏi']) and classification != 'meat':
                return 10, "Rau củ tươi, có thể ăn chay"
                
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
    
    def _score_regional_preference(self, dish, region: str) -> tuple:
        """Tính điểm ưu tiên vùng miền"""
        dish_name = (self._get_dish_attr(dish, 'name') or '').lower()
        dish_desc = (self._get_dish_attr(dish, 'description') or '').lower()
        dish_region = (self._get_dish_attr(dish, 'region') or '').lower()
        
        full_text = f"{dish_name} {dish_desc} {dish_region}"
        
        if region == 'north':
            # Món miền Bắc - có từ khóa đặc trưng
            north_keywords = ['phở', 'bún chả', 'chả cá', 'nem rán', 'xôi', 'bánh cuốn', 'bún đậu', 'miến gà', 'canh chua', 'bắc', 'hà nội']
            if any(keyword in full_text for keyword in north_keywords):
                return 20, "Món đặc trưng miền Bắc"
            elif 'bắc' in dish_region or 'hà nội' in dish_region or 'northern' in dish_region:
                return 18, "Món của miền Bắc"
            # Trừ điểm cho món rõ ràng của miền khác
            elif any(keyword in full_text for keyword in ['bún bò huế', 'cơm tấm', 'bánh xèo', 'hủ tiếu', 'huế', 'sài gòn']):
                return -15, "Không phải món miền Bắc"
                
        elif region == 'central':
            # Món miền Trung - có từ khóa đặc trưng
            central_keywords = ['bún bò huế', 'bánh khoái', 'bánh bèo', 'bánh ít', 'mì quảng', 'cao lầu', 'bánh căn', 'trung', 'huế']
            if any(keyword in full_text for keyword in central_keywords):
                return 20, "Món đặc trưng miền Trung"
            elif 'trung' in dish_region or 'huế' in dish_region or 'central' in dish_region:
                return 18, "Món của miền Trung"
            # Trừ điểm cho món rõ ràng của miền khác
            elif any(keyword in full_text for keyword in ['phở', 'bún chả', 'cơm tấm', 'bánh xèo', 'bắc', 'sài gòn']):
                return -15, "Không phải món miền Trung"
                
        elif region == 'south':
            # Món miền Nam - có từ khóa đặc trưng  
            south_keywords = ['cơm tấm', 'bánh xèo', 'hủ tiếu', 'bánh mì', 'bánh khọt', 'bún thịt nướng', 'gỏi cuốn', 'nam', 'sài gòn']
            if any(keyword in full_text for keyword in south_keywords):
                return 20, "Món đặc trưng miền Nam"
            elif 'nam' in dish_region or 'sài gòn' in dish_region or 'southern' in dish_region:
                return 18, "Món của miền Nam"
            # Trừ điểm cho món rõ ràng của miền khác
            elif any(keyword in full_text for keyword in ['phở', 'bún chả', 'bún bò huế', 'bánh khoái', 'bắc', 'huế']):
                return -15, "Không phải món miền Nam"
        
        return 0, None
    
    def _score_temperature_preference(self, dish, temp_preference: str) -> tuple:
        """Tính điểm cho sở thích nhiệt độ món ăn"""
        dish_name = (self._get_dish_attr(dish, 'name') or '').lower()
        dish_desc = (self._get_dish_attr(dish, 'description') or '').lower()
        
        full_text = f"{dish_name} {dish_desc}"
        
        if temp_preference in ['hot', 'warm']:
            # Ưu tiên món nóng/ấm
            hot_keywords = ['canh', 'súp', 'soup', 'nước dùng', 'lẩu', 'cháo', 'chè', 'nóng', 'ấm']
            if any(keyword in full_text for keyword in hot_keywords):
                return 12, "Món ấm áp như bạn yêu cầu"
            # Món xào, hầm, nướng cũng thường ăn nóng
            elif any(keyword in full_text for keyword in ['xào', 'hầm', 'kho', 'rim', 'nướng']):
                return 8, "Món nóng phù hợp"
            # Trừ điểm cho món lạnh
            elif any(keyword in full_text for keyword in ['gỏi', 'salad', 'kem', 'đá', 'lạnh']):
                return -5, "Món lạnh (không phù hợp yêu cầu ấm áp)"
                
        elif temp_preference == 'cold':
            # Ưu tiên món lạnh
            cold_keywords = ['gỏi', 'salad', 'kem', 'đá', 'lạnh', 'mát']
            if any(keyword in full_text for keyword in cold_keywords):
                return 12, "Món mát lạnh như bạn yêu cầu"
            # Trừ điểm cho món nóng
            elif any(keyword in full_text for keyword in ['canh', 'súp', 'lẩu', 'cháo']):
                return -5, "Món nóng (không phù hợp yêu cầu lạnh)"
        
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
                return "Gỏi rau củ tươi mát, nhiều chất xơ"
            elif 'luộc' in dish_name:
                return "Rau luộc giữ vitamin, ít calo"
            elif 'canh' in dish_name and 'rau' in dish_name:
                return "Canh rau thanh mát, nhiều rau xanh"
            elif any(veg in dish_name for veg in ['rau muống', 'cải', 'rau lang']):
                return "Rau xanh giàu sắt và vitamin"
            else:
                return "Rau xanh bổ dưỡng, nhiều chất xơ"
                
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