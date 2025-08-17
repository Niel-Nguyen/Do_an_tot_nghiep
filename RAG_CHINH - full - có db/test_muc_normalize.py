import unicodedata
import re

def normalize(text):
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r'\s+', ' ', text)  # thay mọi loại whitespace thành 1 space
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

user_input = 'mực ống hấp cũ dậu'
dish_name = 'Mực ống hấp củ đậu'

user_norm = normalize(user_input)
dish_norm = normalize(dish_name)

print(f'User input: {user_input}')
print(f'User normalized: "{user_norm}"')
print(f'Dish name: {dish_name}')
print(f'Dish normalized: "{dish_norm}"')
print(f'Match? {user_norm == dish_norm}')
print(f'Substring? {dish_norm in user_norm}')

# Test fuzzy match
import difflib
match = difflib.get_close_matches(user_norm, [dish_norm], n=1, cutoff=0.7)
print(f'Fuzzy match (cutoff=0.7): {match}')
match2 = difflib.get_close_matches(user_norm, [dish_norm], n=1, cutoff=0.6)
print(f'Fuzzy match (cutoff=0.6): {match2}')
