
from face_login.face_db_manager import FaceDBManager
from face_login.core1 import FaceRecognition
import cv2
import numpy as np

print('🧪 TESTING ENHANCED FACE RECOGNITION SYSTEM')
print('=' * 60)

# Initialize systems
db_manager = FaceDBManager()
face_rec = FaceRecognition()

# Load a test image (using existing one)
import os
test_dir = 'face_login'
test_images = []
for file in os.listdir(test_dir):
    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
        test_images.append(os.path.join(test_dir, file))

if test_images:
    test_image_path = test_images[0]
    print(f'📷 Loading test image: {test_image_path}')
    
    # Test recognition
    result = face_rec.recognize_face(test_image_path)
    print(f'Recognition result: {result}')
    
    if result and 'encoding' in result:
        print('\\n🔍 Testing database matching...')
        match = db_manager.find_face(result['encoding'])
        
        if match:
            print(f'✅ MATCH FOUND: {match}')
        else:
            print('❌ NO MATCH FOUND')
    else:
        print('❌ Failed to extract face encoding from test image')
else:
    print('❌ No test images found in face_login directory')

print('\\n📊 Database status:')
db_manager.get_database_stats()