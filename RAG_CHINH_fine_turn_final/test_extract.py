from models.ai_models import ai_models
ai_models.initialize_models()

from core.rag_system import rag_system
from utils.excel_loader import load_dishes_from_excel
from core.chatbot import VietnameseFoodChatbot

dishes = load_dishes_from_excel('data100mon.xlsx')
rag_system.initialize(dishes)

# Test với conversation mới hoàn toàn
chatbot = VietnameseFoodChatbot()
chatbot.initialize(dishes)

# Test extract dish name
print('=== TEST EXTRACT DISH NAME ===')
test_inputs = [
    'lẩu tôm chua',
    'Lẩu tôm chua',
    'lau tom chua',
    'có lẩu tôm chua không'
]

for test_input in test_inputs:
    dish_name = chatbot._extract_dish_name(test_input)
    print(f'Input: "{test_input}" -> Extracted: "{dish_name}"')

print('\n=== TEST FULL CHAT ===')
result = chatbot.chat('có lẩu tôm chua không', user_id='test_debug')
print('Chat result:', result[:200] + '...' if len(result) > 200 else result)
