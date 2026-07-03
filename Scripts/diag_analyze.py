#!/usr/bin/env python3
"""
diag_analyze.py — วิเคราะห์ per-basket diagnostic CSV จาก TrellisDiag.mqh (TRELLIS-DIAG)

ตอบ 3 คำถามชี้ขาด (spec ที่วินอนุมัติ 2026-07-03):
  Q1  basket ที่แพ้เคยกลับมาใกล้ breakeven ไหม?  -> MFE distribution ของฝั่งแพ้
  Q2  entry ที่ชนะ vs แพ้ ต่างกันที่ context ไหน?  -> breakdown ตาม hour / ER / dev_atr / levels
  Q3  loss รวมมาจาก exit reason ไหนเท่าไหร่?      -> breakdown ต่อ exit_reason

ตัวเลขทุกตัวมาจาก script นี้ (ตรวจซ้ำได้) — LLM ห้ามพิมพ์ตัวเลขสรุปเอง

Usage:
  python diag_analyze.py <path/to/Trellis_diag_*.csv>
"""
import csv
import sys
from pathlib import Path

import numpy as np

# Windows console default ไม่ใช่ UTF-8 -> ข้อความไทยเพี้ยน
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPECTED_COLS = [
    "basket_id", "open_time", "close_time", "age_bars", "dir",
    "er_entry", "dev_atr", "atr_entry", "spread_pts", "hour",
    "levels_max", "lots_total", "mfe_usd", "mfe_age", "mae_usd", "mae_age",
    "realized_usd", "exit_reason", "balance_after",
]

KNOWN_REASONS = {
    "basket-TP", "time-stop", "hard-stop", "day-stop",
    "max-total-DD", "margin-level", "test-end",
    "depth-falsify",  # TRELLIS-007 E1
    "eod", "sl-exit",  # Trellis v4 (Dual Asian BO)
}  # halt-escalate:* ตรวจแยกด้วย prefix


def load(path: Path):
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED_COLS:
            sys.exit(f"FAIL-LOUD: header ไม่ตรง spec\n  expect: {EXPECTED_COLS}\n  got:    {reader.fieldnames}")
        for i, r in enumerate(reader, start=2):
            try:
                rows.append({
                    "id": int(r["basket_id"]),
                    "open_time": r["open_time"],
                    "age": int(r["age_bars"]),
                    "dir": int(r["dir"]),
                    "er": float(r["er_entry"]),
                    "dev_atr": float(r["dev_atr"]),
                    "atr": float(r["atr_entry"]),
                    "spread": int(r["spread_pts"]),
                    "hour": int(r["hour"]),
                    "levels": int(r["levels_max"]),
                    "lots": float(r["lots_total"]),
                    "mfe": float(r["mfe_usd"]),
                    "mfe_age": int(r["mfe_age"]),
                    "mae": float(r["mae_usd"]),
                    "mae_age": int(r["mae_age"]),
                    "pnl": float(r["realized_usd"]),
                    "reason": r["exit_reason"],
                    "bal": float(r["balance_after"]),
                })
            except (ValueError, KeyError) as e:
                sys.exit(f"FAIL-LOUD: parse ไม่ได้ที่บรรทัด {i}: {e}\n  row={r}")
    if not rows:
        sys.exit("FAIL-LOUD: ไฟล์ไม่มีข้อมูล basket เลย")
    # basket_id ต้องต่อเนื่อง 1..N — ถ้าหลุด = มี row หายเงียบ
    ids = [r["id"] for r in rows]
    if ids != list(range(1, len(ids) + 1)):
        missing = sorted(set(range(1, max(ids) + 1)) - set(ids))
        print(f"WARN: basket_id ไม่ต่อเนื่อง — row หาย {len(missing)} ตัว: {missing[:20]}")
    # exit_reason แปลกปลอม = fail loud
    unknown = {r["reason"] for r in rows
               if r["reason"] not in KNOWN_REASONS and not r["reason"].startswith("halt-escalate:")}
    if unknown:
        sys.exit(f"FAIL-LOUD: exit_reason ไม่รู้จัก: {unknown}")
    return rows


def arr(rows, key):
    return np.array([r[key] for r in rows], dtype=float)


def fmt_line(label, sub, n_total):
    pnl = arr(sub, "pnl")
    wins = int((pnl > 0).sum())
    wr = 100.0 * wins / len(sub) if sub else 0.0
    return (f"  {label:<24} n={len(sub):>5} ({100.0*len(sub)/n_total:>5.1f}%)"
            f"  net={pnl.sum():>+10.2f}  avg={pnl.mean():>+8.2f}"
            f"  winrate={wr:>5.1f}%")


def bucket_report(title, rows, key, edges):
    print(f"\n== {title} ==")
    n_total = len(rows)
    for lo, hi in zip(edges[:-1], edges[1:]):
        sub = [r for r in rows if lo <= r[key] < hi]
        if sub:
            print(fmt_line(f"[{lo:g}, {hi:g})", sub, n_total))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    if not path.exists():
        sys.exit(f"FAIL-LOUD: ไม่พบไฟล์ {path}")
    rows = load(path)
    n = len(rows)
    pnl = arr(rows, "pnl")
    wins = [r for r in rows if r["pnl"] > 0]
    losses = [r for r in rows if r["pnl"] <= 0]

    print(f"# TRELLIS-DIAG analysis: {path.name}  (baskets={n})")

    # ---------- Overall ----------
    print("\n== Overall ==")
    print(f"  net P&L          {pnl.sum():+.2f}")
    print(f"  wins/losses      {len(wins)}/{len(losses)}  winrate={100.0*len(wins)/n:.1f}%")
    if wins:
        print(f"  avg win          {arr(wins,'pnl').mean():+.2f}   max {arr(wins,'pnl').max():+.2f}")
    if losses:
        print(f"  avg loss         {arr(losses,'pnl').mean():+.2f}   worst {arr(losses,'pnl').min():+.2f}")
    if wins and losses:
        aw, al = arr(wins, "pnl").mean(), -arr(losses, "pnl").mean()
        p = len(wins) / n
        print(f"  win$/loss$       {aw/al:.3f}   expectancy/basket = {p*aw-(1-p)*al:+.3f}")
        print(f"  breakeven winrate ต้องการ {100.0*al/(aw+al):.1f}%  (จริง {100.0*p:.1f}%)")
    bal = arr(rows, "bal")
    peak = np.maximum.accumulate(bal)
    dd = (peak - bal) / peak * 100.0
    print(f"  balance สุดท้าย  {bal[-1]:.2f}   max balance-DD {dd.max():.1f}%")

    # ---------- Q3: per exit reason ----------
    print("\n== Q3: breakdown ต่อ exit_reason ==")
    reasons = sorted({r["reason"] for r in rows})
    for reason in reasons:
        sub = [r for r in rows if r["reason"] == reason]
        age = arr(sub, "age")
        lv = arr(sub, "levels")
        print(fmt_line(reason, sub, n) + f"  avg_age={age.mean():>6.1f}bars  avg_levels={lv.mean():.2f}")

    # ---------- Q1: losers — เคยใกล้ breakeven ไหม ----------
    print("\n== Q1: MFE ของ basket ที่แพ้ (เคยกลับมาใกล้ 0 ไหม) ==")
    if losses:
        lm = arr(losses, "mfe")
        for th in (0.0, -0.5, -1.0, -2.0, -5.0):
            pct = 100.0 * (lm >= th).sum() / len(losses)
            print(f"  MFE >= {th:>5.1f} USD : {pct:>5.1f}%  ({int((lm>=th).sum())}/{len(losses)})")
        print(f"  median MFE (losers)      {np.median(lm):+.2f}")
        print(f"  median MFE age           {np.median(arr(losses,'mfe_age')):.0f} bars"
              f"  (median lifetime {np.median(arr(losses,'age')):.0f} bars)")
        print(f"  median loss              {np.median(arr(losses,'pnl')):+.2f}")
        # เงินที่ 'กู้คืนได้ในทางทฤษฎี' ถ้า exit ที่ MFE แทน (upper bound ไม่ใช่คำสัญญา)
        recover = (lm - arr(losses, "pnl")).sum()
        print(f"  upper-bound recovery ถ้า exit ที่ MFE: {recover:+.2f} USD (เพดานทฤษฎี)")
    else:
        print("  (ไม่มี basket แพ้)")

    # ---------- Q2: context ----------
    bucket_report("Q2: ตามชั่วโมง server (hour)", rows, "hour", list(range(0, 25)))
    bucket_report("Q2: ตาม ER bucket", rows, "er", [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 1.01])
    bucket_report("Q2: ตาม dev_atr bucket", rows, "dev_atr", [0.0, 1.0, 1.25, 1.5, 2.0, 3.0, 99.0])
    bucket_report("Q2: ตาม levels_max", rows, "levels", list(range(1, 12)))
    bucket_report("Q2: ตามทิศ (dir)", rows, "dir", [-1, 0, 2])

    print("\n(ทุกตัวเลขมาจาก script นี้ — rerun ซ้ำได้ด้วยไฟล์ CSV เดิม)")


if __name__ == "__main__":
    main()
