import yfinance as yf
import pandas as pd
import twstock
import json

def get_ma_cross_data():
    # 1. 自動撈出所有台灣上市櫃股票代號
    all_symbols = [f"{k}.TW" for k, v in twstock.codes.items() if v.type == '股票' and len(k) == 4]
    
    results = {"golden": [], "death": []}
    
    # 2. 分批處理（每批 100 檔）
    chunk_size = 100
    for i in range(0, len(all_symbols), chunk_size):
        chunk = all_symbols[i:i+chunk_size]
        try:
            df = yf.download(chunk, period="1mo", interval="1d", progress=False)
            
            if df.empty or 'Close' not in df:
                continue
            
            close_df = df['Close']
            
            if isinstance(close_df, pd.Series):
                close_df = close_df.to_frame()
            
            # 💡【核心修復：終結週末地雷】
            # 這行會把「完全沒有交易數據」的假日或週末列直接刪除，確保最後一行永遠是最近一個交易日（週五）
            close_df = close_df.dropna(how='all')
            
            if len(close_df) < 15:
                continue
            
            # 同步計算 5MA 與 10MA
            ma5_df = close_df.rolling(window=5).mean()
            ma10_df = close_df.rolling(window=10).mean()
            
            # 取得最後兩天數據（此時最後一天已經正確對齊週五）
            last_ma5 = ma5_df.iloc[-1]
            last_ma10 = ma10_df.iloc[-1]
            prev_ma5 = ma5_df.iloc[-2]
            prev_ma10 = ma10_df.iloc[-2]
            
            # 檢查交叉條件
            for symbol in close_df.columns:
                try:
                    p_5 = prev_ma5[symbol]
                    p_10 = prev_ma10[symbol]
                    l_5 = last_ma5[symbol]
                    l_10 = last_ma10[symbol]
                    
                    if pd.isna(p_5) or pd.isna(p_10) or pd.isna(l_5) or pd.isna(l_10):
                        continue
                    
                    p_5, p_10, l_5, l_10 = float(p_5), float(p_10), float(l_5), float(l_10)
                    
                    name = symbol.replace('.TW', '')
                    if p_5 < p_10 and l_5 > l_10:
                        results["golden"].append(name)
                    elif p_5 > p_10 and l_5 < l_10:
                        results["death"].append(name)
                except Exception:
                    continue
        except Exception as e:
            print(f"處理批次時發生錯誤: {e}")
            continue
    
    results["golden"].sort()
    results["death"].sort()
    
    with open('results.json', 'w') as f:
        json.dump(results, f)
    print(f"全台股掃描完畢！黃金交叉：{len(results['golden'])} 檔，死亡交叉：{len(results['death'])} 檔")

if __name__ == "__main__":
    get_ma_cross_data()
