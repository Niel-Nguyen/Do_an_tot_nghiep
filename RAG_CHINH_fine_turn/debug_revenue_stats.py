#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime
import os

def debug_revenue_stats():
    """Debug revenue statistics calculation"""
    db_path = 'restaurant.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🔍 Debug Revenue Statistics")
            print("=" * 50)
            
            # Kiểm tra ngày hiện tại
            today = datetime.now().date()
            print(f"📅 Today: {today}")
            print(f"📅 Today string: {str(today)}")
            
            # Kiểm tra tháng hiện tại
            month = today.strftime('%Y-%m')
            print(f"📅 Current month: {month}")
            
            print("\n📊 Revenue Summary Table:")
            cursor.execute('SELECT * FROM revenue_summary ORDER BY date')
            rows = cursor.fetchall()
            
            if not rows:
                print("❌ No data in revenue_summary table!")
                return
            
            for row in rows:
                print(f"  📋 Date: {row[0]}, Revenue: {row[1]:,}đ, Orders: {row[2]}")
            
            print("\n🔍 Today's Revenue Query:")
            cursor.execute('SELECT total_revenue, orders_count FROM revenue_summary WHERE date = ?', (str(today),))
            today_data = cursor.fetchone()
            print(f"  Result: {today_data}")
            
            print("\n🔍 Month's Revenue Query:")
            cursor.execute('''
                SELECT SUM(total_revenue), SUM(orders_count) 
                FROM revenue_summary 
                WHERE date LIKE ?
            ''', (f"{month}%",))
            month_data = cursor.fetchone()
            print(f"  Result: {month_data}")
            
            print("\n🔍 Total Revenue Query:")
            cursor.execute('SELECT SUM(total_revenue), SUM(orders_count) FROM revenue_summary')
            total_data = cursor.fetchone()
            print(f"  Result: {total_data}")
            
            print("\n📋 Orders with payment_time:")
            cursor.execute('SELECT id, table_id, total_amount, status, payment_time FROM orders WHERE status = "paid"')
            paid_orders = cursor.fetchall()
            
            for order in paid_orders:
                print(f"  📋 Order {order[0]}: {order[2]:,}đ, Status: {order[3]}, Payment: {order[4]}")
                if order[4]:
                    payment_date = datetime.fromisoformat(order[4]).date()
                    print(f"    📅 Payment date: {payment_date}")
                    print(f"    🔄 Is today? {payment_date == today}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_revenue_stats()
