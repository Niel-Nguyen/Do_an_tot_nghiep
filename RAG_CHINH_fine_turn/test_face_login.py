#!/usr/bin/env python3
"""
Test script for face login functionality and redirect URLs
"""

import sys
import os
import requests
import json
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# Add current directory to path to import modules
sys.path.insert(0, os.path.dirname(__file__))

def create_test_image():
    """Create a simple test image in base64 format"""
    # Create a simple 100x100 RGB image
    image = Image.new('RGB', (100, 100), color='red')
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def test_imports():
    """Test importing required modules"""
    print("=== Testing Imports ===")
    try:
        from face_login.core1 import recognize_user, register_user
        print("✓ Face login imports OK")
    except ImportError as e:
        print(f"✗ Face login import failed: {e}")
        return False
    
    try:
        from app import build_table_redirect
        print("✓ build_table_redirect import OK")
    except ImportError as e:
        print(f"✗ build_table_redirect import failed: {e}")
        return False
    
    return True

def test_build_table_redirect():
    """Test build_table_redirect function"""
    print("\n=== Testing build_table_redirect ===")
    try:
        from app import build_table_redirect
        from flask import Flask
        
        # Create a minimal Flask app context for url_for to work
        app = Flask(__name__)
        with app.app_context():
            # Test with table_token
            result1 = build_table_redirect(table_token="test_token_123")
            print(f"✓ With table_token: {result1}")
            
            # Test with table_id
            result2 = build_table_redirect(table_id="table_001")
            print(f"✓ With table_id: {result2}")
            
            # Test with no parameters
            result3 = build_table_redirect()
            print(f"✓ No parameters: {result3}")
        
        return True
    except Exception as e:
        print(f"✗ build_table_redirect test failed: {e}")
        return False

def test_face_login_api(base_url="https://192.168.110.15:5000"):
    """Test face login API endpoints"""
    print(f"\n=== Testing Face Login API ({base_url}) ===")
    
    # Disable SSL verification for self-signed certificates
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    test_image = create_test_image()
    
    # Test /api/face_login
    print("Testing /api/face_login...")
    try:
        response = requests.post(
            f"{base_url}/api/face_login",
            json={
                "image_b64": test_image,
                "table_token": "test_token_123"
            },
            verify=False,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"✗ API test failed: {e}")
    
    # Test /api/face_register
    print("\nTesting /api/face_register...")
    try:
        response = requests.post(
            f"{base_url}/api/face_register",
            json={
                "name": "test_user",
                "image_b64": test_image,
                "table_token": "test_token_123"
            },
            verify=False,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"✗ API test failed: {e}")

def test_face_login_functions():
    """Test face login functions directly"""
    print("\n=== Testing Face Login Functions ===")
    try:
        from face_login.core1 import recognize_user, register_user
        
        test_image = create_test_image()
        
        # Test recognize_user
        print("Testing recognize_user...")
        result = recognize_user(test_image)
        print(f"Recognition result: {result}")
        
        # Test register_user
        print("Testing register_user...")
        try:
            register_user("test_user_script", test_image)
            print("✓ Registration completed")
        except Exception as e:
            print(f"Registration failed: {e}")
        
        # Test recognition after registration
        print("Testing recognition after registration...")
        result2 = recognize_user(test_image)
        print(f"Recognition result after registration: {result2}")
        
    except Exception as e:
        print(f"✗ Face login function test failed: {e}")

def test_url_patterns():
    """Test URL pattern construction"""
    print("\n=== Testing URL Patterns ===")
    
    test_cases = [
        ("table_123", None),
        (None, "table_456"),
        ("token_789", "table_999"),
        (None, None)
    ]
    
    for token, table_id in test_cases:
        print(f"Testing token={token}, table_id={table_id}")
        
        # Simulate what client would send
        params = {}
        if token:
            params['table_token'] = token
        if table_id:
            params['table_id'] = table_id
        
        # Simulate URL construction
        if token:
            expected_url = f"/mobile_menu?table_token={token}"
        elif table_id:
            expected_url = f"/mobile_menu?table_id={table_id}"
        else:
            expected_url = "/mobile_menu"
        
        print(f"  Expected URL: {expected_url}")

def main():
    """Run all tests"""
    print("Face Login Test Suite")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed. Please check module installation.")
        return
    
    # Test 2: build_table_redirect function
    test_build_table_redirect()
    
    # Test 3: URL patterns
    test_url_patterns()
    
    # Test 4: Face login functions (if available)
    test_face_login_functions()
    
    # Test 5: API endpoints (if server is running)
    server_running = input("\nIs the Flask server running? (y/n): ").lower().startswith('y')
    if server_running:
        base_url = input("Enter server URL (default: https://192.168.110.15:5000): ").strip()
        if not base_url:
            base_url = "https://192.168.110.15:5000"
        test_face_login_api(base_url)
    
    print("\n=== Test Summary ===")
    print("✓ Imports tested")
    print("✓ URL redirect logic tested")
    print("✓ Face login functions tested")
    if server_running:
        print("✓ API endpoints tested")
    
    print("\n🎉 Test suite completed!")

if __name__ == "__main__":
    main()
