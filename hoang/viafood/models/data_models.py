from dataclasses import dataclass
from typing import List, Optional
import pandas as pd

@dataclass
class VietnameseDish:
    """Mô hình dữ liệu cho món ăn Việt Nam"""
    name: str
    region: str
    description: str
    ingredients: str
    recipe: str
    link: Optional[str] = None
    image: Optional[str] = None
    dish_type: str = ""  # Chay/mặn
    mood: str = ""  # Tâm trạng, cảm xúc
    meal_category: str = ""  # Chính/vặt
    texture: str = ""  # Khô/nước
    contributor: str = ""  # Người điền
    
    def to_content_string(self) -> str:
        """Chuyển đổi thành chuỗi nội dung cho RAG"""
        content_parts = [
            f"Tên món: {self.name}",
            f"Vùng miền: {self.region}",
            f"Mô tả: {self.description}",
            f"Nguyên liệu: {self.ingredients}",
            f"Cách làm: {self.recipe}",
        ]
        
        if self.dish_type:
            content_parts.append(f"Loại món: {self.dish_type}")
        if self.mood:
            content_parts.append(f"Phù hợp với tâm trạng: {self.mood}")
        if self.meal_category:
            content_parts.append(f"Phân loại: {self.meal_category}")
        if self.texture:
            content_parts.append(f"Tính chất: {self.texture}")
        if self.link:
            content_parts.append(f"Tham khảo: {self.link}")
            
        return "\n".join(content_parts)
    
    def to_metadata_dict(self) -> dict:
        """Chuyển đổi thành metadata cho Document"""
        return {
            "name": self.name,
            "region": self.region,
            "dish_type": self.dish_type,
            "mood": self.mood,
            "meal_category": self.meal_category,
            "texture": self.texture,
            "contributor": self.contributor,
            "link": self.link,
            "image": self.image
        }

@dataclass 
class ChatMessage:
    """Mô hình cho tin nhắn chat"""
    role: str  # "user" hoặc "assistant"
    content: str
    timestamp: Optional[str] = None

@dataclass
class SearchResult:
    """Mô hình cho kết quả tìm kiếm"""
    dish: VietnameseDish
    score: float
    relevance: str = ""