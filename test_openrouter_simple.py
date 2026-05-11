#!/usr/bin/env python3
"""
Simple OpenRouter API Key Test (bypasses SSL issues for verification)
"""
import os
import sys
import ssl
import urllib.request
import json

# Load .env
from dotenv import load_dotenv
load_dotenv("NexusMind/backend/.env")

API_KEY = os.getenv("OPENROUTER_API_KEY", "")

if not API_KEY:
    print("[X] OPENROUTER_API_KEY not found")
    sys.exit(1)

print(f"[OK] API Key found: {API_KEY[:15]}...{API_KEY[-8:]}")
print(f"     Length: {len(API_KEY)} characters")

# Create SSL context that doesn't verify (for testing only)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Test API
url = "https://openrouter.ai/api/v1/auth/key"
headers = {
    "Authorization": f"Bearer {API_KEY}",
}

print("\n[+] Testing API key validity...")

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
        data = json.loads(response.read().decode())
        
        print(f"\n[OK] API KEY IS VALID!")
        print(f"     Label: {data.get('data', {}).get('label', 'N/A')}")
        print(f"     Usage: {data.get('data', {}).get('usage', 0)}")
        print(f"     Limit: {data.get('data', {}).get('limit', 'N/A') or 'Unlimited'}")
        print(f"     Is Free Tier: {data.get('data', {}).get('is_free_tier', False)}")
        
        # Check rate limits
        print("\n[+] Rate Limit Status:")
        print(f"     Requests today: {data.get('data', {}).get('usage', 0)}")
        print(f"     Free tier limit: 200 requests/day")
        
        remaining = 200 - data.get('data', {}).get('usage', 0)
        print(f"     Remaining today: ~{remaining}")
        
        print("\n[SUCCESS] Your OpenRouter API key is working!")
        print("          You can deploy NexusMind with OpenRouter support.")
        
except Exception as e:
    print(f"\n[X] FAILED: {type(e).__name__}: {e}")
    sys.exit(1)
