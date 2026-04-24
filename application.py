import os
from admin.app import app
from werkzeug.security import generate_password_hash

# Securely fetch environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')

# Example usage of hashed admin password
if not ADMIN_PASSWORD_HASH:
    print("Admin password hash not set. Generate one using the deployment checklist.")

# Placeholder for integrating Google Gemini API
if GEMINI_API_KEY:
    print("Google Gemini API Key loaded successfully.")
else:
    print("Google Gemini API Key is missing. Please set it in the environment variables.")

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
AWS_S3_REGION = os.getenv('AWS_S3_REGION')

# Initialize S3 client
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_S3_BUCKET_NAME and AWS_S3_REGION:
    try:
        import boto3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_S3_REGION
        )
        print("AWS S3 client initialized successfully.")
    except Exception as e:
        print(f"AWS S3 client initialization skipped: {e}")
else:
    print("AWS S3 configuration is incomplete. Please check your environment variables.")

# Payment Integration Configuration
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Example usage of payment keys
if not PAYSTACK_SECRET_KEY or not STRIPE_SECRET_KEY:
    print("Payment API keys are missing. Please set them in the environment variables.")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
