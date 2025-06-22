from fastapi import APIRouter
from core.chatbot import vietnamese_food_chatbot

router = APIRouter()

@router.get("/stats")
def get_stats():
    return vietnamese_food_chatbot.get_chatbot_stats()
