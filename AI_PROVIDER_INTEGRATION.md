# AI Provider Integration Guide — Multi-Provider Support with Intelligent Fallback

## 🎯 Overview

The Duct AI system now supports **three enterprise AI providers** with intelligent fallback logic:

| Provider | Model | Status | Speed | Cost |
|----------|-------|--------|-------|------|
| **Gemini** (Google) | gemini-1.5-flash | Primary ✅ | ⚡ Fast | 💰 Free tier available |
| **OpenAI** | gpt-4o-mini | Fallback 1 ✅ | ⚡⚡ Fastest | 💸 Paid |
| **Anthropic Claude** | claude-3-5-sonnet | Fallback 2 ✅ | ⚡ Fast | 💸 Paid |
| **Knowledge Base** | Pattern Matching | Last Resort | ⚡⚡⚡ Instant | 🆓 Free |

---

## 📦 Installation

### Step 1: Install Required Packages

```bash
pip install anthropic openai
```

Or use the requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variables

Create a `.env` file in the project root:

```bash
# Primary Provider
GEMINI_API_KEY=AIza...your-gemini-key...

# Fallback Providers
OPENAI_API_KEY=sk-...your-openai-key...
ANTHROPIC_API_KEY=sk-ant-...your-anthropic-key...

# Optional: Override default models
GEMINI_MODEL=gemini-1.5-flash
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Optional: Set primary provider (default: gemini)
LLM_PROVIDER=gemini  # Options: gemini, openai, anthropic
```

### Step 3: Get API Keys

#### Google Gemini (Free Tier)
- Go to: https://aistudio.google.com/apikey
- Click "Create API Key"
- Copy the key to `GEMINI_API_KEY`
- **Free Tier:** 1,500 requests/day, 1M tokens/day

#### OpenAI
- Go to: https://platform.openai.com/account/api-keys
- Create a new API key
- Copy to `OPENAI_API_KEY`
- **Pricing:** $0.00015 per 1K input tokens (gpt-4o-mini)

#### Anthropic Claude
- Go to: https://console.anthropic.com/account/keys
- Create a new API key
- Copy to `ANTHROPIC_API_KEY`
- **Pricing:** $3 per 1M input tokens (Claude 3.5 Sonnet)

---

## 🔄 Intelligent Fallback Chain

### How It Works

```
User Query
    ↓
Try Primary Provider (LLM_PROVIDER env var)
    ↓
If success → Return answer
    ↓
If fails → Try Fallback 1 (Gemini)
    ↓
If fails → Try Fallback 2 (OpenAI)
    ↓
If fails → Try Fallback 3 (Anthropic)
    ↓
If all fail → Use Knowledge Base Pattern Matching
    ↓
Return answer (never fails)
```

### Default Priority

1. **Gemini** (Primary) — Most reliable, free tier
2. **OpenAI** (Fallback 1) — Powerful, paid
3. **Anthropic Claude** (Fallback 2) — Advanced reasoning, paid
4. **Knowledge Base** (Last Resort) — Pattern matching, free

### Benefits

✅ **High Availability** — System never completely fails
✅ **Cost Optimization** — Uses cheapest available provider
✅ **Automatic Recovery** — Handles API outages gracefully
✅ **No Manual Intervention** — Works seamlessly

---

## 📝 Code Integration

### In project_gemini/app.py

#### Single Message Query
```python
# Use the smart fallback chain
answer, escalate = _ask_gemini_chat(query, kb, products_data)

# Or directly call with fallback
answer, error = _call_llm(
    prompt_text=query,
    system_instruction="You are Duct AI...",
    max_tokens=512
)
```

#### Available Functions
- `_call_gemini()` — Direct Gemini call
- `_call_openai()` — Direct OpenAI call  
- `_call_anthropic()` — Direct Anthropic call
- `_call_llm()` — Smart fallback chain for single messages

### In admin/app.py

#### Conversation with History
```python
# Use the smart fallback chain for conversations
answer, error = _call_llm_conversation(
    history=chat_history,
    system_instruction=system_prompt,
    max_tokens=512
)
```

#### Available Functions
- `_call_gemini_conversation()` — Direct Gemini with history
- `_call_anthropic_conversation()` — Direct Anthropic with history
- `_call_llm_conversation()` — Smart fallback chain for conversations

---

## 🧪 Testing

### Test All Providers

```bash
python test_ai_providers_full.py
```

**Output Example:**
```
📋 STEP 1: CHECKING API KEY CONFIGURATION
─────────────────────────────────────────
✓ Gemini API Key:     ✅ LOADED
✓ OpenAI API Key:     ✅ LOADED
✓ Anthropic API Key:  ✅ LOADED

🔵 TESTING GEMINI API (Google)
✅ Success!

🟢 TESTING OPENAI API
✅ Success!

🟣 TESTING ANTHROPIC CLAUDE API
✅ Success!

TEST SUMMARY
✅ Passed: 3/3
  ✅ PASS - Gemini
  ✅ PASS - OpenAI
  ✅ PASS - Anthropic Claude
```

### Test Specific Provider

```bash
# Temporary override to test OpenAI
export LLM_PROVIDER=openai
python test_ai_query.py

# Test with Anthropic
export LLM_PROVIDER=anthropic
python test_ai_query.py

# Back to Gemini (default)
export LLM_PROVIDER=gemini
```

---

## 🚀 Deployment

### Environment Variables for Render

On Render.com:

1. Go to **Dashboard** → **Select Service**
2. **Settings** → **Environment**
3. Add variables:
   ```
   GEMINI_API_KEY=AIza...
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   LLM_PROVIDER=gemini
   ```
4. Save and redeploy

### Verifying in Production

```bash
# Check health endpoint
curl https://your-app.onrender.com/api/health

# Test AI query with fallback
curl -X POST https://your-app.onrender.com/ai-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about your furniture",
    "session_id": "user_123"
  }'
```

---

## 📊 Monitoring & Logging

### Check Provider Status in Logs

The system logs which provider was used:

```
[INFO] Trying Gemini for conversation...
[INFO] Fallback 1: Trying Anthropic Claude for conversation...
[ERROR] All LLM providers failed for conversation.
```

### Metrics to Track

- **Success Rate** — % of queries that got AI response
- **Fallback Usage** — How often each provider was used
- **Response Time** — ms per query by provider
- **Cost** — $ spent on each provider monthly

---

## 🛠️ Troubleshooting

### No API Key Set
**Error:** `GEMINI_API_KEY not set. Gemini provider unavailable.`
**Solution:** Add API key to `.env` or environment variables

### Invalid API Key
**Error:** `Gemini API error: [HTTP 401] Unauthorized`
**Solution:** Verify API key is correct (copy from dashboard, no extra spaces)

### Rate Limit Exceeded
**Error:** `Gemini API error: [HTTP 429] Too Many Requests`
**Solution:** Wait 1 minute (free tier: 1,500 req/day limit) or upgrade

### Package Not Installed
**Error:** `Anthropic package not installed. Install with: pip install anthropic`
**Solution:** `pip install -r requirements.txt`

### All Providers Failing
**Error:** `All LLM providers failed. No API keys configured or all APIs are down.`
**Solution:** 
1. Check `.env` file has correct keys
2. Test API keys individually with `test_ai_providers_full.py`
3. Check internet connection
4. Verify API service status pages

---

## 💡 Best Practices

### 1. Use Multiple Providers
- Free tier: Use Gemini (1,500 req/day free)
- Production: Add OpenAI or Anthropic backup

### 2. Monitor Usage
- Track which provider handles each request
- Optimize costs by switching providers

### 3. Handle Edge Cases
```python
# System automatically handles:
answer, error = _call_llm(query)
if error:
    # Try knowledge base next
    answer = _generate_fallback_response(query, kb, products)
```

### 4. Set Appropriate Timeouts
```python
# All API calls have 20s timeout to prevent hanging
timeout=20
```

### 5. Cache Responses
```python
# Store frequently asked questions locally
# Check knowledge base before hitting APIs
if answer_in_knowledge_base:
    return answer  # Free! Instant!
```

---

## 📚 Reference

### Configuration Variables

| Variable | Default | Options |
|----------|---------|---------|
| `LLM_PROVIDER` | gemini | gemini, openai, anthropic |
| `GEMINI_MODEL` | gemini-1.5-flash | gemini-1.5-flash, gemini-1.5-pro |
| `OPENAI_MODEL` | gpt-4o-mini | gpt-4, gpt-4o-mini, gpt-3.5-turbo |
| `ANTHROPIC_MODEL` | claude-3-5-sonnet-20241022 | claude-3-opus, claude-3-sonnet, claude-3-haiku |

### API Costs (Approximate)

**Gemini:** Free (1,500 req/day limit)
**OpenAI (gpt-4o-mini):** $0.00015 per 1K input tokens (~$0.05 per 1000 queries)
**Anthropic (Claude 3.5):** $3 per 1M input tokens (~$0.15 per 1000 queries)

### Response Times (Typical)

| Provider | Time |
|----------|------|
| Gemini | 0.8-1.5s |
| OpenAI | 1-2s |
| Anthropic | 1-2s |
| Knowledge Base | <0.1s |

---

## ✅ Checklist

- [ ] All three API keys set in `.env`
- [ ] Run `test_ai_providers_full.py` — all tests pass
- [ ] Try `/ai-query` endpoint — works with fallback
- [ ] Check logs — see provider being used
- [ ] Deploy to Render — add env vars
- [ ] Test in production — verify fallback works

---

## 📞 Support

For issues:
1. Check logs: `python test_ai_providers_full.py`
2. Verify API keys: `echo $GEMINI_API_KEY`
3. Test directly: Use `test_ai_query.py`
4. Check provider status: Visit provider's status page
