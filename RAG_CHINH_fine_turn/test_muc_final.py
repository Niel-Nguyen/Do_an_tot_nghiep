from models.ai_models import ai_models
ai_models.initialize_models()

from core.rag_system import rag_system
from utils.excel_loader import load_dishes_from_excel
from core.chatbot import VietnameseFoodChatbot

dishes = load_dishes_from_excel('data100mon.xlsx')
rag_system.initialize(dishes)

chatbot = VietnameseFoodChatbot()
chatbot.initialize(dishes)

# Test extract dish name với món mực
print('=== TEST EXTRACT: mực ống hấp cũ dậu ===')
dish_name = chatbot._extract_dish_name('mực ống hấp cũ dậu')
print(f'Extracted: "{dish_name}"')

print('\n=== TEST CHAT: có mực ống hấp cũ dậu không ===')
result = chatbot.chat('có mực ống hấp cũ dậu không', user_id='test_debug')
print('Result:', result[:300] + '...' if len(result) > 300 else result)
