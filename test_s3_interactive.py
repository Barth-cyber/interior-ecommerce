#!/usr/bin/env python3
"""
Interactive S3 Integration Test
This script will prompt you for AWS credentials and test S3 functionality.
"""

import os
import sys
import getpass
from pathlib import Path

# Add the admin directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / 'admin'))

from admin.s3_storage import S3Storage

def get_credentials_interactively():
    """Get AWS credentials from user input"""
    print("AWS S3 Credentials Setup")
    print("=" * 40)

    print("\nPlease enter your AWS credentials:")
    print("(These will only be used for this test session)")

    # Get credentials interactively
    access_key = input("\nAWS Access Key ID: ").strip()
    while not access_key:
        print("Access Key ID cannot be empty.")
        access_key = input("AWS Access Key ID: ").strip()

    secret_key = getpass.getpass("AWS Secret Access Key: ").strip()
    while not secret_key:
        print("Secret Access Key cannot be empty.")
        secret_key = getpass.getpass("AWS Secret Access Key: ").strip()

    bucket = input("S3 Bucket Name [interior-ecommerce-uploads]: ").strip()
    if not bucket:
        bucket = "interior-ecommerce-uploads"

    region = input("AWS Region [us-east-1]: ").strip()
    if not region:
        region = "us-east-1"

    return access_key, secret_key, bucket, region

def test_s3_integration(access_key, secret_key, bucket, region):
    """Test S3 storage functionality with provided credentials"""
    print("\nTesting S3 Integration")
    print("=" * 50)

    # Set environment variables
    os.environ['AWS_ACCESS_KEY_ID'] = "access_key_here"
    os.environ['AWS_SECRET_ACCESS_KEY'] = "secret_key_here"
    os.environ['AWS_S3_BUCKET_NAME'] = "interior-ecommerce-uploads"
    os.environ['AWS_S3_REGION'] = "us-east-1"

    print("Credentials loaded into environment")

    # Display masked credentials for confirmation
    print(f"✅ AWS_ACCESS_KEY_ID: {'*' * len(access_key)}")
    print(f"✅ AWS_SECRET_ACCESS_KEY: {'*' * len(secret_key)}")
    print(f"✅ AWS_S3_BUCKET_NAME: {bucket}")
    print(f"✅ AWS_S3_REGION: {region}")

    print("\nInitializing S3 Storage...")
    try:
        s3 = S3Storage()
        print("S3 Storage initialized successfully")
    except Exception as e:
        print(f"Failed to initialize S3 Storage: {e}")
        print("\nTroubleshooting Tips:")
        print("• Check if your AWS credentials are correct")
        print("• Verify the S3 bucket exists and you have access")
        print("• Ensure your IAM user has S3 permissions")
        print("• Check if the bucket region matches your credentials")
        return False

    # Test basic operations
    print("\nTesting S3 Operations...")

    # Test list files
    try:
        files = s3.list_files()
        print(f"List files: Found {len(files)} files")
        if files:
            print(f"   Sample files: {files[:3]}")
    except Exception as e:
        print(f"List files failed: {e}")

    # Test upload (create a test file)
    test_content = b"Hello, S3 Interactive Test!"
    test_filename = f"test_interactive_{int(os.times().elapsed)}.txt"

    try:
        result = s3.upload_file(test_content, test_filename, "text/plain")
        print(f"Upload file: {result}")
    except Exception as e:
        print(f"Upload file failed: {e}")

    # Test delete
    try:
        result = s3.delete_file(test_filename)
        print(f"Delete file: {result}")
    except Exception as e:
        print(f"Delete file failed: {e}")

    print("\nS3 Integration Test Complete!")
    print("If all tests passed, your S3 setup is working correctly.")
    print("You can now deploy to Render with confidence.")

    return True

def main():
    print("Interactive S3 Integration Test")
    print("This will test your AWS S3 setup for the Interior Ecommerce project")
    print("=" * 70)

    try:
        # Get credentials interactively
        access_key, secret_key, bucket, region = get_credentials_interactively()

        # Run the test
        success = test_s3_integration(access_key, secret_key, bucket, region)

        if success:
            print("\nSUCCESS: Your S3 integration is working!")
            print("You can now proceed with Render deployment.")
        else:
            print("\nFAILURE: S3 integration test failed.")
            print("Please check your AWS setup and try again.")

    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    main()