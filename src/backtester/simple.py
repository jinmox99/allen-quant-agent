import pandas as pd
import numpy as np

def run_indicator_backtests(df: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
    """
    Runs simple backtests on technical indicators and smart strategies.
    Returns a dictionary mapping strategy names to a dict with 'return' and 'trades' list.
    """
    if df.empty or len(df) < 20:
        return {}

    # Date handling
    # Depending on yfinance format, Date might be index or a column. Ensure it's a string format for plotting
    if 'Date' not in df.columns:
        dates = df.index.strftime('%Y-%m-%d')
    else:
        # Check if Date is datetime type
        if pd.api.types.is_datetime64_any_dtype(df['Date']):
            dates = df['Date'].dt.strftime('%Y-%m-%d')
        else:
            dates = df['Date'].astype(str)

    start_price = float(df['Close'].iloc[0])
    end_price = float(df['Close'].iloc[-1])

    def calculate_mdd(history):
        if not history: return 0.0
        import numpy as np
        arr = np.array(history)
        peaks = np.maximum.accumulate(arr)
        drawdowns = (peaks - arr) / peaks
        return float(np.max(drawdowns) * 100)

    bh_return = ((end_price - start_price) / start_price) * 100
    bh_history = (df['Close'] / start_price * initial_capital).tolist()
    bh_mdd = calculate_mdd(bh_history)
    bh_trades = [{"Date": dates.iloc[0], "Action": "BUY", "Price": start_price, "Shares": initial_capital / start_price, "Reason": "첫날 전액 매수"}]

    def simulate(signals: pd.Series, desc: str) -> dict:
        cash = initial_capital
        shares = 0.0
        trades = []
        history = []
        for i in range(len(df)):
            sig = signals.iloc[i]
            price = float(df['Close'].iloc[i])
            date_str = dates.iloc[i]
            
            if sig == 1 and cash > 0:
                shares = cash / price
                trades.append({"Date": date_str, "Action": "BUY", "Price": price, "Shares": shares, "Reason": "조건 만족: 전액 매수"})
                cash = 0.0
            elif sig == -1 and shares > 0:
                cash = shares * price
                trades.append({"Date": date_str, "Action": "SELL", "Price": price, "Shares": shares, "Reason": "조건 만족: 전액 매도"})
                shares = 0.0
            history.append(cash + shares * price)
                
        final_value = cash + (shares * end_price)
        return {
            "return": ((final_value - initial_capital) / initial_capital) * 100,
            "mdd": calculate_mdd(history),
            "trades": trades,
            "desc": desc
        }

    # 1. SMA Signals
    sma_sig = pd.Series(0, index=df.index)
    sma_sig[df['Close'] > df['SMA_20']] = 1
    sma_sig[df['Close'] < df['SMA_20']] = -1
    
    # 2. MACD Signals
    macd_sig = pd.Series(0, index=df.index)
    macd_sig[df['MACD'] > df['MACD_Signal']] = 1
    macd_sig[df['MACD'] < df['MACD_Signal']] = -1
    
    # 3. (RSI/BB removed)

    # ==========================================
    # Smart Strategies
    # ==========================================
    
    def simulate_quant_momentum():
        desc = "Buy&Hold를 이기기 위한 알파 추구형 전략입니다. 100% 주식으로 시작하며 자잘한 하락에는 흔들리지 않고 보유합니다. 주가가 20일선 아래로 무너지고 동시에 MACD마저 데드크로스가 났을 때만 '진짜 폭락장'으로 간주하여 100% 현금화(전액 매도)로 대피합니다. 이후 둘 중 하나라도 회복되면 즉시 상승장에 100% 재탑승합니다."
        cash = 0.0
        shares = initial_capital / float(df['Close'].iloc[0])
        history = [initial_capital]
        trades = [{"Date": dates.iloc[0], "Action": "BUY", "Price": float(df['Close'].iloc[0]), "Shares": shares, "Reason": "초기 100% 매수"}]
        
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            sma20 = float(df['SMA_20'].iloc[i]) if not np.isnan(df['SMA_20'].iloc[i]) else 0
            macd = float(df['MACD'].iloc[i]) if not np.isnan(df['MACD'].iloc[i]) else 0
            macd_signal = float(df['MACD_Signal'].iloc[i]) if not np.isnan(df['MACD_Signal'].iloc[i]) else 0
            date_str = dates.iloc[i]
            
            # 매도 (진짜 폭락장 대피)
            if (close_p < sma20 and macd < macd_signal) and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": "추세/모멘텀 붕괴 (100% 대피)"})
                shares = 0.0
                
            # 매수 (상승장 재탑승)
            elif (close_p > sma20 or macd > macd_signal) and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": "상승 추세 회복 (100% 재탑승)"})
                cash = 0.0
            history.append(cash + shares * close_p)
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    def simulate_adx_trend():
        desc = "ADX(평균방향지수)로 추세의 '강도'를 측정합니다. ADX가 25를 넘고 +DI가 -DI 위에 있으면 강한 상승 추세로 판단하여 매수하고, ADX가 20 아래로 떨어지거나 -DI가 +DI를 상회하면 추세 소멸로 매도합니다."
        cash = initial_capital
        shares = 0.0
        trades = []
        history = [initial_capital]
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            adx = float(df['ADX'].iloc[i]) if 'ADX' in df.columns and not np.isnan(df['ADX'].iloc[i]) else 0
            plus_di = float(df['Plus_DI'].iloc[i]) if 'Plus_DI' in df.columns and not np.isnan(df['Plus_DI'].iloc[i]) else 0
            minus_di = float(df['Minus_DI'].iloc[i]) if 'Minus_DI' in df.columns and not np.isnan(df['Minus_DI'].iloc[i]) else 0
            date_str = dates.iloc[i]
            if adx > 25 and plus_di > minus_di and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": f"ADX {adx:.0f} 강한 상승 추세 (+DI > -DI)"})
                cash = 0.0
            elif (adx < 20 or minus_di > plus_di) and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": f"ADX {adx:.0f} 추세 소멸 또는 하락 전환"})
                shares = 0.0
            history.append(cash + shares * close_p)
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    def simulate_stochastic():
        desc = "스토캐스틱 오실레이터로 과매수/과매도를 탐지합니다. %K가 %D를 상향 돌파하며 20 이하(과매도)에서 올라오면 매수, %K가 %D를 하향 돌파하며 80 이상(과매수)에서 내려오면 매도합니다."
        cash = initial_capital
        shares = 0.0
        trades = []
        history = [initial_capital]
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            k = float(df['Stoch_K'].iloc[i]) if 'Stoch_K' in df.columns and not np.isnan(df['Stoch_K'].iloc[i]) else 50
            d = float(df['Stoch_D'].iloc[i]) if 'Stoch_D' in df.columns and not np.isnan(df['Stoch_D'].iloc[i]) else 50
            k_prev = float(df['Stoch_K'].iloc[i-1]) if 'Stoch_K' in df.columns and not np.isnan(df['Stoch_K'].iloc[i-1]) else 50
            d_prev = float(df['Stoch_D'].iloc[i-1]) if 'Stoch_D' in df.columns and not np.isnan(df['Stoch_D'].iloc[i-1]) else 50
            date_str = dates.iloc[i]
            if k_prev <= d_prev and k > d and k < 30 and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": f"스토캐스틱 골든크로스 (%K={k:.0f}, 과매도 탈출)"})
                cash = 0.0
            elif k_prev >= d_prev and k < d and k > 70 and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": f"스토캐스틱 데드크로스 (%K={k:.0f}, 과매수 이탈)"})
                shares = 0.0
            history.append(cash + shares * close_p)
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    def simulate_ichimoku():
        desc = "일본 전통 기술분석 '일목균형표(이치모쿠 구름)' 전략입니다. 주가가 구름대(선행스팬A·B 사이) 위로 올라서면 상승장으로 매수, 구름대 아래로 떨어지면 하락장으로 매도합니다. 구름대가 두꺼울수록 지지/저항이 강합니다."
        cash = initial_capital
        shares = 0.0
        trades = []
        history = [initial_capital]
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            span_a = float(df['Ichimoku_SpanA'].iloc[i]) if 'Ichimoku_SpanA' in df.columns and not np.isnan(df['Ichimoku_SpanA'].iloc[i]) else close_p
            span_b = float(df['Ichimoku_SpanB'].iloc[i]) if 'Ichimoku_SpanB' in df.columns and not np.isnan(df['Ichimoku_SpanB'].iloc[i]) else close_p
            cloud_top = max(span_a, span_b)
            cloud_bottom = min(span_a, span_b)
            date_str = dates.iloc[i]
            if close_p > cloud_top and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": "구름대 상단 돌파 (상승장 진입)"})
                cash = 0.0
            elif close_p < cloud_bottom and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": "구름대 하단 이탈 (하락장 전환)"})
                shares = 0.0
            history.append(cash + shares * close_p)
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    def simulate_obv():
        desc = "OBV(거래량균형지표)로 세력의 매집/분배를 감지합니다. OBV가 20일 이동평균 위로 올라서면 세력이 매집 중으로 판단하여 매수, 아래로 떨어지면 분배(매도 중)로 판단하여 매도합니다."
        cash = initial_capital
        shares = 0.0
        trades = []
        history = [initial_capital]
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            obv = float(df['OBV'].iloc[i]) if 'OBV' in df.columns and not np.isnan(df['OBV'].iloc[i]) else 0
            obv_ma = float(df['OBV_MA'].iloc[i]) if 'OBV_MA' in df.columns and not np.isnan(df['OBV_MA'].iloc[i]) else 0
            obv_prev = float(df['OBV'].iloc[i-1]) if 'OBV' in df.columns and not np.isnan(df['OBV'].iloc[i-1]) else 0
            obv_ma_prev = float(df['OBV_MA'].iloc[i-1]) if 'OBV_MA' in df.columns and not np.isnan(df['OBV_MA'].iloc[i-1]) else 0
            date_str = dates.iloc[i]
            if obv_prev <= obv_ma_prev and obv > obv_ma and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": "OBV 매집 신호 (OBV > 20일 평균)"})
                cash = 0.0
            elif obv_prev >= obv_ma_prev and obv < obv_ma and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": "OBV 분배 신호 (OBV < 20일 평균)"})
                shares = 0.0
            history.append(cash + shares * close_p)
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    def simulate_parabolic_sar():
        desc = "파라볼릭 SAR(Stop And Reverse) 전략입니다. SAR 점이 주가 아래에 있으면 상승 추세로 매수, SAR 점이 주가 위로 올라오면 추세 반전으로 매도합니다. 후행 스톱로스 역할도 합니다."
        cash = initial_capital
        shares = 0.0
        trades = []
        history = [initial_capital]
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            sar = float(df['PSAR'].iloc[i]) if 'PSAR' in df.columns and not np.isnan(df['PSAR'].iloc[i]) else close_p
            sar_prev = float(df['PSAR'].iloc[i-1]) if 'PSAR' in df.columns and not np.isnan(df['PSAR'].iloc[i-1]) else close_p
            close_prev = float(df['Close'].iloc[i-1])
            date_str = dates.iloc[i]
            # 매수: SAR이 가격 위에서 아래로 내려옴 (추세 상승 전환)
            if sar_prev > close_prev and sar < close_p and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": "SAR 상승 전환 (점이 가격 아래로)"})
                cash = 0.0
            # 매도: SAR이 가격 아래에서 위로 올라옴 (추세 하락 전환)
            elif sar_prev < close_prev and sar > close_p and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": "SAR 하락 전환 (점이 가격 위로)"})
                shares = 0.0
            history.append(cash + shares * close_p)
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    def simulate_vwap():
        desc = "VWAP(거래량가중평균가) 전략입니다. 기관 투자자들이 가장 많이 참고하는 지표로, 주가가 VWAP 위에 있으면 매수 우위, 아래에 있으면 매도 우위로 판단합니다. VWAP 상향 돌파 시 매수, 하향 이탈 시 매도합니다."
        cash = initial_capital
        shares = 0.0
        trades = []
        history = [initial_capital]
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            vwap = float(df['VWAP'].iloc[i]) if 'VWAP' in df.columns and not np.isnan(df['VWAP'].iloc[i]) else close_p
            close_prev = float(df['Close'].iloc[i-1])
            vwap_prev = float(df['VWAP'].iloc[i-1]) if 'VWAP' in df.columns and not np.isnan(df['VWAP'].iloc[i-1]) else close_prev
            date_str = dates.iloc[i]
            if close_prev <= vwap_prev and close_p > vwap and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": "VWAP 상향 돌파 (기관 매수 구간)"})
                cash = 0.0
            elif close_prev >= vwap_prev and close_p < vwap and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": "VWAP 하향 이탈 (기관 매도 구간)"})
                shares = 0.0
            history.append(cash + shares * close_p)
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    return {
        "단순 보유 (Buy & Hold)": {"return": bh_return, "mdd": bh_mdd, "trades": bh_trades, "desc": "가장 기본이 되는 벤치마크. 첫날에 현금을 전액 주식에 몰빵한 뒤, 끝까지 가만히 들고 있었을 경우의 수익률입니다."},
        "이동평균선 (SMA)": simulate(sma_sig, "주가가 20일선 위로 올라타면 전액 매수, 20일선 밑으로 깨고 내려가면 전액 매도합니다. 대세 추세를 따라갈 때 유리합니다."),
        "MACD": simulate(macd_sig, "단기 추세선이 장기 추세선을 상향 돌파(골든크로스)하면 전액 매수, 하향 돌파(데드크로스)하면 전액 매도합니다."),
        "💎 퀀트 모멘텀 (알파 추구형)": simulate_quant_momentum(),
        "💎 ⚡ 골든크로스 EMA (5/20)": simulate_ema_cross(),
        "💎 🛡️ 듀얼 모멘텀": simulate_dual_momentum(),
        "📊 ADX 추세 강도": simulate_adx_trend(),
        "🔄 스토캐스틱": simulate_stochastic(),
        "☁️ 이치모쿠 구름": simulate_ichimoku(),
        "📦 OBV 거래량 균형": simulate_obv(),
        "🔴 파라볼릭 SAR": simulate_parabolic_sar(),
        "🏛️ VWAP 기관 추종": simulate_vwap()
    }
