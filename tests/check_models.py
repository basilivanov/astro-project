import os
import urllib.request
import json

api_key = os.getenv("OPENROUTER_API_KEY")
models = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "stepfun/step-3.5-flash:free",
    "deepseek/deepseek-r1-0528:free",
    "google/gemma-3-27b-it:free",
    "openrouter/free"
]

for model in models:
    print(f"Trying {model}...")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'OK' if you are working."}],
        "max_tokens": 10
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode())
            content = data["choices"][0]["message"]["content"]
            print(f"  [SUCCESS] Response: {content.strip()}")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
