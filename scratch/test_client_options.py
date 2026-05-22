import google.generativeai as genai
from google.api_core.client_options import ClientOptions
import os

key = os.getenv("GEMINI_API_KEY", "dummy_key")
try:
    print("Testing configuring with ClientOptions v1...")
    options = ClientOptions(api_version="v1")
    genai.configure(api_key=key, client_options=options)
    print("[OK] Configured with ClientOptions v1 successfully!")
except Exception as e:
    print("[FAIL] Failed to configure with ClientOptions v1:", str(e))
