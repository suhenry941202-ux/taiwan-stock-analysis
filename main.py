import requests
import pandas as pd
import datetime
import json
import os
import yfinance as yf

HISTORY_FILE = 'history.json'
RESULTS_FILE = 'results.json'

def fetch_historical_data():
    """全市場核心權值股補齊 (擴展監控清單)"""
    print("🔄 正在執行全市場歷史數據回補...", flush=True)
    # 你可以隨時在這裡增加更多代碼，例如 "2303.TW", "2382.TW"
    targets = ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2881.TW", "2303.TW", "2382.TW", "2412.TW", "2882.TW", "2002.TW"]
    combined_data = {}
    
    for ticker_symbol in targets:
        try:
            hist = yf.Ticker(ticker_symbol).history(period="1mo")
            code = ticker_symbol.replace(".TW", "")
            for date, row in hist.tail(20).iterrows():
                date_str = date.strftime('%Y%m%d')
                if date_str not in combined_data: combined_data[date_str] = {}
                combined_data[date_str][code] = round(row['Close'], 2)
        except: continue
    return combined_data

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

    df = pd.DataFrame.from_dict(history, orient='index').sort_index()
    df = df.apply(pd.to_numeric, errors='coerce').ffill().bfill()
    
    ma5 = df.rolling(window=5).mean()
    ma10 = df.rolling(window=10).mean()
    
    golden_list, death_list = [], []
    for col in df.columns:
        if col not in ma5.columns: continue
        is_golden = (ma5[col].shift(1) <= ma10[col].shift(1) + 0.01) & (ma5[col] > ma10[col])
        is_death = (ma5[col].shift(1) >= ma10[col].shift(1) - 0.01) & (ma5[col] < ma10[col])
        if is_golden.iloc[-1]: golden_list.append(col)
        if is_death.iloc[-1]: death_list.append(col)
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "update_time": now.strftime('%Y-%m-%d %H:%M:%S'),
            "data_date": max(history.keys()),
            "status": "全市場掃描運作中",
            "golden": golden_list,
            "death": death_list,
            "top10": top10
        }, f)

if __name__ == "__main__":
    main()
