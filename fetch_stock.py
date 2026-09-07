import yfinance as yf
import pandas as pd  # 已修正此處
import datetime
import os

def fetch_tw_stock_data():
    tickers = ["2330.TW", "2317.TW", "2454.TW", "2388.TW", "2354.TW"]
    file_name = "stock_data.csv"
    log_file = "last_run_log.txt" 
    
    print(f"Start: {datetime.datetime.now()}")
    print(f"Targets: {tickers}")

    try:
        all_data = []

        for ticker in tickers:
            print(f"  --> Fetching {ticker}...")
            # 為了穩定性，使用 5 天內、5 分鐘間隔的數據
            data = yf.download(ticker, period="5y", interval="1d", progress=False)
            
            if data.empty:
                print(f"  ⚠️ Warning: {ticker} failed.")
                continue
            
            data['Ticker'] = ticker
            data = data.reset_index()
            all_data.append(data)
            print(f"  ✅ {ticker} Success.")

        if not all_data:
            print("❌ Error: No data fetched.")
            return

        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(file_name, index=False)
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Last update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
        print(f"✅ Saved to {file_name}. Total rows: {len(final_df)}")
        print("✨ Done.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    fetch_tw_stock_data()
