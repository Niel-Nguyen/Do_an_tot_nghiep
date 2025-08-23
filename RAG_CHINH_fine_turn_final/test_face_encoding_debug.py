#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test face recognition với cùng một ảnh
Kiểm tra tại sao distance lại quá lớn
"""

import sys
import os
import numpy as np
import base64
from PIL import Image
import io

# Add face_login to path
sys.path.insert(0, 'face_login')

def test_same_image_recognition():
    """Test face recognition với cùng một ảnh"""
    print("🧪 Testing Face Recognition with Same Image")
    print("=" * 60)
    
    try:
        from face_login.face_db_manager import FaceDatabase
        import face_recognition
        
        # Create database
        db = FaceDatabase()
        
        # Create a simple test image (white square with some noise)
        # This simulates a face encoding
        print("Creating test face encoding...")
        
        # Method 1: Create random encoding similar to face_recognition output
        test_encoding = np.random.random(128).astype(np.float64)
        # Normalize to typical face_recognition range
        test_encoding = (test_encoding - 0.5) * 2  # Range: -1 to 1
        
        print(f"Test encoding shape: {test_encoding.shape}")
        print(f"Test encoding type: {type(test_encoding)}")
        print(f"Test encoding range: {test_encoding.min():.3f} to {test_encoding.max():.3f}")
        print(f"Test encoding dtype: {test_encoding.dtype}")
        
        # Register the face
        print("\n1. REGISTERING FACE")
        print("-" * 30)
        success = db.register_face("test_same_image", test_encoding)
        print(f"Registration result: {success}")
        
        if not success:
            print("❌ Registration failed!")
            return False
        
        # Try to recognize the SAME encoding
        print("\n2. RECOGNIZING SAME ENCODING")
        print("-" * 30)
        result = db.find_face(test_encoding)
        print(f"Recognition result: {result}")
        
        if result:
            name, confidence = result
            print(f"✅ SAME encoding recognized: {name} (confidence: {confidence:.3f})")
        else:
            print("❌ SAME encoding not recognized!")
        
        # Try with slightly modified encoding
        print("\n3. RECOGNIZING SIMILAR ENCODING")
        print("-" * 30)
        similar_encoding = test_encoding + np.random.random(128) * 0.01  # Add small noise
        result2 = db.find_face(similar_encoding)
        print(f"Similar encoding result: {result2}")
        
        # Calculate manual distance
        print("\n4. MANUAL DISTANCE CALCULATION")
        print("-" * 30)
        
        # Get stored encoding back
        faces = db.get_all_faces()
        if faces:
            stored_encoding = None
            for face_id, name, encoding_blob, created_at in faces:
                if name == "test_same_image":
                    import pickle
                    stored_encoding = pickle.loads(encoding_blob)
                    break
            
            if stored_encoding is not None:
                # Calculate distance manually
                distance_same = np.linalg.norm(test_encoding - stored_encoding)
                distance_face_lib = face_recognition.face_distance([stored_encoding], test_encoding)[0]
                
                print(f"Manual L2 distance (same): {distance_same:.6f}")
                print(f"face_recognition distance (same): {distance_face_lib:.6f}")
                
                # Test with similar
                distance_similar_manual = np.linalg.norm(similar_encoding - stored_encoding)
                distance_similar_face_lib = face_recognition.face_distance([stored_encoding], similar_encoding)[0]
                
                print(f"Manual L2 distance (similar): {distance_similar_manual:.6f}")
                print(f"face_recognition distance (similar): {distance_similar_face_lib:.6f}")
                
                # Check if encodings are exactly the same
                print(f"Encodings exactly equal: {np.array_equal(test_encoding, stored_encoding)}")
                print(f"Max difference: {np.max(np.abs(test_encoding - stored_encoding)):.10f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_real_image():
    """Test với ảnh thật nếu có thể"""
    print("\n🖼️  Testing with Real Image Processing")
    print("=" * 60)
    
    try:
        import face_recognition
        from face_login.core1 import extract_face_encoding
        
        # Create a simple solid color image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_b64 = base64.b64encode(img_bytes.getvalue()).decode()
        
        print("Created test image (solid red square)")
        
        # Try to extract face encoding
        try:
            encoding = extract_face_encoding(img_b64)
            if encoding is not None:
                print(f"✅ Face encoding extracted: shape {encoding.shape}")
                print(f"Encoding range: {encoding.min():.3f} to {encoding.max():.3f}")
                
                # Test with database
                from face_login.face_db_manager import FaceDatabase
                face_db = FaceDatabase()
                success = face_db.register_face("real_test", encoding)
                print(f"Registration: {success}")
                
                result = face_db.find_face(encoding)
                print(f"Recognition: {result}")
            else:
                print("❌ No face found in test image (expected for solid color)")
        except Exception as e:
            print(f"⚠️  Face processing error: {e}")
            print("This is expected if no face is detected in solid color image")
        
    except Exception as e:
        print(f"❌ Real image test failed: {e}")

def main():
    """Run all tests"""
    print("🔍 FACE RECOGNITION DEBUG TESTS")
    print("Testing why distance is too large for same image")
    
    success1 = test_same_image_recognition()
    test_with_real_image()
    
    if success1:
        print("\n✅ Basic tests completed")
    else:
        print("\n❌ Tests failed")
    
    print("\n💡 Next steps:")
    print("1. Check the debug output from actual face login")
    print("2. Compare encoding formats and ranges")
    print("3. Consider if face_recognition library version matters")

if __name__ == "__main__":
    main()
