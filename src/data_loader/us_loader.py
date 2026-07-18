import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# US Target Asset Mapping
US_ASSETS = {
    'SOXL': 'Direxion Daily Semiconductor Bull 3X Shares',
    'TECL': 'Direxion Daily Technology Bull 3X Shares',
    'TQQQ': 'ProShares UltraPro QQQ (3x Nasdaq-100)',
    'UPRO': 'ProShares UltraPro S&P500 (3x S&P 500)'
}

def get_us_assets():
    """Returns the dictionary of predefined US assets."""
    return US_ASSETS

def get_us_stock_data(ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Fetches historical OHLCV data for a US leveraged ETF ticker using yfinance.
    
    Parameters:
    - ticker: str (e.g. 'TQQQ')
    - start_date: str (YYYY-MM-DD)
    - end_date: str (YYYY-MM-DD)
    
    Returns:
    - pd.DataFrame containing Date, Open, High, Low, Close, Volume, Adj Close
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    try:
        # yfinance can fetch directly
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty:
            raise ValueError(f"No data returned for US ticker: {ticker}")
        
        # Flatten MultiIndex columns if present (e.g. from newer yfinance versions)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # Reset index to make Date a column
        df = df.reset_index()
        # Drop rows with NaN Close values
        if 'Close' in df.columns:
            df = df.dropna(subset=['Close'])
        return df
    except Exception as e:
        print(f"Error fetching US data for ticker {ticker}: {str(e)}")
        return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])

def get_us_stock_info(ticker: str) -> dict:
    """
    Returns metadata and current price information for a US asset.
    """
    try:
        # Use Yahoo Search API to get name safely without .info hanging
        import requests
        asset_name = ticker
        if ticker in US_ASSETS:
            asset_name = US_ASSETS[ticker]
        else:
            try:
                url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}"
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url, headers=headers, timeout=2)
                if res.status_code == 200:
                    data = res.json()
                    if 'quotes' in data and len(data['quotes']) > 0:
                        for q in data['quotes']:
                            if q.get('symbol', '').upper() == ticker.upper():
                                asset_name = q.get('shortname') or q.get('longname') or ticker
                                break
            except Exception:
                pass
        
        # Fallback to fetching recent data directly to avoid .info hangs
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        df = get_us_stock_data(ticker, start_date, end_date)
        
        if not df.empty:
            current_price = float(df.iloc[-1]['Close'])
            prev_close = float(df.iloc[-2]['Close']) if len(df) > 1 else current_price
            change_percent = ((current_price - prev_close) / prev_close) * 100
        else:
            current_price = 0.0
            change_percent = 0.0
            
        return {
            'ticker': ticker,
            'name': asset_name,
            'current_price': current_price,
            'change_percent': change_percent,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Error fetching US info for ticker {ticker}: {str(e)}")
        return {
            'ticker': ticker,
            'name': ticker,
            'current_price': 0.0,
            'change_percent': 0.0,
            'last_updated': "N/A"
        }

def get_us_stock_news(ticker: str) -> list:
    """
    Fetches recent news articles for the ticker from yfinance.
    
    Returns:
    - list of dicts: [{'title': ..., 'publisher': ..., 'link': ..., 'time': datetime, 'summary': ...}]
    """
    try:
        yt = yf.Ticker(ticker)
        news_raw = yt.news
        if not news_raw:
            return []
            
        articles = []
        for item in news_raw[:8]:  # Limit to 8 recent articles
            pub_time_raw = item.get('providerPublishTime', 0)
            pub_time = datetime.fromtimestamp(pub_time_raw) if pub_time_raw else datetime.now()
            
            articles.append({
                'title': item.get('title', 'No Title'),
                'publisher': item.get('publisher', 'Unknown Publisher'),
                'link': item.get('link', ''),
                'time': pub_time.strftime('%Y-%m-%d %H:%M'),
                'summary': item.get('summary', 'Click link to read more.')
            })
        return articles
    except Exception as e:
        print(f"Error fetching news for US ticker {ticker}: {str(e)}")
        return []
