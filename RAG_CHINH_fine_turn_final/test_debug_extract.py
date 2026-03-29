#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import ensure_chatbot_ready, vietnamese_food_chatbot

print("=== KHỞI TẠO CHATBOT ===")
ensure_chatbot_ready()

print("\n=== TEST VỚI DEBUG CHI TIẾT ===")
result = vietnamese_food_chatbot._extract_dish_name('món nào có gà')
print(f'Result: "{result}"')

print("\n=== TEST CHATBOT RESPONSE ===")
response = vietnamese_food_chatbot.chat('có món nào có gà không', 'debug_user')
print(f'Response: {response}')
