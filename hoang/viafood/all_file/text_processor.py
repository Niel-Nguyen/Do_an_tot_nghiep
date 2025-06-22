import re
from typing import List, Dict, Any
from models.data_models import VietnameseDish

class TextProcessor:
    """Xử lý và chuẩn hóa văn bản"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Làm sạch văn bản"""
        if not text:
            return ""
        
        # Loại bỏ ký tự đặc biệt và khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Loại bỏ các ký tự không mong muốn
        text = re.sub(r'[^\w\s\u00C0-\u1EF9,.-]', '', text)
        
        return text
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Trích xuất từ khóa từ văn bản"""
        if not text:
            return []
        
        # Chuyển về chữ thường
        text = text.lower()
        
        # Loại bỏ stop words tiếng Việt cơ bản
        stop_words = {
            'và', 'hoặc', 'với', 'của', 'cho', 'từ', 'trong', 'trên', 'dưới', 
            'để', 'khi', 'mà', 'nếu', 'thì', 'như', 'theo', 'về', 'tại',
            'có', 'là', 'được', 'sẽ', 'đã', 'đang', 'không', 'chưa'
        }
        
        # Tách từ và loại bỏ stop words
        words = re.findall(r'\b\w+\b', text)
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    @staticmethod
    def format_ingredients(ingredients: str) -> List[str]:
        """Định dạng danh sách nguyên liệu"""
        if not ingredients:
            return []
        
        # Tách nguyên liệu bằng dấu phay hoặc xuống dòng
        items = re.split(r'[,\n;]', ingredients)
        
        # Làm sạch từng nguyên liệu
        cleaned_items = []
        for item in items:
            item = item.strip()
            if item:
                # Loại bỏ số lượng và đơn vị (nếu có)
                item = re.sub(r'^\d+\s*\w*\s*', '', item)
                cleaned_items.append(item.capitalize())
        
        return cleaned_items
    
    @staticmethod
    def format_recipe_steps(recipe: str) -> List[str]:
        """Định dạng các bước công thức"""
        if not recipe:
            return []
        
        # Tách các bước bằng dấu chấm hoặc xuống dòng
        steps = re.split(r'[.\n]', recipe)
        
        # Làm sạch từng bước
        cleaned_steps = []
        for i, step in enumerate(steps, 1):
            step = step.strip()
            if step and len(step) > 10:  # Chỉ giữ các bước có nội dung
                # Thêm số thứ tự nếu chưa có
                if not re.match(r'^\d+', step):
                    step = f"{i}. {step}"
                cleaned_steps.append(step)
        
        return cleaned_steps
    
    @staticmethod
    def create_search_content(dish: VietnameseDish) -> str:
        """Tạo nội dung tìm kiếm tối ưu cho RAG"""
        content_parts = []
        
        # Tên món (quan trọng nhất)
        content_parts.append(f"Tên món: {dish.name}")
        
        # Vùng miền
        if dish.region:
            content_parts.append(f"Vùng miền: {dish.region}")
        
        # Mô tả
        if dish.description:
            content_parts.append(f"Mô tả: {TextProcessor.clean_text(dish.description)}")
        
        # Nguyên liệu (tối ưu cho tìm kiếm)
        if dish.ingredients:
            ingredients_list = TextProcessor.format_ingredients(dish.ingredients)
            content_parts.append(f"Nguyên liệu chính: {', '.join(ingredients_list[:5])}")  # Chỉ lấy 5 nguyên liệu đầu
        
        # Công thức (tóm tắt)
        if dish.recipe:
            recipe_summary = dish.recipe[:200] + "..." if len(dish.recipe) > 200 else dish.recipe
            content_parts.append(f"Cách làm: {TextProcessor.clean_text(recipe_summary)}")
        
        # Các thông tin phân loại
        classifications = []
        if dish.dish_type:
            classifications.append(f"Loại: {dish.dish_type}")
        if dish.meal_category:
            classifications.append(f"Phân loại: {dish.meal_category}")
        if dish.texture:
            classifications.append(f"Tính chất: {dish.texture}")
        if dish.mood:
            classifications.append(f"Phù hợp: {dish.mood}")
        
        if classifications:
            content_parts.append(" | ".join(classifications))
        
        return "\n".join(content_parts)
    
    @staticmethod
    def analyze_query_intent(query: str) -> Dict[str, Any]:
        """Phân tích ý định của câu hỏi"""
        query_lower = query.lower()
        
        intent = {
            'type': 'general',  # general, recipe, ingredient, region, recommendation
            'keywords': TextProcessor.extract_keywords(query),
            'filters': {}
        }
        
        # Phân tích loại câu hỏi
        if any(word in query_lower for word in ['cách làm', 'công thức', 'nấu', 'chế biến']):
            intent['type'] = 'recipe'
        elif any(word in query_lower for word in ['nguyên liệu', 'cần gì', 'chuẩn bị']):
            intent['type'] = 'ingredient'
        elif any(word in query_lower for word in ['gợi ý', 'tư vấn', 'nên ăn', 'món nào']):
            intent['type'] = 'recommendation'
        elif any(word in query_lower for word in ['miền bắc', 'miền nam', 'miền trung', 'hà nội', 'sài gòn']):
            intent['type'] = 'region'
        
        # Phân tích bộ lọc
        if 'chay' in query_lower:
            intent['filters']['dish_type'] = 'chay'
        elif 'mặn' in query_lower:
            intent['filters']['dish_type'] = 'mặn'
        
        if any(word in query_lower for word in ['nước', 'canh', 'súp']):
            intent['filters']['texture'] = 'nước'
        elif any(word in query_lower for word in ['khô', 'nướng', 'chiên']):
            intent['filters']['texture'] = 'khô'
        
        return intent

# Global instance
text_processor = TextProcessor()