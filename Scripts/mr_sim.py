#!/usr/bin/env python3
"""
mr_sim.py — Phase B ขั้น C: bar-level sim ของ "k=0 pause-fade + asymmetric exit"
(single position 0.01 lot · ไม่มี grid · M1 XAUUSD)

หลัก PESSIMISTIC (กัน sim หลอกตา — Doctrine #5):
- BUY เข้าที่ ask = open + spread(bar) · ออกที่ bid · SELL กลับกัน
- slippage เข้า 0.02 / ออกที่ stop 0.03
- แท่งเดียวโดนทั้ง stop และ favorable → นับ stop ก่อนเสมอ
- gap ทะลุ stop → fill ที่ open ของแท่ง (แย่กว่า stop)
- trail เลื่อนจาก close ของแท่งที่ปิดแล้วเท่านั้น (ไม่มี intrabar trail)

Entry (ตรรกะเดียวกับ v2 + k=0): new bar · ER(100)<0.35 · |close-EMA50| >= 1×ATR(M5,14)
· consec_against == 0 · spread <= 200pt · one position at a time
Exit: stop = S×ATR · trail: หลังกำไร A×ATR → stop = extreme(close) ∓ D×ATR · time-stop T bars
Usage:
  python mr_sim.py is        # grid search บน IS 2023-2024
  python mr_sim.py oos S A D T   # รัน config เดียวบน OOS 2022 + 2025-26 (เปิดครั้งเดียว!)
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from entry_platform import load_m1, ema, er_kaufman, build_m5, atr_variants

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PT = 0.01          # 1 point = $0.01 price
LOT_USD = 1.0      # 0.01 lot gold: $1 P&L ต่อ $1 move
SLIP_IN, SLIP_STOP = 0.02, 0.03
MAX_SPREAD_PT = 200
ER_MAX, DEV_K = 0.35, 1.0


def prep(years):
    m1 = load_m1(years)
    c, h, l, o, sp = m1["c"], m1["h"], m1["l"], m1["o"], m1["sp"]
    e50 = ema(c, 50)
    er = er_kaufman(c, 100)
    m5 = build_m5(m1)
    atr_sma, _ = atr_variants(m5)
    # map แต่ละ M1 bar -> ATR ของ M5 bar ที่ "ปิดแล้ว" ล่าสุด
    tmin = m1["t"].astype("datetime64[m]").astype(np.int64)
    m5_int = m5["t"].astype(np.int64)
    k_form = np.searchsorted(m5_int, tmin - (tmin % 5), side="left")
    atr_at = np.where(k_form >= 1, atr_sma[np.maximum(k_form - 1, 0)], np.nan)
    # consecutive runs ของ close (จบที่ bar j)
    dn = np.zeros(len(c), dtype=int); up = np.zeros(len(c), dtype=int)
    for j in range(1, len(c)):
        if c[j] < c[j - 1]: dn[j] = dn[j - 1] + 1
        elif c[j] > c[j - 1]: up[j] = up[j - 1] + 1
    return m1, e50, er, atr_at, dn, up


def run(m1, e50, er, atr_at, dn, up, S, A, D, T, spread_mult=1.0, start=12000):
    c, h, l, o, sp, t = m1["c"], m1["h"], m1["l"], m1["o"], m1["sp"], m1["t"]
    n = len(c)
    trades = []          # (time, dir, entry, exit, pnl, bars, reason)
    pos = None
    for i in range(start, n):
        if pos is not None:
            d, ent, stop, best, bars, atr0 = pos
            bars += 1
            # 1) stop ก่อนเสมอ (pessimistic)
            hit = (l[i] <= stop) if d == 1 else (h[i] >= stop)
            if hit:
                px = min(stop, o[i]) if d == 1 else max(stop, o[i])
                px -= SLIP_STOP * d
                exit_px = px if d == 1 else px + sp[i] * PT * spread_mult  # SELL ออกที่ ask
                pnl = (exit_px - ent) * d * LOT_USD if d == 1 else (ent - exit_px) * LOT_USD
                trades.append((t[i], d, ent, exit_px, pnl, bars, "stop"))
                pos = None
                continue
            # 2) time-stop ที่ close
            if bars >= T:
                exit_px = c[i] if d == 1 else c[i] + sp[i] * PT * spread_mult
                pnl = (exit_px - ent) * LOT_USD if d == 1 else (ent - exit_px) * LOT_USD
                trades.append((t[i], d, ent, exit_px, pnl, bars, "time"))
                pos = None
                continue
            # 3) trail จาก close แท่งที่จบ
            best = max(best, c[i]) if d == 1 else min(best, c[i])
            fav = (best - ent) if d == 1 else (ent - best)
            if fav >= A * atr0:
                new_stop = best - D * atr0 if d == 1 else best + D * atr0
                stop = max(stop, new_stop) if d == 1 else min(stop, new_stop)
            pos = (d, ent, stop, best, bars, atr0)
            continue
        # entry decision จาก closed bar j = i-1
        j = i - 1
        a = atr_at[i]
        if not np.isfinite(a) or a <= 0 or not np.isfinite(er[j]):
            continue
        if sp[j] > MAX_SPREAD_PT or er[j] >= ER_MAX:
            continue
        dev = c[j] - e50[j]
        if abs(dev) < DEV_K * a:
            continue
        d = 1 if dev < 0 else -1
        if (dn[j] if d == 1 else up[j]) != 0:      # k=0: impulse หยุดแล้วเท่านั้น
            continue
        ent = o[i] + (sp[i] * PT * spread_mult if d == 1 else 0.0) + SLIP_IN * d
        stop = ent - S * a * d
        pos = (d, ent, stop, ent, 0, a)
    return trades


def stats(trades, label=""):
    if not trades:
        return f"{label}: no trades"
    p = np.array([x[4] for x in trades])
    w = p[p > 0]; lo = p[p <= 0]
    eq = np.cumsum(p); peak = np.maximum.accumulate(eq)
    dd = (peak - eq).max()
    pf = w.sum() / max(-lo.sum(), 1e-9)
    yrs = {}
    for x in trades:
        y = str(x[0])[:4]
        yrs[y] = yrs.get(y, 0.0) + x[4]
    ystr = " ".join(f"{y}:{v:+.0f}" for y, v in sorted(yrs.items()))
    return (f"{label} n={len(p)} net={p.sum():+8.1f} wr={100*len(w)/len(p):4.1f}% "
            f"avgW={w.mean() if len(w) else 0:+.2f} avgL={lo.mean() if len(lo) else 0:+.2f} "
            f"PF={pf:.2f} maxDD={dd:.1f} | {ystr}")


def quarters(trades):
    out = {}
    for x in trades:
        q = f"{str(x[0])[:4]}Q{(int(str(x[0])[5:7]) - 1)//3 + 1}"
        out.setdefault(q, []).append(x[4])
    return {q: (len(v), float(np.sum(v))) for q, v in sorted(out.items())}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "is"
    if mode == "is":
        data = prep([2022, 2023, 2024])
        print("== IS grid search (2023-2024) — trail configs ==")
        for S in (1.5, 2.0, 2.5, 3.0):
            for A in (1.0, 1.5, 2.0):
                for D in (1.0, 1.5):
                    for T in (60, 120):
                        tr = run(*data, S, A, D, T)
                        print(stats(tr, f"S{S} A{A} D{D} T{T:>3}"))
    elif mode == "oos":
        S, A, D, T = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
        print(f"== TRUE OOS (2022, 2025-2026) — config S{S} A{A} D{D} T{T} — เปิดครั้งเดียว ==")
        d1 = prep([2021, 2022])
        tr1 = run(*d1, S, A, D, T)
        print(stats(tr1, "2022    "))
        print("  ", quarters(tr1))
        d2 = prep([2024, 2025, 2026])
        tr2 = run(*d2, S, A, D, T)
        print(stats(tr2, "2025-26 "))
        print("  ", quarters(tr2))
        print("\n-- cost stress spread x1.5 --")
        print(stats(run(*d1, S, A, D, T, spread_mult=1.5), "2022 x1.5"))
        print(stats(run(*d2, S, A, D, T, spread_mult=1.5), "2025-26 x1.5"))
