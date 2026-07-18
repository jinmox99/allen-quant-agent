import sys

with open('src/backtester/simple.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add calculate_mdd helper
mdd_helper = '''
    def calculate_mdd(history):
        if not history: return 0.0
        import numpy as np
        arr = np.array(history)
        peaks = np.maximum.accumulate(arr)
        drawdowns = (peaks - arr) / peaks
        return float(np.max(drawdowns) * 100)
'''
content = content.replace('    bh_return = ((end_price - start_price) / start_price) * 100\n    bh_trades = ', mdd_helper + '\n    bh_return = ((end_price - start_price) / start_price) * 100\n    bh_history = (df[\'Close\'] / start_price * initial_capital).tolist()\n    bh_mdd = calculate_mdd(bh_history)\n    bh_trades = ')

# 2. Update simulate()
simulate_old = '''        for i in range(len(df)):
            sig = signals.iloc[i]
            price = float(df['Close'].iloc[i])
            date_str = dates.iloc[i]
            
            if sig == 1 and cash > 0:
                shares = cash / price
                trades.append({"Date": date_str, "Action": "BUY", "Price": price, "Shares": shares, "Reason": "조건 만족: 전액 매수"})
                cash = 0.0
            elif sig == -1 and shares > 0:
                cash = shares * price
                trades.append({"Date": date_str, "Action": "SELL", "Price": price, "Shares": shares, "Reason": "조건 만족: 전액 매도"})
                shares = 0.0
                
        final_value = cash + (shares * end_price)
        return {
            "return": ((final_value - initial_capital) / initial_capital) * 100,
            "trades": trades,
            "desc": desc
        }'''
simulate_new = '''        history = []
        for i in range(len(df)):
            sig = signals.iloc[i]
            price = float(df['Close'].iloc[i])
            date_str = dates.iloc[i]
            
            if sig == 1 and cash > 0:
                shares = cash / price
                trades.append({"Date": date_str, "Action": "BUY", "Price": price, "Shares": shares, "Reason": "조건 만족: 전액 매수"})
                cash = 0.0
            elif sig == -1 and shares > 0:
                cash = shares * price
                trades.append({"Date": date_str, "Action": "SELL", "Price": price, "Shares": shares, "Reason": "조건 만족: 전액 매도"})
                shares = 0.0
            history.append(cash + shares * price)
                
        final_value = cash + (shares * end_price)
        return {
            "return": ((final_value - initial_capital) / initial_capital) * 100,
            "mdd": calculate_mdd(history),
            "trades": trades,
            "desc": desc
        }'''
content = content.replace(simulate_old, simulate_new)

# 3. Update simulate_quant_momentum
quant_old = '''            elif (close_p > sma20 or macd > macd_signal) and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": "상승 추세 회복 (100% 재탑승)"})
                cash = 0.0
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "trades": trades, "desc": desc}'''
quant_new = '''            elif (close_p > sma20 or macd > macd_signal) and cash > 0:
                shares = cash / close_p
                trades.append({"Date": date_str, "Action": "BUY", "Price": close_p, "Shares": shares, "Reason": "상승 추세 회복 (100% 재탑승)"})
                cash = 0.0
            history.append(cash + shares * close_p)
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}'''
content = content.replace(quant_old, quant_new)
content = content.replace('cash = 0.0\n        shares = initial_capital / float(df[\'Close\'].iloc[0])\n        trades =', 'cash = 0.0\n        shares = initial_capital / float(df[\'Close\'].iloc[0])\n        history = [initial_capital]\n        trades =')

# 4. Update simulate_ema_cross
ema_old = '''            elif (ema5_prev >= ema20_prev and ema5 < ema20) and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": "EMA 5/20 데드크로스 (단기 하락)"})
                shares = 0.0
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "trades": trades, "desc": desc}'''
ema_new = '''            elif (ema5_prev >= ema20_prev and ema5 < ema20) and shares > 0:
                cash = shares * close_p
                trades.append({"Date": date_str, "Action": "SELL", "Price": close_p, "Shares": shares, "Reason": "EMA 5/20 데드크로스 (단기 하락)"})
                shares = 0.0
            history.append(cash + shares * close_p)
                
        final_value = cash + (shares * end_price)
        return {"return": ((final_value - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}'''
content = content.replace(ema_old, ema_new)
content = content.replace('cash = initial_capital\n        shares = 0.0\n        trades = []\n        \n        for i in range(1, len(df)):', 'cash = initial_capital\n        shares = 0.0\n        trades = []\n        history = [initial_capital]\n        \n        for i in range(1, len(df)):')

# 5. Update simulate_dual_momentum
dual_old = '''            elif (not cond1) and (not cond3) and shares > 0:
                sell_shares = shares
                cash += shares * close
                shares = 0.0
                trades.append({"Date": date_str, "Action": "SELL", "Price": close, "Shares": sell_shares, "Reason": "단기/중기 추세 꺾임 (현금화)"})
                
        val = cash + (shares * end_price)
        return {"return": ((val - initial_capital) / initial_capital) * 100, "trades": trades, "desc": desc}'''
dual_new = '''            elif (not cond1) and (not cond3) and shares > 0:
                sell_shares = shares
                cash += shares * close
                shares = 0.0
                trades.append({"Date": date_str, "Action": "SELL", "Price": close, "Shares": sell_shares, "Reason": "단기/중기 추세 꺾임 (현금화)"})
            history.append(cash + shares * close)
                
        val = cash + (shares * end_price)
        return {"return": ((val - initial_capital) / initial_capital) * 100, "mdd": calculate_mdd(history), "trades": trades, "desc": desc}'''
content = content.replace(dual_old, dual_new)
content = content.replace('cash = initial_capital\n        shares = 0.0\n        trades = []\n        for i in range(len(df)):', 'cash = initial_capital\n        shares = 0.0\n        trades = []\n        history = []\n        for i in range(len(df)):')

# 6. Update return dictionary
ret_old = '"단순 보유 (Buy & Hold)": {"return": bh_return, "trades": bh_trades, "desc": "가장 기본이 되는 벤치마크. 첫날에 현금을 전액 주식에 몰빵한 뒤, 끝까지 가만히 들고 있었을 경우의 수익률입니다."}'
ret_new = '"단순 보유 (Buy & Hold)": {"return": bh_return, "mdd": bh_mdd, "trades": bh_trades, "desc": "가장 기본이 되는 벤치마크. 첫날에 현금을 전액 주식에 몰빵한 뒤, 끝까지 가만히 들고 있었을 경우의 수익률입니다."}'
content = content.replace(ret_old, ret_new)

with open('src/backtester/simple.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated simple.py')
