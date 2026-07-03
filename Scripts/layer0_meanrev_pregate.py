#!/usr/bin/env python3
"""
TRELLIS Stage 0 — Layer 0: Model-free Mean-Reversion Pre-Gate
==============================================================
อ้างอิง: Plan/TRELLIS-002_expectancy_sim_plan.md §4 ชั้น 0

เป้าหมาย / Purpose:
  ทดสอบ "model-free, entry-agnostic" ว่า XAUUSD มีโครงสร้าง mean-reversion
  ที่ timescale ของ grid หรือเป็น trending — ถ้า trending (grid ตาย) → จบ ไม่ต้อง build engine.

เครื่องมือ (entry-agnostic, ไม่ผูก param เดียว — แก้ circularity ตาม Engineer §3.1):
  1. Variance Ratio test (Lo-MacKinlay 1988) heteroskedasticity-robust z*  : VR<1 = mean-revert, >1 = trend
  2. Hurst exponent via DFA                                                  : H<0.5 = anti-persistent (mean-revert)
  ทดสอบข้ามหลาย horizon (q นาที) — ไม่ใช่ scale เดียว.

วินัยตาม CLAUDE.md "Verify ≠ Self-grading":
  - SELF-TEST ก่อน: รัน estimator บน synthetic ที่รู้คำตอบ (RW→VR≈1, AR(1)+→VR<1, trend→VR>1)
    ถ้า estimator เพี้ยนบน synthetic = ห้ามเชื่อผลบน Gold (ตรวจเครื่องมือตัวเอง)
  - numbers ทั้งหมด derive จาก script นี้ — export JSON, ไม่พิมพ์มือ
  - handle gap: ใช้เฉพาะ return ใน contiguous M1 segment (กัน weekend/session gap ปน → bias)

Data: Gloo/Data/XAUUSD_M1_YYYY.csv (9-col tab, EET, CRLF — csv module handle ให้)
Run:
  python layer0_meanrev_pregate.py --selftest          # ตรวจ estimator อย่างเดียว
  python layer0_meanrev_pregate.py                      # full 2011-2026 + IS/OOS split
  python layer0_meanrev_pregate.py --years 2020 2021    # เฉพาะบางปี
"""

import argparse
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

# console Windows เป็น cp874 — บังคับ UTF-8 กัน UnicodeEncodeError (≈, ไทย)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA_DIR = Path(r"D:\workspace\Doc\T.me\R&D\Gloo\Data")
OUT_DIR = Path(r"D:\workspace\Doc\T.me\R&D\Trellis\Research")
ALL_YEARS = list(range(2011, 2027))
IS_YEARS = list(range(2011, 2022))   # In-sample  (TRELLIS-002 §5)
OOS_YEARS = list(range(2022, 2027))  # Out-of-sample
# horizon (จำนวน M1 bar = นาที) ครอบ timescale ของ grid intraday
HORIZONS = [2, 4, 8, 16, 30, 60, 120, 240]
GAP_SEC = 60          # contiguous = 60s ติดกันพอดี
MIN_SEG = 600         # ใช้ segment ที่ยาวพอ (>=10 ชม.ติด) เพื่อ q ใหญ่

# Cost context (placeholder — รอ §10.6 broker จริง; conservative retail Gold)
ROUND_TRIP_COST_USD = 0.50   # $ ต่อ 1 ออนซ์ (spread+comm round trip โดยประมาณ) — flag ว่าเป็น placeholder


# ----------------------------------------------------------------------------
# Normal CDF (ไม่มี scipy) / Normal CDF without scipy
# ----------------------------------------------------------------------------
def norm_sf(x):
    """Survival function P(Z > x) สำหรับ standard normal."""
    return 0.5 * math.erfc(x / math.sqrt(2.0))


# ----------------------------------------------------------------------------
# Loader — reuse pattern จาก Gloo/Scripts/Phase0_regime_validation.py
# ----------------------------------------------------------------------------
def load_m1_closes(year):
    """คืน list ของ (datetime, close) จาก XAUUSD_M1_YYYY.csv (9-col tab)."""
    rows = []
    path = DATA_DIR / f"XAUUSD_M1_{year}.csv"
    if not path.exists():
        print(f"  ! missing {path.name}")
        return rows
    with open(path, newline="") as f:
        for line in csv.reader(f, delimiter="\t"):
            if len(line) < 6:
                continue
            try:
                dt = datetime.strptime(f"{line[0]} {line[1]}", "%Y.%m.%d %H:%M:%S")
                close = float(line[5])
                rows.append((dt, close))
            except (ValueError, IndexError):
                continue
    return rows


def build_contiguous_logret_segments(closes_dt):
    """
    รับ [(dt, close)...] เรียงเวลา → คืน list ของ numpy array ของ log-return
    เฉพาะช่วงที่ bar ติดกัน 60s (กัน weekend/session gap ปน).
    """
    closes_dt = sorted(closes_dt, key=lambda x: x[0])
    segments = []
    cur_prices = []
    prev_dt = None
    for dt, c in closes_dt:
        if c <= 0:
            # ปิด segment ปัจจุบัน
            if len(cur_prices) > 1:
                segments.append(np.log(np.asarray(cur_prices)))
            cur_prices = []
            prev_dt = None
            continue
        if prev_dt is not None and (dt - prev_dt).total_seconds() == GAP_SEC:
            cur_prices.append(c)
        else:
            if len(cur_prices) > 1:
                segments.append(np.log(np.asarray(cur_prices)))
            cur_prices = [c]
        prev_dt = dt
    if len(cur_prices) > 1:
        segments.append(np.log(np.asarray(cur_prices)))
    # แปลง log-price segment → log-return segment, เก็บเฉพาะที่ยาวพอ
    ret_segs = [np.diff(lp) for lp in segments if len(lp) > MIN_SEG]
    return ret_segs


# ----------------------------------------------------------------------------
# Variance Ratio test (Lo-MacKinlay 1988, overlapping, heteroskedasticity-robust)
# pooled ข้ามหลาย segment ด้วย global mean
# ----------------------------------------------------------------------------
def variance_ratio(ret_segs, q):
    """
    คืน dict: VR, z_star (hetero-robust), p_value, n (จำนวน return รวม).
    VR<1 mean-revert, >1 trend, =1 random walk.
    """
    # global mean ของ 1-period return
    all_r = np.concatenate(ret_segs)
    n = all_r.size
    if n <= q + 1:
        return None
    mu = all_r.mean()

    # σ_a² : variance ของ 1-period return (pooled)
    dev = all_r - mu
    sig_a = np.sum(dev ** 2) / (n - 1)
    if sig_a <= 0:
        return None

    # σ_c² : variance ของ q-period overlapping return (pooled, เฉพาะใน segment)
    sum_sq = 0.0
    m_count = 0
    for r in ret_segs:
        if r.size <= q:
            continue
        # q-period overlapping sum ภายใน segment
        csum = np.cumsum(r)
        qsum = csum[q - 1:] - np.concatenate(([0.0], csum[:-q]))  # ผลรวม q ตัวติดกัน
        d = qsum - q * mu
        sum_sq += np.sum(d ** 2)
        m_count += d.size
    if m_count == 0:
        return None
    # pooled normalizer: ใช้จำนวน q-window จริง (m_count) ไม่ใช่ (n-q+1)
    # window สร้างใน segment เท่านั้น → เสีย (q-1) ทุกขอบ × หลายพัน segment
    # ถ้าใช้ (n-q+1) จะ overstate mean-reversion ที่ q ใหญ่ (VR เล็กเกินจริง)
    m = q * m_count * (1.0 - q / n)
    # normalizer m ของ Lo-MacKinlay ทำให้ sig_c เทียบ sig_a ได้ตรง → VR = sig_c/sig_a
    # (ไม่หาร q ซ้ำ — การหาร q เกินทำให้ VR≈1/q ซึ่งผิด)
    sig_c = sum_sq / m
    vr = sig_c / sig_a

    # heteroskedasticity-robust z* (Lo-MacKinlay theorem)
    dev_sq = dev ** 2
    denom = np.sum(dev_sq) ** 2
    theta = 0.0
    for j in range(1, q):
        # δ_j = Σ (r_t-μ)²(r_{t-j}-μ)² / (Σ(r_t-μ)²)²
        num = np.sum(dev_sq[j:] * dev_sq[:-j])
        delta_j = num / denom
        w = (2.0 * (q - j) / q) ** 2
        theta += w * delta_j
    z = (vr - 1.0) / math.sqrt(theta) if theta > 0 else float("nan")
    p = 2.0 * norm_sf(abs(z)) if not math.isnan(z) else float("nan")
    return {"q": q, "VR": vr, "z_star": z, "p_value": p, "n": int(n)}


# ----------------------------------------------------------------------------
# Hurst exponent via DFA (Detrended Fluctuation Analysis)
# ----------------------------------------------------------------------------
def hurst_dfa(ret_segs, scales=None):
    """
    POOLED DFA ข้ามทุก segment (ไม่ใช่ segment ยาวสุดอันเดียว — กัน single-segment fragility).
    ที่แต่ละ scale รวม detrended variance จากทุก segment แล้ว fit ครั้งเดียว.
    คืน alpha (Hurst): ~0.5 random, <0.5 mean-revert, >0.5 trend.
    """
    segs = [r for r in ret_segs if r.size >= 1000]
    if not segs:
        return None
    nmax = max(r.size for r in segs)
    if scales is None:
        scales = np.unique(np.floor(np.logspace(np.log10(16), np.log10(nmax // 4), 20)).astype(int))
    F, used = [], []
    for s in scales:
        if s < 8:
            continue
        sq_sum, cnt = 0.0, 0
        x = np.arange(s)
        xm = x.mean()
        sxx = np.sum((x - xm) ** 2)
        for r in segs:
            nseg = r.size // s
            if nseg < 4:                       # ต้องมี window พอใน segment นี้
                continue
            profile = np.cumsum(r - r.mean())
            W = profile[:nseg * s].reshape(nseg, s)
            ym = W.mean(axis=1, keepdims=True)
            slope = (W * (x - xm)).sum(axis=1, keepdims=True) / sxx
            resid = W - (ym + slope * (x - xm))   # linear detrend (vectorized)
            sq_sum += float(np.sum(resid ** 2))
            cnt += W.size
        if cnt == 0:
            continue
        F.append(math.sqrt(sq_sum / cnt))         # pooled RMS ที่ scale s
        used.append(s)
    if len(used) < 4:
        return None
    alpha = np.polyfit(np.log(used), np.log(F), 1)[0]
    return float(alpha)


# ----------------------------------------------------------------------------
# Cost context (placeholder จนกว่ามี broker จริง §10.6)
# ----------------------------------------------------------------------------
def move_size_usd(ret_segs, q, ref_price):
    """typical |q-period move| ในหน่วย $ (std ของ q-period log-ret × ราคา)."""
    all_r = np.concatenate(ret_segs)
    sd1 = all_r.std()
    sd_q = sd1 * math.sqrt(q)          # ภายใต้ RW (อ้างอิงคร่าว)
    return sd_q * ref_price


# ----------------------------------------------------------------------------
# SELF-TEST — ตรวจ estimator บน synthetic ที่รู้คำตอบ (CLAUDE.md §Verify)
# ----------------------------------------------------------------------------
def run_selftest():
    print("=" * 72)
    print("SELF-TEST — ตรวจ VR estimator บน synthetic (ต้องผ่านก่อนเชื่อผล Gold)")
    print("=" * 72)
    rng = np.random.default_rng(42)
    N = 200_000
    cases = {}

    # 1) Random walk → VR ≈ 1, |z| เล็ก
    rw = rng.normal(0, 1e-3, N)
    # 2) Mean-reverting AR(1) phi<0 ใน return (anti-persistent) → VR < 1
    ar = np.zeros(N)
    eps = rng.normal(0, 1e-3, N)
    phi = -0.3
    for t in range(1, N):
        ar[t] = phi * ar[t - 1] + eps[t]
    # 3) Trending (positive autocorrelation) → VR > 1
    tr = np.zeros(N)
    eps2 = rng.normal(0, 1e-3, N)
    phi2 = 0.3
    for t in range(1, N):
        tr[t] = phi2 * tr[t - 1] + eps2[t]

    for name, series, expect in [
        ("random_walk", rw, "VR≈1"),
        ("mean_revert_AR(-0.3)", ar, "VR<1"),
        ("trend_AR(+0.3)", tr, "VR>1"),
    ]:
        res = {q: variance_ratio([series], q) for q in [2, 8, 30]}
        cases[name] = {str(q): res[q] for q in res}
        vr8 = res[8]["VR"]
        z8 = res[8]["z_star"]
        print(f"\n[{name}] expect {expect}")
        for q in [2, 8, 30]:
            r = res[q]
            print(f"  q={q:>3}: VR={r['VR']:.4f}  z*={r['z_star']:+.2f}  p={r['p_value']:.3g}")

    # ตัดสินว่า estimator ถูกไหม
    ok_rw = abs(cases["random_walk"]["8"]["VR"] - 1.0) < 0.05
    ok_mr = cases["mean_revert_AR(-0.3)"]["8"]["VR"] < 0.95
    ok_tr = cases["trend_AR(+0.3)"]["8"]["VR"] > 1.05
    verdict = ok_rw and ok_mr and ok_tr
    print("\n" + "-" * 72)
    print(f"  random_walk VR≈1 : {'OK' if ok_rw else 'FAIL'}")
    print(f"  AR(-0.3) VR<1    : {'OK' if ok_mr else 'FAIL'}")
    print(f"  AR(+0.3) VR>1    : {'OK' if ok_tr else 'FAIL'}")
    print(f"  ESTIMATOR SELF-TEST: {'PASS' if verdict else 'FAIL — ห้ามเชื่อผล Gold'}")
    print("=" * 72)
    return {"cases": cases, "pass": bool(verdict)}


# ----------------------------------------------------------------------------
# วิเคราะห์ Gold ช่วงปีที่กำหนด
# ----------------------------------------------------------------------------
def analyze(years, label):
    print(f"\nLoading M1 {label} ({years[0]}-{years[-1]}) ...")
    all_rows = []
    for y in years:
        rows = load_m1_closes(y)
        all_rows.extend(rows)
        if rows:
            print(f"  {y}: {len(rows):,} bars")
    if not all_rows:
        print(f"  ! no data for {label}")
        return None
    ref_price = np.median([c for _, c in all_rows])
    segs = build_contiguous_logret_segments(all_rows)
    total_ret = int(sum(s.size for s in segs))
    print(f"  contiguous segments: {len(segs)}  | usable returns: {total_ret:,}  | ref price ${ref_price:,.0f}")

    vr_rows = []
    for q in HORIZONS:
        res = variance_ratio(segs, q)
        if res is None:
            continue
        res["move_usd"] = move_size_usd(segs, q, ref_price)
        res["move_vs_cost"] = res["move_usd"] / ROUND_TRIP_COST_USD
        vr_rows.append(res)
    hurst = hurst_dfa(segs)

    return {
        "label": label, "years": [years[0], years[-1]],
        "n_segments": len(segs), "n_returns": total_ret,
        "ref_price_usd": float(ref_price),
        "variance_ratio": vr_rows,
        "hurst_dfa": hurst,
    }


def print_block(res):
    if not res:
        return
    print(f"\n=== {res['label']} ({res['years'][0]}-{res['years'][1]}) ===")
    print(f"  Hurst (DFA): {res['hurst_dfa']:.4f}  "
          f"[{'mean-revert' if res['hurst_dfa'] < 0.5 else 'trend/persistent'}]"
          if res['hurst_dfa'] is not None else "  Hurst: n/a")
    print(f"  {'q(min)':>7} {'VR':>8} {'z*':>8} {'p':>10} {'move$':>9} {'move/cost':>10}  signal")
    for r in res["variance_ratio"]:
        sig = "mean-revert" if (r["VR"] < 1 and r["p_value"] < 0.05) else \
              ("trend" if (r["VR"] > 1 and r["p_value"] < 0.05) else "~random")
        print(f"  {r['q']:>7} {r['VR']:>8.4f} {r['z_star']:>+8.2f} {r['p_value']:>10.3g} "
              f"{r['move_usd']:>9.2f} {r['move_vs_cost']:>10.2f}  {sig}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="รัน estimator self-test อย่างเดียว")
    ap.add_argument("--years", type=int, nargs="+", help="เลือกปีเอง (default: full + IS/OOS)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {"cost_assumption_usd": ROUND_TRIP_COST_USD,
           "note": "ROUND_TRIP_COST_USD = placeholder รอ broker จริง §10.6"}

    # 1) SELF-TEST เสมอ (gate)
    st = run_selftest()
    out["selftest"] = st
    if not st["pass"]:
        print("\n!! SELF-TEST FAIL — หยุด ไม่วิเคราะห์ Gold (estimator เชื่อไม่ได้)")
        (OUT_DIR / "layer0_meanrev_result.json").write_text(json.dumps(out, indent=2))
        return
    if args.selftest:
        (OUT_DIR / "layer0_selftest.json").write_text(json.dumps(out, indent=2))
        print(f"\nsaved -> {OUT_DIR / 'layer0_selftest.json'}")
        return

    # 2) วิเคราะห์ Gold
    blocks = []
    if args.years:
        blocks.append(analyze(args.years, "custom"))
    else:
        blocks.append(analyze(ALL_YEARS, "FULL"))
        blocks.append(analyze(IS_YEARS, "IN-SAMPLE"))
        blocks.append(analyze(OOS_YEARS, "OUT-OF-SAMPLE"))

    print("\n" + "=" * 72)
    print("LAYER 0 RESULT — XAUUSD mean-reversion structure")
    print("=" * 72)
    for b in blocks:
        print_block(b)

    out["blocks"] = [b for b in blocks if b]
    (OUT_DIR / "layer0_meanrev_result.json").write_text(json.dumps(out, indent=2))
    print(f"\nsaved -> {OUT_DIR / 'layer0_meanrev_result.json'}")
    print("\nNOTE: move/cost ใช้ cost placeholder $%.2f — ต้อง verify broker จริง (§10.6)" % ROUND_TRIP_COST_USD)


if __name__ == "__main__":
    main()
