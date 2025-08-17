#!/usr/bin/env python3
"""
Script reset orders database
Xóa toàn bộ dữ liệu trong table orders và các table liên quan
"""

import sqlite3
import os
from datetime import datetime

def reset_orders_database():
    """Reset toàn bộ dữ liệu orders"""
    
    db_path = 'restaurant.db'
    
    if not os.path.exists(db_path):
        print("Không tìm thấy file database restaurant.db")
        return False
    
    # Kiểm tra xem có process nào đang dùng database không
    print("🔍 Kiểm tra database connection...")
    
    try:
        # Test connection đơn giản
        test_conn = sqlite3.connect(db_path, timeout=5.0)
        test_conn.execute("SELECT 1")
        test_conn.close()
        print("✓ Database có thể truy cập")
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print("❌ Database đang bị lock!")
            print("💡 Hướng dẫn fix:")
            print("1. Tắt tất cả ứng dụng đang chạy (Flask app, DB browser, etc.)")
            print("2. Đợi 10-15 giây")
            print("3. Chạy lại script này")
            print("4. Nếu vẫn lỗi, restart máy tính")
            return False
        else:
            print(f"❌ Lỗi database: {e}")
            return False
    
    try:
        # Backup database trước khi reset
        backup_path = f"restaurant_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Copy database để backup
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"✓ Đã backup database thành: {backup_path}")
        
        # Kết nối với timeout và các pragma để tránh lock
        with sqlite3.connect(db_path, timeout=30.0) as conn:
            # Set các pragma để tối ưu hóa và tránh lock
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL") 
            conn.execute("PRAGMA temp_store = memory")
            conn.execute("PRAGMA mmap_size = 268435456")  # 256MB
            
            cursor = conn.cursor()
            
            # Kiểm tra số lượng records trước khi xóa
            cursor.execute("SELECT COUNT(*) FROM orders")
            orders_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM order_items")
            items_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM revenue_summary")
            revenue_count = cursor.fetchone()[0]
            
            print(f"\nDữ liệu hiện tại:")
            print(f"- Orders: {orders_count} records")
            print(f"- Order Items: {items_count} records")
            print(f"- Revenue Summary: {revenue_count} records")
            
            if orders_count == 0 and items_count == 0 and revenue_count == 0:
                print("\nDatabase đã trống rồi!")
                return True
            
            # Xác nhận reset
            print(f"\n⚠️  CẢNH BÁO: Bạn sắp xóa toàn bộ dữ liệu orders!")
            confirm = input("Nhập 'RESET' để xác nhận xóa toàn bộ dữ liệu: ")
            
            if confirm != 'RESET':
                print("Reset đã bị hủy")
                return False
            
            # Thực hiện reset
            print("\n🔄 Đang reset database...")
            
            # Begin transaction
            cursor.execute("BEGIN IMMEDIATE")
            
            try:
                # Tắt foreign key constraints tạm thời
                cursor.execute("PRAGMA foreign_keys = OFF")
                
                # Xóa dữ liệu từ các table theo thứ tự
                cursor.execute("DELETE FROM order_items")
                print("✓ Đã xóa order_items")
                
                cursor.execute("DELETE FROM orders") 
                print("✓ Đã xóa orders")
                
                cursor.execute("DELETE FROM revenue_summary")
                print("✓ Đã xóa revenue_summary")
                
                # Reset auto increment counters
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('orders', 'order_items', 'revenue_summary')")
                print("✓ Đã reset auto increment")
                
                # Bật lại foreign key constraints
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Commit transaction
                cursor.execute("COMMIT")
                
                # Vacuum để optimize database
                print("🔧 Đang optimize database...")
                cursor.execute("VACUUM")
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
            
            # Kiểm tra lại
            cursor.execute("SELECT COUNT(*) FROM orders")
            final_orders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM order_items")
            final_items = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM revenue_summary")
            final_revenue = cursor.fetchone()[0]
            
            print(f"\n✅ RESET HOÀN THÀNH!")
            print(f"- Orders: {final_orders} records")
            print(f"- Order Items: {final_items} records") 
            print(f"- Revenue Summary: {final_revenue} records")
            
            return True
            
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"❌ Database vẫn bị lock: {e}")
            print("\n🔧 Thử các cách fix sau:")
            print("1. Tắt hoàn toàn Flask app (Ctrl+C nhiều lần)")
            print("2. Tắt DB Browser hoặc SQLite tools khác") 
            print("3. Đợi 30 giây rồi thử lại")
            print("4. Restart terminal/command prompt")
            print("5. Restart máy tính")
        else:
            print(f"❌ Lỗi database: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi reset database: {e}")
        return False

def reset_tables_only():
    """Reset chỉ table tables (không động đến orders)"""
    
    db_path = 'restaurant.db'
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM tables")
            tables_count = cursor.fetchone()[0]
            
            print(f"Tables hiện tại: {tables_count} records")
            
            if tables_count == 0:
                print("Table tables đã trống!")
                return True
            
            confirm = input(f"Xóa {tables_count} bàn? (y/N): ")
            if confirm.lower() != 'y':
                print("Hủy reset tables")
                return False
            
            cursor.execute("DELETE FROM tables")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'tables'")
            conn.commit()
            
            print("✅ Đã reset table tables")
            return True
            
    except Exception as e:
        print(f"❌ Lỗi reset tables: {e}")
        return False

if __name__ == "__main__":
    print("=== RESET DATABASE ORDERS ===")
    print("1. Reset toàn bộ orders (orders + order_items + revenue_summary)")
    print("2. Reset chỉ tables")
    print("3. Hủy")
    
    choice = input("\nChọn option (1/2/3): ")
    
    if choice == "1":
        reset_orders_database()
    elif choice == "2":
        reset_tables_only()
    else:
        print("Đã hủy")
