# Railway + Cloudflare + Route 53 DNS Configuration Guide

Complete guide to configure your domain infrastructure for Railway backend deployment with Cloudflare DNS acceleration and Route 53 registration.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Route 53 (DNS Registrar)                   │
│          Points to Cloudflare nameservers               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│        Cloudflare (DNS + SSL + CDN)                     │
│  - Manages all DNS records                              │
│  - Handles SSL/TLS certificates                         │
│  - Caches and accelerates traffic                       │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   Frontend      Backend API    S3 Storage
   (Pages)      (Railway)      (Images)
```

---

## Prerequisites

- [ ] Route 53 account (AWS)
- [ ] Cloudflare account (free or paid)
- [ ] Your domain registered (should be in Route 53)
- [ ] Railway backend deployed and accessible
- [ ] Railway public domain: `interior-ecommerce-api.railway.app` (example)

---

## Step 1: Understand Your Current DNS Setup

### 1.1 Check Current Nameservers (Route 53)

```bash
# Find nameservers for your domain in Route 53
# AWS Console → Route 53 → Hosted zones → Your domain

# You should see 4 nameservers like:
# ns-123.awsdns-45.com
# ns-456.awsdns-78.com
# ns-789.awsdns-01.net
# ns-012.awsdns-34.net
```

### 1.2 Verify Cloudflare Nameservers

```bash
# In Cloudflare Dashboard → Your domain → Nameservers
# You should see 2 Cloudflare nameservers like:
# ns1.cloudflare.com
# ns2.cloudflare.com
```

---

## Step 2: Update Domain Registrar to Use Cloudflare

### 2.1 Point Route 53 to Cloudflare (If Not Already Done)

**Important**: This step should already be done for your frontend (Cloudflare Pages). 
Verify in AWS Route 53:

```
AWS Console → Route 53 → Registered domains → Your domain

Under "Name servers", should show Cloudflare nameservers:
- ns1.cloudflare.com
- ns2.cloudflare.com
- ns3.cloudflare.com
- ns4.cloudflare.com
```

If still pointing to Route 53 nameservers, update:

1. AWS Route 53 Console → **Registered domains**
2. Select your domain
3. Click **Add or edit name servers**
4. Replace with Cloudflare nameservers (from Cloudflare Dashboard)
5. Click **Update name servers**
6. Wait 24-48 hours for propagation

### 2.2 Verify Nameserver Propagation

```bash
# Test if nameservers updated globally
nslookup yourdomain.com

# Should return Cloudflare nameservers in results
```

---

## Step 3: Create DNS Records in Cloudflare

From this point forward, **all DNS changes go in Cloudflare**, not Route 53.

### 3.1 Frontend DNS (Cloudflare Pages)

This should already exist if you have a Cloudflare Pages frontend.

**Verify it exists**:
1. **Cloudflare Dashboard** → Your domain → **DNS**
2. Look for record pointing to Cloudflare Pages:
   ```
   Type: CNAME
   Name: yourdomain.com (or www)
   Content: yourdomain.pages.dev
   Proxy status: Proxied (orange cloud)
   ```

If missing, see `COMPLETE_SYSTEM_GUIDE.md` Cloudflare Pages section.

### 3.2 Backend API DNS (Railway)

Create new DNS record for Railway backend:

1. **Cloudflare Dashboard** → Your domain → **DNS** → **Add record**

2. Fill in:
   ```
   Type:        CNAME
   Name:        api          (subdomain for backend API)
   Content:     interior-ecommerce-api.railway.app
   TTL:         Auto
   Proxy:       Proxied (orange cloud - for caching)
   ```

3. Click **Save**

**Result**: 
- `api.yourdomain.com` → Cloudflare → Railway backend

### 3.3 (Optional) S3 Subdomain

If you want to serve S3 files through custom domain (instead of direct S3 URLs):

1. **Cloudflare Dashboard** → **DNS** → **Add record**

2. Fill in:
   ```
   Type:        CNAME
   Name:        cdn     (or images, media, etc.)
   Content:     your-bucket.s3.us-east-1.amazonaws.com
   TTL:         Auto
   Proxy:       DNS only (gray cloud - S3 requires direct access)
   ```

**Note**: Ensure S3 bucket CORS allows Cloudflare IPs.

### 3.4 Verify DNS Records Created

```bash
# List all DNS records pointing to your domain
nslookup -type=CNAME api.yourdomain.com

# Should resolve to Railway domain:
# api.yourdomain.com  canonical name = interior-ecommerce-api.railway.app

# Get IP of Railway domain
nslookup interior-ecommerce-api.railway.app

# Should show Railway's IP addresses
```

---

## Step 4: Configure Railway Custom Domain

Railway needs to know it should accept traffic for `api.yourdomain.com`:

### 4.1 Add Custom Domain in Railway

1. **Railway Dashboard** → Your Project → **Settings** → **Domains**
2. Click **Add domain**
3. Enter: `api.yourdomain.com`
4. Railway will verify the CNAME record
5. Once validated, Railway will show: ✅ Active

```
Domain:     api.yourdomain.com
Status:     ✅ Active
SSL:        ✅ Enabled (via Cloudflare)
```

### 4.2 Verify Railway Certificate

```bash
# Check SSL certificate
curl -v https://api.yourdomain.com/health 2>&1 | grep -i "certificate"

# Should show Cloudflare certificate:
# Subject: *.yourdomain.com
# Issuer: Cloudflare
```

---

## Step 5: SSL/TLS Configuration

### 5.1 Set Cloudflare SSL Mode

1. **Cloudflare Dashboard** → Your domain → **SSL/TLS** → **Overview**

2. Encryption level should be set to:
   ```
   Full (default) or Full (strict)
   ```

   **Explanation**:
   - **Flexible**: HTTP between Cloudflare and Railway (not recommended for production)
   - **Full**: HTTPS between Cloudflare and Railway, but allows self-signed
   - **Full (strict)**: HTTPS with valid certificate (best for production)

3. For **Full (strict)**, select:
   - Certificate: Origin Certificate (if Railway provides one)
   - Or select: Automatic HTTPS Rewrites

### 5.2 Configure HTTP Redirect

1. **Cloudflare Dashboard** → **Rules** → **Page Rules**

2. Create new rule:
   ```
   URL: api.yourdomain.com*
   Setting: Always Use HTTPS
   ```

3. Click **Save**

### 5.3 Verify HTTPS Working

```bash
# Test HTTPS connection
curl https://api.yourdomain.com/health

# Should return 200 OK

# Test HTTP redirect
curl -L http://api.yourdomain.com/health

# Should redirect to HTTPS and return 200 OK
```

---

## Step 6: Configure DNS Records Detail

### 6.1 Recommended DNS Configuration

Complete DNS setup in Cloudflare:

```
Type | Name           | Content                              | Proxy  | TTL
-----|----------------|--------------------------------------|--------|------
A    | yourdomain.com | 104.21.x.x (Cloudflare IP)          | Proxied| Auto
CNAME| www            | yourdomain.com                       | Proxied| Auto
CNAME| api            | interior-ecommerce-api.railway.app  | Proxied| Auto
CNAME| cdn            | your-bucket.s3.us-east-1.amazonaws  | DNS    | Auto
TXT  | @              | v=spf1 include:zoho.com ~all         | -      | Auto
```

### 6.2 Add Mail Records (Zoho)

If using Zoho Mail:

1. **Cloudflare Dashboard** → **DNS**

2. Add MX records:
   ```
   Type:    MX
   Name:    yourdomain.com
   Content: mx.zoho.com
   Priority: 10
   
   Type:    MX
   Name:    yourdomain.com
   Content: mx2.zoho.com
   Priority: 20
   ```

3. Add TXT records for verification:
   ```
   Type:    TXT
   Name:    yourdomain.com
   Content: v=spf1 include:zoho.com ~all
   ```

### 6.3 Verify Mail Records

```bash
# Check MX records
nslookup -type=MX yourdomain.com

# Should show Zoho MX servers

# Check SPF record
nslookup -type=TXT yourdomain.com

# Should show: v=spf1 include:zoho.com ~all
```

---

## Step 7: Configure Cloudflare Page Rules

### 7.1 Bypass Cache for API Endpoints

Ensure API responses aren't heavily cached (or cache only safe content):

1. **Cloudflare Dashboard** → **Rules** → **Page Rules**

2. Create rule for dynamic content:
   ```
   URL: api.yourdomain.com/api/upload*
   Cache Level: Bypass
   ```

3. Create rule for static content:
   ```
   URL: api.yourdomain.com/static/*
   Cache Level: Cache Everything
   Browser Cache TTL: 1 hour
   ```

### 7.2 Recommended Page Rules

```
URL Pattern                    | Setting                | Value
-------------------------------|------------------------|----------
api.yourdomain.com/*           | Security Level         | High
api.yourdomain.com/api/upload* | Cache Level            | Bypass
api.yourdomain.com/health      | Cache Level            | Cache Everything
api.yourdomain.com/static/*    | Cache Level            | Cache Everything
```

---

## Step 8: Verify Complete Setup

### 8.1 DNS Resolution Chain

```bash
# 1. Your domain resolves to Cloudflare
nslookup yourdomain.com
# Should return: 104.21.x.x (Cloudflare IP)

# 2. API subdomain resolves to Railway
nslookup api.yourdomain.com
# Should return: xxx.xxx.xxx.xxx (Railway IP)

# 3. CNAME chain
dig api.yourdomain.com +trace
# Should show: yourdomain.com → Cloudflare → Railway
```

### 8.2 HTTPS Connectivity

```bash
# Test all endpoints
curl -v https://api.yourdomain.com/health
curl -v https://api.yourdomain.com/api/products
curl -v https://api.yourdomain.com/static/style.css

# All should return 200 OK
```

### 8.3 Cloudflare Headers

```bash
# Verify Cloudflare is proxying
curl -I https://api.yourdomain.com/health | grep -i "cf-"

# Should show:
# CF-Cache-Status: HIT or MISS
# CF-Ray: [ray-id]
```

### 8.4 Certificate Verification

```bash
# Check certificate validity
curl -v https://api.yourdomain.com/health 2>&1 | grep -A5 "certificate"

# Should show:
# Subject: *.yourdomain.com (or CN=yourdomain.com)
# Issuer: Cloudflare
# Valid from: [date]
# Valid until: [date]
```

---

## Step 9: Monitoring & Maintenance

### 9.1 Cloudflare Analytics

1. **Cloudflare Dashboard** → **Analytics** → Your domain

2. Monitor:
   - Traffic to api.yourdomain.com
   - Cache hit ratio
   - Error rates (5xx, 4xx)
   - Requests by country

### 9.2 DNS Propagation Monitoring

```bash
# Check DNS from multiple servers
# Use: https://www.whatsmydns.net/

# Or via command line (Linux/Mac):
dig @1.1.1.1 api.yourdomain.com
dig @8.8.8.8 api.yourdomain.com
dig @ns1.cloudflare.com api.yourdomain.com

# All should return same IP
```

### 9.3 Weekly DNS Health Check

```bash
# Verify DNS still resolves correctly
nslookup api.yourdomain.com

# Verify HTTPS still works
curl https://api.yourdomain.com/health

# Check certificate expiration (should be far in future)
curl -v https://api.yourdomain.com/health 2>&1 | grep "Valid until"
```

---

## Troubleshooting

### Issue: "Certificate mismatch" or "SSL error"

**Cause**: Cloudflare SSL mode not correctly configured

**Solution**:
```
Cloudflare Dashboard → SSL/TLS → Overview
Set to: Full or Full (strict)

If still failing:
1. Clear Cloudflare cache (Caching → Purge Cache)
2. Wait 5 minutes
3. Try again: curl https://api.yourdomain.com/health
```

### Issue: DNS not resolving

**Cause**: Nameservers not updated or DNS propagation delayed

**Solution**:
```bash
# Check if Route 53 still set as nameserver
nslookup yourdomain.com

# Should show Cloudflare nameservers
# If not, wait 24-48 hours for propagation

# Force refresh (local DNS cache)
# Windows: ipconfig /flushdns
# Mac: sudo dscacheutil -flushcache
# Linux: sudo systemctl restart systemd-resolved
```

### Issue: "Cloudflare worker timeout"

**Cause**: Railway backend not responding or very slow

**Solution**:
```bash
# Test direct railway connection (bypass Cloudflare)
curl https://interior-ecommerce-api.railway.app/health

# If Railway works directly but fails via Cloudflare:
# Cloudflare Dashboard → Page Rules → Add rule:
# URL: api.yourdomain.com/*
# Setting: Always Online - OFF (temporarily)

# Or increase Railway resources
```

### Issue: S3 CDN CNAME not working

**Cause**: S3 bucket not configured for website hosting or CORS issue

**Solution**:
```bash
# Test direct S3 access
curl https://your-bucket.s3.us-east-1.amazonaws.com/test-file.jpg

# If works directly but fails via CNAME:
# AWS S3 Console → Bucket → Properties
# Enable: Static website hosting OR
# Ensure CORS allows Cloudflare IPs

# Or use CloudFront distribution instead of CNAME
```

---

## Complete DNS Reference Table

| Subdomain | Record Type | Value | Purpose |
|-----------|-------------|-------|---------|
| yourdomain.com | A | 104.21.x.x | Frontend (Cloudflare Pages) |
| www | CNAME | yourdomain.com | Frontend (www redirect) |
| api | CNAME | interior-ecommerce-api.railway.app | Backend (Railway) |
| cdn | CNAME | your-bucket.s3.us-east-1.amazonaws.com | CDN (optional) |
| @ | MX | mx.zoho.com | Email (Zoho) |
| @ | TXT | v=spf1 include:zoho.com ~all | SPF (Zoho) |

---

## Health Check Commands

Run these regularly to verify DNS and services:

```bash
#!/bin/bash
# daily-health-check.sh

echo "=== DNS Health Check ==="
echo "1. Domain resolution:"
nslookup yourdomain.com

echo -e "\n2. API subdomain resolution:"
nslookup api.yourdomain.com

echo -e "\n3. Frontend check:"
curl -I https://yourdomain.com/

echo -e "\n4. Backend API check:"
curl -I https://api.yourdomain.com/health

echo -e "\n5. Certificate check:"
curl -v https://api.yourdomain.com/health 2>&1 | grep "certificate"

echo -e "\n=== DNS Check Complete ==="
```

---

## References

- **Cloudflare DNS Documentation**: https://developers.cloudflare.com/dns/
- **Cloudflare SSL/TLS**: https://developers.cloudflare.com/ssl/
- **AWS Route 53**: https://docs.aws.amazon.com/route53/
- **Railway Custom Domains**: https://docs.railway.app/guides/custom-domains
- **AWS S3 CNAME**: https://docs.aws.amazon.com/AmazonS3/latest/userguide/website-hosting-custom-domain-walkthrough.html

---

## Quick Start Summary

1. ✅ **Nameservers**: Ensure Route 53 points to Cloudflare
2. ✅ **API Record**: Create CNAME `api` → Railway domain in Cloudflare
3. ✅ **Railway Domain**: Add `api.yourdomain.com` in Railway Settings
4. ✅ **SSL/TLS**: Set Cloudflare to "Full" mode
5. ✅ **Verify**: Test with `curl https://api.yourdomain.com/health`
6. ✅ **Monitor**: Watch Cloudflare Analytics for traffic

Done! Your backend is now accessible via Railway with Cloudflare DNS acceleration.
