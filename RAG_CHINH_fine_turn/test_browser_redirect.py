#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import webbrowser
import threading
from flask import Flask
import requests
import subprocess
import sys

def test_real_time_redirect():
    """Test thực tế việc redirect tự động"""
    
    print("🚀 Testing Real-time Table Closure with Browser")
    print("=" * 50)
    
    # 1. Check if Flask is running
    print("1️⃣ Checking Flask app...")
    try:
        response = requests.get('http://localhost:5000/api/tables', timeout=3)
        if response.status_code == 200:
            print("✅ Flask app is already running!")
        else:
            print("❌ Flask app not responding properly")
            return
    except Exception as e:
        print(f"❌ Flask app not running. Please start it manually: {e}")
        print("💡 Run: python app.py")
        return
    
    try:
        # 2. Create table session
        print("\n2️⃣ Creating table session...")
        
        # Đầu tiên lấy table ID
        response = requests.get('http://localhost:5000/api/tables')
        print(f"Tables API response: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Failed to get tables: {response.text}")
            return
            
        tables_data = response.json()
        print(f"Tables response: {list(tables_data.keys())}")
        
        # Truy cập đúng key 'tables'
        tables = tables_data.get('tables', [])
        print(f"Tables found: {len(tables)}")
        
        if not tables:
            print("❌ No tables found")
            return
            
        table_id = tables[0]['id']
        table_name = tables[0]['name']
        print(f"✅ Found table: {table_name} (ID: {table_id[:8]}...)")
        
        # Tạo session
        session_url = f'http://localhost:5000/api/tables/{table_id}/session'
        print(f"Creating session at: {session_url}")
        
        # Gửi data JSON như API yêu cầu
        session_data = {'customer_count': 2}
        response = requests.post(session_url, json=session_data)
        
        print(f"Session API response: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Failed to create session: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        session_result = response.json()
        print(f"Session result: {session_result}")
        token = session_result['session']['token']
        
        print(f"✅ Session created!")
        print(f"🔑 Token: {token[:8]}...")
        
        # 3. Open browser
        test_url = f"http://localhost:5000/mobile_menu?table_token={token}"
        print(f"📱 Opening browser: {test_url}")
        
        # Mở trong browser mới
        webbrowser.open_new_tab(test_url)
        
        # 4. Wait for user to see the page
        print("\n3️⃣ Browser opened!")
        print("👀 Please check the browser window is loaded")
        print("🔍 Open Developer Tools (F12) to see console logs")
        
        input("\n⏳ Press Enter when you see the page loaded and want to test closure...")
        
        # 5. Close table
        print("\n4️⃣ Closing table...")
        
        close_url = f'http://localhost:5000/api/tables/{table_id}/session'
        response = requests.delete(close_url)
        
        if response.status_code == 200:
            print("✅ Table closed!")
            print("👀 Watch the browser - it should redirect automatically within 2-6 seconds")
            print("🔍 Check browser console for monitoring logs")
        else:
            print(f"❌ Failed to close table: {response.status_code}")
            print(response.text)
        
        # 6. Verify token is invalid
        print("\n5️⃣ Verifying token invalidation...")
        
        status_response = requests.get(f'http://localhost:5000/api/table/status/{token}')
        
        if status_response.status_code == 404:
            print("✅ Token invalidated - redirect should happen!")
        else:
            print(f"⚠️ Token still valid: {status_response.status_code}")
            if status_response.status_code == 200:
                print(f"Status: {status_response.json()}")
        
        print("\n6️⃣ Test completed!")
        print("🔍 Check if browser redirected to /table_closed")
        
        input("\nPress Enter to finish test...")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    print("✅ Test completed!")

if __name__ == "__main__":
    test_real_time_redirect()
