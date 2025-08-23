#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

def test_bill_separation():
    """Test việc tách đơn hàng đã paid khỏi admin/bills"""
    base_url = "http://localhost:5000"
    
    # Login first
    login_data = {'username': 'admin', 'password': 'admin123'}
    session = requests.Session()
    
    print("🔐 Logging in...")
    login_response = session.post(f"{base_url}/admin/login", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    print("✅ Login successful!")
    
    # Test 1: Kiểm tra số lượng đơn trong admin/bills
    print("\n📊 Test 1: Kiểm tra admin/bills...")
    response = session.get(f"{base_url}/admin/bills")
    if response.status_code == 200:
        # Parse HTML để đếm số đơn hàng hiển thị
        content = response.text
        if "Đơn hàng chưa thanh toán" in content:
            print("  ✅ Trang admin/bills đã được cập nhật với filter")
        else:
            print("  ⚠️ Trang admin/bills chưa có thông báo filter")
            
        # Đếm số dòng trong bảng đơn hàng
        table_rows = content.count('<tr data-order-id=')
        print(f"  📋 Số đơn hàng hiển thị trong admin/bills: {table_rows}")
    else:
        print(f"  ❌ Failed to load admin/bills: {response.status_code}")
    
    # Test 2: Kiểm tra lịch sử đơn hàng
    print("\n📋 Test 2: Kiểm tra lịch sử đơn hàng...")
    response = session.get(f"{base_url}/api/orders/history")
    if response.status_code == 200:
        orders = response.json()
        print(f"  ✅ Số đơn hàng trong lịch sử: {len(orders)}")
        
        if orders:
            total_revenue = sum(order['total_amount'] for order in orders)
            print(f"  💰 Tổng doanh thu trong lịch sử: {total_revenue:,}đ")
            
            # Hiển thị một vài đơn gần nhất
            for order in orders[:3]:
                payment_time = datetime.fromisoformat(order['payment_time']).strftime('%d/%m/%Y %H:%M')
                print(f"    📋 {order['id'][:8]}... - {order['total_amount']:,}đ - {payment_time}")
    else:
        print(f"  ❌ Failed to load order history: {response.status_code}")
    
    # Test 3: Kiểm tra database trực tiếp
    print("\n🗄️ Test 3: Kiểm tra database...")
    try:
        import sqlite3
        with sqlite3.connect('restaurant.db') as conn:
            cursor = conn.cursor()
            
            # Đếm đơn hàng theo status
            cursor.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
            status_counts = cursor.fetchall()
            
            print("  📊 Thống kê đơn hàng trong database:")
            for status, count in status_counts:
                print(f"    - {status}: {count} đơn")
                
            # Kiểm tra đơn hàng có payment_time
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid' AND payment_time IS NOT NULL")
            paid_with_time = cursor.fetchone()[0]
            print(f"  ⏰ Đơn hàng đã paid có payment_time: {paid_with_time}")
            
    except Exception as e:
        print(f"  ❌ Database error: {e}")
    
    print("\n✅ Test hoàn thành!")

if __name__ == "__main__":
    test_bill_separation()
