#!/usr/bin/env python3
"""
Manual S3 Integration Test
Run this script with your AWS credentials to test S3 functionality.
"""

import os
import sys
import argparse
from pathlib import Path
from io import BytesIO

# Add the admin directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / 'admin'))

from s3_storage import S3Storage

def test_s3_integration(access_key=None, secret_key=None, bucket=None, region=None):
    """Test S3 storage functionality with provided credentials"""
    print("🔍 Manual S3 Integration Test")
    print("=" * 50)

    # Set environment variables from arguments if provided
    if access_key:
        os.environ['AWS_ACCESS_KEY_ID'] = access_key
        print("✅ AWS_ACCESS_KEY_ID set from argument")
    if secret_key:
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        print("✅ AWS_SECRET_ACCESS_KEY set from argument")
    if bucket:
        os.environ['AWS_S3_BUCKET_NAME'] = bucket
        print("✅ AWS_S3_BUCKET_NAME set from argument")
    if region:
        os.environ['AWS_S3_REGION'] = region
        print("✅ AWS_S3_REGION set from argument")

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
        if not value:
            missing_vars.append(var)
        else:
            masked_value = '*' * len(value) if var != 'AWS_S3_REGION' and var != 'AWS_S3_BUCKET_NAME' else value
            print(f"✅ {var}: {masked_value}")

    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please provide them via command line arguments or set them in your environment.")
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
    test_content = b"Hello, S3 Manual Test!"
    test_filename = "test_manual_upload.txt"

    try:
        result = s3.upload_file(__import__("io").BytesIO(test_content), test_filename, "text/plain")
        print(f"✅ Upload file: {result}")
    except Exception as e:
        print(f"❌ Upload file failed: {e}")

    # Test delete
    try:
        result = s3.delete_file(test_filename)
        print(f"✅ Delete file: {result}")
    except Exception as e:
        print(f"❌ Delete file failed: {e}")

    print("\n🎉 Manual S3 Integration Test Complete!")
    print("If all tests passed, your S3 setup is working correctly.")
    print("You can now deploy to Render with confidence.")

    return True

def main():
    parser = argparse.ArgumentParser(description='Test S3 integration with AWS credentials')
    parser.add_argument('--access-key', help='AWS Access Key ID')
    parser.add_argument('--secret-key', help='AWS Secret Access Key')
    parser.add_argument('--bucket', help='S3 Bucket Name', default='interior-ecommerce-uploads')
    parser.add_argument('--region', help='AWS Region', default='us-east-1')

    args = parser.parse_args()

    success = test_s3_integration(
        access_key=args.access_key,
        secret_key=args.secret_key,
        bucket=args.bucket,
        region=args.region
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()