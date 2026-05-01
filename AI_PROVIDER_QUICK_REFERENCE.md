# AI Provider Integration - Quick Reference Guide

## 🚀 Quick Start (5 minutes)

### 1. Get API Keys (Choose at least ONE)

**Google Gemini (Recommended - Free)**
```
Go to: https://aistudio.google.com/apikey
Click: Create API Key
Copy: Set as GEMINI_API_KEY in .env
```

**OpenAI (Paid fallback)**
```
Go to: https://platform.openai.com/account/api-keys
Create: New API key
Copy: Set as OPENAI_API_KEY in .env
```

**Anthropic Claude (Paid fallback)**
```
Go to: https://console.anthropic.com/account/keys
Create: New API key
Copy: Set as ANTHROPIC_API_KEY in .env
```

### 2. Set Environment Variables

Create `.env` file (or add to existing):
```bash
# Primary provider (at least one required)
GEMINI_API_KEY=AIza...your-key...
OPENAI_API_KEY=sk-...your-key...
ANTHROPIC_API_KEY=sk-ant-...your-key...

# Optional: Choose which one is primary (default: gemini)
LLM_PROVIDER=gemini
```

### 3. Test It Works

```bash
python test_ai_providers_full.py
```

Expected: ✅ All configured providers show "Success!"

### 4. Deploy

Add env vars to Render.com → Done! ✅

---

## 📋 How It Works

```
User asks question
        ↓
Try Primary Provider (e.g., Gemini)
        ↓
  Success? → Return answer ✅
        ↓
     NO   → Try Fallback 1 (OpenAI)
        ↓
  Success? → Return answer ✅
        ↓
     NO   → Try Fallback 2 (Anthropic)
        ↓
  Success? → Return answer ✅
        ↓
     NO   → Use Knowledge Base (instant)
        ↓
     Return answer (never fails!)
```

**Key Benefit:** System NEVER completely fails. One provider down? Others take over automatically.

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Example |
|----------|----------|---------|---------|
| `GEMINI_API_KEY` | No* | N/A | `AIza...` |
| `OPENAI_API_KEY` | No* | N/A | `sk-...` |
| `ANTHROPIC_API_KEY` | No* | N/A | `sk-ant-...` |
| `LLM_PROVIDER` | No | `gemini` | `gemini`, `openai`, `anthropic` |

*At least one required

### Model Names (Optional Override)

| Provider | Variable | Default | Alternatives |
|----------|----------|---------|---------------|
| Gemini | `GEMINI_MODEL` | `gemini-2.0-flash` | `gemini-2.0-pro` |
| OpenAI | `OPENAI_MODEL` | `gpt-4o-mini` | `gpt-4`, `gpt-3.5-turbo` |
| Anthropic | `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | `claude-3-opus` |

---

## 🧪 Testing

### Check Configuration
```bash
python check_ai_providers.py
```
Shows which API keys are loaded.

### Test All Providers
```bash
python test_ai_providers_full.py
```
Tests all configured providers with sample queries.

### Test Production Endpoint
```bash
curl -X POST http://localhost:5000/ai-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about your furniture",
    "session_id": "test_user_123"
  }'
```

### Switch Providers (Testing)
```bash
# Temporarily use OpenAI
export LLM_PROVIDER=openai
python test_ai_query.py

# Back to Gemini
export LLM_PROVIDER=gemini
```

---

## 📊 Provider Comparison

| Feature | Gemini | OpenAI | Anthropic | KB |
|---------|--------|--------|-----------|-----|
| Cost | Free tier ✅ | Paid | Paid | Free ✅ |
| Speed | Fast | Fastest | Fast | Instant ✅ |
| Quality | Good | Excellent | Excellent | Limited |
| Reliability | Good | Excellent | Excellent | Always ✅ |
| Response Time | 0.8-1.5s | 1-2s | 1-2s | <0.1s |

### Cost Analysis (Per 1000 Queries)

| Provider | Typical Cost |
|----------|-------------|
| Gemini | $0 (free tier) |
| OpenAI | ~$0.05 (gpt-4o-mini) |
| Anthropic | ~$0.15 (Claude 3.5) |
| Knowledge Base | $0 (free) |

---

## 🔍 Troubleshooting

### "No API key configured"
```
✅ Solution: Set at least GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY
```

### "API Key Invalid"
```
✅ Solution: 
   1. Copy key again from provider dashboard
   2. Check for extra spaces (common mistake)
   3. Verify key hasn't expired
```

### "Quota Exceeded"
```
✅ Solution: 
   - Gemini free tier: Limited to 1,500 req/day
   - Wait until next day for quota reset
   - System will automatically use OpenAI/Anthropic fallback
```

### "All providers failed"
```
❌ Indicates:
   - All API keys invalid OR
   - Internet connection down OR
   - All providers completely down (rare)

✅ Solution:
   1. Check internet: ping google.com
   2. Test API keys with test_ai_providers_full.py
   3. Check provider status pages
   4. System will still use Knowledge Base (last resort)
```

### "Connection timeout"
```
✅ Solution:
   - Increase timeout or retry
   - System will automatically try next provider
   - Knowledge Base returns instantly (no timeout)
```

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `project_gemini/app.py` | Main AI API + Gemini/OpenAI/Anthropic calls |
| `admin/app.py` | Admin endpoints + conversation history |
| `test_ai_providers_full.py` | Test all providers |
| `check_ai_providers.py` | Quick config check |
| `AI_PROVIDER_INTEGRATION.md` | Full documentation |
| `AI_PROVIDER_IMPLEMENTATION_SUMMARY.md` | Technical summary |
| `.env` | Environment variables (local only) |

---

## ⚡ Key Functions

### Single Message Query
```python
# In project_gemini/app.py
from project_gemini.app import _call_llm

answer, error = _call_llm(
    prompt_text="What is Interior Duct Ltd?",
    system_instruction="You are a helpful AI assistant",
    max_tokens=512
)
```

### Conversation with History
```python
# In admin/app.py
from admin.app import _call_llm_conversation

answer, error = _call_llm_conversation(
    history=[
        {"role": "user", "text": "Tell me about sofas"},
        {"role": "assistant", "text": "We have beautiful sofas..."}
    ],
    system_instruction="You are a helpful assistant",
    max_tokens=512
)
```

### Direct Provider Calls
```python
# Gemini
answer, error = _call_gemini(prompt_text="...", max_tokens=512)

# OpenAI
answer, error = _call_openai(prompt_text="...", max_tokens=512)

# Anthropic
answer, error = _call_anthropic(prompt_text="...", max_tokens=512)
```

---

## ✅ Checklist

- [ ] At least one API key obtained
- [ ] API key set in `.env` file
- [ ] `test_ai_providers_full.py` runs successfully
- [ ] `/ai-query` endpoint works
- [ ] Logs show provider being used
- [ ] Deployed to Render with env vars
- [ ] Tested fallback by simulating provider failure

---

## 🎯 Next Steps

1. **Get API Key**
   - Start with Gemini (free)
   - Add OpenAI/Anthropic as backup

2. **Set Environment Variable**
   - Add to `.env` locally
   - Add to Render dashboard for production

3. **Test**
   - Run `test_ai_providers_full.py`
   - Send a test query to `/ai-query`

4. **Deploy**
   - Push changes
   - Verify in production logs
   - Monitor fallback usage

5. **Monitor**
   - Check logs for provider usage
   - Track response times
   - Monitor costs

---

## 📞 Quick Help

### Need to test?
```bash
python test_ai_providers_full.py
```

### Check config?
```bash
python check_ai_providers.py
```

### View logs?
```bash
tail -f logs/app.log
```

### Switch providers?
```bash
export LLM_PROVIDER=openai
```

### Deploy changes?
```bash
git add .
git commit -m "AI provider integration complete"
git push
```

---

## 💡 Pro Tips

1. **Use Gemini for free tier** - 1,500 requests/day free
2. **Add OpenAI as backup** - Most reliable when available
3. **Monitor fallback usage** - Check logs to see which provider gets used
4. **Cache KB responses** - Knowledge base is instant and free
5. **Set alerts** - Alert when all providers fail (shouldn't happen)

---

**Questions?** Check `AI_PROVIDER_INTEGRATION.md` for detailed guide.
