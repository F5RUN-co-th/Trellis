#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_c_wf.py — TRELLIS-010 v3 · Gate C = WF-nonlinear TRANSFER test (Engineer Decision-Table v2)
Gate 1 v2 (null-fixed): continuous-MI 6/19 = MAGNITUDE (DIRECTION-MI(sign)=1/19≈noise · Engineer P1) →
คำถาม decisive: DIRECTION transfer OOS ไหม? = expanding walk-forward (magnitude → gate_magnitude_oos.py)

metric = **expanding-WF signed-R lift เหนือ TRAIN-best-constant-carried-forward** (ex-ante-choosable dir)
protocol: for test-year Y in 2015-2020 · train GBM บนปี < Y · predict Y · dir=sign(pred) · signed-R(Y)
baseline(Y) = train-best-constant (sign of mean(rl−rs) บน train) applied to Y  ← ex-ante · carried-forward
random-label = shuffle X↔outcome ใน train แต่ละ fold → WF → noise-floor · day-clustered bootstrap CI
DECISION (pre-registered TABLE v2): CI-upper < random-WF floor → KILL · CI excl 0 แต่ ≪0.37R →
  INFO-not-deployable · CI excl 0 + survive MTC → proceed · L1 ≠ deployable
⚠ SEARCH · report Claim Object + decision-curve corroboration
Usage: python gate_c_wf.py
"""
import sys
from pathlib import Path

import numpy as np
from lightgbm import LGBMRegressor

sys.path.insert(0, str(Path(__file__).parent))
from direction_predictor_v1 import build
from brain_v1_run import load_ctx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RNG = np.random.default_rng(20260708)
TEST_YEARS = [2015, 2016, 2017, 2018, 2019, 2020]


def gbm():
    return LGBMRegressor(max_depth=4, n_estimators=200, learning_rate=0.05,
                         min_child_samples=200, subsample=0.8, colsample_bytree=0.8,
                         verbose=-1, random_state=0)


def wf(X, yrs, rl, rs, shuffle=False):
    """expanding walk-forward · คืน (oos_signedR, oos_baseline, oos_conf) ต่อ event"""
    sr, base, conf = [], [], []
    for Y in TEST_YEARS:
        tr = yrs < Y
        te = yrs == Y
        if tr.sum() < 1000 or te.sum() < 100:
            continue
        rlt, rst = rl[tr], rs[tr]
        if shuffle:
            idx = RNG.permutation(tr.sum())
            rlt, rst = rlt[idx], rst[idx]              # break X↔outcome in train
        m = gbm()
        m.fit(X[tr], rlt - rst)
        pred = m.predict(X[te])
        dpred = np.where(pred >= 0, 1, -1)
        sr.append(np.where(dpred == 1, rl[te], rs[te]))
        bdir = 1 if (rlt.mean() >= rst.mean()) else -1  # train-best-constant carried-forward
        base.append(rl[te] if bdir == 1 else rs[te])
        conf.append(np.abs(pred))                       # ex-ante confidence (decision-curve)
    return np.concatenate(sr), np.concatenate(base), np.concatenate(conf)


def day_ci(vals, days, nb=400):
    uq = np.unique(days)
    d2i = {d: np.where(days == d)[0] for d in uq}
    out = [np.concatenate([vals[d2i[d]] for d in RNG.choice(uq, len(uq), replace=True)]).mean()
           for _ in range(nb)]
    return np.percentile(out, 2.5), np.percentile(out, 97.5)


def main():
    X, meta = build(load_ctx())
    yrs = np.array([int(m[0]) for m in meta])
    days = np.array([m[1] for m in meta])
    rl = np.array([m[3] for m in meta])
    rs = np.array([m[4] for m in meta])
    # align OOS day indices
    oos_mask = np.isin(yrs, TEST_YEARS)
    days_oos = days[oos_mask]
    print(f"=== Gate C · WF-nonlinear TRANSFER · test={TEST_YEARS} · n_OOS={oos_mask.sum():,} ===")

    sr, base, conf = wf(X, yrs, rl, rs)
    lift = sr - base
    lo, hi = day_ci(lift, days_oos)
    print(f"\n[TRANSFER · expanding-WF]")
    print(f"  predictor OOS signed-R   = {sr.mean():+.4f}R")
    print(f"  carried-forward baseline = {base.mean():+.4f}R")
    print(f"  **WF-lift = {lift.mean():+.4f}R** · 95%CI(day-clustered) [{lo:+.4f},{hi:+.4f}]")

    # DECISION CURVE (plan-mandated · confidence-gating · ทดสอบ transferable subset)
    print(f"\n[DECISION CURVE · OOS confidence-gating |pred| · หา transferable subset]")
    print(f"  {'top-q%':>8}{'n':>8}{'lift':>11}{'95%CI':>22}")
    for q in (100, 50, 20, 10, 5):
        sel = conf >= np.percentile(conf, 100 - q)
        clo, chi = day_ci(lift[sel], days_oos[sel])
        print(f"  {q:>7}%{int(sel.sum()):>8}{lift[sel].mean():>+10.4f}R{f'[{clo:+.4f},{chi:+.4f}]':>22}"
              f"{'  ✓>0' if clo > 0 else ''}")

    # random-label noise floor (WF)
    rand_lifts = []
    for s in range(5):
        srr, baser, _ = wf(X, yrs, rl, rs, shuffle=True)
        rand_lifts.append((srr - baser).mean())
    rf = np.array(rand_lifts)
    print(f"  random-label WF-lift     = {rf.mean():+.4f}R [{rf.min():+.4f},{rf.max():+.4f}] (noise floor)")

    # decision curve corroboration: signed-R by predictor-confidence bucket (need score) — skip formal, report lift-CI as trigger
    floor = max(rf.max(), 0.0)
    req = 0.37
    print(f"\n[DECISION · pre-registered TABLE v2 · trigger = WF-lift CI]")
    if hi < floor:
        dec = f"KILL representation (CI-upper {hi:+.4f} < random-WF floor {floor:+.4f} = undetectable)"
    elif lo > 0 and lift.mean() < req:
        dec = f"INFO-not-deployable (CI excl 0 · point {lift.mean():+.4f}R ≪ required {req}R · ห้าม imply deploy)"
    elif lo > 0:
        dec = f"proceed (CI excl 0 + point ≥ required — ต้องเช็ค MTC/deflated-Sharpe)"
    else:
        dec = f"no-transfer (CI คร่อม 0 · in-sample info ไม่ transfer OOS)"
    print(f"\n[CLAIM OBJECT]")
    print(f"  Observed:     WF-lift {lift.mean():+.4f}R CI[{lo:+.4f},{hi:+.4f}] · random-floor {rf.mean():+.4f} · predictor {sr.mean():+.4f} vs baseline {base.mean():+.4f}")
    print(f"  Supported:    {'in-sample direction-info (Gate 1) TRANSFER OOS' if lo > 0 else 'in-sample info (Gate 1) ไม่ transfer OOS ใน static-WF (สอดคล้อง concept-drift Gate A)'}")
    print(f"  Not-yet:      {'deployable (ยัง ≪ ruin-safe 0.37R · ต้อง sizing/additive)' if lo > 0 else 'adaptive/regime-encoding · other-representation ยังไม่ทดสอบ (ห้ามสรุป direction dead)'}")
    print(f"  Decision:     {dec}")
    print(f"  Evidence-Lvl: L0-L1 (SEARCH · OOS-WF) · Dependencies:[19-feat OHLCV · 1R/1.5R exit · static-GBM] · "
          f"Invalidated-by:[adaptive/regime model shows transfer · other rep]")


if __name__ == "__main__":
    main()
