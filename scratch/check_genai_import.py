try:
    from google import genai
    print("[OK] google-genai is installed!")
except ImportError:
    print("[FAIL] google-genai is not installed.")
