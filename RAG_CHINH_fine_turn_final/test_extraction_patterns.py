import sys
sys.path.append('.')

from app import vietnamese_food_chatbot, ensure_chatbot_ready

# Ensure chatbot is ready before testing
ensure_chatbot_ready()

# Test dish extraction with different patterns
test_cases = [
    "gỏi ngó sen tôm thịt giá",
    "Món Gỏi ngó sen tôm thịt giá bao nhiêu?",
    "Món Gỏi ngó sen tôm thịt",
    "có Gỏi ngó sen tôm thịt không",
    "Gỏi ngó sen tôm thịt có không"
]

print("=== Testing dish name extraction ===")
for test_case in test_cases:
    extracted = vietnamese_food_chatbot._extract_dish_name(test_case)
    print(f"'{test_case}' -> '{extracted}'")
