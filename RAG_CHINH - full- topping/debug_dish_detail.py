import sys
sys.path.append('.')

from core.rag_system import RAGSystem

# Initialize RAG system
rag_system = RAGSystem()

print("=== DEBUG DISH LOOKUP ===")
print(f"Total dishes in lookup: {len(rag_system.dishes_lookup)}")

# Search for "goi ngo sen" variations
search_terms = [
    "goi ngo sen tom thit",
    "Gỏi ngó sen tôm thịt", 
    "gỏi ngó sen tôm thịt",
    "Goi ngo sen tom thit"
]

print("\n=== EXACT SEARCH ===")
for term in search_terms:
    found = rag_system.dishes_lookup.get(term, None)
    print(f"'{term}' -> {found.name if found else 'NOT FOUND'}")

print("\n=== PARTIAL SEARCH ===")
for key, dish in rag_system.dishes_lookup.items():
    if "ngó sen" in key.lower() or "ngo sen" in key.lower():
        print(f"KEY: '{key}' -> DISH: '{dish.name}'")

print("\n=== KEYS CONTAINING 'goi' ===")
goi_dishes = [key for key in rag_system.dishes_lookup.keys() if "goi" in key.lower() or "gỏi" in key.lower()]
print(f"Found {len(goi_dishes)} dishes with 'goi':")
for key in goi_dishes[:10]:  # Show first 10
    dish = rag_system.dishes_lookup[key]
    print(f"  '{key}' -> '{dish.name}'")

print("\n=== TEST EXTRACTION ===")
from core.chatbot import VietnameseFoodChatbot
chatbot = VietnameseFoodChatbot()

test_phrases = [
    "có Gỏi ngó sen tôm thịt không",
    "Món Gỏi ngó sen tôm thịt giá bao nhiêu",
    "gỏi ngó sen tôm thịt"
]

for phrase in test_phrases:
    extracted = chatbot._extract_dish_name(phrase)
    print(f"'{phrase}' -> extracted: '{extracted}'")
    if extracted:
        found_dish = rag_system.dishes_lookup.get(extracted, None)
        print(f"  -> dish found: {found_dish.name if found_dish else 'NOT FOUND'}")
    print()
