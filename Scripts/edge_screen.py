#!/usr/bin/env python3
"""
edge_screen.py — systematic conditional-expectancy screen บน M1 (IS 2023-2024)
วัด E[forward return H bars | condition] เทียบ cost hurdle (~$0.40 round-trip)
ครอบทั้ง MR และ momentum ในรอบเดียว · per-quarter sign stability บังคับ
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from entry_platform import load_m1, ema, er_kaufman, build_m5, atr_variants

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COST = 0.40  # $ round-trip ต่อ 0.01 lot (spread median 0.36 + slip)
HORIZONS = [5, 15, 30, 60, 120]


def main():
    m1 = load_m1([2022, 2023, 2024])
    c, h, l, t = m1["c"], m1["h"], m1["l"], m1["t"]
    n = len(c)
    e50 = ema(c, 50)
    er = er_kaufman(c, 100)
    m5 = build_m5(m1)
    atr_sma, _ = atr_variants(m5)
    tmin = t.astype("datetime64[m]").astype(np.int64)
    kf = np.searchsorted(m5["t"].astype(np.int64), tmin - (tmin % 5), side="left")
    atr = np.where(kf >= 1, atr_sma[np.maximum(kf - 1, 0)], np.nan)

    dn = np.zeros(n, dtype=int); up = np.zeros(n, dtype=int)
    for j in range(1, n):
        if c[j] < c[j - 1]: dn[j] = dn[j - 1] + 1
        elif c[j] > c[j - 1]: up[j] = up[j - 1] + 1

    dev = (c - e50) / np.where(atr > 0, atr, np.nan)          # stretch (ATR units, sign)
    slope = np.r_[np.full(15, np.nan), (e50[15:] - e50[:-15])] / np.where(atr > 0, atr, np.nan)
    ret30 = np.r_[np.full(30, np.nan), (c[30:] - c[:-30])] / np.where(atr > 0, atr, np.nan)
    hour = (tmin // 60) % 24
    q = np.array([f"{str(x)[:4]}Q{(int(str(x)[5:7]) - 1)//3 + 1}" for x in t])

    fwd = {H: np.r_[c[H:] - c[:-H], np.full(H, np.nan)] for H in HORIZONS}

    # ใช้เฉพาะ 2023-2024 (IS) + indicator พร้อม
    base = (np.arange(n) >= 12000) & np.isfinite(dev) & np.isfinite(er) & (atr > 0)
    for H in HORIZONS:
        base &= np.isfinite(fwd[H])
    qs_all = sorted(set(q[base]))

    conds = []
    # --- MR side: stretch แล้ว pause ---
    for dv in (1.0, 1.5, 2.0):
        conds.append((f"MR: dev<=-{dv} & dn==0 (BUY)", (dev <= -dv) & (dn == 0), +1))
        conds.append((f"MR: dev>=+{dv} & up==0 (SELL)", (dev >= dv) & (up == 0), -1))
        conds.append((f"MR: dev<=-{dv} (BUY)", dev <= -dv, +1))
        conds.append((f"MR: dev>=+{dv} (SELL)", dev >= dv, -1))
    # --- momentum: impulse ต่อเนื่อง ---
    for k_ in (4, 6, 8):
        conds.append((f"MOM: up-run>={k_} (BUY)", up >= k_, +1))
        conds.append((f"MOM: dn-run>={k_} (SELL)", dn >= k_, -1))
    for r in (2.0, 3.0):
        conds.append((f"MOM: ret30>=+{r}ATR (BUY)", ret30 >= r, +1))
        conds.append((f"MOM: ret30<=-{r}ATR (SELL)", ret30 <= -r, -1))
    # --- trend-align pullback: slope แรง + ย่อกลับหา EMA ---
    conds.append(("PB: slope>+0.5 & dev in[-1,0] (BUY)", (slope > 0.5) & (dev > -1) & (dev < 0), +1))
    conds.append(("PB: slope<-0.5 & dev in[0,1] (SELL)", (slope < -0.5) & (dev < 1) & (dev > 0), -1))
    # --- ER regime ---
    conds.append(("TREND: er>=0.35 & up-run>=3 (BUY)", (er >= 0.35) & (up >= 3), +1))
    conds.append(("TREND: er>=0.35 & dn-run>=3 (SELL)", (er >= 0.35) & (dn >= 3), -1))
    # --- session drift (ไม่มีเงื่อนไขราคา) ---
    for h0, h1 in ((1, 8), (8, 12), (12, 16), (16, 20), (20, 24)):
        conds.append((f"HOUR {h0:02d}-{h1:02d} (BUY)", (hour >= h0) & (hour < h1), +1))

    print(f"IS bars: {base.sum()} · cost hurdle ${COST} · quarters: {len(qs_all)}")
    print(f"{'condition':<38}{'n':>8}" + "".join(f"{'E'+str(H):>8}" for H in HORIZONS) + f"{'stabH60':>8}")
    for name, m, d in conds:
        mm = m & base
        nn = int(mm.sum())
        if nn < 500:
            continue
        es = [d * np.nanmean(fwd[H][mm]) for H in HORIZONS]
        # stability ที่ H=60: sign ต่อ quarter ตรงกับ pooled กี่ quarter
        s60 = d * np.nanmean(fwd[60][mm])
        stab = tot = 0
        for qq in qs_all:
            mq = mm & (q == qq)
            if mq.sum() >= 50:
                tot += 1
                stab += int((d * np.nanmean(fwd[60][mq]) > 0) == (s60 > 0))
        flag = " ***" if abs(s60) >= COST and stab >= tot - 1 and tot >= 7 else ""
        print(f"{name:<38}{nn:>8}" + "".join(f"{e:>+8.2f}" for e in es) + f"{stab:>5}/{tot}{flag}")


if __name__ == "__main__":
    main()
