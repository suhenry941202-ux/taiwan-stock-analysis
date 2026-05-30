import requests
import pandas as pd
import datetime
import json
import os
import yfinance as yf

HISTORY_FILE = 'history.json'
RESULTS_FILE = 'results.json'

def fetch_current_market_data():
    url = "https://openapi.twse.org.tw/v1/exchangeReport/MI_INDEX"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200: return {}, {}, []
        data = res.json()
        current_prices, name_map, popular_list = {}, {}, []
        for item in data:
            code = item.get('Code', '').strip()
            if len(code) == 4 and code.isdigit():
                try:
                    name = item.get('Name', '未知')
                    close = float(str(item.get('ClosingPrice', '0')).replace(',', ''))
                    val = float(str(item.get('TradeValue', '0')).replace(',', ''))
                    vol = float(str(item.get('TradeVolume', '0')).replace(',', ''))
                    current_prices[code] = close
                    name_map[code] = name
                    popular_list.append({"code": code, "name": name, "price": close, "volume": vol, "value": round(val/100000000, 2)})
                except: continue
        popular_list.sort(key=lambda x: x['value'], reverse=True)
        return current_prices, name_map, popular_list[:10]
    except: return {}, {}, []

def main():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    
    # 讀取歷史與容錯處理
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = {}
            
    current_prices, name_map, top10 = fetch_current_market_data()
    
    if current_prices:
        history[now.strftime('%Y%m%d')] = current_prices
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
            
    # 安全檢查：若資料不足 10 天，無法計算均線
    if len(history) < 10:
        with open(RESULTS_FILE, 'w') as f:
            json.dump({"update_time": now.strftime('%Y-%m-%d %H:%M:%S'), "data_date": "資料累積中", "status": "正在累積歷史數據，請稍候...", "golden": [], "death": [], "top10": top10}, f)
        return

    # 運算邏輯
    df = pd.DataFrame.from_dict(history, orient='index').sort_index()
    df = df.apply(pd.to_numeric, errors='coerce').ffill().bfill()
    ma5 = df.rolling(window=5).mean()
    ma10 = df.rolling(window=10).mean()
    
    golden, death = [], []
    for col in df.columns:
        if col not in ma5.columns: continue
        is_golden = (ma5[col].shift(1) <= ma10[col].shift(1) + 0.01) & (ma5[col] > ma10[col])
        is_death = (ma5[col].shift(1) >= ma10[col].shift(1) - 0.01) & (ma5[col] < ma10[col])
        if is_golden.iloc[-1]: golden.append(f"{name_map.get(col, '未知')}({col})")
        if is_death.iloc[-1]: death.append(f"{name_map.get(col, '未知')}({col})")
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "update_time": now.strftime('%Y-%m-%d %H:%M:%S'),
            "data_date": max(history.keys()),
            "status": "系統運作正常",
            "golden": golden,
            "death": death,
            "top10": top10
        }, f)

if __name__ == "__main__":
    main()
