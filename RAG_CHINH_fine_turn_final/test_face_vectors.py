#!/usr/bin/env python3
"""
Test script để kiểm tra module face_login và vector storage
"""

import sys
import os
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def create_test_image(color='red'):
    """Create a simple test image in base64 format"""
    colors = {
        'red': (255, 0, 0),
        'blue': (0, 0, 255), 
        'green': (0, 255, 0)
    }
    color_rgb = colors.get(color, (255, 0, 0))
    
    # Create a simple 200x200 RGB image
    image = Image.new('RGB', (200, 200), color=color_rgb)
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def test_face_login_module():
    """Test face_login module functions"""
    print("=== Testing Face Login Module ===")
    
    try:
        from face_login.utils import (
            load_faces, save_faces, get_face_database_info, 
            reset_face_database
        )
        from face_login.core1 import recognize_user, register_user
        print("✓ Face login imports successful")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    
    # Test 1: Check database info
    print("\n1. Testing database info...")
    info = get_face_database_info()
    print(f"Database exists: {info['exists']}")
    print(f"Database path: {info['path']}")
    print(f"Face count: {info['count']}")
    print(f"Names: {info['names']}")
    
    # Test 2: Reset database 
    print("\n2. Testing database reset...")
    reset_result = reset_face_database()
    print(f"Reset successful: {reset_result}")
    
    # Test 3: Load empty database
    print("\n3. Testing load faces...")
    faces = load_faces()
    print(f"Loaded faces: {len(faces)} entries")
    
    # Test 4: Register a test user
    print("\n4. Testing user registration...")
    test_image = create_test_image('red')
    try:
        register_user("test_user_1", test_image)
        print("✓ User registration successful")
        
        # Check database after registration
        info_after = get_face_database_info()
        print(f"Face count after registration: {info_after['count']}")
        print(f"Names after registration: {info_after['names']}")
        
    except Exception as e:
        print(f"✗ User registration failed: {e}")
        return False
    
    # Test 5: Try recognition
    print("\n5. Testing face recognition...")
    try:
        # Same image should be recognized
        result1 = recognize_user(test_image)
        print(f"Recognition result (same image): {result1}")
        
        # Different image should not be recognized
        different_image = create_test_image('blue')
        result2 = recognize_user(different_image)
        print(f"Recognition result (different image): {result2}")
        
    except Exception as e:
        print(f"✗ Face recognition failed: {e}")
        return False
    
    # Test 6: Register another user
    print("\n6. Testing multiple users...")
    try:
        green_image = create_test_image('green')
        register_user("test_user_2", green_image)
        
        info_final = get_face_database_info()
        print(f"Final face count: {info_final['count']}")
        print(f"Final names: {info_final['names']}")
        
        # Test recognition of second user
        result3 = recognize_user(green_image)
        print(f"Recognition of second user: {result3}")
        
    except Exception as e:
        print(f"✗ Multiple user test failed: {e}")
        return False
    
    return True

def test_vector_storage():
    """Test the actual vector storage mechanism"""
    print("\n=== Testing Vector Storage ===")
    
    try:
        from face_login.utils import load_faces, save_faces
        import face_recognition
        import numpy as np
        
        # Create dummy face encodings (128-dimensional vectors)
        dummy_encoding_1 = np.random.rand(128).astype(np.float64)
        dummy_encoding_2 = np.random.rand(128).astype(np.float64)
        
        # Test saving
        print("1. Testing manual vector save...")
        test_faces = {
            'dummy_user_1': dummy_encoding_1,
            'dummy_user_2': dummy_encoding_2
        }
        
        save_faces(test_faces)
        print("✓ Vector save successful")
        
        # Test loading
        print("2. Testing vector load...")
        loaded_faces = load_faces()
        print(f"Loaded {len(loaded_faces)} face vectors")
        
        # Verify vector integrity
        print("3. Testing vector integrity...")
        for name, encoding in loaded_faces.items():
            print(f"  {name}: vector shape {encoding.shape}, dtype {encoding.dtype}")
            
            # Verify it's a proper face encoding
            if isinstance(encoding, np.ndarray) and encoding.shape == (128,):
                print(f"    ✓ Valid face encoding vector")
            else:
                print(f"    ✗ Invalid face encoding: {type(encoding)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Vector storage test failed: {e}")
        return False

def test_api_integration():
    """Test integration with Flask app"""
    print("\n=== Testing API Integration ===")
    
    try:
        from app import reset_face_login_database
        
        print("1. Testing app reset function...")
        result = reset_face_login_database()
        print(f"App reset result: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ API integration test failed: {e}")
        return False

def main():
    """Run all face login tests"""
    print("Face Login Module Test Suite")
    print("=" * 50)
    
    success = True
    
    # Test 1: Face login module
    if not test_face_login_module():
        success = False
    
    # Test 2: Vector storage
    if not test_vector_storage():
        success = False
    
    # Test 3: API integration
    if not test_api_integration():
        success = False
    
    print(f"\n{'='*50}")
    print(f"{'✓ All tests passed!' if success else '✗ Some tests failed!'}")
    
    if success:
        print("\nFace Login Module Summary:")
        print("- Sử dụng face_recognition library để tạo 128-D vectors")
        print("- Lưu trữ vectors trong pickle file (face_database.pkl)")
        print("- So sánh vectors bằng face_distance để nhận diện")
        print("- Hỗ trợ reset database khi đóng/mở bàn mới")
        print("- Vectors được lưu theo format: {name: encoding_array}")

if __name__ == "__main__":
    main()
