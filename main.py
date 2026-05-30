import pandas as pd
import yfinance as yf
import requests
import datetime
import json

RESULTS_FILE = 'results.json'
# 固定監控的 ETF
FIXED_LIST = ["0050.TW", "006208.TW"] 

def fetch_top_stocks():
    # 抓取市場熱門股前 10 名
    url = "https://openapi.twse.org.tw/v1/exchangeReport/MI_INDEX"
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        # 簡單篩選金額較大的前 10 檔
        top10 = sorted([d for d in data if len(d['Code'])==4], key=lambda x: float(str(x.get('TradeValue','0')).replace(',','')), reverse=True)[:10]
        return [f"{t['Code']}.TW" for t in top10]
    except: return []

def main():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    
    # 合併固定清單與熱門清單
    all_stocks = list(set(FIXED_LIST + fetch_top_stocks()))
    golden, death = [], []
    
    for ticker in all_stocks:
        try:
            df = yf.download(ticker, period="1mo", interval="1d", progress=False)
            if len(df) < 15: continue
            
            ma5 = df['Close'].rolling(window=5).mean()
            ma10 = df['Close'].rolling(window=10).mean()
            
            ma5_prev, ma5_curr = float(ma5.iloc[-2]), float(ma5.iloc[-1])
            ma10_prev, ma10_curr = float(ma10.iloc[-2]), float(ma10.iloc[-1])
            
            code = ticker.split('.')[0]
            if ma5_prev <= ma10_prev and ma5_curr > ma10_curr:
                golden.append(f"標的({code})")
            elif ma5_prev >= ma10_prev and ma5_curr < ma10_curr:
                death.append(f"標的({code})")
        except: continue
            
    with open(RESULTS_FILE, 'w') as f:
        json.dump({"update_time": now.strftime('%Y-%m-%d %H:%M:%S'), "golden": golden, "death": death}, f)

if __name__ == "__main__":
    main()
