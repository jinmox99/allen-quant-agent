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
                        initial_buy_amount: float = 10000000.0,
                        daily_buy_amount: float = 100000.0,
                        take_profit_pct: float = 5.0) -> dict:
    """
    Simulates a Dollar Cost Averaging (DCA) strategy with Friday profit taking.
    - Start with initial_capital.
    - At the start of a cycle (shares == 0), buy `initial_buy_amount` worth of stock.
    - Every subsequent day, buy `daily_buy_amount` worth of stock.
    - Every Friday, check if the return of the currently held shares is >= `take_profit_pct`.
      If yes, sell all shares and realize the profit into cash, starting a new cycle.
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
    total_invested_for_current_cycle = 0.0
    
    trades = []
    history = []
    
    for i in range(len(df)):
        price = float(df['Close'].iloc[i])
        date_str = dates.iloc[i]
        current_date = df_dates.iloc[i]
        
        # 1. Daily Buy (or Initial Buy if starting a new cycle)
        if shares == 0:
            buy_amount = min(cash, initial_buy_amount)
            reason = "사이클 시작 최초 매수"
        else:
            buy_amount = min(cash, daily_buy_amount)
            reason = "일일 분할 매수"
            
        if buy_amount > 0:
            bought_shares = buy_amount / price
            shares += bought_shares
            cash -= buy_amount
            total_invested_for_current_cycle += buy_amount
            
            # Record trade only for the initial buy to avoid cluttering the trade log
            if reason == "사이클 시작 최초 매수":
                trades.append({"Date": date_str, "Action": "BUY", "Price": price, "Shares": bought_shares, "Reason": reason})
            
        # 2. Friday Profit Taking Check
        # current_date.weekday(): Monday=0, ..., Friday=4
        if current_date.weekday() == 4 and shares > 0:
            current_value = shares * price
            current_return_pct = ((current_value - total_invested_for_current_cycle) / total_invested_for_current_cycle) * 100
            
            if current_return_pct >= take_profit_pct:
                # Take profit: sell all shares
                cash += current_value
                trades.append({
                    "Date": date_str, 
                    "Action": "SELL", 
                    "Price": price, 
                    "Shares": shares, 
                    "Reason": f"금요일 익절 조건 달성 (+{current_return_pct:.2f}%)"
                })
                shares = 0.0
                total_invested_for_current_cycle = 0.0
                
        history.append(cash + shares * price)
        
    final_value = cash + (shares * float(df['Close'].iloc[-1]))
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    
    desc = f"최초 {initial_buy_amount:,.0f}원 매수 후 매일 {daily_buy_amount:,.0f}원씩 분할매수. 매주 금요일 보유 수익률이 {take_profit_pct}% 이상일 때 전량 매도."
    
    return {
        "return": total_return,
        "mdd": calculate_mdd(history),
        "trades": trades,
        "desc": desc,
        "history": history
    }

def optimize_custom_dca(df: pd.DataFrame, 
                        initial_capital: float = 100000000.0,
                        initial_buy_amount: float = 10000000.0,
                        daily_buy_amounts: list = [50000, 100000, 200000],
                        take_profit_pcts: list = [3.0, 5.0, 7.0, 10.0]) -> dict:
    
    best_return = -99999.0
    best_params = {}
    best_result = {}
    
    results = []
    
    for dbuy, tp in product(daily_buy_amounts, take_profit_pcts):
        res = simulate_custom_dca(df, initial_capital, initial_buy_amount, dbuy, tp)
        if not res:
            continue
            
        results.append({
            "daily_buy": dbuy,
            "take_profit": tp,
            "return": res["return"],
            "mdd": res["mdd"]
        })
        
        if res["return"] > best_return:
            best_return = res["return"]
            best_params = {"initial_buy": initial_buy_amount, "daily_buy": dbuy, "take_profit": tp}
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
