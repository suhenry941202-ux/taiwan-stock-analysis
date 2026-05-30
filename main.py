import twstock
import pandas as pd
import json

def debug_stock_data():
    sid = '2330' # 台積電
    stock = twstock.Stock(sid)
    
    # 強制往前抓 3 個月，確保數據一定有
    data = stock.fetch_from(2026, 3) 
    
    print(f"--- 偵錯模式 ---")
    print(f"抓取到 {len(data)} 筆數據")
    
    if len(data) > 0:
        print(f"最新一筆數據: {data[-1]}")
    else:
        print("失敗：沒有抓到任何數據")

    # 模擬產生一點數據寫入 JSON，確認流程是否通暢
    results = {"golden": ["2330(測試)"], "death": []}
    with open('results.json', 'w') as f:
        json.dump(results, f)
    print("已強制寫入測試數據到 results.json")

debug_stock_data()
