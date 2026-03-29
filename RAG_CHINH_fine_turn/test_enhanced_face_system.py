#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script cho enhanced face recognition system
"""

import sys
import os
import cv2
import numpy as np
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_face_system():
    """Test the enhanced face recognition system"""
    print('🧪 TESTING ENHANCED FACE RECOGNITION SYSTEM')
    print('=' * 60)
    
    try:
        # Import face login modules
        from face_login.face_db_manager import FaceDatabase
        from face_login.core1 import FaceRecognition
        
        # Initialize systems
        print('📚 Initializing database...')
        db = FaceDatabase()
        
        print('🤖 Initializing face recognition...')
        face_rec = FaceRecognition()
        
        print('\n📊 Database Statistics:')
        stats = db.get_database_stats()
        print(f"Total faces: {stats.get('total_faces', 0)}")
        print(f"Active faces: {stats.get('active_faces', 0)}")
        print(f"Total logins: {stats.get('total_logins', 0)}")
        
        # List all faces
        print('\n👥 Registered Faces:')
        faces = db.get_all_faces()
        if faces:
            for face in faces:
                print(f"  - ID: {face[0]}, Name: {face[1]}, Logins: {face[5]}, Active: {face[6]}")
        else:
            print("  No faces found")
            
        # Test with sample image if available
        test_dir = 'face_login'
        test_images = []
        for file in os.listdir(test_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                test_images.append(os.path.join(test_dir, file))
        
        if test_images:
            test_image = test_images[0]
            print(f'\n📷 Testing with image: {test_image}')
            
            # Test face recognition
            result = face_rec.recognize_face(test_image)
            print(f'Recognition result: {result}')
            
            if result and 'encoding' in result:
                print('\n🔍 Testing database matching...')
                
                # Test find_face method
                match = db.find_face(result['encoding'])
                
                if match:
                    print(f'✅ MATCH FOUND: {match}')
                else:
                    print('❌ NO MATCH FOUND')
            else:
                print('❌ Failed to extract face encoding')
        else:
            print('\n⚠️  No test images found')
            
        # Test vector storage
        print('\n🔢 Testing vector storage:')
        faces_with_vectors = db.get_faces_with_encodings()
        if faces_with_vectors:
            for face_id, name, encoding_blob in faces_with_vectors:
                encoding = pickle.loads(encoding_blob)
                print(f"  - {name}: vector shape {encoding.shape}, type {type(encoding)}")
        else:
            print("  No face vectors found")
            
    except ImportError as e:
        print(f'❌ Import Error: {e}')
        print('Available modules in face_login:')
        face_login_dir = 'face_login'
        if os.path.exists(face_login_dir):
            for file in os.listdir(face_login_dir):
                if file.endswith('.py'):
                    print(f'  - {file}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

def test_database_only():
    """Test only database functionality"""
    print('🧪 TESTING DATABASE ONLY')
    print('=' * 40)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        
        print('📊 Database Statistics:')
        stats = db.get_database_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print('\n👥 All Faces:')
        faces = db.get_all_faces()
        for face in faces:
            print(f"  Face ID: {face[0]}, Name: {face[1]}")
            
        print('\n🔢 Face Encodings:')
        faces_with_encodings = db.get_faces_with_encodings()
        for face_id, name, encoding_blob in faces_with_encodings:
            encoding = pickle.loads(encoding_blob)
            print(f"  {name}: shape {encoding.shape}, dtype {encoding.dtype}")
            print(f"    Sample values: {encoding[:5]}...")
            
    except Exception as e:
        print(f'❌ Database Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print(f"🚀 Starting test at {datetime.now()}")
    print(f"Python path: {sys.path[:3]}...")
    print(f"Current working directory: {os.getcwd()}")
    
    # Test database first
    test_database_only()
    
    print('\n' + '='*60)
    
    # Then test full system
    test_face_system()
    
    print(f"\n✅ Test completed at {datetime.now()}")
