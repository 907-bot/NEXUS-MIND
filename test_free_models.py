import os
import asyncio
import aiohttp
import ssl
import certifi
from dotenv import load_dotenv

load_dotenv("NexusMind/backend/.env")
API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-chat:free",
    "deepseek/deepseek-coder:free",
    "liquid/lfm-40b:free",
    "gryphe/mythomax-l2-13b:free",
    "undi95/toppy-m-7b:free",
    "openrouter/auto",
]

SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

async def test_model(session, model_id):
    print(f"Testing {model_id}...")
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Say 'OK'"}],
        "max_tokens": 10
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nexusmind.app",
        "X-Title": "NexusMind Test",
    }
    try:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        ) as response:
            status = response.status
            if status == 200:
                print(f"  [OK] {model_id} works!")
                return True
            else:
                text = await response.text()
                print(f"  [ERROR] {model_id} failed with {status}: {text[:100]}")
                return False
    except Exception as e:
        print(f"  [ERROR] {model_id} error: {e}")
        return False

async def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not set")
        return

    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT)
    async with aiohttp.ClientSession(connector=connector) as session:
        for model in MODELS:
            await test_model(session, model)
            await asyncio.sleep(2) # Rate limit friendly

if __name__ == "__main__":
    asyncio.run(main())
