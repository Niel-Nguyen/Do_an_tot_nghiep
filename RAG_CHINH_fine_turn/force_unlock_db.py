#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Force Database Unlock Tool
Công cụ force unlock database bằng cách xóa lock files
"""

import os
import sqlite3
import shutil
import time
from datetime import datetime

def force_unlock_database():
    """Force unlock database bằng cách xóa lock files"""
    print("💪 FORCE UNLOCK DATABASE")
    print("=" * 30)
    
    db_path = "face_login/face_database.db"
    journal_file = db_path + "-journal"
    wal_file = db_path + "-wal"
    shm_file = db_path + "-shm"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print(f"📁 Database: {db_path} ({os.path.getsize(db_path):,} bytes)")
    
    # Check and remove lock files
    removed_files = []
    
    if os.path.exists(journal_file):
        print(f"🔒 Found journal file: {journal_file}")
        try:
            os.remove(journal_file)
            removed_files.append("journal")
            print("✅ Removed journal file")
        except Exception as e:
            print(f"⚠️  Could not remove journal file: {e}")
    
    if os.path.exists(wal_file):
        print(f"🔒 Found WAL file: {wal_file}")
        try:
            os.remove(wal_file)
            removed_files.append("WAL")
            print("✅ Removed WAL file")
        except Exception as e:
            print(f"⚠️  Could not remove WAL file: {e}")
    
    if os.path.exists(shm_file):
        print(f"🔒 Found SHM file: {shm_file}")
        try:
            os.remove(shm_file)
            removed_files.append("SHM")
            print("✅ Removed SHM file")
        except Exception as e:
            print(f"⚠️  Could not remove SHM file: {e}")
    
    if not removed_files:
        print("ℹ️  No lock files found")
    else:
        print(f"🗑️  Removed lock files: {', '.join(removed_files)}")
    
    # Test database connection
    print("\n🔍 Testing database connection...")
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM faces")
        count = cursor.fetchone()[0]
        
        conn.close()
        print(f"✅ Database unlocked! Found {count} faces")
        return True
        
    except Exception as e:
        print(f"❌ Database still locked: {e}")
        return False

def backup_database():
    """Tạo backup database trước khi thao tác"""
    print("💾 CREATING DATABASE BACKUP")
    print("-" * 25)
    
    db_path = "face_login/face_database.db"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"face_login/face_database_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def direct_delete_face(face_id):
    """Direct delete face bypassing the class methods"""
    print(f"\n💥 DIRECT DELETE FACE ID: {face_id}")
    print("-" * 30)
    
    db_path = "face_login/face_database.db"
    
    try:
        # Force unlock first
        if not force_unlock_database():
            return False
        
        # Connect with aggressive settings
        conn = sqlite3.connect(db_path, timeout=60.0)
        
        # Set pragma for performance and safety
        conn.execute("PRAGMA journal_mode=DELETE")  # Simpler journal mode
        conn.execute("PRAGMA synchronous=OFF")      # Faster but less safe
        conn.execute("PRAGMA locking_mode=EXCLUSIVE") # Get exclusive lock
        conn.execute("PRAGMA temp_store=memory")
        
        cursor = conn.cursor()
        
        # Check if face exists
        cursor.execute("SELECT name FROM faces WHERE id = ?", (face_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Face ID {face_id} not found")
            conn.close()
            return False
        
        name = result[0]
        print(f"Found face: {name}")
        
        # Delete in transaction
        cursor.execute("BEGIN EXCLUSIVE")
        
        # Delete related records first
        cursor.execute("DELETE FROM login_history WHERE face_id = ?", (face_id,))
        deleted_history = cursor.rowcount
        print(f"Deleted {deleted_history} login history records")
        
        cursor.execute("DELETE FROM face_sessions WHERE face_id = ?", (face_id,))
        deleted_sessions = cursor.rowcount
        print(f"Deleted {deleted_sessions} session records")
        
        # Delete face record
        cursor.execute("DELETE FROM faces WHERE id = ?", (face_id,))
        deleted_faces = cursor.rowcount
        print(f"Deleted {deleted_faces} face record")
        
        # Commit and close
        conn.commit()
        conn.close()
        
        if deleted_faces > 0:
            print(f"✅ Successfully deleted face '{name}' (ID: {face_id})")
            return True
        else:
            print(f"❌ Failed to delete face")
            return False
        
    except Exception as e:
        print(f"❌ Direct delete failed: {e}")
        return False

def list_faces_simple():
    """Simple face listing"""
    print("\n👥 FACE LIST")
    print("-" * 15)
    
    db_path = "face_login/face_database.db"
    
    try:
        # Force unlock first
        force_unlock_database()
        
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, created_at FROM faces ORDER BY id")
        faces = cursor.fetchall()
        
        conn.close()
        
        if not faces:
            print("No faces found")
            return []
        
        print(f"{'ID':<4} {'Name':<20} {'Created'}")
        print("-" * 45)
        
        for face in faces:
            print(f"{face[0]:<4} {face[1]:<20} {face[2]}")
        
        return faces
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def rebuild_database():
    """Rebuild database from scratch to fix corruption"""
    print("🔨 REBUILD DATABASE")
    print("-" * 20)
    
    db_path = "face_login/face_database.db"
    temp_path = "face_login/face_database_temp.db"
    
    try:
        # Backup first
        backup_path = backup_database()
        if not backup_path:
            print("❌ Cannot proceed without backup")
            return False
        
        # Read all data from original database
        print("📖 Reading original data...")
        
        original_conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = original_conn.cursor()
        
        # Get all faces data
        cursor.execute("SELECT id, name, encoding, created_at, last_login, login_count, is_active FROM faces")
        faces_data = cursor.fetchall()
        print(f"Read {len(faces_data)} faces")
        
        # Get login history
        cursor.execute("SELECT * FROM login_history")
        history_data = cursor.fetchall()
        print(f"Read {len(history_data)} login history records")
        
        original_conn.close()
        
        # Create new database
        print("🏗️  Creating new database...")
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        new_conn = sqlite3.connect(temp_path)
        new_cursor = new_conn.cursor()
        
        # Create tables
        new_cursor.execute('''
            CREATE TABLE faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                encoding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        new_cursor.execute('''
            CREATE TABLE login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                face_id INTEGER NOT NULL,
                table_id TEXT,
                session_token TEXT,
                success INTEGER DEFAULT 1,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (face_id) REFERENCES faces (id)
            )
        ''')
        
        new_cursor.execute('''
            CREATE TABLE face_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                face_id INTEGER NOT NULL,
                table_id TEXT NOT NULL,
                session_token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (face_id) REFERENCES faces (id)
            )
        ''')
        
        # Insert data
        print("📝 Inserting data...")
        
        for face in faces_data:
            new_cursor.execute('''
                INSERT INTO faces (id, name, encoding, created_at, last_login, login_count, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', face)
        
        for history in history_data:
            new_cursor.execute('''
                INSERT INTO login_history VALUES (?, ?, ?, ?, ?, ?)
            ''', history)
        
        new_conn.commit()
        new_conn.close()
        
        # Replace original with new database
        print("🔄 Replacing database...")
        
        if os.path.exists(db_path):
            os.remove(db_path)
        
        os.rename(temp_path, db_path)
        
        print("✅ Database rebuilt successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Rebuild failed: {e}")
        return False

def main():
    """Main menu"""
    print("💪 FORCE DATABASE MANAGEMENT")
    print("=" * 35)
    
    while True:
        print("\n" + "="*40)
        print("FORCE DATABASE MANAGEMENT MENU")
        print("="*40)
        print("1. 🔓 Force unlock database")
        print("2. 👥 List faces (simple)")
        print("3. 💥 Direct delete face by ID")
        print("4. 💾 Backup database")
        print("5. 🔨 Rebuild database")
        print("0. 🚪 Exit")
        
        choice = input("\nSelect (0-5): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            force_unlock_database()
        elif choice == "2":
            list_faces_simple()
        elif choice == "3":
            faces = list_faces_simple()
            if faces:
                try:
                    face_id = int(input("\nEnter face ID to delete: "))
                    confirm = input(f"⚠️  FORCE DELETE face ID {face_id}? (y/N): ").lower()
                    if confirm == 'y':
                        direct_delete_face(face_id)
                except ValueError:
                    print("❌ Invalid ID")
        elif choice == "4":
            backup_database()
        elif choice == "5":
            confirm = input("⚠️  Rebuild database? This will recreate it. (y/N): ").lower()
            if confirm == 'y':
                rebuild_database()
        else:
            print("❌ Invalid option")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
