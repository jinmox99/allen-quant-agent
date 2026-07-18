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
    """Gets the Korean stock name dynamically from FDR."""
    global _KRX_LISTING_CACHE
    if _KRX_LISTING_CACHE is None:
        try:
            _KRX_LISTING_CACHE = fdr.StockListing('KRX')
        except Exception:
            return f"한국 종목 ({ticker})"
            
    try:
        # StockListing returns a DataFrame with 'Code' and 'Name'
        matches = _KRX_LISTING_CACHE[_KRX_LISTING_CACHE['Code'] == ticker]
        if not matches.empty:
            return matches.iloc[0]['Name']
    except Exception:
        pass
        
    return f"한국 종목 ({ticker})"

def get_kr_stock_data(ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Fetches historical OHLCV data for a Korean ETF/ETN ticker.
    
    Parameters:
    - ticker: str (e.g. '441800')
    - start_date: str (YYYY-MM-DD)
    - end_date: str (YYYY-MM-DD)
    
    Returns:
    - pd.DataFrame containing Date, Open, High, Low, Close, Volume, Change
    """
    if start_date is None:
        # Default to last 1 year
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    try:
        df = fdr.DataReader(ticker, start_date, end_date)
        if df.empty:
            raise ValueError(f"No data returned for KR ticker: {ticker}")
        
        # Reset index to make Date a column
        df = df.reset_index()
        # Standardize column names
        df.rename(columns={'index': 'Date'}, inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for ticker {ticker}: {str(e)}")
        # Return an empty DataFrame with standard columns as fallback
        return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change'])

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

