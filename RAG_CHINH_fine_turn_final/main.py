from core.chatbot import vietnamese_food_chatbot
from utils.excel_loader import load_dishes_from_excel
from models.ai_models import ai_models
from config.settings import settings
import re

def strip_html_and_markdown(text):
    # Loại bỏ tag HTML
    text = re.sub(r'<.*?>', '', text)
    # Loại bỏ ký hiệu markdown in đậm/nhấn mạnh
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **text**
    text = re.sub(r'__([^_]+)__', r'\1', text)          # __text__
    text = re.sub(r'\*([^*]+)\*', r'\1', text)        # *text*
    text = re.sub(r'_([^_]+)_', r'\1', text)            # _text_
    return text

if __name__ == "__main__":
    # Thiết lập API key nếu cần
    # settings.GOOGLE_API_KEY = "AIzaSyD9pKeqv1uWrXu2MsM7t6Hf26EAjoKQTIk"
    if not ai_models.is_initialized():
        if not ai_models.initialize_models():
            print("Lỗi: Không thể khởi tạo AI Models. Kiểm tra API key và cấu hình.")
            exit(1)
    # Load dữ liệu món ăn từ file Excel
    dishes = load_dishes_from_excel("data100mon.xlsx")
    vietnamese_food_chatbot.initialize(dishes)
    print("Chatbot ẩm thực Việt Nam đã sẵn sàng! Gõ 'exit' để thoát.")
    while True:
        user_input = input("Bạn: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            break
        answer = vietnamese_food_chatbot.chat(user_input)
        print("Bot:", strip_html_and_markdown(answer))
