#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script debug để kiểm tra lỗi limit khi sử dụng chatbot
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_models_initialization():
    """Test việc khởi tạo models giống như trong app"""
    print("🔄 Testing models initialization...")
    
    try:
        from models.ai_models import ai_models
        from config.settings import settings
        
        print(f"✅ API Key từ settings: {settings.GOOGLE_API_KEY[:10]}...{settings.GOOGLE_API_KEY[-4:]}")
        print(f"✅ Chat Model: {settings.CHAT_MODEL}")
        print(f"✅ Model Provider: {settings.MODEL_PROVIDER}")
        
        # Khởi tạo models
        success = ai_models.initialize_models()
        
        if success:
            print("✅ Models initialized successfully")
            return True
        else:
            print("❌ Failed to initialize models")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing models: {e}")
        return False

def test_single_chat_request():
    """Test một request chat đơn giản như trên UI"""
    print("\n🔄 Testing single chat request...")
    
    try:
        from models.ai_models import ai_models
        
        if not ai_models.is_initialized():
            print("❌ Models not initialized")
            return False
        
        # Test với prompt đơn giản
        llm = ai_models.get_llm()
        test_message = "Xin chào, tôi muốn tìm hiểu về phở"
        
        print(f"Sending message: {test_message}")
        
        response = llm.invoke(test_message)
        print(f"✅ Response received: {str(response)[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error in chat request: {e}")
        # In chi tiết lỗi
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

def test_chatbot_initialization():
    """Test việc khởi tạo chatbot hoàn chỉnh"""
    print("\n🔄 Testing chatbot initialization...")
    
    try:
        from core.chatbot import vietnamese_food_chatbot
        from utils.database_loader import load_dishes_from_database
        
        # Load dishes như trong app
        dishes = load_dishes_from_database()
        print(f"✅ Loaded {len(dishes)} dishes from database")
        
        # Initialize chatbot
        vietnamese_food_chatbot.initialize(dishes)
        print("✅ Chatbot initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

def test_full_chat_flow():
    """Test flow chat hoàn chỉnh như trên UI"""
    print("\n🔄 Testing full chat flow...")
    
    try:
        from core.chatbot import vietnamese_food_chatbot
        
        if not vietnamese_food_chatbot.is_ready:
            print("❌ Chatbot not ready")
            return False
        
        # Test với các message khác nhau
        test_messages = [
            "Xin chào",
            "Tôi muốn ăn phở",
            "Món gì ngon nhất?",
            "Cảm ơn"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Test message {i}/4: {message} ---")
            try:
                response = vietnamese_food_chatbot.chat(message, user_id="test_user")
                print(f"✅ Response {i}: {response[:100]}...")
            except Exception as e:
                print(f"❌ Error in message {i}: {e}")
                # Check if it's a rate limit error
                if "limit" in str(e).lower() or "quota" in str(e).lower() or "429" in str(e):
                    print("🚨 RATE LIMIT DETECTED!")
                    return False
                import traceback
                print(f"Full error: {traceback.format_exc()}")
                return False
        
        print("\n✅ All chat messages processed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in full chat flow: {e}")
        return False

def compare_api_usage():
    """So sánh cách gọi API giữa script test và chatbot"""
    print("\n🔄 Comparing API usage...")
    
    print("1. Script test sử dụng:")
    print("   - Direct requests.post()")
    print("   - X-goog-api-key header")
    print("   - gemini-2.0-flash model")
    print("   - Simple text prompt")
    
    print("\n2. Chatbot sử dụng:")
    print("   - LangChain init_chat_model()")
    print("   - GOOGLE_API_KEY env var")
    print("   - gemini-2.0-flash model")
    print("   - Complex prompt với context")
    
    print("\n🔍 Possible issues:")
    print("   - LangChain có thể có rate limiting khác")
    print("   - Complex prompts có thể dài hơn → nhiều tokens")
    print("   - Multiple parallel calls từ UI")
    print("   - Context và RAG system tạo prompts lớn")

def main():
    """Hàm chính để debug"""
    print("🐛 DEBUG: Chatbot Limit Issue")
    print("=" * 50)
    
    # Test từng bước
    step1 = test_models_initialization()
    if not step1:
        print("\n❌ Stop: Models initialization failed")
        return
    
    step2 = test_single_chat_request()
    if not step2:
        print("\n❌ Stop: Single chat request failed")
        return
    
    step3 = test_chatbot_initialization()
    if not step3:
        print("\n❌ Stop: Chatbot initialization failed")
        return
    
    step4 = test_full_chat_flow()
    if not step4:
        print("\n❌ Stop: Full chat flow failed")
        return
    
    # So sánh cách sử dụng API
    compare_api_usage()
    
    print("\n✅ All tests passed - API should work fine")
    print("\n💡 Suggestions:")
    print("1. Check if UI is making multiple parallel requests")
    print("2. Check if prompts are too long (token limit)")
    print("3. Add delay between requests in UI")
    print("4. Check browser network tab for actual error messages")

if __name__ == "__main__":
    main()