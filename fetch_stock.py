import yfinance as yf
import pandas as pd
import datetime
import os

def fetch_tw_stock_data():
    # 1. 設定台股代號 (記得要加 .TW)
    tickers = ["2330.TW", "2317.TW", "2454.TW", "2388.TW", "2354.TW"]
    
    file_name = "stock_data.csv"
    log_file = "last_run_log.txt" 
    
    print(f"🇹🇼 台股抓取任務啟動... 時間: {datetime.datetime.now()}")
    print(f"🔍 目標清單: {tickers}")

    try:
        all_data = []

        for ticker in tickers:
            print(f"  --> 正在抓取 {ticker}...")
            # 抓取最近 1 天的資料
            data = ytd_data = yf.download(ticker, period="1d", interval="1m", progress=False)
            
            if data.empty:
                print(f"  ⚠️ 警告: {ticker} 抓不到資料，跳過。")
                continue
            
            # 整理資料
            data['Ticker'] = ticker
            data = data.reset_index()
            all_data.append(data)

        if not all_data:
            print("❌ 錯誤: 完全沒有抓到任何股票資料！")
            return

        # 2. 合併資料
        final_df = pd.concat(all_data, ignore_index=True)
        
        # 3. 儲存 CSV
        final_df.to_csv(file_name, index=False)
        print(f"✅ 成功將資料寫入 {file_name}")
        print(f"📊 總共處理了 {len(final_df)} 筆數據列。")

        # 4. 【關鍵】更新 Log 檔，確保 Git 偵測到變動
        # 這行絕對不會再有錯誤符號了
        with open(log_file, "w", encoding="utf-8") as f:
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"最後更新時間: {now_str}\n")
            
        print(f"📝 更新了 {log_file}，這會觸發 Git Commit。")
        print("✨ 任務圓滿完成！")

    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")
        exit(1)

if __name__ == "__main__":
    fetch_tw_stock_data()
