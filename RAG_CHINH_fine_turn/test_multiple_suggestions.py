#!/usr/bin/env python3
"""
Test chatbot response for multiple dish suggestions
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_chatbot_suggestions():
    print("=== TEST CHATBOT MULTIPLE DISH SUGGESTIONS ===")
    
    try:
        # Import
        from core.chatbot import vietnamese_food_chatbot
        from utils.excel_loader import load_dishes_from_excel
        from models.ai_models import ai_models
        
        print("Loading dishes from Excel...")
        dishes = load_dishes_from_excel("data100mon.xlsx")
        print(f"Loaded {len(dishes)} dishes")
        
        # Check if AI models are already initialized
        if not ai_models.is_initialized():
            print("Initializing AI models...")
            # Try to initialize without error handling
            try:
                ai_models.initialize()
                print("AI models initialized")
            except Exception as e:
                print(f"Warning: Could not initialize AI models: {e}")
                print("Continuing with existing setup...")
        else:
            print("AI models already initialized")
        
        print("Initializing chatbot...")
        success = vietnamese_food_chatbot.initialize(dishes)
        if not success:
            print("❌ Failed to initialize chatbot")
            return
        print("✅ Chatbot initialized successfully")
        
        # Test query
        test_query = "Gợi ý món ngon hôm nay"
        print(f"\nTesting query: '{test_query}'")
        
        response = vietnamese_food_chatbot.chat(test_query, user_id="test_user")
        print(f"\nResponse length: {len(response)} characters")
        print(f"Response:\n{response}")
        
        # Count dishes in response
        dish_count = response.count("VNĐ/")
        print(f"\nNumber of dishes found in response: {dish_count}")
        
        if dish_count >= 3:
            print("✅ Test PASSED - Multiple dishes suggested")
        else:
            print("❌ Test FAILED - Too few dishes suggested")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_chatbot_suggestions()
