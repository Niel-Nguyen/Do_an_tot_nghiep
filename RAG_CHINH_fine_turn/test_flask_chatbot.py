#!/usr/bin/env python3
"""
Simple test for chatbot response length in Flask environment
"""

import sys
import os
import requests
import json

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_flask_chatbot():
    print("=== TEST FLASK CHATBOT MULTIPLE SUGGESTIONS ===")
    
    # Test via Flask API
    api_url = "http://localhost:5000/api/chat"
    
    test_queries = [
        "Gợi ý món ngon hôm nay",
        "Món gì ngon nhất ở nhà hàng",
        "Tư vấn món ăn cho tôi",
        "Có món nào đặc biệt không"
    ]
    
    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        
        try:
            payload = {
                'message': query,
                'table_id': 'test_table'
            }
            
            response = requests.post(api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get('response', '')
                
                print(f"Response length: {len(bot_response)} characters")
                
                # Count number of dishes suggested
                dish_count = bot_response.count('VNĐ/')
                price_mentions = bot_response.count('VNĐ')
                
                print(f"Number of price mentions (dishes): {price_mentions}")
                print(f"Response preview: {bot_response[:200]}...")
                
                if price_mentions >= 3:
                    print("✅ Multiple dishes suggested")
                else:
                    print("❌ Only few dishes suggested")
                    print(f"Full response: {bot_response}")
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == '__main__':
    test_flask_chatbot()
