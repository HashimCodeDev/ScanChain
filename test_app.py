#!/usr/bin/env python3
"""
Simple test script for ScanChain Flask app
"""
import os
import sys
import hashlib
import json
from datetime import datetime

def test_environment():
    """Test environment variables and dependencies"""
    print("🧪 Testing ScanChain Flask Environment")
    print("=" * 50)
    
    # Test environment variables
    required_vars = [
        'GREENFIELD_ADDRESS',
        'GREENFIELD_PRIVATE_KEY', 
        'CONTRACT_ADDRESS',
        'BSC_PRIVATE_KEY'
    ]
    
    print("📋 Environment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * 8}...{value[-4:] if len(value) > 8 else value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # Test imports
    print("\n📦 Testing Python Dependencies:")
    try:
        import flask
        print(f"  ✅ Flask: {flask.__version__}")
    except ImportError:
        print("  ❌ Flask: Not installed")
    
    try:
        import flask_cors
        print("  ✅ Flask-CORS: Available")
    except ImportError:
        print("  ❌ Flask-CORS: Not installed")
    
    try:
        import flask_jwt_extended
        print("  ✅ Flask-JWT-Extended: Available")
    except ImportError:
        print("  ❌ Flask-JWT-Extended: Not installed")
    
    try:
        import qrcode
        print("  ✅ QRCode: Available")
    except ImportError:
        print("  ❌ QRCode: Not installed")
    
    try:
        import web3
        print(f"  ✅ Web3: Available")
    except ImportError:
        print("  ❌ Web3: Not installed")
    
    # Test utility functions
    print("\n🔧 Testing Utility Functions:")
    
    # Test hash generation
    test_data = b"Hello ScanChain!"
    test_hash = hashlib.sha256(test_data).hexdigest()
    print(f"  ✅ SHA256 Hash: {test_hash[:16]}...")
    
    # Test JSON handling
    test_json = {"productId": "TEST123", "timestamp": datetime.utcnow().isoformat()}
    json_str = json.dumps(test_json)
    parsed_json = json.loads(json_str)
    print(f"  ✅ JSON Processing: {parsed_json['productId']}")
    
    print("\n🚀 Ready to start Flask server!")
    print("Run: python app.py")

if __name__ == '__main__':
    test_environment()