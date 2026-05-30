import yfinance as yf
import pandas as pd
import twstock
import json
import time

def get_ma_cross_data():
    # 1. 撈出全台股代號
    all_symbols = [f"{k}.TW" for k, v in twstock.codes.items() if v.type == '股票' and len(k) == 4]
    print(f"📢 系統啟動：總共偵測到 {len(all_symbols)} 檔台灣上市櫃股票。")
    
    results = {"golden": [], "death": []}
    
    # 2. 既然 yfinance 自己會處理防封鎖，我們可以把每批數量放大到 200 檔，跑得更快！
    chunk_size = 200
    success_count = 0 
    
    for i in range(0, len(all_symbols), chunk_size):
        chunk = all_symbols[i:i+chunk_size]
        print(f"⏳ 正在下載第 {i+1} ~ {min(i+chunk_size, len(all_symbols))} 檔股票...")
        
        try:
            # 💡【遵照錯誤指示】完全拿掉 session 參數！讓 yfinance 用它內建的頂級偽裝去抓資料
            df = yf.download(chunk, period="1mo", interval="1d", progress=False)
            
            if df.empty or 'Close' not in df:
                print(f"⚠️ 警告：此批次下載回傳空標籤。")
                continue
            
            # 自動剔除週末、假日的空白橫列
            close_df = df['Close'].dropna(how='all')
            
            if close_df.isna().all().all():
                print(f"⚠️ 警告：此批次所有的收盤價都是空白(NaN)！")
                continue
            
            if len(close_df) < 15:
                print(f"⚠️ 警告：歷史交易日不滿 15 天，無法計算均線。")
                continue
            
            # 記錄成功抓到資料的股票數量
            success_count += len(close_df.columns)
            
            # 計算均線
            ma5 = close_df.rolling(window=5).mean()
            ma10 = close_df.rolling(window=10).mean()
            
            last_ma5 = ma5.iloc[-1]
            last_ma10 = ma10.iloc[-1]
            prev_ma5 = ma5.iloc[-2]
            prev_ma10 = ma10.iloc[-2]
            
            # 比對交叉
            golden_series = (prev_ma5 < prev_ma10) & (last_ma5 > last_ma10)
            death_series = (prev_ma5 > prev_ma10) & (last_ma5 < last_ma10)
            
            golden_list = golden_series[golden_series].index.tolist()
            death_list = death_series[death_series].index.tolist()
            
            results["golden"].extend([s.replace('.TW', '') for s in golden_list])
            results["death"].extend([s.replace('.TW', '') for s in death_list])
            
            # 每批之間稍微休息 1.5 秒，維持好公民禮貌
            time.sleep(1.5)
            
        except Exception as e:
            print(f"❌ 處理此批次時發生錯誤: {e}")
            continue
            
    print(f"📊 掃描結束。全台股真實成功讀取到資料的共有：{success_count} 檔。")
    
    if success_count == 0:
        raise RuntimeError("🚨 失敗暴走！真實下載成功的股票數量還是 0！")
        
    results["golden"].sort()
    results["death"].sort()
    
    with open('results.json', 'w') as f:
        json.dump(results, f)
        
    print(f"🎉 【大功告成】成功寫入 results.json！黃金交叉：{len(results['golden'])} 檔，死亡交叉：{len(results['death'])} 檔")

if __name__ == "__main__":
    get_ma_cross_data()
