import os
import json
import google.generativeai as genai

def analyze_news_sentiment(title: str, summary: str, api_key: str = None) -> dict:
    """
    Analyzes the sentiment of a news article using Gemini API.
    Provides a fallback mock analyzer if the API key is missing.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    
    # 1. Fallback mock analyzer if no API key is set
    if not key or key == "YOUR_GEMINI_API_KEY_HERE" or key.strip() == "":
        score = 0.0
        title_lower = title.lower()
        
        # Simple keyword heuristic
        bull_words = ["rise", "gain", "up", "bull", "surge", "growth", "beat", "buy", "profit", "positive", "high", "lead", "record"]
        bear_words = ["drop", "down", "bear", "plummet", "fall", "miss", "sell", "loss", "negative", "low", "risk", "decline", "slow"]
        
        bull_count = sum(1 for w in bull_words if w in title_lower)
        bear_count = sum(1 for w in bear_words if w in title_lower)
        
        if bull_count > bear_count:
            score = 0.5
        elif bear_count > bull_count:
            score = -0.5
            
        label = "NEUTRAL"
        if score > 0.1:
            label = "BULLISH"
        elif score < -0.1:
            label = "BEARISH"
            
        return {
            "score": score,
            "label": label,
            "reason": "로컬 키워드 분석 결과 (Gemini API 키 미등록)",
            "mock": True
        }
        
    # 2. Real Gemini API call with dynamic model fallback
    try:
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
        
        # Try to dynamically list models first to see what this key supports
        try:
            available_models = [m.name.split('/')[-1] for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if available_models:
                active_models = [m for m in models_to_try if m in available_models]
                for m in available_models:
                    if m not in active_models:
                        active_models.append(m)
                if active_models:
                    models_to_try = active_models
        except Exception as list_err:
            print(f"Sentiment: list_models failed (using default fallback list): {str(list_err)}")
        
        prompt = f"""
        Analyze the following stock market news article:
        Title: {title}
        Summary: {summary}
        
        Tasks:
        1. Calculate a sentiment score from -1.0 (extremely negative/bearish) to +1.0 (extremely positive/bullish).
        2. Classify as "BULLISH", "BEARISH", or "NEUTRAL".
        3. Write a concise, 1-sentence explanation of why in Korean.
        
        Respond ONLY with a valid JSON block containing:
        {{
            "score": <float>,
            "label": "BULLISH" | "BEARISH" | "NEUTRAL",
            "reason": "<korean_explanation>"
        }}
        Do not wrap the response in ```json or any markdown blocks. Output raw JSON only.
        """
        
        last_error = None
        genai.configure(api_key=key)
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = response.text.strip()
                
                # Clean potential markdown block formatting from LLM
                if text.startswith("```"):
                    lines = text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                    text = "\n".join(lines).strip()
                    
                result = json.loads(text)
                result["mock"] = False
                return result
            except Exception as e:
                last_error = e
                print(f"Sentiment fallback: Model {model_name} failed: {str(e)}")
                continue
                
        # If all models failed, raise the last exception to let the outer block handle it
        raise last_error
        
    except Exception as e:
        print(f"Gemini API Sentiment Error: {str(e)}")
        return {
            "score": 0.0,
            "label": "NEUTRAL",
            "reason": f"AI 분석 중 오류가 발생했습니다: {str(e)[:50]}",
            "mock": True
        }
