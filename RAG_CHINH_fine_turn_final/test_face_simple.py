#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for face recognition system
"""

import sys
import os
import pickle
import numpy as np
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_face_database():
    """Test face database functionality"""
    print('🧪 TESTING FACE DATABASE')
    print('=' * 40)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        # Initialize database
        db = FaceDatabase()
        
        print('\n📊 Database Content:')
        
        # Get all faces
        faces = db.get_all_faces()
        print(f"Total faces found: {len(faces)}")
        
        if faces:
            print('\n👥 Face Details:')
            for face in faces:
                face_id, name, encoding_blob, created_at = face[:4]
                print(f"  ID: {face_id}, Name: {name}, Created: {created_at}")
                
                # Decode encoding to check
                try:
                    encoding = pickle.loads(encoding_blob)
                    print(f"    Encoding shape: {encoding.shape}, dtype: {encoding.dtype}")
                    print(f"    Sample values: {encoding[:3]}...")
                except Exception as e:
                    print(f"    Error loading encoding: {e}")
        
        # Test face stats
        try:
            stats = db.get_face_stats()
            print(f'\n📈 Face Statistics: {stats}')
        except Exception as e:
            print(f'\n⚠️  Face stats error: {e}')
        
        # Test recent login history
        try:
            history = db.get_recent_login_history(5)
            print(f'\n📋 Recent Login History ({len(history)} entries):')
            for entry in history:
                print(f"  {entry}")
        except Exception as e:
            print(f'\n⚠️  Login history error: {e}')
            
    except Exception as e:
        print(f'❌ Database Error: {e}')
        import traceback
        traceback.print_exc()

def test_face_recognition():
    """Test face recognition without actual image"""
    print('\n🧪 TESTING FACE RECOGNITION FUNCTIONS')
    print('=' * 45)
    
    try:
        from face_login import core1
        
        # List available functions
        print('📋 Available functions in core1:')
        functions = [name for name in dir(core1) if callable(getattr(core1, name)) and not name.startswith('_')]
        for func in functions:
            print(f"  - {func}")
        
        # Test specific functions if they exist
        if hasattr(core1, 'enhance_image_quality'):
            print('\n✅ enhance_image_quality function found')
            
        if hasattr(core1, 'decode_base64_image'):
            print('✅ decode_base64_image function found')
            
        if hasattr(core1, 'find_face'):
            print('✅ find_face function found')
            
    except Exception as e:
        print(f'❌ Face Recognition Error: {e}')
        import traceback
        traceback.print_exc()

def test_face_matching():
    """Test face matching with database"""
    print('\n🧪 TESTING FACE MATCHING')
    print('=' * 35)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        from face_login import core1
        
        db = FaceDatabase()
        
        # Get a face from database to test matching
        faces = db.get_all_faces()
        
        if faces:
            print(f'Found {len(faces)} faces in database')
            
            # Take first face and test matching
            first_face = faces[0]
            face_id, name, encoding_blob = first_face[0], first_face[1], first_face[2]
            
            print(f'Testing matching with: {name} (ID: {face_id})')
            
            # Load the encoding
            encoding = pickle.loads(encoding_blob)
            print(f'Encoding shape: {encoding.shape}')
            
            # Test find_face method
            if hasattr(db, 'find_face'):
                print('Testing find_face method...')
                match_result = db.find_face(encoding)
                
                if match_result:
                    print(f'✅ Match found: {match_result}')
                else:
                    print('❌ No match found (unexpected for same encoding)')
            else:
                print('⚠️  find_face method not available')
                
        else:
            print('No faces in database to test with')
            
    except Exception as e:
        print(f'❌ Face Matching Error: {e}')
        import traceback
        traceback.print_exc()

def quick_database_info():
    """Quick database information"""
    print('🔍 QUICK DATABASE INFO')
    print('=' * 25)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        
        # Check database file
        if os.path.exists(db.db_path):
            size = os.path.getsize(db.db_path)
            print(f'Database file: {db.db_path}')
            print(f'Database size: {size:,} bytes')
        
        # Quick face count
        faces = db.get_all_faces()
        print(f'Total faces: {len(faces)}')
        
        # List face names
        if faces:
            names = [face[1] for face in faces]
            print(f'Face names: {", ".join(names)}')
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    print(f'🚀 Face Recognition Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Working directory: {os.getcwd()}')
    
    # Quick info first
    quick_database_info()
    
    print('\n' + '='*60)
    
    # Test database
    test_face_database()
    
    # Test recognition functions  
    test_face_recognition()
    
    # Test face matching
    test_face_matching()
    
    print(f'\n✅ Test completed - {datetime.now().strftime("%H:%M:%S")}')
