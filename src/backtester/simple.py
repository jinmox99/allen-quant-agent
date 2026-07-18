import pandas as pd
import numpy as np

def run_indicator_backtests(df: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
    """
    Runs simple backtests on 4 technical indicators plus Buy & Hold over the given DataFrame.
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

    return {
        "단순 보유 (Buy & Hold)": bh_return,
        "이동평균선 (SMA)": simulate(sma_sig),
        "MACD": simulate(macd_sig),
        "RSI": simulate(rsi_sig),
        "볼린저 밴드 (BB)": simulate(bb_sig)
    }
