from typing import List, Dict, Any
from models.data_models import VietnameseDish

class TextProcessor:
    def create_search_content(self, dish: VietnameseDish) -> str:
        return dish.to_content_string()

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
