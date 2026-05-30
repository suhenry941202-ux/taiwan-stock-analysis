import yfinance as yf
import pandas as pd
import json

def get_ma_cross_data():
    # 在這裡增加你要追蹤的股票代號，記得加上 .TW
    symbols = ['2330.TW', '2317.TW', '2454.TW', '2308.TW', '2303.TW'] 
    results = {"golden": [], "death": []}

    for symbol in symbols:
        # 下載過去一個月的數據
        df = yf.download(symbol, period="1mo", interval="1d")
        
        # 確保有足夠的資料量
        if len(df) < 15: continue
        
        # 計算 5MA 和 10MA
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        
        # 取得最後兩天的資料來判斷交叉
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 判斷邏輯
        if prev['MA5'] < prev['MA10'] and last['MA5'] > last['MA10']:
            results["golden"].append(symbol.replace('.TW', ''))
        elif prev['MA5'] > prev['MA10'] and last['MA5'] < last['MA10']:
            results["death"].append(symbol.replace('.TW', ''))
            
    # 將結果存入檔案
    with open('results.json', 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    get_ma_cross_data()
