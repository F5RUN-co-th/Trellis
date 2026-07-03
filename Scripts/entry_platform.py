#!/usr/bin/env python3
"""
entry_platform.py — Phase B (TRELLIS-008): indicator/feature platform บน M1 จริง
ขั้น A: CALIBRATION — replicate ER/EMA-dev/ATR ของ EA แล้วเทียบกับค่าที่ EA log จริง
(diag CSV: er_entry, dev_atr, atr_entry ที่ 1,576 entries) — ผ่านเกณฑ์ก่อนถึงใช้ทำ feature

Usage: python entry_platform.py calibrate
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(r"D:/workspace/Doc/T.me/R&D/Gloo/Data")
DIAG = Path(r"C:/Users/itd_surachartt/AppData/Roaming/MetaQuotes/Terminal/Common/Files")
QS = ["66q1", "66q2", "66q3", "66q4", "67q1", "67q2", "67q3", "67q4"]

# ---------- M1 loader ----------
def load_m1(years, warmup_tail=12000):
    """คืน dict arrays: t (datetime64[m]), o,h,l,c (float), sp (spread points) — bar-sequence
    ปีแรกใน years ใช้เฉพาะหาง warmup_tail bars (indicator warmup)"""
    ts, o, h, l, c, sp = [], [], [], [], [], []
    for i, y in enumerate(years):
        rows = []
        with open(DATA / f"XAUUSD_M1_{y}.csv", newline="") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                rows.append(p)
        if i == 0:
            rows = rows[-warmup_tail:]
        for p in rows:
            ts.append(np.datetime64(p[0].replace(".", "-") + "T" + p[1][:5]))
            o.append(float(p[2])); h.append(float(p[3])); l.append(float(p[4])); c.append(float(p[5]))
            sp.append(float(p[8]) if len(p) > 8 else 36.0)
    return dict(t=np.array(ts), o=np.array(o), h=np.array(h), l=np.array(l), c=np.array(c),
                sp=np.array(sp))


# ---------- indicators (replicate MT5) ----------
def ema(series, period):
    k = 2.0 / (period + 1)
    out = np.empty_like(series)
    out[0] = series[0]
    for i in range(1, len(series)):
        out[i] = out[i - 1] + k * (series[i] - out[i - 1])
    return out


def er_kaufman(c, n):
    """ER ที่ index i = ใช้ window c[i-n+1..i] (n bars) — ตรงกับ EfficiencyRatio(cl, n) ของ EA"""
    d = np.abs(np.diff(c))
    path = np.convolve(d, np.ones(n - 1), mode="full")[: len(d)]  # rolling sum n-1 diffs
    out = np.full(len(c), np.nan)
    for i in range(n - 1, len(c)):
        net = abs(c[i] - c[i - n + 1])
        p = d[i - n + 1 : i].sum() + 0.0  # path ของ window
        p = np.abs(np.diff(c[i - n + 1 : i + 1])).sum()
        out[i] = net / p if p > 0 else 1.0
    return out


def build_m5(m1):
    """รวม M1 -> M5 (floor นาที/5 ตาม server time — MT5 semantics)"""
    tmin = m1["t"].astype("datetime64[m]").astype(np.int64)
    key = tmin - (tmin % 5)
    idx = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    o = m1["o"][idx]
    cl = m1["c"][np.r_[idx[1:] - 1, len(key) - 1]]
    hi = np.array([m1["h"][a:b].max() for a, b in zip(idx, np.r_[idx[1:], len(key)])])
    lo = np.array([m1["l"][a:b].min() for a, b in zip(idx, np.r_[idx[1:], len(key)])])
    return dict(t=key[idx].astype("datetime64[m]"), o=o, h=hi, l=lo, c=cl)


def atr_variants(m5, period=14):
    pc = np.r_[m5["c"][0], m5["c"][:-1]]
    tr = np.maximum(m5["h"] - m5["l"], np.maximum(np.abs(m5["h"] - pc), np.abs(m5["l"] - pc)))
    # variant 1: rolling SMA ของ TR (MT5 built-in ATR)
    sma = np.full(len(tr), np.nan)
    cs = np.cumsum(tr)
    sma[period - 1:] = (cs[period - 1:] - np.r_[0, cs[:-period]][: len(cs) - period + 1]) / period
    # variant 2: Wilder smoothing
    wil = np.full(len(tr), np.nan)
    wil[period - 1] = tr[:period].mean()
    for i in range(period, len(tr)):
        wil[i] = (wil[i - 1] * (period - 1) + tr[i]) / period
    return sma, wil


# ---------- diag entries (ค่าจริงจาก EA) ----------
def load_entries():
    out = []
    for q in QS:
        with open(DIAG / f"Trellis_diag_770001_{q}.csv", newline="") as f:
            for r in csv.DictReader(f):
                out.append(dict(
                    q=q,
                    ot=np.datetime64(datetime.strptime(r["open_time"], "%Y.%m.%d %H:%M:%S")
                                     .strftime("%Y-%m-%dT%H:%M")),
                    er=float(r["er_entry"]), dev=float(r["dev_atr"]), atr=float(r["atr_entry"]),
                    dir=int(r["dir"]), pnl=float(r["realized_usd"]),
                    levels=int(r["levels_max"]), reason=r["exit_reason"], age=int(r["age_bars"]),
                ))
    return out


def calibrate():
    m1 = load_m1([2022, 2023, 2024])
    n = len(m1["t"])
    print(f"M1 bars: {n} ({m1['t'][0]} -> {m1['t'][-1]})")

    e50 = ema(m1["c"], 50)
    er = er_kaufman(m1["c"], 100)
    m5 = build_m5(m1)
    atr_sma, atr_wil = atr_variants(m5)

    # map: bar time -> index
    t_idx = {t.astype("datetime64[m]").astype(np.int64).item(): i for i, t in enumerate(m1["t"])}
    m5_int = m5["t"].astype(np.int64)

    entries = load_entries()
    print(f"entries จาก diag: {len(entries)}")

    res = dict(er=[], dev=[], atr_s=[], atr_w=[], miss=0)
    for x in entries:
        ti = x["ot"].astype("datetime64[m]").astype(np.int64).item()
        if ti not in t_idx:
            res["miss"] += 1
            continue
        i = t_idx[ti]           # forming bar ตอนเข้า
        j = i - 1               # closed bar (shift 1) — ที่ EA ใช้ตัดสิน
        # ER: CopyClose(shift1, 100 bars) = window จบที่ bar j
        my_er = er[j]
        # dev_atr: |close[j] - EMA[j]| / ATR
        # ATR: last CLOSED M5 bar ณ เวลา bar i (forming M1)
        k = np.searchsorted(m5_int, ti) - 1          # M5 forming = bar ที่ครอบ ti
        k_closed = k - 1 if m5_int[min(k, len(m5_int)-1)] <= ti else k - 1
        # หา M5 forming index ที่ floor(ti/5): closed = index ก่อนหน้า
        k_form = np.searchsorted(m5_int, ti - (ti % 5), side="left")
        kc = k_form - 1
        a_s, a_w = atr_sma[kc], atr_wil[kc]
        my_dev_s = abs(m1["c"][j] - e50[j]) / a_s if a_s > 0 else np.nan
        res["er"].append((my_er, x["er"]))
        res["dev"].append((my_dev_s, x["dev"]))
        res["atr_s"].append((a_s, x["atr"]))
        res["atr_w"].append((a_w, x["atr"]))

    print(f"หา bar ไม่เจอ (missing minute): {res['miss']}")
    for name, tol in [("er", 0.005), ("dev", 0.03), ("atr_s", 0.03), ("atr_w", 0.03)]:
        arr = np.array(res[name])
        d = np.abs(arr[:, 0] - arr[:, 1])
        ok = np.isfinite(d)
        print(f"  {name:<6} match(±{tol}): {100 * (d[ok] <= tol).sum() / ok.sum():5.1f}%"
              f"  median|Δ|={np.nanmedian(d):.4f}  p95|Δ|={np.nanpercentile(d[ok],95):.4f}  n={ok.sum()}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "calibrate":
        calibrate()
    else:
        sys.exit(__doc__)
