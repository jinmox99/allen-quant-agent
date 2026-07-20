import os
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Re-use the existing KR mappings
from data_loader.kr_loader import KR_ASSETS, get_kr_stock_name

load_dotenv()

@st.cache_data(ttl=82800) # Cache for 23 hours (Token expires in 24 hours)
def get_toss_token() -> str:
    """
    Toss Invest API OAuth 2.0 액세스 토큰을 발급받습니다.
    """
    client_id = os.getenv("TOSS_ID")
    client_secret = os.getenv("TOS__SECRET") # Note the typo in .env variable name
    
    if not client_id or not client_secret:
        raise ValueError("TOSS_ID or TOS__SECRET environment variables are missing.")
        
    url = "https://openapi.tossinvest.com/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    res = requests.post(url, data=data)
    if res.status_code == 200:
        return res.json().get("access_token")
    else:
        raise Exception(f"Failed to fetch Toss token: {res.status_code} - {res.text}")

def get_toss_cache_key():
    """
    캐시 키 생성 (1시간 단위 갱신)
    """
    now = datetime.now()
    return now.strftime('toss_%Y-%m-%d_%H')

@st.cache_data(ttl=3600)
def get_toss_stock_data(ticker: str, start_date: str = "", end_date: str = "", cache_key: str = "") -> pd.DataFrame:
    """
    Toss API를 통해 과거 일봉(Candle) 데이터를 가져옵니다.
    """
    token = get_toss_token()
    
    # 글로벌 인덱스(^)는 야후 파이낸스 폴백 사용
    if ticker.startswith("^"):
        import yfinance as yf
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        df.rename(columns={'index': 'Date'}, inplace=True)
        if 'Close' in df.columns:
            df = df.dropna(subset=['Close'])
        return df

    # Toss API 호환 심볼로 변환 (기본 6자리 유지)
    symbol = ticker
    
    url = f"https://openapi.tossinvest.com/api/v1/candles?symbol={symbol}&interval=1d&count=200"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to fetch Toss candles for {symbol}: {res.status_code} - {res.text}")
        return pd.DataFrame()
        
    data = res.json()
    candles = data.get("result", {}).get("candles", [])
    
    if not candles:
        return pd.DataFrame()
        
    df = pd.DataFrame(candles)
    
    # Toss API returns: timestamp, openPrice, highPrice, lowPrice, closePrice, volume
    # Convert format to match standard format
    df['Date'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None) # Remove timezone for standard plotting
    df['Open'] = pd.to_numeric(df['openPrice'])
    df['High'] = pd.to_numeric(df['highPrice'])
    df['Low'] = pd.to_numeric(df['lowPrice'])
    df['Close'] = pd.to_numeric(df['closePrice'])
    df['Volume'] = pd.to_numeric(df['volume'])
    
    # Toss returns newest first (descending). We need chronological order (ascending)
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Select only required columns
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    # Filter by start_date and end_date if provided
    if start_date:
        start = pd.to_datetime(start_date)
        df = df[df['Date'] >= start]
    if end_date:
        end = pd.to_datetime(end_date)
        df = df[df['Date'] <= end]
        
    return df.reset_index(drop=True)

@st.cache_data(ttl=3600)
def get_toss_stock_info(ticker: str, cache_key: str = "") -> dict:
    """
    Toss API를 통해 실시간 현재가와 메타데이터를 가져옵니다.
    """
    asset_name = KR_ASSETS.get(ticker, get_kr_stock_name(ticker))
    
    current_price = 0.0
    daily_change = 0.0
    last_updated = "N/A"
    
    # 글로벌 인덱스(^)의 경우 야후파이낸스로 폴백
    if ticker.startswith("^"):
        from data_loader.kr_loader import get_kr_stock_info
        # Use existing kr_loader for global indices
        return get_kr_stock_info(ticker, cache_key=cache_key)
        
    try:
        token = get_toss_token()
        url = f"https://openapi.tossinvest.com/api/v1/prices?symbols={ticker}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            prices = data.get("result", [])
            if prices:
                item = prices[0]
                current_price = float(item.get("lastPrice", 0))
                last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Fetch historical data to calculate daily change
                df = get_toss_stock_data(ticker)
                if len(df) > 1:
                    # Find previous day's close
                    # If today's data is already the last row, prev is the second to last
                    # Since we don't know if current_price is already in df, we just take the last closed day
                    # Toss candles returns today as the last row if market is open/closed today
                    latest_date = df.iloc[-1]['Date'].date()
                    if latest_date == datetime.now().date():
                        prev = float(df.iloc[-2]['Close'])
                    else:
                        prev = float(df.iloc[-1]['Close'])
                    daily_change = ((current_price - prev) / prev) * 100
                    
    except Exception as e:
        print(f"Failed to fetch Toss info for {ticker}: {e}")
        
    # If Toss fails, fallback to Toss Historical (just in case) or kr_loader logic
    if current_price == 0.0:
        df = get_toss_stock_data(ticker)
        if not df.empty:
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            if len(df) > 1:
                prev = float(df.iloc[-2]['Close'])
                daily_change = ((current_price - prev) / prev) * 100
            last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return {
        'ticker': ticker,
        'name': asset_name,
        'current_price': current_price,
        'change_percent': daily_change,
        'last_updated': last_updated
    }
