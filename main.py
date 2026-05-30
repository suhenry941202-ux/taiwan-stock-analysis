import yfinance as yf
import pandas as pd
import json

def get_ma_cross_data():
    # 這裡就是你以後想追蹤的股票清單
    symbols = ['2330.TW', '2317.TW', '2454.TW', '2308.TW'] 
    results = {"golden": [], "death": []}

    for symbol in symbols:
        df = yf.download(symbol, period="1mo", interval="1d")
        if len(df) < 15: continue
        
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 只存代號，不存任何測試文字
        name = symbol.replace('.TW', '')
        if prev['MA5'] < prev['MA10'] and last['MA5'] > last['MA10']:
            results["golden"].append(name)
        elif prev['MA5'] > prev['MA10'] and last['MA5'] < last['MA10']:
            results["death"].append(name)
            
    with open('results.json', 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    get_ma_cross_data()
