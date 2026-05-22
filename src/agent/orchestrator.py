import os
import google.generativeai as genai
import pandas as pd

def generate_agent_report(ticker: str, 
                          name: str, 
                          df: pd.DataFrame, 
                          news_sentiment: dict, 
                          api_key: str = None) -> dict:
    """
    Generates a professional investment briefing report combining technical signals and news sentiment.
    If Gemini API key is not provided, dynamically renders a highly detailed rule-based report.
    """
    if df.empty:
        return {"error": "분석할 데이터가 존재하지 않습니다."}
        
    latest = df.iloc[-1]
    current_price = float(latest.get('Close', 0.0))
    rsi = float(latest.get('RSI', 50.0))
    
    # Extract technical indicators state
    sma10 = float(latest.get('SMA_10', current_price))
    sma25 = float(latest.get('SMA_25', current_price))
    sma45 = float(latest.get('SMA_45', current_price))
    macd = float(latest.get('MACD', 0.0))
    macd_sig = float(latest.get('MACD_Signal', 0.0))
    
    # Assess technical trend
    trend = "상승 추세" if current_price >= sma25 else "하락 추세"
    ma_cross = "골든 크로스 (MA25 이평선이 MA45 이평선 상회)" if sma25 > sma45 else "데드 크로스 (MA25 이평선이 MA45 이평선 하회)"
    
    # Assess RSI level
    rsi_state = "과매수 상태 (과열 위험)" if rsi >= 70 else ("과매도 상태 (반등 기회)" if rsi <= 30 else "중립 상태")
    
    # Extract news sentiment metrics
    sentiment_score = news_sentiment.get('score', 0.0)
    sentiment_label = news_sentiment.get('label', 'NEUTRAL')
    sentiment_reason = news_sentiment.get('reason', '수집된 뉴스가 없거나 분석되지 않았습니다.')
    
    # Formulate a baseline recommendation rule-based
    score_points = 0
    if current_price >= sma25: score_points += 1
    if sma25 > sma45: score_points += 1
    if rsi < 35: score_points += 2 # Highly oversold buy signal
    elif rsi > 65: score_points -= 2 # Highly overbought sell signal
    
    if sentiment_score > 0.2: score_points += 1
    elif sentiment_score < -0.2: score_points -= 1
    
    if score_points >= 3:
        opinion = "STRONG BUY"
        opinion_kr = "적극 매수"
    elif score_points == 1 or score_points == 2:
        opinion = "BUY"
        opinion_kr = "매수"
    elif score_points == 0 or score_points == -1:
        opinion = "HOLD"
        opinion_kr = "관망 (Hold)"
    elif score_points == -2 or score_points == -3:
        opinion = "SELL"
        opinion_kr = "매도"
    else:
        opinion = "STRONG SELL"
        opinion_kr = "적극 매도"

    # Configure Gemini API Key
    key = api_key or os.getenv("GEMINI_API_KEY")
    
    # Check if API key is valid
    if not key or key == "YOUR_GEMINI_API_KEY_HERE" or key.strip() == "":
        # Fallback: Return a detailed, highly structured, rule-based generated template report
        risk_guide = "해당 자산은 고변동성 자산(레버리지 ETF 또는 ETN)이므로, 급격한 변동에 대응할 수 있도록 비중 조절이 필수적입니다."
        if "3X" in name or "레버리지" in name or ticker in ['SOXL', 'TECL', 'TQQQ', 'UPRO', '520054', '520098']:
            risk_guide = "이 자산은 **3배 또는 2배 레버리지 상품**으로, 방향성 추종 실패 시 '음의 복리 효과(Volatility Drag)'로 장기 보유 시 손실이 극대화될 수 있습니다. 단기 추세 반전 시 즉각적인 대응을 권장합니다."
            
        report_md = f"""### 📊 {name} ({ticker}) AI 에이전트 종합 리포트 (Fallback)

> [!NOTE]
> *본 리포트는 Gemini API 키 미등록 상태로 인해 자체 퀀트 규칙 기반 엔진에 의해 생성되었습니다.*

#### **1. 종합 투자 의견: ** `[{opinion_kr}]`
현재 기술 지표 및 로컬 뉴스 센티먼트 필터를 종합해 볼 때, 단기적으로 **{opinion_kr}** 포지션을 제안합니다. (퀀트 채점 스코어: {score_points}/4)

#### **2. 기술적 지표 상세 진단**
*   **가격 및 이동평균선:** 현재 주가는 `{current_price:,.2f}` 수준으로 25일 이동평균선(`{sma25:,.2f}`) 대비 **{'위' if current_price >= sma25 else '아래'}**에 위치하여, 단기 **{trend}**를 보이고 있습니다.
*   **이평선 교차 상태:** `{ma_cross}` 상태로, 중장기 흐름이 견조한 편입니다. (MA10: `{sma10:,.2f}`, MA25: `{sma25:,.2f}`, MA45: `{sma45:,.2f}`)
*   **상대강도지수 (RSI):** RSI 수치가 **`{rsi:.1f}`**를 기록하며 현재 **{rsi_state}**입니다.
*   **MACD 모멘텀:** MACD 수치(`{macd:.4f}`)와 Signal선(`{macd_sig:.4f}`)의 괴리는 `{macd - macd_sig:.4f}`로, 단기 모멘텀의 {'상승' if macd > macd_sig else '하락'} 압력이 작용하고 있습니다.

#### **3. 뉴스 및 감성 평가**
*   **대표 감성 라벨:** `[{sentiment_label}]` (스코어: `{sentiment_score:+.2f}`)
*   **분석 요약:** *"{sentiment_reason}"*

#### **4. 리스크 요인 및 매매 가이드**
*   {risk_guide}
*   **목표가(단기):** `{current_price * 1.15:,.2f}` (+15%) | **손절가(단기):** `{current_price * 0.90:,.2f}` (-10%)
"""
        return {
            "opinion": opinion,
            "opinion_kr": opinion_kr,
            "report_markdown": report_md,
            "score": score_points,
            "mock": True
        }

    # Real Gemini Generation with dynamic model fallback
    try:
        genai.configure(api_key=key)
        
        models_to_try = [
            'gemini-3.5-flash',
            'gemini-3.5-pro',
            'gemini-3.1-pro',
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
            print(f"Report: list_models failed (using default fallback list): {str(list_err)}")
            
        prompt = f"""
        당신은 금융 및 주식 투자 전문가인 'Allen AI 퀀트 포트폴리오 매니저'입니다.
        아래 제공되는 최신 기술적 지표 데이터와 뉴스 감성 분석 요약을 종합하여, 고객에게 보고할 수 있는 매우 전문적이고 세련된 **투자 권고 리포트**를 작성해 주세요.
        
        [분석 대상 자산]
        - 티커: {ticker}
        - 자산명: {name}
        
        [실시간 기술적 지표]
        - 현재가: {current_price:,.2f}
        - 10일 이동평균선(SMA_10): {sma10:,.2f}
        - 25일 이동평균선(SMA_25): {sma25:,.2f}
        - 45일 이동평균선(SMA_45): {sma45:,.2f}
        - 상대강도지수(RSI): {rsi:.2f}
        - MACD: {macd:.4f} (Signal: {macd_sig:.4f})
        - 추세 평가: {trend} / {ma_cross} / {rsi_state}
        
        [최근 뉴스 감성 요약]
        - 감성 분류: {sentiment_label} (센티먼트 스코어: {sentiment_score:+.2f})
        - 핵심 요약: {sentiment_reason}
        
        [작성 가이드라인]
        1. **종합 투자 의견**을 명확히 제시하십시오. (STRONG BUY, BUY, HOLD, SELL, STRONG SELL 중 택 1)
        2. **기술적 차트 진단**에서 이동평균선 돌파 및 RSI 과열 여부를 분석하십시오.
        3. **시장 센티먼트 진단**에서 최근 뉴스가 주는 시사점을 언급하십시오.
        4. 해당 자산의 특성(예: 3배 레버리지 ETF의 복리 갉아먹기 리스크 또는 한국형 배당 ETF/ETN의 특성)에 맞춰 **전문적인 리스크 가이드 및 단기 매매 대응법(목표가/손절가 제안 포함)**을 작성해 주십시오.
        5. 가독성이 뛰어난 GitHub 스타일 마크다운(Markdown) 포맷으로 작성해 주세요. 전문적이고 분석적인 어조를 사용하고 한국어로 대답하십시오.
        
        마지막에 아래 형식의 JSON 데이터 블록만 별도로 포함하거나 리포트 텍스트 뒤에 붙이지 말고,
        출력은 오직 마크다운 형식의 보고서 텍스트만 리턴하십시오.
        """
        
        last_error = None
        genai.configure(api_key=key)
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                report_md = response.text.strip()
                
                return {
                    "opinion": opinion,
                    "opinion_kr": opinion_kr,
                    "report_markdown": report_md,
                    "score": score_points,
                    "mock": False
                }
            except Exception as e:
                last_error = e
                print(f"Report fallback: Model {model_name} failed: {str(e)}")
                continue
                
        # If all models failed, raise the last exception to let the outer block handle it
        raise last_error
        
    except Exception as e:
        print(f"Gemini Report Generation Error: {str(e)}")
        return {
            "opinion": "HOLD",
            "opinion_kr": "관망 (Hold)",
            "report_markdown": f"### ⚠️ AI 에이전트 리포트 생성 실패\n\n오류: {str(e)}",
            "score": 0,
            "mock": True
        }
