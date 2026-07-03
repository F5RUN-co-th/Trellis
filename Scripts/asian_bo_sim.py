#!/usr/bin/env python3
"""
asian_bo_sim.py — Asian-High Breakout (long-only trend continuation) · M1 execution
Entry: close M1 แรกของวันที่ทะลุ Asian-high (range 01:00-07:59 server) ช่วง 08:00-19:59
       + regime filter (optional): close > EMA(2880) [~2 วัน]
Stop:  Asian-low (โครงสร้าง) แต่ไม่เกิน CAPR×range · Trail: หลังกำไร A×R → trail D×R (R=range สูง-ต่ำ Asian)
Exit:  หมดวัน (23:00) ที่ close · PESSIMISTIC fills เหมือน mr_sim (stop ก่อน, gap ที่ open, spread+slip)
Usage:
  python asian_bo_sim.py is                 # variants บน IS 2023-2024
  python asian_bo_sim.py oos <REG> <CAPR> <A> <D>   # OOS 2022 + 2025-26 ครั้งเดียว
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from entry_platform import load_m1, ema

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PT = 0.01
SLIP_IN, SLIP_STOP = 0.02, 0.03
MAX_SPREAD_PT = 200


def prep(years):
    m1 = load_m1(years)
    c = m1["c"]
    e2d = ema(c, 2880)
    tmin = m1["t"].astype("datetime64[m]").astype(np.int64)
    return m1, e2d, (tmin // 60) % 24, (tmin // 1440).astype(int)


def run(m1, e2d, hour, day, REG=True, CAPR=1.0, A=1.0, D=0.75, spread_mult=1.0, start=12000):
    c, h, l, o, sp, t = m1["c"], m1["h"], m1["l"], m1["o"], m1["sp"], m1["t"]
    n = len(c)
    trades = []
    pos = None
    cur_d = -1
    ash = asl = np.nan
    traded = set()
    for i in range(start, n):
        if day[i] != cur_d:
            cur_d = day[i]; ash = asl = np.nan
        if 1 <= hour[i] < 8:
            ash = h[i] if np.isnan(ash) else max(ash, h[i])
            asl = l[i] if np.isnan(asl) else min(asl, l[i])
        if pos is not None:
            ent, stop, best, R = pos
            if l[i] <= stop:                                   # stop ก่อนเสมอ
                px = min(stop, o[i]) - SLIP_STOP
                trades.append((t[i], px - ent, "stop"))
                pos = None
                continue
            if hour[i] >= 23:                                  # end of day
                trades.append((t[i], c[i] - ent, "eod"))
                pos = None
                continue
            best = max(best, c[i])
            if best - ent >= A * R:
                stop = max(stop, best - D * R)
            pos = (ent, stop, best, R)
            continue
        # entry: first close ข้าม Asian-high ช่วง 08-20
        if cur_d in traded or not (8 <= hour[i - 1] < 20):
            continue
        if not (np.isfinite(ash) and np.isfinite(asl)) or ash <= asl:
            continue
        j = i - 1
        if not (c[j] > ash and c[j - 1] <= ash):
            continue
        if sp[j] > MAX_SPREAD_PT:
            continue
        if REG and c[j] <= e2d[j]:
            continue
        R = ash - asl
        ent = o[i] + sp[i] * PT * spread_mult + SLIP_IN
        stop = max(asl, ent - CAPR * R)
        traded.add(cur_d)
        pos = (ent, stop, ent, R)
    return trades


def stats(tr, label=""):
    if not tr:
        return f"{label}: no trades"
    p = np.array([x[1] for x in tr])
    w = p[p > 0]; lo = p[p <= 0]
    eq = np.cumsum(p); dd = (np.maximum.accumulate(eq) - eq).max()
    pf = w.sum() / max(-lo.sum(), 1e-9)
    yrs = {}
    for x in tr:
        yrs.setdefault(str(x[0])[:4], []).append(x[1])
    ystr = " ".join(f"{y}:{np.sum(v):+.0f}({len(v)})" for y, v in sorted(yrs.items()))
    return (f"{label} n={len(p)} net={p.sum():+8.1f} wr={100*len(w)/len(p):4.1f}% "
            f"avgW={w.mean() if len(w) else 0:+.2f} avgL={lo.mean() if len(lo) else 0:+.2f} "
            f"PF={pf:.2f} maxDD={dd:.1f} | {ystr}")


def quarters(tr):
    out = {}
    for x in tr:
        qq = f"{str(x[0])[:4]}Q{(int(str(x[0])[5:7]) - 1)//3 + 1}"
        out.setdefault(qq, []).append(x[1])
    return " ".join(f"{q}:{np.sum(v):+.0f}({len(v)})" for q, v in sorted(out.items()))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "is"
    if mode == "is":
        d = prep([2022, 2023, 2024])
        print("== IS 2023-2024 — Asian-High BO variants ==")
        for REG in (True, False):
            for CAPR in (0.75, 1.0, 1.5):
                for A in (0.75, 1.0, 1.5):
                    for D in (0.5, 0.75, 1.0):
                        tr = run(*d, REG, CAPR, A, D)
                        print(stats(tr, f"REG={int(REG)} CAP{CAPR} A{A} D{D}"))
    else:
        REG = bool(int(sys.argv[2])); CAPR = float(sys.argv[3]); A = float(sys.argv[4]); D = float(sys.argv[5])
        print(f"== TRUE OOS — REG={REG} CAP{CAPR} A{A} D{D} — เปิดครั้งเดียว ==")
        d1 = prep([2021, 2022])
        tr1 = run(*d1, REG, CAPR, A, D)
        print(stats(tr1, "2022    ")); print("   ", quarters(tr1))
        d2 = prep([2024, 2025, 2026])
        tr2 = run(*d2, REG, CAPR, A, D)
        print(stats(tr2, "2025-26 ")); print("   ", quarters(tr2))
        print("-- cost stress x1.5 --")
        print(stats(run(*d1, REG, CAPR, A, D, spread_mult=1.5), "2022 x1.5"))
        print(stats(run(*d2, REG, CAPR, A, D, spread_mult=1.5), "2025-26 x1.5"))
