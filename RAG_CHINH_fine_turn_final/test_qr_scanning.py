#!/usr/bin/env python3
"""
Test script để kiểm tra chức năng quét QR code
"""

import json
from core.table_manager import table_manager

def test_qr_scanning():
    """Test chức năng quét QR code"""
    print("=== Test QR Code Scanning ===")
    
    # Test 1: QR code hợp lệ cho Bàn 1
    print("\n1. Test QR code hợp lệ cho Bàn 1:")
    qr_data_1 = {
        "table_id": "table_1",
        "table_name": "Bàn 1",
        "action": "scan_table"
    }
    
    result_1 = table_manager.scan_qr_code(json.dumps(qr_data_1))
    print(f"Input: {qr_data_1}")
    print(f"Result: {json.dumps(result_1, indent=2, ensure_ascii=False)}")
    
    # Test 2: QR code hợp lệ cho Bàn 2
    print("\n2. Test QR code hợp lệ cho Bàn 2:")
    qr_data_2 = {
        "table_id": "table_2",
        "table_name": "Bàn 2",
        "action": "scan_table"
    }
    
    result_2 = table_manager.scan_qr_code(json.dumps(qr_data_2))
    print(f"Input: {qr_data_2}")
    print(f"Result: {json.dumps(result_2, indent=2, ensure_ascii=False)}")
    
    # Test 3: QR code không hợp lệ (thiếu action)
    print("\n3. Test QR code không hợp lệ (thiếu action):")
    qr_data_3 = {
        "table_id": "table_1",
        "table_name": "Bàn 1"
    }
    
    result_3 = table_manager.scan_qr_code(json.dumps(qr_data_3))
    print(f"Input: {qr_data_3}")
    print(f"Result: {json.dumps(result_3, indent=2, ensure_ascii=False)}")
    
    # Test 4: QR code không hợp lệ (table_id không tồn tại)
    print("\n4. Test QR code không hợp lệ (table_id không tồn tại):")
    qr_data_4 = {
        "table_id": "table_999",
        "table_name": "Bàn không tồn tại",
        "action": "scan_table"
    }
    
    result_4 = table_manager.scan_qr_code(json.dumps(qr_data_4))
    print(f"Input: {qr_data_4}")
    print(f"Result: {json.dumps(result_4, indent=2, ensure_ascii=False)}")
    
    # Test 5: QR code không hợp lệ (JSON sai định dạng)
    print("\n5. Test QR code không hợp lệ (JSON sai định dạng):")
    result_5 = table_manager.scan_qr_code("invalid json data")
    print(f"Input: invalid json data")
    print(f"Result: {json.dumps(result_5, indent=2, ensure_ascii=False)}")
    
    # Test 6: Kiểm tra danh sách bàn hiện có
    print("\n6. Danh sách bàn hiện có:")
    tables = table_manager.get_all_tables()
    for table in tables:
        print(f"  - ID: {table.id}, Name: {table.name}, Status: {table.status}")
    
    print("\n=== Kết thúc test ===")

if __name__ == "__main__":
    test_qr_scanning()
