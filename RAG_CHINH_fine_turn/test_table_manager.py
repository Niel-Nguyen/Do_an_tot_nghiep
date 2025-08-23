#!/usr/bin/env python3
"""
Test script cho TableManager
"""

from core.table_manager import table_manager
from datetime import datetime

def test_table_manager():
    print("=== Test TableManager ===")
    
    try:
        # Test 1: Lấy danh sách bàn
        print("\n1. Lấy danh sách bàn:")
        tables = table_manager.get_all_tables()
        print(f"   Số lượng bàn: {len(tables)}")
        for table in tables[:3]:  # Chỉ hiển thị 3 bàn đầu
            print(f"   - {table.name} ({table.capacity} người) - {table.status}")
        
        # Test 2: Lấy tổng quan
        print("\n2. Tổng quan hệ thống:")
        summary = table_manager.get_table_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        # Test 3: Tạo bàn mới
        print("\n3. Tạo bàn mới:")
        new_table = table_manager.create_table("Bàn Test", 6, "Khu Test")
        print(f"   Đã tạo: {new_table.name} (ID: {new_table.id})")
        
        # Test 4: Bắt đầu phiên làm việc
        print("\n4. Bắt đầu phiên làm việc:")
        session = table_manager.start_table_session(new_table.id, 4)
        if session:
            print(f"   Phiên bắt đầu: {session.table_name} - {session.customer_count} khách")
        
        # Test 5: Cập nhật trạng thái
        print("\n5. Cập nhật trạng thái:")
        success = table_manager.update_table_status(new_table.id, "maintenance")
        print(f"   Cập nhật trạng thái: {'Thành công' if success else 'Thất bại'}")
        
        # Test 6: Kết thúc phiên
        print("\n6. Kết thúc phiên làm việc:")
        success = table_manager.end_table_session(new_table.id)
        print(f"   Kết thúc phiên: {'Thành công' if success else 'Thất bại'}")
        
        print("\n=== Test hoàn thành thành công! ===")
        
    except Exception as e:
        print(f"\n=== Lỗi: {e} ===")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_manager()
