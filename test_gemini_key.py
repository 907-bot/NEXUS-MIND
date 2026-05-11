#!/usr/bin/env python3
"""
Quick test to verify Gemini API key is working.
Run: python test_gemini_key.py
"""
import os
import sys
import ssl

# Fix Windows SSL certificate issues
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

# Load from .env if available - try multiple locations
try:
    from dotenv import load_dotenv
    # Try current directory first, then backend
    load_dotenv()
    load_dotenv("NexusMind/backend/.env")
    load_dotenv("backend/.env")
except ImportError:
    pass

API_KEY = os.getenv("GEMINI_API_KEY", "")

if not API_KEY:
    print("[X] GEMINI_API_KEY not found in environment variables or .env file")
    print("    Please set it in: NexusMind/backend/.env")
    print("    Example: GEMINI_API_KEY=your-key-here")
    sys.exit(1)

print(f"[OK] API Key found: {API_KEY[:10]}...{API_KEY[-4:]}")
print(f"   Length: {len(API_KEY)} characters")

# Test the key
try:
    import google.generativeai as genai
    genai.configure(api_key=API_KEY)
    
    # List available models
    print("\n[+] Checking available models...")
    models = list(genai.list_models())
    gemini_models = [m for m in models if 'gemini' in m.name.lower()]
    
    if gemini_models:
        print(f"    Found {len(gemini_models)} Gemini models:")
        for m in gemini_models:
            print(f"      - {m.name}")
    else:
        print("    [!] No Gemini models found (key may be restricted)")
    
    # Try a simple generation
    print("\n[+] Testing simple generation...")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Say 'API key is working!' in 5 words or less.")
    
    print(f"    Response received:")
    print(f"      '{response.text.strip()}'")
    
    # Check usage metadata
    usage = getattr(response, 'usage_metadata', None)
    if usage:
        print(f"\n[+] Usage:")
        print(f"      Input tokens:  {getattr(usage, 'prompt_token_count', 'N/A')}")
        print(f"      Output tokens: {getattr(usage, 'candidates_token_count', 'N/A')}")
    
    print("\n[SUCCESS] API KEY IS VALID AND WORKING!")
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    
    # Common error diagnostics
    error_str = str(e).lower()
    if "api key not valid" in error_str or "permission denied" in error_str:
        print("\n[!] Diagnosis: Invalid API key or key doesn't have Gemini API enabled.")
        print("    Check: https://makersuite.google.com/app/apikey")
    elif "quota" in error_str or "rate limit" in error_str:
        print("\n[!] Diagnosis: API quota exceeded or rate limited.")
        print("    Check: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas")
    elif "billing" in error_str:
        print("\n[!] Diagnosis: Billing issue. Check your Google Cloud billing status.")
    elif "model" in error_str and "not found" in error_str:
        print("\n[!] Diagnosis: Model 'gemini-1.5-flash' not available for this key.")
        print("    Try a different model or enable the API.")
    
    sys.exit(1)
