#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

def test_revenue_api():
    """Test revenue API endpoints"""
    base_url = "http://localhost:5000"
    
    # Login first to get session
    login_data = {'username': 'admin', 'password': 'admin123'}
    session = requests.Session()
    
    print("🔐 Logging in...")
    login_response = session.post(f"{base_url}/admin/login", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    print("✅ Login successful!")
    
    # Test revenue summary
    print("\n📊 Testing /api/revenue/summary...")
    summary_response = session.get(f"{base_url}/api/revenue/summary")
    if summary_response.status_code == 200:
        summary_data = summary_response.json()
        print(f"  Today Revenue: {summary_data.get('today_revenue', 0):,}đ")
        print(f"  Month Revenue: {summary_data.get('month_revenue', 0):,}đ")
        print(f"  Total Revenue: {summary_data.get('total_revenue', 0):,}đ")
    else:
        print(f"❌ Summary API failed: {summary_response.status_code}")
    
    # Test daily revenue for today
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"\n📅 Testing /api/revenue/daily for {today}...")
    daily_response = session.get(f"{base_url}/api/revenue/daily?date={today}")
    if daily_response.status_code == 200:
        daily_data = daily_response.json()
        print(f"  Daily Revenue: {daily_data.get('total_revenue', 0):,}đ")
        print(f"  Orders Count: {daily_data.get('orders_count', 0)}")
        print(f"  Orders Details: {len(daily_data.get('orders', []))} orders")
        
        for order in daily_data.get('orders', [])[:3]:  # Show first 3 orders
            print(f"    📋 Order {order['order_id']}: {order['total_amount']:,}đ, Items: {len(order['items'])}")
    else:
        print(f"❌ Daily API failed: {daily_response.status_code}")
        print(f"Error: {daily_response.text}")

if __name__ == "__main__":
    test_revenue_api()
