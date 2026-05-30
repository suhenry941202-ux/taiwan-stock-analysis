import requests
import pandas as pd
import datetime
import json
import os

HISTORY_FILE = 'history.json'
RESULTS_FILE = 'results.json'

def fetch_openapi_prices():
    url = "https://openapi.twse.org.tw/v1/exchangeReport/MI_INDEX"
    print("🌐 正在連線證交所 OpenAPI 核心機房...", flush=True)
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return {}
        data = res.json()
        if not isinstance(data, list): return {}
        current_prices = {}
        for item in data:
            code = item.get('Code', '').strip() or item.get('證券代號', '').strip()
            if len(code) == 4 and code.isdigit():
                close_str = item.get('ClosingPrice') or item.get('收盤價', '0')
                close_str = str(close_str).replace(',', '').strip()
                try: current_prices[code] = float(close_str)
                except ValueError: continue
        return current_prices
    except Exception as e:
        print(f"❌ 錯誤: {e}", flush=True)
        return {}

def main():
    # 計算台北時間 (GitHub 伺服器預設是 UTC，必須 +8 小時)
    taipei_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    update_time_str = taipei_now.strftime('%Y-%m-%d %H:%M:%S')

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try: history = json.load(f)
            except json.JSONDecodeError: history = {}
    else:
        history = {}
        
    print(f"📁 成功載入歷史資料庫，目前已累積: {len(history)} 天的資料。", flush=True)

    current_prices = fetch_openapi_prices()
    if not current_prices:
        print("🚨 無法取得今日數據，終止本次執行。", flush=True)
        return

    today_str = datetime.date.today().strftime('%Y%m%d')
    if history:
        latest_date = max(history.keys())
        is_duplicate = True
        for check_code in ['2330', '2317', '2454']:
            if current_prices.get(check_code) != history[latest_date].get(check_code):
                is_duplicate = False
                break
        if is_duplicate:
            print(f"🛑 偵測到今日資料與歷史最新一天 ({latest_date}) 完全相同。今天為休市日，跳過更新！", flush=True)
            today_str = None

    if today_str:
        history[today_str] = current_prices
        history = dict(sorted(history.items())[-30:])
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
        print(f"✅ 成功將今日 ({today_str}) 數據寫入歷史資料庫！（當前總累積: {len(history)}/15 天）", flush=True)

    # 取得歷史資料庫中最新的股票開盤日期
    data_date_str = max(history.keys()) if history else "無資料"

    # 狀況 A：如果蓄水池不滿 15 天，也更新時間，避免網頁壞掉
    if len(history) < 15:
        print(f"⏳ 蓄水池累積進度：{len(history)}/15 天。", flush=True)
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                "update_time": update_time_str,
                "data_date": data_date_str,
                "golden": [],
                "death": [],
                "status": f"資料累積中 ({len(history)}/15天)"
            }, f)
        return

    # 狀況 B：資料集滿，啟動矩陣計算
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
    
    # 💡 在結果中打包時間資訊
    results = {
        "update_time": update_time_str,  # 網頁更新的系統時間
        "data_date": data_date_str,      # 股票資料截止的日期
        "status": "已集滿15天，訊號計算成功",
        "golden": sorted(golden_series[golden_series].index.tolist()),
        "death": sorted(death_series[death_series].index.tolist())
    }
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f)
        
    print(f"🎉 【大獲全勝】更新時間：{update_time_str}", flush=True)

if __name__ == "__main__":
    main()
