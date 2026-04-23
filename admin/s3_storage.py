"""
AWS S3 Storage Module
Provides persistent file storage for Render's ephemeral filesystem
"""
import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
from werkzeug.utils import secure_filename
from io import BytesIO

class S3Storage:
    """AWS S3 storage handler for images and 3D models"""
    
    def __init__(self):
        """Initialize S3 client with environment variables"""
        self.bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        self.region = os.environ.get('AWS_S3_REGION', 'us-east-1')
        self.use_s3 = self.bucket_name is not None
        
        if self.use_s3:
            try:
                self.client = boto3.client(
                    's3',
                    region_name=self.region,
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
                )
                # Test connection
                self.client.head_bucket(Bucket=self.bucket_name)
            except NoCredentialsError:
                raise Exception("AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            except ClientError as e:
                raise Exception(f"S3 bucket error: {str(e)}")
            except Exception as e:
                raise Exception(f"S3 initialization error: {str(e)}")
    
    def upload_file(self, file_obj, filename, prefix='images/'):
        """
        Upload file to S3
        
        Args:
            file_obj: File object from request.files
            filename: Original filename
            prefix: S3 folder prefix (e.g., 'images/', 'models/')
        
        Returns:
            URL of uploaded file or local path if S3 disabled
        """
        if not self.use_s3:
            return None
        
        try:
            secure_name = secure_filename(filename)
            key = f"{prefix}{secure_name}"
            
            # Upload to S3
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs={'ContentType': getattr(file_obj, 'content_type', None) or 'application/octet-stream'}
            )
            
            # Generate public URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            return url
        except ClientError as e:
            raise Exception(f"S3 upload error: {str(e)}")
    
    def delete_file(self, filename, prefix='images/'):
        """Delete file from S3"""
        if not self.use_s3:
            return True
        
        try:
            key = f"{prefix}{secure_filename(filename)}"
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            raise Exception(f"S3 delete error: {str(e)}")
    
    def list_files(self, prefix='images/'):
        """List all files in S3 prefix"""
        if not self.use_s3:
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            files = []
            for obj in response['Contents']:
                # Extract filename from key
                filename = obj['Key'].replace(prefix, '')
                if filename:  # Skip empty filenames
                    files.append(filename)
            
            return sorted(files)
        except ClientError as e:
            raise Exception(f"S3 list error: {str(e)}")
    
    def get_file_url(self, filename, prefix='images/'):
        """Get public URL for file"""
        if not self.use_s3:
            return None
        
        secure_name = secure_filename(filename)
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{prefix}{secure_name}"
    
    def get_file_object(self, filename, prefix='images/'):
        """Download file from S3 as BytesIO object"""
        if not self.use_s3:
            return None
        
        try:
            key = f"{prefix}{secure_filename(filename)}"
            obj = BytesIO()
            self.client.download_fileobj(self.bucket_name, key, obj)
            obj.seek(0)
            return obj
        except ClientError as e:
            raise Exception(f"S3 download error: {str(e)}")

def init_s3():
    """Initialize S3 storage if credentials provided"""
    try:
        return S3Storage()
    except Exception as e:
        print(f"Warning: S3 not configured - using local storage. {str(e)}")
        return None
