#!/usr/bin/env python3
"""Fetch Yahoo Finance daily OHLCV for the full TW stock list (symbols.txt).

- One stable CSV per stock: data/<CODE>_TW.csv (e.g. data/2330_TW.csv)
- Raw (unadjusted) prices as displayed on the day; columns: date,open,high,low,close,volume
- Backfill from START_DATE (2020-01-01); afterwards only the missing tail is fetched:
    start = last_date - 3d buffer, UNLESS the file's min_date is after START_DATE+14d
    (i.e. history is still partial — a mid-backfill file or pre-IPO IPO'd later —
    then refetch from START_DATE; dedupe keeps the merge correct either way).
- Retries with backoff per symbol; partial failures are OK (next run refetches
  whatever is stale), all-failures fail the run.
"""
import argparse
import os
import random
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
START_DATE = "2020-01-01"          # 資料庫起算日
PARTIAL_EPS = timedelta(days=14)   # min_date 比 START_DATE 晚超過這值 → 視為未回填完
TAIL_BUFFER = timedelta(days=3)    # 增量重疊緩衝(去重會處理)
SLEEP_RANGE = (0.3, 1.3)         # 每檔間隔(秒,隨機)——避免定時節奏被 Yahoo 辨識/限流
KEEP_COLS = ["date", "open", "high", "low", "close", "volume"]


def load_symbols(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            syms = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        if syms:
            return syms
    return []


def fetch_with_retry(symbol, start, end, retries=3):
    for attempt in range(1, retries + 1):
        try:
            df = yf.Ticker(symbol).history(start=start, end=end, interval="1d", auto_adjust=False)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            print(f"  第 {attempt}/{retries} 次失敗: {e}")
        if attempt < retries:
            time.sleep(2 * attempt)
    return None


def _to_date_str(val):
    """Map any date-like value (naive/tz-aware Timestamp, or legacy
    'YYYY-MM-DD HH:MM:SS+08:00' string) to a plain 'YYYY-MM-DD' string,
    keeping the value's own calendar date (the TW trading date as displayed)."""
    try:
        return pd.Timestamp(val).strftime("%Y-%m-%d")
    except Exception:
        return None


def _norm_date(s):
    """Normalize a date column to plain 'YYYY-MM-DD' strings so legacy and new
    formats can be concatenated/deduped/sorted together (ISO strings sort
    chronologically)."""
    return s.map(_to_date_str)


def merge_history(filepath, new_df):
    """Append new rows to existing CSV, dedupe by date, keep latest values."""
    if not os.path.exists(filepath):
        return new_df
    old = pd.read_csv(filepath)
    common = [c for c in new_df.columns if c in old.columns]
    old, new = old[common], new_df[common]
    if "date" in old.columns:
        old["date"] = _norm_date(old["date"])
    if "date" in new.columns:
        new["date"] = _norm_date(new["date"])
    merged = pd.concat([old, new], ignore_index=True)
    merged = merged.dropna(subset=["date"])
    return merged.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)


def pick_start(filepath):
    """Backfill-from-2020 until the file covers the full range, then incremental tail."""
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    if os.path.exists(filepath):
        try:
            old = pd.read_csv(filepath)
            if not old.empty and "date" in old.columns:
                d = pd.to_datetime(_norm_date(old["date"]), errors="coerce").dropna()
                if not d.empty:
                    min_d, max_d = d.min(), d.max()
                    if min_d > start + PARTIAL_EPS:
                        print(f"  歷史不完整(min={min_d.date()}),從 {START_DATE} 重新回填")
                        return start.strftime("%Y-%m-%d")
                    return max((max_d - TAIL_BUFFER).date(), start.date()).strftime("%Y-%m-%d")
        except Exception:
            pass
    return start.strftime("%Y-%m-%d")


def fetch_stock_data(symbol):
    filepath = os.path.join(DATA_DIR, f"{symbol.replace('.', '_')}.csv")
    start = pick_start(filepath)
    end = datetime.now().strftime("%Y-%m-%d")
    df = fetch_with_retry(symbol, start, end)
    if df is None:
        print(f"  失敗: {symbol} 無資料")
        return False

    df = df.reset_index()
    df.columns = [c.replace(" ", "_").lower() for c in df.columns]
    os.makedirs(DATA_DIR, exist_ok=True)

    df = df[[c for c in KEEP_COLS if c in df.columns]]
    if "date" in df.columns:
        df["date"] = _norm_date(df["date"])   # 統一為 YYYY-MM-DD 字串(含新建檔路徑)
    df = merge_history(filepath, df)
    df.to_csv(filepath, index=False)
    print(f"  OK: {len(df)} 筆 ({df['date'].iloc[0]}~{df['date'].iloc[-1]}) -> {os.path.basename(filepath)}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Fetch Yahoo Finance daily OHLCV for the TW stock list")
    ap.add_argument("--symbols", default=os.path.join(BASE_DIR, "symbols.txt"), help="股票清單檔")
    ap.add_argument("--limit", type=int, default=0, help="只抓前 N 檔(0=全部),測試用")
    args = ap.parse_args()

    symbols = load_symbols(args.symbols)
    if args.limit:
        symbols = symbols[: args.limit]
    print(f"共 {len(symbols)} 檔股票,起算日 {START_DATE}")

    ok = fail = 0
    for i, s in enumerate(symbols, 1):
        if fetch_stock_data(s):
            ok += 1
        else:
            fail += 1
        if i % 100 == 0:
            print(f"進度 {i}/{len(symbols)} (成功 {ok} / 失敗 {fail})")
        time.sleep(random.uniform(*SLEEP_RANGE))

    print(f"完成: 成功 {ok}/{len(symbols)},失敗 {fail}")
    if ok == 0:
        sys.exit(1)  # 全失敗才讓 Action 紅(部分失敗明天重抓)


if __name__ == "__main__":
    main()
