#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để clear các hóa đơn không thể thanh toán
"""

import sqlite3
from datetime import datetime

def check_unpayable_orders():
    """Kiểm tra các đơn hàng không thể thanh toán"""
    print("=" * 60)
    print("KIỂM TRA CÁC ĐƠN HÀNG KHÔNG THỂ THANH TOÁN")
    print("=" * 60)
    
    try:
        with sqlite3.connect('restaurant.db') as conn:
            cursor = conn.cursor()
            
            # Lấy tất cả đơn hàng chưa thanh toán
            cursor.execute("""
                SELECT o.id, o.table_id, t.name as table_name, o.total_amount, 
                       o.status, o.created_at, o.updated_at
                FROM orders o
                LEFT JOIN tables t ON o.table_id = t.id
                WHERE o.status NOT IN ('paid', 'cancelled')
                ORDER BY o.created_at DESC
            """)
            
            unpaid_orders = cursor.fetchall()
            
            print(f"📊 Tìm thấy {len(unpaid_orders)} đơn hàng chưa thanh toán:")
            
            for i, order in enumerate(unpaid_orders, 1):
                order_id = order[0]
                table_id = order[1] 
                table_name = order[2] or f"Bàn {table_id}"
                total_amount = order[3]
                status = order[4]
                created_at = order[5]
                
                print(f"\n  {i}. Order: {order_id}")
                print(f"     Bàn: {table_name}")
                print(f"     Trạng thái: {status}")
                print(f"     Tổng tiền: {total_amount:,.0f}₫")
                print(f"     Tạo lúc: {created_at}")
            
            return unpaid_orders
            
    except Exception as e:
        print(f"❌ Lỗi kiểm tra: {e}")
        return []

def clear_orders_by_status(status_list):
    """Xóa các đơn hàng theo trạng thái"""
    print(f"\n🗑️  XÓA CÁC ĐƠN HÀNG CÓ TRẠNG THÁI: {', '.join(status_list)}")
    print("=" * 60)
    
    try:
        with sqlite3.connect('restaurant.db') as conn:
            cursor = conn.cursor()
            
            # Tạo placeholder cho query
            placeholders = ','.join(['?' for _ in status_list])
            
            # Đếm số đơn hàng sẽ bị xóa
            cursor.execute(f"""
                SELECT COUNT(*) FROM orders 
                WHERE status IN ({placeholders})
            """, status_list)
            
            count_to_delete = cursor.fetchone()[0]
            
            if count_to_delete == 0:
                print("✅ Không có đơn hàng nào cần xóa")
                return
            
            print(f"⚠️  Sẽ xóa {count_to_delete} đơn hàng với trạng thái: {', '.join(status_list)}")
            
            # Xóa order_items trước
            cursor.execute(f"""
                DELETE FROM order_items 
                WHERE order_id IN (
                    SELECT id FROM orders WHERE status IN ({placeholders})
                )
            """, status_list)
            
            deleted_items = cursor.rowcount
            print(f"✅ Đã xóa {deleted_items} order_items")
            
            # Xóa orders
            cursor.execute(f"""
                DELETE FROM orders 
                WHERE status IN ({placeholders})
            """, status_list)
            
            deleted_orders = cursor.rowcount
            conn.commit()
            
            print(f"✅ Đã xóa {deleted_orders} đơn hàng")
            
    except Exception as e:
        print(f"❌ Lỗi xóa đơn hàng: {e}")

def clear_test_orders():
    """Xóa các đơn hàng test"""
    print(f"\n🧪 XÓA CÁC ĐƠN HÀNG TEST")
    print("=" * 60)
    
    try:
        with sqlite3.connect('restaurant.db') as conn:
            cursor = conn.cursor()
            
            # Xóa order_items test
            cursor.execute("""
                DELETE FROM order_items 
                WHERE order_id LIKE 'test_order_%' 
                   OR order_id LIKE 'real_order_%'
            """)
            
            deleted_items = cursor.rowcount
            
            # Xóa orders test
            cursor.execute("""
                DELETE FROM orders 
                WHERE id LIKE 'test_order_%' 
                   OR id LIKE 'real_order_%'
            """)
            
            deleted_orders = cursor.rowcount
            conn.commit()
            
            print(f"✅ Đã xóa {deleted_orders} đơn hàng test")
            print(f"✅ Đã xóa {deleted_items} order_items test")
            
    except Exception as e:
        print(f"❌ Lỗi xóa đơn hàng test: {e}")

def clear_orders_by_table_id(table_ids):
    """Xóa các đơn hàng theo table_id"""
    print(f"\n🏠 XÓA CÁC ĐƠN HÀNG THEO TABLE_ID")
    print("=" * 60)
    
    try:
        with sqlite3.connect('restaurant.db') as conn:
            cursor = conn.cursor()
            
            for table_id in table_ids:
                # Đếm số đơn hàng
                cursor.execute("SELECT COUNT(*) FROM orders WHERE table_id = ?", (table_id,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"  Bàn {table_id}: {count} đơn hàng")
                    
                    # Xóa order_items
                    cursor.execute("""
                        DELETE FROM order_items 
                        WHERE order_id IN (
                            SELECT id FROM orders WHERE table_id = ?
                        )
                    """, (table_id,))
                    
                    # Xóa orders
                    cursor.execute("DELETE FROM orders WHERE table_id = ?", (table_id,))
            
            conn.commit()
            print(f"✅ Hoàn thành xóa đơn hàng theo table_id")
            
    except Exception as e:
        print(f"❌ Lỗi xóa theo table_id: {e}")

def show_clean_summary():
    """Hiển thị tóm tắt sau khi dọn dẹp"""
    print(f"\n📊 TÓM TẮT SAU KHI DỌN DẸP")
    print("=" * 60)
    
    try:
        with sqlite3.connect('restaurant.db') as conn:
            cursor = conn.cursor()
            
            # Đếm đơn hàng theo trạng thái
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM orders 
                GROUP BY status
                ORDER BY status
            """)
            
            status_counts = cursor.fetchall()
            
            print("📋 Đơn hàng còn lại theo trạng thái:")
            total_orders = 0
            for status, count in status_counts:
                print(f"  - {status}: {count} đơn")
                total_orders += count
            
            print(f"\n📊 Tổng cộng: {total_orders} đơn hàng")
            
            # Kiểm tra đơn hàng chưa thanh toán
            cursor.execute("""
                SELECT COUNT(*) FROM orders 
                WHERE status NOT IN ('paid', 'cancelled')
            """)
            
            pending_count = cursor.fetchone()[0]
            print(f"⏳ Đơn hàng chưa thanh toán: {pending_count}")
            
            if pending_count == 0:
                print("✅ HOÀN THÀNH! Không còn đơn hàng nào cần xử lý")
            
    except Exception as e:
        print(f"❌ Lỗi hiển thị tóm tắt: {e}")

def main():
    """Chương trình chính"""
    print("🚀 BẮT ĐẦU DỌN DẸP ĐƠN HÀNG")
    
    # 1. Kiểm tra tình trạng hiện tại
    unpaid_orders = check_unpayable_orders()
    
    if not unpaid_orders:
        print("✅ Không có đơn hàng nào cần dọn dẹp!")
        return
    
    print(f"\n💡 CÁC TÙYCHỌN DỌN DẸP:")
    print("1. Xóa các đơn hàng test (test_order_, real_order_)")
    print("2. Xóa các đơn hàng trạng thái 'confirmed' (đã gửi bếp)")
    print("3. Xóa tất cả đơn hàng chưa thanh toán")
    print("4. Xóa đơn hàng theo table_id cụ thể")
    print("5. Thoát")
    
    choice = input("\nNhập lựa chọn (1-5): ").strip()
    
    if choice == "1":
        clear_test_orders()
    elif choice == "2":
        clear_orders_by_status(['confirmed'])
    elif choice == "3":
        statuses = ['confirmed', 'pending', 'sent_to_kitchen', 'completed']
        clear_orders_by_status(statuses)
    elif choice == "4":
        table_id = input("Nhập table_id cần xóa: ").strip()
        if table_id:
            clear_orders_by_table_id([table_id])
    elif choice == "5":
        print("👋 Thoát chương trình")
        return
    else:
        print("❌ Lựa chọn không hợp lệ")
        return
    
    # Hiển thị kết quả
    show_clean_summary()

if __name__ == "__main__":
    main()
