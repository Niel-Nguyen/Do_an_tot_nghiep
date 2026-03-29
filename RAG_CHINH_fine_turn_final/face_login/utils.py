import face_recognition
import pickle
import os
import numpy as np
from .face_db_manager import get_face_database

# Legacy pickle file path (for backward compatibility)
FACE_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "face_login", "face_database.pkl")

def load_faces():
    """Load face encodings - now uses SQLite database"""
    try:
        face_db = get_face_database()
        face_rows = face_db.get_all_faces()  # Returns List[Tuple[id, name, encoding_blob, created_at]]
        
        # Convert to dictionary format for backward compatibility
        faces_dict = {}
        for face_id, name, encoding_blob, created_at in face_rows:
            try:
                encoding = pickle.loads(encoding_blob)
                faces_dict[name] = encoding
                print(f"Loaded face: {name}, encoding shape: {encoding.shape}, type: {type(encoding)}")
            except Exception as e:
                print(f"Error deserializing encoding for {name}: {e}")
        
        print(f"Loaded {len(faces_dict)} faces from database")
        return faces_dict
    except Exception as e:
        print(f"Error loading faces from database: {e}")
        # Fallback to pickle file
        return load_faces_from_pickle()

def save_faces(data):
    """Save face encodings - now uses SQLite database"""
    try:
        face_db = get_face_database()
        saved_count = 0
        
        for name, encoding in data.items():
            if face_db.register_face(name, encoding):
                saved_count += 1
        
        print(f"Saved {saved_count}/{len(data)} faces to database")
        
        # Also export to pickle for compatibility
        face_db.export_faces_to_pickle(FACE_DB)
        
    except Exception as e:
        print(f"Error saving faces to database: {e}")
        # Fallback to pickle
        save_faces_to_pickle(data)

def find_face(face_encoding, known_faces=None, tolerance=0.6):
    """Find matching face - now uses database with enhanced matching"""
    try:
        face_db = get_face_database()
        result = face_db.find_face(face_encoding, tolerance=tolerance)
        
        if result:
            name, confidence = result
            return name
        else:
            return None
            
    except Exception as e:
        print(f"Error finding face in database: {e}")
        # Fallback to old method
        return find_face_legacy(face_encoding, known_faces, tolerance)

def start_face_session(name: str, table_id: str, session_token: str) -> bool:
    """Start a face session for table management"""
    try:
        face_db = get_face_database()
        return face_db.start_face_session(name, table_id, session_token)
    except Exception as e:
        print(f"Error starting face session: {e}")
        return False

def end_face_session(table_id: str = None, session_token: str = None) -> bool:
    """End face session - this is what gets called when table closes"""
    try:
        face_db = get_face_database()
        return face_db.end_face_session(table_id=table_id, session_token=session_token)
    except Exception as e:
        print(f"Error ending face session: {e}")
        return False

def get_face_database_info():
    """Get information about the face database"""
    try:
        face_db = get_face_database()
        stats = face_db.get_face_stats()
        all_faces = load_faces()  # Use the corrected load_faces function
        
        return {
            'exists': True,
            'path': face_db.db_path,
            'count': stats.get('total_faces', 0),
            'names': list(all_faces.keys()),
            'recent_logins': stats.get('total_logins', 0),
            'active_sessions': stats.get('active_sessions', 0),
            'top_user': stats.get('top_user', 'None')
        }
    except Exception as e:
        return {
            'exists': False,
            'path': '',
            'count': 0,
            'names': [],
            'error': str(e)
        }

def get_user_login_history(name: str):
    """Get login history for a specific user"""
    try:
        face_db = get_face_database()
        return face_db.get_user_history(name)
    except Exception as e:
        print(f"Error getting user history: {e}")
        return []

def cleanup_old_data(days: int = 7):
    """Cleanup old session data"""
    try:
        face_db = get_face_database()
        return face_db.cleanup_old_sessions(days)
    except Exception as e:
        print(f"Error cleaning up old data: {e}")
        return 0

# Legacy functions for backward compatibility
def load_faces_from_pickle():
    """Load faces from pickle file (legacy)"""
    if os.path.exists(FACE_DB):
        try:
            with open(FACE_DB, "rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, IOError) as e:
            print(f"Error loading face pickle: {e}")
            return {}
    return {}

def save_faces_to_pickle(data):
    """Save faces to pickle file (legacy)"""
    try:
        os.makedirs(os.path.dirname(FACE_DB), exist_ok=True)
        with open(FACE_DB, "wb") as f:
            pickle.dump(data, f)
        print(f"Saved {len(data)} faces to pickle")
    except (pickle.PickleError, IOError) as e:
        print(f"Error saving face pickle: {e}")

def find_face_legacy(face_encoding, known_faces, tolerance=0.6):
    """Find matching face using legacy method"""
    if not known_faces:
        print("No known faces to compare against")
        return None

    encodings = list(known_faces.values())
    names = list(known_faces.keys())

    print(f"Input encoding shape: {face_encoding.shape}, type: {type(face_encoding)}")
    print(f"Encoding range: min={face_encoding.min():.3f}, max={face_encoding.max():.3f}")

    # Calculate distances
    distances = face_recognition.face_distance(encodings, face_encoding)
    print(f"All distances: {distances}")
    
    # Find best match
    best_idx = distances.argmin()
    best_distance = distances[best_idx]
    best_name = names[best_idx]
    
    print(f"Best match: {best_name}, distance: {best_distance:.3f}, tolerance: {tolerance}")
    
    if best_distance <= tolerance:
        confidence = 1 - best_distance
        print(f"Legacy face match: {best_name} (confidence: {confidence:.3f})")
        return best_name
    else:
        print(f"No face match. Best distance: {best_distance:.3f}")
        return None

def reset_face_database():
    """Reset only sessions, keep face data intact"""
    try:
        face_db = get_face_database()
        
        # End all active sessions (but keep face data)
        success = face_db.end_face_session()  # Ends all active sessions
        
        print("✓ Face sessions reset (face data preserved)")
        return True
        
    except Exception as e:
        print(f"Error resetting face sessions: {e}")
        return False

def hard_reset_face_database():
    """Complete reset - delete all face data (admin only)"""
    try:
        face_db = get_face_database()
        
        # Delete database file completely
        if os.path.exists(face_db.db_path):
            os.remove(face_db.db_path)
            print("✓ Face database completely reset")
        
        # Also delete pickle file
        if os.path.exists(FACE_DB):
            os.remove(FACE_DB)
            print("✓ Legacy pickle file deleted")
        
        return True
        
    except Exception as e:
        print(f"Error hard resetting face database: {e}")
        return False
