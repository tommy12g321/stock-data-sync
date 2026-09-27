#!/usr/bin/env python3
"""Generate the full TW listed/OTC stock symbol list into symbols.txt.

Source: twstock's built-in official code list (no network needed, works anywhere).
Scope: 上市股票 + 上櫃股票 + 特別股 + 創新板 (ETF / 權證 / ETN / TDR excluded).
Re-run any time — new IPOs are picked up automatically, output is idempotent.
"""
import os

import twstock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "symbols.txt")
KEEP_TYPES = {"股票", "特別股", "創新板"}


def main():
    stocks = sorted(
        (v for v in twstock.codes.values() if v.type in KEEP_TYPES),
        key=lambda v: v.code,
    )
    lines = [
        "# 全股票清單(上市+上櫃+特別股+創新板)— 由 build_symbols.py 自動產生,勿手改",
        f"# 共 {len(stocks)} 檔;不含 ETF/權證/ETN",
    ]
    lines += [f"{v.code}.TW" for v in stocks]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(stocks)} 檔 -> {OUT}")


if __name__ == "__main__":
    main()
