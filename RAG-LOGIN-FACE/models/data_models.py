from dataclasses import dataclass
from typing import Optional

@dataclass
class VietnameseDish:
    name: str
    region: str
    ingredients: str
    description: str
    recipe: str
    price: Optional[str] = None
    unit: Optional[str] = None
    mood: str = ""
    dish_type: str = ""
    texture: str = ""
    image: Optional[str] = None
    meal_category: str = ""
    cook_time: Optional[str] = None
    calories: Optional[str] = None
    fat: Optional[str] = None
    fiber: Optional[str] = None
    sugar: Optional[str] = None
    protein: Optional[str] = None
    nutrient_content: Optional[str] = None
    contributor: Optional[str] = None
    link: Optional[str] = None

    def to_content_string(self) -> str:
        content_parts = [
            f"Tên món: {self.name}",
            f"Vùng miền: {self.region}",
            f"Mô tả: {self.description}",
            f"Nguyên liệu: {self.ingredients}",
            f"Cách làm: {self.recipe}",
        ]
        if self.price:
            content_parts.append(f"Giá: {self.price}")
        if self.unit:
            content_parts.append(f"Đơn vị tính: {self.unit}")
        if self.dish_type:
            content_parts.append(f"Loại món: {self.dish_type}")
        if self.mood:
            content_parts.append(f"Tâm trạng: {self.mood}")
        if self.meal_category:
            content_parts.append(f"Chay/Mặn: {self.meal_category}")
        if self.texture:
            content_parts.append(f"Tính chất: {self.texture}")
        if self.cook_time:
            content_parts.append(f"Thời gian nấu: {self.cook_time}")
        if self.calories:
            content_parts.append(f"Calories: {self.calories}")
        if self.fat:
            content_parts.append(f"Fat: {self.fat}")
        if self.fiber:
            content_parts.append(f"Fiber: {self.fiber}")
        if self.sugar:
            content_parts.append(f"Sugar: {self.sugar}")
        if self.protein:
            content_parts.append(f"Protein: {self.protein}")
        if self.nutrient_content:
            content_parts.append(f"Thành phần dinh dưỡng: {self.nutrient_content}")
        if self.image:
            content_parts.append(f"Hình ảnh: {self.image}")
        if self.link:
            content_parts.append(f"Tham khảo: {self.link}")
        return "\n".join(content_parts)

    def to_metadata_dict(self) -> dict:
        return {
            "name": self.name,
            "region": self.region,
            "ingredients": self.ingredients,
            "description": self.description,
            "recipe": self.recipe,
            "price": self.price,
            "unit": self.unit,
            "mood": self.mood,
            "dish_type": self.dish_type,
            "texture": self.texture,
            "image": self.image,
            "meal_category": self.meal_category,
            "cook_time": self.cook_time,
            "calories": self.calories,
            "fat": self.fat,
            "fiber": self.fiber,
            "sugar": self.sugar,
            "protein": self.protein,
            "nutrient_content": self.nutrient_content,
            "contributor": self.contributor,
            "link": self.link
        }

@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: Optional[str] = None

@dataclass
class SearchResult:
    dish: VietnameseDish
    score: float
    relevance: str = ""
