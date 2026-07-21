import pandas as pd
import numpy as np
from itertools import product

def calculate_mdd(history):
    if not history: return 0.0
    import numpy as np
    arr = np.array(history)
    peaks = np.maximum.accumulate(arr)
    with np.errstate(divide='ignore', invalid='ignore'):
        drawdowns = (peaks - arr) / peaks
        drawdowns[~np.isfinite(drawdowns)] = 0.0
    return float(np.max(drawdowns) * 100)

def simulate_custom_dca(df: pd.DataFrame, 
                        initial_capital: float = 100000000.0, 
                        initial_buy_pct: float = 10.0,
                        daily_buy_pct: float = 1.0,
                        take_profit_pct: float = 5.0) -> dict:
    """
    Simulates a DCA strategy with compound asset tracking and Friday profit taking.
    - Start with initial_capital.
    - At cycle start (shares == 0), calc initial/daily buy amounts based on CURRENT total asset.
    - Every Friday, check if the stock return since cycle start >= take_profit_pct.
    - If yes, sell ALL shares. The cycle resets next day with new compounded total asset.
    """
    if df.empty or len(df) < 5:
        return {}

    if 'Date' not in df.columns:
        dates = df.index.strftime('%Y-%m-%d')
        df_dates = pd.to_datetime(df.index)
    else:
        if pd.api.types.is_datetime64_any_dtype(df['Date']):
            dates = df['Date'].dt.strftime('%Y-%m-%d')
            df_dates = df['Date']
        else:
            dates = df['Date'].astype(str)
            df_dates = pd.to_datetime(df['Date'])

    cash = initial_capital
    shares = 0.0
    
    cycle_start_price = float(df['Close'].iloc[0])
    cycle_initial_buy_amt = 0.0
    cycle_daily_buy_amt = 0.0
    
    trades = []
    history = []
    
    for i in range(len(df)):
        price = float(df['Close'].iloc[i])
        date_str = dates.iloc[i]
        current_date = df_dates.iloc[i]
        
        # 1. Daily Buy (or Initial Buy if starting a new cycle)
        if shares == 0:
            current_total_asset = cash  # shares are 0, so cash is total asset
            cycle_initial_buy_amt = current_total_asset * (initial_buy_pct / 100.0)
            cycle_daily_buy_amt = current_total_asset * (daily_buy_pct / 100.0)
            
            buy_amount = min(cash, cycle_initial_buy_amt)
            reason = f"사이클 시작 최초 매수 (총자산의 {initial_buy_pct:g}%)"
            cycle_start_price = price  # Reset stock tracking price
        else:
            buy_amount = min(cash, cycle_daily_buy_amt)
            reason = "일일 분할 매수"
            
        if buy_amount > 0:
            bought_shares = buy_amount / price
            shares += bought_shares
            cash -= buy_amount
            
            # Record trade only for the initial buy to avoid cluttering the trade log
            if "최초 매수" in reason:
                trades.append({"Date": date_str, "Action": "BUY", "Price": price, "Shares": bought_shares, "Reason": reason})
            
        if current_date.weekday() == 4 and shares > 0:
            # 주간 누적 주가 상승률 (해당 종목의 수익률 기준)
            stock_return_pct = ((price - cycle_start_price) / cycle_start_price) * 100
            
            if stock_return_pct >= take_profit_pct:
                # Take profit: sell ALL shares
                realized_cash = shares * price
                cash += realized_cash
                
                trades.append({
                    "Date": date_str, 
                    "Action": "SELL", 
                    "Price": price, 
                    "Shares": shares, 
                    "Reason": f"종목 목표 수익 달성 ({take_profit_pct}% 익절, 전량 매도)"
                })
                
                shares = 0.0
                
        history.append(cash + shares * price)
        
    final_value = cash + (shares * float(df['Close'].iloc[-1]))
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    
    desc = f"총 자산의 {initial_buy_pct:g}% 최초 매수 후 매일 {daily_buy_pct:g}% 분할매수. 주가 {take_profit_pct}% 상승 시 전량 매도 및 복리 재투자."
    
    return {
        "return": total_return,
        "mdd": calculate_mdd(history),
        "trades": trades,
        "desc": desc,
        "history": history,
        "final_cash": cash,
        "final_stock_value": shares * float(df['Close'].iloc[-1])
    }

def optimize_custom_dca(df: pd.DataFrame, 
                        initial_capital: float = 100000000.0,
                        initial_buy_pcts: list = [5.0, 10.0],
                        daily_buy_pcts: list = [1.0, 5.0],
                        take_profit_pcts: list = [5.0, 10.0]) -> dict:
    
    best_return = -99999.0
    best_params = {}
    best_result = {}
    
    results = []
    
    for ibuy, dbuy, tp in product(initial_buy_pcts, daily_buy_pcts, take_profit_pcts):
        res = simulate_custom_dca(df, initial_capital, ibuy, dbuy, tp)
        if not res:
            continue
            
        results.append({
            "initial_buy": ibuy,
            "daily_buy": dbuy,
            "take_profit": tp,
            "return": res["return"],
            "mdd": res["mdd"]
        })
        
        if res["return"] > best_return:
            best_return = res["return"]
            best_params = {"initial_buy": ibuy, "daily_buy": dbuy, "take_profit": tp}
            best_result = res
            
    # Calculate Buy & Hold for comparison
    start_price = float(df['Close'].iloc[0])
    end_price = float(df['Close'].iloc[-1])
    bh_return = ((end_price - start_price) / start_price) * 100
    bh_history = (df['Close'] / start_price * initial_capital).tolist()
    bh_mdd = calculate_mdd(bh_history)
    
    return {
        "best_params": best_params,
        "best_result": best_result,
        "all_results": results,
        "buy_and_hold": {
            "return": bh_return,
            "mdd": bh_mdd,
            "history": bh_history
        }
    }
