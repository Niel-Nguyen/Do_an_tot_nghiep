from models.ai_models import ai_models
ai_models.initialize_models()

from core.rag_system import rag_system
from utils.excel_loader import load_dishes_from_excel
from core.chatbot import VietnameseFoodChatbot

dishes = load_dishes_from_excel('data100mon.xlsx')
rag_system.initialize(dishes)

chatbot = VietnameseFoodChatbot()
chatbot.initialize(dishes)

# Test các loại câu hỏi
test_cases = [
    "Cho tôi biết món Mực ống hấp củ đậu là món gì?",
    "có mực ống hấp cũ dậu không",
    "cho tôi 2 phần mực ống hấp củ đậu",  # Đây mới là order thực sự
]

for i, test_input in enumerate(test_cases, 1):
    print(f'=== TEST {i}: {test_input} ===')
    try:
        result = chatbot.chat(test_input, user_id=f'test_debug{i}')
        print('Result:', result[:250] + '...' if len(result) > 250 else result)
        print('Is order?', '✅ Đã thêm' in result)
    except Exception as e:
        print('ERROR:', str(e))
    print('=' * 50)
