import yfinance as yf
import pandas as pd
import json

def get_ma_cross_data():
    # 這裡放入你想追蹤的所有股票代碼 (台股請加 .TW)
    symbols = ['2330.TW', '2317.TW', '2454.TW', '2308.TW', '2303.TW', '2603.TW', '2412.TW'] 
    results = {"golden": [], "death": []}

    for symbol in symbols:
        try:
            # 下載過去 30 天數據，確保資料充足
            df = yf.download(symbol, period="1mo", interval="1d")
            
            if len(df) < 15: continue
            
            # 計算 5MA 與 10MA
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            
            # 取得最後兩個交易日的資料進行交叉比對
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # 判斷邏輯
            if prev['MA5'] < prev['MA10'] and last['MA5'] > last['MA10']:
                results["golden"].append(symbol.replace('.TW', ''))
            elif prev['MA5'] > prev['MA10'] and last['MA5'] < last['MA10']:
                results["death"].append(symbol.replace('.TW', ''))
        except Exception as e:
            print(f"處理 {symbol} 時發生錯誤: {e}")
            continue
            
    # 將結果存入 JSON
    with open('results.json', 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    get_ma_cross_data()
