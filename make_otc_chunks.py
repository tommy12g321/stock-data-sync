#!/usr/bin/env python3
"""Split the OTC (上櫃 / TPEx) symbols in symbols.txt into balanced chunks.

Outputs a JSON array of N strings to stdout, each string being a
comma-separated list of OTC symbols — ready to feed a GitHub Actions matrix:
  ["1240,1101,1301", "2401,2413", ...]

Routing uses twstock's official code database (data_source == 'tpex'), which is
the authoritative split between 上市(TWSE) and 上櫃(TPEx) — not the code prefix.
"""
import argparse
import json
import os

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
    ap = argparse.ArgumentParser(description="Split OTC symbols into balanced chunks")
    ap.add_argument("--symbols", default=os.path.join(BASE_DIR, "symbols.txt"))
    ap.add_argument("--n", type=int, default=12, help="chunk 數量")
    args = ap.parse_args()

    otc = sorted(load_otc(args.symbols))
    n = max(1, args.n)
    # 均分:前 (len%n) 塊多一檔;輸出 [{i, s}, ...] 讓 matrix 有唯一 index 可做 artifact 名
    chunks = []
    base, extra = divmod(len(otc), n)
    i = 0
    for k in range(n):
        size = base + (1 if k < extra else 0)
        if size == 0:
            break
        chunk = otc[i : i + size]
        i += size
        chunks.append({"i": k, "s": ",".join(chunk)})

    import sys
    print(f"OTC 共 {len(otc)} 檔 -> {len(chunks)} 塊(每塊約 {len(otc)//max(1,n)} 檔)", file=sys.stderr)
    print(json.dumps(chunks))


if __name__ == "__main__":
    main()
