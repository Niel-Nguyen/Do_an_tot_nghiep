#!/usr/bin/env python3
"""
Script migration: Chuyển dữ liệu từ revenue_data.json sang SQLite database
Chạy script này để migrate dữ liệu cũ
"""

import json
import os
from datetime import datetime
from core.database_manager import db_manager

def migrate_revenue_data():
    """Migration dữ liệu từ JSON sang SQLite"""
    
    # Đường dẫn file JSON
    json_file = 'revenue_data.json'
    
    if not os.path.exists(json_file):
        print("Không tìm thấy file revenue_data.json")
        return
    
    try:
        # Đọc dữ liệu từ JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"Tìm thấy {len(json_data)} ngày dữ liệu trong JSON")
        
        migrated_orders = 0
        
        # Migrate từng ngày
        for date_str, day_data in json_data.items():
            orders = day_data.get('orders', [])
            
            for order in orders:
                try:
                    # Chuẩn bị dữ liệu order cho SQLite
                    order_data = {
                        'order_id': order.get('order_id', f"migrated_{migrated_orders}"),
                        'user_id': order.get('user_id', 'unknown'),
                        'table_id': order.get('table_id', 'unknown'),
                        'total_amount': order.get('total_amount', 0),
                        'status': order.get('status', 'paid'),
                        'created_at': order.get('payment_time', datetime.now()),
                        'items': order.get('items', [])
                    }
                    
                    # Lưu vào SQLite
                    if db_manager.save_order(order_data):
                        # Cập nhật trạng thái paid
                        payment_time = datetime.fromisoformat(order.get('payment_time', datetime.now().isoformat()))
                        db_manager.update_order_status(order_data['order_id'], 'paid', payment_time)
                        migrated_orders += 1
                        print(f"✓ Migrated order {order_data['order_id']}")
                    
                except Exception as e:
                    print(f"✗ Lỗi migrate order {order.get('order_id', 'unknown')}: {e}")
        
        print(f"\n=== MIGRATION HOÀN THÀNH ===")
        print(f"Đã migrate {migrated_orders} đơn hàng từ JSON sang SQLite")
        
        # Backup file JSON cũ
        backup_file = f"revenue_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.rename(json_file, backup_file)
        print(f"File JSON cũ đã được backup thành: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"Lỗi migration: {e}")
        return False

if __name__ == "__main__":
    print("=== MIGRATION REVENUE DATA ===")
    print("Chuyển đổi dữ liệu từ revenue_data.json sang SQLite database")
    
    # Xác nhận từ user
    confirm = input("\nBạn có muốn tiếp tục migration? (y/N): ")
    if confirm.lower() != 'y':
        print("Migration đã bị hủy")
        exit()
    
    success = migrate_revenue_data()
    if success:
        print("\n✓ Migration thành công!")
        print("Hệ thống đã được chuyển đổi hoàn toàn sang SQLite")
    else:
        print("\n✗ Migration thất bại!")
