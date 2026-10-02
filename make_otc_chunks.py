#!/usr/bin/env python3
"""Split the OTC (上櫃 / TPEx) symbols that still need backfill into balanced chunks.

Outputs a JSON array of {i, s} objects to stdout:
  i = chunk index (so each matrix job gets a unique artifact name otc-<i>)
  s = comma-separated symbol list for that chunk

Only OTC stocks that do NOT yet have a data/<CODE>_TW.csv are emitted. The
per-stock TPEx fetch is all-or-nothing (the file is written only after all
months succeed), so "no file" is exactly "needs backfill" — no content check
needed. Capped at --max per run so each chunk finishes well inside the
~6h job-time cap (the shared TPEx throughput bounds total wall-clock, not
parallelism), and the full 881-stock backfill converges over a couple of runs.
Routing uses twstock's official code database (data_source == 'tpex'), the
authoritative 上市/上櫃 split — not the code prefix.
"""
import argparse
import json
import os
import sys

import twstock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_otc(path):
    if not os.path.exists(path):
        return []
    otc = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            code = ln[:-3] if ln.endswith(".TW") else ln
            c = twstock.codes.get(code)
            if c is not None and c.data_source == "tpex":
                otc.append(ln)
    return otc


def main():
    ap = argparse.ArgumentParser(description="Chunk OTC symbols that still need backfill")
    ap.add_argument("--symbols", default=os.path.join(BASE_DIR, "symbols.txt"))
    ap.add_argument("--data", default=os.path.join(BASE_DIR, "data"))
    ap.add_argument("--n", type=int, default=12, help="chunk 數量")
    ap.add_argument("--max", type=int, default=480, help="單 run 最多回補幾檔(0=不限)")
    args = ap.parse_args()

    # 只挑「還沒檔」的上櫃股;抓到的 chunk 檔是全量(atomic),有檔=已回補完
    todo = [
        sym for sym in sorted(load_otc(args.symbols))
        if not os.path.exists(os.path.join(args.data,
                                           (sym[:-3] if sym.endswith(".TW") else sym) + "_TW.csv"))
    ]
    if args.max and len(todo) > args.max:
        todo = todo[: args.max]

    n = max(1, args.n)
    base, extra = divmod(len(todo), n)
    chunks, i = [], 0
    for k in range(n):
        size = base + (1 if k < extra else 0)
        if size == 0:
            break
        chunk = todo[i : i + size]
        i += size
        chunks.append({"i": k, "s": ",".join(chunk)})

    print(f"OTC 待回補 {len(todo)} 檔 -> {len(chunks)} 塊(每塊約 {len(todo)//max(1,n)} 檔)", file=sys.stderr)
    print(json.dumps(chunks))


if __name__ == "__main__":
    main()
