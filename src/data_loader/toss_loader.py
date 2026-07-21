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
    client_secret = os.getenv("TOSS_SECRET")
    
    if not client_id or not client_secret:
        return None
        
    url = "https://openapi.tossinvest.com/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        res = requests.post(url, data=data, timeout=3)
        if res.status_code == 200:
            return res.json().get("access_token")
        else:
            print(f"Failed to fetch Toss token: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print(f"Exception fetching Toss token: {e}")
        return None

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
    API 호출 실패 시 data/toss/ 폴더의 정적 파일을 확인하고, 없으면 kr_loader로 폴백합니다.
    """
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

    def fallback_to_static_or_kr():
        try:
            from data_loader.kr_loader import get_kr_stock_data
            df = get_kr_stock_data(ticker, start_date, end_date, cache_key=cache_key)
            if not df.empty:
                return df
        except Exception as e:
            print(f"kr_loader failed for {ticker}, trying static file: {e}")
            
        import json
        static_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'toss', f'{ticker}.csv')
        if os.path.exists(static_file):
            try:
                df = pd.read_csv(static_file)
                df['Date'] = pd.to_datetime(df['Date'])
                if start_date:
                    start = pd.to_datetime(start_date)
                    df = df[df['Date'] >= start]
                if end_date:
                    end = pd.to_datetime(end_date)
                    df = df[df['Date'] <= end]
                return df.reset_index(drop=True)
            except Exception as e:
                print(f"Failed to load static data for {ticker}: {e}")
        
        # If both fail, return empty dataframe to avoid crashing
        return pd.DataFrame()

    # Toss API candles have missing dates and incorrect adjustment factors.
    # Therefore, we bypass Toss candles and ALWAYS use kr_loader (yfinance/Naver) for reliable historical data (SMA, MACD).
    # This also fixes the change_percent calculation because kr_loader provides the correct previous close.
    return fallback_to_static_or_kr().reset_index(drop=True)

@st.cache_data(ttl=3600)
def get_toss_stock_info(ticker: str, cache_key: str = "") -> dict:
    """
    Toss API를 통해 실시간 현재가와 메타데이터를 가져옵니다.
    API 호출 실패 시 data/toss/ 폴더의 정적 파일을 확인하고, 없으면 kr_loader로 폴백합니다.
    """
    asset_name = KR_ASSETS.get(ticker, get_kr_stock_name(ticker))
    
    # 글로벌 인덱스(^)의 경우 야후파이낸스로 폴백
    if ticker.startswith("^"):
        from data_loader.kr_loader import get_kr_stock_info
        return get_kr_stock_info(ticker, cache_key=cache_key)
        
    def fallback_to_static_or_kr():
        try:
            from data_loader.kr_loader import get_kr_stock_info
            info = get_kr_stock_info(ticker, cache_key=cache_key)
            if info and info.get('current_price', 0.0) != 0.0:
                return info
        except Exception as e:
            print(f"kr_loader info failed for {ticker}, trying static file: {e}")
            
        import json
        static_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'toss', f'{ticker}_info.json')
        if os.path.exists(static_file):
            try:
                with open(static_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load static info for {ticker}: {e}")
        
        # Return basic info if all fail
        return {
            'ticker': ticker,
            'name': asset_name,
            'current_price': 0.0,
            'change_percent': 0.0,
            'last_updated': "N/A"
        }

    token = get_toss_token()
    if not token:
        print(f"Toss token not available, falling back to static/kr_loader for {ticker}")
        return fallback_to_static_or_kr()
        
    try:
        url = f"https://openapi.tossinvest.com/api/v1/prices?symbols={ticker}"
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            prices = data.get("result", [])
            if prices:
                item = prices[0]
                current_price = float(item.get("lastPrice", 0))
                last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Fetch historical data to calculate daily change
                df = get_toss_stock_data(ticker)
                daily_change = 0.0
                if not df.empty and len(df) > 1:
                    latest_date = df.iloc[-1]['Date'].date()
                    if latest_date == datetime.now().date():
                        prev = float(df.iloc[-2]['Close'])
                    else:
                        prev = float(df.iloc[-1]['Close'])
                    daily_change = ((current_price - prev) / prev) * 100
                    
                return {
                    'ticker': ticker,
                    'name': asset_name,
                    'current_price': current_price,
                    'change_percent': daily_change,
                    'last_updated': last_updated
                }
            else:
                return fallback_to_static_or_kr()
        else:
            print(f"Toss API returned {res.status_code} for prices. Falling back to static/kr_loader.")
            return fallback_to_static_or_kr()
                    
    except Exception as e:
        print(f"Failed to fetch Toss info for {ticker}: {e}. Falling back to static/kr_loader.")
        return fallback_to_static_or_kr()
