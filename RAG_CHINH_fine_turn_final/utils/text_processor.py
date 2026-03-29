#text_processor.py
from typing import List, Dict, Any
import re
import unicodedata
from models.data_models import VietnameseDish

class TextProcessor:
    def create_search_content(self, dish: VietnameseDish) -> str:
        return dish.to_content_string()

    def remove_emojis_and_icons(self, text: str) -> str:
        """
        Loại bỏ emojis, icons và các ký tự đặc biệt khỏi văn bản
        Giữ lại chữ cái, số và dấu câu cơ bản
        """
        # Loại bỏ emojis (Unicode emoji ranges)
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # Emoticons
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # Misc Symbols and Pictographs
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # Transport and Map Symbols
        text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # Regional Indicator Symbols
        text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # Supplemental Symbols and Pictographs
        text = re.sub(r'[\U0001FA70-\U0001FAFF]', '', text)  # Symbols and Pictographs Extended-A
        
        # Loại bỏ các ký tự đặc biệt khác như bullet points, arrows, etc.
        text = re.sub(r'[•·▪▫‣⁃◦‣⁌⁍]', '', text)  # Bullet points
        text = re.sub(r'[→←↑↓⇒⇐⇑⇓]', '', text)  # Arrows
        text = re.sub(r'[★☆✭✮✯✰]', '', text)  # Stars
        text = re.sub(r'[♥♦♣♠]', '', text)  # Card suits
        text = re.sub(r'[☀☁☂☃☄★☆☎☏]', '', text)  # Weather and misc symbols
        
        # Loại bỏ các ký tự Unicode đặc biệt khác
        text = ''.join(char for char in text if unicodedata.category(char) not in ['So', 'Sk', 'Sm'])
        
        # Dọn dẹp khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def clean_text_for_reading(self, text: str) -> str:
        """
        Làm sạch văn bản để chatbot đọc, loại bỏ emojis, format và link hình ảnh
        Đảm bảo giữ nguyên toàn bộ nội dung văn bản hợp lệ
        """
        # Loại bỏ emojis trước
        text = self.remove_emojis_and_icons(text)
        
        # Loại bỏ Markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
        
        # Loại bỏ HTML tags một cách chính xác
        # Xử lý các HTML tags bị lỗi format như <brimg, <img src'...
        text = re.sub(r'<brimg[^>]*>', '', text)
        text = re.sub(r'<img[^>]*>', '', text)
        
        # Xử lý các HTML tags còn sót lại
        text = re.sub(r'<[^>]+>', '', text)
        
        # Loại bỏ các HTML fragments bị lỗi format cụ thể
        # Loại bỏ brimg và các biến thể (không có dấu < >)
        text = re.sub(r'brimg\s+[^>]*', '', text)
        
        # Loại bỏ các HTML attributes bị lỗi format cụ thể
        # Chỉ loại bỏ những attributes thực sự bị lỗi, không loại bỏ nội dung hợp lệ
        text = re.sub(r'\b(?:class|style|title|alt|src|id|name|type|value|placeholder|data-[a-zA-Z-]+)\s*[\'"]?[^\s\'">]*[\'"]?', '', text)
        
        # Loại bỏ các CSS properties bị lỗi
        text = re.sub(r'\b(?:max-width|border-radius|margin|cursor|zoom-in|zoom-out)\s*:\s*[^;]*;?', '', text)
        
        # Loại bỏ các giá trị CSS cụ thể
        text = re.sub(r'\b(?:180px|8px|0|zoom-in|zoom-out)\b', '', text)
        
        # Loại bỏ link hình ảnh và URL
        # Loại bỏ các URL pattern phổ biến
        text = re.sub(r'https?://[^\s]+', '', text)  # HTTP/HTTPS URLs
        text = re.sub(r'www\.[^\s]+', '', text)     # www URLs
        text = re.sub(r'[^\s]+\.(com|vn|org|net|edu|gov|info|biz|co|io|ai|app|dev)[^\s]*', '', text)  # Domain extensions
        
        # Loại bỏ các đường dẫn file hình ảnh
        text = re.sub(r'[^\s]+\.(jpg|jpeg|png|gif|bmp|webp|svg|ico)[^\s]*', '', text)  # Image file extensions
        text = re.sub(r'[^\s]+\.(mp4|avi|mov|wmv|flv|webm)[^\s]*', '', text)  # Video file extensions
        
        # Dọn dẹp khoảng trắng thừa sau khi loại bỏ các pattern
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        # Ưu tiên nhận diện vùng miền Việt Nam nếu user hỏi 'trung', 'bắc', 'nam' mà không có từ 'hoa', 'quốc', 'china', ...
        is_vietnam_region = False
        region_map = {'trung': 'miền trung', 'bắc': 'miền bắc', 'nam': 'miền nam'}
        for key, region in region_map.items():
            if key in query_lower:
                # Nếu có từ 'hoa', 'quốc', 'china' thì không phải vùng miền VN
                if not any(x in query_lower for x in ['hoa', 'quốc', 'china', 'trung quốc', 'trung hoa']):
                    is_vietnam_region = region
                    break
        # Bổ sung nhận diện intent contact
        contact_keywords = ["địa chỉ", "liên hệ", "số điện thoại", "hotline", "address", "contact"]
        if any(kw in query_lower for kw in contact_keywords):
            intent_type = "contact"
        elif any(kw in query_lower for kw in ["cách làm", "nấu", "công thức"]):
            intent_type = "recipe"
        elif any(kw in query_lower for kw in ["nguyên liệu", "thành phần"]):
            intent_type = "ingredient"
        elif any(kw in query_lower for kw in ["gợi ý", "nên ăn", "phù hợp"]):
            intent_type = "recommendation"
        elif any(kw in query_lower for kw in ["miền bắc", "miền nam", "miền trung"]):
            intent_type = "region"
        elif is_vietnam_region:
            intent_type = "region"
        else:
            intent_type = "other"
        keywords = [w for w in query_lower.split() if len(w) > 2]
        filters = {}
        if is_vietnam_region:
            filters["region"] = is_vietnam_region
        if "chay" in query_lower:
            filters["dish_type"] = "chay"
        if "khô" in query_lower:
            filters["texture"] = "khô"
        if "nước" in query_lower:
            filters["texture"] = "nước"
        return {
            "type": intent_type,
            "keywords": keywords,
            "filters": filters
        }

    def clean_text(self, text: str) -> str:
        return text.strip()

    def extract_keywords(self, text: str) -> List[str]:
        return [w for w in text.lower().split() if len(w) > 2]

text_processor = TextProcessor()
