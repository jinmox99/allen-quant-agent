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

def get_us_top_50():
    """Returns a hardcoded list of top 50 NASDAQ stocks by market cap for performance."""
    nasdaq_top_50 = [
        {"ticker": "AAPL", "name": "Apple Inc."},
        {"ticker": "MSFT", "name": "Microsoft Corp."},
        {"ticker": "NVDA", "name": "NVIDIA Corp."},
        {"ticker": "GOOGL", "name": "Alphabet Inc."},
        {"ticker": "AMZN", "name": "Amazon.com Inc."},
        {"ticker": "META", "name": "Meta Platforms Inc."},
        {"ticker": "AVGO", "name": "Broadcom Inc."},
        {"ticker": "TSLA", "name": "Tesla Inc."},
        {"ticker": "COST", "name": "Costco Wholesale Corp."},
        {"ticker": "ASML", "name": "ASML Holding NV"},
        {"ticker": "NFLX", "name": "Netflix Inc."},
        {"ticker": "AMD", "name": "Advanced Micro Devices"},
        {"ticker": "TMUS", "name": "T-Mobile US Inc."},
        {"ticker": "PEP", "name": "PepsiCo Inc."},
        {"ticker": "LIN", "name": "Linde plc"},
        {"ticker": "CSCO", "name": "Cisco Systems Inc."},
        {"ticker": "INTU", "name": "Intuit Inc."},
        {"ticker": "QCOM", "name": "QUALCOMM Inc."},
        {"ticker": "AMAT", "name": "Applied Materials Inc."},
        {"ticker": "TXN", "name": "Texas Instruments Inc."},
        {"ticker": "INTC", "name": "Intel Corp."},
        {"ticker": "AMGN", "name": "Amgen Inc."},
        {"ticker": "CMCSA", "name": "Comcast Corp."},
        {"ticker": "ISRG", "name": "Intuitive Surgical Inc."},
        {"ticker": "HON", "name": "Honeywell International Inc."},
        {"ticker": "SBUX", "name": "Starbucks Corp."},
        {"ticker": "GILD", "name": "Gilead Sciences Inc."},
        {"ticker": "MDLZ", "name": "Mondelez International Inc."},
        {"ticker": "VRTX", "name": "Vertex Pharmaceuticals Inc."},
        {"ticker": "REGN", "name": "Regeneron Pharmaceuticals Inc."},
        {"ticker": "BKNG", "name": "Booking Holdings Inc."},
        {"ticker": "ADI", "name": "Analog Devices Inc."},
        {"ticker": "ADP", "name": "Automatic Data Processing Inc."},
        {"ticker": "MU", "name": "Micron Technology Inc."},
        {"ticker": "PANW", "name": "Palo Alto Networks Inc."},
        {"ticker": "MELI", "name": "MercadoLibre Inc."},
        {"ticker": "KLAC", "name": "KLA Corp."},
        {"ticker": "LRCX", "name": "Lam Research Corp."},
        {"ticker": "SNPS", "name": "Synopsys Inc."},
        {"ticker": "CDNS", "name": "Cadence Design Systems Inc."},
        {"ticker": "CSX", "name": "CSX Corp."},
        {"ticker": "PYPL", "name": "PayPal Holdings Inc."},
        {"ticker": "MAR", "name": "Marriott International Inc."},
        {"ticker": "CRWD", "name": "CrowdStrike Holdings Inc."},
        {"ticker": "ORLY", "name": "O'Reilly Automotive Inc."},
        {"ticker": "CTAS", "name": "Cintas Corp."},
        {"ticker": "NXPI", "name": "NXP Semiconductors NV"},
        {"ticker": "FTNT", "name": "Fortinet Inc."},
        {"ticker": "MNST", "name": "Monster Beverage Corp."},
        {"ticker": "PCAR", "name": "PACCAR Inc."}
    ]
    return nasdaq_top_50

def get_us_etf_top_50():
    """Returns a hardcoded list of top 50 US ETFs/ETNs by popularity/volume for performance."""
    # Since FDR's ETF/US fetching is extremely slow, we provide a hardcoded list of major US ETFs/ETNs
    us_etf_top_50 = [
        {"ticker": "SPY", "name": "SPDR S&P 500 ETF Trust"},
        {"ticker": "QQQ", "name": "Invesco QQQ Trust"},
        {"ticker": "VOO", "name": "Vanguard S&P 500 ETF"},
        {"ticker": "IVV", "name": "iShares Core S&P 500 ETF"},
        {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF"},
        {"ticker": "SOXX", "name": "iShares Semiconductor ETF"},
        {"ticker": "SMH", "name": "VanEck Semiconductor ETF"},
        {"ticker": "TQQQ", "name": "ProShares UltraPro QQQ"},
        {"ticker": "SOXL", "name": "Direxion Daily Semiconductor Bull 3X"},
        {"ticker": "ARKK", "name": "ARK Innovation ETF"},
        {"ticker": "GLD", "name": "SPDR Gold Shares"},
        {"ticker": "TLT", "name": "iShares 20+ Year Treasury Bond ETF"},
        {"ticker": "IWM", "name": "iShares Russell 2000 ETF"},
        {"ticker": "VUG", "name": "Vanguard Growth ETF"},
        {"ticker": "VTV", "name": "Vanguard Value ETF"},
        {"ticker": "VEA", "name": "Vanguard FTSE Developed Markets ETF"},
        {"ticker": "IEFA", "name": "iShares Core MSCI EAFE ETF"},
        {"ticker": "BND", "name": "Vanguard Total Bond Market ETF"},
        {"ticker": "AGG", "name": "iShares Core US Aggregate Bond ETF"},
        {"ticker": "XLK", "name": "Technology Select Sector SPDR Fund"},
        {"ticker": "XLF", "name": "Financial Select Sector SPDR Fund"},
        {"ticker": "XLE", "name": "Energy Select Sector SPDR Fund"},
        {"ticker": "XLV", "name": "Health Care Select Sector SPDR Fund"},
        {"ticker": "VIG", "name": "Vanguard Dividend Appreciation ETF"},
        {"ticker": "VYM", "name": "Vanguard High Dividend Yield ETF"},
        {"ticker": "SCHD", "name": "Schwab US Dividend Equity ETF"},
        {"ticker": "DIA", "name": "SPDR Dow Jones Industrial Average ETF"},
        {"ticker": "EFA", "name": "iShares MSCI EAFE ETF"},
        {"ticker": "VWO", "name": "Vanguard FTSE Emerging Markets ETF"},
        {"ticker": "IEMG", "name": "iShares Core MSCI Emerging Markets ETF"},
        {"ticker": "IJH", "name": "iShares Core S&P Mid-Cap ETF"},
        {"ticker": "IJR", "name": "iShares Core S&P Small-Cap ETF"},
        {"ticker": "VGT", "name": "Vanguard Information Technology ETF"},
        {"ticker": "ITOT", "name": "iShares Core S&P Total US Stock Mkt ETF"},
        {"ticker": "USMV", "name": "iShares MSCI USA Min Vol Factor ETF"},
        {"ticker": "RSP", "name": "Invesco S&P 500 Equal Weight ETF"},
        {"ticker": "MDY", "name": "SPDR S&P MIDCAP 400 ETF"},
        {"ticker": "XLI", "name": "Industrial Select Sector SPDR Fund"},
        {"ticker": "XLY", "name": "Consumer Discretionary Select Sector SPDR"},
        {"ticker": "XLP", "name": "Consumer Staples Select Sector SPDR Fund"},
        {"ticker": "SDY", "name": "SPDR S&P Dividend ETF"},
        {"ticker": "VNQ", "name": "Vanguard Real Estate ETF"},
        {"ticker": "SPYG", "name": "SPDR Portfolio S&P 500 Growth ETF"},
        {"ticker": "SPYV", "name": "SPDR Portfolio S&P 500 Value ETF"},
        {"ticker": "SCHX", "name": "Schwab US Large-Cap ETF"},
        {"ticker": "VXUS", "name": "Vanguard Total International Stock ETF"},
        {"ticker": "IWF", "name": "iShares Russell 1000 Growth ETF"},
        {"ticker": "IWD", "name": "iShares Russell 1000 Value ETF"},
        {"ticker": "QUAL", "name": "iShares MSCI USA Quality Factor ETF"},
        {"ticker": "MTUM", "name": "iShares MSCI USA Momentum Factor ETF"}
    ]
    return us_etf_top_50

import streamlit as st

def get_us_cache_key() -> str:
    import pytz
    try:
        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        is_weekday = now.weekday() < 5
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        is_market_active = is_weekday and (market_open <= now <= market_close)
        
        if is_market_active:
            # Round to nearest 5 minutes
            minute_round = (now.minute // 5) * 5
            return f"active_{now.strftime('%Y-%m-%d')}_{now.hour:02d}_{minute_round:02d}"
        else:
            # Round to nearest hour
            return f"closed_{now.strftime('%Y-%m-%d')}_{now.hour:02d}"
    except Exception:
        now = datetime.now()
        return f"fallback_{now.strftime('%Y-%m-%d')}_{now.hour:02d}"

@st.cache_data(ttl=3600)
def get_us_stock_data(ticker: str, start_date: str = None, end_date: str = None, cache_key: str = "") -> pd.DataFrame:
    """
    Fetches historical OHLCV data for a US ticker.
    Tries Toss API first, then falls back to yfinance.
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    def fallback_to_yf():
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
            print(f"Error fetching US data via yfinance for ticker {ticker}, trying static file: {str(e)}")
            
        import os
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
                print(f"Failed to load static US data for {ticker}: {e}")
                
        return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])

    # Toss API candles can be unreliable (missing dates or incorrect adjustment).
    # We bypass Toss candles and ALWAYS use yfinance for reliable historical data (SMA, MACD).
    # This also fixes the change_percent calculation because yfinance provides the correct previous close.
    return fallback_to_yf()

@st.cache_data(ttl=3600)
def get_us_stock_info(ticker: str, cache_key: str = "") -> dict:
    """
    Returns metadata and current price information for a US asset.
    Tries Toss API first, then falls back to Yahoo Search and yfinance.
    """
    try:
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
                
        def fallback_to_yf():
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
                df = get_us_stock_data(ticker, start_date, end_date, cache_key=cache_key)
                
                # Check if yfinance returned empty or default data
                if df.empty or (len(df) > 0 and 'Close' not in df.columns) or (len(df) == 0):
                    raise ValueError("No valid data from yfinance fallback.")
                    
                current_price = float(df.iloc[-1]['Close'])
                prev_close = float(df.iloc[-2]['Close']) if len(df) > 1 else current_price
                change_percent = ((current_price - prev_close) / prev_close) * 100
                return {
                    'ticker': ticker,
                    'name': asset_name,
                    'current_price': current_price,
                    'change_percent': change_percent,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            except Exception as e:
                print(f"yfinance info fallback failed for {ticker}, trying static file: {e}")
                
            import os
            import json
            static_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'toss', f'{ticker}_info.json')
            if os.path.exists(static_file):
                try:
                    with open(static_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Failed to load static US info for {ticker}: {e}")
                    
            return {
                'ticker': ticker,
                'name': asset_name,
                'current_price': 0.0,
                'change_percent': 0.0,
                'last_updated': "N/A"
            }
            
        from data_loader.toss_loader import get_toss_token
        token = get_toss_token()
        if not token:
            return fallback_to_yf()
            
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
                
                df = get_us_stock_data(ticker)
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
                return fallback_to_yf()
        else:
            return fallback_to_yf()
            
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
