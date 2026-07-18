import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# Target Asset Mapping
KR_ASSETS = {
    '441800': 'TIMEFOLIO Korea플러스배당액티브',
    '315930': 'KODEX Top5PlusTR',
    '520054': '미래에셋 레버리지 코스피200선물 ETN',
    '520098': '미래에셋 레버리지 반도체 ETN'
}

def get_kr_assets():
    """Returns the dictionary of predefined Korean assets."""
    return KR_ASSETS

# Global cache for KRX stock listing to avoid fetching multiple times
_KRX_LISTING_CACHE = None

def get_kr_stock_name(ticker: str) -> str:
    """Returns stock name via Yahoo Search API to avoid KRX IP block and .info hangs."""
    import requests
    try:
        # Try KOSPI search
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}.KS"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=2)
        if res.status_code == 200:
            data = res.json()
            if 'quotes' in data and len(data['quotes']) > 0:
                return data['quotes'][0].get('shortname') or data['quotes'][0].get('longname') or ticker
                
        # Try KOSDAQ search
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}.KQ"
        res = requests.get(url, headers=headers, timeout=2)
        if res.status_code == 200:
            data = res.json()
            if 'quotes' in data and len(data['quotes']) > 0:
                return data['quotes'][0].get('shortname') or data['quotes'][0].get('longname') or ticker
    except Exception:
        pass
        
    return ticker

import streamlit as st

@st.cache_data(ttl=300)
def get_kr_stock_data(ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Fetches historical OHLCV data for a Korean ETF/ETN/Stock ticker using yfinance.
    (Bypasses Naver Finance / KRX IP blocking on cloud servers)
    """
    import yfinance as yf
    
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    try:
        # If the ticker is already a global index (like ^KS200, ^KS11), download directly
        if ticker.startswith("^"):
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        else:
            # Try KOSPI first
            df = yf.download(f"{ticker}.KS", start=start_date, end=end_date, progress=False)
            # If empty, try KOSDAQ
            if df.empty:
                df = yf.download(f"{ticker}.KQ", start=start_date, end=end_date, progress=False)
            
        if df.empty:
            raise ValueError(f"No data returned for KR ticker: {ticker}")
            
        # Flatten MultiIndex columns if present (e.g. from newer yfinance versions)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # Reset index to make Date a column
        df = df.reset_index()
        # Rename standard Date column from yfinance
        df.rename(columns={'index': 'Date'}, inplace=True)
        # Drop rows with NaN Close values
        if 'Close' in df.columns:
            df = df.dropna(subset=['Close'])
        return df
    except Exception as e:
        print(f"Error fetching data for KR ticker {ticker}: {str(e)}")
        # Return an empty DataFrame with standard columns as fallback
        return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change'])

@st.cache_data(ttl=300)
def get_kr_stock_info(ticker: str) -> dict:
    """
    Returns metadata and current price information for a Korean asset.
    """
    asset_name = KR_ASSETS.get(ticker, get_kr_stock_name(ticker))
    
    # Fetch recent price to extract current close and change
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    
    df = get_kr_stock_data(ticker, start_date, end_date)
    
    current_price = 0.0
    daily_change = 0.0
    last_updated = "N/A"
    
    if not df.empty:
        latest = df.iloc[-1]
        current_price = float(latest['Close'])
        # Handle different column names for change
        if 'Change' in latest:
            daily_change = float(latest['Change']) * 100 # Change is usually represented as a decimal fraction
        elif len(df) > 1:
            prev_close = float(df.iloc[-2]['Close'])
            daily_change = ((current_price - prev_close) / prev_close) * 100
        
        if 'Date' in latest:
            last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
    return {
        'ticker': ticker,
        'name': asset_name,
        'current_price': current_price,
        'change_percent': daily_change,
        'last_updated': last_updated
    }

if __name__ == '__main__':
    print("=== [KR] Korean Assets List ===")
    assets = get_kr_assets()
    for ticker, name in assets.items():
        print(f"[{ticker}] {name}")
        
    test_ticker = '441800'
    print(f"\n=== Fetching Stock Info for '{test_ticker}' ===")
    info = get_kr_stock_info(test_ticker)
    for k, v in info.items():
        print(f"  {k}: {v}")
    
    print(f"\n=== Fetching Recent Data for '{test_ticker}' ===")
    # Fetch last 10 days
    start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    df = get_kr_stock_data(test_ticker, start_date=start)
    if not df.empty:
        print(df.tail(3))
    else:
        print("No data retrieved.")

