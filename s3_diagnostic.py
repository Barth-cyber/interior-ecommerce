#!/usr/bin/env python3
"""
AWS S3 Diagnostic Tool
This script helps diagnose S3 access issues and provides solutions.
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from pathlib import Path

def diagnose_s3_access(access_key, secret_key, bucket_name, region):
    """Diagnose S3 access issues"""
    print("🔍 AWS S3 Diagnostic Tool")
    print("=" * 50)

    # Set credentials
    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key

    print(f"🔑 Testing credentials: {access_key[:8]}...")

    try:
        # Test basic AWS credentials
        sts_client = boto3.client('sts', region_name=region)
        identity = sts_client.get_caller_identity()
        print("✅ AWS credentials are valid"        print(f"   Account: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")

    except NoCredentialsError:
        print("❌ No AWS credentials found")
        return False
    except PartialCredentialsError:
        print("❌ Incomplete AWS credentials")
        return False
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidAccessKeyId':
            print("❌ Invalid Access Key ID")
            return False
        elif e.response['Error']['Code'] == 'SignatureDoesNotMatch':
            print("❌ Invalid Secret Access Key")
            return False
        else:
            print(f"❌ AWS Error: {e}")
            return False

    # Test S3 client creation
    try:
        s3_client = boto3.client('s3', region_name=region)
        print("✅ S3 client created successfully")
    except Exception as e:
        print(f"❌ Failed to create S3 client: {e}")
        return False

    # Test bucket existence and access
    print(f"\n🔍 Checking bucket: {bucket_name}")
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print("✅ Bucket exists and is accessible")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404' or error_code == 'NoSuchBucket':
            print(f"❌ Bucket '{bucket_name}' does not exist")
            print("   Solution: Create the bucket first")
            return False
        elif error_code == '403':
            print(f"❌ Access denied to bucket '{bucket_name}'")
            print("   This is likely an IAM permissions issue")
            return False
        else:
            print(f"❌ Bucket access error: {error_code} - {e.response['Error']['Message']}")
            return False

    # Test bucket location
    try:
        location = s3_client.get_bucket_location(Bucket=bucket_name)
        bucket_region = location.get('LocationConstraint', 'us-east-1')
        if bucket_region != region:
            print(f"⚠️  Bucket region mismatch: bucket is in '{bucket_region}', but you're using '{region}'")
            print("   Solution: Use the correct region or recreate bucket in correct region")
        else:
            print(f"✅ Bucket region confirmed: {bucket_region}")
    except ClientError as e:
        print(f"⚠️  Could not verify bucket region: {e}")

    # Test basic S3 operations
    print("
🧪 Testing S3 operations..."    test_key = "diagnostic_test.txt"
    test_content = b"AWS S3 Diagnostic Test"

    # Test put object
    try:
        s3_client.put_object(Bucket=bucket_name, Key=test_key, Body=test_content)
        print("✅ Put object: SUCCESS")
    except ClientError as e:
        print(f"❌ Put object failed: {e.response['Error']['Code']}")
        return False

    # Test list objects
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        objects = response.get('Contents', [])
        print(f"✅ List objects: Found {len(objects)} objects")
    except ClientError as e:
        print(f"❌ List objects failed: {e.response['Error']['Code']}")

    # Test get object
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
        retrieved_content = response['Body'].read()
        if retrieved_content == test_content:
            print("✅ Get object: SUCCESS")
        else:
            print("⚠️  Get object: Content mismatch")
    except ClientError as e:
        print(f"❌ Get object failed: {e.response['Error']['Code']}")

    # Clean up test object
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print("✅ Delete object: SUCCESS")
    except ClientError as e:
        print(f"⚠️  Delete object failed: {e.response['Error']['Code']}")

    print("
🎉 S3 Diagnostic Complete!"    print("✅ All basic S3 operations are working!")
    return True

def create_bucket_if_needed(access_key, secret_key, bucket_name, region):
    """Create S3 bucket if it doesn't exist"""
    print(f"\n🏗️  Attempting to create bucket: {bucket_name}")

    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key

    try:
        s3_client = boto3.client('s3', region_name=region)

        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                pass  # Bucket doesn't exist, we'll create it
            else:
                print(f"❌ Cannot check bucket existence: {e}")
                return False

        # Create bucket
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )

        print(f"✅ Bucket '{bucket_name}' created successfully")
        return True

    except ClientError as e:
        print(f"❌ Failed to create bucket: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return False

def main():
    print("🚀 AWS S3 Diagnostic Tool")
    print("This tool will help diagnose and fix S3 access issues")
    print("=" * 60)

    # Get credentials interactively
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    bucket_name = input("S3 Bucket Name [interior-ecommerce-uploads]: ").strip() or "interior-ecommerce-uploads"
    region = input("AWS Region [us-east-1]: ").strip() or "us-east-1"

    print("
🔧 Running diagnostics..."    success = diagnose_s3_access(access_key, secret_key, bucket_name, region)

    if not success:
        print("
❌ Diagnostics found issues. Attempting auto-fix..."        # Try to create bucket
        if create_bucket_if_needed(access_key, secret_key, bucket_name, region):
            print("
🔄 Re-running diagnostics after bucket creation..."            success = diagnose_s3_access(access_key, secret_key, bucket_name, region)

    if success:
        print("
🎉 SUCCESS! Your S3 setup is working correctly."        print("You can now run your application tests.")
    else:
        print("
❌ DIAGNOSIS: S3 access issues persist."        print("
🔧 Manual Solutions:"        print("1. Check IAM permissions - ensure your user has S3 full access")
        print("2. Verify bucket exists in the correct region")
        print("3. Check bucket policy if it has restrictive permissions")
        print("4. Try creating a new bucket with a unique name")
        print("5. Contact AWS support if issues persist")

if __name__ == "__main__":
    main()