import pandas as pd
import yfinance as yf
import datetime
import json

RESULTS_FILE = 'results.json'
# 若要增加更多股票，請在此列表新增，例如: ["2330.TW", "2317.TW", "2454.TW", ...]
STOCK_LIST = ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2303.TW", "2881.TW"] 

def main():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    golden, death, ticker_data = [], [], []
    
    for ticker in STOCK_LIST:
        try:
            df = yf.download(ticker, period="1mo", interval="1d", progress=False)
            if len(df) < 15: continue
            
            ma5 = df['Close'].rolling(window=5).mean()
            ma10 = df['Close'].rolling(window=10).mean()
            
            ma5_prev, ma5_curr = float(ma5.iloc[-2]), float(ma5.iloc[-1])
            ma10_prev, ma10_curr = float(ma10.iloc[-2]), float(ma10.iloc[-1])
            
            code = ticker.split('.')[0]
            if ma5_prev <= ma10_prev and ma5_curr > ma10_curr:
                golden.append(f"股票({code})")
            elif ma5_prev >= ma10_prev and ma5_curr < ma10_curr:
                death.append(f"股票({code})")
            
            ticker_data.append({"code": code, "price": round(float(df['Close'].iloc[-1]), 2)})
        except: continue
            
    with open(RESULTS_FILE, 'w') as f:
        json.dump({"update_time": now.strftime('%Y-%m-%d %H:%M:%S'), "golden": golden, "death": death, "list": ticker_data}, f)

if __name__ == "__main__":
    main()
