import urllib.request
import ssl
import sys

# GRACE Smoke Test for Stage
TARGET_URL = "http://localhost:3000"

PATHS = [
    ("/", "Астро-Сводка"), # Content expected in Feed
    ("/reports", "Витрина"),
    ("/admin", "AstroSaaS Admin"), # Title or h1 content
]

def check_url(path, expected_text):
    url = f"{TARGET_URL}{path}"
    print(f"Checking {url}...", end=" ")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
            if response.status != 200:
                print(f"FAILED (Status {response.status})")
                return False
            
            content = response.read().decode("utf-8")
            if expected_text and expected_text not in content:
                # Fallback check for title tag which might be easier to match
                if f"<title>{expected_text}" in content:
                     print("OK")
                     return True
                
                print(f"FAILED (Text '{expected_text}' not found)")
                # print(f"Sample: {content[:200]}")
                return False
            
            print("OK")
            return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print(f"--- Smoke Test: {TARGET_URL} ---")
    failed = False
    for path, text in PATHS:
        if not check_url(path, text):
            failed = True
    
    if failed:
        sys.exit(1)
    print("--- ALL PASS ---")

if __name__ == "__main__":
    main()
