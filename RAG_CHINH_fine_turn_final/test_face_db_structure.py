#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để kiểm tra cấu trúc database face_database.db
"""

import sqlite3
import pickle
import numpy as np
import os
from datetime import datetime

def check_database_structure():
    """Kiểm tra cấu trúc database và dữ liệu"""
    
    # Đường dẫn database
    db_path = os.path.join('face_login', 'face_database.db')
    
    print("=" * 60)
    print("🔍 KIỂM TRA CẤU TRÚC FACE DATABASE")
    print("=" * 60)
    
    print(f"📂 Database path: {db_path}")
    print(f"📁 File exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("❌ Database file không tồn tại!")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Liệt kê tất cả tables
            print("\n📋 DANH SÁCH TABLES:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for i, table in enumerate(tables, 1):
                print(f"{i}. {table[0]}")
            
            # 2. Kiểm tra structure từng table
            for table_name in [t[0] for t in tables]:
                print(f"\n🏗️  STRUCTURE TABLE '{table_name}':")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, primary_key = col
                    pk_marker = " 🔑 PRIMARY KEY" if primary_key else ""
                    null_marker = " NOT NULL" if not_null else ""
                    default_marker = f" DEFAULT {default_val}" if default_val else ""
                    
                    print(f"   - {col_name}: {col_type}{null_marker}{default_marker}{pk_marker}")
            
            # 3. Đếm records trong từng table
            print(f"\n📊 SỐ LƯỢNG RECORDS:")
            for table_name in [t[0] for t in tables]:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   - {table_name}: {count} records")
            
            # 4. Kiểm tra dữ liệu faces table (nơi lưu vector)
            print(f"\n🧬 CHI TIẾT FACES TABLE (NƠI LƯU VECTOR):")
            cursor.execute("SELECT id, name, created_at, login_count, is_active FROM faces ORDER BY id")
            faces = cursor.fetchall()
            
            if not faces:
                print("   ❌ Không có face nào trong database")
            else:
                for face in faces:
                    face_id, name, created_at, login_count, is_active = face
                    status = "✅ Active" if is_active else "❌ Inactive"
                    print(f"   - ID {face_id}: {name} | Created: {created_at} | Logins: {login_count} | {status}")
                
                # Lấy vector đầu tiên để kiểm tra
                print(f"\n🎯 KIỂM TRA VECTOR (ENCODING) ĐẦU TIÊN:")
                cursor.execute("SELECT id, name, encoding FROM faces LIMIT 1")
                first_face = cursor.fetchone()
                
                if first_face:
                    face_id, name, encoding_blob = first_face
                    
                    print(f"   - Face ID: {face_id}")
                    print(f"   - Name: {name}")
                    print(f"   - Encoding blob size: {len(encoding_blob)} bytes")
                    
                    try:
                        # Deserialize vector
                        encoding = pickle.loads(encoding_blob)
                        print(f"   - Vector shape: {encoding.shape}")
                        print(f"   - Vector type: {type(encoding)}")
                        print(f"   - Vector dtype: {encoding.dtype}")
                        print(f"   - Vector range: [{encoding.min():.3f}, {encoding.max():.3f}]")
                        print(f"   - Vector first 5 values: {encoding[:5]}")
                        
                        # Kiểm tra tính hợp lệ của vector
                        if encoding.shape == (128,):
                            print("   ✅ Vector có định dạng chuẩn face_recognition (128 dimensions)")
                        else:
                            print(f"   ⚠️  Vector không chuẩn! Expected (128,), got {encoding.shape}")
                            
                    except Exception as e:
                        print(f"   ❌ Lỗi khi deserialize vector: {e}")
            
            # 5. Kiểm tra face_sessions (session data)
            print(f"\n🎪 FACE SESSIONS (TEMPORARY DATA):")
            cursor.execute("SELECT COUNT(*) FROM face_sessions WHERE is_active = 1")
            active_sessions = cursor.fetchone()[0]
            print(f"   - Active sessions: {active_sessions}")
            
            cursor.execute("""
                SELECT fs.id, f.name, fs.table_id, fs.session_token, fs.started_at 
                FROM face_sessions fs 
                JOIN faces f ON fs.face_id = f.id 
                WHERE fs.is_active = 1
                ORDER BY fs.started_at DESC
                LIMIT 5
            """)
            sessions = cursor.fetchall()
            
            if sessions:
                for session in sessions:
                    sess_id, name, table_id, token, started_at = session
                    print(f"   - {name} @ Table {table_id} | Started: {started_at}")
            else:
                print("   - Không có active session nào")
            
            # 6. Thống kê login history
            print(f"\n📈 THỐNG KÊ LOGIN HISTORY:")
            cursor.execute("SELECT COUNT(*) FROM login_history")
            total_logins = cursor.fetchone()[0]
            print(f"   - Total logins: {total_logins}")
            
            cursor.execute("""
                SELECT f.name, COUNT(*) as login_count 
                FROM login_history lh 
                JOIN faces f ON lh.face_id = f.id 
                GROUP BY f.name 
                ORDER BY login_count DESC 
                LIMIT 5
            """)
            top_users = cursor.fetchall()
            
            if top_users:
                print("   - Top users:")
                for user, count in top_users:
                    print(f"     • {user}: {count} logins")
    
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main function"""
    try:
        check_database_structure()
        
        print("\n" + "=" * 60)
        print("📝 KẾT LUẬN:")
        print("=" * 60)
        print("• Vector (face encoding) được lưu trong TABLE 'faces'")
        print("• Cột 'encoding' chứa BLOB data (pickle serialized numpy array)")
        print("• Mỗi vector là numpy array 128 dimensions")
        print("• Faces table là PERSISTENT data (không reset)")
        print("• Face_sessions table là TEMPORARY data (reset khi bàn đóng)")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error in main: {e}")

if __name__ == "__main__":
    main()
