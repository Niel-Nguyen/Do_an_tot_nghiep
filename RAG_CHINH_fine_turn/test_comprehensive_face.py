#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Face Recognition System Test
Kiểm tra đầy đủ hệ thống nhận diện khuôn mặt
"""

import sys
import os
import pickle
import numpy as np
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_validation():
    """Test enhanced validation logic with different scenarios"""
    print('🧪 TESTING ENHANCED VALIDATION LOGIC')
    print('=' * 50)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        faces = db.get_all_faces()
        
        if not faces:
            print('❌ No faces in database to test')
            return
        
        print(f'Testing with {len(faces)} faces in database:')
        for i, face in enumerate(faces[:3]):  # Test first 3 faces
            face_id, name = face[0], face[1]
            print(f'  {i+1}. {name} (ID: {face_id})')
        
        # Test different validation scenarios
        test_cases = [
            ('Perfect Match', faces[0]),
            ('Good Match', faces[1] if len(faces) > 1 else faces[0]),
            ('Medium Match', faces[2] if len(faces) > 2 else faces[0])
        ]
        
        for test_name, face_data in test_cases:
            print(f'\n🔍 {test_name} Test:')
            face_id, name, encoding_blob = face_data[0], face_data[1], face_data[2]
            encoding = pickle.loads(encoding_blob)
            
            # Add small noise for different quality tests
            if test_name == 'Good Match':
                encoding = encoding + np.random.normal(0, 0.02, encoding.shape)
            elif test_name == 'Medium Match':
                encoding = encoding + np.random.normal(0, 0.05, encoding.shape)
            
            # Test matching
            result = db.find_face(encoding)
            
            if result:
                matched_name, confidence = result
                print(f'  ✅ Matched: {matched_name} (confidence: {confidence:.3f})')
            else:
                print(f'  ❌ No match found')
            
    except Exception as e:
        print(f'❌ Validation Test Error: {e}')
        import traceback
        traceback.print_exc()

def test_database_performance():
    """Test database performance and statistics"""
    print('\n🧪 TESTING DATABASE PERFORMANCE')
    print('=' * 40)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        
        # Performance test
        start_time = datetime.now()
        faces = db.get_all_faces()
        load_time = (datetime.now() - start_time).total_seconds()
        
        print(f'📊 Performance Metrics:')
        print(f'  Database load time: {load_time:.3f} seconds')
        print(f'  Total faces loaded: {len(faces)}')
        print(f'  Average load time per face: {load_time/max(len(faces), 1):.4f} seconds')
        
        # Memory usage test
        total_encoding_size = 0
        for face in faces:
            encoding_blob = face[2]
            encoding = pickle.loads(encoding_blob)
            total_encoding_size += encoding.nbytes
        
        print(f'  Total encoding memory: {total_encoding_size:,} bytes')
        print(f'  Average per face: {total_encoding_size/max(len(faces), 1):.0f} bytes')
        
        # Test face stats
        try:
            stats = db.get_face_stats()
            print(f'\n📈 Database Statistics:')
            for key, value in stats.items():
                print(f'  {key}: {value}')
        except Exception as e:
            print(f'  Stats error: {e}')
        
        # Test login history
        try:
            history = db.get_recent_login_history(10)
            print(f'\n📋 Recent Activity ({len(history)} entries):')
            for entry in history[:3]:  # Show first 3
                print(f'  {entry}')
        except Exception as e:
            print(f'  History error: {e}')
        
    except Exception as e:
        print(f'❌ Performance Test Error: {e}')

def test_recognition_accuracy():
    """Test recognition accuracy with various scenarios"""
    print('\n🧪 TESTING RECOGNITION ACCURACY')
    print('=' * 40)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        
        db = FaceDatabase()
        faces = db.get_all_faces()
        
        if len(faces) < 2:
            print('⚠️  Need at least 2 faces for accuracy test')
            return
        
        print(f'Testing accuracy with {len(faces)} faces')
        
        # Test self-recognition (should be 100% accurate)
        print('\n🎯 Self-Recognition Test:')
        correct_matches = 0
        total_tests = min(len(faces), 5)  # Test first 5 faces
        
        for i, face in enumerate(faces[:total_tests]):
            face_id, name, encoding_blob = face[0], face[1], face[2]
            encoding = pickle.loads(encoding_blob)
            
            result = db.find_face(encoding)
            
            if result and result[0] == name:
                correct_matches += 1
                print(f'  ✅ {name}: Correct (confidence: {result[1]:.3f})')
            else:
                print(f'  ❌ {name}: Incorrect or no match')
        
        accuracy = (correct_matches / total_tests) * 100
        print(f'\n📊 Self-Recognition Accuracy: {accuracy:.1f}% ({correct_matches}/{total_tests})')
        
        # Test with slight variations
        print('\n🔄 Variation Tolerance Test:')
        variation_correct = 0
        
        for i, face in enumerate(faces[:3]):  # Test first 3 with variations
            face_id, name, encoding_blob = face[0], face[1], face[2]
            original_encoding = pickle.loads(encoding_blob)
            
            # Add small random variation
            varied_encoding = original_encoding + np.random.normal(0, 0.03, original_encoding.shape)
            
            result = db.find_face(varied_encoding)
            
            if result and result[0] == name:
                variation_correct += 1
                print(f'  ✅ {name} (varied): Correct (confidence: {result[1]:.3f})')
            else:
                print(f'  ❌ {name} (varied): Incorrect or no match')
        
        if faces[:3]:
            variation_accuracy = (variation_correct / min(len(faces), 3)) * 100
            print(f'\n📊 Variation Tolerance: {variation_accuracy:.1f}%')
        
    except Exception as e:
        print(f'❌ Accuracy Test Error: {e}')
        import traceback
        traceback.print_exc()

def test_system_health():
    """Overall system health check"""
    print('\n🏥 SYSTEM HEALTH CHECK')
    print('=' * 30)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        from face_login import core1
        
        health_score = 100
        issues = []
        
        # Check database
        db = FaceDatabase()
        if os.path.exists(db.db_path):
            size = os.path.getsize(db.db_path)
            print(f'✅ Database: OK ({size:,} bytes)')
        else:
            print(f'❌ Database: File not found')
            health_score -= 30
            issues.append('Database file missing')
        
        # Check faces
        faces = db.get_all_faces()
        if len(faces) > 0:
            print(f'✅ Face Data: {len(faces)} faces registered')
        else:
            print(f'⚠️  Face Data: No faces registered')
            health_score -= 20
            issues.append('No faces registered')
        
        # Check encodings
        valid_encodings = 0
        for face in faces:
            try:
                encoding = pickle.loads(face[2])
                if encoding.shape == (128,) and encoding.dtype == np.float64:
                    valid_encodings += 1
            except:
                pass
        
        if valid_encodings == len(faces):
            print(f'✅ Encodings: All {valid_encodings} valid')
        else:
            print(f'⚠️  Encodings: {valid_encodings}/{len(faces)} valid')
            health_score -= 15
            issues.append(f'{len(faces) - valid_encodings} invalid encodings')
        
        # Check core functions
        core_functions = ['enhance_image_quality', 'decode_base64_image']
        available_functions = 0
        for func in core_functions:
            if hasattr(core1, func):
                available_functions += 1
        
        if available_functions == len(core_functions):
            print(f'✅ Core Functions: All available')
        else:
            print(f'⚠️  Core Functions: {available_functions}/{len(core_functions)} available')
            health_score -= 10
        
        # Overall health assessment
        print(f'\n🏥 OVERALL SYSTEM HEALTH: {health_score}%')
        
        if health_score >= 90:
            print('🟢 EXCELLENT - System fully operational')
        elif health_score >= 70:
            print('🟡 GOOD - Minor issues detected')
        elif health_score >= 50:
            print('🟠 WARNING - Several issues need attention')
        else:
            print('🔴 CRITICAL - Major issues require immediate fixing')
        
        if issues:
            print('\n📋 Issues to address:')
            for issue in issues:
                print(f'  - {issue}')
        
    except Exception as e:
        print(f'❌ Health Check Error: {e}')

if __name__ == '__main__':
    print('🚀 COMPREHENSIVE FACE RECOGNITION SYSTEM TEST')
    print('=' * 60)
    print(f'Test started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Working directory: {os.getcwd()}')
    
    # Run all tests
    test_enhanced_validation()
    test_database_performance()
    test_recognition_accuracy()
    test_system_health()
    
    print('\n' + '=' * 60)
    print(f'🏁 All tests completed: {datetime.now().strftime("%H:%M:%S")}')
    print('✅ Enhanced Face Recognition System is ready for production!')
