import yfinance as yf
import pandas as pd
import datetime
import os

def fetch_tw_stock_data():
    # 1. 設定台股代號 (請確保格式正確)
    tickers = ["2330.TW", "2317.TW", "2454.TW", "2388.TW", "2354.TW"]
    
    file_name = "stock_data.csv"
    log_file = "last_run_log.txt" 
    
    print(f"🇹🇼 台股抓取任務啟動... 時間: {datetime.datetime.now()}")
    print(f"🔍 目標清單: {tickers}")

    try:
        all_data = []

        for ticker in tickers:
            print(f"  --> 正在嘗試抓取 {ticker}...")
            
            # 【優化】抓取過去 5 天的 5 分鐘線，增加資料量與成功率
            # period="5d" 確保有足夠的歷史資料可以抓取
            # interval="5m" 比 1m 更穩定，且適合自動化任務
            data = yf.download(ticker, period="5d", interval="5m", progress=False)
            
            if data.empty:
                print(f"  ⚠️ 警告: {ticker} 抓取失敗，可能查無資料或連線問題。")
                continue
            
            # 檢查是否抓到資料列
            if len(data) == 0:
                print(f"  ⚠️ 警告: {ticker} 雖然抓到了，但內容是空的。")
                continue

            # 整理資料
            data['Ticker'] = ticker
            data = data.reset_index()
            all_data.append(data)
            print(f"  ✅ {ticker} 抓取成功！({len(data)} 筆數據)")

        if not all_data:
            print("❌ 錯誤: 完全沒有抓到任何股票資料！")
            return

        # 2. 合併資料
        final_df = pd.concat(all_data, ignore_index=True)
        
        # 3. 儲存 CSV
        final_df.to_csv(file_name, index=False)
        print(f"✅ 成功將資料寫入 {file_name}")
        print(f"📊 總共處理了 {len(final_df)} 筆數據列。")

        # 4. 更新 Log 檔
        with open(log_file, "w", encoding="utf-8") as f:
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"最後更新時間: {...”
            # (這裡簡化一下，直接寫時間)
            f.write(f"最後更新時間: {now_str}\n")
            
        print(f"📝 更新了 {log_file}，這會觸發 Git Commit。")
        print("✨ 任務圓滿完成！")

    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")
        exit(1)

if __name__ == "__main__":
    fetch_tw_stock_data()
