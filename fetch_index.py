#!/usr/bin/env python3
"""Fetch Yahoo Finance ^TWII (台指/加權指數) daily OHLCV.

- Single CSV: out/TWII.csv — same format as the per-stock files:
  date,open,high,low,close,volume (raw values as displayed, dates YYYY-MM-DD)
- Full history from START_DATE each run (one symbol = one request, so no
  incremental-tail logic needed); the commit job overwrites data/TWII.csv,
  which is idempotent.
"""
import argparse
import os
import time

import pandas as pd
import yfinance as yf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
START_DATE = "2020-01-01"           # 與個股檔同起算日
KEEP_COLS = ["date", "open", "high", "low", "close", "volume"]


def fetch_with_retry(symbol, start, retries=3):
    for attempt in range(1, retries + 1):
        try:
            df = yf.Ticker(symbol).history(start=start, interval="1d", auto_adjust=False)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            print(f"  第 {attempt}/{retries} 次失敗: {e}")
        if attempt < retries:
            time.sleep(2 * attempt)
    return None


def main():
    ap = argparse.ArgumentParser(description="Fetch ^TWII daily OHLCV")
    ap.add_argument("--outdir", default=os.path.join(BASE_DIR, "out"))
    args = ap.parse_args()

    df = fetch_with_retry("^TWII", START_DATE)
    if df is None:
        raise SystemExit("failed to fetch ^TWII")

    out = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    out = out.rename(columns=str.lower)
    # 保留該根 K 顯示的日曆日(與個股檔一致)
    dates = pd.to_datetime(out.index).strftime("%Y-%m-%d")
    out.insert(0, "date", dates)
    out = out[KEEP_COLS].dropna(subset=["close"]).sort_values("date").reset_index(drop=True)
    out["volume"] = out["volume"].astype("int64")

    os.makedirs(args.outdir, exist_ok=True)
    path = os.path.join(args.outdir, "TWII.csv")
    out.to_csv(path, index=False)
    print(f"wrote {len(out)} rows -> {path} ({out['date'].iloc[0]} ~ {out['date'].iloc[-1]})")


if __name__ == "__main__":
    main()
