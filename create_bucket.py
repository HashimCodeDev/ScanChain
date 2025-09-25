#!/usr/bin/env python3
"""
Script to create BNB Greenfield bucket for ScanChain
"""

import os
import requests
import json
from dotenv import load_dotenv

def create_greenfield_bucket():
    """Create bucket on BNB Greenfield Testnet"""
    
    # Load environment variables
    load_dotenv()
    
    bucket_name = os.getenv('GREENFIELD_BUCKET_NAME', 'bnbhack1')
    account_address = os.getenv('GREENFIELD_ACCOUNT_ADDRESS')
    
    if not account_address:
        print("❌ GREENFIELD_ACCOUNT_ADDRESS not configured in .env")
        return False
    
    # Storage Provider endpoints
    sp_endpoints = [
        'https://gnfd-testnet-sp1.bnbchain.org',
        'https://gnfd-testnet-sp2.bnbchain.org',
        'https://gnfd-testnet-sp3.bnbchain.org'
    ]
    
    print(f"🪣 Creating bucket: {bucket_name}")
    print(f"👤 Account: {account_address}")
    
    for sp_endpoint in sp_endpoints:
        try:
            print(f"\n🔄 Trying Storage Provider: {sp_endpoint}")
            
            # Method 1: Try admin API
            create_url = f"{sp_endpoint}/greenfield/admin/v1/create-bucket"
            
            payload = {
                'bucket_name': bucket_name,
                'creator': account_address,
                'visibility': 'VISIBILITY_TYPE_PUBLIC_READ',
                'payment_address': account_address
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Gnfd-User-Address': account_address,
                'X-Gnfd-App-Domain': 'scanchain.app'
            }
            
            response = requests.post(
                create_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            print(f"   Admin API response: {response.status_code}")
            
            if response.status_code in [200, 201, 202]:
                print(f"✅ Bucket created successfully via {sp_endpoint}")
                return True
            elif response.status_code == 409:
                print(f"ℹ️  Bucket already exists")
                return True
            else:
                print(f"   Response: {response.text[:200]}")
            
            # Method 2: Try direct bucket creation
            bucket_url = f"{sp_endpoint}/greenfield/storage/v1/bucket"
            
            bucket_payload = {
                'bucket_name': bucket_name,
                'visibility': 1,  # Public read
                'payment_address': account_address,
                'primary_sp_address': account_address
            }
            
            response2 = requests.post(
                bucket_url,
                json=bucket_payload,
                headers=headers,
                timeout=30
            )
            
            print(f"   Direct API response: {response2.status_code}")
            
            if response2.status_code in [200, 201, 202]:
                print(f"✅ Bucket created successfully via direct API")
                return True
            elif response2.status_code == 409:
                print(f"ℹ️  Bucket already exists")
                return True
            else:
                print(f"   Response: {response2.text[:200]}")
                
        except Exception as e:
            print(f"   Error with {sp_endpoint}: {e}")
            continue
    
    print(f"\n❌ Failed to create bucket on all Storage Providers")
    print(f"💡 The app will use local mock storage instead")
    return False

def check_bucket_exists():
    """Check if bucket already exists"""
    
    load_dotenv()
    
    bucket_name = os.getenv('GREENFIELD_BUCKET_NAME', 'bnbhack1')
    account_address = os.getenv('GREENFIELD_ACCOUNT_ADDRESS')
    
    sp_endpoint = 'https://gnfd-testnet-sp1.bnbchain.org'
    
    try:
        bucket_url = f"{sp_endpoint}/greenfield/storage/v1/bucket-meta/{bucket_name}"
        response = requests.get(bucket_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Bucket '{bucket_name}' exists and is accessible")
            return True
        elif response.status_code == 404:
            print(f"❌ Bucket '{bucket_name}' not found")
            return False
        else:
            print(f"⚠️  Bucket status unclear: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking bucket: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BNB Greenfield Bucket Setup")
    print("=" * 40)
    
    # Check if bucket exists
    if check_bucket_exists():
        print("\n✅ Bucket is ready!")
    else:
        print("\n🔧 Creating bucket...")
        if create_greenfield_bucket():
            print("\n✅ Setup complete!")
        else:
            print("\n⚠️  Bucket creation failed, but app will work with local storage")
    
    print("\n🔍 Testing upload functionality...")
    
    # Test the service
    try:
        from services.greenfield_service import GreenfieldService
        service = GreenfieldService()
        status = service.get_status()
        
        print(f"Service mode: {status['mode']}")
        print(f"Bucket: {status['bucket']}")
        print(f"Ready: {status['ready']}")
        
        # Test upload with small file
        test_data = b"Hello BNB Greenfield!"
        test_result = service.upload_file(test_data, "test.txt", "text/plain")
        
        if test_result:
            print(f"✅ Test upload successful: {test_result}")
        else:
            print("❌ Test upload failed")
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
    
    print("\n🎉 Setup complete! You can now upload files.")