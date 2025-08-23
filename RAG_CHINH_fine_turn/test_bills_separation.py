#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_bills_separation():
    """Test việc tách đơn hàng đã thanh toán và chưa thanh toán"""
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
    
    # Test 1: Kiểm tra trang admin/bills
    print("\n📋 Testing admin/bills page...")
    response = session.get(f"{base_url}/admin/bills")
    if response.status_code == 200:
        content = response.text
        if "Đơn Hàng Đang Xử Lý" in content:
            print("  ✅ Found active orders statistics")
        if "Đơn Hàng Đã Hoàn Thành" in content:
            print("  ✅ Found completed orders statistics")
        if "Tất cả đơn hàng đã được thanh toán" in content:
            print("  ✅ Found no active orders message")
        elif "Bàn" in content:
            print("  ✅ Found active orders in tables")
        print("  ✅ Admin bills page loaded successfully")
    else:
        print(f"  ❌ Failed to load admin/bills: {response.status_code}")
    
    # Test 2: Kiểm tra API lịch sử
    print("\n📚 Testing order history API...")
    response = session.get(f"{base_url}/api/orders/history")
    if response.status_code == 200:
        orders = response.json()
        print(f"  ✅ Found {len(orders)} paid orders in history")
        
        if orders:
            total_revenue = sum(order['total_amount'] for order in orders)
            print(f"  💰 Total revenue in history: {total_revenue:,}đ")
            
            # Show sample order
            sample_order = orders[0]
            print(f"  📋 Sample order: {sample_order['id'][:8]}... - {sample_order['total_amount']:,}đ")
    else:
        print(f"  ❌ Failed to load order history: {response.status_code}")
    
    # Test 3: Kiểm tra API chi tiết đơn hàng
    if orders and len(orders) > 0:
        order_id = orders[0]['id']
        print(f"\n🔍 Testing order detail for {order_id[:8]}...")
        response = session.get(f"{base_url}/api/orders/{order_id}/detail")
        if response.status_code == 200:
            order_detail = response.json()
            print(f"  ✅ Order detail loaded")
            print(f"  🍽️ Items count: {len(order_detail.get('items', []))}")
            print(f"  💰 Total amount: {order_detail.get('total_amount', 0):,}đ")
        else:
            print(f"  ❌ Failed to load order detail: {response.status_code}")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_bills_separation()
