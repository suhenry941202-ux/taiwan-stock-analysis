import requests
import pandas as pd
import datetime
import json
import os

HISTORY_FILE = 'history.json'
RESULTS_FILE = 'results.json'

def fetch_openapi_prices():
    """直連證交所 OpenAPI 機房"""
    url = "https://openapi.twse.org.tw/v1/exchangeReport/MI_INDEX"
    print("🌐 正在連線證交所 OpenAPI 核心機房...", flush=True)
    
    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            print(f"❌ OpenAPI 伺服器回傳錯誤代碼: {res.status_code}", flush=True)
            return {}
        
        data = res.json()
        if not isinstance(data, list):
            print("❌ 回傳格式異常，預期應為陣列資料。", flush=True)
            return {}
            
        current_prices = {}
        for item in data:
            code = item.get('Code', '').strip() or item.get('證券代號', '').strip()
            if len(code) == 4 and code.isdigit():
                close_str = item.get('ClosingPrice') or item.get('收盤價', '0')
                close_str = str(close_str).replace(',', '').strip()
                try:
                    current_prices[code] = float(close_str)
                except ValueError:
                    continue
                    
        return current_prices
    except Exception as e:
        print(f"❌ 連線 OpenAPI 發生非預期錯誤: {e}", flush=True)
        return {}

def main():
    # 🎯 第一步：不論有沒有股市資料，先精準鎖定當下的台北時間 (UTC+8)
    tz_taipei = datetime.timezone(datetime.timedelta(hours=8))
    taipei_now = datetime.datetime.now(tz_taipei)
    update_time_str = taipei_now.strftime('%Y-%m-%d %H:%M:%S')

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
    
    # 先預設一個目前已知的最新歷史資料日期
    data_date_str = max(history.keys()) if history else "無歷史資料"

    # 2. 抓取今天最新數據
    current_prices = fetch_openapi_prices()
    
    # 💡【關鍵修正】：如果今天是週末/假日，OpenAPI 沒有資料
    if not current_prices:
        print("🚨 無法取得今日數據（可能因週末休市或API維護）。", flush=True)
        print(f"📝 正在將檢查時間 ({update_time_str}) 與『休市狀態』寫入網頁...", flush=True)
        
        # 就算沒開盤，也要更新網頁的時間跟狀態，讓使用者安心！
        status_msg = f"週末/假日休市中 (資料庫已儲存: {len(history)}/15天)" if len(history) < 15 else "週末/假日休市中 (訊號暫不更新)"
        
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                "update_time": update_time_str,
                "data_date": data_date_str,
                "status": status_msg,
                "golden": [],
                "death": []
            }, f)
        return # 溫雅地結束

    # 3. 智慧防重複機制
    today_str = taipei_now.strftime('%Y%m%d')
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

    # 4. 如果是全新交易日，存入資料庫
    if today_str:
        history[today_str] = current_prices
        history = dict(sorted(history.items())[-30:])
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
        print(f"✅ 成功將今日 ({today_str}) 數據寫入歷史資料庫！（當前總累積: {len(history)}/15 天）", flush=True)
        data_date_str = today_str

    # 5. 檢查蓄水池進度是否足夠 15 天
    if len(history) < 15:
        print(f"⏳ 蓄水池累積進度：{len(history)}/15 天。尚無法計算均線交叉。", flush=True)
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                "update_time": update_time_str,
                "data_date": data_date_str,
                "status": f"資料累積中 ({len(history)}/15天)",
                "golden": [],
                "death": []
            }, f)
        return

    # 6. 資料集滿 15 天，啟動均線矩陣計算
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
        "update_time": update_time_str,
        "data_date": data_date_str,
        "status": "已集滿15天，訊號計算成功",
        "golden": sorted(golden_series[golden_series].index.tolist()),
        "death": sorted(death_series[death_series].index.tolist())
    }
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f)
        
    print(f"🎉 【大獲全勝】更新時間：{update_time_str}，黃金交叉：{len(results['golden'])} 檔", flush=True)

if __name__ == "__main__":
    main()
