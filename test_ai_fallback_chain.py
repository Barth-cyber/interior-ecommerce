#!/usr/bin/env python3
"""
Test script to verify AI provider fallback chain is working correctly.
Tests the /ai-query endpoint with all three providers.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Load env vars
from dotenv import load_dotenv
load_dotenv()

# Detect if running locally or on production
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:5000')

# Test query
TEST_QUERY = "What furniture would you recommend for a modern living room with a budget of 500,000 NGN?"

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print('='*70)

def print_status(provider, status, details=""):
    icon = "✅" if status == "SUCCESS" else "⚠️" if status == "PARTIAL" else "❌"
    print(f"{icon} {provider:20} {status:12} {details}")

def test_ai_query_endpoint():
    """Test the /ai-query endpoint directly."""
    print_header("Testing /ai-query Endpoint (Multi-Provider Fallback)")
    
    # Prepare request
    payload = {
        "query": TEST_QUERY,
        "session_id": f"test_session_{datetime.now().timestamp()}"
    }
    
    print(f"\n📤 Sending request to: {BASE_URL}/ai-query")
    print(f"📝 Query: {TEST_QUERY[:60]}...")
    print(f"📌 Session ID: {payload['session_id']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/ai-query",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response Data:")
            print(f"  - Has answer: {'answer' in data and data['answer'] is not None}")
            if data.get('answer'):
                print(f"  - Answer length: {len(data['answer'])} characters")
                print(f"  - Answer preview: {data['answer'][:100]}...")
                print(f"  - Escalate: {data.get('escalate', False)}")
                if 'provider' in data:
                    print(f"  - Provider used: {data['provider']}")
                print_status("AI Query Endpoint", "SUCCESS", "Got valid response")
                return True
            else:
                print(f"  - ERROR: Empty answer returned")
                print_status("AI Query Endpoint", "FAILED", "No answer in response")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            print_status("AI Query Endpoint", "FAILED", f"HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error: Cannot reach {BASE_URL}")
        print(f"   Make sure the server is running: python -m flask --app application run")
        print_status("AI Query Endpoint", "FAILED", "Connection refused")
        return False
    except requests.exceptions.Timeout:
        print(f"\n❌ Request Timeout: Server took too long to respond")
        print_status("AI Query Endpoint", "FAILED", "Timeout")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print_status("AI Query Endpoint", "FAILED", str(e))
        return False

def test_health_endpoint():
    """Test the health endpoint to verify server is running."""
    print_header("Testing Server Health")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot reach server at {BASE_URL}")
        print(f"   Expected: python -m flask --app application run")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_environment():
    """Check if required API keys are configured."""
    print_header("Checking Environment Configuration")
    
    gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
    anthropic_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
    openai_key = os.getenv('OPENAI_API_KEY', '').strip()
    
    print(f"\n📋 API Key Status:")
    
    if gemini_key:
        print(f"  ✅ GEMINI_API_KEY: {'*' * 20} (configured)")
    else:
        print(f"  ❌ GEMINI_API_KEY: NOT SET")
    
    if anthropic_key:
        print(f"  ✅ ANTHROPIC_API_KEY: {'*' * 20} (configured)")
    else:
        print(f"  ❌ ANTHROPIC_API_KEY: NOT SET")
    
    if openai_key:
        print(f"  ✅ OPENAI_API_KEY: {'*' * 20} (configured)")
    else:
        print(f"  ❌ OPENAI_API_KEY: NOT SET")
    
    has_any = gemini_key or anthropic_key or openai_key
    if has_any:
        count = sum([bool(gemini_key), bool(anthropic_key), bool(openai_key)])
        print(f"\n📊 {count} AI provider(s) configured")
        return True
    else:
        print(f"\n❌ NO AI PROVIDERS CONFIGURED!")
        print(f"   Please set at least one of: GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY")
        return False

def main():
    print("\n" + "🤖 DUCT AI FALLBACK CHAIN TEST ".center(70, "="))
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    # Step 1: Check environment
    if not check_environment():
        print("\n⚠️  Warning: No API keys configured. The chat will only use Knowledge Base.")
    
    # Step 2: Check server health
    if not test_health_endpoint():
        print("\n❌ Server is not running. Cannot proceed with endpoint tests.")
        print("   Start server with: cd c:\\ecommerce && python -m flask --app application run")
        return 1
    
    # Step 3: Test the /ai-query endpoint
    if test_ai_query_endpoint():
        print_header("✅ ALL TESTS PASSED")
        return 0
    else:
        print_header("❌ TESTS FAILED")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
