import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

def fetch_stock_data(symbol, days=30):
    print(f"正在抓取 {symbol} 的數據 (最近 {days} 天)...")
    try:
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch history
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"警告: 找不到 {symbol} 的資料。")
            return False

        # Clean up data for CSV storage
        df.reset_index(inplace=True)
        df.columns = [c.replace(' ', '_').lower() for c in df.columns]
        
        # Create filename with date
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{symbol.replace('.', '_')}_{date_str}.csv"
        filepath = os.path.join("/home/tommy/stock-data-sync/data", filename)
        
        df.to_csv(filepath, index=False)
        print(f"成功！資料已儲存至: {filepath}")
        return True
    except Exception as e:
        print(f"發生錯誤 ({symbol}): {e}")
        return False

if __name__ == "__main__":
    # 預設抓取幾個台灣代表性股票做測試
    test_symbols = ["2330.TW", "2317.TW", "2454.TW"]
    for s in test_symbols:
        fetch_stock_data(s)
