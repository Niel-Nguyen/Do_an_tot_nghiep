#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để đồng bộ lại revenue_summary từ các đơn hàng đã paid
"""

import sqlite3
from datetime import datetime
import os

# Database path
DB_PATH = 'restaurant.db'

def sync_revenue_summary():
    """Đồng bộ lại revenue_summary từ orders table"""
    try:
        if not os.path.exists(DB_PATH):
            print("❌ Database file không tồn tại!")
            return False
            
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            print("🔄 Đang đồng bộ revenue_summary...")
            
            # Xóa dữ liệu cũ trong revenue_summary
            cursor.execute("DELETE FROM revenue_summary")
            print("✅ Đã xóa dữ liệu cũ trong revenue_summary")
            
            # Tính toán lại từ orders table
            cursor.execute('''
                SELECT 
                    DATE(payment_time) as payment_date,
                    SUM(total_amount) as total_revenue,
                    COUNT(*) as orders_count
                FROM orders 
                WHERE status = 'paid' AND payment_time IS NOT NULL
                GROUP BY DATE(payment_time)
                ORDER BY payment_date
            ''')
            
            revenue_data = cursor.fetchall()
            
            if not revenue_data:
                print("⚠️  Không có đơn hàng đã paid nào có payment_time")
                return True
            
            # Insert lại vào revenue_summary
            for payment_date, total_revenue, orders_count in revenue_data:
                cursor.execute('''
                    INSERT INTO revenue_summary (date, total_revenue, orders_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (payment_date, total_revenue, orders_count, datetime.now(), datetime.now()))
                
                print(f"📊 {payment_date}: {total_revenue:,.0f} VND ({orders_count} đơn)")
            
            conn.commit()
            print(f"✅ Đã đồng bộ {len(revenue_data)} bản ghi revenue_summary")
            
            return True
            
    except Exception as e:
        print(f"❌ Lỗi khi đồng bộ revenue_summary: {e}")
        return False

def check_data_status():
    """Kiểm tra trạng thái dữ liệu"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            print("\n📊 TRẠNG THÁI DỮ LIỆU:")
            print("=" * 50)
            
            # Kiểm tra orders
            cursor.execute("SELECT COUNT(*) FROM orders")
            total_orders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'")
            paid_orders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid' AND payment_time IS NOT NULL")
            paid_with_time = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(total_amount) FROM orders WHERE status = 'paid'")
            total_paid_amount = cursor.fetchone()[0] or 0
            
            print(f"📦 Tổng số orders: {total_orders}")
            print(f"💰 Orders đã paid: {paid_orders}")
            print(f"⏰ Orders đã paid có payment_time: {paid_with_time}")
            print(f"💵 Tổng tiền đã paid: {total_paid_amount:,.0f} VND")
            
            # Kiểm tra revenue_summary
            cursor.execute("SELECT COUNT(*) FROM revenue_summary")
            revenue_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(total_revenue) FROM revenue_summary")
            summary_total = cursor.fetchone()[0] or 0
            
            print(f"📈 Bản ghi revenue_summary: {revenue_records}")
            print(f"💰 Tổng trong revenue_summary: {summary_total:,.0f} VND")
            
            if total_paid_amount != summary_total:
                print("⚠️  DỮ LIỆU KHÔNG KHỚP! Cần đồng bộ lại.")
                return False
            else:
                print("✅ Dữ liệu khớp!")
                return True
                
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra dữ liệu: {e}")
        return False

def fix_payment_time():
    """Sửa payment_time cho các đơn hàng đã paid nhưng chưa có payment_time"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Tìm các đơn hàng paid nhưng chưa có payment_time
            cursor.execute('''
                SELECT id, created_at FROM orders 
                WHERE status = 'paid' AND payment_time IS NULL
            ''')
            
            orders_to_fix = cursor.fetchall()
            
            if not orders_to_fix:
                print("✅ Tất cả đơn hàng đã paid đều có payment_time")
                return True
            
            print(f"🔧 Sửa payment_time cho {len(orders_to_fix)} đơn hàng...")
            
            for order_id, created_at in orders_to_fix:
                # Sử dụng created_at làm payment_time
                cursor.execute('''
                    UPDATE orders 
                    SET payment_time = ?, updated_at = ?
                    WHERE id = ?
                ''', (created_at, datetime.now(), order_id))
                
                print(f"🔧 Đã sửa payment_time cho order {order_id}")
            
            conn.commit()
            print(f"✅ Đã sửa payment_time cho {len(orders_to_fix)} đơn hàng")
            return True
            
    except Exception as e:
        print(f"❌ Lỗi khi sửa payment_time: {e}")
        return False

def main():
    """Main function"""
    print("🏪 SCRIPT ĐỒNG BỘ REVENUE SUMMARY")
    print("=" * 50)
    
    if not os.path.exists(DB_PATH):
        print("❌ Database file không tồn tại!")
        return
    
    # Kiểm tra trạng thái hiện tại
    check_data_status()
    
    print("\n🔧 BƯỚC 1: Sửa payment_time")
    fix_payment_time()
    
    print("\n🔄 BƯỚC 2: Đồng bộ revenue_summary")
    sync_revenue_summary()
    
    print("\n📊 BƯỚC 3: Kiểm tra lại")
    check_data_status()
    
    print("\n✅ Hoàn thành!")

if __name__ == "__main__":
    main()
