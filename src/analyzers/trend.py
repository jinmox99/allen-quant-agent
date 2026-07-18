import pandas as pd

def analyze_trend(df: pd.DataFrame) -> dict:
    """
    Analyzes technical indicators and returns individual signals for SMA, MACD, and others.
    """
    if df.empty or len(df) < 50:
        default_signal = {"status": "데이터 부족", "message": "데이터가 부족합니다.", "color": "#94a3b8"}
        return {
            "sma": default_signal,
            "macd": default_signal,
            "quant_momentum": default_signal,
            "ema_cross": default_signal,
            "dual_momentum": default_signal,
            "adx_trend": default_signal,
            "stochastic": default_signal,
            "ichimoku": default_signal,
            "obv": default_signal,
            "parabolic_sar": default_signal,
            "vwap": default_signal
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

    import numpy as np
    # 9. Dual Momentum
    c1 = latest['Close_1M_ago'] if 'Close_1M_ago' in latest and not np.isnan(latest['Close_1M_ago']) else 0
    c3 = latest['Close_3M_ago'] if 'Close_3M_ago' in latest and not np.isnan(latest['Close_3M_ago']) else 0
    c6 = latest['Close_6M_ago'] if 'Close_6M_ago' in latest and not np.isnan(latest['Close_6M_ago']) else 0
    
    cond1 = (close > c1) if c1 > 0 else True
    cond3 = (close > c3) if c3 > 0 else True
    cond6 = (close > c6) if c6 > 0 else True

    if cond1 and cond3 and cond6:
        signals["dual_momentum"] = {"status": "트리플 크라운 (홀딩)", "message": "1, 3, 6개월 단기/중기/장기 모멘텀이 모두 살아있는 강력한 상승장입니다.", "color": "#10b981"}
    elif (not cond1) and (not cond3):
        signals["dual_momentum"] = {"status": "모멘텀 붕괴 (현금화)", "message": "단기와 중기 모멘텀이 모두 꺾였습니다. 리스크 관리를 위해 전량 현금화가 필요합니다.", "color": "#ef4444"}
    else:
        signals["dual_momentum"] = {"status": "혼조세", "message": "타임프레임별 모멘텀이 엇갈리고 있습니다.", "color": "#f59e0b"}

    # 10. ADX Trend
    adx = latest['ADX'] if 'ADX' in latest and not np.isnan(latest['ADX']) else 0
    plus_di = latest['Plus_DI'] if 'Plus_DI' in latest and not np.isnan(latest['Plus_DI']) else 0
    minus_di = latest['Minus_DI'] if 'Minus_DI' in latest and not np.isnan(latest['Minus_DI']) else 0
    if adx > 25 and plus_di > minus_di:
        signals["adx_trend"] = {"status": f"강한 상승 추세 (ADX {adx:.0f})", "message": f"+DI({plus_di:.0f})가 -DI({minus_di:.0f})를 압도하며 강력한 상승 추세가 확인됩니다.", "color": "#10b981"}
    elif adx > 25 and minus_di > plus_di:
        signals["adx_trend"] = {"status": f"강한 하락 추세 (ADX {adx:.0f})", "message": f"-DI({minus_di:.0f})가 +DI({plus_di:.0f})를 압도하며 하락 추세가 강합니다.", "color": "#ef4444"}
    elif adx < 20:
        signals["adx_trend"] = {"status": f"추세 없음 (ADX {adx:.0f})", "message": "ADX가 20 미만으로 뚜렷한 추세가 없는 횡보 구간입니다.", "color": "#64748b"}
    else:
        signals["adx_trend"] = {"status": f"추세 형성 중 (ADX {adx:.0f})", "message": "추세가 형성되기 시작하는 단계입니다. 방향 확인이 필요합니다.", "color": "#f59e0b"}

    # 11. Stochastic
    stoch_k = latest['Stoch_K'] if 'Stoch_K' in latest and not np.isnan(latest['Stoch_K']) else 50
    stoch_d = latest['Stoch_D'] if 'Stoch_D' in latest and not np.isnan(latest['Stoch_D']) else 50
    if stoch_k < 20:
        signals["stochastic"] = {"status": f"과매도 구간 (%K={stoch_k:.0f})", "message": "극단적 과매도 영역으로, 반등 가능성이 높습니다.", "color": "#38bdf8"}
    elif stoch_k > 80:
        signals["stochastic"] = {"status": f"과매수 구간 (%K={stoch_k:.0f})", "message": "극단적 과매수 영역으로, 조정 가능성이 있습니다.", "color": "#f43f5e"}
    elif stoch_k > stoch_d:
        signals["stochastic"] = {"status": f"상승 모멘텀 (%K={stoch_k:.0f})", "message": "%K가 %D 위에서 상승 탄력을 유지하고 있습니다.", "color": "#10b981"}
    else:
        signals["stochastic"] = {"status": f"하락 모멘텀 (%K={stoch_k:.0f})", "message": "%K가 %D 아래로 내려가며 하락 압력이 존재합니다.", "color": "#ef4444"}

    # 12. Ichimoku Cloud
    span_a = latest['Ichimoku_SpanA'] if 'Ichimoku_SpanA' in latest and not np.isnan(latest['Ichimoku_SpanA']) else close
    span_b = latest['Ichimoku_SpanB'] if 'Ichimoku_SpanB' in latest and not np.isnan(latest['Ichimoku_SpanB']) else close
    cloud_top = max(span_a, span_b)
    cloud_bottom = min(span_a, span_b)
    if close > cloud_top:
        signals["ichimoku"] = {"status": "구름대 위 (상승장)", "message": "주가가 구름대 위에 있어 강한 상승 추세가 확인됩니다.", "color": "#10b981"}
    elif close < cloud_bottom:
        signals["ichimoku"] = {"status": "구름대 아래 (하락장)", "message": "주가가 구름대 아래에 있어 하락 추세가 지속되고 있습니다.", "color": "#ef4444"}
    else:
        signals["ichimoku"] = {"status": "구름대 내부 (방향 탐색)", "message": "주가가 구름대 안에서 방향을 결정하는 중입니다.", "color": "#f59e0b"}

    # 13. OBV
    if 'OBV' in latest and 'OBV_MA' in latest and not np.isnan(latest['OBV']) and not np.isnan(latest['OBV_MA']):
        obv = latest['OBV']
        obv_ma = latest['OBV_MA']
        if obv > obv_ma:
            signals["obv"] = {"status": "매집 진행 중", "message": "OBV가 20일 평균 위에 있어 세력의 매집이 감지됩니다.", "color": "#10b981"}
        else:
            signals["obv"] = {"status": "분배 진행 중", "message": "OBV가 20일 평균 아래로, 세력의 매도(분배)가 진행 중입니다.", "color": "#ef4444"}
    else:
        signals["obv"] = {"status": "데이터 없음", "message": "거래량 데이터가 없어 OBV를 계산할 수 없습니다.", "color": "#64748b"}

    # 14. Parabolic SAR
    if 'PSAR' in latest and not np.isnan(latest['PSAR']):
        psar = latest['PSAR']
        if close > psar:
            signals["parabolic_sar"] = {"status": "상승 추세 (SAR 아래)", "message": "SAR 점이 주가 아래에 위치하여 상승 추세를 지지합니다.", "color": "#10b981"}
        else:
            signals["parabolic_sar"] = {"status": "하락 추세 (SAR 위)", "message": "SAR 점이 주가 위에 위치하여 하락 압력이 존재합니다.", "color": "#ef4444"}
    else:
        signals["parabolic_sar"] = {"status": "계산 불가", "message": "데이터 부족으로 SAR을 계산할 수 없습니다.", "color": "#64748b"}

    # 15. VWAP
    if 'VWAP' in latest and not np.isnan(latest['VWAP']):
        vwap = latest['VWAP']
        if close > vwap:
            signals["vwap"] = {"status": "VWAP 상회 (매수 우위)", "message": "주가가 거래량가중평균가 위에 있어 기관 매수 우위 구간입니다.", "color": "#10b981"}
        else:
            signals["vwap"] = {"status": "VWAP 하회 (매도 우위)", "message": "주가가 거래량가중평균가 아래에 있어 매도 압력이 우세합니다.", "color": "#ef4444"}
    else:
        signals["vwap"] = {"status": "데이터 없음", "message": "거래량 데이터가 없어 VWAP을 계산할 수 없습니다.", "color": "#64748b"}

    return signals
