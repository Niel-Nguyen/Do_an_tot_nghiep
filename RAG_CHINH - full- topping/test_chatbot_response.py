#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.excel_loader import load_dishes_from_excel
from core.rag_system import rag_system
from models.ai_models import ai_models
from core.chatbot import VietnameseFoodChatbot

def test_chatbot_response():
    """Test chatbot response với hình ảnh"""
    print("=== Test Chatbot Response ===")
    
    try:
        # Load dishes từ Excel
        dishes = load_dishes_from_excel('data100mon.xlsx')
        print(f"✅ Loaded {len(dishes)} dishes")
        
        # Initialize AI models
        ai_models.initialize_models()
        print("✅ AI models initialized")
        
        # Initialize RAG system
        if rag_system.initialize(dishes):
            print("✅ RAG system initialized")
            
            # Initialize chatbot
            chatbot = VietnameseFoodChatbot()
            if chatbot.initialize(dishes):
                print("✅ Chatbot initialized")
                
                # Test với một món cụ thể
                test_messages = [
                    "Mực ống hấp củ đậu",
                    "gợi ý món ngon",
                    "tôi muốn ăn gà"
                ]
                
                for msg in test_messages:
                    print(f"\n--- Test message: '{msg}' ---")
                    response = chatbot.chat(msg)
                    print(f"Response length: {len(response)}")
                    print(f"Contains <img>: {'<img' in response}")
                    if '<img' in response:
                        # Đếm số lượng thẻ img
                        img_count = response.count('<img')
                        print(f"Number of <img> tags: {img_count}")
                        # Hiển thị 200 ký tự đầu
                        print(f"First 200 chars: {response[:200]}...")
                    else:
                        print(f"Full response: {response}")
                    print("-" * 50)
                
            else:
                print("❌ Chatbot initialization failed")
        else:
            print("❌ RAG system initialization failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot_response()
