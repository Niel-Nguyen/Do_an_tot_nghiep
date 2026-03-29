#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

def test_order_history_api():
    """Test order history API với filter"""
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
    
    # Test 1: Tất cả đơn hàng
    print("\n📊 Test 1: Tất cả đơn hàng...")
    response = session.get(f"{base_url}/api/orders/history")
    if response.status_code == 200:
        orders = response.json()
        print(f"  ✅ Found {len(orders)} orders")
        for order in orders[:3]:  # Show first 3
            payment_time = datetime.fromisoformat(order['payment_time']).strftime('%d/%m/%Y %H:%M')
            print(f"    📋 {order['id'][:8]}... - {order['total_amount']:,}đ - {payment_time}")
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test 2: Filter theo ngày hôm nay
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"\n📅 Test 2: Filter theo ngày {today}...")
    response = session.get(f"{base_url}/api/orders/history?filter_type=date&date={today}")
    if response.status_code == 200:
        orders = response.json()
        print(f"  ✅ Found {len(orders)} orders for today")
        total_revenue = sum(order['total_amount'] for order in orders)
        print(f"  💰 Total revenue today: {total_revenue:,}đ")
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test 3: Filter theo tháng hiện tại
    current_month = datetime.now().strftime('%Y-%m')
    print(f"\n📅 Test 3: Filter theo tháng {current_month}...")
    response = session.get(f"{base_url}/api/orders/history?filter_type=month&month={current_month}")
    if response.status_code == 200:
        orders = response.json()
        print(f"  ✅ Found {len(orders)} orders for this month")
        total_revenue = sum(order['total_amount'] for order in orders)
        print(f"  💰 Total revenue this month: {total_revenue:,}đ")
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test 4: Filter theo khoảng thời gian
    from_date = "2025-08-01"
    to_date = "2025-08-31"
    print(f"\n📅 Test 4: Filter từ {from_date} đến {to_date}...")
    response = session.get(f"{base_url}/api/orders/history?filter_type=range&from_date={from_date}&to_date={to_date}")
    if response.status_code == 200:
        orders = response.json()
        print(f"  ✅ Found {len(orders)} orders in range")
        total_revenue = sum(order['total_amount'] for order in orders)
        print(f"  💰 Total revenue in range: {total_revenue:,}đ")
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test 5: Chi tiết đơn hàng
    if orders and len(orders) > 0:
        order_id = orders[0]['id']
        print(f"\n📋 Test 5: Chi tiết đơn hàng {order_id[:8]}...")
        response = session.get(f"{base_url}/api/orders/{order_id}/detail")
        if response.status_code == 200:
            order_detail = response.json()
            print(f"  ✅ Order details loaded")
            print(f"  🍽️ Items: {len(order_detail['items'])} dishes")
            for item in order_detail['items'][:3]:
                print(f"    - {item['dish_name']}: {item['quantity']}x {item['unit_price']:,}đ")
        else:
            print(f"  ❌ Failed: {response.status_code}")

if __name__ == "__main__":
    test_order_history_api()
