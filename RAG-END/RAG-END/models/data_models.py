from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import uuid

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

@dataclass
class Table:
    """Model cho bàn trong nhà hàng"""
    id: str
    name: str  # Tên bàn (VD: Bàn 1, Bàn VIP, Bàn ngoài trời)
    capacity: int  # Sức chứa (số người)
    status: str  # available, occupied, reserved, maintenance
    qr_code: str  # URL hoặc data của QR code
    location: str  # Vị trí (VD: Tầng 1, Khu A, Ngoài trời)
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

@dataclass
class Bill:
    """Model cho hóa đơn của một bàn"""
    id: str
    table_id: str
    table_name: str
    items: List[dict]  # Danh sách món ăn đã đặt
    total_amount: float
    status: str  # pending, confirmed, in_progress, done, paid, cancelled
    created_at: datetime
    updated_at: datetime
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

@dataclass
class TableSession:
    """Model cho phiên làm việc của một bàn"""
    id: str
    table_id: str
    table_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    customer_count: int = 0
    status: str = "active"  # active, closed
    bill_id: Optional[str] = None
    session_token: Optional[str] = None  # Token bảo mật cho phiên bàn
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.start_time:
            self.start_time = datetime.now()
