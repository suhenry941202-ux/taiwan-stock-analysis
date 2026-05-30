import requests
import pandas as pd
import datetime
import json
import os

HISTORY_FILE = 'history.json'
RESULTS_FILE = 'results.json'

def fetch_openapi_prices():
    """直連證交所 OpenAPI 機房，同時抓取收盤價與熱門度數據"""
    url = "https://openapi.twse.org.tw/v1/exchangeReport/MI_INDEX"
    print("🌐 正在連線證交所 OpenAPI 核心機房...", flush=True)
    
    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            print(f"❌ OpenAPI 伺服器回傳錯誤代碼: {res.status_code}", flush=True)
            return {}, []
        
        data = res.json()
        if not isinstance(data, list):
            print("❌ 回傳格式異常，預期應為陣列資料。", flush=True)
            return {}, []
            
        current_prices = {}
        popular_candidates = []
        
        for item in data:
            code = item.get('Code', '').strip() or item.get('證券代號', '').strip()
            name = item.get('Name', '').strip() or item.get('證券名稱', '').strip()
            
            # 過濾標準 4 位數台股
            if len(code) == 4 and code.isdigit():
                close_str = item.get('ClosingPrice') or item.get('收盤價', '0')
                close_str = str(close_str).replace(',', '').strip()
                
                value_str = item.get('TradeValue') or item.get('成交金額', '0')
                value_str = str(value_str).replace(',', '').strip()
                
                volume_str = item.get('TradeVolume') or item.get('成交股數', '0')
                volume_str = str(volume_str).replace(',', '').strip()
                
                try:
                    # 1. 均線專用收盤價
                    close_val = float(close_str)
                    current_prices[code] = close_val
                    
                    # 2. 熱門度專用數據（成交金額與成交量）
                    val_float = float(value_str)
                    vol_int = int(float(volume_str))
                    
                    vol_lots = round(vol_int / 1000)       # 股轉為「張」
                    val_yi = round(val_float / 100000000, 2) # 元轉為「億元']
                    
                    popular_candidates.append({
                        "code": code,
                        "name": name,
                        "price": close_val,
                        "volume": vol_lots,
                        "value": val_yi
                    })
                except ValueError:
                    continue # 當天停牌或無交易則跳過
                    
        # 依成交金額（億元）由大到小排序，取前 10 名
        popular_candidates.sort(key=lambda x: x['value'], reverse=True)
        top10_popular = popular_candidates[:10]
        
        return current_prices, top10_popular
    except Exception as e:
        print(f"❌ 連線 OpenAPI 發生非預期錯誤: {e}", flush=True)
        return {}, []

def main():
    tz_taipei = datetime.timezone(datetime.timedelta(hours=8))
    taipei_now = datetime.datetime.now(tz_taipei)
    update_time_str = taipei_now.strftime('%Y-%m-%d %H:%M:%S')

    # 讀取現有的歷史資料庫
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try: history = json.load(f)
            except json.JSONDecodeError: history = {}
    else:
        history = {}
        
    print(f"📁 成功載入歷史資料庫，目前已累積: {len(history)} 天的資料。", flush=True)
    data_date_str = max(history.keys()) if history else "無歷史資料"

    # 讀取舊的結果，用來在週末時留存熱門股榜單不被洗掉
    old_top10 = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            try:
                old_res = json.load(f)
                old_top10 = old_res.get('top10', [])
            except:
                pass

    # 抓取最新數據
    current_prices, top10_popular = fetch_openapi_prices()
    
    # 如果是週末/假日沒資料
    if not current_prices:
        print("🚨 無法取得今日數據（週末或休市）。將保留上一次的熱門榜單。", flush=True)
        status_msg = f"週末/假日休市中 (資料庫已儲存: {len(history)}/15天)" if len(history) < 15 else "週末/假日休市中 (訊號暫不更新)"
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                "update_time": update_time_str,
                "data_date": data_date_str,
                "status": status_msg,
                "golden": [],
                "death": [],
                "top10": old_top10 # 繼承舊資料，防空檔洗白
            }, f)
        return

    # 智慧防重複機制
    today_str = taipei_now.strftime('%Y%m%d')
    if history:
        latest_date = max(history.keys())
        is_duplicate = True
        for check_code in ['2330', '2317', '2454']:
            if current_prices.get(check_code) != history[latest_date].get(check_code):
                is_duplicate = False
                break
        if is_duplicate:
            print(f"🛑 偵測到今日資料與歷史最新一天 ({latest_date}) 完全相同。休市日跳過更新！", flush=True)
            today_str = None

    # 全新交易日寫入資料庫
    if today_str:
        history[today_str] = current_prices
        history = dict(sorted(history.items())[-30:])
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
        print(f"✅ 成功將今日 ({today_str}) 數據寫入歷史資料庫！", flush=True)
        data_date_str = today_str

    # 檢查蓄水池進度
    if len(history) < 15:
        print(f"⏳ 蓄水池累積進度：{len(history)}/15 天。", flush=True)
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                "update_time": update_time_str,
                "data_date": data_date_str,
                "status": f"資料累積中 ({len(history)}/15天)",
                "golden": [],
                "death": [],
                "top10": top10
