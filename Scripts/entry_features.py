#!/usr/bin/env python3
"""
entry_features.py — Phase B ขั้น B: feature discrimination ที่ 1,576 entries จริง
ทุก feature คำนวณจาก closed bar ณ ตอนเข้า (no lookahead) · ทุกตัวเลขจาก script
เกณฑ์เชื่อ: (1) แยก avg pnl ชัด (2) ทิศเดียวกัน ≥6/8 quarters (3) ชนะ null (permutation)
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from entry_platform import load_m1, ema, er_kaufman, build_m5, atr_variants, load_entries, QS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    m1 = load_m1([2022, 2023, 2024])
    e50 = ema(m1["c"], 50)
    m5 = build_m5(m1)
    atr_sma, _ = atr_variants(m5)
    m5_int = m5["t"].astype(np.int64)
    t_idx = {t.astype(np.int64).item(): i for i, t in enumerate(m1["t"].astype("datetime64[m]"))}
    o, h, l, c = m1["o"], m1["h"], m1["l"], m1["c"]

    # TR M1 สำหรับ vol-expansion feature
    pc = np.r_[c[0], c[:-1]]
    tr1 = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    cs_tr = np.cumsum(tr1)

    def tr_mean(j, n):
        if j - n < 0: return np.nan
        return (cs_tr[j] - cs_tr[j - n]) / n

    ents = load_entries()
    F = {k: [] for k in ["slope_against", "impulse30", "ext_dist", "bars_since_ext",
                         "consec_against", "wick_rej", "vol_x", "hour", "dev"]}
    meta = []
    for x in ents:
        ti = x["ot"].astype("datetime64[m]").astype(np.int64).item()
        i = t_idx[ti]; j = i - 1
        d = x["dir"]
        kc = np.searchsorted(m5_int, ti - (ti % 5), side="left") - 1
        atr = atr_sma[kc]
        if not np.isfinite(atr) or atr <= 0 or j < 300:
            continue
        # 1) EMA slope สวนทิศ basket (บวก = fade สวน trend ที่กำลังวิ่งแรง)
        F["slope_against"].append((e50[j] - e50[j - 15]) / atr * (-d))
        # 2) impulse 30 bars สวนทิศ (ขนาด dip/rip ที่กำลัง fade)
        F["impulse30"].append((c[j] - c[j - 30]) / atr * (-d))
        # 3) ระยะจาก extreme 120-bar (BUY: ห่างจาก low — 0 = ปิดที่ก้นพอดี)
        if d == 1:
            w = l[j - 119: j + 1]; ext = w.min(); F["ext_dist"].append((c[j] - ext) / atr)
            F["bars_since_ext"].append(119 - int(np.argmin(w[::-1])))
        else:
            w = h[j - 119: j + 1]; ext = w.max(); F["ext_dist"].append((ext - c[j]) / atr)
            F["bars_since_ext"].append(119 - int(np.argmax(w[::-1])))
        # 4) แท่งติดกันสวนทิศ basket (momentum ที่กำลังสวน)
        k = 0
        while j - k - 1 >= 0 and (c[j - k] - c[j - k - 1]) * (-d) > 0 and k < 30:
            k += 1
        F["consec_against"].append(k)
        # 5) rejection wick ฝั่งที่ fade (BUY: ไส้ล่าง)
        F["wick_rej"].append(((min(o[j], c[j]) - l[j]) if d == 1 else (h[j] - max(o[j], c[j]))) / atr)
        # 6) vol expansion: TR15 / TR240
        F["vol_x"].append(tr_mean(j, 15) / tr_mean(j, 240))
        # 7) ชั่วโมง server
        F["hour"].append(int(str(x["ot"])[11:13]))
        # 8) dev (ของเดิม — ไว้เทียบ)
        F["dev"].append(x["dev"])
        meta.append((x["q"], x["pnl"], 1 if x["pnl"] > 0 else 0, 1 if x["levels"] >= 5 else 0))

    qs = np.array([m[0] for m in meta])
    pnl = np.array([m[1] for m in meta])
    win = np.array([m[2] for m in meta])
    deep = np.array([m[3] for m in meta])
    n = len(pnl)
    print(f"entries ใช้ได้: {n} · base: winrate {100*win.mean():.1f}% · avg pnl {pnl.mean():+.3f} · P(deep) {100*deep.mean():.1f}%\n")

    rng = np.random.default_rng(7)
    print(f"{'feature':<16}{'Q1(แย่สุด?)':>22}{'Q5':>22}{'สเปรดavg$':>10}{'ทิศคงที่':>9}{'null p':>8}")
    for name, vals in F.items():
        v = np.array(vals, dtype=float)
        edges = np.nanquantile(v, [0, .2, .4, .6, .8, 1.0])
        edges[-1] += 1e-9
        qb = np.clip(np.searchsorted(edges, v, side="right") - 1, 0, 4)
        a1, a5 = pnl[qb == 0].mean(), pnl[qb == 4].mean()
        w1, w5 = 100 * win[qb == 0].mean(), 100 * win[qb == 4].mean()
        d1, d5 = 100 * deep[qb == 0].mean(), 100 * deep[qb == 4].mean()
        spread = a5 - a1
        # per-quarter sign stability ของสเปรด Q5-Q1
        signs = 0; tot = 0
        for q in QS:
            m_ = qs == q
            if (qb[m_] == 0).sum() >= 5 and (qb[m_] == 4).sum() >= 5:
                s = pnl[m_ & (qb == 4)].mean() - pnl[m_ & (qb == 0)].mean()
                tot += 1; signs += (1 if (s > 0) == (spread > 0) else 0)
        # permutation null: shuffle pnl 500 รอบ
        null = np.array([
            pnl[perm[qb == 4]].mean() - pnl[perm[qb == 0]].mean()
            for perm in (rng.permutation(n) for _ in range(500))
        ])
        pval = (np.abs(null) >= abs(spread)).mean()
        print(f"{name:<16}"
              f"{a1:>+7.2f}$ w{w1:>4.0f}% d{d1:>4.0f}%"
              f"{a5:>+7.2f}$ w{w5:>4.0f}% d{d5:>4.0f}%"
              f"{spread:>+10.2f}{signs:>6}/{tot}{pval:>8.3f}")

    print("\n(Q1/Q5 = quintile ล่าง/บนของ feature · d = P(deep) · ทิศคงที่ = quarters ที่สเปรดทิศเดียวกับ pooled · null p = permutation)")


if __name__ == "__main__":
    main()
