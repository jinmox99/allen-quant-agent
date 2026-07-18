import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

df = yf.download("^KS200", start=start_date, end=end_date, progress=False)
print("--- RAW DOWNLOAD ---")
print(df)
