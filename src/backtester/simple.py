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
    # Smart Strategies (A, B, Hybrid)
    # ==========================================
    
    def simulate_strategy_A():
        desc = "100% 주식으로 시작. 지표가 과열(RSI >= 70 또는 볼린저 상단 돌파) 시 보유 주식의 30%를 익절하여 현금화합니다. 이후 주가가 20일선 밑으로 조정받을 때 모아둔 현금을 전액 재투자합니다."
        cash = 0.0
        shares = initial_capital / float(df['Close'].iloc[0])
        trades = [{"Date": dates.iloc[0], "Action": "BUY", "Price": float(df['Close'].iloc[0]), "Shares": shares, "Reason": "초기 100% 매수"}]
        
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            high_p = float(df['High'].iloc[i])
            rsi = float(df['RSI'].iloc[i]) if not np.isnan(df['RSI'].iloc[i]) else 50
            bb_upper = float(df['BB_Upper'].iloc[i]) if not np.isnan(df['BB_Upper'].iloc[i]) else float('inf')
            sma20 = float(df['SMA_20'].iloc[i]) if not np.isnan(df['SMA_20'].iloc[i]) else 0
            date_str = dates.iloc[i]
            
            if (rsi >= 70 or high_p >= bb_upper) and shares > 0:
                sell_shares = shares * 0.3
                cash += sell_shares * close_p
                shares -= sell_shares
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": sell_shares, "Reason": "과열 징후 (30% 익절)"})
            elif close_p <= sma20 and cash > 0:
                buy_shares = cash / close_p
                shares += buy_shares
                cash = 0.0
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": buy_shares, "Reason": "20일선 조정 (전액 재매수)"})
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "trades": trades, "desc": desc}

    def simulate_strategy_B():
        desc = "50% 주식, 50% 현금으로 여유있게 시작. 시장이 투매(RSI <= 30 또는 볼린저 하단 이탈)를 보일 때마다 보유 현금의 절반을 투입하여 분할 매수(바닥 줍기)합니다. 매도는 하지 않습니다."
        cash = initial_capital * 0.5
        shares = (initial_capital * 0.5) / float(df['Close'].iloc[0])
        trades = [{"Date": dates.iloc[0], "Action": "BUY", "Price": float(df['Close'].iloc[0]), "Shares": shares, "Reason": "초기 50% 매수"}]
        
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            low_p = float(df['Low'].iloc[i])
            rsi = float(df['RSI'].iloc[i]) if not np.isnan(df['RSI'].iloc[i]) else 50
            bb_lower = float(df['BB_Lower'].iloc[i]) if not np.isnan(df['BB_Lower'].iloc[i]) else 0
            date_str = dates.iloc[i]
            
            if (rsi <= 30 or low_p <= bb_lower) and cash > 10:
                buy_cash = cash * 0.5
                buy_shares = buy_cash / close_p
                shares += buy_shares
                cash -= buy_cash
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": buy_shares, "Reason": "투매 포착 (50% 분할매수)"})
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "trades": trades, "desc": desc}

    def simulate_hybrid():
        desc = "70% 주식, 30% 현금으로 시작. 전략 A(부분 익절)와 전략 B(바닥 분할매수)를 결합한 최고의 리스크 관리 전략입니다. 오를 때 30%씩 덜어내고, 폭락할 때 50%씩 줍습니다."
        cash = initial_capital * 0.3
        shares = (initial_capital * 0.7) / float(df['Close'].iloc[0])
        trades = [{"Date": dates.iloc[0], "Action": "BUY", "Price": float(df['Close'].iloc[0]), "Shares": shares, "Reason": "초기 70% 매수"}]
        
        for i in range(1, len(df)):
            close_p = float(df['Close'].iloc[i])
            high_p = float(df['High'].iloc[i])
            low_p = float(df['Low'].iloc[i])
            rsi = float(df['RSI'].iloc[i]) if not np.isnan(df['RSI'].iloc[i]) else 50
            bb_upper = float(df['BB_Upper'].iloc[i]) if not np.isnan(df['BB_Upper'].iloc[i]) else float('inf')
            bb_lower = float(df['BB_Lower'].iloc[i]) if not np.isnan(df['BB_Lower'].iloc[i]) else 0
            date_str = dates.iloc[i]
            
            if (rsi >= 70 or high_p >= bb_upper) and shares > 0:
                sell_shares = shares * 0.3
                cash += sell_shares * close_p
                shares -= sell_shares
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": sell_shares, "Reason": "과열 징후 (30% 익절)"})
            elif (rsi <= 30 or low_p <= bb_lower) and cash > 10:
                buy_cash = cash * 0.5
                buy_shares = buy_cash / close_p
                shares += buy_shares
                cash -= buy_cash
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": buy_shares, "Reason": "투매 포착 (50% 분할매수)"})
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "trades": trades, "desc": desc}

    return {
        "단순 보유 (Buy & Hold)": {"return": bh_return, "trades": bh_trades, "desc": "가장 기본이 되는 벤치마크. 첫날에 현금을 전액 주식에 몰빵한 뒤, 끝까지 가만히 들고 있었을 경우의 수익률입니다."},
        "이동평균선 (SMA)": simulate(sma_sig, "주가가 20일선 위로 올라타면 전액 매수, 20일선 밑으로 깨고 내려가면 전액 매도합니다. 대세 추세를 따라갈 때 유리합니다."),
        "MACD": simulate(macd_sig, "단기 추세선이 장기 추세선을 상향 돌파(골든크로스)하면 전액 매수, 하향 돌파(데드크로스)하면 전액 매도합니다."),
        "RSI": simulate(rsi_sig, "RSI가 30 이하(과매도)로 떨어지면 싼 값이라 판단해 전액 매수, 70 이상(과매수)으로 올라가면 비싸다 판단해 전액 매도합니다."),
        "볼린저 밴드 (BB)": simulate(bb_sig, "주가가 볼린저 밴드 하단에 닿거나 뚫고 내려가면 전액 매수, 밴드 상단에 닿거나 뚫고 올라가면 전액 매도합니다."),
        "💡 전략 A (부분 익절)": simulate_strategy_A(),
        "💡 전략 B (바닥 줍기)": simulate_strategy_B(),
        "💎 스마트 하이브리드": simulate_hybrid()
    }
