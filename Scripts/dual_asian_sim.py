#!/usr/bin/env python3
"""
dual_asian_sim.py — CANONICAL sim ของ Trellis v4.00 (ตรง Trellis.mq5 ทุกเงื่อนไข)
สร้างตาม Engineer review 2026-07-03: script นี้เป็นเจ้าของตัวเลข v4 — reproducible

ตรง EA:
  LONG : close[j] ทะลุ AsianHigh(01-08) ครั้งแรกของวัน ช่วง 08-20 (bar j = closed)
         + close[j] > EMA2880[j] + (EMA2880[j]-EMA2880[j-1440]) > 0.001*close[j]
  SHORT: mirror · stop = ขอบตรงข้าม cap 1×R (SL) · trail arm 1×R dist 0.75×R (bar close)
  EOD 23:00 · 1 เทรด/วัน · 0.01 lot ($1/$1)
Pessimistic: stop-first, gap fill ที่ open, entry spread จริง/บาร์ + slip 0.02, stop slip 0.03
cost stress: spread_mult คูณทั้ง spread และ stop-slip (Engineer E2)

Usage:
  python dual_asian_sim.py all          # ทุก window + bootstrap CI
  python dual_asian_sim.py sens         # sensitivity sweep บน 2012-2020
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


def load_full(years):
    """โหลดเต็มทุกปี (ไม่มี warmup trim) — คุม start เอง"""
    return load_m1(years, warmup_tail=10 ** 9)


def run(m1, start, CAPR=1.0, A=1.0, D=0.75, SLOPE=0.001, EMA_P=2880, SLOPE_B=1440,
        allow_short=True, spread_mult=1.0):
    c, h, l, o, sp, t = m1["c"], m1["h"], m1["l"], m1["o"], m1["sp"], m1["t"]
    e = ema(c, EMA_P)
    es = np.r_[np.full(SLOPE_B, np.nan), e[SLOPE_B:] - e[:-SLOPE_B]]
    tmin = t.astype("datetime64[m]").astype(np.int64)
    hour = (tmin // 60) % 24
    day = (tmin // 1440).astype(int)
    dow = (day + 4) % 7          # MQL convention: 0=อาทิตย์ .. 5=ศุกร์
    n = len(c)
    trades = []
    pos = None
    cur_d = -1
    ash = asl = np.nan
    traded = set()
    slip_stop = SLIP_STOP * spread_mult
    for i in range(start, n):
        if day[i] != cur_d:
            cur_d = day[i]; ash = asl = np.nan
        if 1 <= hour[i] < 8:
            ash = h[i] if np.isnan(ash) else max(ash, h[i])
            asl = l[i] if np.isnan(asl) else min(asl, l[i])
        if pos is not None:
            d, ent, stop, best, R = pos
            hit = l[i] <= stop if d == 1 else h[i] >= stop
            if hit:
                px = (min(stop, o[i]) if d == 1 else max(stop, o[i])) - slip_stop * d
                ex = px if d == 1 else px + sp[i] * PT * spread_mult
                trades.append((t[i], (ex - ent) * d if d == 1 else (ent - ex), "stop"))
                pos = None
                continue
            # EOD: ศุกร์ 20:00 (flat ก่อน weekend — ตลาดบางศุกร์ปิด 20:xx) วันอื่น 23:00
            if hour[i] >= (20 if dow[i] == 5 else 23):
                ex = c[i] if d == 1 else c[i] + sp[i] * PT * spread_mult
                trades.append((t[i], (ex - ent) if d == 1 else (ent - ex), "eod"))
                pos = None
                continue
            best = max(best, c[i]) if d == 1 else min(best, c[i])
            fav = (best - ent) if d == 1 else (ent - best)
            if fav >= A * R:
                ns = best - D * R if d == 1 else best + D * R
                stop = max(stop, ns) if d == 1 else min(stop, ns)
            pos = (d, ent, stop, best, R)
            continue
        if cur_d in traded or not (8 <= hour[i - 1] < 20):
            continue
        if not (np.isfinite(ash) and np.isfinite(asl)) or ash <= asl:
            continue
        j = i - 1
        if sp[j] > MAX_SPREAD_PT or not np.isfinite(es[j]):
            continue
        R = ash - asl
        if c[j] > ash and c[j - 1] <= ash and c[j] > e[j] and es[j] > SLOPE * c[j]:
            ent = o[i] + sp[i] * PT * spread_mult + SLIP_IN
            traded.add(cur_d)
            pos = (1, ent, max(asl, ent - CAPR * R), ent, R)
        elif allow_short and c[j] < asl and c[j - 1] >= asl and c[j] < e[j] and es[j] < -SLOPE * c[j]:
            ent = o[i] - SLIP_IN
            traded.add(cur_d)
            pos = (-1, ent, min(ash, ent + CAPR * R), ent, R)
    return trades


def year_start_index(m1, year):
    """index แรกของปีที่กำหนด (ปีที่อยู่ก่อนหน้า = warmup)"""
    ys = np.datetime64(f"{year}-01-01")
    return int(np.searchsorted(m1["t"], ys))


def stats(tr, label=""):
    if not tr:
        print(f"{label}: no trades"); return np.array([])
    p = np.array([x[1] for x in tr])
    w = p[p > 0]; lo = p[p <= 0]
    eq = np.cumsum(p); dd = (np.maximum.accumulate(eq) - eq).max()
    pf = w.sum() / max(-lo.sum(), 1e-9)
    yrs = {}
    for x in tr:
        yrs.setdefault(str(x[0])[:4], []).append(x[1])
    ystr = " ".join(f"{y}:{np.sum(v):+.0f}" for y, v in sorted(yrs.items()))
    print(f"{label:<14} n={len(p):>4} net={p.sum():>+8.1f} wr={100*len(w)/len(p):4.1f}% "
          f"PF={pf:.2f} maxDD={dd:.1f}\n    {ystr}")
    return p


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "all":
        allp = []
        # 2011 (warmup = ต้นปีเอง ~Jan; เทรดจริง Feb เป็นต้นไป — 2010 ไม่มีไฟล์)
        m1 = load_full([2011]); allp += list(stats(run(m1, 12000), "2011(Feb+)"))
        m1 = load_full([2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020])
        allp += list(stats(run(m1, year_start_index(m1, 2012)), "2012-2020"))
        m1 = load_full([2021, 2022]); allp += list(stats(run(m1, year_start_index(m1, 2022)), "2022"))
        m1 = load_full([2022, 2023, 2024]); allp += list(stats(run(m1, year_start_index(m1, 2023)), "2023-2024"))
        m1 = load_full([2024, 2025, 2026]); allp += list(stats(run(m1, year_start_index(m1, 2025)), "2025-2026"))
        p = np.array(allp)
        print(f"\nTOTAL 2011(Feb)-2026: n={len(p)} net={p.sum():+.1f}")
        # bootstrap CI (Engineer A-fix-3)
        rng = np.random.default_rng(11)
        boots = np.array([rng.choice(p, size=len(p), replace=True).sum() for _ in range(10000)])
        print(f"bootstrap 10k: mean={boots.mean():+.0f} · CI95=[{np.percentile(boots,2.5):+.0f}, {np.percentile(boots,97.5):+.0f}]"
              f" · P(total<=0)={100*(boots<=0).mean():.1f}%")
        # cost stress (spread + stop slip)
        m1 = load_full([2024, 2025, 2026])
        stats(run(m1, year_start_index(m1, 2025), spread_mult=1.5), "25-26 x1.5")
    elif mode == "sens":
        m1 = load_full([2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020])
        s0 = year_start_index(m1, 2012)
        print("== sensitivity 2012-2020 (คนละยุคกับ IS ที่ fit plateau) ==")
        base = dict(CAPR=1.0, A=1.0, D=0.75, SLOPE=0.001, EMA_P=2880)
        for key, vals in [("CAPR", [0.75, 1.0, 1.25, 1.5]), ("A", [0.75, 1.0, 1.5]),
                          ("D", [0.5, 0.75, 1.0]), ("SLOPE", [0.0005, 0.001, 0.002]),
                          ("EMA_P", [1440, 2880, 4320])]:
            for v in vals:
                kw = dict(base); kw[key] = v
                tr = run(m1, s0, **kw)
                p = np.array([x[1] for x in tr])
                mark = " <== base" if v == base[key] else ""
                print(f"  {key}={v:<7} n={len(p):>4} net={p.sum():>+8.1f}{mark}")
