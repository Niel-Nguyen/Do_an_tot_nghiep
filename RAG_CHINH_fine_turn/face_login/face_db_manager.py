#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Face Database Manager với SQLite
Quản lý dữ liệu face recognition với database persistent
"""

import sqlite3
import pickle
import numpy as np
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

class FaceDatabase:
    """Quản lý database SQLite cho face recognition"""
    
    def __init__(self, db_path: str = None):
        """Initialize face database"""
        if db_path is None:
            # Tạo database trong thư mục face_login
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, 'face_database.db')
            
        self.db_path = db_path
        self._init_database()
        print(f"Face database initialized: {self.db_path}")
    
    def _init_database(self):
        """Tạo database và tables nếu chưa tồn tại"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table lưu face encodings (persistent data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    encoding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Table lưu lịch sử login
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    face_id INTEGER NOT NULL,
                    table_id TEXT,
                    session_token TEXT,
                    success INTEGER DEFAULT 1,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (face_id) REFERENCES faces (id)
                )
            ''')
            
            # Table quản lý face sessions (temporary data - reset khi bàn đóng)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS face_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    face_id INTEGER NOT NULL,
                    table_id TEXT NOT NULL,
                    session_token TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (face_id) REFERENCES faces (id)
                )
            ''')
            
            conn.commit()
    
    def _get_connection(self):
        """Tạo connection đến database"""
        return sqlite3.connect(self.db_path)
    
    def register_face(self, name: str, encoding: np.ndarray) -> bool:
        """Đăng ký face mới hoặc cập nhật face existing"""
        try:
            print(f"Registering face: {name}")
            print(f"Encoding shape: {encoding.shape}, type: {type(encoding)}")
            print(f"Encoding range: min={encoding.min():.3f}, max={encoding.max():.3f}")
            
            # Serialize encoding
            encoding_blob = pickle.dumps(encoding)
            print(f"Serialized encoding size: {len(encoding_blob)} bytes")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if name already exists
                cursor.execute('SELECT id FROM faces WHERE name = ?', (name,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing face
                    cursor.execute('''
                        UPDATE faces 
                        SET encoding = ?, is_active = 1, created_at = CURRENT_TIMESTAMP
                        WHERE name = ?
                    ''', (encoding_blob, name))
                    print(f"Updated face data for: {name}")
                else:
                    # Insert new face
                    cursor.execute('''
                        INSERT INTO faces (name, encoding) 
                        VALUES (?, ?)
                    ''', (name, encoding_blob))
                    print(f"Registered new face: {name}")
                
                conn.commit()
                
                # Verify by reading back
                cursor.execute('SELECT encoding FROM faces WHERE name = ?', (name,))
                saved_blob = cursor.fetchone()[0]
                saved_encoding = pickle.loads(saved_blob)
                print(f"Verified saved encoding shape: {saved_encoding.shape}")
                print(f"Encodings match: {np.array_equal(encoding, saved_encoding)}")
                
                return True
                
        except Exception as e:
            print(f"Error registering face {name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def find_face(self, encoding: np.ndarray, tolerance: float = 0.6) -> Optional[Tuple[str, float]]:
        """Find matching face with enhanced accuracy and multiple validation layers"""
        try:
            import face_recognition
            
            # Get all faces from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, encoding FROM faces WHERE is_active = 1')
                rows = cursor.fetchall()
            
            if not rows:
                print("No faces found in database")
                return None

            names = []
            encodings = []
            face_ids = []
            
            for face_id, name, encoding_blob in rows:
                face_encoding = pickle.loads(encoding_blob)
                print(f"Loaded face: {name}, encoding shape: {face_encoding.shape}, type: {type(face_encoding)}")
                names.append(name)
                encodings.append(face_encoding)
                face_ids.append(face_id)
            
            print(f"Input encoding shape: {encoding.shape}, type: {type(encoding)}")
            print(f"Encoding range: min={encoding.min():.3f}, max={encoding.max():.3f}")
            
            # ENHANCED MATCHING ALGORITHM
            # 1. Calculate distances using face_recognition (Euclidean distance)
            distances = face_recognition.face_distance(encodings, encoding)
            print(f"All distances: {distances}")
            
            # 2. Find candidates within tolerance
            candidates = []
            for i, distance in enumerate(distances):
                if distance <= tolerance:
                    confidence = 1 - distance if distance < 1 else 0.1
                    candidates.append((i, names[i], distance, confidence))
            
            if not candidates:
                best_idx = distances.argmin()
                best_distance = distances[best_idx]
                print(f"No face match. Best distance: {best_distance:.3f} > tolerance: {tolerance}")
                return None
            
            # 3. Sort candidates by distance (best first)
            candidates.sort(key=lambda x: x[2])  # Sort by distance
            
            print(f"Found {len(candidates)} candidate(s) within tolerance:")
            for i, (idx, name, dist, conf) in enumerate(candidates):
                print(f"  {i+1}. {name}: distance={dist:.3f}, confidence={conf:.3f}")
            
            # 4. VALIDATION LAYERS FOR BEST CANDIDATE
            best_idx, best_name, best_distance, best_confidence = candidates[0]
            
            # Layer 1: Distance validation with stricter thresholds for quality
            quality_threshold = 0.4  # Stricter for high quality match
            if best_distance <= quality_threshold:
                print(f"✅ HIGH QUALITY MATCH: {best_name} (distance: {best_distance:.3f})")
                validation_passed = True
            elif best_distance <= 0.5:
                print(f"⚠️  MEDIUM QUALITY MATCH: {best_name} (distance: {best_distance:.3f})")
                validation_passed = True
            else:
                print(f"🔍 LOW QUALITY MATCH: {best_name} (distance: {best_distance:.3f})")
                # Continue with additional validation for low quality matches
                validation_passed = False
            
            # Layer 2: Enhanced Gap analysis with adaptive thresholds
            gap_validation_passed = True
            if len(candidates) > 1:
                second_best_distance = candidates[1][2]
                distance_gap = second_best_distance - best_distance
                
                # Adaptive minimum gap based on distance quality
                if best_distance <= 0.3:
                    min_gap = 0.05  # Very small gap OK for excellent matches
                elif best_distance <= 0.4:
                    min_gap = 0.08  # Small gap OK for good matches  
                else:
                    min_gap = 0.12  # Larger gap needed for poor matches
                
                if distance_gap < min_gap:
                    print(f"⚠️  AMBIGUOUS MATCH: Gap {distance_gap:.3f} < {min_gap} (threshold for distance {best_distance:.3f})")
                    # For ambiguous matches, only reject if both distance is high AND quality is poor
                    if best_distance > 0.4:
                        gap_validation_passed = False
                        print(f"⚠️  Gap validation failed for high distance match")
                    else:
                        print(f"✅ Gap validation passed due to low distance")
                else:
                    print(f"✅ CLEAR WINNER: Gap = {distance_gap:.3f} > {min_gap}")
            
            # Layer 3: Encoding quality validation
            encoding_quality_score = self._validate_encoding_quality(encoding)
            print(f"Input encoding quality score: {encoding_quality_score:.3f}")
            
            quality_validation_passed = True
            if encoding_quality_score < 0.3:
                print(f"⚠️  Poor input encoding quality: {encoding_quality_score:.3f}")
                if best_distance > 0.45:  # Only reject poor quality if distance also high
                    quality_validation_passed = False
                    print(f"⚠️  Quality validation failed for high distance match")
            
            # Final decision with multiple acceptance criteria
            accept_match = False
            
            # Criteria 1: High validation passed (good distance + good gap + good quality)
            if validation_passed and gap_validation_passed and quality_validation_passed:
                accept_match = True
                print(f"✅ ACCEPTED: All validations passed")
            
            # Criteria 2: Excellent distance (< 0.35) overrides other concerns
            elif best_distance <= 0.35:
                accept_match = True
                print(f"✅ ACCEPTED: Excellent distance {best_distance:.3f} overrides other issues")
            
            # Criteria 3: Good distance (< 0.4) + decent quality
            elif best_distance <= 0.4 and encoding_quality_score >= 0.5:
                accept_match = True
                print(f"✅ ACCEPTED: Good distance + decent quality")
            
            # Criteria 4: Reasonable distance (< 0.5) + clear winner + good quality
            elif best_distance <= 0.5 and gap_validation_passed and quality_validation_passed:
                accept_match = True
                print(f"✅ ACCEPTED: Reasonable distance + validations passed")
            
            if accept_match:
                # Update login stats
                self._update_login_stats(face_ids[best_idx], best_confidence)
                
                print(f"🎉 FACE MATCHED: {best_name} (distance: {best_distance:.3f}, confidence: {best_confidence:.3f})")
                return best_name, best_confidence
            else:
                print(f"❌ FINAL REJECTION: {best_name} (distance: {best_distance:.3f})")
                return None
                
        except Exception as e:
            print(f"Error finding face: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _validate_encoding_quality(self, encoding: np.ndarray) -> float:
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
            return 0.5  # Neutral score on error    def _update_login_stats(self, face_id: int, confidence: float):
        """Update login statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE faces 
                    SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                    WHERE id = ?
                ''', (face_id,))
                conn.commit()
        except Exception as e:
            print(f"Error updating login stats: {e}")
    
    def start_face_session(self, face_id: int, table_id: str, session_token: str) -> Optional[int]:
        """Bắt đầu face session cho table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # End any existing session for this face
                cursor.execute('''
                    UPDATE face_sessions 
                    SET is_active = 0 
                    WHERE face_id = ? AND is_active = 1
                ''', (face_id,))
                
                # Start new session
                cursor.execute('''
                    INSERT INTO face_sessions (face_id, table_id, session_token)
                    VALUES (?, ?, ?)
                ''', (face_id, table_id, session_token))
                
                session_id = cursor.lastrowid
                conn.commit()
                return session_id
                
        except Exception as e:
            print(f"Error starting face session: {e}")
            return None
    
    def end_face_session(self, face_id: int) -> bool:
        """Kết thúc face session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE face_sessions 
                    SET is_active = 0 
                    WHERE face_id = ? AND is_active = 1
                ''', (face_id,))
                
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows > 0
                
        except Exception as e:
            print(f"Error ending face session: {e}")
            return False
    
    def get_face_by_name(self, name: str) -> Optional[Tuple[int, str, np.ndarray]]:
        """Lấy face theo tên"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, encoding FROM faces WHERE name = ? AND is_active = 1', (name,))
                row = cursor.fetchone()
                
                if row:
                    face_id, face_name, encoding_blob = row
                    encoding = pickle.loads(encoding_blob)
                    return face_id, face_name, encoding
                
                return None
                
        except Exception as e:
            print(f"Error getting face by name: {e}")
            return None
    
    def get_all_faces(self) -> List[Tuple[int, str, bytes, str]]:
        """Lấy tất cả faces"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, encoding, created_at FROM faces WHERE is_active = 1')
                return cursor.fetchall()
                
        except Exception as e:
            print(f"Error getting all faces: {e}")
            return []
    
    def get_active_sessions(self) -> List[Tuple]:
        """Lấy tất cả sessions đang hoạt động"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT fs.id, fs.face_id, f.name, fs.table_id, fs.session_token, fs.started_at
                    FROM face_sessions fs
                    JOIN faces f ON fs.face_id = f.id
                    WHERE fs.is_active = 1
                ''')
                return cursor.fetchall()
                
        except Exception as e:
            print(f"Error getting active sessions: {e}")
            return []
    
    def add_login_history(self, face_id: int, table_id: str, session_token: str, success: bool = True):
        """Thêm lịch sử login"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO login_history (face_id, table_id, session_token, success)
                    VALUES (?, ?, ?, ?)
                ''', (face_id, table_id, session_token, int(success)))
                conn.commit()
                
        except Exception as e:
            print(f"Error adding login history: {e}")
    
    def get_recent_login_history(self, limit: int = 10) -> List[Tuple]:
        """Lấy lịch sử login gần đây"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT lh.id, f.name, lh.table_id, lh.session_token, lh.success, lh.login_time
                    FROM login_history lh
                    JOIN faces f ON lh.face_id = f.id
                    ORDER BY lh.login_time DESC
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
                
        except Exception as e:
            print(f"Error getting login history: {e}")
            return []
    
    def reset_sessions(self) -> bool:
        """Reset tất cả sessions (không xóa face data)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE face_sessions SET is_active = 0')
                conn.commit()
                print("All face sessions reset")
                return True
                
        except Exception as e:
            print(f"Error resetting sessions: {e}")
            return False
    
    def hard_reset(self) -> bool:
        """Xóa tất cả dữ liệu (faces, sessions, history)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM face_sessions')
                cursor.execute('DELETE FROM login_history')  
                cursor.execute('DELETE FROM faces')
                conn.commit()
                print("All face data deleted")
                return True
                
        except Exception as e:
            print(f"Error hard resetting database: {e}")
            return False
    
    def _update_login_stats(self, face_id: int, confidence: float) -> None:
        """Update login statistics for a face"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update face login stats
                cursor.execute('''
                    UPDATE faces 
                    SET last_login = CURRENT_TIMESTAMP,
                        login_count = login_count + 1 
                    WHERE id = ?
                ''', (face_id,))
                
                # Add to login history
                cursor.execute('''
                    INSERT INTO login_history (face_id, success, login_time)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                ''', (face_id,))
                
                conn.commit()
                print(f"Updated login stats for face_id {face_id}")
                
        except Exception as e:
            print(f"Error updating login stats: {e}")
    
    def get_face_stats(self) -> Dict[str, Any]:
        """Lấy thống kê database"""
        try:
            stats = {
                'total_faces': 0,
                'total_logins': 0,
                'successful_logins': 0,
                'active_sessions': 0,
                'top_user': None,
                'faces': []
            }
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count faces
                cursor.execute('SELECT COUNT(*) FROM faces WHERE is_active = 1')
                stats['total_faces'] = cursor.fetchone()[0]
                
                # Count logins
                cursor.execute('SELECT COUNT(*), SUM(success) FROM login_history')
                total_logins, successful = cursor.fetchone()
                stats['total_logins'] = total_logins or 0
                stats['successful_logins'] = successful or 0
                
                # Count active sessions
                cursor.execute('SELECT COUNT(*) FROM face_sessions WHERE is_active = 1')
                stats['active_sessions'] = cursor.fetchone()[0]
                
                # Get top user
                cursor.execute('''
                    SELECT name, login_count FROM faces 
                    WHERE is_active = 1 AND login_count > 0
                    ORDER BY login_count DESC LIMIT 1
                ''')
                top_result = cursor.fetchone()
                if top_result:
                    stats['top_user'] = f"{top_result[0]} ({top_result[1]} logins)"
                else:
                    stats['top_user'] = "None"
                
                # Get face list
                cursor.execute('SELECT id, name, created_at, login_count FROM faces WHERE is_active = 1')
                for row in cursor.fetchall():
                    stats['faces'].append({
                        'id': row[0],
                        'name': row[1], 
                        'created_at': row[2],
                        'login_count': row[3]
                    })
            
            return stats
            
        except Exception as e:
            print(f"Error getting face stats: {e}")
            return {
                'total_faces': 0,
                'total_logins': 0,
                'successful_logins': 0,
                'active_sessions': 0,
                'top_user': 'Error',
                'faces': []
            }
    
    def delete_face_by_name(self, name: str) -> bool:
        """Xóa khuôn mặt theo tên"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Kiểm tra face có tồn tại không
                cursor.execute('SELECT id FROM faces WHERE name = ?', (name,))
                face_row = cursor.fetchone()
                
                if not face_row:
                    print(f"❌ Face '{name}' not found")
                    return False
                
                face_id = face_row[0]
                
                # Xóa login history trước (foreign key constraint)
                cursor.execute('DELETE FROM login_history WHERE face_id = ?', (face_id,))
                deleted_history = cursor.rowcount
                
                # Xóa face sessions
                cursor.execute('DELETE FROM face_sessions WHERE face_id = ?', (face_id,))
                deleted_sessions = cursor.rowcount
                
                # Xóa face chính
                cursor.execute('DELETE FROM faces WHERE id = ?', (face_id,))
                deleted_face = cursor.rowcount
                
                conn.commit()
                
                if deleted_face > 0:
                    print(f"✅ Deleted face '{name}':")
                    print(f"  - Face record: {deleted_face}")
                    print(f"  - Login history: {deleted_history}")
                    print(f"  - Sessions: {deleted_sessions}")
                    return True
                else:
                    print(f"❌ Failed to delete face '{name}'")
                    return False
                    
        except Exception as e:
            print(f"❌ Error deleting face '{name}': {e}")
            return False
    
    def delete_face_by_id(self, face_id: int) -> bool:
        """Xóa khuôn mặt theo ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Lấy tên face trước khi xóa
                cursor.execute('SELECT name FROM faces WHERE id = ?', (face_id,))
                face_row = cursor.fetchone()
                
                if not face_row:
                    print(f"❌ Face ID {face_id} not found")
                    return False
                
                name = face_row[0]
                
                # Xóa login history trước
                cursor.execute('DELETE FROM login_history WHERE face_id = ?', (face_id,))
                deleted_history = cursor.rowcount
                
                # Xóa face sessions
                cursor.execute('DELETE FROM face_sessions WHERE face_id = ?', (face_id,))
                deleted_sessions = cursor.rowcount
                
                # Xóa face chính
                cursor.execute('DELETE FROM faces WHERE id = ?', (face_id,))
                deleted_face = cursor.rowcount
                
                conn.commit()
                
                if deleted_face > 0:
                    print(f"✅ Deleted face ID {face_id} ('{name}'):")
                    print(f"  - Face record: {deleted_face}")
                    print(f"  - Login history: {deleted_history}")
                    print(f"  - Sessions: {deleted_sessions}")
                    return True
                else:
                    print(f"❌ Failed to delete face ID {face_id}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error deleting face ID {face_id}: {e}")
            return False
    
    def delete_all_faces(self, confirm: bool = False) -> bool:
        """Xóa tất cả khuôn mặt (cần xác nhận)"""
        if not confirm:
            print("⚠️  WARNING: This will delete ALL face data!")
            print("To confirm, call with confirm=True")
            return False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Đếm trước khi xóa
                cursor.execute('SELECT COUNT(*) FROM faces')
                total_faces = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM login_history')
                total_history = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM face_sessions')
                total_sessions = cursor.fetchone()[0]
                
                if total_faces == 0:
                    print("ℹ️  No faces to delete")
                    return True
                
                # Xóa tất cả login history
                cursor.execute('DELETE FROM login_history')
                
                # Xóa tất cả face sessions
                cursor.execute('DELETE FROM face_sessions')
                
                # Xóa tất cả faces
                cursor.execute('DELETE FROM faces')
                
                # Reset auto-increment
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="faces"')
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="login_history"')
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="face_sessions"')
                
                conn.commit()
                
                print(f"🗑️  DELETED ALL FACE DATA:")
                print(f"  - Faces: {total_faces}")
                print(f"  - Login history: {total_history}")
                print(f"  - Sessions: {total_sessions}")
                print("  - Auto-increment counters reset")
                
                return True
                
        except Exception as e:
            print(f"❌ Error deleting all faces: {e}")
            return False
    
    def deactivate_face(self, name: str) -> bool:
        """Deactivate face (soft delete) thay vì xóa hẳn"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('UPDATE faces SET is_active = 0 WHERE name = ?', (name,))
                updated = cursor.rowcount
                
                if updated > 0:
                    # Xóa active sessions
                    cursor.execute('DELETE FROM face_sessions WHERE face_id IN (SELECT id FROM faces WHERE name = ?)', (name,))
                    
                    conn.commit()
                    print(f"✅ Deactivated face '{name}' (soft delete)")
                    return True
                else:
                    print(f"❌ Face '{name}' not found")
                    return False
                    
        except Exception as e:
            print(f"❌ Error deactivating face '{name}': {e}")
            return False
    
    def reactivate_face(self, name: str) -> bool:
        """Reactivate a deactivated face"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('UPDATE faces SET is_active = 1 WHERE name = ?', (name,))
                updated = cursor.rowcount
                
                if updated > 0:
                    conn.commit()
                    print(f"✅ Reactivated face '{name}'")
                    return True
                else:
                    print(f"❌ Face '{name}' not found")
                    return False
                    
        except Exception as e:
            print(f"❌ Error reactivating face '{name}': {e}")
            return False
    
    def clear_login_history(self, face_name: str = None) -> bool:
        """Xóa lịch sử login (tất cả hoặc của một face cụ thể)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if face_name:
                    # Xóa history của một face cụ thể
                    cursor.execute('''
                        DELETE FROM login_history 
                        WHERE face_id IN (SELECT id FROM faces WHERE name = ?)
                    ''', (face_name,))
                    deleted = cursor.rowcount
                    print(f"🗑️  Cleared login history for '{face_name}': {deleted} records")
                else:
                    # Xóa tất cả history
                    cursor.execute('SELECT COUNT(*) FROM login_history')
                    total = cursor.fetchone()[0]
                    
                    cursor.execute('DELETE FROM login_history')
                    cursor.execute('DELETE FROM sqlite_sequence WHERE name="login_history"')
                    
                    print(f"🗑️  Cleared all login history: {total} records")
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ Error clearing login history: {e}")
            return False

# Global instance để dùng chung
_face_database_instance = None

def get_face_database() -> FaceDatabase:
    """Singleton pattern để lấy database instance"""
    global _face_database_instance
    if _face_database_instance is None:
        _face_database_instance = FaceDatabase()
    return _face_database_instance

if __name__ == "__main__":
    # Test basic functionality
    db = FaceDatabase()
    
    # Test register
    import numpy as np
    test_encoding = np.random.random(128)
    
    result = db.register_face("test_user", test_encoding)
    print(f"Register result: {result}")
    
    # Test find
    result = db.find_face(test_encoding)
    print(f"Find result: {result}")
    
    # Test stats
    stats = db.get_face_stats()
    print(f"Stats: {stats}")
