#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_magnitude_oos.py — TRELLIS-010 v3 · MAGNITUDE-OOS transfer test (Engineer P3 fix · script-owned)
Gate 1 พบ signal อยู่ที่ MAGNITUDE (MI 6/19) ไม่ใช่ direction (MI-sign 1/19≈noise) → คำถาม decisive:
magnitude นี้ **transfer OOS** ไหม (หรือ pivot→magnitude = in-sample trap ซ้ำ · Engineer P3)?

payoff = **straddle = rl + rs** (net double-cost · trade_R subtract cost/ขา · = กำไรเมื่อ move ใหญ่พอ
ไม่ว่าทิศไหน) · predict straddle ด้วย GBM · expanding-WF · gate top-q% predicted (magnitude-timing)
metric = OOS realized straddle บน traded subset · day-clustered CI · baseline = always-straddle
+ Spearman(predicted, realized) OOS = magnitude rank-skill (exit-agnostic-ish)
DECISION: top-q% CI excl 0 บวก → magnitude viable (pivot ได้) · ทุก bucket ลบ/คร่อม 0 → magnitude
  ไม่ transfer = pivot ก็ trap (terminal negative representation+exit นี้) · ⚠ SEARCH · report Claim Object
Usage: python gate_magnitude_oos.py
"""
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from direction_predictor_v1 import build
from brain_v1_run import load_ctx
from gate_c_wf import gbm, day_ci, TEST_YEARS       # reuse harness (no dup)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    X, meta = build(load_ctx())
    yrs = np.array([int(m[0]) for m in meta])
    days = np.array([m[1] for m in meta])
    rl = np.array([m[3] for m in meta]); rs = np.array([m[4] for m in meta])
    strad = rl + rs                                  # straddle payoff · net double-cost

    real, pred, dy = [], [], []
    for Y in TEST_YEARS:
        tr = yrs < Y; te = yrs == Y
        if tr.sum() < 1000 or te.sum() < 100:
            continue
        m = gbm(); m.fit(X[tr], strad[tr])
        real.append(strad[te]); pred.append(m.predict(X[te])); dy.append(days[te])
    real = np.concatenate(real); pred = np.concatenate(pred); dy = np.concatenate(dy)

    print(f"=== MAGNITUDE-OOS · straddle(rl+rs · net double-cost) · expanding-WF · n_OOS={len(real):,} ===")
    print(f"  unconditional straddle E = {real.mean():+.4f}R (always-straddle baseline)")
    print(f"\n[decision-curve: trade top-q% by predicted-straddle · realized straddle + day-clustered CI]")
    print(f"  {'top-q%':>8}{'n':>8}{'realized':>12}{'95%CI':>22}")
    any_pos = False
    for q in (100, 50, 20, 10, 5):
        sel = pred >= np.percentile(pred, 100 - q)
        lo, hi = day_ci(real[sel], dy[sel])
        pos = lo > 0; any_pos = any_pos or pos
        print(f"  {q:>7}%{int(sel.sum()):>8}{real[sel].mean():>+11.4f}R{f'[{lo:+.4f},{hi:+.4f}]':>22}"
              f"{'  ✓>0' if pos else ''}")
    rho = spearmanr(pred, real).correlation
    print(f"\n  Spearman(predicted, realized straddle) OOS = {rho:+.4f} (rank-skill · ≈0 = magnitude ทำนายไม่ได้ OOS)")

    print(f"\n[CLAIM OBJECT]")
    print(f"  Observed:     always-straddle E={real.mean():+.4f}R · ทุก top-q% bucket {'มี CI บวก' if any_pos else 'ลบ/คร่อม 0'} · Spearman={rho:+.4f}")
    print(f"  Supported:    {'magnitude transfer OOS — straddle viable' if any_pos else 'magnitude ไม่ transfer OOS (net double-cost) — pivot→magnitude = trap เดิม (Engineer P3)'}")
    print(f"  Not-yet:      exit อื่น (let-winners-run · 1R/1.5R cap upside) · population/representation อื่น")
    print(f"  Decision:     {'pivot to magnitude/vol-timing viable' if any_pos else 'direction+magnitude ตาย OOS บน (19-feat OHLCV × trigger-pop × 1R/1.5R exit) → next = exit/population constraint (ไม่ใช่ feature-swap)'}")
    print(f"  Evidence-Lvl: L0-L1 SEARCH OOS · Dependencies:[19-feat OHLCV · straddle · 1R/1.5R exit] · Invalidated-by:[exit/pop อื่น shows OOS edge]")


if __name__ == "__main__":
    main()
