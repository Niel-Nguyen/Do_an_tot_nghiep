#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Thêm path để import
sys.path.append(os.path.dirname(__file__))

from utils.excel_loader import load_dishes_from_excel
from core.chatbot import VietnameseFoodChatbot
from models.ai_models import ai_models

print("=== TEST CHATBOT VỚI CÂU HỎI VỀ MỰC ===")

# Khởi tạo AI models
print("Đang khởi tạo AI models...")
ai_models.initialize_models()

# Khởi tạo chatbot
print("Đang khởi tạo chatbot...")
chatbot = VietnameseFoodChatbot()
data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
dishes = load_dishes_from_excel(data_path)
chatbot.initialize(dishes)

print("✅ Chatbot đã sẵn sàng!")

# Test các câu hỏi về mực
test_queries = [
    "có món mực không?",
    "nhà hàng có món mực gì?", 
    "tôi muốn ăn mực",
    "cho tôi xem món mực",
    "menu có mực không?"
]

user_id = "test_user_real"

print("\n=== TEST CÁC CÂU HỎI VỀ MỰC ===")
for i, query in enumerate(test_queries, 1):
    print(f"\n--- Test {i}: '{query}' ---")
    try:
        response = chatbot.chat(query, user_id)
        print(f"Chatbot trả lời: {response}")
        
        # Kiểm tra có trả về thông tin mực không
        if "mực" in response.lower() or "muc" in response.lower():
            print("✅ Có nhắc đến mực")
        else:
            print("❌ KHÔNG nhắc đến mực - CÓ VẤN ĐỀ!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

print("\n=== HOÀN THÀNH TEST ===")
