#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time

def test_simple_table_close():
    """Test đơn giản tính năng auto close"""
    base_url = "http://localhost:5000"
    
    # Login admin
    login_data = {'username': 'admin', 'password': 'admin123'}
    session = requests.Session()
    
    print("🔐 Logging in...")
    login_response = session.post(f"{base_url}/admin/login", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed")
        return
    
    print("✅ Login successful!")
    
    # Lấy danh sách tables để tìm table ID thực
    print("\n📋 Getting tables list...")
    tables_response = session.get(f"{base_url}/api/tables")
    if tables_response.status_code != 200:
        print("❌ Failed to get tables")
        return
    
    tables = tables_response.json()
    print(f"Tables data type: {type(tables)}")
    print(f"Tables data: {tables}")
    
    if not tables:
        print("❌ No tables found")
        return
    
    # Xử lý tables có thể là dict hoặc list
    if isinstance(tables, dict):
        if 'tables' in tables:
            table_list = tables['tables']
        else:
            table_list = list(tables.values())
    else:
        table_list = tables
    
    if not table_list:
        print("❌ No tables in list")
        return
    
    # Lấy table đầu tiên
    table = table_list[0]
    table_id = table['id']
    table_name = table['name']
    
    print(f"✅ Found table: {table_name} (ID: {table_id[:8]}...)")
    
    # Tạo session cho bàn
    print(f"\n🔓 Creating session for {table_name}...")
    session_response = session.post(f"{base_url}/api/tables/{table_id}/session", 
                                  json={'customer_count': 2},
                                  headers={'Content-Type': 'application/json'})
    
    if session_response.status_code == 200:
        session_data = session_response.json()
        token = session_data.get('token')
        
        print(f"✅ Session created!")
        print(f"🔑 Token: {token[:8]}...")
        print(f"📱 Test URL: {base_url}/mobile_menu?table_token={token}")
        
        # Test API status
        print("\n🔍 Testing status API...")
        status_response = requests.get(f"{base_url}/api/table/status/{token}")
        print(f"Status check: {status_response.status_code}")
        if status_response.status_code == 200:
            print(f"Status data: {status_response.json()}")
        
        print("\n💡 Now:")
        print("1. Open the mobile URL in a browser")
        print("2. Press Enter here to close the table")
        print("3. Watch the browser redirect automatically")
        
        input("\nPress Enter to close table...")
        
        # Đóng bàn
        print("\n🔒 Closing table...")
        close_response = session.delete(f"{base_url}/api/tables/{table_id}/session")
        
        if close_response.status_code == 200:
            print("✅ Table closed!")
            
            # Test status sau khi đóng
            print("\n🔍 Testing status after close...")
            status_response = requests.get(f"{base_url}/api/table/status/{token}")
            print(f"Status check: {status_response.status_code}")
            if status_response.status_code == 404:
                print("✅ Token invalidated - users will be redirected!")
            else:
                print(f"Status data: {status_response.json()}")
        else:
            print(f"❌ Failed to close: {close_response.status_code}")
    
    else:
        print(f"❌ Failed to create session: {session_response.status_code}")
        print(f"Error response: {session_response.text}")
        try:
            error_data = session_response.json()
            print(f"Error details: {error_data}")
        except:
            pass

if __name__ == "__main__":
    test_simple_table_close()
