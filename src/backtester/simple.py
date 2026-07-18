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

    def simulate_ema_cross():
        desc = "반응이 느린 단순이동평균(SMA) 대신, 최근 가격에 가중치를 두어 반응을 극한으로 끌어올린 지수이동평균(EMA) 5일선과 20일선의 교차 전략입니다. 단기 5일선이 장기 20일선을 위로 뚫으면(골든크로스) 매수하고, 아래로 뚫으면(데드크로스) 칼같이 매도하여 하락장을 빠르게 피합니다."
        cash = initial_capital
        shares = 0.0
        trades = []
        history = [initial_capital]
        
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            ema5_prev = float(df['EMA_5'].iloc[i-1]) if 'EMA_5' in df.columns and not np.isnan(df['EMA_5'].iloc[i-1]) else 0
            ema20_prev = float(df['EMA_20'].iloc[i-1]) if 'EMA_20' in df.columns and not np.isnan(df['EMA_20'].iloc[i-1]) else 0
            ema5 = float(df['EMA_5'].iloc[i]) if 'EMA_5' in df.columns and not np.isnan(df['EMA_5'].iloc[i]) else 0
            ema20 = float(df['EMA_20'].iloc[i]) if 'EMA_20' in df.columns and not np.isnan(df['EMA_20'].iloc[i]) else 0
            date_str = dates.iloc[i]
            
            # 골든크로스 매수
            if (ema5_prev <= ema20_prev and ema5 > ema20) and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": "EMA 5/20 골든크로스 (단기 상승)"})
                cash = 0.0
                
            # 데드크로스 매도
            elif (ema5_prev >= ema20_prev and ema5 < ema20) and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": "EMA 5/20 데드크로스 (단기 하락)"})
                shares = 0.0
            history.append(cash + shares * close_p)
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    def simulate_dual_momentum():
        desc = "1개월, 3개월, 6개월 전 주가와 비교하여 모든 기간에서 주가가 상승했을 때만 100% 주식을 보유하고, 단기 추세가 꺾이면 전량 현금화하는 극강의 방어형 전략입니다."
        cash = initial_capital
        shares = 0.0
        trades = []
        history = []
        for i in range(len(df)):
            close = float(df['Close'].iloc[i])
            c1 = float(df['Close_1M_ago'].iloc[i]) if 'Close_1M_ago' in df.columns and not np.isnan(df['Close_1M_ago'].iloc[i]) else 0
            c3 = float(df['Close_3M_ago'].iloc[i]) if 'Close_3M_ago' in df.columns and not np.isnan(df['Close_3M_ago'].iloc[i]) else 0
            c6 = float(df['Close_6M_ago'].iloc[i]) if 'Close_6M_ago' in df.columns and not np.isnan(df['Close_6M_ago'].iloc[i]) else 0
            date_str = dates.iloc[i]
            
            cond1 = (close > c1) if c1 > 0 else True
            cond3 = (close > c3) if c3 > 0 else True
            cond6 = (close > c6) if c6 > 0 else True
            
            # 매수: 1, 3, 6개월 전보다 현재 주가가 모두 높을 때
            if cond1 and cond3 and cond6 and cash > 10:
                buy_shares = cash / close
                shares += buy_shares
                cash = 0.0
                trades.append({"Date": date_str, "Action": "BUY", "Price": close, "Shares": buy_shares, "Reason": "듀얼 모멘텀 (모든 추세 상승)"})
            # 매도: 1개월, 3개월 모멘텀이 모두 마이너스로 돌아서면
            elif (not cond1) and (not cond3) and shares > 0:
                sell_shares = shares
                cash += shares * close
                shares = 0.0
                trades.append({"Date": date_str, "Action": "SELL", "Price": close, "Shares": sell_shares, "Reason": "단기/중기 추세 꺾임 (현금화)"})
            history.append(cash + shares * close)
                
        val = cash + (shares * end_price)
        return {"return": ((val - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}

    return {
        "단순 보유 (Buy & Hold)": {"return": bh_return, "mdd": bh_mdd, "trades": bh_trades, "desc": "가장 기본이 되는 벤치마크. 첫날에 현금을 전액 주식에 몰빵한 뒤, 끝까지 가만히 들고 있었을 경우의 수익률입니다."},
        "이동평균선 (SMA)": simulate(sma_sig, "주가가 20일선 위로 올라타면 전액 매수, 20일선 밑으로 깨고 내려가면 전액 매도합니다. 대세 추세를 따라갈 때 유리합니다."),
        "MACD": simulate(macd_sig, "단기 추세선이 장기 추세선을 상향 돌파(골든크로스)하면 전액 매수, 하향 돌파(데드크로스)하면 전액 매도합니다."),
        "💎 퀀트 모멘텀 (알파 추구형)": simulate_quant_momentum(),
        "💎 ⚡ 골든크로스 EMA (5/20)": simulate_ema_cross(),
        "💎 🛡️ 듀얼 모멘텀": simulate_dual_momentum()
    }
