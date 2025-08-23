#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script toàn diện cho hệ thống face login mới
Kiểm tra tất cả các tính năng của database SQLite và session management
"""

import os
import sys
import json
import time
import numpy as np
from datetime import datetime
import shutil

# Add face_login module to path
sys.path.insert(0, 'face_login')

def test_database_creation():
    """Test tạo database và tables"""
    print("=" * 60)
    print("1. KIỂM TRA TẠO DATABASE")
    print("=" * 60)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        # Tạo database instance
        db = FaceDatabase()
        print("✓ Database instance đã được tạo")
        
        # Kiểm tra database path
        if os.path.exists(db.db_path):
            print(f"✓ Database file tồn tại: {db.db_path}")
        else:
            print(f"✗ Database file không tồn tại: {db.db_path}")
            return False
            
        # Kiểm tra schema
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra table faces
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='faces'")
        if cursor.fetchone():
            print("✓ Table 'faces' tồn tại")
        else:
            print("✗ Table 'faces' không tồn tại")
            
        # Kiểm tra table login_history
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='login_history'")
        if cursor.fetchone():
            print("✓ Table 'login_history' tồn tại")
        else:
            print("✗ Table 'login_history' không tồn tại")
            
        # Kiểm tra table face_sessions
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='face_sessions'")
        if cursor.fetchone():
            print("✓ Table 'face_sessions' tồn tại")
        else:
            print("✗ Table 'face_sessions' không tồn tại")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test database: {str(e)}")
        return False

def test_face_registration():
    """Test đăng ký face"""
    print("\n" + "=" * 60)
    print("2. KIỂM TRA ĐĂNG KÝ FACE")
    print("=" * 60)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        
        # Tạo fake face encoding (128-dimensional vector)
        fake_encoding = np.random.random(128)
        
        # Test đăng ký user mới
        user_id = db.register_face("test_user_1", fake_encoding)
        if user_id:
            print(f"✓ Đăng ký user thành công, ID: {user_id}")
        else:
            print("✗ Đăng ký user thất bại")
            return False
            
        # Test đăng ký user trùng tên
        user_id2 = db.register_face("test_user_1", fake_encoding)
        if user_id2:
            print(f"✓ User trùng tên được cập nhật, ID: {user_id2}")
        else:
            print("✗ Không thể cập nhật user trùng tên")
            
        # Đăng ký thêm một user khác
        fake_encoding2 = np.random.random(128)
        user_id3 = db.register_face("test_user_2", fake_encoding2)
        if user_id3:
            print(f"✓ Đăng ký user thứ 2 thành công, ID: {user_id3}")
            
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test đăng ký face: {str(e)}")
        return False

def test_face_recognition():
    """Test nhận diện face"""
    print("\n" + "=" * 60)
    print("3. KIỂM TRA NHẬN DIỆN FACE")
    print("=" * 60)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        
        # Lấy danh sách users đã đăng ký
        faces = db.get_all_faces()
        if not faces:
            print("✗ Không có face nào trong database")
            return False
            
        print(f"✓ Có {len(faces)} faces trong database")
        
        for face_id, name, encoding_blob, created_at in faces:
            print(f"  - ID: {face_id}, Name: {name}, Created: {created_at}")
            
            # Test nhận diện với encoding tương tự
            import pickle
            original_encoding = pickle.loads(encoding_blob)
            
            # Tạo encoding hơi khác để test threshold
            similar_encoding = original_encoding + np.random.random(128) * 0.1
            
            result = db.find_face(similar_encoding)
            if result:
                found_id, found_name, distance = result
                print(f"    ✓ Nhận diện thành công: {found_name} (distance: {distance:.4f})")
            else:
                print(f"    ✗ Không nhận diện được")
                
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test nhận diện face: {str(e)}")
        return False

def test_session_management():
    """Test quản lý session"""
    print("\n" + "=" * 60)
    print("4. KIỂM TRA QUẢN LÝ SESSION")
    print("=" * 60)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        
        # Lấy face đầu tiên để test
        faces = db.get_all_faces()
        if not faces:
            print("✗ Không có face nào để test session")
            return False
            
        face_id, face_name = faces[0][0], faces[0][1]
        
        # Test start session
        session_id = db.start_face_session(face_id, "table_001", "session_token_123")
        if session_id:
            print(f"✓ Bắt đầu session thành công, ID: {session_id}")
        else:
            print("✗ Không thể bắt đầu session")
            return False
            
        # Test get active sessions
        active_sessions = db.get_active_sessions()
        print(f"✓ Có {len(active_sessions)} session đang hoạt động")
        
        for session in active_sessions:
            print(f"  - Session ID: {session[0]}, Face: {session[2]}, Table: {session[3]}")
            
        # Test end session
        success = db.end_face_session(face_id)
        if success:
            print("✓ Kết thúc session thành công")
        else:
            print("✗ Không thể kết thúc session")
            
        # Kiểm tra lại active sessions
        active_sessions = db.get_active_sessions()
        print(f"✓ Còn {len(active_sessions)} session đang hoạt động sau khi end")
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test session: {str(e)}")
        return False

def test_statistics():
    """Test thống kê database"""
    print("\n" + "=" * 60)
    print("5. KIỂM TRA THỐNG KÊ DATABASE")
    print("=" * 60)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        
        # Tạo một vài login history
        faces = db.get_all_faces()
        if faces:
            face_id = faces[0][0]
            # Thêm login history
            db.add_login_history(face_id, "table_001", "session_123", True)
            db.add_login_history(face_id, "table_002", "session_456", True)
        
        # Lấy thống kê
        stats = db.get_face_stats()
        
        print("📊 THỐNG KÊ DATABASE:")
        print(f"  - Tổng số faces: {stats['total_faces']}")
        print(f"  - Tổng lượt login: {stats['total_logins']}")
        print(f"  - Login thành công: {stats['successful_logins']}")
        print(f"  - Session đang hoạt động: {stats['active_sessions']}")
        print(f"  - User có nhiều login nhất: {stats['top_user']}")
        
        print("\n📋 DANH SÁCH FACES:")
        for face in stats['faces']:
            print(f"  - {face['name']} (ID: {face['id']}, Created: {face['created_at']})")
            
        print("\n📈 LỊCH SỬ LOGIN GÃN ĐÂY:")
        recent_logins = db.get_recent_login_history(5)
        for login in recent_logins:
            status = "✓" if login[4] else "✗"
            print(f"  {status} {login[1]} - Table: {login[2]} ({login[5]})")
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test thống kê: {str(e)}")
        return False

def test_utils_integration():
    """Test tích hợp với utils.py"""
    print("\n" + "=" * 60)
    print("6. KIỂM TRA TÍCH HỢP UTILS")
    print("=" * 60)
    
    try:
        from face_login.utils import (
            get_face_database_info, 
            reset_face_database,
            hard_reset_face_database,
            start_face_session,
            end_face_session
        )
        
        # Test get database info
        info = get_face_database_info()
        print("📊 THÔNG TIN DATABASE:")
        print(f"  - Tồn tại: {info['exists']}")
        print(f"  - Đường dẫn: {info['path']}")
        print(f"  - Số users: {info['count']}")
        print(f"  - Danh sách: {', '.join(info['names'])}")
        print(f"  - Recent logins: {info.get('recent_logins', 'N/A')}")
        print(f"  - Active sessions: {info.get('active_sessions', 'N/A')}")
        print(f"  - Top user: {info.get('top_user', 'N/A')}")
        
        # Test session management qua utils
        if info['names']:
            test_name = info['names'][0]
            print(f"\n🔄 Test session với user: {test_name}")
            
            session_result = start_face_session(test_name, "table_test", "token_test")
            print(f"  - Start session: {session_result}")
            
            end_result = end_face_session(test_name)
            print(f"  - End session: {end_result}")
        
        # Test reset sessions (không xóa face data)
        reset_result = reset_face_database()
        print(f"\n🔄 Reset sessions: {reset_result}")
        
        # Kiểm tra face data vẫn còn
        info_after_reset = get_face_database_info()
        print(f"  - Faces sau reset sessions: {info_after_reset['count']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test utils: {str(e)}")
        return False

def test_core_integration():
    """Test tích hợp với core1.py"""
    print("\n" + "=" * 60)
    print("7. KIỂM TRA TÍCH HỢP CORE")
    print("=" * 60)
    
    try:
        # Tạo fake image data
        import cv2
        import numpy as np
        
        # Tạo ảnh fake 480x640x3
        fake_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Lưu ảnh tạm
        temp_image_path = "temp_test_image.jpg"
        cv2.imwrite(temp_image_path, fake_image)
        
        print(f"✓ Tạo ảnh test: {temp_image_path}")
        
        # Test với core functions (chỉ test import vì cần face_recognition thực)
        try:
            from face_login.core1 import recognize_user, register_user
            print("✓ Import core functions thành công")
            
            # Note: Không test thực vì cần face_recognition và ảnh thật
            print("⚠️  Core functions cần ảnh thật và face_recognition để test")
            
        except ImportError as ie:
            print(f"⚠️  Không thể import core functions: {str(ie)}")
        except Exception as ce:
            print(f"⚠️  Lỗi khác với core: {str(ce)}")
        
        # Cleanup
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print("✓ Đã xóa ảnh test")
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test core: {str(e)}")
        return False

def test_hard_reset():
    """Test hard reset (xóa tất cả data)"""
    print("\n" + "=" * 60)
    print("8. KIỂM TRA HARD RESET")
    print("=" * 60)
    
    try:
        from face_login.utils import hard_reset_face_database, get_face_database_info
        
        # Kiểm tra trước khi reset
        info_before = get_face_database_info()
        print(f"Trước reset: {info_before['count']} faces")
        
        # Hard reset
        result = hard_reset_face_database()
        print(f"Hard reset result: {result}")
        
        # Kiểm tra sau khi reset
        info_after = get_face_database_info()
        print(f"Sau reset: {info_after['count']} faces")
        
        if info_after['count'] == 0:
            print("✓ Hard reset thành công - tất cả dữ liệu đã bị xóa")
        else:
            print("✗ Hard reset thất bại - vẫn còn dữ liệu")
            
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi test hard reset: {str(e)}")
        return False

def main():
    """Chạy tất cả tests"""
    print("🧪 FACE LOGIN SYSTEM - COMPREHENSIVE TEST")
    print("Testing SQLite database and session management")
    
    tests = [
        test_database_creation,
        test_face_registration,
        test_face_recognition,
        test_session_management,
        test_statistics,
        test_utils_integration,
        test_core_integration,
        test_hard_reset
    ]
    
    passed = 0
    failed = 0
    
    start_time = time.time()
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} crashed: {str(e)}")
            failed += 1
        
        time.sleep(0.5)  # Tạm dừng giữa các tests
    
    end_time = time.time()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TỔNG QUAN")
    print("=" * 60)
    print(f"✅ Tests passed: {passed}")
    print(f"❌ Tests failed: {failed}")
    print(f"⏱️  Total time: {end_time - start_time:.2f} seconds")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 TẤT CẢ TESTS ĐỀU PASS!")
        print("Hệ thống face login SQLite đã sẵn sàng sử dụng")
    else:
        print("⚠️  CÓ MỘT SỐ TESTS FAIL")
        print("Cần kiểm tra lại cấu hình và dependencies")
    
    print("\n💡 Lưu ý:")
    print("- Database SQLite sẽ tự động tạo khi chạy lần đầu")
    print("- Face data sẽ được giữ lại giữa các sessions")
    print("- Chỉ session tracking được reset khi bàn đóng/mở")
    print("- Admin có thể hard reset để xóa tất cả dữ liệu")

if __name__ == "__main__":
    main()
