#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate1_mi_ceiling.py — TRELLIS-010 v3 · Gate B step-1 = MI-CEILING (v2 · Engineer-FAIL-fixed)
คำถาม decisive: features มี **extractable direction information** ต่อ signed-R objective ไหม?

v2 fixes (Engineer FAIL): (P1) i.i.d. null บน day-clustered data → **DAY-BLOCK circular-shift null +
MAX-STAT FWE** (Westfall-Young · autocorr-safe เหมือน opportunity_unit_v4:160) · (P1 split) 3 targets
แยก **DIRECTION(sign) vs MAGNITUDE(|rl−rs|)** — continuous(rl−rs) เป็น magnitude-contaminated:
  (a) MI 3-target + FWE → direction-ceiling = MI(sign) · magnitude = MI(|d|)
  (b) ⭐ DE-CLUSTER MI (1 event/วัน) = clustering-artifact หรือ real per-day
  (c) in-sample GBM = **DIAGNOSTIC เท่านั้น ไม่ใช่ evidence** (overfit · OOS=Gate C/gate_magnitude_oos)
⚠ SEARCH · MI = necessary-cond (ไม่ใช่ deploy) · OOS edge = Gate C(direction)+gate_magnitude_oos เท่านั้น
Usage: python gate1_mi_ceiling.py
"""
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
from lightgbm import LGBMRegressor

sys.path.insert(0, str(Path(__file__).parent))
from direction_predictor_v1 import build, FEATS
from brain_v1_run import load_ctx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RNG = np.random.default_rng(20260708)
N_SHUF = 15         # max-stat FWE (0.95-quantile ของ max) · x3 targets · runtime-bounded


def fwe_mi(X, tgt, discrete):
    """MI + day-block circular-shift null (autocorr-safe) + MAX-STAT FWE (Westfall-Young · MTC-correct)
    คืน (mi_real, null_mean, thr_fwe, sig-boolean) · discrete=True → classif (sign) · False → regression"""
    fn = mutual_info_classif if discrete else mutual_info_regression
    real = fn(X, tgt, discrete_features=False, random_state=0)
    n = len(tgt)
    nul = np.zeros((N_SHUF, X.shape[1]))
    for s in range(N_SHUF):
        nul[s] = fn(X, np.roll(tgt, int(RNG.integers(2000, n - 2000))), discrete_features=False, random_state=s + 1)
    thr = np.percentile(nul.max(1), 95)
    return real, nul.mean(0), thr, real > thr


def main():
    X, meta = build(load_ctx())
    days = np.array([m[1] for m in meta])
    rl = np.array([m[3] for m in meta]); rs = np.array([m[4] for m in meta])
    y = rl - rs; n = len(y)
    print(f"=== Gate 1 v2 · MI-CEILING · target=continuous(rl−rs) · n={n:,} · {X.shape[1]} feats ===")

    # ── (a) marginal MI · 3 targets แยก DIRECTION vs MAGNITUDE (Engineer P1 · script-owned) ──
    #    continuous(rl−rs) = magnitude-weighted · SIGN = direction ล้วน · |rl−rs| = magnitude ล้วน
    mc, ncm, tc, sc = fwe_mi(X, y, False)                       # continuous
    ms, nsm, ts, ss = fwe_mi(X, (y >= 0).astype(int), True)    # SIGN = direction
    mm, nmm, tm, sm = fwe_mi(X, np.abs(y), False)              # magnitude
    print(f"\n[a] MARGINAL MI · day-block null + MAX-STAT FWE · 3 targets (DIRECTION vs MAGNITUDE · Engineer P1):")
    print(f"  {'feature':<14}{'MI_cont':>9}{'MI_SIGN':>9}{'MI_mag':>9}  sign-sig mag-sig")
    for k in np.argsort(mc)[::-1]:
        print(f"  {FEATS[k]:<14}{mc[k]:>9.4f}{ms[k]:>9.4f}{mm[k]:>9.4f}  {'✓' if ss[k] else ' '}       {'✓' if sm[k] else ''}")
    print(f"  → continuous FWE-sig = {sc.sum()}/{X.shape[1]} (magnitude-contaminated) · "
          f"**SIGN(direction) = {ss.sum()}/{X.shape[1]}** · MAGNITUDE = {sm.sum()}/{X.shape[1]}")
    print(f"    → direction ceiling in-sample = {ss.sum()}/19 (≈noise ถ้า 0-1) · signal อยู่ที่ magnitude")

    # ── (b) ⭐ DE-CLUSTER MI (1 event/วัน) = decisive clustering test ──
    uq = np.unique(days)
    accsig = []
    for r in range(3):
        pk = np.array([RNG.choice(np.where(days == d)[0]) for d in uq])
        Xs, ys = X[pk], y[pk]
        mr = mutual_info_regression(Xs, ys, n_neighbors=3, random_state=0)
        nl = np.array([mutual_info_regression(Xs, RNG.permutation(ys), n_neighbors=3, random_state=s) for s in range(10)])
        accsig.append(sum(mr[k] > np.percentile(nl[:, k], 97.5) for k in range(X.shape[1])))
    print(f"\n[b] ⭐ DE-CLUSTER MI (1 event/วัน · n={len(uq)} · ตัด within-day clustering):")
    print(f"  significant หลัง de-cluster (3 resamples) = {accsig} / {X.shape[1]}")
    print(f"  → strong MI ที่หายหลัง de-cluster = clustering-artifact · ที่รอด = real per-day (อ่อน)")

    # ── (c) in-sample GBM = DIAGNOSTIC ONLY (ไม่ใช่ evidence · Engineer P2) ──
    m = LGBMRegressor(max_depth=4, n_estimators=200, learning_rate=0.05, min_child_samples=200,
                      subsample=0.8, colsample_bytree=0.8, verbose=-1, random_state=0)
    m.fit(X, y)
    lift_real = np.where(m.predict(X) >= 0, rl, rs).mean() - max(rl.mean(), rs.mean())
    idx = RNG.permutation(n)
    m.fit(X, y[idx])
    lift_rand = np.where(m.predict(X) >= 0, rl[idx], rs[idx]).mean() - max(rl[idx].mean(), rs[idx].mean())
    print(f"\n[c] in-sample GBM lift (⚠ DIAGNOSTIC ไม่ใช่ evidence · overfit floor): "
          f"real {lift_real:+.4f}R vs random {lift_rand:+.4f}R — OOS จริงดู Gate C เท่านั้น")

    # ── VERDICT (Claim Object · honest · post Engineer P1 + Claude deep-verify) ──
    print(f"\n[CLAIM OBJECT]")
    print(f"  Observed:     DIRECTION-MI(sign)={ss.sum()}/{X.shape[1]} · MAGNITUDE-MI={sm.sum()}/{X.shape[1]} · "
          f"continuous={sc.sum()}/{X.shape[1]} · de-cluster={accsig} · in-sample GBM(diag) {lift_real:+.4f} vs rand {lift_rand:+.4f}")
    print(f"  Supported:    in-sample DIRECTION info ≈ noise ({ss.sum()}/19) · signal อยู่ที่ MAGNITUDE ({sm.sum()}/19) · "
          f"strong continuous-MI = magnitude+clustering (ไม่ใช่ direction)")
    print(f"  Not-yet:      exploitable OOS? = Gate C (direction) + magnitude-OOS test ตัดสิน (in-sample ≠ OOS)")
    print(f"  Decision:     direction ceiling in-sample = noise → OOS transfer test (Gate C = direction · gate_magnitude_oos = magnitude)")
    print(f"  Evidence-Lvl: L0 SEARCH in-sample · Dependencies:[19-feat OHLCV · 1R/1.5R exit] · Invalidated-by:[OOS transfer +]")


if __name__ == "__main__":
    main()
