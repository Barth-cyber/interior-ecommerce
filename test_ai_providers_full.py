#!/usr/bin/env python3
"""
Comprehensive AI Provider Testing Script
Tests Gemini, OpenAI, and Anthropic Claude APIs for the Duct AI system.
"""

import os
import sys
from dotenv import load_dotenv
import requests as http_requests

# Load environment variables
load_dotenv()

print("=" * 70)
print("DUCT AI - AI PROVIDER COMPREHENSIVE TEST")
print("=" * 70)

# ──────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURATION CHECK
# ──────────────────────────────────────────────────────────────────────────────

print("\n📋 STEP 1: CHECKING API KEY CONFIGURATION")
print("─" * 70)

GEMINI_API_KEY = (
    os.environ.get('GEMINI_API_KEY') or
    os.environ.get('Gemini_API_Key') or
    os.environ.get('GOOGLE_API_KEY') or
    ''
)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

gemini_available = bool(GEMINI_API_KEY)
openai_available = bool(OPENAI_API_KEY)
anthropic_available = bool(ANTHROPIC_API_KEY)

print(f"✓ Gemini API Key:     {'✅ LOADED' if gemini_available else '❌ NOT LOADED'}")
print(f"✓ OpenAI API Key:     {'✅ LOADED' if openai_available else '❌ NOT LOADED'}")
print(f"✓ Anthropic API Key:  {'✅ LOADED' if anthropic_available else '❌ NOT LOADED'}")

if not any([gemini_available, openai_available, anthropic_available]):
    print("\n⚠️ ERROR: No AI API keys configured!")
    print("Please set one or more of:")
    print("  - GEMINI_API_KEY")
    print("  - OPENAI_API_KEY")
    print("  - ANTHROPIC_API_KEY")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# 2. GEMINI API TEST
# ──────────────────────────────────────────────────────────────────────────────

def test_gemini():
    """Test Google Gemini API."""
    print("\n🔵 TESTING GEMINI API (Google)")
    print("─" * 70)
    
    if not GEMINI_API_KEY:
        print("❌ Gemini API key not configured. Skipping.")
        return False
    
    try:
        GEMINI_MODEL = 'gemini-2.0-flash'
        GEMINI_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'
        
        prompt = "What is Interior Duct Ltd? Answer in 1 sentence."
        
        body = {
            'contents': [
                {'role': 'user', 'parts': [{'text': prompt}]}
            ],
            'generationConfig': {
                'maxOutputTokens': 200,
                'temperature': 0.7,
            },
            'systemInstruction': {
                'parts': [{'text': 'You are a helpful AI assistant for Interior Duct Ltd, a luxury furniture company.'}]
            }
        }
        
        response = http_requests.post(
            GEMINI_URL,
            params={'key': GEMINI_API_KEY},
            headers={'Content-Type': 'application/json'},
            json=body,
            timeout=20,
        )
        
        response.raise_for_status()
        data = response.json()
        answer = data['candidates'][0]['content']['parts'][0]['text'].strip()
        
        print(f"✅ Success!")
        print(f"📝 Response: {answer}")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# 3. OPENAI API TEST
# ──────────────────────────────────────────────────────────────────────────────

def test_openai():
    """Test OpenAI API."""
    print("\n🟢 TESTING OPENAI API")
    print("─" * 70)
    
    if not OPENAI_API_KEY:
        print("❌ OpenAI API key not configured. Skipping.")
        return False
    
    try:
        OPENAI_MODEL = 'gpt-4o-mini'
        OPENAI_URL = 'https://api.openai.com/v1/chat/completions'
        
        prompt = "What is Interior Duct Ltd? Answer in 1 sentence."
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful AI assistant for Interior Duct Ltd, a luxury furniture company.'},
            {'role': 'user', 'content': prompt}
        ]
        
        body = {
            'model': OPENAI_MODEL,
            'messages': messages,
            'max_tokens': 200,
            'temperature': 0.7,
        }
        
        response = http_requests.post(
            OPENAI_URL,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPENAI_API_KEY}'
            },
            json=body,
            timeout=20,
        )
        
        response.raise_for_status()
        data = response.json()
        answer = data['choices'][0]['message']['content'].strip()
        
        print(f"✅ Success!")
        print(f"📝 Response: {answer}")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# 4. ANTHROPIC CLAUDE API TEST
# ──────────────────────────────────────────────────────────────────────────────

def test_anthropic():
    """Test Anthropic Claude API."""
    print("\n🟣 TESTING ANTHROPIC CLAUDE API")
    print("─" * 70)
    
    if not ANTHROPIC_API_KEY:
        print("❌ Anthropic API key not configured. Skipping.")
        return False
    
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        prompt = "What is Interior Duct Ltd? Answer in 1 sentence."
        
        response = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=200,
            system='You are a helpful AI assistant for Interior Duct Ltd, a luxury furniture company.',
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.7,
        )
        
        if response.content and len(response.content) > 0:
            answer = response.content[0].text.strip()
            print(f"✅ Success!")
            print(f"📝 Response: {answer}")
            return True
        
        print(f"❌ Failed: Empty response from Claude")
        return False
        
    except ImportError:
        print("❌ Failed: Anthropic package not installed. Run: pip install anthropic")
        return False
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# 5. RUN ALL TESTS
# ──────────────────────────────────────────────────────────────────────────────

results = {}

if gemini_available:
    results['Gemini'] = test_gemini()

if openai_available:
    results['OpenAI'] = test_openai()

if anthropic_available:
    results['Anthropic'] = test_anthropic()

# ──────────────────────────────────────────────────────────────────────────────
# 6. SUMMARY REPORT
# ──────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

passed = sum(1 for v in results.values() if v)
total = len(results)

print(f"\n✅ Passed: {passed}/{total}")
for provider, success in results.items():
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {status} - {provider}")

print("\n" + "=" * 70)
print("FALLBACK CHAIN PRIORITY")
print("=" * 70)
print("1. 🔵 Gemini (Primary - Most reliable)")
print("2. 🟢 OpenAI (Fallback 1)")
print("3. 🟣 Anthropic Claude (Fallback 2)")
print("4. 📚 Knowledge Base (Last resort - No API)")
print("\n" + "=" * 70)

if passed == total:
    print("✅ All configured providers working!")
    sys.exit(0)
elif passed > 0:
    print(f"⚠️ {passed} provider(s) working, {total - passed} failed. System will use fallback chain.")
    sys.exit(0)
else:
    print("❌ All providers failed. Check your API keys and internet connection.")
    sys.exit(1)
