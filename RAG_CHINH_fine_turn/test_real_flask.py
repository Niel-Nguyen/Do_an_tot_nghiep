#!/usr/bin/env python3
"""
Test dish status in real Flask app context
"""

import requests
import json
import time

def test_real_flask_environment():
    print("=== TEST DISH STATUS IN REAL FLASK ENVIRONMENT ===")
    
    base_url = "http://localhost:5000"
    
    try:
        # Test 1: Check if Flask app is running
        print("1. Testing Flask app connectivity...")
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            print(f"✅ Flask app is running (status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ Flask app not running: {e}")
            print("Please start the Flask app first with: python app.py")
            return
        
        # Test 2: Login as admin (assuming basic auth)
        print("\n2. Testing admin login...")
        session = requests.Session()
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        response = session.post(f"{base_url}/admin/login", data=login_data)
        if response.status_code == 200 or "admin" in response.text.lower():
            print("✅ Admin login successful")
        else:
            print(f"❌ Admin login failed (status: {response.status_code})")
            # Try to continue anyway
        
        # Test 3: Set dish status via API
        print("\n3. Testing dish status API...")
        test_dish = "Mực ống hấp củ đậu"
        
        # Disable the dish
        dish_data = {
            'name': test_dish,
            'status': False
        }
        response = session.post(
            f"{base_url}/api/admin/dish_status",
            json=dish_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully disabled {test_dish}")
        else:
            print(f"❌ Failed to disable dish (status: {response.status_code})")
            print(f"Response: {response.text}")
        
        # Test 4: Try to order the disabled dish via chat
        print("\n4. Testing chatbot order blocking...")
        chat_data = {
            'message': f'tôi muốn order {test_dish}',
            'table_id': 'test_table'
        }
        
        response = session.post(
            f"{base_url}/api/chat",
            json=chat_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            bot_response = response.json().get('response', '')
            print(f"Bot response: {bot_response[:200]}...")
            
            # Check if the response indicates the dish is unavailable
            unavailable_keywords = ['tạm hết', 'không có', 'hết', 'không thể order']
            if any(keyword in bot_response.lower() for keyword in unavailable_keywords):
                print("✅ Chatbot correctly blocked order for disabled dish")
            else:
                print("❌ Chatbot still allowed order for disabled dish")
                print(f"Full response: {bot_response}")
        else:
            print(f"❌ Chat API failed (status: {response.status_code})")
            print(f"Response: {response.text}")
        
        # Test 5: Re-enable the dish
        print("\n5. Re-enabling dish...")
        dish_data['status'] = True
        response = session.post(
            f"{base_url}/api/admin/dish_status",
            json=dish_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully re-enabled {test_dish}")
        else:
            print(f"❌ Failed to re-enable dish")
        
        # Test 6: Try to order again (should work now)
        print("\n6. Testing order after re-enabling...")
        response = session.post(
            f"{base_url}/api/chat",
            json=chat_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            bot_response = response.json().get('response', '')
            success_keywords = ['đã thêm', 'added', 'order thành công']
            if any(keyword in bot_response.lower() for keyword in success_keywords):
                print("✅ Chatbot correctly allowed order for enabled dish")
            else:
                print("❓ Chatbot response unclear")
                print(f"Response: {bot_response}")
        
        print("\n=== TEST COMPLETED ===")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_real_flask_environment()
