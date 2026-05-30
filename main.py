import requests
import pandas as pd
import datetime
import json
import time

def extract_twse_prices(json_data):
    """解析證交所回傳的 JSON，自動相容新舊版格式並抽出所有股票收盤價"""
    rows, fields = [], []
    
    if 'fields9' in json_data and 'data9' in json_data:
        fields = json_data['fields9']
        rows = json_data['data9']
    elif 'tables' in json_data:
        for table in json_data['tables']:
            if '每日收盤行情' in table.get('title', ''):
                fields = table.get('fields', [])
                rows = table.get('data', [])
                break
                
    if not fields or not rows:
        return {}
        
    try:
        code_idx = fields.index('證券代號')
        close_idx = fields.index('收盤價')
    except ValueError:
        return {}
        
    day_prices = {}
    for r in rows:
        code = r[code_idx].strip()
        # 只要標準的 4 位數台股（排除權證、ETF等）
        if len(code) == 4 and code.isdigit():
            close_str = r[close_idx].replace(',', '').strip()
            try:
                day_prices[code] = float(close_str)
            except ValueError:
                # 當天停牌或無交易則跳過
                continue
    return day_prices

def get_ma_cross_data():
    print("🚀 啟動證交所官方直連對接系統（抗斷線重裝版）...")
    
    trading_days_data = {}
    today = datetime.date.today()
    
    collected_count = 0
    lookback_days = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 最多倒退搜尋 40 天，直到集滿 15 個真實開盤交易日
    while collected_count < 15 and lookback_days < 40:
        target_date = today - datetime.timedelta(days=lookback_days)
        date_str = target_date.strftime('%Y%m%d')
        lookback_days += 1
        
        url = f"https://www.twse.org.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALLBUT0999"
        
        # 單日最多重試 3 次
        for attempt in range(1, 4):
            try:
                res = requests.get(url, headers=headers, timeout=15)
                
                if res.status_code != 200:
                    break
                    
                data = res.json()
                if data.get('stat') != 'OK':
                    break # 當天休市，直接跳出換下一天
                    
                day_prices = extract_twse_prices(data)
                if day_prices:
                    trading_days_data[date_str] = day_prices
                    collected_count += 1
                    print(f"✅ 成功下載官方 {date_str} 行情表（已集齊 {collected_count}/15 天）")
                
                time.sleep(2.0) # 保持好公民禮貌
                break # 成功了，跳出重試迴圈
                
            except Exception as e:
                print(f"⚠️ 讀取 {date_str} 失敗 (第 {attempt}/3 次嘗試)... 原因: {e}")
                if attempt < 3:
                    print("⏳ 觸發防禦機制：靜止 5 秒後重新撥號...")
                    time.sleep(5)
                else:
                    print(f"❌ 已連續失敗 3 次，跳過 {date_str}。")

    if len(trading_days_data) < 15:
        raise RuntimeError(f"🚨 歷史交易日收集不足！只收集到 {len(trading_days_data)} 天，無法計算均線。")

    print("📊 正在利用大數據矩陣計算全市場均線...")
    df = pd.DataFrame.from_dict(trading_days_data, orient='index').sort_index(ascending=True)
    
    ma5 = df.rolling(window=5).mean()
    ma10 = df.rolling(window=10).mean()
    
    last_ma5 = ma5.iloc[-1]
    last_ma10 = ma10.iloc[-1]
    prev_ma5 = ma5.iloc[-2]
    prev_ma10 = ma10.iloc[-2]
    
    golden_series = (prev_ma5 < prev_ma10) & (last_ma5 > last_ma10)
    death_series = (prev_ma5 > prev_ma10) & (last_ma5 < last_ma10)
    
    results = {
        "golden": sorted(golden_series[golden_series].index.tolist()),
        "death": sorted(death_series[death_series].index.tolist())
    }
    
    with open('results.json', 'w') as f:
        json.dump(results, f)
        
    print(f"🎉 【史詩級成功】已成功對接證交所！上市黃金交叉：{len(results['golden'])} 檔，死亡交叉：{len(results['death'])} 檔")

if __name__ == "__main__":
    get_ma_cross_data()
