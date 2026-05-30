import pandas as pd
import yfinance as yf
import datetime
import json

RESULTS_FILE = 'results.json'

# 這裡列出你想監控的股票代碼，建議分批處理以避免 GitHub Actions 超時
STOCK_LIST = ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2303.TW", "2881.TW"] 

def main():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    
    golden, death = [], []
    
    for ticker in STOCK_LIST:
        try:
            # 下載 1 個月數據確保均線計算有足夠資料
            df = yf.download(ticker, period="1mo", interval="1d", progress=False)
            if len(df) < 15: continue
            
            # 計算均線
            ma5 = df['Close'].rolling(window=5).mean()
            ma10 = df['Close'].rolling(window=10).mean()
            
            # 獲取最後兩個時間點的數值 (轉為 float 避免 Series 比較錯誤)
            ma5_prev, ma5_curr = float(ma5.iloc[-2]), float(ma5.iloc[-1])
            ma10_prev, ma10_curr = float(ma10.iloc[-2]), float(ma10.iloc[-1])
            
            # 判斷交叉邏輯
            if ma5_prev <= ma10_prev and ma5_curr > ma10_curr:
                golden.append(f"股票({ticker.split('.')[0]})")
            elif ma5_prev >= ma10_prev and ma5_curr < ma10_curr:
                death.append(f"股票({ticker.split('.')[0]})")
                
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue
            
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "update_time": now.strftime('%Y-%m-%d %H:%M:%S'),
            "data_date": now.strftime('%Y-%m-%d'),
            "status": "全市場精準掃描完成",
            "golden": golden,
            "death": death,
            "top10": []
        }, f)

if __name__ == "__main__":
    main()
