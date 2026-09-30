#!/usr/bin/env python3
"""Fetch OTC (上櫃 / TPEx) daily OHLCV from the official TPEx source.

Yahoo Finance does not carry TPEx (上櫃) stocks, so they come from the exchange:
  http://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock  (one month per request)

- One stable CSV per stock: outdir/<CODE>_TW.csv (e.g. out/1240_TW.csv)
- Columns: date,open,high,low,close,volume  (same shape as the Yahoo fetcher)
- Backfill from START_DATE month; afterwards only the recent tail is fetched.
- A month that returns empty after retries is tolerated (partial OK — the next
  run refetches the tail and any stock whose CSV is incomplete refetches from
  START_DATE). Intended to be run per-chunk (--symbols) in parallel.
"""
import argparse
import os
import random
import sys
import time
from datetime import datetime

import pandas as pd

from twstock.stock import TPEXFetcher

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
START_DATE = "2020-01-01"          # 資料庫起算日(與 Yahoo 抓取一致)
PARTIAL_EPS_DAYS = 14              # min_date 比起算日晚超過此值 → 視為未回填完
TAIL_DAYS = 45                     # 增量時回補的尾巴長度(日)
MONTH_SLEEP_RANGE = (0.15, 0.4)    # 每月請求間隔(秒)——禮貌性節流
STOCK_SLEEP_RANGE = (0.3, 0.9)     # 每檔間隔(秒)
MONTH_RETRIES = 2                  # 單月重試次數(僅防暫現失敗;空月通常=IPO前,不必重試)
KEEP_COLS = ["date", "open", "high", "low", "close", "volume"]

_TPEX = TPEXFetcher()


def month_range(start_dt, end_dt):
    """Inclusive list of (year, month) from start_dt to end_dt."""
    out = []
    y, m = start_dt.year, start_dt.month
    while (y, m) <= (end_dt.year, end_dt.month):
        out.append((y, m))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def fetch_month(year, month, code):
    """Fetch one month for a stock; retry transient empties. Returns row list."""
    for attempt in range(1, MONTH_RETRIES + 1):
        data = _TPEX.fetch(year, month, code).get("data", [])
        if data:
            return data
        if attempt < MONTH_RETRIES:
            time.sleep(1.5 * attempt)  # 退避
    return []


def plan_start(existing_path, start):
    """Decide the backfill start month: full refetch if incomplete, else tail."""
    if os.path.exists(existing_path):
        try:
            old = pd.read_csv(existing_path, parse_dates=["date"])
            if not old.empty:
                min_d, max_d = old["date"].min(), old["date"].max()
                now = datetime.now()
                if min_d <= start + pd.Timedelta(days=PARTIAL_EPS_DAYS):
                    if (now - max_d).days <= TAIL_DAYS:
                        return max((max_d - pd.Timedelta(days=7)).to_pydatetime(), start)
                    return start  # 有洞 → 整段重抓(會重疊,去重處理)
        except Exception:
            pass
    return start


def fetch_stock(sym, existing_path, outdir):
    code = sym[:-3] if sym.endswith(".TW") else sym
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    start = plan_start(existing_path, start)
    now = datetime.now()

    # 由最近月份往前抓;遇到(重試後仍)空月即視為 IPO 前,停止——省掉大量 IPO 前請求
    rows = []
    for (y, m) in reversed(month_range(start, now)):
        data = fetch_month(y, m, code)
        if not data:
            break
        rows.extend(data)
        time.sleep(random.uniform(*MONTH_SLEEP_RANGE))

    if not rows:
        print(f"  失敗: {sym} 無資料")
        return False

    df = pd.DataFrame(
        [
            {
                "date": r.date.strftime("%Y-%m-%d"),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.capacity,
            }
            for r in rows
        ]
    )
    df = df.dropna(subset=["date"]).drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date")

    # 併入既有歷史(若存在)
    if os.path.exists(existing_path):
        try:
            old = pd.read_csv(existing_path)
            common = [c for c in KEEP_COLS if c in old.columns and c in df.columns]
            df = pd.concat([old[common], df[common]], ignore_index=True)
            df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
        except Exception:
            pass

    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{code}_TW.csv")
    df.to_csv(out, index=False)
    print(f"  OK: {len(df)} 筆 ({df['date'].iloc[0]}~{df['date'].iloc[-1]}) -> {os.path.basename(out)}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Fetch OTC (TPEx) daily OHLCV from the official source")
    ap.add_argument("--symbols", default="", help="本 chunk 的 OTC 代號(逗號分隔, e.g. 1240,1101)")
    ap.add_argument("--data", default=os.path.join(BASE_DIR, "data"), help="既有資料目錄(合併用)")
    ap.add_argument("--outdir", default=os.path.join(BASE_DIR, "out"), help="輸出目錄")
    args = ap.parse_args()

    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if not syms:
        print("沒有要抓的 OTC 代號"); sys.exit(0)
    print(f"TPEx OTC: {len(syms)} 檔,起算 {START_DATE}")

    ok = fail = 0
    for s in syms:
        existing = os.path.join(args.data, s.replace(".", "_") + ".csv")
        if fetch_stock(s, existing, args.outdir):
            ok += 1
        else:
            fail += 1
        time.sleep(random.uniform(*STOCK_SLEEP_RANGE))

    print(f"TPEx 完成: 成功 {ok}/{len(syms)},失敗 {fail}")
    if ok == 0:
        sys.exit(1)  # 全失敗才紅(部分失敗下次補)


if __name__ == "__main__":
    main()
