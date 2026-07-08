#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_spread_mi.py — TRELLIS-010 v3 · SPREAD-channel MI test (Engineer P-A · cheapest-decisive-first)
audit พบ: spread (M1 col9 · โหลดเป็น `sp` แล้ว) ใช้แค่ cost · **ไม่เคยเป็น feature** · corr กับ range
เพียง +0.26 = channel อิสระที่ยังไม่เทสต์ · zero tick-reprocessing (data ใน RAM)

คำถาม: spread-derived features มี DIRECTION-info ที่ OHLC 19-feat ไม่มีไหม? (beat 1/19 ceiling?)
features (as-of ≤ bar i): spread_lvl · spread_z(rel time) · dspread · spread/range(illiquidity) ·
  spread_trend · spread/R · spread×tdir(interaction)
target: sign(rl−rs) [direction] + continuous(rl−rs) · day-block null + max-stat FWE (reuse gate1.fwe_mi)
DECISION: spread MI(sign) >0 = spread เพิ่ม direction-info → เพิ่มเข้า predictor · =0 = spread ก็ไม่ช่วย
  → เหลือ 1-year tick-price pilot (plain=UTC) ก่อน all-years GB · Stage-F ถ้า tick ก็ตาย
⚠ SEARCH · in-sample MI = necessary-cond · report Claim Object
Usage: python gate_spread_mi.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, PT, SLIP_IN, SLIP_STOP
from opportunity_unit_v4 import make_triggers, build_normalizers, ACCT_TARGETS
from direction_predictor import trade_R
from gate1_mi_ceiling import fwe_mi
import gate1_mi_ceiling as g1

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RNG = np.random.default_rng(20260708)
SF = ["spread_lvl", "spread_z", "dspread5", "spread_over_range", "spread_trend",
      "spread_over_R", "spread_x_tdir"]


def main():
    ctx = load_ctx()
    o, h, l, c, sp, day, hour = (ctx["o"], ctx["h"], ctx["l"], ctx["c"], ctx["sp"],
                                 ctx["day"], ctx["hour"])
    Rmap = build_normalizers(ctx)[0][f"daily@{ACCT_TARGETS[0]}"]
    uniq, fidx = np.unique(day, return_index=True); bnd = np.r_[fidx[1:], len(h)]
    dhi = {di: float(h[i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(l[i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    ul, fl, bl = uniq.tolist(), fidx.tolist(), bnd.tolist()

    X, ss, META = [], [], []
    for j, (di, i0, i1) in enumerate(zip(ul, fl, bl)):
        dts = str(np.datetime64(int(di), "D"))
        if dts not in Rmap or Rmap[dts] <= 0:
            continue
        R = Rmap[dts]
        m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22); gi = np.arange(i0, i1)[m]
        oo, hh, ll, cc, spd = o[gi], h[gi], l[gi], c[gi], sp[gi]
        n = len(cc)
        if n < 90:
            continue
        pdi = ul[j - 1] if j > 0 else None
        lt, st = make_triggers(hh, ll, cc, dhi.get(pdi) if pdi else None,
                               dlo.get(pdi) if pdi else None, "both", 60)
        for i in np.where(lt | st)[0]:
            if i < 60 or i > n - 5:
                continue
            tdir = 1 if (lt[i] and not st[i]) else (-1 if (st[i] and not lt[i]) else 0)
            if tdir == 0:
                continue
            cost = (spd[i] * PT + SLIP_IN + SLIP_STOP) / R
            rl = trade_R(hh, ll, cc, i, 1, R, cost); rs = trade_R(hh, ll, cc, i, -1, R, cost)
            recent = spd[i - 60:i]
            feat = [
                spd[i],
                (spd[i] - recent.mean()) / (recent.std() + 1e-9),
                spd[i] - spd[i - 5:i].mean(),
                spd[i] / ((hh[i] - ll[i]) + 1e-9),
                spd[i - 5:i + 1].mean() / (spd[i - 60:i + 1].mean() + 1e-9),
                spd[i] / R,
                spd[i] * tdir,
            ]
            X.append(feat); ss.append(1 if rl >= rs else 0)
            META.append((int(dts[:4]), j, rl, rs))
    X = np.array(X); yb = np.array(ss); META = np.array(META)
    yr = META[:, 0].astype(int); dday = META[:, 1].astype(int); rl_a = META[:, 2]; rs_a = META[:, 3]
    print(f"=== Gate SPREAD-MI · n={len(X):,} events · {len(SF)} spread features ===")

    g1.X = X; g1.FEATS = SF
    ms, _, ts, _ = fwe_mi(X, yb, True)                    # MI(sign) = direction · full sample
    print(f"\n[a] MI(spread feature; DIRECTION=sign) · day-block null + max-stat FWE:")
    print(f"  {'feature':<18}{'MI(sign)':>10}  FWE-sig(>{ts:.4f})")
    for k in np.argsort(ms)[::-1]:
        print(f"  {SF[k]:<18}{ms[k]:>10.4f}  {'✓' if ms[k] > ts else ''}")
    nsig = int((ms > ts).sum())
    print(f"  → in-sample spread DIRECTION-sig = {nsig}/{len(SF)} (⚠ necessary ไม่ใช่ sufficient · slow-feature "
          f"อาจ clustering-inflated เหมือน dist_pdl)")

    # [b] DE-CLUSTER (1 event/วัน) — spread_over_R เป็น clustering-artifact ไหม
    #     1 event/day = within-day autocorr ตัดแล้ว → permutation null ใช้ได้ (เหมือน gate1 [b])
    from sklearn.feature_selection import mutual_info_classif
    uq = np.unique(dday)
    sig_dc = []
    for r in range(3):
        pk = np.array([RNG.choice(np.where(dday == d)[0]) for d in uq])
        Xs, ysb = X[pk], yb[pk]
        mr = mutual_info_classif(Xs, ysb, discrete_features=False, random_state=0)
        nl = np.array([mutual_info_classif(Xs, RNG.permutation(ysb), discrete_features=False, random_state=s)
                       for s in range(15)])
        thr_dc = np.percentile(nl.max(1), 95)                 # max-stat FWE
        sig_dc.append(int((mr > thr_dc).sum()))
    print(f"\n[b] DE-CLUSTER MI (1 event/วัน · n={len(uq)} · 3 resamples): spread DIRECTION-sig = {sig_dc}/{len(SF)} "
          f"→ {'รอด = real per-day' if max(sig_dc) > 0 else 'COLLAPSE = clustering-artifact (เหมือน dist_pdl)'}")
    dc_survive = max(sig_dc) > 0

    # [c] OOS TRANSFER (expanding-WF · decisive) — spread ยัง OOS direction-lift ไหม
    from gate_c_wf import gbm, day_ci, TEST_YEARS
    sr, base, dyo = [], [], []
    for Y in TEST_YEARS:
        tr = yr < Y; te = yr == Y
        if tr.sum() < 500 or te.sum() < 100: continue
        gm = gbm(); gm.fit(X[tr], rl_a[tr] - rs_a[tr])
        dp = np.where(gm.predict(X[te]) >= 0, 1, -1)
        sr.append(np.where(dp == 1, rl_a[te], rs_a[te]))
        bdir = 1 if (rl_a[tr].mean() >= rs_a[tr].mean()) else -1
        base.append(rl_a[te] if bdir == 1 else rs_a[te]); dyo.append(dday[te])
    sr = np.concatenate(sr); base = np.concatenate(base); dyo = np.concatenate(dyo)
    lift = sr - base; lo, hi = day_ci(lift, dyo)
    print(f"\n[c] OOS TRANSFER (spread-features GBM · expanding-WF · DECISIVE):")
    print(f"  WF-lift = {lift.mean():+.4f}R · 95%CI(day-clustered) [{lo:+.4f},{hi:+.4f}] "
          f"{'✓>0 transfer' if lo > 0 else 'คร่อม 0 = ไม่ transfer'}")

    transfer = lo > 0 and dc_survive
    print(f"\n[CLAIM OBJECT]")
    print(f"  Observed:     spread in-sample MI-sig {nsig}/7 · de-cluster {sig_dc}/7 · OOS WF-lift {lift.mean():+.4f}R CI[{lo:+.4f},{hi:+.4f}]")
    print(f"  Supported:    {'spread เพิ่ม OOS direction-edge' if transfer else 'spread in-sample MI = clustering/artifact + ไม่ transfer OOS — spread ก็ไม่ช่วย direction'}")
    print(f"  Not-yet:      tick-level bid/ask price (higher-res · ceiling ไม่ bind · P-B) · 1-year pilot")
    print(f"  Decision:     {'เพิ่ม spread เข้า predictor' if transfer else 'spread ตาย OOS → เหลือ 1-year tick-price pilot (plain=UTC) = channel สุดท้ายใน hand ก่อน Stage-F'}")
    print(f"  Evidence-Lvl: {'L1' if transfer else 'L0-L1'} SEARCH · Invalidated-by:[tick-price MI · richer exit/pop]")


if __name__ == "__main__":
    main()
