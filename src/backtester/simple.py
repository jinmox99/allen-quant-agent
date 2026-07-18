import pandas as pd
import numpy as np

def run_indicator_backtests(df: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
    """
    Runs- `[x]` Update `src/backtester/simple.py` with Strategy A, B, and Hybrid
- `[/]` Update `main.py` UI to highlight smart strategies in chartaFrame.
    Returns a dictionary mapping strategy names to their percentage returns.
    """
    if df.empty or len(df) < 20:
        return {}

    # Buy & Hold Return
    start_price = float(df['Close'].iloc[0])
    end_price = float(df['Close'].iloc[-1])
    bh_return = ((end_price - start_price) / start_price) * 100

    def simulate(signals: pd.Series) -> float:
        cash = initial_capital
        shares = 0.0
        
        for i in range(len(df)):
            sig = signals.iloc[i]
            price = float(df['Close'].iloc[i])
            
            # Buy signal and we have cash
            if sig == 1 and cash > 0:
                shares = cash / price
                cash = 0.0
            # Sell signal and we have shares
            elif sig == -1 and shares > 0:
                cash = shares * price
                shares = 0.0
                
        final_value = cash + (shares * end_price)
        return ((final_value - initial_capital) / initial_capital) * 100

    # 1. SMA Signals (Buy when Close > SMA20, Sell when Close < SMA20)
    sma_sig = pd.Series(0, index=df.index)
    sma_sig[df['Close'] > df['SMA_20']] = 1
    sma_sig[df['Close'] < df['SMA_20']] = -1
    
    # 2. MACD Signals (Buy when MACD > Signal, Sell when MACD < Signal)
    macd_sig = pd.Series(0, index=df.index)
    macd_sig[df['MACD'] > df['MACD_Signal']] = 1
    macd_sig[df['MACD'] < df['MACD_Signal']] = -1
    
    # 3. RSI Signals (Buy <= 30, Sell >= 70)
    rsi_sig = pd.Series(0, index=df.index)
    rsi_sig[df['RSI'] <= 30] = 1
    rsi_sig[df['RSI'] >= 70] = -1
    
    # 4. BB Signals (Buy Low <= BB_Lower, Sell High >= BB_Upper)
    bb_sig = pd.Series(0, index=df.index)
    bb_sig[(df['Low'] <= df['BB_Lower']) | (df['Close'] <= df['BB_Lower']*1.01)] = 1
    bb_sig[(df['High'] >= df['BB_Upper']) | (df['Close'] >= df['BB_Upper']*0.99)] = -1

    # ==========================================
    # Smart Strategies (A, B, Hybrid)
    # ==========================================
    
    def simulate_strategy_A():
        """전략 A (부분 익절): 100% 주식 시작. 과열 시 30% 매도, 20일선 터치 시 전액 재매수"""
        cash = 0.0
        shares = initial_capital / float(df['Close'].iloc[0])
        for i in range(len(df)):
            close_p = float(df['Close'].iloc[i])
            high_p = float(df['High'].iloc[i])
            rsi = float(df['RSI'].iloc[i]) if not np.isnan(df['RSI'].iloc[i]) else 50
            bb_upper = float(df['BB_Upper'].iloc[i]) if not np.isnan(df['BB_Upper'].iloc[i]) else float('inf')
            sma20 = float(df['SMA_20'].iloc[i]) if not np.isnan(df['SMA_20'].iloc[i]) else 0
            
            # 매도 조건 (과열): RSI >= 70 or 고가 >= 밴드 상단
            if (rsi >= 70 or high_p >= bb_upper) and shares > 0:
                sell_shares = shares * 0.3 # 30% 매도
                cash += sell_shares * close_p
                shares -= sell_shares
            # 매수 조건 (조정): 종가 <= 20일선
            elif close_p <= sma20 and cash > 0:
                shares += cash / close_p
                cash = 0.0
                
        final_value = cash + (shares * end_price)
        return ((final_value - initial_capital) / initial_capital) * 100

    def simulate_strategy_B():
        """전략 B (바닥 줍기): 50% 주식/50% 현금 시작. 투매 시 현금의 50%씩 분할 매수. 매도 없음."""
        cash = initial_capital * 0.5
        shares = (initial_capital * 0.5) / float(df['Close'].iloc[0])
        for i in range(len(df)):
            close_p = float(df['Close'].iloc[i])
            low_p = float(df['Low'].iloc[i])
            rsi = float(df['RSI'].iloc[i]) if not np.isnan(df['RSI'].iloc[i]) else 50
            bb_lower = float(df['BB_Lower'].iloc[i]) if not np.isnan(df['BB_Lower'].iloc[i]) else 0
            
            # 매수 조건 (투매): RSI <= 30 or 저가 <= 밴드 하단
            if (rsi <= 30 or low_p <= bb_lower) and cash > 10:
                buy_cash = cash * 0.5 # 남은 현금의 50% 사용
                shares += buy_cash / close_p
                cash -= buy_cash
                
        final_value = cash + (shares * end_price)
        return ((final_value - initial_capital) / initial_capital) * 100

    def simulate_hybrid():
        """스마트 하이브리드 (A+B): 70% 주식/30% 현금 시작. 과열 시 30% 매도, 투매 시 현금 50% 매수."""
        cash = initial_capital * 0.3
        shares = (initial_capital * 0.7) / float(df['Close'].iloc[0])
        for i in range(len(df)):
            close_p = float(df['Close'].iloc[i])
            high_p = float(df['High'].iloc[i])
            low_p = float(df['Low'].iloc[i])
            rsi = float(df['RSI'].iloc[i]) if not np.isnan(df['RSI'].iloc[i]) else 50
            bb_upper = float(df['BB_Upper'].iloc[i]) if not np.isnan(df['BB_Upper'].iloc[i]) else float('inf')
            bb_lower = float(df['BB_Lower'].iloc[i]) if not np.isnan(df['BB_Lower'].iloc[i]) else 0
            
            # 매도 (A)
            if (rsi >= 70 or high_p >= bb_upper) and shares > 0:
                sell_shares = shares * 0.3
                cash += sell_shares * close_p
                shares -= sell_shares
            # 매수 (B)
            elif (rsi <= 30 or low_p <= bb_lower) and cash > 10:
                buy_cash = cash * 0.5
                shares += buy_cash / close_p
                cash -= buy_cash
                
        final_value = cash + (shares * end_price)
        return ((final_value - initial_capital) / initial_capital) * 100

    return {
        "단순 보유 (Buy & Hold)": bh_return,
        "이동평균선 (SMA)": simulate(sma_sig),
        "MACD": simulate(macd_sig),
        "RSI": simulate(rsi_sig),
        "볼린저 밴드 (BB)": simulate(bb_sig),
        "💡 전략 A (부분 익절)": simulate_strategy_A(),
        "💡 전략 B (바닥 줍기)": simulate_strategy_B(),
        "💎 스마트 하이브리드": simulate_hybrid()
    }
