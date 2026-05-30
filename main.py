import requests
import pandas as pd
import datetime
import json
import os
import yfinance as yf

HISTORY_FILE = 'history.json'
RESULTS_FILE = 'results.json'

def fetch_historical_data():
    """使用 yfinance 補齊 2330 歷史數據作為基準"""
    try:
        hist = yf.Ticker("2330.TW").history(period="1mo")
        data = {}
        for date, row in hist.tail(20).iterrows():
            data[date.strftime('%Y%m%d')] = {"2330": round(row['Close'], 2)}
        return data
    except: return {}

def fetch_current_market_data():
    """抓取證交所最新盤後行情"""
    url = "https://openapi.twse.org.tw/v1/exchangeReport/MI_INDEX"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200: return {}, []
        data = res.json()
        current_prices = {}
        popular_list = []
        for item in data:
            code = item.get('Code', '').strip()
            if len(code) == 4 and code.isdigit():
                try:
                    close = float(str(item.get('ClosingPrice', '0')).replace(',', ''))
                    val = float(str(item.get('TradeValue', '0')).replace(',', ''))
                    current_prices[code] = close
                    popular_list.append({"code": code, "name": item.get('Name', ''), "price": close, "value": round(val/100000000, 2)})
                except: continue
        popular_list.sort(key=lambda x: x['value'], reverse=True)
        return current_prices, popular_list[:10]
    except: return {}, []

def main():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    
    # 讀取並合併數據
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = {}
            
    if len(history) < 10:
        history.update(fetch_historical_data())

    current_prices, top10 = fetch_current_market_data()
    if current_prices:
        history[now.strftime('%Y%m%d')] = current_prices
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)

    # 【核心升級】使用 DataFrame 進行精確交叉計算
    df = pd.DataFrame.from_dict(history, orient='index').sort_index()
    # 將所有非數值轉為 NaN
    df = df.apply(pd.to_numeric, errors='coerce').fillna(method='ffill')
    
    ma5 = df.rolling(window=5).mean()
    ma10 = df.rolling(window=10).mean()
    
    # 交叉邏輯：MA5 從下往上穿過 MA10
    # 增加一個極微小的 tolerance，避免浮點數誤差導致漏判
    tolerance = 0.0001
    golden_s = (ma5.shift(1) <= ma10.shift(1) + tolerance) & (ma5 > ma10)
    death_s = (ma5.shift(1) >= ma10.shift(1) - tolerance) & (ma5 < ma10)
    
    # 只取最後一天的訊號
    last_golden = golden_s.iloc[-1]
    last_death = death_s.iloc[-1]
    
    golden_list = last_golden[last_golden].index.tolist()
    death_list = last_death[last_death].index.tolist()

    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "update_time": now.strftime('%Y-%m-%d %H:%M:%S'),
            "data_date": max(history.keys()),
            "status": "工業級偵測模式運作中",
            "golden": golden_list,
            "death": death_list,
            "top10": top10
        }, f)

if __name__ == "__main__":
    main()
