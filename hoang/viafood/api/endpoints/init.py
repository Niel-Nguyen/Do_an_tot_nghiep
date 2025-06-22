from fastapi import APIRouter
from core.chatbot import vietnamese_food_chatbot
from models.ai_models import ai_models
from utils.data_loader import data_loader

router = APIRouter()

@router.post("/init")
def initialize():
    if not ai_models.initialize_models():
        return {"status": "error", "message": "Lỗi khởi tạo AI models"}

    if not data_loader.load_excel_data():
        return {"status": "error", "message": "Không tải được dữ liệu món ăn"}

    dishes = data_loader.get_dishes()

    if not vietnamese_food_chatbot.initialize(dishes):
        return {"status": "error", "message": "Không khởi tạo được RAG chatbot"}

    return {"status": "ok", "message": f"Khởi tạo thành công với {len(dishes)} món ăn"}
