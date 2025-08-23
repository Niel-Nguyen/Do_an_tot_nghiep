#!/usr/bin/env python3
"""
Test dish status management in Flask environment
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_flask_dish_status():
    print("=== TEST FLASK DISH STATUS MANAGEMENT ===")
    
    try:
        # Import app module
        import app
        print(f"✅ App module imported successfully")
        print(f"Initial dish_status_map: {app.dish_status_map}")
        
        # Test setting dish status
        test_dish = "Mực ống hấp củ đậu"
        app.dish_status_map[test_dish] = False
        print(f"Set {test_dish} = False")
        print(f"Current dish_status_map: {app.dish_status_map}")
        
        # Test chatbot import
        from core.chatbot import get_dish_status_map
        retrieved_map = get_dish_status_map()
        print(f"Retrieved via get_dish_status_map(): {retrieved_map}")
        
        # Test chatbot availability check
        from core.chatbot import vietnamese_food_chatbot
        if hasattr(vietnamese_food_chatbot, '_is_dish_available'):
            result = vietnamese_food_chatbot._is_dish_available(test_dish)
            print(f"Chatbot _is_dish_available('{test_dish}'): {result}")
        else:
            print("❌ _is_dish_available method not found")
            
        # Test if they're the same object
        print(f"Same object? {app.dish_status_map is retrieved_map}")
        print(f"Equal values? {app.dish_status_map == retrieved_map}")
        
        if app.dish_status_map == retrieved_map:
            print("✅ Test PASSED - dish_status_map is properly shared")
        else:
            print("❌ Test FAILED - dish_status_map not properly shared")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_flask_dish_status()
