import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("AI PROVIDER CONFIGURATION CHECK")
print("=" * 60)

gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

print(f"\n✓ Gemini API Key:    {'LOADED' if gemini_key else 'NOT LOADED'}")
print(f"✓ OpenAI API Key:    {'LOADED' if openai_key else 'NOT LOADED'}")
print(f"✓ Anthropic API Key: {'LOADED' if anthropic_key else 'NOT LOADED'}")

print("\n" + "=" * 60)
print("AI PROVIDER FALLBACK CHAIN:")
print("=" * 60)
print("1. Gemini (Primary)")
print("2. OpenAI (Fallback 1)")
print("3. Anthropic Claude (Fallback 2)")
print("4. Knowledge Base Fallback (Last Resort)")
print("=" * 60)
