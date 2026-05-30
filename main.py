import requests
import pandas as pd
import datetime
import json
import os

HISTORY_FILE = 'history.json'
RESULTS_FILE = 'results.json'

def fetch_current_market_data():
    """抓取最新市場行情"""
    url = "https://openapi.twse.org.tw/v1/exchangeReport/MI_INDEX"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200: return {}, []
        data = res.json()
        
        current_prices = {}
        popular_list = []
        
        for item in data:
            code = item.get('Code', '').strip()
            name = item.get('Name', '').strip()
            if len(code) == 4 and code.isdigit():
                try:
                    close = float(str(item.get('ClosingPrice', '0')).replace(',', ''))
                    val = float(str(item.get('TradeValue', '0')).replace(',', ''))
                    vol = int(float(str(item.get('TradeVolume', '0')).replace(',', '')))
                    
                    current_prices[code] = close
                    popular_list.append({"code": code, "name": name, "price": close, "volume": round(vol/1000), "value": round(val/100000000, 2)})
                except: continue
        
        popular_list.sort(key=lambda x: x['value'], reverse=True)
        return current_prices, popular_list[:10]
    except: return {}, []

def main():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    
    # 讀取歷史
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = {}

    # 取得最新資料
    current_prices, top10 = fetch_current_market_data()
    
    # 如果週一開盤有新資料，更新歷史
    today_str = now.strftime('%Y%m%d')
    if current_prices:
        history[today_str] = current_prices
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    
    # 【關鍵突破】：只要資料大於 5 天就開始算交叉 (不需死等 15 天)
    df = pd.DataFrame.from_dict(history, orient='index').sort_index()
    
    golden, death = [], []
    if len(df) >= 10: # 稍微集滿一點即可計算
        ma5 = df.rolling(window=5).mean()
        ma10 = df.rolling(window=10).mean()
        
        golden_s = (ma5.iloc[-2] < ma10.iloc[-2]) & (ma5.iloc[-1] > ma10.iloc[-1])
        death_s = (ma5.iloc[-2] > ma10.iloc[-2]) & (ma5.iloc[-1] < ma10.iloc[-1])
        
        golden = sorted(golden_s[golden_s].index.tolist())
        death = sorted(death_s[death_s].index.tolist())

    # 寫入結果
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "update_time": now.strftime('%Y-%m-%d %H:%M:%S'),
            "data_date": max(history.keys()) if history else "無資料",
            "status": f"運作正常 (歷史樣本: {len(history)}天)",
            "golden": golden,
            "death": death,
            "top10": top10
        }, f)

if __name__ == "__main__":
    main()
