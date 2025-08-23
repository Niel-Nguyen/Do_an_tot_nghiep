#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def migrate_tables_schema():
    """Thêm các column mới cho table tables"""
    db_path = 'restaurant.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🔄 Migrating tables schema...")
            
            # Kiểm tra column is_closed
            cursor.execute("PRAGMA table_info(tables)")
            columns = [column[1] for column in cursor.fetchall()]
            
            print(f"Current columns: {columns}")
            
            # Thêm column is_closed nếu chưa có
            if 'is_closed' not in columns:
                print("➕ Adding is_closed column...")
                cursor.execute('ALTER TABLE tables ADD COLUMN is_closed BOOLEAN DEFAULT 0')
                print("✅ Added is_closed column")
            else:
                print("✅ is_closed column already exists")
            
            # Thêm column token nếu chưa có
            if 'token' not in columns:
                print("➕ Adding token column...")
                cursor.execute('ALTER TABLE tables ADD COLUMN token TEXT')
                print("✅ Added token column")
            else:
                print("✅ token column already exists")
            
            # Thêm column updated_at nếu chưa có
            if 'updated_at' not in columns:
                print("➕ Adding updated_at column...")
                cursor.execute('ALTER TABLE tables ADD COLUMN updated_at TIMESTAMP')
                print("✅ Added updated_at column")
            else:
                print("✅ updated_at column already exists")
            
            # Thêm column location nếu chưa có
            if 'location' not in columns:
                print("➕ Adding location column...")
                cursor.execute('ALTER TABLE tables ADD COLUMN location TEXT DEFAULT ""')
                print("✅ Added location column")
            else:
                print("✅ location column already exists")
            
            conn.commit()
            print("✅ Migration completed successfully!")
            
            # Hiển thị schema mới
            cursor.execute("PRAGMA table_info(tables)")
            new_columns = cursor.fetchall()
            print("\n📋 New table schema:")
            for col in new_columns:
                print(f"  - {col[1]} ({col[2]})")
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_tables_schema()
