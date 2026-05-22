import os
import google.generativeai as genai

print("google-generativeai version:")
try:
    import pkg_resources
    print("Version via pkg_resources:", pkg_resources.get_distribution("google-generativeai").version)
except Exception as e:
    print("Could not get version via pkg_resources:", str(e))

try:
    import importlib.metadata
    print("Version via importlib.metadata:", importlib.metadata.version("google-generativeai"))
except Exception as e:
    print("Could not get version via importlib.metadata:", str(e))

key = os.getenv("GEMINI_API_KEY")
print("GEMINI_API_KEY is set:", bool(key))
if key:
    print("Key starts with:", key[:8] if len(key) >= 8 else key)
    genai.configure(api_key=key)
    try:
        print("Listing available models...")
        models = genai.list_models()
        for m in models:
            print(f"- {m.name} (Supported methods: {m.supported_generation_methods})")
    except Exception as e:
        print("Failed to list models:", str(e))
else:
    print("No GEMINI_API_KEY env var found. Please pass one.")
