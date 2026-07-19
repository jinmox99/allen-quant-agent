import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict

# internal modules
from data_loader.kr_loader import get_kr_top_50, get_kr_etfs_all, get_kr_stock_data, get_krx_cache_key
from data_loader.us_loader import get_us_top_50, get_us_etf_top_50, get_us_stock_data, get_us_cache_key
from analyzers.indicators import add_all_indicators
from analyzers.trend import analyze_trend

@st.cache_data(ttl=3600, show_spinner=False)
def rank_stocks(market: str) -> pd.DataFrame:
    """
    Fetches the top 50 assets for the given market (KR, US, KR_ETF, US_ETF),
    calculates their 5 technical indicators, and ranks them by total score.
    Returns a DataFrame containing the results.
    """
    is_kr = market.startswith("KR")
    
    # 1. Get universe
    if market == "KR":
        top50 = get_kr_top_50()
        cache_key = get_krx_cache_key()
    elif market == "KR_ETF":
        top50 = get_kr_etfs_all()
        cache_key = get_krx_cache_key()
    elif market == "US":
        top50 = get_us_top_50()
        cache_key = get_us_cache_key()
    elif market == "US_ETF":
        top50 = get_us_etf_top_50()
        cache_key = get_us_cache_key()
    else:
        top50 = []
        cache_key = ""
        
    results = []
    
    # Needs at least 250 days for indicators like Close_6M_ago, SMA_120
    fetch_start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Optional: Streamlit progress bar callback if we want to show progress
    # But since this is cached, we might not always see it, so we handle it gracefully in main.py
    for i, stock in enumerate(top50):
        ticker = stock['ticker']
        name = stock['name']
        
        if is_kr:
            df = get_kr_stock_data(ticker, start_date=fetch_start_date, cache_key=cache_key)
        else:
            df = get_us_stock_data(ticker, start_date=fetch_start_date, cache_key=cache_key)
            
        if df.empty or len(df) < 50:
            continue
            
        # Add indicators
        df = add_all_indicators(df)
        
        # Analyze trend
        signals = analyze_trend(df)
        
        # Calculate scores
        sma_score = signals.get('sma', {}).get('score', 0)
        macd_score = signals.get('macd', {}).get('score', 0)
        qm_score = signals.get('quant_momentum', {}).get('score', 0)
        ema_score = signals.get('ema_cross', {}).get('score', 0)
        dm_score = signals.get('dual_momentum', {}).get('score', 0)
        
        total_score = sma_score + macd_score + qm_score + ema_score + dm_score
        
        # Current Price & change (Optional, nice for display)
        current_price = df.iloc[-1]['Close']
        if len(df) > 1:
            prev_price = df.iloc[-2]['Close']
            change = (current_price - prev_price) / prev_price * 100
        else:
            change = 0.0
            
        results.append({
            '종목명': name,
            'Ticker': ticker,
            '총점': total_score,
            'SMA': sma_score,
            'MACD': macd_score,
            '퀀트모멘텀': qm_score,
            'EMA크로스': ema_score,
            '듀얼모멘텀': dm_score,
            '현재가': current_price,
            '등락률(%)': change
        })
        
    # Create DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by total score descending
    if not results_df.empty:
        results_df = results_df.sort_values(by='총점', ascending=False).reset_index(drop=True)
        # Add Rank
        results_df.index = results_df.index + 1
        results_df = results_df.reset_index().rename(columns={'index': '순위'})
        
    return results_df
