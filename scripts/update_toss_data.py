import os
import sys
import json
import pandas as pd
import requests
from datetime import datetime

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'toss')

sys.path.append(os.path.join(PROJECT_ROOT, 'src'))
from data_loader.toss_loader import get_toss_token
from data_loader.kr_loader import KR_ASSETS, get_kr_stock_name
from dotenv import load_dotenv

def main():
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    token = get_toss_token()
    if not token:
        print("Failed to get Toss token. Please run locally with correct .env")
        return
        
    # Read favorites
    fav_file = os.path.join(PROJECT_ROOT, 'favorites.json')
    if not os.path.exists(fav_file):
        print("No favorites.json found.")
        return
        
    with open(fav_file, 'r', encoding='utf-8') as f:
        favorites = json.load(f)
        
        
    kr_tickers = list(favorites.get('KR', {}).values())
    us_tickers = list(favorites.get('US', {}).values())
    
    all_tickers = kr_tickers + us_tickers
    
    if not all_tickers:
        print("No tickers found in favorites.")
        return
        
    for ticker in all_tickers:
        print(f"Updating data for {ticker}...")
        
        # Global index skip
        if ticker.startswith("^"):
            print(f"Skipping global index {ticker}")
            continue
            
        # 1. Fetch Candles
        url = f"https://openapi.tossinvest.com/api/v1/candles?symbol={ticker}&interval=1d&count=200"
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            candles = data.get("result", {}).get("candles", [])
            if candles:
                df = pd.DataFrame(candles)
                df['Date'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
                df['Open'] = pd.to_numeric(df['openPrice'])
                df['High'] = pd.to_numeric(df['highPrice'])
                df['Low'] = pd.to_numeric(df['lowPrice'])
                df['Close'] = pd.to_numeric(df['closePrice'])
                df['Volume'] = pd.to_numeric(df['volume'])
                df = df.sort_values('Date').reset_index(drop=True)
                df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                
                csv_path = os.path.join(DATA_DIR, f'{ticker}.csv')
                df.to_csv(csv_path, index=False)
                print(f"  -> Saved {len(df)} candles to {csv_path}")
                
                # Pre-calculate daily change
                current_price = float(df.iloc[-1]['Close'])
                if len(df) > 1:
                    latest_date = df.iloc[-1]['Date'].date()
                    if latest_date == datetime.now().date():
                        prev = float(df.iloc[-2]['Close'])
                    else:
                        prev = float(df.iloc[-1]['Close'])
                    daily_change = ((current_price - prev) / prev) * 100
                else:
                    daily_change = 0.0
                    
                asset_name = KR_ASSETS.get(ticker, get_kr_stock_name(ticker)) if ticker in kr_tickers else ticker
                
                # Fetch Real-time price (optional, but good for accuracy)
                price_url = f"https://openapi.tossinvest.com/api/v1/prices?symbols={ticker}"
                p_res = requests.get(price_url, headers=headers)
                if p_res.status_code == 200:
                    p_data = p_res.json()
                    prices = p_data.get("result", [])
                    if prices:
                        current_price = float(prices[0].get("lastPrice", current_price))
                        if len(df) > 1:
                            daily_change = ((current_price - prev) / prev) * 100
                            
                info_data = {
                    'ticker': ticker,
                    'name': asset_name,
                    'current_price': current_price,
                    'change_percent': daily_change,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                json_path = os.path.join(DATA_DIR, f'{ticker}_info.json')
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(info_data, jf, ensure_ascii=False, indent=2)
                print(f"  -> Saved info to {json_path}")
            else:
                print(f"  -> No candles returned for {ticker}")
        else:
            print(f"  -> Failed to fetch candles: {res.status_code}")

if __name__ == '__main__':
    main()
