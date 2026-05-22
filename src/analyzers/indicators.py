import pandas as pd
import numpy as np

def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = 'Close') -> pd.Series:
    """Calculates Simple Moving Average (SMA)."""
    return df[column].rolling(window=period).mean()

def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = 'Close') -> pd.Series:
    """Calculates Exponential Moving Average (EMA)."""
    return df[column].ewm(span=period, adjust=False).mean()

def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'Close') -> pd.Series:
    """Calculates Relative Strength Index (RSI)."""
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()
    
    # Exponential moving average for gain and loss
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, 0.00001) # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, column: str = 'Close') -> pd.DataFrame:
    """Calculates Moving Average Convergence Divergence (MACD)."""
    macd_df = pd.DataFrame(index=df.index)
    ema_fast = calculate_ema(df, fast, column)
    ema_slow = calculate_ema(df, slow, column)
    
    macd_df['MACD'] = ema_fast - ema_slow
    macd_df['MACD_Signal'] = macd_df['MACD'].ewm(span=signal, adjust=False).mean()
    macd_df['MACD_Hist'] = macd_df['MACD'] - macd_df['MACD_Signal']
    return macd_df

def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2, column: str = 'Close') -> pd.DataFrame:
    """Calculates Bollinger Bands (Middle, Upper, Lower)."""
    bb_df = pd.DataFrame(index=df.index)
    bb_df['BB_Mid'] = calculate_sma(df, period, column)
    rolling_std = df[column].rolling(window=period).std()
    
    bb_df['BB_Upper'] = bb_df['BB_Mid'] + (rolling_std * std_dev)
    bb_df['BB_Lower'] = bb_df['BB_Mid'] - (rolling_std * std_dev)
    return bb_df

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
    df_out['EMA_10'] = calculate_ema(df_out, 10, 'Close')
    df_out['EMA_20'] = calculate_ema(df_out, 20, 'Close')
    df_out['EMA_50'] = calculate_ema(df_out, 50, 'Close')
    
    # RSI
    df_out['RSI'] = calculate_rsi(df_out, 14, 'Close')
    
    # MACD
    macd = calculate_macd(df_out, 12, 26, 9, 'Close')
    df_out['MACD'] = macd['MACD']
    df_out['MACD_Signal'] = macd['MACD_Signal']
    df_out['MACD_Hist'] = macd['MACD_Hist']
    
    # Bollinger Bands
    bb = calculate_bollinger_bands(df_out, 20, 2, 'Close')
    df_out['BB_Mid'] = bb['BB_Mid']
    df_out['BB_Upper'] = bb['BB_Upper']
    df_out['BB_Lower'] = bb['BB_Lower']
    
    # Daily returns
    df_out['Daily_Return'] = df_out['Close'].pct_change()
    
    return df_out
