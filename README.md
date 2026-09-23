# Stock Data Sync (Yahoo Finance) 📈

An automated pipeline to fetch Taiwan stock market data from Yahoo Finance and commit it back to this repository using GitHub Actions.

## 🚀 How it works
1. **Fetch**: A Python script uses `yfinance` to download OHLCV data for specified symbols.
    - Local execution: `./.venv/bin/python fetch_yahoo_data.py`
2. **Automate**: A scheduled [GitHub Action](https://github.com/features/actions) runs every day at market close.
3. **Store**: The fetched `.csv` files are automatically committed to the `data/` directory in this repo.

## 🛠️ Setup & Usage
### Local Execution
Ensure you have a virtual environment set up:
```bash
cd .venv/bin
./python ../fetch_yahoo_data.py
```

### Automated Sync Configuration
This repository is ready for GitHub Actions. Once pushed, it will run on a schedule defined in `.github/workflows/sync.yml`.

## 📊 Data Format
Files are stored as `{symbol}_{date}.csv` inside the `data/` folder with columns like Date, Open, High, Low, Close, Volume.