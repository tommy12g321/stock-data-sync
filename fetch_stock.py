import yfinance as yf
import pandas as pd
import os

def fetch_data():
    # 你想要抓取的股票代碼，可以隨時增加
    symbols = ["2330.TW", "2317.TW", "2454.TW"] 
    
    for symbol in symbols:
        print(f"正在抓取: {symbol}")
        try:
            # 抓取最近 5 天的數據
            data = yf.download(symbol, period="5d", interval="1d")
            if not data.empty:
                # 轉換成 CSV 格式
                filename = f"{symbol}.csv"
                data.to_csv(filename)
                print(f"成功儲存: {filename}")
            else:
                print(f"{symbol} 沒抓到數據")
        except Exception as e:
            print(f"抓取 {symbol} 失敗: {e}")

if __name__ == "__main_main":
    fetch_data()
