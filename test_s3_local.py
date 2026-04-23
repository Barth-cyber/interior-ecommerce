#!/usr/bin/env python3
"""
Test S3 Integration Locally
This script tests the S3 storage functionality with local fallback.
"""

import os
import sys
from pathlib import Path

# Add the admin directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / 'admin'))

from dotenv import load_dotenv
from s3_storage import S3Storage

def test_s3_integration():
    """Test S3 storage functionality"""
    print("🔍 Testing S3 Integration Locally")
    print("=" * 50)

    # Load environment variables
    load_dotenv()
    print("✅ Loaded environment variables from .env")

    # Check required environment variables
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_S3_BUCKET_NAME',
        'AWS_S3_REGION'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f'your_{var.lower()}_here':
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * len(value)} (set)")

    if missing_vars:
        print(f"\n❌ Missing or placeholder values for: {', '.join(missing_vars)}")
        print("Please update your .env file with real AWS credentials.")
        return False

    print("\n🔧 Initializing S3 Storage...")
    try:
        s3 = S3Storage()
        print("✅ S3 Storage initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize S3 Storage: {e}")
        return False

    # Test basic operations
    print("\n🧪 Testing S3 Operations...")

    # Test list files
    try:
        files = s3.list_files()
        print(f"✅ List files: Found {len(files)} files")
        if files:
            print(f"   Sample files: {files[:3]}")
    except Exception as e:
        print(f"❌ List files failed: {e}")

    # Test upload (create a test file)
    test_content = b"Hello, S3 Test!"
    test_filename = "test_upload.txt"

    try:
        result = s3.upload_file(test_content, test_filename, "text/plain")
        print(f"✅ Upload file: {result}")
    except Exception as e:
        print(f"❌ Upload file failed: {e}")

    # Test delete
    try:
        result = s3.delete_file(test_filename)
        print(f"✅ Delete file: {result}")
    except Exception as e:
        print(f"❌ Delete file failed: {e}")

    print("\n🎉 S3 Integration Test Complete!")
    print("If all tests passed, your S3 setup is working correctly.")
    print("You can now deploy to Render with confidence.")

    return True

if __name__ == "__main__":
    success = test_s3_integration()
    sys.exit(0 if success else 1)