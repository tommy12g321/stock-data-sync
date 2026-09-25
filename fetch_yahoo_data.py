#!/usr/bin/env python3
"""Fetch Yahoo Finance OHLCV data and store one stable CSV per stock.

- Symbol list: symbols.txt (one per line, # = comment), fallback to DEFAULT_SYMBOLS
- Output: data/<SYMBOL>.csv (e.g. data/2330_TW.csv) — same file updated daily,
  new rows merged into existing history (no per-day file proliferation)
- Retries with backoff for transient network / rate-limit errors
"""
import argparse
import os
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_SYMBOLS = ["2330.TW", "2317.TW", "2454.TW"]


def load_symbols(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            syms = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        if syms:
            return syms
    return DEFAULT_SYMBOLS


def fetch_with_retry(symbol, start, end, retries=3):
    for attempt in range(1, retries + 1):
        try:
            df = yf.Ticker(symbol).history(start=start, end=end)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            print(f"  第 {attempt}/{retries} 次失敗: {e}")
        if attempt < retries:
            time.sleep(2 * attempt)
    return None


def merge_history(filepath, new_df):
    """Append new rows to existing CSV, dedupe by date, keep latest values."""
    if not os.path.exists(filepath):
        return new_df
    old = pd.read_csv(filepath)
    common = [c for c in new_df.columns if c in old.columns]
    merged = pd.concat([old[common], new_df[common]], ignore_index=True)
    return merged.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)


def fetch_stock_data(symbol, days=30):
    start = datetime.now() - timedelta(days=days)
    end = datetime.now()
    print(f"正在抓取 {symbol} (最近 {days} 天)...")

    df = fetch_with_retry(symbol, start, end)
    if df is None:
        print(f"  失敗: {symbol} 無資料")
        return False

    df = df.reset_index()
    df.columns = [c.replace(" ", "_").lower() for c in df.columns]

    # Stable filename per stock (2330_TW.csv) — true sync semantics
    filepath = os.path.join(DATA_DIR, f"{symbol.replace('.', '_')}.csv")
    os.makedirs(DATA_DIR, exist_ok=True)

    df = merge_history(filepath, df)
    df.to_csv(filepath, index=False)
    print(f"  OK: {len(df)} 筆 -> {filepath}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Fetch Yahoo Finance data for TW stocks")
    ap.add_argument("--days", type=int, default=30, help="回看天數 (預設 30)")
    ap.add_argument("--symbols", default=os.path.join(BASE_DIR, "symbols.txt"), help="股票清單檔")
    args = ap.parse_args()

    symbols = load_symbols(args.symbols)
    print(f"共 {len(symbols)} 檔股票: {', '.join(symbols)}")

    ok = [s for s in symbols if fetch_stock_data(s, args.days)]
    print(f"完成: {len(ok)}/{len(symbols)} 成功")
    if not ok:
        sys.exit(1)  # fail the run (and the Action) when everything failed


if __name__ == "__main__":
    main()
