#!/usr/bin/env python3
"""
edge_screen2.py — screen รอบ 2: horizon ยาว (4-24 ชม.) + เงื่อนไขโครงสร้าง
(prior-day H/L breakout, Asian-range breakout, spike bars, DOW, EMA400 stretch)
IS = 2023-2024 · cost hurdle $0.40 (จิ๋วเมื่อเทียบ move ระดับนี้ — ใช้ $1.0 เป็นเกณฑ์ flag แทน)
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from entry_platform import load_m1, ema, build_m5, atr_variants

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HORIZONS = [240, 480, 960, 1440]
FLAG = 1.0


def main():
    m1 = load_m1([2022, 2023, 2024])
    c, h, l, o, t = m1["c"], m1["h"], m1["l"], m1["o"], m1["t"]
    n = len(c)
    e400 = ema(c, 400)
    m5 = build_m5(m1)
    atr_sma, _ = atr_variants(m5)
    tmin = t.astype("datetime64[m]").astype(np.int64)
    kf = np.searchsorted(m5["t"].astype(np.int64), tmin - (tmin % 5), side="left")
    atr = np.where(kf >= 1, atr_sma[np.maximum(kf - 1, 0)], np.nan)
    hour = (tmin // 60) % 24
    day = (tmin // 1440).astype(int)
    dow = ((tmin // 1440) + 4) % 7    # 1970-01-01 = พฤหัส(4) -> 0=อาทิตย์
    q = np.array([f"{str(x)[:4]}Q{(int(str(x)[5:7]) - 1)//3 + 1}" for x in t])

    # prior-day high/low (server day)
    pd_hi = np.full(n, np.nan); pd_lo = np.full(n, np.nan)
    dh = {}; dl = {}
    for j in range(n):
        d_ = day[j]
        if d_ not in dh:
            dh[d_] = h[j]; dl[d_] = l[j]
        else:
            dh[d_] = max(dh[d_], h[j]); dl[d_] = min(dl[d_], l[j])
    days_sorted = {}
    for j in range(n):
        d_ = day[j]
        if d_ - 1 in dh: pd_hi[j] = dh[d_ - 1]; pd_lo[j] = dl[d_ - 1]
        elif d_ - 2 in dh: pd_hi[j] = dh[d_ - 2]; pd_lo[j] = dl[d_ - 2]  # ข้าม weekend
        elif d_ - 3 in dh: pd_hi[j] = dh[d_ - 3]; pd_lo[j] = dl[d_ - 3]

    # Asian range (server 01:00-08:00 ของวันเดียวกัน)
    as_hi = np.full(n, np.nan); as_lo = np.full(n, np.nan)
    cur = {}
    for j in range(n):
        d_ = day[j]
        if 1 <= hour[j] < 8:
            if d_ not in cur: cur[d_] = [h[j], l[j]]
            else: cur[d_] = [max(cur[d_][0], h[j]), min(cur[d_][1], l[j])]
        if d_ in cur and hour[j] >= 8:
            as_hi[j] = cur[d_][0]; as_lo[j] = cur[d_][1]

    # first cross ของวัน (กัน overlap มหาศาล): bar แรกที่ close ทะลุ
    def first_cross(level, above, window_ok):
        out = np.zeros(n, dtype=bool)
        done = set()
        for j in range(1, n):
            d_ = day[j]
            if d_ in done or not window_ok[j] or not np.isfinite(level[j]):
                continue
            crossed = c[j] > level[j] if above else c[j] < level[j]
            prev_in = c[j - 1] <= level[j] if above else c[j - 1] >= level[j]
            if crossed and prev_in:
                out[j] = True; done.add(d_)
        return out

    win_day = (hour >= 8) & (hour < 22)
    bo_pdh = first_cross(pd_hi, True, win_day)
    bo_pdl = first_cross(pd_lo, False, win_day)
    bo_ash = first_cross(as_hi, True, (hour >= 8) & (hour < 20))
    bo_asl = first_cross(as_lo, False, (hour >= 8) & (hour < 20))

    # spike bar: range แท่ง >= 4x ATR
    rng = h - l
    spike_up = (rng >= 4 * atr) & (c > o)
    spike_dn = (rng >= 4 * atr) & (c < o)

    dev400 = (c - e400) / np.where(atr > 0, atr, np.nan)

    fwd = {H: np.r_[c[H:] - c[:-H], np.full(H, np.nan)] for H in HORIZONS}
    base = (np.arange(n) >= 12000) & (atr > 0)
    for H in HORIZONS:
        base &= np.isfinite(fwd[H])
    qs_all = sorted(set(q[base]))

    conds = [
        ("BO prior-day-high (BUY)", bo_pdh, +1),
        ("BO prior-day-low (SELL)", bo_pdl, -1),
        ("BO prior-day-high FADE (SELL)", bo_pdh, -1),
        ("BO Asian-high (BUY)", bo_ash, +1),
        ("BO Asian-low (SELL)", bo_asl, -1),
        ("SPIKE up cont (BUY)", spike_up, +1),
        ("SPIKE up fade (SELL)", spike_up, -1),
        ("SPIKE dn cont (SELL)", spike_dn, -1),
        ("SPIKE dn fade (BUY)", spike_dn, +1),
        ("dev400<=-3 (BUY)", dev400 <= -3, +1),
        ("dev400>=+3 (SELL)", dev400 >= 3, -1),
        ("dev400<=-5 (BUY)", dev400 <= -5, +1),
        ("dev400>=+5 (SELL)", dev400 >= 5, -1),
    ]
    for dw in range(1, 6):
        conds.append((f"DOW={dw} @01-02 (BUY)", (dow == dw) & (hour == 1), +1))

    print(f"IS bars: {base.sum()} · horizons(min): {HORIZONS} · flag เมื่อ |E|>=${FLAG} + stable")
    print(f"{'condition':<32}{'n':>7}" + "".join(f"{'E'+str(H):>8}" for H in HORIZONS) + f"{'stab480':>8}")
    for name, m, d in conds:
        mm = m & base
        nn = int(mm.sum())
        if nn < 150:
            continue
        es = [d * np.nanmean(fwd[H][mm]) for H in HORIZONS]
        s = d * np.nanmean(fwd[480][mm])
        stab = tot = 0
        for qq in qs_all:
            mq = mm & (q == qq)
            if mq.sum() >= 15:
                tot += 1
                stab += int((d * np.nanmean(fwd[480][mq]) > 0) == (s > 0))
        flag = " ***" if abs(s) >= FLAG and tot >= 6 and stab >= tot - 1 else ""
        print(f"{name:<32}{nn:>7}" + "".join(f"{e:>+8.2f}" for e in es) + f"{stab:>5}/{tot}{flag}")


if __name__ == "__main__":
    main()
