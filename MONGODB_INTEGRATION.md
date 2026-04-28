# MongoDB Integration — Deployment Guide

## ✅ Steps Completed

### STEP 7 — Install MongoDB in your backend
- ✅ Added `pymongo==4.10.1` to [requirements.txt](requirements.txt)

### STEP 8 — Connect in your Flask backend
- ✅ Added MongoDB connection code to all Flask apps:
  - [project_gemini/app.py](project_gemini/app.py) — Main backend
  - [admin/app.py](admin/app.py) — Admin panel
  - [app.py](app.py) — Root application

```python
from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"))
db = client["ductai"]
chats = db["chats"]
```

### STEP 9 — Save chat data
- ✅ Implemented `save_chat()` function that replaces S3 save logic:

```python
def save_chat(session_id, user_msg, bot_reply):
    """Save chat messages to MongoDB."""
    if not chats:
        app.logger.warning("MongoDB not available. Chat not saved.")
        return False
    
    try:
        chats.insert_one({
            "session_id": session_id,
            "user": user_msg,
            "bot": bot_reply,
            "timestamp": datetime.utcnow()
        })
        return True
    except Exception as e:
        app.logger.error(f"Error saving chat to MongoDB: {e}")
        return False
```

- ✅ Integrated into chat endpoints (`/ai-query` routes)

### STEP 10 — Load history (context memory)
- ✅ Implemented `load_history()` function:

```python
def load_history(session_id, limit=5):
    """Load chat history from MongoDB (context memory)."""
    if not chats:
        app.logger.warning("MongoDB not available. No history loaded.")
        return []
    
    try:
        history = chats.find({"session_id": session_id}).sort("_id", -1).limit(limit)
        
        messages = []
        for h in reversed(list(history)):
            messages.append({"role": "user", "parts": [h["user"]]})
            messages.append({"role": "model", "parts": [h["bot"]]})
        
        return messages
    except Exception as e:
        app.logger.error(f"Error loading chat history from MongoDB: {e}")
        return []
```

- ✅ Added new endpoint `/chat-history/<session_id>` to retrieve chat history

---

## 🚀 Deployment Steps

### 1. Install MongoDB Dependency Locally
```powershell
pip install -r requirements.txt
```

### 2. Set Up Environment Variable on Render
In your Render.com dashboard:
- Go to **Settings** → **Environment**
- Add new variable:
  - **Key:** `MONGO_URI`
  - **Value:** `mongodb+srv://<username>:<password>@<cluster>.mongodb.net/ductai?retryWrites=true&w=majority`

Get your MongoDB connection string from:
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Click **Connect** on your cluster
3. Copy the connection string
4. Replace `<username>`, `<password>`, and `<cluster>` with your credentials

### 3. Redeploy on Render
- Push changes to GitHub or redeploy manually
- Monitor logs to ensure MongoDB connects: `✅ MongoDB connected successfully`

### 4. Test Chat Endpoints

**Send a chat query:**
```bash
curl -X POST http://localhost:5000/ai-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about your furniture",
    "session_id": "user_123"
  }'
```

**Retrieve chat history:**
```bash
curl http://localhost:5000/chat-history/user_123
```

---

## 📊 MongoDB Collection Schema

The `chats` collection stores documents with this structure:

```json
{
  "_id": ObjectId,
  "session_id": "user_123",
  "user": "Tell me about your furniture",
  "bot": "We specialize in luxury interior design solutions...",
  "timestamp": ISODate("2025-04-27T10:30:00.000Z")
}
```

---

## ✨ Benefits

- **Persistent Chat History** — Users can resume conversations
- **Context Memory** — AI can reference past messages (up to 5 most recent)
- **No S3 Storage Needed** — Chat data goes to MongoDB instead
- **Scalable** — MongoDB Atlas handles growth automatically
- **Free Tier Available** — MongoDB Atlas offers free tier (512 MB)

---

## 🔧 Files Modified

1. **[requirements.txt](requirements.txt)** — Added `pymongo==4.10.1`
2. **[project_gemini/app.py](project_gemini/app.py)** — MongoDB connection + functions
3. **[admin/app.py](admin/app.py)** — MongoDB connection + functions
4. **[app.py](app.py)** — MongoDB connection + functions

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `MONGO_URI not set` | Add environment variable to Render dashboard |
| Connection timeout | Whitelist Render IP in MongoDB Atlas (Settings → Network Access) |
| `pymongo` import error | Run `pip install pymongo==4.10.1` |
| Chat not saving | Check MongoDB connection: `✅ MongoDB connected successfully` in logs |

---

## 📚 Next Steps

1. **Test locally** with MongoDB Atlas connection string
2. **Deploy to Render** and monitor logs
3. **Update frontend** to send `session_id` with chat queries
4. **Monitor MongoDB usage** via MongoDB Atlas dashboard

---

**Status:** ✅ MongoDB integration complete and ready for deployment!
