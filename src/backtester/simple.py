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
    bh_return = ((end_price - start_price) / start_price) * 100
    bh_trades = [{"Date": dates.iloc[0], "Action": "BUY", "Price": start_price, "Shares": initial_capital / start_price, "Reason": "첫날 전액 매수"}]

    def simulate(signals: pd.Series, desc: str) -> dict:
        cash = initial_capital
        shares = 0.0
        trades = []
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
                
        final_value = cash + (shares * end_price)
        return {
            "return": ((final_value - initial_capital) / initial_capital) * 100,
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
    
    # 3. RSI Signals
    rsi_sig = pd.Series(0, index=df.index)
    rsi_sig[df['RSI'] <= 30] = 1
    rsi_sig[df['RSI'] >= 70] = -1
    
    # 4. BB Signals
    bb_sig = pd.Series(0, index=df.index)
    bb_sig[(df['Low'] <= df['BB_Lower']) | (df['Close'] <= df['BB_Lower']*1.01)] = 1
    bb_sig[(df['High'] >= df['BB_Upper']) | (df['Close'] >= df['BB_Upper']*0.99)] = -1

    # ==========================================
    # Smart Strategy: 퀀트 모멘텀 (알파 추구형)
    # ==========================================
    
    def simulate_quant_momentum():
        desc = "Buy&Hold를 이기기 위한 알파 추구형 전략입니다. 100% 주식으로 시작하며 자잘한 하락에는 흔들리지 않고 보유합니다. 주가가 20일선 아래로 무너지고 동시에 MACD마저 데드크로스가 났을 때만 '진짜 폭락장'으로 간주하여 100% 현금화(전액 매도)로 대피합니다. 이후 둘 중 하나라도 회복되면 즉시 상승장에 100% 재탑승합니다."
        cash = 0.0
        shares = initial_capital / float(df['Close'].iloc[0])
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
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "trades": trades, "desc": desc}

    return {
        "단순 보유 (Buy & Hold)": {"return": bh_return, "trades": bh_trades, "desc": "가장 기본이 되는 벤치마크. 첫날에 현금을 전액 주식에 몰빵한 뒤, 끝까지 가만히 들고 있었을 경우의 수익률입니다."},
        "이동평균선 (SMA)": simulate(sma_sig, "주가가 20일선 위로 올라타면 전액 매수, 20일선 밑으로 깨고 내려가면 전액 매도합니다. 대세 추세를 따라갈 때 유리합니다."),
        "MACD": simulate(macd_sig, "단기 추세선이 장기 추세선을 상향 돌파(골든크로스)하면 전액 매수, 하향 돌파(데드크로스)하면 전액 매도합니다."),
        "RSI": simulate(rsi_sig, "RSI가 30 이하(과매도)로 떨어지면 싼 값이라 판단해 전액 매수, 70 이상(과매수)으로 올라가면 비싸다 판단해 전액 매도합니다."),
        "볼린저 밴드 (BB)": simulate(bb_sig, "주가가 볼린저 밴드 하단에 닿거나 뚫고 내려가면 전액 매수, 밴드 상단에 닿거나 뚫고 올라가면 전액 매도합니다."),
        "💎 퀀트 모멘텀 (알파 추구형)": simulate_quant_momentum()
    }
