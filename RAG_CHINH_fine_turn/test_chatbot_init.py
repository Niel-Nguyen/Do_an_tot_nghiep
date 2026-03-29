#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

# Import các module cần thiết
from core.chatbot import VietnameseFoodChatbot
from models.ai_models import ai_models
from utils.excel_loader import load_dishes_from_excel

def test_chatbot_with_proper_init():
    """Test chatbot với khởi tạo đúng cách"""
    
    print("🚀 Testing Chatbot with Proper Initialization")
    print("=" * 50)
    
    try:
        # 1. Khởi tạo AI models
        print("1️⃣ Initializing AI models...")
        if not ai_models.is_initialized():
            ai_models.initialize_models()
        print("✅ AI models initialized")
        
        # 2. Load data món ăn
        print("2️⃣ Loading dishes data...")
        data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
        if not os.path.exists(data_path):
            print(f"❌ Data file not found: {data_path}")
            return
        
        dishes = load_dishes_from_excel(data_path)
        print(f"✅ Loaded {len(dishes)} dishes")
        
        # 3. Khởi tạo chatbot
        print("3️⃣ Initializing chatbot...")
        chatbot = VietnameseFoodChatbot()
        success = chatbot.initialize(dishes)
        
        if not success:
            print("❌ Failed to initialize chatbot")
            return
        
        print(f"✅ Chatbot initialized successfully")
        print(f"   - Ready status: {chatbot.is_ready}")
        print(f"   - Available dishes: {len(chatbot.conversation_history) if hasattr(chatbot, 'conversation_history') else 'N/A'}")
        
        # 4. Test gợi ý món
        print("\n4️⃣ Testing dish suggestions...")
        
        test_queries = [
            "gợi ý món ăn",
            "món ngon hôm nay", 
            "thực đơn đa dạng",
            "có món gì ngon"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: '{query}' ---")
            response = chatbot.chat(query, user_id="test_user")
            
            print(f"Response length: {len(response)}")
            print(f"First 200 chars: {response[:200]}")
            
            if len(response) > 200:
                print(f"Last 200 chars: {response[-200:]}")
            
            # Kiểm tra xem có parse được món không
            if hasattr(chatbot, 'last_suggested_dishes'):
                print(f"Suggested dishes: {chatbot.last_suggested_dishes}")
            
            print("=" * 30)
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot_with_proper_init()
