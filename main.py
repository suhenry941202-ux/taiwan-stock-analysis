import twstock
import pandas as pd
import json

def get_ma_cross_data():
    # 這裡示範抓取幾檔熱門股，未來可以擴充成全市場清單
    stocks = ['2330', '2317', '2454'] 
    results = {"golden": [], "death": []}

    for sid in stocks:
        stock = twstock.Stock(sid)
        # 抓取最近 20 天的資料以計算 5MA, 10MA
        data = stock.fetch_from(2026, 5) 
        df = pd.DataFrame(data)
        
        if len(df) < 10: continue
        
        # 計算移動平均線
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        
        # 取最後兩天來判斷是否交叉
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 黃金交叉: 昨天 MA5 < MA10, 今天 MA5 > MA10
        if prev['MA5'] < prev['MA10'] and last['MA5'] > last['MA10']:
            results["golden"].append(sid)
            
        # 死亡交叉: 昨天 MA5 > MA10, 今天 MA5 < MA10
        if prev['MA5'] > prev['MA10'] and last['MA5'] < last['MA10']:
            results["death"].append(sid)
            
    # 將結果存成 JSON 檔案
    with open('results.json', 'w') as f:
        json.dump(results, f)
    print("分析完成，結果已存入 results.json")

get_ma_cross_data()
