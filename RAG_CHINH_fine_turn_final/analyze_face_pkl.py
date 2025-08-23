#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để kiểm tra file face_database.pkl
"""

import os
import pickle
import numpy as np
from datetime import datetime

def analyze_pickle_file():
    """Phân tích file face_database.pkl"""
    
    pkl_path = os.path.join('face_login', 'face_database.pkl')
    
    print("=" * 60)
    print("🔍 PHÂN TÍCH FILE FACE_DATABASE.PKL")
    print("=" * 60)
    
    print(f"📂 File path: {pkl_path}")
    print(f"📁 File exists: {os.path.exists(pkl_path)}")
    
    if not os.path.exists(pkl_path):
        print("❌ File face_database.pkl không tồn tại!")
        print("\n💡 File này là:")
        print("   - Legacy storage format (cũ)")  
        print("   - Lưu face encodings dưới dạng dictionary pickle")
        print("   - Được thay thế bằng SQLite database")
        print("   - Chỉ còn dùng để backward compatibility")
        return
    
    try:
        # Lấy thông tin file
        file_stats = os.stat(pkl_path)
        file_size = file_stats.st_size
        file_modified = datetime.fromtimestamp(file_stats.st_mtime)
        
        print(f"📊 File size: {file_size} bytes ({file_size/1024:.1f} KB)")
        print(f"🕒 Last modified: {file_modified}")
        
        # Đọc nội dung file
        print(f"\n🔬 PHÂN TÍCH NỘI DUNG:")
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
            
        print(f"   - Data type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"   - Dictionary keys (faces): {len(data)}")
            
            if data:
                print(f"\n👥 DANH SÁCH FACES TRONG PKL:")
                for i, (name, encoding) in enumerate(data.items(), 1):
                    try:
                        print(f"   {i}. {name}:")
                        print(f"      • Encoding type: {type(encoding)}")
                        if isinstance(encoding, np.ndarray):
                            print(f"      • Shape: {encoding.shape}")
                            print(f"      • DType: {encoding.dtype}")
                            print(f"      • Range: [{encoding.min():.3f}, {encoding.max():.3f}]")
                            print(f"      • Mean: {encoding.mean():.3f}")
                            print(f"      • Std: {encoding.std():.3f}")
                            print(f"      • First 3 values: {encoding[:3]}")
                            
                            # Validate shape
                            if encoding.shape == (128,):
                                print(f"      • ✅ Valid face encoding shape")
                            else:
                                print(f"      • ⚠️ Invalid shape! Expected (128,)")
                        else:
                            print(f"      • ❌ Not a numpy array: {encoding}")
                            
                    except Exception as e:
                        print(f"   {i}. {name}: ❌ Error analyzing: {e}")
            else:
                print("   - Dictionary is empty")
        else:
            print(f"   - ❌ Unexpected data type: {type(data)}")
            print(f"   - Content preview: {str(data)[:200]}...")
            
    except pickle.PickleError as e:
        print(f"❌ Pickle error: {e}")
    except Exception as e:
        print(f"❌ Error reading file: {e}")

def compare_pkl_vs_sqlite():
    """So sánh dữ liệu giữa pkl và SQLite"""
    
    print(f"\n" + "=" * 60)
    print("⚖️  SO SÁNH PKL vs SQLite DATABASE")
    print("=" * 60)
    
    try:
        # Import database manager
        import sys
        sys.path.append('face_login')
        from face_db_manager import FaceDatabase
        
        face_db = FaceDatabase()
        
        # Lấy data từ SQLite
        print("🗄️  SQLITE DATABASE:")
        sqlite_faces = face_db.get_all_faces()
        sqlite_dict = {}
        
        for face_id, name, encoding_blob, created_at, is_active in sqlite_faces:
            if is_active:
                try:
                    encoding = pickle.loads(encoding_blob)
                    sqlite_dict[name] = encoding
                    print(f"   - {name}: {encoding.shape}")
                except Exception as e:
                    print(f"   - {name}: ❌ Error: {e}")
        
        print(f"   Total active faces: {len(sqlite_dict)}")
        
        # Lấy data từ PKL
        pkl_path = os.path.join('face_login', 'face_database.pkl')
        pkl_dict = {}
        
        print(f"\n📦 PICKLE FILE:")
        if os.path.exists(pkl_path):
            try:
                with open(pkl_path, 'rb') as f:
                    pkl_dict = pickle.load(f)
                    
                for name, encoding in pkl_dict.items():
                    print(f"   - {name}: {encoding.shape if isinstance(encoding, np.ndarray) else type(encoding)}")
                    
                print(f"   Total faces: {len(pkl_dict)}")
            except Exception as e:
                print(f"   ❌ Error loading PKL: {e}")
        else:
            print("   ❌ PKL file doesn't exist")
        
        # So sánh
        print(f"\n🔍 SO SÁNH:")
        
        # Tên người dùng
        sqlite_names = set(sqlite_dict.keys())
        pkl_names = set(pkl_dict.keys())
        
        common_names = sqlite_names & pkl_names
        only_sqlite = sqlite_names - pkl_names
        only_pkl = pkl_names - sqlite_names
        
        print(f"   - Faces chung cả 2: {len(common_names)} {list(common_names) if common_names else ''}")
        print(f"   - Chỉ trong SQLite: {len(only_sqlite)} {list(only_sqlite) if only_sqlite else ''}")
        print(f"   - Chỉ trong PKL: {len(only_pkl)} {list(only_pkl) if only_pkl else ''}")
        
        # So sánh encodings của faces chung
        if common_names:
            print(f"\n🧬 SO SÁNH ENCODINGS:")
            for name in common_names:
                sqlite_enc = sqlite_dict[name]
                pkl_enc = pkl_dict[name]
                
                if isinstance(sqlite_enc, np.ndarray) and isinstance(pkl_enc, np.ndarray):
                    if sqlite_enc.shape == pkl_enc.shape:
                        max_diff = np.max(np.abs(sqlite_enc - pkl_enc))
                        are_identical = np.array_equal(sqlite_enc, pkl_enc)
                        print(f"   - {name}: {'✅ Identical' if are_identical else f'⚠️ Max diff: {max_diff:.6f}'}")
                    else:
                        print(f"   - {name}: ❌ Different shapes: {sqlite_enc.shape} vs {pkl_enc.shape}")
                else:
                    print(f"   - {name}: ❌ Type mismatch")
        
    except ImportError:
        print("❌ Cannot import face database manager")
    except Exception as e:
        print(f"❌ Error comparing: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🔍 Face Database PKL Analyzer")
    
    # Analyze pickle file
    analyze_pickle_file()
    
    # Compare with SQLite
    compare_pkl_vs_sqlite()
    
    print(f"\n" + "=" * 60)
    print("📝 KẾT LUẬN VỀ FACE_DATABASE.PKL:")
    print("=" * 60)
    print("📦 face_database.pkl là LEGACY STORAGE FORMAT")
    print("• Format: Dictionary pickle file")
    print("• Structure: {name: numpy_array_128D}")
    print("• Purpose: Lưu face encodings trước khi có SQLite")
    print("• Status: Deprecated, chỉ dùng backward compatibility")
    print("• Primary storage: SQLite database (face_database.db)")
    print("• Sync: PKL được export từ SQLite để tương thích")
    print("=" * 60)

if __name__ == "__main__":
    main()
