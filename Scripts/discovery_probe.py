#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discovery_probe.py — TRELLIS-010 v3 Step 2 · DISCOVERY probe v0

หลัง behavior-research ตัน (fade ตาย · behavior บน v4-entry ไม่มี additive headroom
= pooled-ceiling) → bottleneck ย้ายมา DISCOVERY: หา **entry ที่ v4 จับไม่ได้**
(opportunity_unit: v4 blind · lift −2.2pp) = additive path เดียวสู่เป้า "เข้าทุกโอกาส"

Discovery trigger v0 (generalized momentum · fire ได้ทุกวัน ไม่ใช่แค่ Asian-BO ของ v4):
  · prior-day-range breakout: close แรก (hour 1-22) ที่ทะลุ prior-day-high (long) /
    prior-day-low (short) → เข้าทิศ breakout · 1/วัน
  · R = ATR14 (prior days · ex-ante) · stop = entry ∓ 1R · trail arm 1R dist 0.75R
    (mirror v4) · EOD 23:00 · cost spread+slip เหมือน v4

DISCOVERY FALSIFICATION GATE (ChatGPT · ex-ante):
  Q1: trigger นี้เจอ opportunity type ไหนที่ v4 เจอไม่ได้? → วันที่ prior-day-break แต่
      ไม่มี Asian-BO / ถูก slope-filter บล็อก
  Q2: **เพิ่ม oracle-coverage จริงไหม (additive)** ไม่ใช่ย้าย entry ใน opportunity เดิม? →
      วัด P&L บนวัน **v4-missed** โดยเฉพาะ (ถ้า net+ = additive จริง)
  Q3 info-ceiling: prior-day-break = f(OHLC) → ถ้า oracle-opp บนวัน missed มีจริงแต่
      trigger จับไม่ได้ net+ = OHLC-Discovery ceiling → Stage F trigger (new data)
สนาม SEARCH · DoF pin ex-ante · setup as-of (prior-day known ณ session open · no lookahead)
Usage: python discovery_probe.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, PT, SLIP_IN, SLIP_STOP

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = Path(__file__).parent.parent / "Research" / "h0"
ATR_N = 14
A_ARM, D_TRAIL = 1.0, 0.75


def sim_day(ctx, i0, i1, phi, plo, R):
    """prior-day-range breakout trade ในวัน [i0,i1) · คืน (pnl, reason) หรือ (nan,'no-trig')"""
    o, h, l, c, sp = ctx["o"], ctx["h"], ctx["l"], ctx["c"], ctx["sp"]
    hour, dow = ctx["hour"], ctx["dow"]
    ent = stop = best = None
    d = 0
    armed = False
    for q in range(i0, i1):
        if 1 <= hour[q] < 22 and d == 0:                 # หา trigger
            if c[q] > phi:
                d = 1
            elif c[q] < plo:
                d = -1
            if d != 0:
                ent = (c[q] + sp[q] * PT + SLIP_IN) if d == 1 else (c[q] - SLIP_IN)
                stop = ent - R if d == 1 else ent + R
                best = ent
                continue
        if d == 0:
            continue
        if hour[q] >= (20 if dow[q] == 5 else 23):        # eod
            ex = c[q] if d == 1 else c[q] + sp[q] * PT
            return (ex - ent) * d, "eod", d
        hit = l[q] <= stop if d == 1 else h[q] >= stop
        if hit:
            px = (min(stop, o[q]) if d == 1 else max(stop, o[q])) - SLIP_STOP * d
            ex = px if d == 1 else px + sp[q] * PT
            return (ex - ent) * d, "stop", d
        best = max(best, c[q]) if d == 1 else min(best, c[q])
        if (best - ent) * d >= A_ARM * R:
            armed = True
            ns = best - D_TRAIL * R if d == 1 else best + D_TRAIL * R
            stop = max(stop, ns) if d == 1 else min(stop, ns)
    if d == 0:
        return np.nan, "no-trigger", 0
    return np.nan, "eof", d


def oracle_day(ctx, i0, i1, R):
    """oracle best-swing (opportunity_unit logic) → (orcR, dir) · ex-post label"""
    h, l, hour = ctx["h"], ctx["l"], ctx["hour"]
    m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22)
    hh, ll = h[i0:i1][m], l[i0:i1][m]
    if len(hh) < 30:
        return np.nan, 0
    bl = float((hh - np.minimum.accumulate(ll)).max())
    bs = float((np.maximum.accumulate(hh) - ll).max())
    return max(bl, bs) / R, (1 if bl >= bs else -1)


def main():
    ctx = load_ctx()
    day, h, l = ctx["day"], ctx["h"], ctx["l"]
    v4day = {r["date"]: int(r["dir"]) for r in csv.DictReader(
        ln for ln in open(DIR / "h0_day_facts_2012_2020.csv", encoding="utf-8")
        if not ln.startswith("#")) if r["traded"] == "1"}

    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(h)]
    dhi = {di: float(h[i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(l[i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dr_hist = []
    rows = []
    prev = None
    for di, i0, i1 in zip(uniq.tolist(), fidx.tolist(), bnd.tolist()):
        dts = str(np.datetime64(int(di), "D"))
        R = float(np.mean(dr_hist[-ATR_N:])) if len(dr_hist) >= ATR_N else np.nan
        dr_hist.append(dhi[di] - dlo[di])
        if prev is not None and dts[:4] >= "2012" and np.isfinite(R) and R > 0:
            pnl, reason, ddir = sim_day(ctx, i0, i1, dhi[prev], dlo[prev], R)
            orcR, odir = oracle_day(ctx, i0, i1, R)
            rows.append(dict(date=dts, yr=dts[:4], pnl=pnl, reason=reason, ddir=ddir,
                             v4=dts in v4day, opp=bool(np.isfinite(orcR) and orcR >= 2.0),
                             odir=odir))
        prev = di

    trig = [r for r in rows if np.isfinite(r["pnl"])]
    p = np.array([r["pnl"] for r in trig])
    print(f"=== DISCOVERY probe v0 (prior-day breakout) · field=SEARCH · n_days={len(rows)} ===")
    print(f"trigger fired = {len(trig)}/{len(rows)} = {100*len(trig)/len(rows):.1f}% ของวัน")
    print(f"Discovery P&L (ทุกวันที่ fire): sum={p.sum():+.1f} exp={p.mean():+.3f} "
          f"WR={100*(p>0).mean():.1f}%")
    miss = np.array([not r["v4"] for r in trig])
    print(f"\n  [cost diagnostic · NOT gate] all v4-missed (fire): n={miss.sum()} "
          f"exp={p[miss].mean():+.3f} — 94% chop, ไม่ใช่ gate population")

    # ⭐ FALSIFICATION GATE Q2 (correct population · Engineer): v4-missed ∧ oracle-OPPORTUNITY
    mo = np.array([(not r["v4"]) and r["opp"] for r in trig])
    print(f"\n⭐ GATE Q2 — v4-missed ∧ oracle-OPPORTUNITY (population ที่ gate ต้องการ):")
    print(f"  n={mo.sum()} · Discovery P&L sum={p[mo].sum():+.1f} exp={p[mo].mean():+.3f} "
          f"WR={100*(p[mo]>0).mean():.1f}%  ← additive? (net+ = ผ่าน)")
    # direction agreement (probe dir == oracle dir)
    da = np.array([r["ddir"] == r["odir"] for r in trig])
    for lab, m2 in (("probe-dir == oracle-dir", mo & da), ("probe-dir ≠ oracle-dir", mo & ~da)):
        if m2.any():
            print(f"    {lab}: n={m2.sum():>3} exp={p[m2].mean():+.3f} WR={100*(p[m2]>0).mean():.0f}%")
    print(f"\n  per-year (v4-missed ∧ opp):")
    for y in range(2012, 2021):
        ym = np.array([r["yr"] == str(y) and not r["v4"] and r["opp"] for r in trig])
        if ym.any():
            print(f"    {y}: n={ym.sum():>2} sum={p[ym].sum():+6.1f} exp={p[ym].mean():+.3f}")
    print("\n⚠ v0 · scope=Momentum family (prior-day-break) · n เล็ก (ยังไม่ถึง 'signal' bar) · "
          "oracle=hindsight upper-bound (ต้อง trigger-constrained ก่อน claim capture · §9) · "
          "net+ = Discovery NOT falsified (ยังไม่ใช่ ceiling · Stage F premature)")


if __name__ == "__main__":
    main()
