#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from utils.excel_loader import load_dishes_from_excel
from core.chatbot import VietnameseFoodChatbot
from models.ai_models import ai_models

def test_full_chatbot_response():
    print("🔄 Initializing AI models...")
    try:
        ai_models.initialize_models()
        print("✅ AI models initialized")
    except Exception as e:
        print(f"❌ Error initializing AI models: {e}")
        return
    
    print("🔄 Loading dishes from Excel...")
    try:
        dishes = load_dishes_from_excel('data100mon.xlsx')
        print(f"✅ Loaded {len(dishes)} dishes")
        
        print("🔄 Initializing chatbot...")
        chatbot = VietnameseFoodChatbot()
        if not chatbot.initialize(dishes):
            print("❌ Failed to initialize chatbot")
            return
        print("✅ Chatbot initialized")
        
        print("\n🔄 Testing response...")
        response = chatbot.chat('gợi ý món ngon hôm nay', user_id="test_user")
        
        print("=== FULL RESPONSE DEBUG ===")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(response)}")
        print(f"Response repr: {repr(response[:300])}...")
        
        print("\n=== VISIBLE CONTENT ===")
        print(response)
        
        print("\n=== LOOKING FOR HTML/FORMATTING ===")
        if '<br>' in response:
            print("✅ Contains <br> tags")
        if '<img' in response:
            print("✅ Contains <img> tags")
        if '<strong>' in response:
            print("✅ Contains <strong> tags")
        if '🍜' in response:
            print("✅ Contains emoji")
            
        # Test second response để xem có khác biệt không
        print("\n🔄 Testing second response...")
        response2 = chatbot.chat('gợi ý món chua ngọt', user_id="test_user")
        print(f"Second response length: {len(response2)}")
        print("Second response preview:", response2[:200], "...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_chatbot_response()
