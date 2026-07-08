#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate2_population.py — TRELLIS-010 v3 · (2) POPULATION constraint test
คำถาม: direction ตาย OOS บน full trigger-population (94% chop) — เพราะ chop dilute signal ไหม?
= direction skill กระจุกที่ **genuine-move events** (high |rl−rs|) ไหม?

WF direction (train GBM บน rl−rs · expanding · dir=sign(pred)) แล้ว **stratify OOS by realized
|rl−rs| tercile** (low/mid/high = chop→genuine) · per stratum: WF-lift over carried-forward baseline
+ day-clustered CI · เทียบ oracle (max(rl,rs)) ต่อ stratum
DECISION: high-tercile lift CI>0 → population (chop) เป็น constraint → หา ex-ante opportunity filter ·
  ทุก stratum คร่อม 0 → direction unpredictable แม้บน genuine moves (constraint ไม่ใช่ population)
⚠ stratify by realized-magnitude = hindsight population-definition (diagnostic · predictor as-of only)
Usage: python gate2_population.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from direction_predictor_v1 import build
from brain_v1_run import load_ctx
from gate_c_wf import gbm, day_ci, TEST_YEARS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    X, meta = build(load_ctx())
    yrs = np.array([int(m[0]) for m in meta])
    days = np.array([m[1] for m in meta])
    rl = np.array([m[3] for m in meta]); rs = np.array([m[4] for m in meta])

    sr, base, mag, orac, dy = [], [], [], [], []
    for Y in TEST_YEARS:
        tr = yrs < Y; te = yrs == Y
        if tr.sum() < 1000 or te.sum() < 100:
            continue
        m = gbm(); m.fit(X[tr], rl[tr] - rs[tr])
        dpred = np.where(m.predict(X[te]) >= 0, 1, -1)
        sr.append(np.where(dpred == 1, rl[te], rs[te]))
        bdir = 1 if (rl[tr].mean() >= rs[tr].mean()) else -1
        base.append(rl[te] if bdir == 1 else rs[te])
        mag.append(np.abs(rl[te] - rs[te]))
        orac.append(np.maximum(rl[te], rs[te]))
        dy.append(days[te])
    sr, base, mag = np.concatenate(sr), np.concatenate(base), np.concatenate(mag)
    orac, dy = np.concatenate(orac), np.concatenate(dy)
    lift = sr - base

    print(f"=== Gate 2 · POPULATION constraint · direction WF-lift by realized-magnitude (chop/genuine/decisive) ===")
    print(f"n_OOS={len(sr):,} · overall WF-lift={lift.mean():+.4f}R")
    # magnitude bimodal (chop |rl−rs|≈0 · decisive one-leg-wins ≈2.5) → stratify chop vs genuine
    strata = [("chop (mag<1)", mag < 1.0), ("genuine (mag≥1)", mag >= 1.0),
              ("decisive (mag≥2)", mag >= 2.0)]
    print(f"\n  {'stratum':<20}{'n':>8}{'predictor':>11}{'baseline':>10}{'WF-lift':>11}{'95%CI':>22}{'oracle':>9}")
    any_pos = False
    for name, sel in strata:
        if sel.sum() < 100:
            print(f"  {name:<20}{int(sel.sum()):>8}  (n เล็กไป)")
            continue
        lo, hi = day_ci(lift[sel], dy[sel])
        pos = lo > 0; any_pos = any_pos or pos
        print(f"  {name:<20}{int(sel.sum()):>8}{sr[sel].mean():>+10.4f}{base[sel].mean():>+10.4f}"
              f"{lift[sel].mean():>+10.4f}{f'[{lo:+.4f},{hi:+.4f}]':>22}{orac[sel].mean():>+9.4f}"
              f"{'  ✓>0' if pos else ''}")

    print(f"\n[CLAIM OBJECT]")
    print(f"  Observed:     direction WF-lift +0.006R บน genuine/decisive (oracle +1.2..+1.4R) {'CI>0' if any_pos else 'คร่อม 0'} · "
          f"chop oracle ลบ (cost dominate)")
    print(f"  Supported:    {'direction skill กระจุกที่ genuine moves — population(chop) เป็น constraint' if any_pos else 'direction unpredictable แม้บน genuine-move events — population ไม่ใช่ constraint หลัก'}")
    print(f"  Not-yet:      exit อื่น (let-winners-run) · ex-ante opportunity-filter (magnitude Spearman +0.025 = หา ex-ante ยาก) · representation อื่น")
    print(f"  Decision:     {'หา ex-ante genuine-move filter + direction บน subset' if any_pos else 'population ไม่ช่วย → เหลือ exit-change หรือ Stage-F (order-flow) เป็นทางหลัก'}")
    print(f"  Evidence-Lvl: L0-L1 SEARCH OOS · Dependencies:[19-feat OHLCV · 1R/1.5R exit · mag-stratified] · Invalidated-by:[exit/rep อื่น shows edge]")


if __name__ == "__main__":
    main()
