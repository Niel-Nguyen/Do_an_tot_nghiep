import sys
sys.path.append('.')

from core.rag_system import rag_system

# Test if dish exists in lookup
dish_name = "Gỏi ngó sen tôm thịt"
print(f"Checking if '{dish_name}' exists in dishes_lookup...")

if dish_name in rag_system.dishes_lookup:
    dish = rag_system.dishes_lookup[dish_name]
    print(f"✅ Found: {dish.name}")
    print(f"Price: {getattr(dish, 'price', 'No price')}")
    print(f"Description: {getattr(dish, 'description', 'No description')}")
else:
    print(f"❌ Not found in dishes_lookup")
    print(f"Available dishes (first 10):")
    for i, key in enumerate(list(rag_system.dishes_lookup.keys())[:10]):
        print(f"  {i+1}. {key}")

# Test context generation
print(f"\n--- Testing context generation ---")
context = rag_system.get_context_for_llm(dish_name)
print(f"Context length: {len(context)}")
print(f"Context preview: {context[:200]}...")
