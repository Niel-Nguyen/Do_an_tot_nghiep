#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.chatbot import VietnameseFoodChatbot
from models.ai_models import ai_models  
from utils.excel_loader import load_dishes_from_excel
from app import ensure_chatbot_ready, vietnamese_food_chatbot

print("=== KHỞI TẠO CHATBOT ===")
ensure_chatbot_ready()

print("\n=== DEBUG _extract_dish_name ===")
result1 = vietnamese_food_chatbot._extract_dish_name('món nào có gà')
print(f'_extract_dish_name("món nào có gà") = "{result1}"')

result2 = vietnamese_food_chatbot._extract_dish_name('món mực')  
print(f'_extract_dish_name("món mực") = "{result2}"')

result3 = vietnamese_food_chatbot._extract_dish_name('gà')
print(f'_extract_dish_name("gà") = "{result3}"')

result4 = vietnamese_food_chatbot._extract_dish_name('mực')
print(f'_extract_dish_name("mực") = "{result4}"')

print("\n=== TEST PATTERN MATCHING ===")
import re

user_message = "có món nào có gà không"
question_patterns = [
    r'có\s+(.+?)\s+(không|ko)\s*\?*$',
    r'(.+?)\s+có\s+(không|ko)\s*\?*$',
    r'nhà\s+hàng\s+có\s+(.+?)\s+(không|ko)\s*\?*$'
]

for i, pattern in enumerate(question_patterns):
    match = re.search(pattern, user_message.lower().strip())
    if match:
        potential_dish = match.group(1).strip()
        print(f"Pattern {i+1} matched: potential_dish = '{potential_dish}'")
        
        dish_name = vietnamese_food_chatbot._extract_dish_name(potential_dish)
        print(f"  -> _extract_dish_name('{potential_dish}') = '{dish_name}'")
        
        if dish_name:
            print(f"  -> Sẽ chạy logic TÌM THẤY MÓN: {dish_name}")
        else:
            print(f"  -> Sẽ chạy logic KHÔNG TÌM THẤY MÓN -> kiểm tra nguyên liệu")
        break

print("\n=== TEST CHATBOT RESPONSES ===")
print("1. Test 'có món nào có gà không':")
response1 = vietnamese_food_chatbot.chat('có món nào có gà không', 'test_user')
print(f"Response: {response1}\n")

print("2. Test 'có món mực không':")
response2 = vietnamese_food_chatbot.chat('có món mực không', 'test_user')
print(f"Response: {response2}\n")

print("3. Test 'có gà không':")
response3 = vietnamese_food_chatbot.chat('có gà không', 'test_user')
print(f"Response: {response3}\n")
