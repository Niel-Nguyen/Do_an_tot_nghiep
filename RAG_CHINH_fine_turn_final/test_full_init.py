import sys
import os
sys.path.append('.')

from models.ai_models import ai_models
from utils.excel_loader import load_dishes_from_excel
from core.chatbot import VietnameseFoodChatbot
from core.rag_system import RAGSystem

print("=== FULL INITIALIZATION TEST ===")

# Step 1: Initialize AI models
print("1. Initializing AI models...")
if not ai_models.is_initialized():
    ai_models.initialize_models()
print(f"   AI Models ready: {ai_models.is_initialized()}")

# Step 2: Load dishes
print("2. Loading dishes from Excel...")
data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
dishes = load_dishes_from_excel(data_path)
print(f"   Loaded {len(dishes)} dishes")

# Step 3: Initialize chatbot
print("3. Initializing chatbot...")
vietnamese_food_chatbot = VietnameseFoodChatbot()
result = vietnamese_food_chatbot.initialize(dishes)
print(f"   Chatbot initialized: {result}")
print(f"   Chatbot ready: {vietnamese_food_chatbot.is_ready}")

# Step 4: Check RAG system
print("4. Checking RAG system...")
from core.chatbot import rag_system
print(f"   RAG system initialized: {rag_system.is_initialized}")
print(f"   Dishes in lookup: {len(rag_system.dishes_lookup)}")

if len(rag_system.dishes_lookup) > 0:
    # Check for our test dish
    test_dish = rag_system.dishes_lookup.get("Gỏi ngó sen tôm thịt", None)
    print(f"   'Gỏi ngó sen tôm thịt' found: {test_dish is not None}")
    if test_dish:
        print(f"   Dish details: {test_dish.name}, Price: {test_dish.price}")

# Step 5: Test extraction
print("5. Testing dish extraction...")
if vietnamese_food_chatbot.is_ready:
    test_phrase = "có Gỏi ngó sen tôm thịt không"
    extracted = vietnamese_food_chatbot._extract_dish_name(test_phrase)
    print(f"   Extracted from '{test_phrase}': '{extracted}'")
else:
    print("   Chatbot not ready for testing")

print("\n=== CONCLUSION ===")
if vietnamese_food_chatbot.is_ready and len(rag_system.dishes_lookup) > 0:
    print("✅ Everything looks good - chatbot should work!")
else:
    print("❌ Something is wrong with initialization")
