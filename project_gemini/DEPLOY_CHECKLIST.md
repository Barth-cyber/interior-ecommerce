# Deployment Checklist — Interior Duct Ltd (Gemini AI Edition)

## ✅ AI Platform: Google Gemini (FREE)
- Model: gemini-1.5-flash
- Free tier: **1,500 requests/day | 1 million tokens/day** — no credit card required
- Get your free API key: https://aistudio.google.com/apikey
- No extra Python package needed (uses `requests`, already in requirements.txt)

---

## Environment Variables (Set in Render Dashboard)

### Required
| Variable | Where to Get |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey (free, instant) |
| `ADMIN_PASSWORD_HASH` | Generate with `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword'))"` |

### Payment (set when ready)
| Variable | Where to Get |
|---|---|
| `PAYSTACK_SECRET_KEY` | Paystack dashboard → Settings → API Keys |
| `PAYSTACK_PUBLIC_KEY` | Paystack dashboard → Settings → API Keys |
| `STRIPE_SECRET_KEY` | Stripe dashboard → Developers → API Keys |
| `STRIPE_PUBLISHABLE_KEY` | Stripe dashboard → Developers → API Keys |
| `STRIPE_WEBHOOK_SECRET` | Stripe dashboard → Webhooks |

### Optional (AWS S3 for image storage)
| Variable | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret |
| `AWS_S3_BUCKET_NAME` | Your S3 bucket name |
| `AWS_S3_REGION` | e.g. us-east-1 |

---

## Deploy Steps (Render.com)
1. Push code to GitHub
2. Connect repo in Render → New Web Service
3. Set all env vars in Render dashboard (never commit secrets to git)
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn -w 2 -b 0.0.0.0:$PORT application:app`

## Local Development
```bash
# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
echo "ADMIN_USERNAME=admin" >> .env
echo "ADMIN_SECRET_KEY=local-dev-secret" >> .env

pip install -r requirements.txt
python app.py
```
