import yfinance as yf
import pandas as pd
import json

def get_ma_cross_data():
    symbols = ['2330.TW', '2317.TW', '2454.TW', '2308.TW', '2303.TW', '2412.TW'] 
    results = {"golden": [], "death": []}

    for symbol in symbols:
        try:
            # 抓取資料
            df = yf.download(symbol, period="1mo", interval="1d")
            if len(df) < 15: continue
            
            # 計算 MA
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            
            # 取得數值 (確保為純數值)
            last_ma5 = df['MA5'].iloc[-1].item()
            last_ma10 = df['MA10'].iloc[-1].item()
            prev_ma5 = df['MA5'].iloc[-2].item()
            prev_ma10 = df['MA10'].iloc[-2].item()
            
            # 判斷交叉
            name = symbol.replace('.TW', '')
            if prev_ma5 < prev_ma10 and last_ma5 > last_ma10:
                results["golden"].append(name)
            elif prev_ma5 > prev_ma10 and last_ma5 < last_ma10:
                results["death"].append(name)
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            continue
            
    # 存檔
    with open('results.json', 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    get_ma_cross_data()
