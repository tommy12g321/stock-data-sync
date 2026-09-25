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
./.venv/bin/python fetch_yahoo_data.py              # 預設 30 天
./.venv/bin/python fetch_yahoo_data.py --days 90    # 回看 90 天
```
Stock list lives in `symbols.txt` (one Yahoo symbol per line).

### Automated Sync Configuration
This repository is ready for GitHub Actions. Once pushed, it will run on a schedule defined in `.github/workflows/sync.yml`.

## 📊 Data Format
Files are stored as one stable `{SYMBOL}.csv` per stock (e.g. `2330_TW.csv`) inside `data/`, merged with prior history (deduped by date). Columns: date, open, high, low, close, volume, dividends, stock_splits.