#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để debug dish status management
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Test 1: Kiểm tra import dish_status_map
print("=== TEST 1: Import dish_status_map ===")
try:
    from app import dish_status_map
    print(f"✅ Import thành công: {dish_status_map}")
    print(f"Type: {type(dish_status_map)}")
    print(f"Length: {len(dish_status_map)}")
except Exception as e:
    print(f"❌ Import failed: {e}")

# Test 2: Tạo test data và test toggle
print("\n=== TEST 2: Test toggle functionality ===")
try:
    from app import dish_status_map
    
    # Thêm test data
    test_dish = "Mực ống hấp củ đậu"
    dish_status_map[test_dish] = True
    print(f"Đặt {test_dish} = True: {dish_status_map[test_dish]}")
    
    # Toggle
    dish_status_map[test_dish] = False
    print(f"Toggle {test_dish} = False: {dish_status_map[test_dish]}")
    
    print(f"dish_status_map hiện tại: {dish_status_map}")
    
except Exception as e:
    print(f"❌ Test toggle failed: {e}")

# Test 3: Test chatbot import
print("\n=== TEST 3: Test chatbot import ===")
try:
    from core.chatbot import VietnameseFoodChatbot
    chatbot = VietnameseFoodChatbot()
    
    # Test method _is_dish_available
    test_dish = "Mực ống hấp củ đậu"
    result = chatbot._is_dish_available(test_dish)
    print(f"_is_dish_available('{test_dish}'): {result}")
    
except Exception as e:
    print(f"❌ Chatbot test failed: {e}")

# Test 4: Test end-to-end
print("\n=== TEST 4: End-to-end test ===")
try:
    from app import dish_status_map
    from core.chatbot import VietnameseFoodChatbot
    
    # Disable dish
    test_dish = "Mực ống hấp củ đậu"
    dish_status_map[test_dish] = False
    print(f"Disabled {test_dish}: {dish_status_map[test_dish]}")
    
    # Test chatbot check
    chatbot = VietnameseFoodChatbot()
    result = chatbot._is_dish_available(test_dish)
    print(f"Chatbot check result: {result}")
    
    if result == False:
        print("✅ Test PASSED - Dish is correctly marked as unavailable")
    else:
        print("❌ Test FAILED - Dish should be unavailable but chatbot says it's available")
        
except Exception as e:
    print(f"❌ End-to-end test failed: {e}")

# Test 5: Test real order scenario
print("\n=== TEST 5: Test real order scenario ===")
try:
    from app import dish_status_map, app
    from core.chatbot import VietnameseFoodChatbot
    from utils.excel_loader import load_dishes_from_excel
    
    # Load dishes
    dishes = load_dishes_from_excel("data100mon.xlsx")
    
    # Initialize chatbot
    chatbot = VietnameseFoodChatbot()
    chatbot.initialize(dishes)
    
    # Disable test dish
    test_dish = "Mực ống hấp củ đậu"
    dish_status_map[test_dish] = False
    print(f"Disabled {test_dish}")
    
    # Test order
    response = chatbot.chat(f"cho tôi 1 {test_dish}", user_id="test_user")
    print(f"Chatbot response: {response}")
    
    if "tạm hết" in response or "không có" in response:
        print("✅ Test PASSED - Chatbot correctly refused the order")
    else:
        print("❌ Test FAILED - Chatbot accepted order for disabled dish")
        
except Exception as e:
    print(f"❌ Real order test failed: {e}")

print("\n=== TEST COMPLETED ===")
