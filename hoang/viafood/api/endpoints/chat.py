from fastapi import APIRouter
from pydantic import BaseModel
from core.chatbot import vietnamese_food_chatbot

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat_with_bot(request: ChatRequest):
    response = vietnamese_food_chatbot.chat(request.message)
    return {"response": response}
