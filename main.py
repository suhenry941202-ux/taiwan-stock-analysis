import yfinance as yf
import pandas as pd
import twstock
import json

def get_ma_cross_data():
    # 1. 自動撈出所有台灣「上市與上櫃的股票」代號
    # 篩選條件：型態是 '股票' 且代號是 4 位數（自動過濾權證、特別股與 ETF）
    all_symbols = [f"{k}.TW" for k, v in twstock.codes.items() if v.type == '股票' and len(k) == 4]
    
    results = {"golden": [], "death": []}
    
    # 2. 分批處理（每批 100 檔），速度極快且絕對不會被封鎖
    chunk_size = 100
    for i in range(0, len(all_symbols), chunk_size):
        chunk = all_symbols[i:i+chunk_size]
        try:
            # 一口氣下載這 100 檔過去一個月的 K 線資料
            df = yf.download(chunk, period="1mo", interval="1d", progress=False)
            
            if df.empty or 'Close' not in df:
                continue
            
            close_df = df['Close']
            
            # 安全機制：如果這批剛好只有一檔成功，格式會變 Series，強制轉回 DataFrame
            if isinstance(close_df, pd.Series):
                close_df = close_df.to_frame()
            
            # 確保有足夠的交易日數據來計算均線
            if len(close_df) < 15:
                continue
            
            # 同步計算整批股票的 5MA 與 10MA
            ma5_df = close_df.rolling(window=5).mean()
            ma10_df = close_df.rolling(window=10).mean()
            
            # 取得最後兩天數據
            last_ma5 = ma5_df.iloc[-1]
            last_ma10 = ma10_df.iloc[-1]
            prev_ma5 = ma5_df.iloc[-2]
            prev_ma10 = ma10_df.iloc[-2]
            
            # 檢查這 100 檔裡面有哪些股票符合交叉條件
            for symbol in close_df.columns:
                try:
                    p_5 = prev_ma5[symbol]
                    p_10 = prev_ma10[symbol]
                    l_5 = last_ma5[symbol]
                    l_10 = last_ma10[symbol]
                    
                    # 排除空值
                    if pd.isna(p_5) or pd.isna(p_10) or pd.isna(l_5) or pd.isna(l_10):
                        continue
                    
                    # 轉成純數字進行比較
                    p_5, p_10, l_5, l_10 = float(p_5), float(p_10), float(l_5), float(l_10)
                    
                    name = symbol.replace('.TW', '')
                    if p_5 < p_10 and l_5 > l_10:
                        results["golden"].append(name)
                    elif p_5 > p_10 and l_5 < l_10:
                        results["death"].append(name)
                except Exception:
                    continue # 個別股票有問題就跳過，不影響大局
        except Exception as e:
            print(f"處理批次時發生錯誤: {e}")
            continue
    
    # 3. 將股票代號由小到大排序，讓網頁比較美觀
    results["golden"].sort()
    results["death"].sort()
    
    # 寫入檔案
    with open('results.json', 'w') as f:
        json.dump(results, f)
    print(f"全台股掃描完畢！黃金交叉：{len(results['golden'])} 檔，死亡交叉：{len(results['death'])} 檔")

if __name__ == "__main__":
    get_ma_cross_data()
