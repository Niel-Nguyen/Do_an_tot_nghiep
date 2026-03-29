#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Face Data Management Tool
Công cụ quản lý dữ liệu khuôn mặt
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_menu():
    """Hiển thị menu chính"""
    print("\n" + "="*50)
    print("🎭 FACE DATA MANAGEMENT TOOL")
    print("="*50)
    print("1. 📋 Xem danh sách khuôn mặt")
    print("2. 🗑️  Xóa khuôn mặt theo tên")
    print("3. 🗑️  Xóa khuôn mặt theo ID")
    print("4. ❌ Vô hiệu hóa khuôn mặt (soft delete)")
    print("5. ✅ Kích hoạt lại khuôn mặt")
    print("6. 🧹 Xóa lịch sử login")
    print("7. 💥 XÓA TẤT CẢ (nguy hiểm!)")
    print("8. 📊 Xem thống kê database")
    print("0. 🚪 Thoát")
    print("-"*50)

def list_faces(db):
    """Hiển thị danh sách khuôn mặt"""
    print("\n👥 DANH SÁCH KHUÔN MẶT:")
    print("-" * 60)
    
    try:
        faces = db.get_all_faces()
        
        if not faces:
            print("  Không có khuôn mặt nào được đăng ký")
            return
        
        print(f"{'ID':<4} {'Tên':<20} {'Ngày tạo':<20} {'Đăng nhập':<10} {'Trạng thái':<10}")
        print("-" * 60)
        
        for face in faces:
            face_id = face[0]
            name = face[1] 
            created_at = face[3] if len(face) > 3 else "N/A"
            login_count = face[5] if len(face) > 5 else 0
            is_active = face[6] if len(face) > 6 else 1
            status = "Hoạt động" if is_active else "Vô hiệu"
            
            print(f"{face_id:<4} {name:<20} {created_at:<20} {login_count:<10} {status:<10}")
            
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách: {e}")

def delete_face_by_name(db):
    """Xóa khuôn mặt theo tên"""
    print("\n🗑️  XÓA KHUÔN MẶT THEO TÊN")
    print("-" * 30)
    
    # Hiển thị danh sách trước
    list_faces(db)
    
    name = input("\nNhập tên khuôn mặt muốn xóa: ").strip()
    if not name:
        print("❌ Tên không được rỗng")
        return
    
    confirm = input(f"⚠️  Bạn có chắc muốn xóa '{name}'? (y/N): ").strip().lower()
    if confirm != 'y':
        print("🚫 Đã hủy xóa")
        return
    
    success = db.delete_face_by_name(name)
    if success:
        print(f"✅ Đã xóa thành công '{name}'")
    else:
        print(f"❌ Không thể xóa '{name}'")

def delete_face_by_id(db):
    """Xóa khuôn mặt theo ID"""
    print("\n🗑️  XÓA KHUÔN MẶT THEO ID")
    print("-" * 30)
    
    # Hiển thị danh sách trước
    list_faces(db)
    
    try:
        face_id = int(input("\nNhập ID khuôn mặt muốn xóa: ").strip())
    except ValueError:
        print("❌ ID phải là số")
        return
    
    confirm = input(f"⚠️  Bạn có chắc muốn xóa ID {face_id}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("🚫 Đã hủy xóa")
        return
    
    success = db.delete_face_by_id(face_id)
    if success:
        print(f"✅ Đã xóa thành công ID {face_id}")
    else:
        print(f"❌ Không thể xóa ID {face_id}")

def deactivate_face(db):
    """Vô hiệu hóa khuôn mặt"""
    print("\n❌ VÔ HIỆU HÓA KHUÔN MẶT")
    print("-" * 25)
    
    list_faces(db)
    
    name = input("\nNhập tên khuôn mặt muốn vô hiệu hóa: ").strip()
    if not name:
        print("❌ Tên không được rỗng")
        return
    
    success = db.deactivate_face(name)
    if success:
        print(f"✅ Đã vô hiệu hóa '{name}'")
    else:
        print(f"❌ Không thể vô hiệu hóa '{name}'")

def reactivate_face(db):
    """Kích hoạt lại khuôn mặt"""
    print("\n✅ KÍCH HOẠT LẠI KHUÔN MẶT")
    print("-" * 25)
    
    list_faces(db)
    
    name = input("\nNhập tên khuôn mặt muốn kích hoạt lại: ").strip()
    if not name:
        print("❌ Tên không được rỗng")
        return
    
    success = db.reactivate_face(name)
    if success:
        print(f"✅ Đã kích hoạt lại '{name}'")
    else:
        print(f"❌ Không thể kích hoạt lại '{name}'")

def clear_login_history(db):
    """Xóa lịch sử login"""
    print("\n🧹 XÓA LỊCH SỬ LOGIN")
    print("-" * 20)
    
    print("1. Xóa lịch sử của một khuôn mặt cụ thể")
    print("2. Xóa toàn bộ lịch sử login")
    
    choice = input("Chọn (1-2): ").strip()
    
    if choice == "1":
        list_faces(db)
        name = input("\nNhập tên khuôn mặt: ").strip()
        if name:
            confirm = input(f"⚠️  Xóa lịch sử login của '{name}'? (y/N): ").strip().lower()
            if confirm == 'y':
                db.clear_login_history(name)
            else:
                print("🚫 Đã hủy")
        else:
            print("❌ Tên không được rỗng")
            
    elif choice == "2":
        confirm = input("⚠️  Xóa TOÀN BỘ lịch sử login? (y/N): ").strip().lower()
        if confirm == 'y':
            db.clear_login_history()
        else:
            print("🚫 Đã hủy")
    else:
        print("❌ Lựa chọn không hợp lệ")

def delete_all_faces(db):
    """Xóa tất cả khuôn mặt"""
    print("\n💥 XÓA TẤT CẢ DỮ LIỆU KHUÔN MẶT")
    print("-" * 35)
    
    # Hiển thị thống kê trước
    try:
        stats = db.get_face_stats()
        print(f"📊 Hiện tại có:")
        print(f"  - Khuôn mặt: {stats.get('total_faces', 0)}")
        print(f"  - Lịch sử login: {stats.get('total_logins', 0)}")
        print(f"  - Phiên hoạt động: {stats.get('active_sessions', 0)}")
    except:
        pass
    
    print("\n⚠️  CẢNH BÁO: Thao tác này sẽ XÓA TẤT CẢ dữ liệu khuôn mặt!")
    print("Bao gồm: faces, login_history, face_sessions")
    print("Không thể khôi phục sau khi xóa!")
    
    confirm1 = input("\nBạn có chắc chắn? (y/N): ").strip().lower()
    if confirm1 != 'y':
        print("🚫 Đã hủy")
        return
    
    confirm2 = input("Nhập 'DELETE ALL' để xác nhận: ").strip()
    if confirm2 != 'DELETE ALL':
        print("🚫 Xác nhận sai, đã hủy")
        return
    
    success = db.delete_all_faces(confirm=True)
    if success:
        print("💥 ĐÃ XÓA TẤT CẢ DỮ LIỆU KHUÔN MẶT!")
    else:
        print("❌ Có lỗi xảy ra khi xóa")

def show_database_stats(db):
    """Hiển thị thống kê database"""
    print("\n📊 THỐNG KÊ DATABASE")
    print("-" * 30)
    
    try:
        stats = db.get_face_stats()
        
        print(f"👥 Tổng số khuôn mặt: {stats.get('total_faces', 0)}")
        print(f"🔐 Tổng số lần login: {stats.get('total_logins', 0)}")
        print(f"✅ Login thành công: {stats.get('successful_logins', 0)}")
        print(f"🟢 Phiên hoạt động: {stats.get('active_sessions', 0)}")
        print(f"🏆 Người dùng tích cực nhất: {stats.get('top_user', 'N/A')}")
        
        # Database file info
        db_path = db.db_path
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"💾 Kích thước database: {size:,} bytes")
            
            # Recent login history
            try:
                history = db.get_recent_login_history(5)
                if history:
                    print(f"\n📋 5 lần login gần nhất:")
                    for entry in history:
                        print(f"  {entry}")
            except:
                pass
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy thống kê: {e}")

def main():
    """Chương trình chính"""
    print("🚀 Starting Face Data Management Tool")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        # Initialize database
        db = FaceDatabase()
        print(f"✅ Connected to database: {db.db_path}")
        
        while True:
            show_menu()
            
            try:
                choice = input("Chọn chức năng (0-8): ").strip()
                
                if choice == "0":
                    print("👋 Tạm biệt!")
                    break
                    
                elif choice == "1":
                    list_faces(db)
                    
                elif choice == "2":
                    delete_face_by_name(db)
                    
                elif choice == "3":
                    delete_face_by_id(db)
                    
                elif choice == "4":
                    deactivate_face(db)
                    
                elif choice == "5":
                    reactivate_face(db)
                    
                elif choice == "6":
                    clear_login_history(db)
                    
                elif choice == "7":
                    delete_all_faces(db)
                    
                elif choice == "8":
                    show_database_stats(db)
                    
                else:
                    print("❌ Lựa chọn không hợp lệ")
                    
                input("\nNhấn Enter để tiếp tục...")
                
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"❌ Lỗi: {e}")
                input("Nhấn Enter để tiếp tục...")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Không thể kết nối database")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
