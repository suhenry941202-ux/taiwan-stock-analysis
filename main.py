import twstock
import pandas as pd

# 測試抓取台積電 (代號 2330) 的歷史資料
stock = twstock.Stock('2330')
data = stock.fetch_from(2026, 5) # 抓取 2026 年 5 月開始的資料

# 轉換成 Pandas 表格顯示
df = pd.DataFrame(data)
print(df.head()) # 印出前五筆資料看看
