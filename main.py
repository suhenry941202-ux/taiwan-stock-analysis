import yfinance as yf
import pandas as pd
import twstock
import json
import requests # 💡 引入網路請求模組來做偽裝
import time

def get_ma_cross_data():
    # 1. 撈出全台股代號
    all_symbols = [f"{k}.TW" for k, v in twstock.codes.items() if v.type == '股票' and len(k) == 4]
    print(f"📢 系統啟動：總共偵測到 {len(all_symbols)} 檔台灣上市櫃股票。")
    
    # 💡【核心突破：隱形斗篷】建立一個偽裝成一般 Chrome 瀏覽器的連線工作階段
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    results = {"golden": [], "death": []}
    
    # 2. 安全分批（每批 150 檔），搭配瀏覽器偽裝，既不會網址過長，也不會被封鎖
    chunk_size = 150
    success_count = 0 # 用來計算到底有幾檔股票成功抓到數值
    
    for i in range(0, len(all_symbols), chunk_size):
        chunk = all_symbols[i:i+chunk_size]
        print(f"⏳ 正在下載第 {i+1} ~ {min(i+chunk_size, len(all_symbols))} 檔股票...")
        
        try:
            # 💡 將偽裝好的 session 餵給 yfinance
            df = yf.download(chunk, period="1mo", interval="1d", progress=False, session=session)
            
            if df.empty or 'Close' not in df:
                print(f"⚠️ 警告：此批次下載回傳空標籤，Yahoo 可能開始阻擋。")
                continue
            
            close_df = df['Close'].dropna(how='all')
            
            # 檢查這批資料是不是被 Yahoo 用一堆空白(NaN)惡意敷衍
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
            
            # 稍微休息 1 秒，保持禮貌
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ 處理此批次時發生錯誤: {e}")
            continue
            
    print(f"📊 掃描結束。全台股真實成功讀取到資料的共有：{success_count} 檔。")
    
    # 💡【核心防呆：戳破假成功】
    # 如果全台灣跑完，成功下載的數量居然是 0，代表 100% 被 Yahoo 防火牆全面封鎖了！
    # 我們直接中斷程式、主動報錯，讓 GitHub Actions 亮起紅燈！
    if success_count == 0:
        raise RuntimeError("🚨 失敗暴走！真實下載成功的股票數量為 0！這代表 GitHub 雲端 IP 被封鎖了，請檢查日誌。")
        
    results["golden"].sort()
    results["death"].sort()
    
    with open('results.json', 'w') as f:
        json.dump(results, f)
        
    print(f"🎉 【大功告成】成功寫入 results.json！黃金交叉：{len(results['golden'])} 檔，死亡交叉：{len(results['death'])} 檔")

if __name__ == "__main__":
    get_ma_cross_data()
