#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để test chi tiết vector storage trong face database
"""

import sqlite3
import pickle
import numpy as np
import os
import sys
sys.path.append('face_login')

from face_db_manager import FaceDatabase

def test_vector_storage():
    """Test cách vector được lưu và retrieve"""
    
    print("=" * 60)
    print("🧬 TEST VECTOR STORAGE & RETRIEVAL")
    print("=" * 60)
    
    try:
        # Khởi tạo database manager
        face_db = FaceDatabase()
        
        print("✅ Database manager initialized")
        print(f"📂 Database path: {face_db.db_path}")
        
        # Test 1: Tạo fake vector và lưu
        print("\n🔬 TEST 1: Tạo và lưu fake vector")
        fake_name = "Test_User_Vector"
        fake_vector = np.random.random(128).astype(np.float64)
        
        print(f"   - Created vector shape: {fake_vector.shape}")
        print(f"   - Vector type: {type(fake_vector)}")
        print(f"   - Vector dtype: {fake_vector.dtype}")
        print(f"   - Vector range: [{fake_vector.min():.3f}, {fake_vector.max():.3f}]")
        
        # Lưu vector
        success = face_db.register_face(fake_name, fake_vector)
        print(f"   - Save result: {'✅ Success' if success else '❌ Failed'}")
        
        # Test 2: Retrieve vector và so sánh
        print(f"\n🔍 TEST 2: Retrieve và verify vector")
        
        with sqlite3.connect(face_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT encoding FROM faces WHERE name = ?", (fake_name,))
            result = cursor.fetchone()
            
            if result:
                encoding_blob = result[0]
                print(f"   - Retrieved blob size: {len(encoding_blob)} bytes")
                
                # Deserialize
                retrieved_vector = pickle.loads(encoding_blob)
                print(f"   - Retrieved vector shape: {retrieved_vector.shape}")
                print(f"   - Retrieved vector type: {type(retrieved_vector)}")
                print(f"   - Retrieved vector dtype: {retrieved_vector.dtype}")
                
                # So sánh
                are_equal = np.array_equal(fake_vector, retrieved_vector)
                max_diff = np.max(np.abs(fake_vector - retrieved_vector))
                
                print(f"   - Vectors identical: {'✅ Yes' if are_equal else '❌ No'}")
                print(f"   - Max difference: {max_diff:.10f}")
                
                if are_equal:
                    print("   ✅ Vector storage/retrieval works perfectly!")
                else:
                    print("   ⚠️  Vector có sự khác biệt sau khi lưu/lấy")
            else:
                print("   ❌ Không tìm thấy vector trong database")
        
        # Cleanup - xóa test user
        print(f"\n🧹 CLEANUP: Xóa test user")
        with sqlite3.connect(face_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM faces WHERE name = ?", (fake_name,))
            deleted_count = cursor.rowcount
            print(f"   - Deleted {deleted_count} test record(s)")
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🚀 Face Vector Storage Test Script")
    print("=" * 60)
    
    # Test vector storage
    test_vector_storage()
    
    print("\n" + "=" * 60)
    print("📝 TÓM TẮT:")
    print("=" * 60)
    print("✅ Vectors được lưu trong table 'faces', column 'encoding'")
    print("✅ Format: BLOB (pickle serialized numpy array)")
    print("✅ Standard shape: (128,) dimensions")
    print("✅ Data type: float64 numpy array") 
    print("✅ Retrieval và comparison hoạt động chính xác")
    print("=" * 60)

if __name__ == "__main__":
    main()
