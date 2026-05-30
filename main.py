import twstock
import pandas as pd
import json

def get_ma_cross_data():
    stocks = ['2330', '2317', '2454'] 
    results = {"golden": [], "death": []}

    for sid in stocks:
        stock = twstock.Stock(sid)
        # 為了保證有足夠數據，我們改用 fetch_from 往前抓取更久
        data = stock.fetch_from(2026, 1) 
        
        if len(data) < 20: 
            print(f"股票 {sid} 資料太少，無法計算，目前僅有 {len(data)} 筆")
            continue
            
        df = pd.DataFrame(data)
        
        # 計算移動平均線
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        
        # 檢查最後幾筆計算結果是否為空 (這很常見)
        if df['MA5'].isna().iloc[-1] or df['MA10'].isna().iloc[-1]:
            print(f"股票 {sid} 計算結果為空")
            continue

        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        print(f"{sid} 最新收盤: {last['close']}, 5MA: {last['MA5']:.2f}, 10MA: {last['MA10']:.2f}")

        if prev['MA5'] < prev['MA10'] and last['MA5'] > last['MA10']:
            results["golden"].append(sid)
        if prev['MA5'] > prev['MA10'] and last['MA5'] < last['MA10']:
            results["death"].append(sid)
            
    with open('results.json', 'w') as f:
        json.dump(results, f)
    print("分析完成，資料已儲存")

get_ma_cross_data()    print("分析完成，結果已存入 results.json")

get_ma_cross_data()
