import pandas as pd
import numpy as np

def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = 'Close') -> pd.Series:
    """Calculates Simple Moving Average (SMA)."""
    return df[column].rolling(window=period).mean()

def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = 'Close') -> pd.Series:
    """Calculates Exponential Moving Average (EMA)."""
    return df[column].ewm(span=period, adjust=False).mean()



def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, column: str = 'Close') -> pd.DataFrame:
    """Calculates Moving Average Convergence Divergence (MACD)."""
    macd_df = pd.DataFrame(index=df.index)
    ema_fast = calculate_ema(df, fast, column)
    ema_slow = calculate_ema(df, slow, column)
    
    macd_df['MACD'] = ema_fast - ema_slow
    macd_df['MACD_Signal'] = macd_df['MACD'].ewm(span=signal, adjust=False).mean()
    macd_df['MACD_Hist'] = macd_df['MACD'] - macd_df['MACD_Signal']
    return macd_df



def add_all_indicators(df: pd.DataFrame, column: str = 'Close') -> pd.DataFrame:
    """
    Appends a full suite of technical indicators to the DataFrame.
    """
    # Create a copy to prevent SettingWithCopyWarning
    df_out = df.copy()
    
    # Ensure standard types
    df_out['Close'] = df_out[column].astype(float)
    
    # Simple Moving Averages
    df_out['SMA_10'] = calculate_sma(df_out, 10, 'Close')
    df_out['SMA_20'] = calculate_sma(df_out, 20, 'Close')
    df_out['SMA_25'] = calculate_sma(df_out, 25, 'Close')
    df_out['SMA_45'] = calculate_sma(df_out, 45, 'Close')
    df_out['SMA_50'] = calculate_sma(df_out, 50, 'Close')
    df_out['SMA_120'] = calculate_sma(df_out, 120, 'Close')
    
    # Exponential Moving Averages
    df_out['EMA_5'] = calculate_ema(df_out, 5, 'Close')
    df_out['EMA_10'] = calculate_ema(df_out, 10, 'Close')
    df_out['EMA_20'] = calculate_ema(df_out, 20, 'Close')
    df_out['EMA_50'] = calculate_ema(df_out, 50, 'Close')
    

    
    # MACD
    macd = calculate_macd(df_out, 12, 26, 9, 'Close')
    df_out['MACD'] = macd['MACD']
    df_out['MACD_Signal'] = macd['MACD_Signal']
    df_out['MACD_Hist'] = macd['MACD_Hist']
    

    
    # Historical Prices (Dual Momentum)
    # Approx: 1M=21 days, 3M=63 days, 6M=126 days
    df_out['Close_1M_ago'] = df_out['Close'].shift(21)
    df_out['Close_3M_ago'] = df_out['Close'].shift(63)
    df_out['Close_6M_ago'] = df_out['Close'].shift(126)
        
    # Daily returns
    df_out['Daily_Return'] = df_out['Close'].pct_change()
    
    # ==========================================
    # New Indicators for additional strategies
    # ==========================================
    
    # ADX (Average Directional Index)
    if 'High' in df_out.columns and 'Low' in df_out.columns:
        high = df_out['High'].astype(float)
        low = df_out['Low'].astype(float)
        close = df_out['Close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        # When +DM > -DM, -DM = 0 and vice versa
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr_14 = tr.ewm(alpha=1/14, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_14)
        minus_di = 100 * (minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_14)
        
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 0.0001)
        adx = dx.ewm(alpha=1/14, adjust=False).mean()
        
        df_out['Plus_DI'] = plus_di
        df_out['Minus_DI'] = minus_di
        df_out['ADX'] = adx
    
    # Stochastic Oscillator (%K, %D)
    if 'High' in df_out.columns and 'Low' in df_out.columns:
        low_14 = df_out['Low'].astype(float).rolling(window=14).min()
        high_14 = df_out['High'].astype(float).rolling(window=14).max()
        df_out['Stoch_K'] = 100 * (df_out['Close'] - low_14) / (high_14 - low_14).replace(0, 0.0001)
        df_out['Stoch_D'] = df_out['Stoch_K'].rolling(window=3).mean()
    
    # Ichimoku Cloud (이치모쿠 구름)
    if 'High' in df_out.columns and 'Low' in df_out.columns:
        high_9 = df_out['High'].astype(float).rolling(window=9).max()
        low_9 = df_out['Low'].astype(float).rolling(window=9).min()
        high_26 = df_out['High'].astype(float).rolling(window=26).max()
        low_26 = df_out['Low'].astype(float).rolling(window=26).min()
        high_52 = df_out['High'].astype(float).rolling(window=52).max()
        low_52 = df_out['Low'].astype(float).rolling(window=52).min()
        
        tenkan = (high_9 + low_9) / 2  # Conversion Line (전환선)
        kijun = (high_26 + low_26) / 2  # Base Line (기준선)
        
        df_out['Ichimoku_SpanA'] = ((tenkan + kijun) / 2).shift(26)  # Leading Span A
        df_out['Ichimoku_SpanB'] = ((high_52 + low_52) / 2).shift(26)  # Leading Span B
    
    # OBV (On-Balance Volume)
    if 'Volume' in df_out.columns:
        volume = df_out['Volume'].astype(float)
        close_diff = df_out['Close'].diff()
        obv = pd.Series(0.0, index=df_out.index)
        obv = volume.where(close_diff > 0, -volume).where(close_diff != 0, 0).cumsum()
        df_out['OBV'] = obv
        df_out['OBV_MA'] = obv.rolling(window=20).mean()
    
    # Parabolic SAR
    if 'High' in df_out.columns and 'Low' in df_out.columns:
        high_arr = df_out['High'].astype(float).values
        low_arr = df_out['Low'].astype(float).values
        close_arr = df_out['Close'].values
        n = len(df_out)
        psar = np.zeros(n)
        af = 0.02
        af_step = 0.02
        af_max = 0.2
        bull = True
        ep = low_arr[0]
        psar[0] = high_arr[0]
        
        for i in range(1, n):
            if bull:
                psar[i] = psar[i-1] + af * (ep - psar[i-1])
                psar[i] = min(psar[i], low_arr[i-1])
                if i >= 2:
                    psar[i] = min(psar[i], low_arr[i-2])
                if low_arr[i] < psar[i]:
                    bull = False
                    psar[i] = ep
                    ep = low_arr[i]
                    af = af_step
                else:
                    if high_arr[i] > ep:
                        ep = high_arr[i]
                        af = min(af + af_step, af_max)
            else:
                psar[i] = psar[i-1] + af * (ep - psar[i-1])
                psar[i] = max(psar[i], high_arr[i-1])
                if i >= 2:
                    psar[i] = max(psar[i], high_arr[i-2])
                if high_arr[i] > psar[i]:
                    bull = True
                    psar[i] = ep
                    ep = high_arr[i]
                    af = af_step
                else:
                    if low_arr[i] < ep:
                        ep = low_arr[i]
                        af = min(af + af_step, af_max)
        df_out['PSAR'] = psar
    
    # VWAP (Volume Weighted Average Price) - rolling 20-day
    if 'Volume' in df_out.columns and 'High' in df_out.columns and 'Low' in df_out.columns:
        typical_price = (df_out['High'].astype(float) + df_out['Low'].astype(float) + df_out['Close']) / 3
        vol = df_out['Volume'].astype(float)
        df_out['VWAP'] = (typical_price * vol).rolling(window=20).sum() / vol.rolling(window=20).sum()
    
    return df_out
