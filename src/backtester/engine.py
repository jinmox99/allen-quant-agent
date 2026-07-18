import pandas as pd
import numpy as np
from datetime import datetime

def run_band_backtest(df_ord: pd.DataFrame,
                      df_lev: pd.DataFrame,
                      initial_capital: float = 15000.0,
                      commission: float = 0.0,
                      upper_band: float = 0.20,
                      lower_band: float = 0.20,
                      additional_buy_ratio: float = 0.10,
                      initial_stock_ratio: float = 0.667) -> dict:
    """
    Unified Band Trading Strategy.
    - Initial Stock Base Value = initial_capital * initial_stock_ratio
    - Initial Cash = initial_capital * (1.0 - initial_stock_ratio)
    - Upper Limit = Base Stock Value * (1 + upper_band)
    - Lower Limit = Base Stock Value * (1 - lower_band)
    - If stock value >= Upper Limit: Sell back to Base Stock Value (gain cash)
    - If stock value <= Lower Limit: Buy up to Base Stock Value * (1 + additional_buy_ratio) (using cash)
    """
    if df_ord.empty or df_lev.empty:
        return {"error": "Insufficient data"}

    df_o = df_ord[['Date', 'Close']].rename(columns={'Close': 'Close_Ord'})
    df_l = df_lev[['Date', 'Close']].rename(columns={'Close': 'Close_Lev'})
    df_merged = pd.merge(df_o, df_l, on='Date', how='inner').sort_values('Date').reset_index(drop=True)

    if len(df_merged) < 2:
        return {"error": "Insufficient overlapping data"}

    close_ord_0 = float(df_merged.iloc[0]["Close_Ord"])
    close_lev_0 = float(df_merged.iloc[0]["Close_Lev"])

    # Portfolio initialization
    base_stock_value = initial_capital * initial_stock_ratio
    cash = initial_capital * (1.0 - initial_stock_ratio)
    shares = (base_stock_value * (1.0 - commission)) / close_lev_0

    
    # Recalculate actual stock value after entry commission
    stock_value = shares * close_lev_0
    initial_actual_value = cash + stock_value

    eq_curve = []
    trades = [{
        "Date": pd.to_datetime(df_merged.iloc[0]["Date"]).strftime("%Y-%m-%d"),
        "Action": "INIT", 
        "Details": f"초기 자산 설정 (기준주식: {base_stock_value:,.0f} | 현금: {cash:,.0f})",
        "Ord_Price": close_ord_0, "Lev_Price": close_lev_0,
        "Ord_Shares": 0.0, "Lev_Shares": shares,
        "Portfolio_Value": initial_actual_value,
        "Cash": cash, "Stock_Value": stock_value
    }]

    for i in range(len(df_merged)):
        row = df_merged.iloc[i]
        date_str = pd.to_datetime(row["Date"]).strftime("%Y-%m-%d")
        close_ord = float(row["Close_Ord"])
        close_lev = float(row["Close_Lev"])

        val_stock = shares * close_lev
        total = val_stock + cash

        upper_limit = base_stock_value * (1.0 + upper_band)
        lower_limit = base_stock_value * (1.0 - lower_band)

        action_type = "HOLD"
        details = ""

        # 1. Upper Band Exceeded: Sell down to base_stock_value
        if val_stock >= upper_limit:
            sell_value = val_stock - base_stock_value
            shares_to_sell = sell_value / close_lev
            cash += sell_value * (1.0 - commission)
            shares -= shares_to_sell
            val_stock = shares * close_lev
            action_type = f"SELL (상한초과↑→{base_stock_value:,.0f})"
            details = f"주식 가치 {val_stock + sell_value:,.0f}원 (상한 {upper_limit:,.0f} 초과) -> {sell_value:,.0f}원 매도 현금화"

            trades.append({
                "Date": date_str, "Action": action_type,
                "Details": details,
                "Ord_Price": close_ord, "Lev_Price": close_lev,
                "Ord_Shares": 0.0, "Lev_Shares": shares,
                "Portfolio_Value": val_stock + cash,
                "Cash": cash, "Stock_Value": val_stock
            })

        # 2. Lower Band Exceeded: Buy up to base_stock_value + additional_buy_ratio
        elif val_stock <= lower_limit:
            target_stock_value = base_stock_value * (1.0 + additional_buy_ratio)
            buy_value = target_stock_value - val_stock
            
            # Check cash availability (including commission)
            max_buy_val = cash / (1.0 + commission)
            actual_buy_val = min(buy_value, max_buy_val)

            if actual_buy_val > 0:
                shares_to_buy = actual_buy_val / close_lev
                shares += shares_to_buy
                cash -= actual_buy_val * (1.0 + commission)
                val_stock = shares * close_lev
                action_type = f"BUY (하한미달↓→{target_stock_value:,.0f})"
                details = f"주식 가치 {val_stock - actual_buy_val:,.0f}원 (하한 {lower_limit:,.0f} 미달) -> {actual_buy_val:,.0f}원 추가 매수"

                trades.append({
                    "Date": date_str, "Action": action_type,
                    "Details": details,
                    "Ord_Price": close_ord, "Lev_Price": close_lev,
                    "Ord_Shares": 0.0, "Lev_Shares": shares,
                    "Portfolio_Value": val_stock + cash,
                    "Cash": cash, "Stock_Value": val_stock
                })

        eq_curve.append({
            "Date": date_str, 
            "Portfolio_Value": val_stock + cash,
            "Cash": cash,
            "Stock_Value": val_stock
        })

    # Metrics calculation
    eq_df = pd.DataFrame(eq_curve)
    eq_bh_ord = df_merged["Close_Ord"] / close_ord_0 * initial_capital
    eq_bh_lev = df_merged["Close_Lev"] / close_lev_0 * initial_capital
    eq_bh_blend = (df_merged["Close_Ord"] / close_ord_0 * (initial_capital * 0.5)) + \
                  (df_merged["Close_Lev"] / close_lev_0 * (initial_capital * 0.5))

    results_df = pd.DataFrame({
        "Date": df_merged["Date"],
        "BH_Ord": eq_bh_ord,
        "BH_Lev": eq_bh_lev,
        "BH_Blend": eq_bh_blend,
        "Strategy": eq_df["Portfolio_Value"].values
    })

    def get_metrics(curve, bh_curve):
        first, last = curve.iloc[0], curve.iloc[-1]
        ret = ((last - first) / first) * 100
        bh_ret = ((bh_curve.iloc[-1] - bh_curve.iloc[0]) / bh_curve.iloc[0]) * 100
        days = (pd.to_datetime(results_df.iloc[-1]["Date"]) - pd.to_datetime(results_df.iloc[0]["Date"])).days
        years = max(days / 365.25, 0.01)
        cagr = (((last / first) ** (1 / years)) - 1) * 100
        peak = curve.cummax()
        mdd = ((curve - peak) / peak).min() * 100
        daily_ret = curve.pct_change()
        excess = daily_ret - 0.03 / 252
        sharpe = (excess.mean() / excess.std()) * np.sqrt(252) if excess.std() > 0 else 0.0
        return {"Final_Capital": last, "Total_Return_Pct": ret, "Benchmark_Return_Pct": bh_ret,
                "CAGR_Pct": cagr, "MDD_Pct": mdd, "Sharpe_Ratio": sharpe}

    metrics_ord = get_metrics(results_df["BH_Ord"], results_df["BH_Ord"])
    metrics_lev = get_metrics(results_df["BH_Lev"], results_df["BH_Lev"])
    metrics_blend = get_metrics(results_df["BH_Blend"], results_df["BH_Blend"])
    metrics = get_metrics(results_df["Strategy"], results_df["BH_Blend"])
    metrics["Trade_Count"] = len(trades)

    return {
        "curves": results_df,
        "metrics": metrics,
        "metrics_ord": metrics_ord,
        "metrics_lev": metrics_lev,
        "metrics_blend": metrics_blend,
        "trades": trades
    }
