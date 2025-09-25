#!/usr/bin/env python3
"""
Test script for DCellar bucket upload functionality
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_dcellar_upload():
    """Test the /upload endpoint for DCellar bucket uploads"""
    
    # Server URL
    base_url = f"http://localhost:{os.getenv('PORT', 5000)}"
    upload_url = f"{base_url}/upload"
    
    # Create a test file
    test_content = b"This is a test file for DCellar bucket upload"
    test_filename = "test_dcellar_upload.txt"
    
    # Prepare the file upload
    files = {
        'file': (test_filename, test_content, 'text/plain')
    }
    
    try:
        print(f"Testing DCellar upload to: {upload_url}")
        print(f"Test file: {test_filename} ({len(test_content)} bytes)")
        
        # Make the upload request
        response = requests.post(upload_url, files=files, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Upload successful!")
                print(f"   Greenfield URL: {result.get('greenfieldUrl')}")
                print(f"   File size: {result.get('fileSize')} bytes")
                print(f"   Content type: {result.get('contentType')}")
            else:
                print("❌ Upload failed:", result.get('error'))
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the Flask server is running")
        print("   Run: python app.py")
    except Exception as e:
        print(f"❌ Test error: {e}")

def test_health_check():
    """Test the health check endpoint"""
    
    base_url = f"http://localhost:{os.getenv('PORT', 5000)}"
    health_url = f"{base_url}/api/health"
    
    try:
        print(f"Testing health check: {health_url}")
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Server is healthy")
            print(f"   Status: {result.get('status')}")
            print(f"   Version: {result.get('version')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("🧪 Testing DCellar Upload Functionality")
    print("=" * 50)
    
    # Test health check first
    test_health_check()
    print()
    
    # Test upload
    test_dcellar_upload()
    
    print("\n" + "=" * 50)
    print("Test completed!")