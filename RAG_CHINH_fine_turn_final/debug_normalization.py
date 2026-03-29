import sys
sys.path.append('.')

from core.chatbot import VietnameseFoodChatbot, normalize
from core.rag_system import rag_system

print("=== Testing normalization and matching ===")

# Test normalization
test_inputs = [
    "gỏi ngó sen tôm thịt giá",
    "Món Gỏi ngó sen tôm thịt",
    "có Gỏi ngó sen tôm thịt không",
    "Gỏi ngó sen tôm thịt"
]

print("User input normalization:")
for inp in test_inputs:
    norm = normalize(inp)
    print(f"'{inp}' -> '{norm}'")

print("\nDish names in database:")
for dish_name, dish_obj in list(rag_system.dishes_lookup.items())[:10]:
    dish_norm = normalize(dish_name)
    print(f"'{dish_name}' -> '{dish_norm}'")

print("\nLooking for 'Gỏi ngó sen tôm thịt' specifically:")
target_dish = rag_system.dishes_lookup.get("Gỏi ngó sen tôm thịt")
if target_dish:
    target_norm = normalize(target_dish.name)
    print(f"Database: '{target_dish.name}' -> '{target_norm}'")
    
    # Test if any user input matches
    for inp in test_inputs:
        user_norm = normalize(inp)
        print(f"'{inp}' -> '{user_norm}'")
        print(f"  Exact match? {user_norm == target_norm}")
        print(f"  Contains dish? {target_norm in user_norm}")
        print(f"  User contains dish? {user_norm in target_norm}")
        print()
else:
    print("❌ 'Gỏi ngó sen tôm thịt' not found in database")

print("\nAll dishes containing 'goi ngo sen':")
for dish_name, dish_obj in rag_system.dishes_lookup.items():
    dish_norm = normalize(dish_name)
    if "goi ngo sen" in dish_norm:
        print(f"'{dish_name}' -> '{dish_norm}'")
