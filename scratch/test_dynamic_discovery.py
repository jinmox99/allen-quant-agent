import os
import google.generativeai as genai

def test_discovery():
    key = os.getenv("GEMINI_API_KEY", "dummy_key")
    genai.configure(api_key=key)
    
    models_to_try = [
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-2.0-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    print("Default models to try:", models_to_try)
    
    try:
        print("Attempting to list models dynamically...")
        available_models = [m.name.split('/')[-1] for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print("Available models from API:", available_models)
        if available_models:
            active_models = [m for m in models_to_try if m in available_models]
            for m in available_models:
                if m not in active_models:
                    active_models.append(m)
            if active_models:
                models_to_try = active_models
            print("Resolved models to try:", models_to_try)
    except Exception as list_err:
        print(f"[EXPECTED/OK] list_models failed: {str(list_err)}")
        print("Falling back to default list:", models_to_try)

test_discovery()
