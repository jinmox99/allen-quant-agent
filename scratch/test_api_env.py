import os
import google.generativeai as genai

os.environ["GENAI_API_VERSION"] = "v1"
key = os.getenv("GEMINI_API_KEY", "dummy_key")
genai.configure(api_key=key)

try:
    print("Testing if we can create model and see api version...")
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("[OK] GenerativeModel created successfully!")
    # Let's inspect the model client if possible
    client = model._client
    print("Client service path:", getattr(client, "service_path", None))
    print("Client API version:", getattr(client, "_api_version", None))
except Exception as e:
    print("[FAIL] Failed:", str(e))
