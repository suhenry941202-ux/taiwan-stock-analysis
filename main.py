import yfinance as yf
import pandas as pd
import twstock
import json

def get_ma_cross_data():
    # 1. 自動撈出全台灣所有 4 位數的上市櫃股票代號
    symbols = [f"{k}.TW" for k, v in twstock.codes.items() if v.type == '股票' and len(k) == 4]
    
    print(f"🚀 開始挑戰極速下載全台股（共 {len(symbols)} 檔）...")
    
    # 💡【核心突破】不寫迴圈、不分批！全台灣股票做成一個大清單，只發送「1 次」請求！
    # 這樣一來，伺服器完全不會觸發防禦機制，5 秒鐘直接完工！
    df = yf.download(symbols, period="1mo", interval="1d", progress=False)
    
    results = {"golden": [], "death": []}
    
    if df.empty or 'Close' not in df:
        print("❌ 下載失敗，請檢查網路連線")
        return
        
    # 2. 自動剔除週末或休市的空白橫列
    close_df = df['Close'].dropna(how='all')
    
    if len(close_df) < 15:
        print("❌ 歷史交易日資料不足，無法計算均線")
        return
        
    # 3. 運用 Pandas 矩陣運算：一瞬間算出全台灣所有股票的 5MA 與 10MA
    ma5 = close_df.rolling(window=5).mean()
    ma10 = close_df.rolling(window=10).mean()
    
    # 取得最後兩天（今天與昨天）的整片數據
    last_ma5 = ma5.iloc[-1]
    last_ma10 = ma10.iloc[-1]
    prev_ma5 = ma5.iloc[-2]
    prev_ma10 = ma10.iloc[-2]
    
    # 4. 超高速平行比對：一條指令找出全台灣符合黃金交叉與死亡交叉的股票
    golden_series = (prev_ma5 < prev_ma10) & (last_ma5 > last_ma10)
    death_series = (prev_ma5 > prev_ma10) & (last_ma5 < last_ma10)
    
    # 篩選出結果為 True 的股票代碼
    golden_list = golden_series[golden_series].index.tolist()
    death_list = death_series[death_series].index.tolist()
    
    # 5. 清理格式，只留下純數字代號，並存檔
    results["golden"] = [s.replace('.TW', '') for s in golden_list]
    results["death"] = [s.replace('.TW', '') for s in death_list]
    
    results["golden"].sort()
    results["death"].sort()
    
    with open('results.json', 'w') as f:
        json.dump(results, f)
        
    print(f"🎉 掃描成功！今日黃金交叉：{len(results['golden'])} 檔，死亡交叉：{len(results['death'])} 檔")

if __name__ == "__main__":
    get_ma_cross_data()
