import pandas as pd
import numpy as np
from datetime import datetime
from ..analyzers.indicators import add_all_indicators, calculate_sma, calculate_rsi

def run_backtest(df: pd.DataFrame, 
                 initial_capital: float = 10000.0, 
                 commission: float = 0.001,  # 0.1% transaction cost
                 strategy_type: str = "SMA Crossover", 
                 params: dict = None) -> dict:
    """
    Runs a simulation-based backtest on a single stock's historical price DataFrame.
    
    Parameters:
    - df: pd.DataFrame (containing price data)
    - initial_capital: float
    - commission: float (rate of trading cost, e.g. 0.001 for 0.1%)
    - strategy_type: str ("SMA Crossover", "RSI Momentum", "Combined")
    - params: dict (configuration parameters)
    
    Returns:
    - dict containing equity_curve, trades, metrics
    """
    if df.empty or len(df) < 5:
        return {"metrics": {"error": "Insufficient data to run backtest"}}
        
    # Standardize params
    if params is None:
        params = {}
        
    df_runs = df.copy()
    
    # 1. Prepare indicators based on strategy parameters
    if strategy_type == "SMA Crossover":
        short_window = params.get("sma_short", 20)
        long_window = params.get("sma_long", 50)
        df_runs["Short_MA"] = calculate_sma(df_runs, short_window)
        df_runs["Long_MA"] = calculate_sma(df_runs, long_window)
    elif strategy_type == "RSI Momentum":
        rsi_window = params.get("rsi_period", 14)
        df_runs["RSI"] = calculate_rsi(df_runs, rsi_window)
        rsi_lower = params.get("rsi_buy", 30)
        rsi_upper = params.get("rsi_sell", 70)
    elif strategy_type == "Combined":
        short_window = params.get("sma_short", 20)
        long_window = params.get("sma_long", 50)
        df_runs["Short_MA"] = calculate_sma(df_runs, short_window)
        df_runs["Long_MA"] = calculate_sma(df_runs, long_window)
        rsi_window = params.get("rsi_period", 14)
        df_runs["RSI"] = calculate_rsi(df_runs, rsi_window)
        rsi_lower = params.get("rsi_buy", 35)
        rsi_upper = params.get("rsi_sell", 65)

    # 2. Simulation variables
    cash = initial_capital
    position = 0.0  # Shares held
    portfolio_value = initial_capital
    
    equity_curve = []
    trades = []
    
    # Fill NA to prevent crashing
    df_runs = df_runs.bfill().fillna(0)
    
    # 3. Step-by-step Daily Simulation
    for i in range(len(df_runs)):
        row = df_runs.iloc[i]
        date_str = pd.to_datetime(row["Date"]).strftime("%Y-%m-%d")
        close_price = float(row["Close"])
        
        # Check signal if we have enough data (avoid first few rows of NA)
        signal = "HOLD"
        
        if strategy_type == "SMA Crossover" and i > 0:
            prev_row = df_runs.iloc[i-1]
            # Golden Cross (Short MA crosses above Long MA)
            if prev_row["Short_MA"] <= prev_row["Long_MA"] and row["Short_MA"] > row["Long_MA"]:
                signal = "BUY"
            # Death Cross (Short MA crosses below Long MA)
            elif prev_row["Short_MA"] >= prev_row["Long_MA"] and row["Short_MA"] < row["Long_MA"]:
                signal = "SELL"
                
        elif strategy_type == "RSI Momentum" and i > 0:
            prev_row = df_runs.iloc[i-1]
            # RSI rises above lower boundary (Oversold recovery) or RSI crosses above 50
            if prev_row["RSI"] <= rsi_lower and row["RSI"] > rsi_lower:
                signal = "BUY"
            # RSI falls below upper boundary (Overbought cooling) or RSI crosses below 50
            elif prev_row["RSI"] >= rsi_upper and row["RSI"] < rsi_upper:
                signal = "SELL"
                
        elif strategy_type == "Combined" and i > 0:
            prev_row = df_runs.iloc[i-1]
            # Golden Cross + RSI is not overbought
            if (prev_row["Short_MA"] <= prev_row["Long_MA"] and row["Short_MA"] > row["Long_MA"]) and row["RSI"] < rsi_upper:
                signal = "BUY"
            # Death Cross or RSI falls from overbought
            elif (prev_row["Short_MA"] >= prev_row["Long_MA"] and row["Short_MA"] < row["Long_MA"]) or (prev_row["RSI"] >= rsi_upper and row["RSI"] < rsi_upper):
                signal = "SELL"
        
        # Execute Trades
        if signal == "BUY" and cash > 10:  # Allow buying if cash remains
            shares_to_buy = cash * (1.0 - commission) / close_price
            commission_paid = cash * commission
            position += shares_to_buy
            cash = 0.0
            trades.append({
                "Date": date_str,
                "Action": "BUY",
                "Price": close_price,
                "Shares": shares_to_buy,
                "Value": shares_to_buy * close_price,
                "Commission": commission_paid,
                "Cash": cash
            })
            
        elif signal == "SELL" and position > 0:
            value_sold = position * close_price
            commission_paid = value_sold * commission
            cash = value_sold - commission_paid
            trades.append({
                "Date": date_str,
                "Action": "SELL",
                "Price": close_price,
                "Shares": position,
                "Value": value_sold,
                "Commission": commission_paid,
                "Cash": cash
            })
            position = 0.0
            
        # Daily portfolio calculation
        portfolio_value = cash + (position * close_price)
        equity_curve.append({
            "Date": date_str,
            "Price": close_price,
            "Cash": cash,
            "Position": position,
            "Portfolio_Value": portfolio_value
        })
        
    # Convert to DataFrame
    eq_df = pd.DataFrame(equity_curve)
    
    # 4. Metric Calculations
    first_val = eq_df.iloc[0]["Portfolio_Value"]
    last_val = eq_df.iloc[-1]["Portfolio_Value"]
    
    total_return = ((last_val - first_val) / first_val) * 100
    
    # Benchmark return (Buy & Hold the asset itself)
    bench_start = eq_df.iloc[0]["Price"]
    bench_end = eq_df.iloc[-1]["Price"]
    benchmark_return = ((bench_end - bench_start) / bench_start) * 100
    
    # Calculate CAGR
    days = (pd.to_datetime(eq_df.iloc[-1]["Date"]) - pd.to_datetime(eq_df.iloc[0]["Date"])).days
    years = max(days / 365.25, 0.01) # Avoid division by zero
    cagr = (((last_val / first_val) ** (1 / years)) - 1) * 100
    
    # Calculate MDD (Maximum Drawdown)
    eq_df["Peak"] = eq_df["Portfolio_Value"].cummax()
    eq_df["Drawdown"] = (eq_df["Portfolio_Value"] - eq_df["Peak"]) / eq_df["Peak"]
    mdd = eq_df["Drawdown"].min() * 100
    
    # Daily Sharpe Ratio (Assuming 3% annual risk-free rate)
    eq_df["Daily_Return"] = eq_df["Portfolio_Value"].pct_change()
    daily_rf = 0.03 / 252
    excess_returns = eq_df["Daily_Return"] - daily_rf
    mean_excess = excess_returns.mean()
    std_excess = excess_returns.std()
    
    if std_excess > 0 and not np.isnan(std_excess):
        sharpe_ratio = (mean_excess / std_excess) * np.sqrt(252)
    else:
        sharpe_ratio = 0.0
        
    # Calculate Win Rate from closed trades
    closed_trades = []
    buy_trade = None
    for t in trades:
        if t["Action"] == "BUY":
            buy_trade = t
        elif t["Action"] == "SELL" and buy_trade is not None:
            profit = t["Value"] - buy_trade["Value"] - t["Commission"] - buy_trade["Commission"]
            closed_trades.append(profit)
            buy_trade = None
            
    win_rate = 0.0
    if len(closed_trades) > 0:
        wins = sum(1 for p in closed_trades if p > 0)
        win_rate = (wins / len(closed_trades)) * 100
        
    metrics = {
        "Initial_Capital": initial_capital,
        "Final_Capital": last_val,
        "Total_Return_Pct": total_return,
        "Benchmark_Return_Pct": benchmark_return,
        "CAGR_Pct": cagr,
        "MDD_Pct": mdd,
        "Sharpe_Ratio": sharpe_ratio,
        "Trade_Count": len(trades),
        "Win_Rate_Pct": win_rate
    }
    
    return {
        "equity_curve": eq_df,
        "trades": trades,
        "metrics": metrics
    }
