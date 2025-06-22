from fastapi import APIRouter
from core.chatbot import vietnamese_food_chatbot

router = APIRouter()

@router.post("/clear-chat")
def clear_chat_history():
    vietnamese_food_chatbot.clear_conversation()
    return {"status": "ok", "message": "Đã xóa lịch sử hội thoại"}
