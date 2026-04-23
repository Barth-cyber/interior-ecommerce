# AWS S3 Storage Setup Guide
## Persistent File Storage for Render Deployment

### Problem: Ephemeral Filesystem
On Render's free tier, the filesystem is ephemeral - **files are deleted when the app restarts**. This means:
- ❌ Uploaded images lost
- ❌ 3D models lost  
- ❌ User data lost

### Solution: AWS S3
Store files persistently in AWS S3 with automatic fallback to local storage.

---

## Step 1: Create AWS Account & S3 Bucket

### 1.1 Create AWS Account
1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Fill in your details (email, password, etc.)
4. Verify your email
5. Set up billing information

### 1.2 Create S3 Bucket
1. Sign in to AWS Console: https://console.aws.amazon.com
2. Search for **S3** in the search bar
3. Click "S3"
4. Click **"Create bucket"**
5. **Bucket name:** `interior-ecommerce-uploads` (must be globally unique)
6. **Region:** Select your closest region (e.g., `us-east-1`)
7. **Block Public Access:** Leave unchecked (we'll use signed URLs)
8. Click **"Create bucket"**

### 1.3 Enable Public Access (Optional - for public image serving)
1. Go to your bucket → **Permissions** tab
2. Click **"Edit"** next to "Block public access"
3. Uncheck all options for public read access
4. Click **"Save"**

---

## Step 2: Create IAM User with S3 Access

### 2.1 Create IAM User
1. In AWS Console, search for **IAM**
2. Click **"Users"** → **"Create user"**
3. **User name:** `interior-ecommerce-app`
4. Click **"Next"** → **"Create user"**

### 2.2 Attach S3 Policy
1. Select your new user
2. Click **"Add permissions"** → **"Attach policies directly"**
3. Search for **`AmazonS3FullAccess`**
4. Check the box and click **"Next"** → **"Add permissions"**

### 2.3 Create Access Keys
1. Select your user → **"Security credentials"** tab
2. Scroll to **"Access keys"**
3. Click **"Create access key"**
4. Select **"Application running outside AWS"**
5. Click **"Next"** → **"Create access key"**
6. **Save these immediately:**
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJal...`
   - ⚠️ **Never commit these to GitHub!**

---

## Step 3: Configure Render Environment Variables

### 3.1 Add S3 Credentials to Render
1. Go to Render Dashboard → Your Service → **Settings**
2. Scroll to **Environment**
3. Add these variables:

```
AWS_ACCESS_KEY_ID = [Your Access Key ID from Step 2.3]
AWS_SECRET_ACCESS_KEY = [Your Secret Access Key from Step 2.3]
AWS_S3_BUCKET_NAME = interior-ecommerce-uploads
AWS_S3_REGION = us-east-1
```

4. Click **"Save"** and wait for redeploy

---

## Step 4: Test S3 Integration Locally

### 4.1 Create `.env` file (local testing)
```bash
# .env (local only - DO NOT COMMIT)
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_S3_BUCKET_NAME=interior-ecommerce-uploads
AWS_S3_REGION=us-east-1
```

### 4.2 Test Upload
```bash
# Install boto3 locally
pip install boto3

# Start the app
python application.py

# Try uploading an image via admin panel
# Check AWS S3 console → your bucket
# Should see images/ folder with your file
```

---

## How It Works

### Upload Flow
```
User uploads file
    ↓
Flask receives file
    ↓
S3Storage.upload_file()
    ├→ Upload to S3 (if credentials available)
    └→ Fallback to local storage (if S3 fails)
    ↓
Return success response
```

### Storage Hierarchy
1. **Primary:** AWS S3 (persistent, scalable)
2. **Fallback:** Local filesystem (for development, temporary)

### When Files Are Accessed
- Admin dashboard: Lists files from local folder
- Public routes: Serve from local or S3 via `/idl-images/<filename>`

---

## AWS Pricing

### Free Tier (First 12 months)
- ✅ **5 GB storage** (free)
- ✅ **20,000 GET requests** (free)
- ✅ **2,000 PUT requests** (free)

### After Free Tier
**Typical monthly cost for small app:**
- Storage: ~$1-5 (depending on file size)
- Requests: ~$0.50-2 (depending on usage)
- **Total: ~$2-10/month**

---

## File Organization in S3

```
interior-ecommerce-uploads/
├── images/
│   ├── product-1.jpg
│   ├── product-2.png
│   └── ...
├── models/
│   ├── door-model.glb
│   ├── vent-model.gltf
│   └── ...
```

---

## Accessing Files

### Public URL Format
```
https://interior-ecommerce-uploads.s3.us-east-1.amazonaws.com/images/filename.jpg
```

### In Flask App
```python
# Get public URL
url = s3_storage.get_file_url('filename.jpg', 'images/')

# Upload file
url = s3_storage.upload_file(file_obj, 'myfile.jpg', 'images/')

# List files
files = s3_storage.list_files('images/')

# Delete file
s3_storage.delete_file('filename.jpg', 'images/')
```

---

## Troubleshooting

### ❌ "NoCredentialsError"
**Problem:** AWS credentials not found
```
KeyError: AWS_ACCESS_KEY_ID not set
```
**Solution:**
- Add environment variables to `.env` (local) or Render Settings
- Ensure credentials are correct

### ❌ "Access Denied"
**Problem:** IAM user doesn't have S3 permission
**Solution:**
- Go to IAM User → Attach `AmazonS3FullAccess` policy
- Wait 5 minutes for permission to propagate

### ❌ "Bucket does not exist"
**Problem:** Bucket name wrong or not created
**Solution:**
- Verify bucket name in AWS S3 console
- Ensure `AWS_S3_BUCKET_NAME` matches exactly

### ❌ Files still lost after restart
**Problem:** S3 not working, falling back to local
**Solution:**
1. Check Render logs for S3 errors
2. Verify all AWS environment variables are set
3. Test credentials in `.env` locally first

---

## Local Development Without S3

If you don't have AWS yet, the app still works:
- Files save to `IDL_Product_branding/` locally
- Perfect for development
- Just add S3 environment variables when ready for production

---

## Migration: Existing Files to S3

If you have files already uploaded:

### Option 1: Manual Upload via AWS Console
1. AWS S3 Console → Your bucket
2. Click **"Upload"** → Select files
3. Organize into `images/` and `models/` folders

### Option 2: Programmatic Migration
```python
import boto3
import os

s3 = boto3.client('s3', 
    aws_access_key_id='your_key',
    aws_secret_access_key='your_secret'
)

bucket = 'interior-ecommerce-uploads'

# Upload all images
for filename in os.listdir('IDL_Product_branding'):
    local_path = f'IDL_Product_branding/{filename}'
    s3_key = f'images/{filename}'
    s3.upload_file(local_path, bucket, s3_key)
    print(f"Uploaded {filename}")
```

---

## Security Best Practices

### ✅ Do:
- [ ] Keep AWS credentials in environment variables
- [ ] Use IAM user (not root account keys)
- [ ] Limit IAM permissions to S3 only
- [ ] Rotate access keys periodically
- [ ] Monitor S3 access in CloudTrail

### ❌ Don't:
- [ ] Don't commit `.env` to Git
- [ ] Don't hardcode credentials in code
- [ ] Don't use root AWS account keys
- [ ] Don't make bucket public without reason
- [ ] Don't commit AWS credentials anywhere

---

## Next Steps

1. ✅ Create AWS account & S3 bucket
2. ✅ Create IAM user with S3 access
3. ✅ Add environment variables to Render
4. ✅ Test locally with `.env`
5. ✅ Deploy to Render
6. ✅ Monitor app logs for S3 errors

Your app is now ready for persistent storage on Render! 🚀

---

## Support Resources

- **AWS S3 Documentation:** https://docs.aws.amazon.com/s3/
- **Boto3 Reference:** https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
- **IAM Best Practices:** https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
