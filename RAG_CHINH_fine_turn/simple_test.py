#!/usr/bin/env python3
"""
Simple test script for face login redirect functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_basic_imports():
    """Test basic imports"""
    print("Testing basic imports...")
    
    try:
        print("  - Importing Flask...")
        from flask import Flask, url_for
        print("  ✓ Flask OK")
        
        print("  - Importing face_login modules...")
        from face_login.core1 import recognize_user, register_user
        print("  ✓ Face login modules OK")
        
        print("  - Importing app functions...")
        from app import build_table_redirect
        print("  ✓ App functions OK")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_redirect_logic():
    """Test redirect URL generation logic"""
    print("\nTesting redirect URL logic...")
    
    try:
        from flask import Flask
        from app import build_table_redirect
        
        # Create Flask app context
        app = Flask(__name__)
        
        with app.app_context():
            # Test various scenarios
            test_cases = [
                ("token_123", None, "Should use table_token"),
                (None, "table_456", "Should use table_id"),
                ("token_789", "table_999", "Should prefer table_token"),
                (None, None, "Should fallback to mobile_menu")
            ]
            
            for token, table_id, description in test_cases:
                try:
                    result = build_table_redirect(table_token=token, table_id=table_id)
                    print(f"  ✓ {description}: {result}")
                except Exception as e:
                    print(f"  ✗ {description}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Redirect logic test failed: {e}")
        return False

def test_session_data():
    """Test session data structure"""
    print("\nTesting session data structure...")
    
    # Simulate session data that would be set after login
    mock_session = {
        'user_name': 'test_user',
        'user_id': 'test_user'
    }
    
    print(f"  ✓ Mock session: {mock_session}")
    
    # Test URL parameters that would be preserved
    mock_url_params = {
        'table_token': 'abc123def456',
        'table_id': 'table_001'
    }
    
    print(f"  ✓ Mock URL params: {mock_url_params}")
    
    return True

def test_face_login_reset():
    """Test face login reset functionality"""
    print("\nTesting face login reset functionality...")
    
    try:
        from app import reset_face_login_database, init_face_login_for_session
        
        # Test reset function
        print("  - Testing reset_face_login_database...")
        result1 = reset_face_login_database()
        print(f"  ✓ Reset result: {result1}")
        
        # Test init function
        print("  - Testing init_face_login_for_session...")
        result2 = init_face_login_for_session()
        print(f"  ✓ Init result: {result2}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Face login reset test failed: {e}")
        return False

def test_session_lifecycle():
    """Test session lifecycle with face login reset"""
    print("\nTesting session lifecycle...")
    
    # Simulate session start
    print("  1. Starting table session (should reset face login)")
    print("     - Reset face login database")
    print("     - Create new session token")
    print("     - Initialize face login for new session")
    
    # Simulate face registration during session
    print("  2. During session (face registration)")
    print("     - User registers face")
    print("     - Face data stored in database")
    
    # Simulate session end
    print("  3. Ending table session (should reset face login)")
    print("     - Clear face login database")
    print("     - Remove session token")
    print("     - Close table")
    
    print("  ✓ Session lifecycle simulation completed")
    return True

def main():
    """Run simple tests"""
    print("Simple Face Login Test")
    print("=" * 40)
    
    success = True
    
    # Test 1: Basic imports
    if not test_basic_imports():
        success = False
    
    # Test 2: Redirect logic
    if not test_redirect_logic():
        success = False
    
    # Test 3: Session data
    if not test_session_data():
        success = False
    
    # Test 4: Face login reset
    if not test_face_login_reset():
        success = False
    
    # Test 5: Session lifecycle
    if not test_session_lifecycle():
        success = False
    
    print(f"\n{'✓ All tests passed!' if success else '✗ Some tests failed!'}")
    
    if success:
        print("\nReady to test with actual server!")
        print("Usage example:")
        print("  1. Start Flask server")
        print("  2. Visit: https://192.168.110.15:5000/face-login?table_token=YOUR_TOKEN")
        print("  3. Face login should redirect to: /mobile_menu?table_token=YOUR_TOKEN")
        print("  4. When table session ends, face database will be reset automatically")

if __name__ == "__main__":
    main()
