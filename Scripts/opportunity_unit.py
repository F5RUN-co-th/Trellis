#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opportunity_unit.py — TRELLIS-010 v3 Step 1 · Canonical Opportunity Unit
(measurement frame · §6) — ground-truth opportunity set + base rate

แยก 3 วัตถุ (Engineer + ChatGPT Q6 · กัน circular):
  · UNIT (ex-ante, strategy-independent) = 1 trading day (decision point · enumerate
    ทุกวันเทรด รวมวันที่ v4 ข้าม → วัด additive path "เข้าทุกโอกาส")
  · LABEL (ex-post oracle — อนาคตใช้ได้เพราะเป็น target ไม่ใช่ feature) = best single-swing
    R-multiple ที่ perfect-timing จับได้ intraday (long=max drawup, short=max drawdown, O(n))
  · R (ex-ante risk unit, strategy-independent) = ATR14 ของ N วันก่อน (รู้ ณ session open ·
    ไม่ผูก Asian-width ของ v4)
  · OPPORTUNITY = oracle-R ≥ TARGET (2.0) → "มี swing ≥2R ให้จับ โดยไม่สน EA เข้าไหม"
  · PREDICTOR (ex-ante features ทำนาย opportunity+ทิศ) = Step 2 (ยังไม่ทำ)

DoF pin ex-ante (ก่อนรัน · ให้ Engineer review): TARGET=2.0R · ATR window=14 วัน ·
  session=hour 1-22 (tradeable) · oracle = perfect single-swing (ไม่ใช่ multi-entry)
no-leak: unit=วัน (ex-ante) · R=prior-days (ex-ante) · label ใช้ future = ตั้งใจ (target)
Usage: python opportunity_unit.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(r"D:/workspace/Doc/T.me/R&D/Gloo/Data")
DIR = Path(__file__).parent.parent / "Research" / "h0"
YEARS = list(range(2011, 2021))
TARGET = 2.0                 # opportunity threshold (R-multiple) — pin ex-ante
ATR_N = 14                   # R = ATR ของ N วันก่อน (ex-ante)


def main():
    # โหลด M1 (SEARCH field) → group by day
    t, o, h, l, c = [], [], [], [], []
    for y in YEARS:
        with open(DATA / f"XAUUSD_M1_{y}.csv", newline="") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                t.append(np.datetime64(p[0].replace(".", "-") + "T" + p[1][:5]))
                o.append(float(p[2])); h.append(float(p[3]))
                l.append(float(p[4])); c.append(float(p[5]))
    t = np.array(t); h = np.array(h); l = np.array(l); c = np.array(c)
    tmin = t.astype("datetime64[m]").astype(np.int64)
    hour = (tmin // 60) % 24
    day = (tmin // 1440).astype(int)

    # v4 traded days (เทียบ coverage)
    with open(DIR / "h0_day_facts_2012_2020.csv", encoding="utf-8") as f:
        v4day = {r["date"]: int(r["dir"]) for r in csv.DictReader(
            ln for ln in f if not ln.startswith("#")) if r["traded"] == "1"}
    v4days = set(v4day)

    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(t)]
    # daily true range (สำหรับ ATR ex-ante)
    drange = {}
    for di, i0, i1 in zip(uniq.tolist(), fidx.tolist(), bnd.tolist()):
        drange[di] = float(h[i0:i1].max() - l[i0:i1].min())

    rows = []
    dr_hist = []
    for di, i0, i1 in zip(uniq.tolist(), fidx.tolist(), bnd.tolist()):
        dstr = str(np.datetime64(int(di), "D"))
        yr = dstr[:4]
        R = float(np.mean(dr_hist[-ATR_N:])) if len(dr_hist) >= ATR_N else np.nan
        dr_hist.append(drange[di])
        if yr < "2012" or not np.isfinite(R) or R <= 0:
            continue
        m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22)     # tradeable session
        hh, ll = h[i0:i1][m], l[i0:i1][m]
        if len(hh) < 30:
            continue
        # oracle perfect single-swing (O(n))
        best_long = float((hh - np.minimum.accumulate(ll)).max())    # max drawup
        best_short = float((np.maximum.accumulate(hh) - ll).max())   # max drawdown
        orc = max(best_long, best_short) / R
        rows.append(dict(date=dstr, yr=yr, R=R, orcR=orc,
                         dir=1 if best_long >= best_short else -1,
                         opp=orc >= TARGET, v4=dstr in v4days,
                         v4dir=v4day.get(dstr, 0)))

    n = len(rows)
    opp = [r for r in rows if r["opp"]]
    print(f"=== Canonical Opportunity Unit · field=SEARCH · TARGET={TARGET}R · ATR{ATR_N} ===")
    print(f"UNIT = trading day (n={n}, 2012-2020) · LABEL = oracle best-swing R-multiple")
    print(f"\nORACLE / REFERENCE OPPORTUNITY SET (ยังไม่ใช่ 'ground-truth' — oracle=hindsight/"
          f"single-swing/day-level/ไม่ trigger-constrained · ChatGPT caution):")
    print(f"  opportunities (oracle-R≥{TARGET}) = {len(opp)}/{n} = {100*len(opp)/n:.1f}% base rate")
    print(f"  oracle-R distribution: median={np.median([r['orcR'] for r in rows]):.2f} "
          f"p25={np.percentile([r['orcR'] for r in rows],25):.2f} "
          f"p75={np.percentile([r['orcR'] for r in rows],75):.2f} "
          f"max={max(r['orcR'] for r in rows):.2f}")
    lo = sum(1 for r in opp if r["dir"] == 1)
    print(f"  direction split (opp): long={lo} short={len(opp)-lo}")
    print(f"\n  per-year opportunities:")
    for y in range(2012, 2021):
        yr = [r for r in rows if r["yr"] == str(y)]
        yo = [r for r in yr if r["opp"]]
        print(f"    {y}: {len(yo):>3}/{len(yr):>3} = {100*len(yo)/len(yr):.0f}%")
    # coverage ของ v4 (additive path)
    base_cov = sum(1 for r in rows if r["v4"]) / n
    v4opp = sum(1 for r in opp if r["v4"])
    captured = sum(1 for r in opp if r["v4"] and r["v4dir"] == r["dir"])
    lift = v4opp / len(opp) - base_cov
    print(f"\nOPPORTUNITY COVERAGE (Engineer MED-1: selectivity ไม่ใช่ raw miss):")
    print(f"  v4 overall coverage (baseline) = {100*base_cov:.1f}%")
    print(f"  v4 coverage บน opp-days = {100*v4opp/len(opp):.1f}% → **LIFT = {100*lift:+.1f}pp** "
          f"(≈0 = v4 entry uncorrelated กับ opportunity)")
    print(f"  v4 CAPTURED (traded ∧ ทิศตรง oracle) = {captured}/{len(opp)} = "
          f"{100*captured/len(opp):.1f}% (entered ≠ captured)")
    print(f"  → 'v4 missed ~35%' = blind skip-rate ไม่ใช่ additive edge ที่พิสูจน์ · "
          f"oracle=hindsight → realizable headroom ต้อง **trigger-constrained oracle**")
    print(f"\n⚠ [MED-2] unit=วัน 1 swing/ทิศ = undercount + v4-cadence → v2 ควร swing/event-level "
          f"· oracle=hindsight upper-bound · DoF (TARGET/ATR_N) รอ pin · Step 2 = predictor")


if __name__ == "__main__":
    main()
