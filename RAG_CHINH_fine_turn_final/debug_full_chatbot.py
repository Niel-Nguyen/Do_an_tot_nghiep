#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Test chatbot với debug chi tiết
import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.chatbot import VietnameseFoodChatbot
from models.ai_models import ai_models
from core.rag_system import rag_system
from utils.excel_loader import load_dishes_from_excel

print("=== KHỞI TẠO CHATBOT ===")
chatbot = VietnameseFoodChatbot()

# Khởi tạo AI models và dữ liệu
print("Khởi tạo AI models...")
ai_models.initialize_models()

print("Load dữ liệu từ Excel...")
data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
dishes = load_dishes_from_excel(data_path)

print("Khởi tạo chatbot...")
chatbot.initialize(dishes)

print(f"✅ Chatbot ready: {chatbot.is_ready}")
print(f"✅ Số món trong lookup: {len(rag_system.dishes_lookup)}")

# Test trực tiếp
print("\n=== TEST TRỰC TIẾP ===")
query = "có món nào có gà không"
print(f"Query: {query}")

# Thêm debug vào hàm _extract_dish_name
import re

def debug_extract_dish_name(user_message: str) -> str:
    print(f"[DEBUG] _extract_dish_name input: '{user_message}'")
    
    # Kiểm tra skip patterns
    skip_patterns = [
        r'^\d+\s*(nguoi|person|people)$',
        r'^(xin\s*chao|chao|hello|hi)$',
        r'.*(thuc\s*don|menu|goi\s*thuc\s*don|goi\s*y|recommendation|suggest).*',
        r'.*(gia\s+bao\s*nhieu|bao\s*nhieu\s+gia|gia\s*ca|price|cost|budget|nghin\s*dong|vnd|\d+k|\d+\s*nghin\s*dong).*',
        r'.*(cam\s*on|thank).*',
        r'^\d{8,11}$',
        r'^\d+$',
        r'.*(gi|sao|the\s*nao|how|what|why).*',
        r'^(mon\s*(man|chay|chinh|phu|ngon|moi)|dish|food)$',
        r'^(ok|co|khong|duoc|roi|vang|phai|dung|chuan|chinh\s*xac|uh|da|yeah|yes|no|nope)$',
        r'^\w{1,2}$',
    ]
    
    from utils.text_processor import normalize
    user_norm = normalize(user_message)
    print(f"[DEBUG] user_norm: '{user_norm}'")
    
    for i, pattern in enumerate(skip_patterns):
        if re.match(pattern, user_norm, re.IGNORECASE):
            print(f"[DEBUG] SKIPPED by pattern {i}: {pattern}")
            return ""
    
    print(f"[DEBUG] NOT SKIPPED, proceeding with extraction...")
    return ""  # Simplified for debug

# Test extract
result = debug_extract_dish_name("món nào có gà")

print("\n=== TEST CHATBOT RESPONSE ===")
response = chatbot.chat(query, "debug_user")
print(f"Response: {response}")
