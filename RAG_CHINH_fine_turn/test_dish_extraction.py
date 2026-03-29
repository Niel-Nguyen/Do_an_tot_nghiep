import re
from difflib import get_close_matches

# Test dish name extraction
test_input = "Món Gỏi ngó sen tôm thịt giá bao nhiêu?"

# Simulate dish_keys from RAG system (some sample Vietnamese dishes)
sample_dishes = [
    "Gỏi ngó sen tôm thịt",
    "Phở bò",
    "Bún chả",
    "Cơm tấm",
    "Canh thơm cá ngừ",
    "Bánh mì thịt nướng"
]

print(f"Testing dish extraction for: '{test_input}'")
print(f"Available dishes: {sample_dishes}")
print()

# Test 1: Simple extraction by checking if dish name exists in message
def simple_extract(message, dishes):
    message_lower = message.lower()
    for dish in dishes:
        if dish.lower() in message_lower:
            return dish
    return None

result1 = simple_extract(test_input, sample_dishes)
print(f"Simple extraction: {result1}")

# Test 2: Fuzzy matching
def fuzzy_extract(message, dishes, cutoff=0.6):
    message_lower = message.lower()
    
    # Try exact matching first
    for dish in dishes:
        if dish.lower() in message_lower:
            return dish
    
    # Try fuzzy matching
    words = message_lower.split()
    for dish in dishes:
        dish_words = dish.lower().split()
        for dish_word in dish_words:
            matches = get_close_matches(dish_word, words, n=1, cutoff=cutoff)
            if matches:
                return dish
    return None

result2 = fuzzy_extract(test_input, sample_dishes)
print(f"Fuzzy extraction: {result2}")

# Test 3: Regex patterns to remove question words
def clean_extract(message, dishes):
    # Remove question patterns
    clean_msg = re.sub(r'\b(món|giá|bao\s+nhiêu|như\s+thế\s+nào|\?)\b', '', message.lower())
    clean_msg = re.sub(r'\s+', ' ', clean_msg).strip()
    
    print(f"Cleaned message: '{clean_msg}'")
    
    for dish in dishes:
        if dish.lower() in clean_msg:
            return dish
    return None

result3 = clean_extract(test_input, sample_dishes)
print(f"Clean extraction: {result3}")
