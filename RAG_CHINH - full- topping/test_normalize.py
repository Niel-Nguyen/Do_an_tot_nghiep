import unicodedata
import re

def normalize(text):
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r'\s+', ' ', text)  # thay mọi loại whitespace thành 1 space
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

user_input = 'lẩu tôm chua'
dish_name = 'Lẩu tôm chua'

user_norm = normalize(user_input)
dish_norm = normalize(dish_name)

print(f'User input: {user_input}')
print(f'User normalized: "{user_norm}"')
print(f'Dish name: {dish_name}')
print(f'Dish normalized: "{dish_norm}"')
print(f'Match? {user_norm == dish_norm}')
print(f'Substring? {dish_norm in user_norm}')
