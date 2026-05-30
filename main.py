import requests
import pandas as pd
import datetime
import json
import os

HISTORY_FILE = 'history.json'
RESULTS_FILE = 'results.json'

def fetch_openapi_prices():
    """直連證交所 OpenAPI 機房，0.5秒極速下載當日全台股行情"""
    url = "https://openapi.twse.org.tw/v1/exchangeReport/MI_INDEX"
    print("🌐 正在連線證交所 OpenAPI 核心機房...", flush=True)
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            print(f"❌ OpenAPI 伺服器回傳錯誤代碼: {res.status_code}", flush=True)
            return {}
        
        data = res.json()
        if not isinstance(data, list):
            print("❌ 回傳格式異常，預期應為陣列資料。", flush=True)
            return {}
            
        current_prices = {}
        for item in data:
            # OpenAPI 的欄位名稱通常為英文：Code (代號), ClosingPrice (收盤價)
            code = item.get('Code', '').strip()
            # 相容部分中文欄位狀況
            if not code:
                code = item.get('證券代號', '').strip()
                
            if len(code) == 4 and code.isdigit():
                close_str = item.get('ClosingPrice') or item.get('收盤價', '0')
                close_str = str(close_str).replace(',', '').strip()
                try:
                    current_prices[code] = float(close_str)
                except ValueError:
                    continue # 停牌或無交易則跳過
                    
        return current_prices
    except Exception as e:
        print(f"❌ 連線 OpenAPI 發生非預期錯誤: {e}", flush=True)
        return {}

def main():
    # 1. 讀取現有的歷史資料庫
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = {}
    else:
        history = {}
        
    print(f"📁 成功載入歷史資料庫，目前已累積: {len(history)} 天的資料。", flush=True)

    # 2. 抓取今天最新數據
    current_prices = fetch_openapi_prices()
    if not current_prices:
        print("🚨 無法取得今日數據，終止本次執行。", flush=True)
        return

    # 3. 智慧防重複機制：比對今天跟歷史最後一天的台積電(2330)與鴻海(2317)股價
    # 如果完全一樣，代表今天可能是週末/假日，證交所還沒更新資料
    today_str = datetime.date.today().strftime('%Y%m%d')
    if history:
        latest_date = max(history.keys())
        is_duplicate = True
        for check_code in ['2330', '2317', '2454']:
            if current_prices.get(check_code) != history[latest_date].get(check_code):
                is_duplicate = False
                break
        if is_duplicate:
            print(f"🛑 偵測到今日資料與歷史最新一天 ({latest_date}) 完全相同。今天應為休市日，跳過更新！", flush=True)
            today_str = None

    # 4. 如果是全新交易日，存入儲蓄豬
    if today_str:
        history[today_str] = current_prices
        # 只保留最近 30 天的資料，避免檔案無限膨脹
        history = dict(sorted(history.items())[-30:])
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
        print(f"✅ 成功將今日 ({today_str}) 數據寫入歷史資料庫！（當前總累積: {len(history)}/15 天）", flush=True)

    # 5. 檢查蓄水池進度：夠不夠 15 天計算均線？
    if len(history) < 15:
        print(f"⏳ 蓄水池累積進度：{len(history)}/15 天。資料量還不夠計算 5MA/10MA 黃金交叉，請讓它每天自動跑，集滿後訊號就會誕生！", flush=True)
        # 先建立一個空的結果檔案防止噴錯
        if not os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'w') as f:
                json.dump({"golden": [], "death": []}, f)
        return

    # 6. 資料集滿，啟動矩陣計算
    print("📊 蓄水池已滿！正在計算全市場 5MA / 10MA 交叉訊號...", flush=True)
    df = pd.DataFrame.from_dict(history, orient='index').sort_index(ascending=True)
    
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
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f)
        
    print(f"🎉 【大獲全勝】黃金交叉：{len(results['golden'])} 檔，死亡交叉：{len(results['death'])} 檔", flush=True)

if __name__ == "__main__":
    main()
