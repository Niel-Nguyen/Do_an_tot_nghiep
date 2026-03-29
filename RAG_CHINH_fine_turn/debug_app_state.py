import sys
sys.path.append('.')

from app import vietnamese_food_chatbot, rag_system, normalize, ensure_chatbot_ready

print("=== FORCING APP INITIALIZATION ===")
ensure_chatbot_ready()

print("=== APP STATE DEBUG ===")
print(f"Chatbot ready: {vietnamese_food_chatbot.is_ready}")
print(f"RAG system initialized: {rag_system.is_initialized}")
print(f"Total dishes in lookup: {len(rag_system.dishes_lookup)}")

# Check for target dish
target_dish = rag_system.dishes_lookup.get("Gỏi ngó sen tôm thịt")
print(f"'Gỏi ngó sen tôm thịt' found: {target_dish is not None}")

if target_dish:
    print(f"Dish details: {target_dish.name}, Price: {target_dish.price}")

# List all dishes containing "goi" or "sen"
print("\nDishes containing 'gỏi' or 'sen':")
for name, dish in rag_system.dishes_lookup.items():
    if "gỏi" in name.lower() or "sen" in name.lower() or "goi" in normalize(name) or "sen" in normalize(name):
        print(f"  {name}")

# Show first 10 dishes
print(f"\nFirst 10 dishes in lookup:")
for i, (name, dish) in enumerate(list(rag_system.dishes_lookup.items())[:10]):
    print(f"  {i+1}. {name}")

# Look for similar names
print(f"\nSimilar dishes with 'sen' and 'tôm':")
for name in rag_system.dishes_lookup.keys():
    if "sen" in name.lower() and "tôm" in name.lower():
        print(f"  '{name}'")
