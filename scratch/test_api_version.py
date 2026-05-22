import google.generativeai as genai
import os

key = os.getenv("GEMINI_API_KEY", "dummy_key")
try:
    print("Testing configuring with v1...")
    genai.configure(api_key=key, client_options={"api_version": "v1"})
    print("[OK] Configured with v1 successfully!")
except Exception as e:
    print("[FAIL] Failed to configure with v1:", str(e))

try:
    print("Testing configuring with v1beta...")
    genai.configure(api_key=key, client_options={"api_version": "v1beta"})
    print("[OK] Configured with v1beta successfully!")
except Exception as e:
    print("[FAIL] Failed to configure with v1beta:", str(e))
