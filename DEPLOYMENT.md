# Interior Duct Ltd Website - Deployment Guide

## Overview
This is a Flask-based web application with admin panel for managing content. The application includes product management, image uploads, and dynamic content editing.

## Prerequisites
- Python 3.8+
- AWS Account
- Git

## Service Comparison & Recommendation

### AWS Service Options for Flask Applications

| Service | Cost | Ease of Use | Security | Reliability | Best For |
|---------|------|-------------|----------|-------------|----------|
| **AWS Amplify** | Low (free tier for static) | Medium | High | High | Static sites, serverless backends |
| **AWS Elastic Beanstalk** | Medium | High | High | High | Web applications, APIs |
| **AWS EC2** | Low-Medium | Low | High (manual config) | High | Full control, custom setups |

### **Recommended: AWS Elastic Beanstalk**
For this Flask application, **AWS Elastic Beanstalk** is the most suitable choice because:
- ✅ **Easiest**: Designed specifically for deploying web applications like Flask
- ✅ **Secure**: Built-in security features, auto-scaling, load balancing
- ✅ **Reliable**: Managed service with high availability
- ✅ **Cost-Effective**: Only pay for underlying EC2 instances + small EB fee
- ✅ **Scalable**: Automatic scaling based on traffic

**Why not Amplify?** Amplify is excellent for static sites and serverless applications, but this Flask app requires a persistent server for file uploads, sessions, and database operations. Converting to serverless would require significant code changes and increase complexity/costs.

**Why not EC2?** While EC2 offers more control, it requires manual server management, security hardening, and maintenance - making it less suitable for most developers.

## Deployment to AWS Elastic Beanstalk

### Step 1: Prepare Your Application
1. Ensure all dependencies are in `requirements.txt`:
   ```
   Flask
   Werkzeug
   ```

2. Create `application.py` in the root directory:
   ```python
   from admin.app import app

   if __name__ == "__main__":
       app.run()
   ```

3. Create `.ebextensions/python.config`:
   ```yaml
   option_settings:
     aws:elasticbeanstalk:application:environment:
       FLASK_ENV: production
     aws:elasticbeanstalk:environment:proxy:staticfiles:
       /static: static
       /idl-images: "IDL Product branding"
   ```

4. Create `Procfile`:
   ```
   web: python application.py
   ```

### Step 2: Install AWS CLI and EB CLI
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install EB CLI
pip install awsebcli
```

### Step 3: Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, default region (us-east-1), and output format (json)
```

### Step 4: Initialize Elastic Beanstalk
```bash
cd /path/to/your/project
eb init
# Select region (us-east-1 recommended)
# Select application name (interior-duct-website)
# Select Python platform
# Select latest Python version
```

### Step 5: Create Environment and Deploy
```bash
eb create production-env
# This will create an EC2 instance, load balancer, security groups, etc.
# Takes 5-10 minutes
```

### Step 6: Monitor Deployment
```bash
eb status
eb logs
```

### Step 7: Access Your Application
Once deployed, EB will provide a URL like: `http://interior-duct-website-prod.eba-xxxxxxxx.us-east-1.elasticbeanstalk.com`

## Domain Configuration

### Step 1: Register Domain (Optional)
- Use Route 53 or any registrar
- Recommended: Use Route 53 for easier AWS integration

### Step 2: Configure Custom Domain
```bash
eb create production-env --cname yourdomain
```

### Step 3: Add SSL Certificate
1. Go to AWS Certificate Manager
2. Request a certificate for your domain
3. Update EB environment to use HTTPS

## File Upload Configuration

The application uploads files to the local filesystem. For production:

1. **Option 1: Use S3 (Recommended)**
   - Create S3 bucket
   - Modify `app.py` to use boto3 for S3 uploads
   - More scalable and reliable

2. **Option 2: EFS (Elastic File System)**
   - Attach EFS to EB environment
   - Files persist across deployments

## Scaling Configuration

### Auto Scaling
EB automatically handles scaling, but you can customize:

1. Go to EB Console > Configuration > Capacity
2. Set min/max instances
3. Configure scaling triggers

### Database (Future Enhancement)
For production, consider adding a database:
- Amazon RDS (PostgreSQL/MySQL)
- DynamoDB for serverless

## Monitoring & Maintenance

### CloudWatch Logs
```bash
eb logs
```

### Health Checks
EB provides automatic health monitoring at the environment URL.

### Updates
```bash
eb deploy  # Deploy code changes
eb setenv FLASK_ENV=production  # Update environment variables
```

## Cost Estimation

### Free Tier Eligible
- t2.micro EC2 instance (750 hours/month free)
- Elastic Load Balancer (15 GB data free)
- Basic monitoring

### Estimated Monthly Cost (Low Traffic)
- EC2: $0 (free tier)
- EB: ~$5-10/month
- Load Balancer: $0 (free tier)
- **Total: $5-10/month**

### Scaling Costs
- Additional EC2 instances: $8-15/month each
- S3 storage: $0.023/GB/month

## Security Best Practices

1. **Change Admin Credentials**: Update username/password in `app.py`
2. **Enable HTTPS**: Always use SSL certificates
3. **Environment Variables**: Store secrets in EB environment variables
4. **Regular Updates**: Keep dependencies updated
5. **Backup**: Regular backups of `content.json`

## Troubleshooting

### Common Issues
1. **Deployment Fails**: Check EB logs with `eb logs`
2. **Application Errors**: Check Flask logs in `/var/log/web.stdout.log`
3. **File Upload Issues**: Ensure upload directory permissions
4. **Static Files Not Loading**: Verify `.ebextensions` configuration

### Support
- AWS Documentation: https://docs.aws.amazon.com/elasticbeanstalk/
- EB CLI Reference: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html

## Admin Access
- URL: `https://your-domain.com/admin`
- Username: `interiorductadmin`
- Password: `IDL2024Secure!`
- **Important**: Change credentials immediately after first login!