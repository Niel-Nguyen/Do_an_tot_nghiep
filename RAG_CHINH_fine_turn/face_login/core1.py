import face_recognition
import cv2
import base64
import numpy as np
from .utils import load_faces, save_faces, find_face, start_face_session

def decode_base64_image(image_b64):
    """Decode base64 image to OpenCV format with enhanced preprocessing"""
    try:
        if "," in image_b64:
            header, encoded = image_b64.split(",", 1)
        else:
            encoded = image_b64
        img_data = base64.b64decode(encoded)
        nparr = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is not None:
            # Enhanced preprocessing for better face recognition
            image = enhance_image_quality(image)
        
        return image
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None

def enhance_image_quality(image):
    """Enhance image quality for better face recognition"""
    try:
        # 1. Resize if too small or too large
        height, width = image.shape[:2]
        
        # Target size for optimal face recognition
        target_size = 640
        if width < 300 or height < 300:
            # Upscale small images
            scale = max(300/width, 300/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"Upscaled image from {width}x{height} to {new_width}x{new_height}")
        elif width > 1200 or height > 1200:
            # Downscale large images
            scale = min(target_size/width, target_size/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            print(f"Downscaled image from {width}x{height} to {new_width}x{new_height}")
        
        # 2. Improve lighting and contrast
        # Convert to LAB color space for better lighting adjustment
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        
        # Merge channels back
        enhanced_lab = cv2.merge((cl, a, b))
        image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # 3. Reduce noise
        image = cv2.bilateralFilter(image, 9, 75, 75)
        
        # 4. Ensure proper color space
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Convert BGR to RGB for face_recognition
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image_rgb
        
        return image
        
    except Exception as e:
        print(f"Error enhancing image quality: {e}")
        return image  # Return original if enhancement fails

def calculate_match_confidence(encoding1, encoding2):
    """Calculate more accurate confidence score between two encodings"""
    try:
        # Use face_recognition distance (Euclidean)
        distance = face_recognition.face_distance([encoding1], encoding2)[0]
        
        # Convert distance to confidence (inverse relationship)
        # Good matches have distance < 0.6, excellent matches < 0.4
        if distance < 0.3:
            confidence = 0.95 - (distance * 0.5)  # 0.95-0.80 range
        elif distance < 0.4:
            confidence = 0.85 - (distance * 0.75)  # 0.85-0.55 range
        elif distance < 0.6:
            confidence = 0.70 - (distance * 0.5)   # 0.70-0.40 range
        else:
            confidence = max(0.1, 0.6 - distance)  # Low confidence
        
        return max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
    except Exception as e:
        print(f"Error calculating confidence: {e}")
        return 0.5

def recognize_user(image_b64: str, table_id: str = None, session_token: str = None) -> str:
    """Recognize user from base64 image with enhanced processing and session tracking"""
    try:
        print(f"🔍 Starting enhanced face recognition...")
        
        known_faces = load_faces()
        if not known_faces:
            print("No faces in database for recognition")
            return None
        
        print(f"Loaded {len(known_faces)} known faces: {list(known_faces.keys())}")
            
        image = decode_base64_image(image_b64)
        if image is None:
            print("Failed to decode image")
            return None

        print(f"Enhanced image processed, shape: {image.shape}")

        # Image is already in RGB from enhance_image_quality
        
        # Multiple face detection attempts with different models
        face_encodings = []
        
        # Method 1: Standard face_recognition with large model
        encodings_1 = face_recognition.face_encodings(image, model='large')
        if encodings_1:
            face_encodings.extend(encodings_1)
            print(f"Found {len(encodings_1)} face(s) with large model")
        
        # Method 2: If no faces found, try small model (faster, sometimes more permissive)
        if not face_encodings:
            encodings_2 = face_recognition.face_encodings(image, model='small')
            if encodings_2:
                face_encodings.extend(encodings_2)
                print(f"Found {len(encodings_2)} face(s) with small model")
        
        # Method 3: If still no faces, try with different face detection
        if not face_encodings:
            # Try HOG-based detection (more permissive)
            face_locations = face_recognition.face_locations(image, model='hog')
            if face_locations:
                encodings_3 = face_recognition.face_encodings(image, face_locations, model='large')
                if encodings_3:
                    face_encodings.extend(encodings_3)
                    print(f"Found {len(encodings_3)} face(s) with HOG detection")

        if not face_encodings:
            print("❌ No faces detected in image after all attempts")
            return None
        
        print(f"✅ Total face encodings extracted: {len(face_encodings)}")
        
        # Try recognition with each encoding (in case multiple faces detected)
        best_match = None
        best_confidence = 0
        
        for i, face_encoding in enumerate(face_encodings):
            print(f"\n🎯 Testing face encoding {i+1}/{len(face_encodings)}:")
            print(f"   Encoding shape: {face_encoding.shape}, dtype: {face_encoding.dtype}")
            print(f"   Encoding range: min={face_encoding.min():.3f}, max={face_encoding.max():.3f}")
            print(f"   Encoding std: {face_encoding.std():.3f}, mean abs: {np.mean(np.abs(face_encoding)):.3f}")
            
            # Try multiple tolerance levels
            tolerances = [0.4, 0.5, 0.6]  # From strict to permissive
            
            for tolerance in tolerances:
                print(f"   🔍 Trying tolerance: {tolerance}")
                match_name = find_face(face_encoding, tolerance=tolerance)
                
                if match_name:
                    # Calculate confidence more precisely
                    confidence = calculate_match_confidence(face_encoding, known_faces[match_name])
                    print(f"   ✅ Found match: {match_name} (confidence: {confidence:.3f}, tolerance: {tolerance})")
                    
                    # Keep track of best match
                    if confidence > best_confidence:
                        best_match = match_name
                        best_confidence = confidence
                    
                    break  # Found match with this tolerance, no need to try higher ones
                else:
                    print(f"   ❌ No match with tolerance {tolerance}")
        
        if best_match:
            if table_id and session_token:
                start_face_session(best_match, table_id, session_token)
            
            print(f"🎉 FINAL RESULT: Recognized {best_match} (confidence: {best_confidence:.3f})")
            return best_match
        else:
            print(f"❌ FINAL RESULT: No face recognized")
            return None
            
    except Exception as e:
        print(f"Error in user recognition: {e}")
        import traceback
        traceback.print_exc()
        return None

def register_user(name: str, image_b64: str, table_id: str = None, session_token: str = None) -> bool:
    """Register new user with face encoding and optional session tracking"""
    try:
        print(f"🔧 Registering user: {name}")
        
        known_faces = load_faces()
        image = decode_base64_image(image_b64)
        if image is None:
            print("Failed to decode image for registration")
            return False

        print(f"Registration image decoded, shape: {image.shape}")

        # Image is already in RGB from enhance_image_quality
        
        # Get face encodings with multiple attempts for best quality
        face_encodings = []
        
        # Try large model first for best quality
        encodings = face_recognition.face_encodings(image, model='large')
        if encodings:
            face_encodings.extend(encodings)
            print(f"Found {len(encodings)} face(s) for registration with large model")
        
        if not face_encodings:
            # Fallback to small model
            encodings = face_recognition.face_encodings(image, model='small')
            if encodings:
                face_encodings.extend(encodings)
                print(f"Found {len(encodings)} face(s) for registration with small model")

        if face_encodings:
            # Use the first (and usually best) face found
            face_encoding = face_encodings[0]
            print(f"Registration encoding shape: {face_encoding.shape}, dtype: {face_encoding.dtype}")
            print(f"Registration encoding range: min={face_encoding.min():.3f}, max={face_encoding.max():.3f}")
            
            # Validate encoding quality
            quality_score = validate_encoding_quality(face_encoding)
            print(f"Encoding quality score: {quality_score:.3f}")
            
            if quality_score < 0.3:
                print("⚠️ Warning: Poor quality encoding detected. Registration may be unreliable.")
            
            known_faces[name] = face_encoding
            save_faces(known_faces)
            
            if table_id and session_token:
                # Start face session for newly registered user
                start_face_session(name, table_id, session_token)
            
            print(f"Successfully registered user: {name}")
            return True
        else:
            print(f"No face detected in registration image for user: {name}")
            return False
            
    except Exception as e:
        print(f"Error in user registration: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_encoding_quality(encoding: np.ndarray) -> float:
    """Validate quality of face encoding"""
    try:
        # Check if encoding has reasonable distribution
        std_dev = np.std(encoding)
        mean_abs = np.mean(np.abs(encoding))
        
        # Good encodings typically have std between 0.1-0.3 and mean_abs between 0.05-0.25
        std_score = 1.0 if 0.1 <= std_dev <= 0.3 else max(0.0, 1.0 - abs(std_dev - 0.2) / 0.2)
        mean_score = 1.0 if 0.05 <= mean_abs <= 0.25 else max(0.0, 1.0 - abs(mean_abs - 0.15) / 0.15)
        
        # Check for anomalies (too many extreme values)
        extreme_values = np.sum(np.abs(encoding) > 0.5)
        extreme_score = 1.0 if extreme_values <= 10 else max(0.0, 1.0 - (extreme_values - 10) / 20)
        
        quality_score = (std_score + mean_score + extreme_score) / 3
        return quality_score
        
    except Exception as e:
        print(f"Error validating encoding quality: {e}")
        return 0.5  # Neutral score on error

def extract_face_encoding(image_b64: str) -> np.ndarray:
    """Extract face encoding from base64 image for testing purposes"""
    try:
        image = decode_base64_image(image_b64)
        if image is None:
            return None
        
        encodings = face_recognition.face_encodings(image, model='large')
        return encodings[0] if encodings else None
    except Exception as e:
        print(f"Error extracting face encoding: {e}")
        return None
