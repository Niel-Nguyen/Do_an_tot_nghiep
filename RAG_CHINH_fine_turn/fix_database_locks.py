#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Database Lock Issues
Giải quyết vấn đề database bị khóa
"""

import sqlite3
import os
import time
import sys
from datetime import datetime

def check_database_locks():
    """Kiểm tra và giải quyết database locks"""
    print("🔍 CHECKING DATABASE LOCKS")
    print("=" * 30)
    
    db_path = "face_login/face_database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        # Kiểm tra xem database có thể mở được không
        print(f"📁 Database path: {db_path}")
        print(f"📏 Database size: {os.path.getsize(db_path):,} bytes")
        
        # Test connection với timeout ngắn
        conn = sqlite3.connect(db_path, timeout=1.0)
        cursor = conn.cursor()
        
        # Test read operation
        cursor.execute("SELECT COUNT(*) FROM faces")
        face_count = cursor.fetchone()[0]
        print(f"✅ Database accessible - {face_count} faces found")
        
        # Check for locks
        cursor.execute("PRAGMA locking_mode")
        lock_mode = cursor.fetchone()[0]
        print(f"🔒 Lock mode: {lock_mode}")
        
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        print(f"📝 Journal mode: {journal_mode}")
        
        conn.close()
        print("✅ Database connection test passed")
        return True
        
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print("🔒 DATABASE IS LOCKED!")
            print("Trying to resolve...")
            return fix_database_lock(db_path)
        else:
            print(f"❌ Database error: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def fix_database_lock(db_path):
    """Cố gắng sửa database lock"""
    print("\n🔧 ATTEMPTING TO FIX DATABASE LOCK")
    print("-" * 40)
    
    try:
        # Method 1: Force close connections
        print("1. Force closing any open connections...")
        
        # Method 2: Check for WAL and SHM files
        wal_file = db_path + "-wal"
        shm_file = db_path + "-shm"
        
        if os.path.exists(wal_file):
            print(f"📄 Found WAL file: {wal_file}")
            try:
                os.remove(wal_file)
                print("✅ Removed WAL file")
            except Exception as e:
                print(f"⚠️  Could not remove WAL file: {e}")
        
        if os.path.exists(shm_file):
            print(f"📄 Found SHM file: {shm_file}")
            try:
                os.remove(shm_file)
                print("✅ Removed SHM file")
            except Exception as e:
                print(f"⚠️  Could not remove SHM file: {e}")
        
        # Method 3: Try connecting with longer timeout
        print("2. Attempting connection with extended timeout...")
        time.sleep(1)  # Wait a bit
        
        conn = sqlite3.connect(db_path, timeout=10.0)
        
        # Try to run VACUUM to fix any corruption
        print("3. Running database maintenance...")
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        print(f"🔍 Integrity check: {integrity}")
        
        if integrity == "ok":
            # Run vacuum to optimize
            cursor.execute("VACUUM")
            print("🧹 Database vacuumed")
            
            # Reset journal mode if needed
            cursor.execute("PRAGMA journal_mode=DELETE")
            cursor.execute("PRAGMA journal_mode=WAL")
            print("📝 Journal mode reset")
        
        conn.close()
        print("✅ Database lock resolved!")
        return True
        
    except Exception as e:
        print(f"❌ Could not fix database lock: {e}")
        return False

def safe_delete_face_by_id(face_id, max_retries=3):
    """Safely delete face with retry logic"""
    print(f"\n🗑️  SAFELY DELETING FACE ID: {face_id}")
    print("-" * 35)
    
    db_path = "face_login/face_database.db"
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}...")
            
            # Use longer timeout and WAL mode
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=memory")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            cursor = conn.cursor()
            
            # Check if face exists first
            cursor.execute('SELECT name FROM faces WHERE id = ?', (face_id,))
            face_row = cursor.fetchone()
            
            if not face_row:
                print(f"❌ Face ID {face_id} not found")
                conn.close()
                return False
            
            name = face_row[0]
            print(f"Found face: {name}")
            
            # Begin transaction
            cursor.execute("BEGIN IMMEDIATE")
            
            # Delete in correct order (foreign key constraints)
            cursor.execute('DELETE FROM login_history WHERE face_id = ?', (face_id,))
            deleted_history = cursor.rowcount
            print(f"Deleted {deleted_history} login history records")
            
            cursor.execute('DELETE FROM face_sessions WHERE face_id = ?', (face_id,))
            deleted_sessions = cursor.rowcount
            print(f"Deleted {deleted_sessions} session records")
            
            cursor.execute('DELETE FROM faces WHERE id = ?', (face_id,))
            deleted_face = cursor.rowcount
            print(f"Deleted {deleted_face} face record")
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            if deleted_face > 0:
                print(f"✅ Successfully deleted face ID {face_id} ('{name}')")
                return True
            else:
                print(f"❌ No face was deleted")
                return False
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"⏳ Database locked, waiting... (attempt {attempt + 1})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                print(f"❌ Database error: {e}")
                break
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            break
    
    print(f"❌ Failed to delete face ID {face_id} after {max_retries} attempts")
    return False

def safe_delete_face_by_name(name, max_retries=3):
    """Safely delete face by name with retry logic"""
    print(f"\n🗑️  SAFELY DELETING FACE: {name}")
    print("-" * 30)
    
    db_path = "face_login/face_database.db"
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}...")
            
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            
            cursor = conn.cursor()
            
            # Get face ID first
            cursor.execute('SELECT id FROM faces WHERE name = ?', (name,))
            face_row = cursor.fetchone()
            
            if not face_row:
                print(f"❌ Face '{name}' not found")
                conn.close()
                return False
            
            face_id = face_row[0]
            print(f"Found face ID: {face_id}")
            
            # Begin transaction
            cursor.execute("BEGIN IMMEDIATE")
            
            # Delete in order
            cursor.execute('DELETE FROM login_history WHERE face_id = ?', (face_id,))
            deleted_history = cursor.rowcount
            
            cursor.execute('DELETE FROM face_sessions WHERE face_id = ?', (face_id,))
            deleted_sessions = cursor.rowcount
            
            cursor.execute('DELETE FROM faces WHERE id = ?', (face_id,))
            deleted_face = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_face > 0:
                print(f"✅ Successfully deleted '{name}':")
                print(f"  - Face record: {deleted_face}")
                print(f"  - Login history: {deleted_history}")
                print(f"  - Sessions: {deleted_sessions}")
                return True
            else:
                print(f"❌ No face was deleted")
                return False
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"⏳ Database locked, waiting... (attempt {attempt + 1})")
                time.sleep(2 ** attempt)
                continue
            else:
                print(f"❌ Database error: {e}")
                break
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            break
    
    return False

def list_faces_safe():
    """Safely list faces"""
    print("\n👥 FACE LIST")
    print("-" * 15)
    
    try:
        db_path = "face_login/face_database.db"
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, created_at, login_count, is_active 
            FROM faces 
            ORDER BY id
        ''')
        
        faces = cursor.fetchall()
        conn.close()
        
        if not faces:
            print("No faces found")
            return
        
        print(f"{'ID':<4} {'Name':<20} {'Created':<20} {'Logins':<8} {'Active'}")
        print("-" * 60)
        
        for face in faces:
            face_id, name, created_at, login_count, is_active = face
            status = "Yes" if is_active else "No"
            print(f"{face_id:<4} {name:<20} {created_at:<20} {login_count:<8} {status}")
        
        return faces
        
    except Exception as e:
        print(f"❌ Error listing faces: {e}")
        return []

def main():
    """Main program"""
    print("🔧 FACE DATABASE REPAIR TOOL")
    print("=" * 35)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for locks first
    if not check_database_locks():
        print("❌ Could not access database")
        return
    
    while True:
        print("\n" + "="*40)
        print("SAFE FACE MANAGEMENT MENU")
        print("="*40)
        print("1. 📋 List faces")
        print("2. 🗑️  Delete face by ID (safe)")
        print("3. 🗑️  Delete face by name (safe)")
        print("4. 🔧 Check/fix database locks")
        print("0. 🚪 Exit")
        
        choice = input("\nSelect option (0-4): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
            
        elif choice == "1":
            list_faces_safe()
            
        elif choice == "2":
            faces = list_faces_safe()
            if faces:
                try:
                    face_id = int(input("\nEnter face ID to delete: "))
                    confirm = input(f"⚠️  Delete face ID {face_id}? (y/N): ").lower()
                    if confirm == 'y':
                        safe_delete_face_by_id(face_id)
                except ValueError:
                    print("❌ Invalid ID")
            
        elif choice == "3":
            faces = list_faces_safe()
            if faces:
                name = input("\nEnter face name to delete: ").strip()
                if name:
                    confirm = input(f"⚠️  Delete face '{name}'? (y/N): ").lower()
                    if confirm == 'y':
                        safe_delete_face_by_name(name)
        
        elif choice == "4":
            check_database_locks()
            
        else:
            print("❌ Invalid option")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
