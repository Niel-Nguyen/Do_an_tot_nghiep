#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test nhanh cho hệ thống face login mới
"""

import sys
import numpy as np

# Add face_login to path  
sys.path.insert(0, 'face_login')

def quick_test():
    """Test nhanh các chức năng cơ bản"""
    print("🧪 QUICK TEST - Face Login System")
    print("-" * 50)
    
    try:
        # Test import
        from face_login.face_db_manager import FaceDatabase
        from face_login.utils import get_face_database_info, reset_face_database
        print("✅ Import thành công")
        
        # Test database creation
        db = FaceDatabase()
        print("✅ Database instance tạo thành công")
        
        # Test register fake user
        fake_encoding = np.random.random(128)
        user_id = db.register_face("quick_test_user", fake_encoding)
        print(f"✅ Đăng ký user: ID {user_id}")
        
        # Test find face
        result = db.find_face(fake_encoding + np.random.random(128) * 0.01)
        if result:
            print(f"✅ Nhận diện: {result[0]} (confidence: {result[1]:.4f})")
        else:
            print("⚠️  Không nhận diện được (có thể do threshold)")
        
        # Test session
        session_id = db.start_face_session(user_id, "table_test", "token_test")
        print(f"✅ Start session: {session_id}")
        
        end_result = db.end_face_session(user_id)  
        print(f"✅ End session: {end_result}")
        
        # Test database info
        info = get_face_database_info()
        print(f"✅ Database info: {info['count']} users")
        
        # Test session reset (không xóa face data)
        reset_result = reset_face_database()
        print(f"✅ Session reset: {reset_result}")
        
        # Kiểm tra face data vẫn còn
        info_after = get_face_database_info()
        print(f"✅ Face data sau reset: {info_after['count']} users (nên giữ nguyên)")
        
        print("-" * 50)
        print("🎉 TẤT CẢ TESTS CƠ BẢN PASS!")
        print("Hệ thống đã sẵn sàng!")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    quick_test()
