import pandas as pd

def analyze_trend(df: pd.DataFrame) -> dict:
    """
    Analyzes technical indicators and returns individual signals for SMA, MACD, RSI, and BB.
    """
    if df.empty or len(df) < 50:
        default_signal = {"status": "데이터 부족", "message": "데이터가 부족합니다.", "color": "#94a3b8"}
        return {

            "sma": default_signal,
            "macd": default_signal,
            "rsi": default_signal,
            "bb": default_signal,
            "quant_momentum": default_signal,
            "ema_cross": default_signal,
            "bb_squeeze": default_signal,
            "rsi_div": default_signal,
            "dual_momentum": default_signal
        }
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    close = latest['Close']
    sma20 = latest['SMA_20']
    sma50 = latest['SMA_50']
    sma20_prev = prev['SMA_20']
    
    macd = latest['MACD']
    macd_signal = latest['MACD_Signal']
    macd_hist = latest['MACD_Hist']
    macd_hist_prev = prev['MACD_Hist']
    
    rsi = latest['RSI']
    bb_lower = latest['BB_Lower']
    bb_upper = latest['BB_Upper']
    low = latest['Low']
    high = latest['High']
    
    signals = {}
    
    # 1. SMA (이동평균선) 분석
    if close < sma20 and sma20 < sma50:
        signals["sma"] = {"status": "역배열 하락세", "message": "주가가 20일선 아래에 있으며, 20일선이 50일선 아래인 완연한 하락 추세입니다.", "color": "#ef4444"}
    elif close > sma20 and sma20 > sma50:
        signals["sma"] = {"status": "정배열 상승세", "message": "단기, 중기 이평선이 정배열을 이루며 탄탄한 상승 추세를 그리고 있습니다.", "color": "#10b981"}
    elif sma20 < sma20_prev and close < sma20:
        signals["sma"] = {"status": "단기 하락 전환", "message": "20일선이 꺾이고 주가가 그 아래로 내려가 단기 하락(조정)이 진행 중입니다.", "color": "#f43f5e"}
    elif sma20 > sma20_prev and close > sma20:
        signals["sma"] = {"status": "단기 반등세", "message": "20일선 위로 주가가 올라타며 단기적인 반등세가 나타나고 있습니다.", "color": "#34d399"}
    else:
        signals["sma"] = {"status": "방향성 탐색 중", "message": "이동평균선 간 거리가 좁혀지며 뚜렷한 추세가 없는 횡보 구간입니다.", "color": "#64748b"}

    # 2. MACD 분석
    if macd > macd_signal and macd_hist > macd_hist_prev:
        signals["macd"] = {"status": "강한 매수 시그널", "message": "MACD가 시그널을 상회하고 히스토그램이 커지는 상승 모멘텀 확장 구간입니다.", "color": "#10b981"}
    elif macd > macd_signal and macd_hist <= macd_hist_prev:
        signals["macd"] = {"status": "상승 둔화", "message": "MACD가 시그널 위에 있으나 상승 탄력이 점점 줄어들고 있습니다.", "color": "#f59e0b"}
    elif macd < macd_signal and macd_hist < macd_hist_prev:
        signals["macd"] = {"status": "강한 매도 시그널", "message": "MACD가 시그널을 하회하며 하락 모멘텀이 거세지고 있습니다.", "color": "#ef4444"}
    elif macd < macd_signal and macd_hist >= macd_hist_prev:
        signals["macd"] = {"status": "하락 둔화 (반등 조짐)", "message": "MACD가 시그널 아래에 있으나 하락폭이 좁혀지며 반등 에너지가 모이고 있습니다.", "color": "#38bdf8"}
    else:
        signals["macd"] = {"status": "중립 (신호 혼재)", "message": "MACD 뚜렷한 모멘텀을 보이지 않고 있습니다.", "color": "#64748b"}

    # 3. RSI 분석
    if rsi >= 70:
        signals["rsi"] = {"status": "과매수 (과열)", "message": f"RSI가 {rsi:.1f}로 과열 상태입니다. 단기 조정(하락)에 주의해야 합니다.", "color": "#ef4444"}
    elif rsi <= 30:
        signals["rsi"] = {"status": "과매도 (바닥권)", "message": f"RSI가 {rsi:.1f}로 심한 매도세가 있었습니다. 기술적 반등이 기대되는 구간입니다.", "color": "#a855f7"}
    else:
        signals["rsi"] = {"status": "안정권 (중립)", "message": f"RSI가 {rsi:.1f}로 과열이나 과매도 없이 안정적인 흐름을 보이고 있습니다.", "color": "#64748b"}

    # 4. Bollinger Bands (볼린저 밴드) 분석
    if low <= bb_lower or close <= bb_lower * 1.01:
        signals["bb"] = {"status": "하단 이탈 (투매 구간)", "message": "주가(꼬리 포함)가 밴드 하단을 찍거나 뚫었습니다. 강한 반등 저항선 역할을 기대할 수 있습니다.", "color": "#a855f7"}
    elif high >= bb_upper or close >= bb_upper * 0.99:
        signals["bb"] = {"status": "상단 돌파 (단기 고점)", "message": "주가가 밴드 상단에 도달했습니다. 차익 실현 매물이 나올 확률이 높습니다.", "color": "#f59e0b"}
    else:
        bb_width = (bb_upper - bb_lower) / latest['BB_Mid'] * 100
        if bb_width < 5:
            signals["bb"] = {"status": "밴드 수축 (응축기)", "message": "밴드 폭이 매우 좁아 변동성이 축소된 상태로, 조만간 큰 방향성 분출이 예상됩니다.", "color": "#38bdf8"}
        else:
            signals["bb"] = {"status": "정상 변동성 구간", "message": "주가가 밴드 안에서 정상적인 변동성을 보이며 움직이고 있습니다.", "color": "#64748b"}

    # 5. Quant Momentum (퀀트 모멘텀)
    if close < sma20 and macd < macd_signal:
        signals["quant_momentum"] = {"status": "위험 (폭락 징후)", "message": "추세선(20일)과 모멘텀(MACD)이 동시에 무너졌습니다. 전액 매도(100% 현금화)가 유리한 구간입니다.", "color": "#ef4444"}
    elif close > sma20 or macd > macd_signal:
        signals["quant_momentum"] = {"status": "양호 (추세 유지)", "message": "상승 추세 혹은 모멘텀이 살아있어 100% 주식을 보유하며 끝까지 수익을 극대화할 수 있는 구간입니다.", "color": "#10b981"}
    else:
        signals["quant_momentum"] = {"status": "방향 탐색", "message": "추세 판단의 경계선에 위치해 있습니다.", "color": "#64748b"}

    # 6. EMA Cross (골든크로스)
    ema5 = latest['EMA_5'] if 'EMA_5' in latest else 0
    ema20 = latest['EMA_20'] if 'EMA_20' in latest else 0
    if ema5 > ema20:
        signals["ema_cross"] = {"status": "상승 국면 (골든크로스)", "message": "반응이 빠른 5일 EMA가 20일 EMA 위로 올라선 단기 상승장입니다.", "color": "#10b981"}
    elif ema5 < ema20:
        signals["ema_cross"] = {"status": "하락 국면 (데드크로스)", "message": "5일 EMA가 20일 EMA 밑으로 떨어지며 단기 하락 압력이 커지고 있습니다.", "color": "#f43f5e"}
    else:
        signals["ema_cross"] = {"status": "교차 대기", "message": "단기선과 장기선이 겹쳐져 방향을 결정하는 중입니다.", "color": "#64748b"}

    # 7. BB Squeeze
    bb_width_prev = prev['BB_Width'] if 'BB_Width' in prev else 100
    if bb_width_prev < 5.0 and close > bb_upper:
        signals["bb_squeeze"] = {"status": "상단 돌파 (매수)", "message": "에너지를 꽉 응축한 스퀴즈 상태에서 상단을 뚫고 대세 상승을 시작했습니다.", "color": "#10b981"}
    elif bb_width_prev < 5.0:
        signals["bb_squeeze"] = {"status": "스퀴즈 (응축기)", "message": "밴드 폭이 매우 좁아 곧 큰 변동성이 터질 준비를 하고 있습니다.", "color": "#38bdf8"}
    else:
        signals["bb_squeeze"] = {"status": "정상 변동성", "message": "일반적인 밴드 변동성 구간입니다.", "color": "#64748b"}

    # 8. RSI Divergence
    min_rsi_prev = prev['Min_RSI_20'] if 'Min_RSI_20' in prev else 50
    min_close_prev = prev['Min_Close_20'] if 'Min_Close_20' in prev else close
    if close < min_close_prev and rsi > min_rsi_prev and rsi < 40:
        signals["rsi_div"] = {"status": "다이버전스 포착 (바닥 줍기)", "message": "주가는 신저가를 갱신했지만 RSI는 저점을 높이는 다이버전스가 발생했습니다. 강력한 바닥 매수 타이밍입니다.", "color": "#a855f7"}
    else:
        signals["rsi_div"] = {"status": "다이버전스 없음", "message": "특이한 RSI 다이버전스 패턴이 보이지 않습니다.", "color": "#64748b"}

    import numpy as np
    # 9. Dual Momentum
    c1 = latest['Close_1M_ago'] if 'Close_1M_ago' in latest and not np.isnan(latest['Close_1M_ago']) else close
    c3 = latest['Close_3M_ago'] if 'Close_3M_ago' in latest and not np.isnan(latest['Close_3M_ago']) else close
    c6 = latest['Close_6M_ago'] if 'Close_6M_ago' in latest and not np.isnan(latest['Close_6M_ago']) else close
    if close > c1 and close > c3 and close > c6:
        signals["dual_momentum"] = {"status": "트리플 크라운 (홀딩)", "message": "1, 3, 6개월 단기/중기/장기 모멘텀이 모두 살아있는 강력한 상승장입니다.", "color": "#10b981"}
    elif close < c1 and close < c3:
        signals["dual_momentum"] = {"status": "모멘텀 붕괴 (현금화)", "message": "단기와 중기 모멘텀이 모두 꺾였습니다. 리스크 관리를 위해 전량 현금화가 필요합니다.", "color": "#ef4444"}
    else:
        signals["dual_momentum"] = {"status": "혼조세", "message": "타임프레임별 모멘텀이 엇갈리고 있습니다.", "color": "#f59e0b"}

    return signals
